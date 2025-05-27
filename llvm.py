from llvmlite import binding, ir

import ap_ast as ast
from type import Type

LLVM = {
    Type.INT: ir.IntType(32),
    Type.FLOAT32: ir.FloatType(),
    Type.FLOAT64: ir.DoubleType(),
    Type.BOOL: ir.IntType(1),
    Type.STRING: ir.IntType(8).as_pointer(),
}


class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="main_module")
        self.builder = None
        self.printf = None
        self.func = None
        self.variables = {}
        self.fmt_str = None
        self.if_count = 0

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

    def declare_scanf(self):
        voidptr = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [voidptr], var_arg=True)
        self.scanf = ir.Function(self.module, scanf_ty, name="scanf")

    def declare_fgets(self):
        char_ptr = ir.IntType(8).as_pointer()
        fgets_ty = ir.FunctionType(char_ptr, [char_ptr, ir.IntType(32), char_ptr])
        self.fgets = ir.Function(self.module, fgets_ty, name="fgets")

    def declare_stdin(self):
        if "stdin" not in self.module.globals:
            stdin = ir.GlobalVariable(
                self.module, ir.IntType(8).as_pointer(), name="stdin"
            )
            stdin.linkage = "external"
            # stdin.initializer = ir.Constant(i8ptr, None)  # null pointer to satisfy llvmlite

    def generate(self, tree):
        main_ty = ir.FunctionType(ir.IntType(32), [])
        self.func = ir.Function(self.module, main_ty, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.declare_printf()
        self.declare_scanf()
        self.declare_fgets()
        self.declare_stdin()

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
                    # val = self.builder.fptrunc(val, ir.FloatType())
                    val = self.builder.sitofp(val, ir.FloatType())
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
            ptr = self.variables.get(stmt.name)
            if ptr is None:
                raise RuntimeError(f"Variable '{stmt.name}' not declared")

            var_type = ptr.type.pointee

            if isinstance(var_type, ir.PointerType):  # STRING (char*)
                buf_len = 256
                buf_type = ir.ArrayType(ir.IntType(8), buf_len)
                buf = self.builder.alloca(buf_type, name=f"{stmt.name}_buf")
                buf_ptr = self.builder.gep(
                    buf,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
                )

                stdin_ptr = self.module.get_global("stdin")
                stdin_val = self.builder.load(stdin_ptr)

                self.builder.call(
                    self.fgets,
                    [buf_ptr, ir.Constant(ir.IntType(32), buf_len), stdin_val],
                )
                self.builder.store(buf_ptr, ptr)

            # BOOL: map 0 to "negative", 1 to "positive"
            elif isinstance(var_type, ir.IntType) and var_type.width == 1:
                str_buf_type = ir.ArrayType(ir.IntType(8), 8)
                str_buf = self.builder.alloca(str_buf_type, name=f"{stmt.name}_buf")
                str_ptr = self.builder.gep(
                    str_buf,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
                )

                # Step 2: Read into buffer using %s
                fmt_ptr = self._scanf_format(LLVM[Type.STRING])
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.scanf, [fmt_cast, str_ptr])

                true_ptr = self._string_constant("positive", name="bool_true_cmp")
                # false_ptr = self._string_constant("negative", name="bool_false_cmp")

                strcmp_ty = ir.FunctionType(
                    ir.IntType(32),
                    [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()],
                )
                strcmp = self.module.globals.get("strcmp")
                if not strcmp:
                    strcmp = ir.Function(self.module, strcmp_ty, name="strcmp")

                result = self.builder.call(strcmp, [str_ptr, true_ptr])
                is_true = self.builder.icmp_signed(
                    "==", result, ir.Constant(ir.IntType(32), 0)
                )

                bool_val = self.builder.zext(is_true, ir.IntType(1))
                self.builder.store(bool_val, ptr)

            else:
                fmt_ptr = self._scanf_format(var_type)
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.scanf, [fmt_cast, ptr])

        elif isinstance(stmt, ast.Print):
            val = self.gen_expr(stmt.value)
            val_type = val.type

            # BOOL: map 0 to "negative", 1 to "positive"
            if isinstance(val_type, ir.IntType) and val_type.width == 1:
                true_str = self._string_constant("positive", "bool_true")
                true_cast = self.builder.bitcast(true_str, ir.IntType(8).as_pointer())
                false_str = self._string_constant("negative", "bool_false")
                false_cast = self.builder.bitcast(false_str, ir.IntType(8).as_pointer())

                is_true = self.builder.icmp_unsigned(
                    "==", val, ir.Constant(ir.IntType(1), 1)
                )
                bool_str = self.builder.select(is_true, true_cast, false_cast)
                fmt_ptr = self._printf_format(ir.IntType(1))
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_cast, bool_str])
            else:
                # llvm can't print floats for some reason and need to be casted to double :(
                if isinstance(val_type, ir.FloatType):
                    val = self.builder.fpext(val, ir.DoubleType())

                fmt_ptr = self._printf_format(val_type)
                fmt_cast = self.builder.bitcast(fmt_ptr, ir.IntType(8).as_pointer())
                self.builder.call(self.printf, [fmt_cast, val])

        elif isinstance(stmt, ast.ForLoop):
            # Initializer
            self.gen_stmt(stmt.var)

            # Create blocks
            assert isinstance(self.func, ir.Function)
            loop_cond_block = self.func.append_basic_block("loop_cond")
            loop_body_block = self.func.append_basic_block("loop_body")
            loop_iter_block = self.func.append_basic_block("loop_iter")
            loop_exit_block = self.func.append_basic_block("loop_exit")

            # Branch to condition first
            self.builder.branch(loop_cond_block)

            # Condition block
            self.builder.position_at_start(loop_cond_block)
            cond_val = self.gen_expr(stmt.cond)

            # Ensure cond_val is boolean (i1)
            if not (isinstance(cond_val.type, ir.IntType) and cond_val.type.width == 1):
                # Convert to boolean if necessary, e.g., compare != 0
                if isinstance(cond_val.type, ir.IntType):
                    zero = ir.Constant(cond_val.type, 0)
                    cond_val = self.builder.icmp_signed("!=", cond_val, zero)
                elif isinstance(cond_val.type, (ir.FloatType, ir.DoubleType)):
                    zero = ir.Constant(cond_val.type, 0.0)
                    cond_val = self.builder.fcmp_ordered("!=", cond_val, zero)
                else:
                    raise RuntimeError("Unsupported condition type in for loop")

            self.builder.cbranch(cond_val, loop_body_block, loop_exit_block)

            # Loop body block
            self.builder.position_at_start(loop_body_block)
            for body_stmt in stmt.body:
                self.gen_stmt(body_stmt)
            self.builder.branch(loop_iter_block)

            # Loop iteration block
            self.builder.position_at_start(loop_iter_block)
            self.gen_stmt(stmt.iter)
            self.builder.branch(loop_cond_block)

            # Loop exit block
            self.builder.position_at_start(loop_exit_block)

        elif isinstance(stmt, ast.If):
            if_id = self.if_count
            self.if_count += 1

            cond_val = self.gen_expr(stmt.cond)

            # Create basic blocks for if-true, else (optional), and merge
            if_true_block = self.builder.append_basic_block(f"if_true_{if_id}")
            merge_block = self.builder.append_basic_block(f"if_merge_{if_id}")

            # Branch on the condition
            if stmt.else_body:
                if_false_block = self.builder.append_basic_block(f"if_false_{if_id}")
                self.builder.cbranch(cond_val, if_true_block, if_false_block)
            else:
                self.builder.cbranch(cond_val, if_true_block, merge_block)

            # Compile the if body
            self.builder.position_at_start(if_true_block)
            for body_stmt in stmt.if_body:
                self.gen_stmt(body_stmt)
            self.builder.branch(merge_block)  # jump to merge block after if body

            # Compile the else body if it exists
            if stmt.else_body:
                self.builder.position_at_start(if_false_block)
                for body_stmt in stmt.else_body:
                    self.gen_stmt(body_stmt)
                self.builder.branch(merge_block)

            # Position builder at the merge block to continue
            self.builder.position_at_start(merge_block)

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

    def _scanf_format(self, type_):
        if isinstance(type_, ir.IntType):
            fmt_str = "%d\0"
            if type_.width == 1:
                name = "scan_bool"
            else:
                name = "scan_int"
        elif isinstance(type_, ir.DoubleType):
            fmt_str = "%lf\0"
            name = "scan_float"
        elif isinstance(type_, ir.FloatType):
            fmt_str = "%f\0"
            name = "scan_double"
        elif (
            isinstance(type_, ir.PointerType)
            and isinstance(type_.pointee, ir.IntType)
            and type_.pointee.width == 8
        ):
            fmt_str = "%s\0"
            name = "scan_str"
        else:
            raise NotImplementedError("Unsupported scanf type: " + str(type_))

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

        ptr = self.builder.gep(
            var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)]
        )
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
            if expr.op == "NOT":
                if isinstance(val.type, ir.IntType) and val.type.width == 1:
                    return self.builder.xor(val, ir.Constant(ir.IntType(1), 1))
            raise NotImplementedError(f"Unary operator {expr.op}")

        elif isinstance(expr, ast.BinaryOp):
            left = self.gen_expr(expr.left)
            right = self.gen_expr(expr.right)

            # Change types if nessesery
            if left.type != right.type:
                # int -> float/double
                if isinstance(left.type, ir.IntType) and isinstance(
                    right.type, (ir.FloatType, ir.DoubleType)
                ):
                    left = self.builder.sitofp(left, right.type)
                elif isinstance(right.type, ir.IntType) and isinstance(
                    left.type, (ir.FloatType, ir.DoubleType)
                ):
                    right = self.builder.sitofp(right, left.type)
                # float -> double
                elif isinstance(left.type, ir.FloatType) and isinstance(
                    right.type, ir.DoubleType
                ):
                    left = self.builder.fpext(left, ir.DoubleType())
                elif isinstance(right.type, ir.FloatType) and isinstance(
                    left.type, ir.DoubleType
                ):
                    right = self.builder.fpext(right, ir.DoubleType())
                # double -> float
                # elif isinstance(left.type, ir.DoubleType) and isinstance(right.type, ir.FloatType):
                #    left = self.builder.fptrunc(left, ir.FloatType())
                # elif isinstance(right.type, ir.DoubleType) and isinstance(left.type, ir.FloatType):
                #    right = self.builder.fptrunc(right, ir.FloatType())

            op = expr.op

            if isinstance(left.type, ir.FloatType) or isinstance(
                left.type, ir.DoubleType
            ):
                if op == "+":
                    return self.builder.fadd(left, right)
                elif op == "-":
                    return self.builder.fsub(left, right)
                elif op == "*":
                    return self.builder.fmul(left, right)
                elif op == "/":
                    return self.builder.fdiv(left, right)
            else:
                if op == "+":
                    return self.builder.add(left, right)
                elif op == "-":
                    return self.builder.sub(left, right)
                elif op == "*":
                    return self.builder.mul(left, right)
                elif op == "/":
                    return self.builder.sdiv(left, right)

            if op == "<":
                return self.builder.icmp_signed("<", left, right)
            elif op == ">":
                return self.builder.icmp_signed(">", left, right)
            elif op == "=<":
                return self.builder.icmp_signed("<=", left, right)
            elif op == ">=":
                return self.builder.icmp_signed(">=", left, right)
            elif op == "==":
                return self.builder.icmp_signed("==", left, right)
            elif op == "!=":
                return self.builder.icmp_signed("!=", left, right)

            elif op == "AND":
                return self.builder.and_(left, right)
            elif op == "OR":
                return self.builder.or_(left, right)
            elif op == "XOR":
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
                name = f"str_{abs(hash(expr.value)) % 100_000}"  # names must be unique
                var = ir.GlobalVariable(self.module, str_type, name=name)
                var.global_constant = True
                var.initializer = ir.Constant(
                    str_type, bytearray(strval.encode("utf-8"))
                )
                return self.builder.gep(
                    var,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
                )
