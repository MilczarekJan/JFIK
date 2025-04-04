from output.AnsiipythoniumListener import AnsiipythoniumListener
from output.AnsiipythoniumParser import AnsiipythoniumParser
import ap_ast

class ASTLitener(AnsiipythoniumListener):

    def __init__(self):
        self.stack = []
        self.ast = []

    def exitVar_ass(self, ctx: AnsiipythoniumParser.Var_assContext):
        name = str(ctx.ID().getText())
        value = int(ctx.expr().getText())
        self.stack.append(ap_ast.Assignment(name, value))

    def exitVar_decl(self, ctx: AnsiipythoniumParser.Var_declContext):
        type_ = str(ctx.type_().getText())
        name = str(ctx.ID().getText())
        value = int(ctx.expr().getText())
        self.stack.append(ap_ast.Delcaration(type_, name, value))

