import ap_ast as ast
from output.AnsiipythoniumListener import AnsiipythoniumListener
from output.AnsiipythoniumParser import AnsiipythoniumParser
from type import Type


class ASTListener(AnsiipythoniumListener):

    def __init__(self):
        self.stack = []
        self.ast = []

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
            # print("s_p")
            value.type_ = Type.FLOAT32
        self.stack.append(ast.Declaration(type_, name, value))

    def exitPrint(self, ctx: AnsiipythoniumParser.PrintContext):
        value = self.stack.pop()
        self.stack.append(ast.Print(value))

    def exitRead(self, ctx: AnsiipythoniumParser.ReadContext):
        self.stack.append(ast.Read(ctx.ID().getText()))

    def exitPrimaryexpr(self, ctx: AnsiipythoniumParser.PrimaryexprContext):
        if ctx.literal():
            pass
        elif ctx.funcallexpr():
            pass
        elif ctx.expr():
            inner_expr = self.stack.pop()
            self.stack.append(inner_expr)

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
            # It's not a literal, it's a variable
            self.stack.append(ast.Variable(ctx.ID().getText()))

    def exitType(self, ctx: AnsiipythoniumParser.TypeContext):
        pass

    def exitType_identifier(self, ctx: AnsiipythoniumParser.Type_identifierContext):
        pass
