from type import Type
from llvmlite import ir, binding
import ap_ast as ast

LLVM = {
    Type.INT: ir.IntType(32),
    Type.DOUBLE: ir.DoubleType(),
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
        # self.gen_main()
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
            ptr = self.builder.alloca(ir.IntType(32), name=stmt.name)
            self.builder.store(val, ptr)
            self.variables[stmt.name] = ptr

        elif isinstance(stmt, ast.Assignment):
            val = self.gen_expr(stmt.value)
            ptr = self.variables.get(stmt.name)
            if not ptr:
                raise RuntimeError(f"Variable '{stmt.name}' not declared")
            self.builder.store(val, ptr)

        elif isinstance(stmt, ast.Print):
            val = self.gen_expr(stmt.value)
            fmt_ptr = self.printf_format()
            ptr = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
            self.builder.call(self.printf, [ptr, val])

    def printf_format(self):
        if self.fmt_str:
            return self.fmt_str

        fmt_str = "%d\n\0"
        fmt_bytes = bytearray(fmt_str.encode("utf8"))
        str_type = ir.ArrayType(ir.IntType(8), len(fmt_bytes))

        if "fmt" in self.module.globals:
            return self.module.globals["fmt"]

        global_fmt = ir.GlobalVariable(self.module, str_type, name="fmt")

        global_fmt.linkage = "internal"
        global_fmt.global_constant = True
        global_fmt.initializer = ir.Constant(str_type, fmt_bytes)

        return global_fmt

    def gen_expr(self, expr):
        assert isinstance(self.builder, ir.IRBuilder)

        if isinstance(expr, ast.Literal):
            return ir.Constant(ir.IntType(32), expr.value)

        elif isinstance(expr, ast.Variable):
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
            op = expr.op

            if op == '+':
                return self.builder.add(left, right)
            elif op == '-':
                return self.builder.sub(left, right)
            elif op == '*':
                return self.builder.mul(left, right)
            elif op == '/':
                return self.builder.sdiv(left, right)

            elif op == '<':
                return self.builder.icmp_signed('<', left, right)
            elif op == '>':
                return self.builder.icmp_signed('>', left, right)
            elif op == '<=':
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

            if type_ == Type.INT:
                return ir.Constant(LLVM[type_], expr.value)

            elif type_ == Type.DOUBLE:
                return ir.Constant(LLVM[type_], expr.value)

            elif type_ == Type.BOOL:
                return ir.Constant(LLVM[type_], int(expr.value))

            elif type_ == Type.STRING:
                # Create a global constant string
                strval = expr.value + "\0"
                str_type = ir.ArrayType(ir.IntType(8), len(strval))
                var = ir.GlobalVariable(self.module, str_type, name="str")
                var.global_constant = True
                # var.initializer = ir.Constant(str_type, bytearray(strval.encode("utf-8")))
                return self.builder.gep(var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])

