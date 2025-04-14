from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from output.AnsiipythoniumLexer import AnsiipythoniumLexer
from output.AnsiipythoniumParser import AnsiipythoniumParser
from listener import ASTListener
from llvm import CodeGenerator

import sys

filename = sys.argv[1]

if __name__ == "__main__":
    stream = FileStream(filename)
    lexer = AnsiipythoniumLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = AnsiipythoniumParser(tokens)
    tree = parser.prog()
    listener = ASTListener()
    walker = ParseTreeWalker()

    walker.walk(listener, tree)

    codegen = CodeGenerator()
    codegen.generate(listener.ast)
    print(codegen.module)

