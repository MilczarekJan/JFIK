from output.AnsiipythoniumListener import AnsiipythoniumListener
from output.AnsiipythoniumParser import AnsiipythoniumParser
import ap_ast as ast

class ASTListener(AnsiipythoniumListener):

    def __init__(self):
        self.stack = []
        self.ast = []

    def exitProg(self, ctx: AnsiipythoniumParser.ProgContext):
        self.ast = self.stack.copy()

    def exitVar_ass(self, ctx: AnsiipythoniumParser.Var_assContext):
        name = ctx.ID().getText()
        value = int(ctx.expr().getText())
        self.stack.append(ast.Assignment(name, value))

    def exitVar_decl(self, ctx: AnsiipythoniumParser.Var_declContext):
        type_ = ctx.type_().getText()
        name = ctx.ID().getText()
        value = int(ctx.expr().getText())
        self.stack.append(ast.Declaration(type_, name, value))

    def exitPrint(self, ctx: AnsiipythoniumParser.PrintContext):
        value = ctx.expr().getText()
        self.stack.append(ast.Print(value))

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

    def exitAddexpr(self, ctx):
        self._build_binary_expr(ctx, "minusexpr")

    def exitMultexpr(self, ctx):
        self._build_binary_expr(ctx, "addexpr")

    def exitCompexpr(self, ctx):
        if len(ctx.multexpr()) == 1:
            return
        right = self.stack.pop()
        left = self.stack.pop()
        op = ctx.getChild(1).getText()
        self.stack.append(ast.BinaryOp(left, op, right))

    def exitAndexpr(self, ctx):
        if len(ctx.notexpr()) == 1:
            return
        right = self.stack.pop()
        left = self.stack.pop()
        self.stack.append(ast.BinaryOp(left, "AND", right))

    def exitXorexpr(self, ctx):
        if ctx.XOR():
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(ast.BinaryOp(left, "XOR", right))

    def exitOrexpr(self, ctx):
        if len(ctx.xorexpr()) == 1:
            return
        rights = [self.stack.pop() for _ in range(len(ctx.xorexpr()) - 1)]
        left = self.stack.pop()
        # flatten ORs into a left-associative tree
        expr = left
        for right in reversed(rights):
            expr = ast.BinaryOp(expr, "OR", right)
        self.stack.append(expr)

    def exitNotexpr(self, ctx):
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

