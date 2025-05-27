import ap_ast as ast
from output.AnsiipythoniumListener import AnsiipythoniumListener
from output.AnsiipythoniumParser import AnsiipythoniumParser
from type import Type


class ASTListener(AnsiipythoniumListener):

    def __init__(self):
        self.stack = []
        self.ast = []
        self.struct_types = set()

    def exitProg(self, ctx: AnsiipythoniumParser.ProgContext):
        self.ast = ast.Program(self.stack.copy())

    def exitVar_ass(self, ctx: AnsiipythoniumParser.Var_assContext):
        name = ctx.ID().getText()
        value = self.stack.pop()
        self.stack.append(ast.Assignment(name, value))

    def exitVar_decl(self, ctx: AnsiipythoniumParser.Var_declContext):
        type_ = ctx.type_().getText()
        name = ctx.ID().getText()
        value = self.stack.pop()
        if type_ == "single_precision":
            value.type_ = Type.FLOAT32
        self.stack.append(ast.Declaration(type_, name, value))

    def exitPrint(self, ctx: AnsiipythoniumParser.PrintContext):
        value = self.stack.pop()
        self.stack.append(ast.Print(value))

    def exitRead(self, ctx: AnsiipythoniumParser.ReadContext):
        self.stack.append(ast.Read(ctx.ID().getText()))

    # Add this method to handle return statements
    def exitReturn_statement(self, ctx: AnsiipythoniumParser.Return_statementContext):
        value = self.stack.pop()
        self.stack.append(ast.ReturnStatement(value))

    def exitPrimaryexpr(self, ctx: AnsiipythoniumParser.PrimaryexprContext):
        if ctx.literal():
            pass
        elif ctx.funcallexpr():
            pass
        elif ctx.expr():
            inner_expr = self.stack.pop()
            self.stack.append(inner_expr)

    def exitFuncallexpr(self, ctx: AnsiipythoniumParser.FuncallexprContext):
        # Get function name
        func_name = ctx.ID().getText()

        # Get arguments
        args = []
        for i in range(len(ctx.expr())):
            args.insert(0, self.stack.pop())  # Pop in reverse order

        # Create function call node
        self.stack.append(ast.FunctionCall(func_name, args))

    def exitStatement(self, ctx: AnsiipythoniumParser.StatementContext):
        if ctx.expr():
            self.stack.pop()

    def exitExpr(self, ctx: AnsiipythoniumParser.ExprContext):
        if ctx.getChildCount() == 1:
            pass

    def exitAddexpr(self, ctx: AnsiipythoniumParser.AddexprContext):
        self._build_binary_expr(ctx, "multexpr")

    def exitMultexpr(self, ctx: AnsiipythoniumParser.MultexprContext):
        self._build_binary_expr(ctx, "minusexpr")

    def exitCompexpr(self, ctx: AnsiipythoniumParser.CompexprContext):
        if len(ctx.addexpr()) == 1:
            return
        right = self.stack.pop()
        left = self.stack.pop()
        op = ctx.getChild(1).getText()
        self.stack.append(ast.BinaryOp(left, op, right))

    def exitAndexpr(self, ctx: AnsiipythoniumParser.AndexprContext):
        if len(ctx.notexpr()) == 1:
            return
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(ast.BinaryOp(left, "AND", right))

    def exitXorexpr(self, ctx: AnsiipythoniumParser.XorexprContext):
        if ctx.XOR():
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(ast.BinaryOp(left, "XOR", right))

    def exitOrexpr(self, ctx: AnsiipythoniumParser.OrexprContext):
        if len(ctx.xorexpr()) == 1:
            return
        rights = [self.stack.pop() for _ in range(len(ctx.xorexpr()) - 1)]
        left = self.stack.pop()
        # flatten ORs into a left-associative tree
        expr = left
        for right in reversed(rights):
            expr = ast.BinaryOp(expr, "OR", right)
        self.stack.append(expr)

    def exitNotexpr(self, ctx: AnsiipythoniumParser.NotexprContext):
        if ctx.NOT():
            operand = self.stack.pop()
            self.stack.append(ast.UnaryOp("NOT", operand))

    def exitFun_decl(self, ctx: AnsiipythoniumParser.Fun_declContext):
        # Get return type
        return_type = ctx.type_().getText()

        # Get function name
        func_name = ctx.ID().getText()

        # Get parameters
        parameters = []
        for arg_ctx in ctx.arg_decl():
            param_type = arg_ctx.type_().getText()
            param_name = arg_ctx.ID().getText()
            parameters.append(ast.Parameter(param_type, param_name))

        # Get function body
        stat_block = ctx.stat_block()
        body = []
        # We need to pop statements in reverse order
        for _ in range(len(stat_block.statement())):
            if self.stack:  # Check if stack is not empty
                body.insert(0, self.stack.pop())

        # Create function declaration node
        self.stack.append(
            ast.FunctionDeclaration(return_type, func_name, parameters, body)
        )

    def _build_binary_expr(self, ctx, rule_name, node_cls=ast.BinaryOp):
        children = getattr(ctx, rule_name)()
        if len(children) == 1:
            return  # single child, already on stack

        right = self.stack.pop()
        left = self.stack.pop()
        op = ctx.getChild(1).getText()
        self.stack.append(node_cls(left, op, right))

    def exitLiteral(self, ctx: AnsiipythoniumParser.LiteralContext):
        if ctx.INT():
            val = int(ctx.INT().getText())
            self.stack.append(ast.Literal(val, Type.INT))

        elif ctx.DOUBLE():
            val = float(ctx.DOUBLE().getText())
            self.stack.append(ast.Literal(val, Type.FLOAT64))

        elif ctx.TRUE():
            self.stack.append(ast.Literal(True, Type.BOOL))

        elif ctx.FALSE():
            self.stack.append(ast.Literal(False, Type.BOOL))

        elif ctx.STRING():
            raw = ctx.STRING().getText()
            val = raw[1:-1].replace('\\"', '"')  # remove quotes
            self.stack.append(ast.Literal(val, Type.STRING))

        elif ctx.ID():
            self.stack.append(ast.Variable(ctx.ID().getText()))

    def exitFor_statement(self, ctx: AnsiipythoniumParser.For_statementContext):
        body_stmts = self.stack.pop()
        iter_expr = self.stack.pop()
        cond_expr = self.stack.pop()
        init_stmt = self.stack.pop()

        loop = ast.ForLoop(init_stmt, cond_expr, iter_expr, body_stmts)
        self.stack.append(loop)

    def exitType_identifier(self, ctx: AnsiipythoniumParser.Type_identifierContext):
        pass

    def exitStruct_decl(self, ctx: AnsiipythoniumParser.Struct_declContext):
        # Get structure name
        struct_name = ctx.ID().getText()
        self.struct_types.add(struct_name)  # <== Track it
        # Get fields
        fields = []
        for field_ctx in ctx.field():
            field_type = field_ctx.type_().getText()
            field_name = field_ctx.ID().getText()
            fields.append(ast.Field(field_type, field_name))
            # print("Field declared:", field_type)  # DEBUG
        # Create structure declaration node
        self.stack.append(ast.StructDeclaration(struct_name, fields))

    def exitStruct_access(self, ctx: AnsiipythoniumParser.Struct_accessContext):
        # Get the variable ID and field name
        var_name = ctx.ID(0).getText()
        field_name = ctx.ID(1).getText()

        # Create a variable reference node for the struct
        struct_var = ast.Variable(var_name)

        # Create the struct access node
        self.stack.append(ast.StructAccess(struct_var, field_name))

    def exitStruct_field_ass(self, ctx: AnsiipythoniumParser.Struct_field_assContext):
        # Get the value to assign (should be on top of the stack)
        value = self.stack.pop()

        # Get the struct_access node (will have object and field information)
        struct_access = self.stack.pop()

        # Create a StructFieldAssignment AST node and push it onto the stack
        self.stack.append(
            ast.StructFieldAssignment(
                struct_access.struct_var, struct_access.field_name, value
            )
        )

    def exitStructVar_decl(self, ctx: AnsiipythoniumParser.Struct_field_assContext):
        # Extract the struct type name (e.g., "Person") and the variable name (e.g., "janek")
        struct_type_name = ctx.struct_access().ID(0).getText()  # Type name
        var_name = ctx.struct_access().ID(1).getText()  # Variable name
        var_value = self.stack.pop()

        # Create a StructVarDeclaration AST node and push it on the stack
        self.stack.append(
            ast.StructVarDeclaration(struct_type_name, var_name, var_value)
        )

    def exitIf_statement(self, ctx: AnsiipythoniumParser.If_statementContext):
        else_body = None
        if len(ctx.stat_block()) == 2:
            else_body = self.stack.pop()
        if_body = self.stack.pop()
        cond = self.stack.pop()

        node = ast.If(cond, if_body, else_body)
        self.stack.append(node)

    def exitStat_block(self, ctx: AnsiipythoniumParser.Stat_blockContext):
        body = []
        for _ in ctx.statement():
            body.append(self.stack.pop())
        body.reverse()
        self.stack.append(body)
