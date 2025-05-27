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
        self.functions = {}  # Store function definitions
        self.current_function = None  # Track the function currently being processed
        self.function_scope_variables = {}  # Variables scoped to each function
        self.struct_types = {}  # Store struct type definitions

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
        # First pass: Declare all structs and functions
        for stmt in tree.statements:
            if isinstance(stmt, ast.StructDeclaration):
                self.declare_struct(stmt)
            elif isinstance(stmt, ast.FunctionDeclaration):
                self.declare_function(stmt)
                
        # Create main function
        main_ty = ir.FunctionType(ir.IntType(32), [])
        self.func = ir.Function(self.module, main_ty, name="main")
        self.functions["main"] = self.func
        
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.declare_printf()
        self.declare_scanf()
        self.declare_fgets()
        self.declare_stdin()
        
        # Save main function's builder
        main_builder = self.builder
        
        # Second pass: Process all statements
        for stmt in tree.statements:
            if isinstance(stmt, ast.FunctionDeclaration):
                self.gen_function_body(stmt)
            else:
                # We're back in main for non-function statements
                self.current_function = self.func
                self.builder = main_builder
                self.gen_stmt(stmt)

        # Make sure we're in main when returning
        self.builder = main_builder
        self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def get_llvm_type(self, type_str):
        """Convert type string to LLVM type"""
        type_map = {
            "integer": Type.INT,
            "boolean": Type.BOOL,
            "single_precision": Type.FLOAT32,
            "double_precision": Type.FLOAT64,
            "text": Type.STRING
        }
        
        # Check if it's a built-in type
        if type_str in type_map:
            return LLVM[type_map[type_str]]
            
        # Check if it's a user-defined struct
        if type_str in self.struct_types:
            return self.struct_types[type_str]['type']
            
        raise ValueError(f"Unknown type: {type_str}")

    def declare_struct(self, struct_decl):
        """First pass: Create struct type definition"""
        # Create a list to hold field types
        field_types = []
        field_names = []

        # Add each field's type
        for field in struct_decl.fields:
            field_type = self.get_llvm_type(field.type_)
            field_types.append(field_type)
            field_names.append(field.name)

        # Create an identified (named) struct type
        struct_type = self.module.context.get_identified_type(struct_decl.name)
        struct_type.set_body(*field_types)

        # Store the struct type and field information for later use
        self.struct_types[struct_decl.name] = {
            'type': struct_type,
            'fields': field_names
        }

        return struct_type


    def declare_function(self, func_decl):
        """First pass: Declare function signature"""
        # Get return type
        return_type = self.get_llvm_type(func_decl.return_type)
        
        # Get parameter types
        param_types = []
        for param in func_decl.parameters:
            param_types.append(self.get_llvm_type(param.type_))
        
        # Create function type
        func_type = ir.FunctionType(return_type, param_types)
        
        # Create function
        func = ir.Function(self.module, func_type, name=func_decl.name)
        
        # Store function for later reference
        self.functions[func_decl.name] = func
        
        # Name parameters
        for i, param in enumerate(func_decl.parameters):
            func.args[i].name = param.name
        
        return func

    def gen_function_body(self, func_decl):
        """Second pass: Generate function body"""
        # Get the already declared function
        func = self.functions[func_decl.name]
        
        # Create function entry block
        block = func.append_basic_block(name="entry")
        
        # Save current state
        old_builder = self.builder
        old_function = self.current_function
        old_variables = self.variables.copy()
        
        # Set new state
        self.builder = ir.IRBuilder(block)
        self.current_function = func
        self.variables = {}  # Clear variables for new function scope
        
        # Allocate and store function parameters
        for i, param in enumerate(func_decl.parameters):
            # Allocate space for parameter
            ptr = self.builder.alloca(func.args[i].type, name=param.name)
            # Store parameter value
            self.builder.store(func.args[i], ptr)
            # Add to variables dictionary
            self.variables[param.name] = ptr
        
        # Generate code for function body
        for stmt in func_decl.body:
            self.gen_stmt(stmt)
            # Check if the last statement was a return - if so, no need to add default return
            if isinstance(stmt, ast.ReturnStatement):
                break
        
        # Add default return if the function block is not terminated (no return statement was found)
        if not self.builder.block.is_terminated:
            # Default return based on function return type
            return_type = func.return_value.type
            if return_type == ir.IntType(32):
                self.builder.ret(ir.Constant(ir.IntType(32), 0))
            elif return_type == ir.FloatType():
                self.builder.ret(ir.Constant(ir.FloatType(), 0.0))
            elif return_type == ir.DoubleType():
                self.builder.ret(ir.Constant(ir.DoubleType(), 0.0))
            elif return_type == ir.IntType(1):
                self.builder.ret(ir.Constant(ir.IntType(1), 0))
            elif return_type == ir.IntType(8).as_pointer():
                null_str = self._string_constant("", "null_str_return")
                self.builder.ret(null_str)
        
        # Restore state
        self.builder = old_builder
        self.current_function = old_function
        self.variables = old_variables

    def gen_stmt(self, stmt):
        assert isinstance(self.builder, ir.IRBuilder)
        # Set debug flag if not present
        if not hasattr(self, 'debug'):
            self.debug = False  # Set to True to enable debug messages

        if isinstance(stmt, ast.Declaration):
            # Regular variable declaration
            llvm_type = self.get_llvm_type(stmt.type_)
            ptr = self.builder.alloca(llvm_type, name=stmt.name)
            self.variables[stmt.name] = ptr

            if stmt.value is not None:
                val = self.gen_expr(stmt.value)
                self.builder.store(val, ptr)

        # Here's the fix for struct variable declarations
        elif isinstance(stmt, ast.StructVarDeclaration):
            struct_info = self.struct_types.get(stmt.struct_type_name)
            if struct_info is None:
                raise RuntimeError(f"Struct type '{stmt.struct_type_name}' not defined")

            llvm_struct_type = struct_info["type"]
            
            # Allocate memory for the struct
            ptr = self.builder.alloca(llvm_struct_type, name=stmt.var_name)
            self.variables[stmt.var_name] = ptr
            
            # Initialize struct fields to default values
            for i, field_name in enumerate(struct_info["fields"]):
                field_type = llvm_struct_type.elements[i]
                field_ptr = self.builder.gep(
                    ptr,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)],
                    name=f"{stmt.var_name}_{field_name}_ptr"
                )
                
                # Initialize with zeros based on field type
                if isinstance(field_type, ir.IntType):
                    self.builder.store(ir.Constant(field_type, 0), field_ptr)
                elif isinstance(field_type, ir.DoubleType):
                    self.builder.store(ir.Constant(field_type, 0.0), field_ptr)
                # Add other type initializations as needed

        elif isinstance(stmt, ast.StructFieldAssignment):
            # Get the struct variable
            struct_var_name = stmt.struct_var.name  # ✅ Get the name of the struct variable
            struct_ptr = self.variables.get(struct_var_name)  # ✅ Then use it to get the LLVM pointer
            if struct_ptr is None:
                raise RuntimeError(f"Undefined struct variable: {struct_var_name}")

            # Get the type of the struct
            struct_type = struct_ptr.type.pointee
            if not isinstance(struct_type, ir.IdentifiedStructType):
                raise RuntimeError(f"Variable '{struct_var_name}' is not a struct")

            struct_name = struct_type.name
            struct_info = self.struct_types.get(struct_name)
            if struct_info is None:
                raise RuntimeError(f"Struct type info for '{struct_name}' not found")

            field_name = stmt.field_name
            if field_name not in struct_info["fields"]:
                raise RuntimeError(f"Struct '{struct_name}' has no field '{field_name}'")

            field_idx = struct_info["fields"].index(field_name)
            field_type = struct_type.elements[field_idx]

            # Generate code to evaluate the value expression
            value = self.gen_expr(stmt.value)

            
            # Ensure value type matches field type
            if value.type != field_type:
                # You might need type conversion here depending on your language semantics
                raise RuntimeError(f"Type mismatch: cannot assign {value.type} to field of type {field_type}")

            # Get pointer to the field
            field_ptr = self.builder.gep(
                struct_ptr,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), field_idx)],
                name=f"{struct_var_name}_{field_name}_ptr"
            )
            
            if self.debug:
                print(f"Storing value to {struct_var_name}.{field_name}")
            
            # Store the value to the field
            self.builder.store(value, field_ptr)

        elif isinstance(stmt, ast.Assignment):
            # Struct field assignment
            if isinstance(stmt.name, ast.StructAccess):
                struct_var_name = stmt.name.struct_var.name
                field_name = stmt.name.field_name

                struct_ptr = self.variables.get(struct_var_name)
                if struct_ptr is None:
                    raise RuntimeError(f"Undefined struct variable: {struct_var_name}")

                # Get the struct type from the pointer
                struct_type = struct_ptr.type.pointee
                if not isinstance(struct_type, ir.IdentifiedStructType):
                    raise RuntimeError(f"Variable '{struct_var_name}' is not a struct")

                struct_name = struct_type.name
                struct_info = self.struct_types.get(struct_name)
                if struct_info is None:
                    raise RuntimeError(f"Struct type info for '{struct_name}' not found")

                if field_name not in struct_info["fields"]:
                    raise RuntimeError(f"Struct '{struct_name}' has no field '{field_name}'")

                field_idx = struct_info["fields"].index(field_name)
                val = self.gen_expr(stmt.value)

                # Get a pointer to the specific field and store value there
                field_ptr = self.builder.gep(
                    struct_ptr,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), field_idx)],
                    name=f"{struct_var_name}_{field_name}_ptr"
                )
                
                # Debug: Print the value being stored
                if self.debug:
                    print(f"Storing value {val} to field {struct_var_name}.{field_name}")
                
                self.builder.store(val, field_ptr)

            else:
                # Regular assignment
                ptr = self.variables.get(stmt.name)
                if ptr is None:
                    raise RuntimeError(f"Variable '{stmt.name}' not declared before assignment")

                val = self.gen_expr(stmt.value)
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
                
        elif isinstance(stmt, ast.FunctionCall):
            # Generate code for function call but discard result
            self.gen_expr(stmt)
            
        # Add this handler for return statements
        elif isinstance(stmt, ast.ReturnStatement):
            # Generate code for the return expression
            return_val = self.gen_expr(stmt.value)
            
            # Get the function's return type
            func_return_type = self.current_function.return_value.type
            
            # Cast the return value to the function's return type if needed
            if return_val.type != func_return_type:
                if isinstance(func_return_type, ir.FloatType) and isinstance(return_val.type, ir.IntType):
                    return_val = self.builder.sitofp(return_val, ir.FloatType())
                elif isinstance(func_return_type, ir.DoubleType) and isinstance(return_val.type, ir.IntType):
                    return_val = self.builder.sitofp(return_val, ir.DoubleType())
                elif isinstance(func_return_type, ir.DoubleType) and isinstance(return_val.type, ir.FloatType):
                    return_val = self.builder.fpext(return_val, ir.DoubleType())
                elif isinstance(func_return_type, ir.IntType) and isinstance(return_val.type, ir.FloatType):
                    return_val = self.builder.fptosi(return_val, ir.IntType(32))
                    
            # Generate the return instruction
            self.builder.ret(return_val)

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

        elif isinstance(expr, ast.FunctionCall):
            # Get the function from the stored functions
            func = self.functions.get(expr.name)
            if func is None:
                raise RuntimeError(f"Undefined function: {expr.name}")
            
            # Generate code for arguments
            args = []
            for arg_expr in expr.arguments:
                arg_val = self.gen_expr(arg_expr)
                args.append(arg_val)
            
            # Check and adjust argument types if needed
            for i, (arg, param_type) in enumerate(zip(args, func.args)):
                if arg.type != param_type.type:
                    # Handle type conversions
                    if isinstance(param_type.type, ir.FloatType) and isinstance(arg.type, ir.IntType):
                        args[i] = self.builder.sitofp(arg, ir.FloatType())
                    elif isinstance(param_type.type, ir.DoubleType) and isinstance(arg.type, ir.IntType):
                        args[i] = self.builder.sitofp(arg, ir.DoubleType())
                    elif isinstance(param_type.type, ir.DoubleType) and isinstance(arg.type, ir.FloatType):
                        args[i] = self.builder.fpext(arg, ir.DoubleType())
                    # Add more conversions as needed
            
            # Call the function
            return self.builder.call(func, args)

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
            
        elif isinstance(expr, ast.StructAccess):
            struct_var_name = expr.struct_var.name
            struct_ptr = self.variables.get(struct_var_name)
            if struct_ptr is None:
                raise RuntimeError(f"Undefined struct variable: {struct_var_name}")

            # Get the type of the struct
            struct_type = struct_ptr.type.pointee
            if not isinstance(struct_type, ir.IdentifiedStructType):
                raise RuntimeError(f"Variable '{struct_var_name}' is not a struct")

            struct_name = struct_type.name
            struct_info = self.struct_types.get(struct_name)
            if struct_info is None:
                raise RuntimeError(f"Struct type info for '{struct_name}' not found")

            field_name = expr.field_name
            if field_name not in struct_info["fields"]:
                raise RuntimeError(f"Struct '{struct_name}' has no field '{field_name}'")

            field_idx = struct_info["fields"].index(field_name)

            # Get pointer to field
            field_ptr = self.builder.gep(
                struct_ptr,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), field_idx)],
                name=f"{struct_var_name}_{field_name}_ptr"
            )
            
            if self.debug:
                print(f"Loading field value from {struct_var_name}.{field_name}")
                
            # Load and return field value
            return self.builder.load(field_ptr, name=f"{struct_var_name}_{field_name}_val")