from type import Type
from llvmlite import ir, binding
import ap_ast as ast

LLVM = {
    Type.INT: ir.IntType(32),
    Type.FLOAT32: ir.FloatType(),
    Type.FLOAT64: ir.DoubleType(),
    Type.BOOL: ir.IntType(1),
    Type.STRING: ir.IntType(8).as_pointer()
}

class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="main_module")
        self.builder = None
        self.printf = None
        self.func = None
        self.variables = {}
        self.fmt_str = None


        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

        # Get the default target triple
        self.module.triple = binding.get_default_triple()

        # Set a default data layout
        target = binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        self.module.data_layout = target_machine.target_data

    def compile(self):
        print(self.module)

    def declare_printf(self):
        voidptr = ir.IntType(8).as_pointer()
        printf = ir.FunctionType(ir.IntType(32), [voidptr], var_arg=True)
        self.printf = ir.Function(self.module, printf, name="printf")

    def generate(self, tree):
        main_ty = ir.FunctionType(ir.IntType(32), [])
        self.func = ir.Function(self.module, main_ty, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.declare_printf()

        for stmt in tree.statements:
            self.gen_stmt(stmt)

        self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def gen_stmt(self, stmt):
        assert isinstance(self.builder, ir.IRBuilder)

        if isinstance(stmt, ast.Declaration):
            val = self.gen_expr(stmt.value)
            llvm_type = LLVM[stmt.type_]

            if val.type != llvm_type:
                if llvm_type == ir.FloatType():
                    val = self.builder.fptrunc(val, ir.FloatType())
                    # val = self.builder.sitofp(val, ir.FloatType())
                elif llvm_type == ir.DoubleType():
                    val = self.builder.sitofp(val, ir.DoubleType())
                elif llvm_type == ir.IntType(32):
                    val = self.builder.fptosi(val, ir.IntType(32))

            # print(llvm_type, val)
            ptr = self.builder.alloca(llvm_type, name=stmt.name)
            self.builder.store(val, ptr)
            self.variables[stmt.name] = ptr

        elif isinstance(stmt, ast.Assignment):
            val = self.gen_expr(stmt.value)
            ptr = self.variables.get(stmt.name)
            if not ptr:
                raise RuntimeError(f"Variable '{stmt.name}' not declared")
            self.builder.store(val, ptr)

        elif isinstance(stmt, ast.Read):
            ptr = self.variables[stmt.name]

        elif isinstance(stmt, ast.Print):
            val = self.gen_expr(stmt.value)
            val_type = val.type

            # BOOL: map 0 to "false", 1 to "true"
            if isinstance(val_type, ir.IntType) and val_type.width == 1:
                true_str = self._string_constant("positive", "bool_true")
                true_cast = self.builder.bitcast(true_str, ir.IntType(8).as_pointer())
                false_str = self._string_constant("negative", "bool_false")
                false_cast = self.builder.bitcast(false_str, ir.IntType(8).as_pointer())

                is_true = self.builder.icmp_unsigned("==", val, ir.Constant(ir.IntType(1), 1))
                bool_str = self.builder.select(is_true, true_cast, false_cast)
                fmt_ptr = self._printf_format(ir.IntType(1))
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_cast, bool_str])
            else:
                if isinstance(val_type, ir.FloatType):
                    val = self.builder.fpext(val, ir.DoubleType())
                fmt_ptr = self._printf_format(val_type)
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_cast, val])

    def _printf_format(self, type_):
        if isinstance(type_, ir.IntType):
            if type_.width == 1:
                fmt_str = "%s\n\0"
                name = "fmt_bool"
            else:
                fmt_str = "%d\n\0"
                name = "fmt_int"
        elif isinstance(type_, (ir.DoubleType, ir.FloatType)):
            fmt_str = "%f\n\0"
            name = "fmt_float"
        elif isinstance(type_, ir.PointerType):
            fmt_str = "%s\n\0"
            name = "fmt_str"
        else:
            raise NotImplementedError("No printf format for: " + type_)

        if name in self.module.globals:
            return self.module.globals[name]

        fmt_bytes = bytearray(fmt_str.encode("utf8"))
        str_type = ir.ArrayType(ir.IntType(8), len(fmt_bytes))
        global_fmt = ir.GlobalVariable(self.module, str_type, name=name)
        global_fmt.linkage = "internal"
        global_fmt.global_constant = True
        global_fmt.initializer = ir.Constant(str_type, fmt_bytes)

        return global_fmt

    def _string_constant(self, s, name):
        s += "\0"
        str_type = ir.ArrayType(ir.IntType(8), len(s))
        if name in self.module.globals:
            return self.module.get_global(name)

        var = ir.GlobalVariable(self.module, str_type, name)
        var.linkage = "internal"
        var.global_constant = True
        var.initializer = ir.Constant(str_type, bytearray(s.encode("utf8")))

        ptr = self.builder.gep(var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        return ptr


    def gen_expr(self, expr):
        assert isinstance(self.builder, ir.IRBuilder)

        if isinstance(expr, ast.Variable):
            ptr = self.variables.get(expr.name)
            if ptr is None:
                raise RuntimeError(f"Undefined variable: {expr.name}")
            return self.builder.load(ptr)

        elif isinstance(expr, ast.UnaryOp):
            val = self.gen_expr(expr.operand)
            if expr.op == 'NOT':
                return self.builder.icmp_unsigned('==', val, ir.Constant(ir.IntType(32), 0))
            raise NotImplementedError(f"Unary operator {expr.op}")

        elif isinstance(expr, ast.BinaryOp):
            left = self.gen_expr(expr.left)
            right = self.gen_expr(expr.right)

            # Change types if nessesery
            if left.type != right.type:
                # int -> float/double
                if isinstance(left.type, ir.IntType) and isinstance(right.type, (ir.FloatType, ir.DoubleType)):
                    left = self.builder.sitofp(left, right.type)
                elif isinstance(right.type, ir.IntType) and isinstance(left.type, (ir.FloatType, ir.DoubleType)):
                    # print(f"changed {right.type} {right} to {left.type}")
                    right = self.builder.sitofp(right, left.type)
                    # print(f"proof: {right} {right.type}")
                # float -> double
                elif isinstance(left.type, ir.FloatType) and isinstance(right.type, ir.DoubleType):
                    left = self.builder.fpext(left, ir.DoubleType())
                elif isinstance(right.type, ir.FloatType) and isinstance(left.type, ir.DoubleType):
                    right = self.builder.fpext(right, ir.DoubleType())
                # double -> float
                elif isinstance(left.type, ir.DoubleType) and isinstance(right.type, ir.FloatType):
                    left = self.builder.fptrunc(left, ir.FloatType())
                elif isinstance(right.type, ir.DoubleType) and isinstance(left.type, ir.FloatType):
                    right = self.builder.fptrunc(right, ir.FloatType())

            op = expr.op

            if isinstance(left.type, ir.FloatType) or isinstance(left.type, ir.DoubleType):
                if op == '+':
                    return self.builder.fadd(left, right)
                elif op == '-':
                    return self.builder.fsub(left, right)
                elif op == '*':
                    return self.builder.fmul(left, right)
                elif op == '/':
                    return self.builder.fdiv(left, right)
            else:
                if op == '+':
                    return self.builder.add(left, right)
                elif op == '-':
                    return self.builder.sub(left, right)
                elif op == '*':
                    return self.builder.mul(left, right)
                elif op == '/':
                    return self.builder.sdiv(left, right)

            if op == '<':
                return self.builder.icmp_signed('<', left, right)
            elif op == '>':
                return self.builder.icmp_signed('>', left, right)
            elif op == '=<':
                return self.builder.icmp_signed('<=', left, right)
            elif op == '>=':
                return self.builder.icmp_signed('>=', left, right)
            elif op == '==':
                return self.builder.icmp_signed('==', left, right)
            elif op == '!=':
                return self.builder.icmp_signed('!=', left, right)

            elif op == 'AND':
                return self.builder.and_(left, right)
            elif op == 'OR':
                return self.builder.or_(left, right)
            elif op == 'XOR':
                return self.builder.xor(left, right)

            raise NotImplementedError(f"Operator '{op}' not handled.")

        elif isinstance(expr, ast.Literal):
            type_ = expr.type_
            # print(expr.value, type_)

            if type_ == Type.INT:
                return ir.Constant(LLVM[type_], int(expr.value))
            elif type_ == Type.FLOAT32:
                return ir.Constant(LLVM[type_], expr.value)
            elif type_ == Type.FLOAT64:
                return ir.Constant(LLVM[type_], float(expr.value))
            elif type_ == Type.BOOL:
                return ir.Constant(LLVM[type_], int(expr.value))

            elif type_ == Type.STRING:
                # Create a global constant string
                strval = expr.value + "\0"
                str_type = ir.ArrayType(ir.IntType(8), len(strval))
                var = ir.GlobalVariable(self.module, str_type, name="str")
                var.global_constant = True
                var.initializer = ir.Constant(str_type, bytearray(strval.encode("utf-8")))
                return self.builder.gep(var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])

