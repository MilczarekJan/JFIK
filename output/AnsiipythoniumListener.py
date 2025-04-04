# Generated from Ansiipythonium.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .AnsiipythoniumParser import AnsiipythoniumParser
else:
    from AnsiipythoniumParser import AnsiipythoniumParser

# This class defines a complete listener for a parse tree produced by AnsiipythoniumParser.
class AnsiipythoniumListener(ParseTreeListener):

    # Enter a parse tree produced by AnsiipythoniumParser#prog.
    def enterProg(self, ctx:AnsiipythoniumParser.ProgContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#prog.
    def exitProg(self, ctx:AnsiipythoniumParser.ProgContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#expr.
    def enterExpr(self, ctx:AnsiipythoniumParser.ExprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#expr.
    def exitExpr(self, ctx:AnsiipythoniumParser.ExprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#orexpr.
    def enterOrexpr(self, ctx:AnsiipythoniumParser.OrexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#orexpr.
    def exitOrexpr(self, ctx:AnsiipythoniumParser.OrexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#xorexpr.
    def enterXorexpr(self, ctx:AnsiipythoniumParser.XorexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#xorexpr.
    def exitXorexpr(self, ctx:AnsiipythoniumParser.XorexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#andexpr.
    def enterAndexpr(self, ctx:AnsiipythoniumParser.AndexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#andexpr.
    def exitAndexpr(self, ctx:AnsiipythoniumParser.AndexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#notexpr.
    def enterNotexpr(self, ctx:AnsiipythoniumParser.NotexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#notexpr.
    def exitNotexpr(self, ctx:AnsiipythoniumParser.NotexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#compexpr.
    def enterCompexpr(self, ctx:AnsiipythoniumParser.CompexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#compexpr.
    def exitCompexpr(self, ctx:AnsiipythoniumParser.CompexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#multexpr.
    def enterMultexpr(self, ctx:AnsiipythoniumParser.MultexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#multexpr.
    def exitMultexpr(self, ctx:AnsiipythoniumParser.MultexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#addexpr.
    def enterAddexpr(self, ctx:AnsiipythoniumParser.AddexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#addexpr.
    def exitAddexpr(self, ctx:AnsiipythoniumParser.AddexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#minusexpr.
    def enterMinusexpr(self, ctx:AnsiipythoniumParser.MinusexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#minusexpr.
    def exitMinusexpr(self, ctx:AnsiipythoniumParser.MinusexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#powexpr.
    def enterPowexpr(self, ctx:AnsiipythoniumParser.PowexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#powexpr.
    def exitPowexpr(self, ctx:AnsiipythoniumParser.PowexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#primaryexpr.
    def enterPrimaryexpr(self, ctx:AnsiipythoniumParser.PrimaryexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#primaryexpr.
    def exitPrimaryexpr(self, ctx:AnsiipythoniumParser.PrimaryexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#funcallexpr.
    def enterFuncallexpr(self, ctx:AnsiipythoniumParser.FuncallexprContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#funcallexpr.
    def exitFuncallexpr(self, ctx:AnsiipythoniumParser.FuncallexprContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#literal.
    def enterLiteral(self, ctx:AnsiipythoniumParser.LiteralContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#literal.
    def exitLiteral(self, ctx:AnsiipythoniumParser.LiteralContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#statement.
    def enterStatement(self, ctx:AnsiipythoniumParser.StatementContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#statement.
    def exitStatement(self, ctx:AnsiipythoniumParser.StatementContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#var_decl.
    def enterVar_decl(self, ctx:AnsiipythoniumParser.Var_declContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#var_decl.
    def exitVar_decl(self, ctx:AnsiipythoniumParser.Var_declContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#var_ass.
    def enterVar_ass(self, ctx:AnsiipythoniumParser.Var_assContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#var_ass.
    def exitVar_ass(self, ctx:AnsiipythoniumParser.Var_assContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#if_statement.
    def enterIf_statement(self, ctx:AnsiipythoniumParser.If_statementContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#if_statement.
    def exitIf_statement(self, ctx:AnsiipythoniumParser.If_statementContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#for_statement.
    def enterFor_statement(self, ctx:AnsiipythoniumParser.For_statementContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#for_statement.
    def exitFor_statement(self, ctx:AnsiipythoniumParser.For_statementContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#stat_block.
    def enterStat_block(self, ctx:AnsiipythoniumParser.Stat_blockContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#stat_block.
    def exitStat_block(self, ctx:AnsiipythoniumParser.Stat_blockContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#fun_decl.
    def enterFun_decl(self, ctx:AnsiipythoniumParser.Fun_declContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#fun_decl.
    def exitFun_decl(self, ctx:AnsiipythoniumParser.Fun_declContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#arg_decl.
    def enterArg_decl(self, ctx:AnsiipythoniumParser.Arg_declContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#arg_decl.
    def exitArg_decl(self, ctx:AnsiipythoniumParser.Arg_declContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#class_decl.
    def enterClass_decl(self, ctx:AnsiipythoniumParser.Class_declContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#class_decl.
    def exitClass_decl(self, ctx:AnsiipythoniumParser.Class_declContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#struct_decl.
    def enterStruct_decl(self, ctx:AnsiipythoniumParser.Struct_declContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#struct_decl.
    def exitStruct_decl(self, ctx:AnsiipythoniumParser.Struct_declContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#field.
    def enterField(self, ctx:AnsiipythoniumParser.FieldContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#field.
    def exitField(self, ctx:AnsiipythoniumParser.FieldContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#print.
    def enterPrint(self, ctx:AnsiipythoniumParser.PrintContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#print.
    def exitPrint(self, ctx:AnsiipythoniumParser.PrintContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#read.
    def enterRead(self, ctx:AnsiipythoniumParser.ReadContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#read.
    def exitRead(self, ctx:AnsiipythoniumParser.ReadContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#type.
    def enterType(self, ctx:AnsiipythoniumParser.TypeContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#type.
    def exitType(self, ctx:AnsiipythoniumParser.TypeContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#type_identifier.
    def enterType_identifier(self, ctx:AnsiipythoniumParser.Type_identifierContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#type_identifier.
    def exitType_identifier(self, ctx:AnsiipythoniumParser.Type_identifierContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#matrix_identifier.
    def enterMatrix_identifier(self, ctx:AnsiipythoniumParser.Matrix_identifierContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#matrix_identifier.
    def exitMatrix_identifier(self, ctx:AnsiipythoniumParser.Matrix_identifierContext):
        pass


    # Enter a parse tree produced by AnsiipythoniumParser#vector_identifier.
    def enterVector_identifier(self, ctx:AnsiipythoniumParser.Vector_identifierContext):
        pass

    # Exit a parse tree produced by AnsiipythoniumParser#vector_identifier.
    def exitVector_identifier(self, ctx:AnsiipythoniumParser.Vector_identifierContext):
        pass



del AnsiipythoniumParser