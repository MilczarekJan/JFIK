import sys

from antlr4 import CommonTokenStream, FileStream, ParseTreeWalker

from errors import APErrorListener
from listener import ASTListener
from llvm import CodeGenerator
from output.AnsiipythoniumLexer import AnsiipythoniumLexer
from output.AnsiipythoniumParser import AnsiipythoniumParser

filename = sys.argv[1]

if __name__ == "__main__":
    stream = FileStream(filename)
    lexer = AnsiipythoniumLexer(stream)

    lexer.removeErrorListeners()
    lexer_err = APErrorListener()
    lexer.addErrorListener(lexer_err)

    tokens = CommonTokenStream(lexer)
    parser = AnsiipythoniumParser(tokens)

    parser.removeErrorListeners()
    parser_err = APErrorListener()
    parser.addErrorListener(parser_err)

    tree = parser.prog()

    if lexer_err.had_error or parser_err.had_error:
        print("Syntax errors. Compilation aborted.")
        sys.exit(1)

    listener = ASTListener()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    codegen = CodeGenerator()
    codegen.generate(listener.ast)

    with open("temp.ll", "w") as f:
        f.write(str(codegen.module))
