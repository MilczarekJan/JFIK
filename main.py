from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker
from output.AnsiipythoniumLexer import AnsiipythoniumLexer
from output.AnsiipythoniumParser import AnsiipythoniumParser
from listener import ASTListener
from llvm import CodeGenerator

# for debuging
from pprint import pprint

filename = './tests/01_assign_print_declare'

if __name__ == "__main__":
    stream = FileStream(filename)
    lexer = AnsiipythoniumLexer(stream)
    tokens = CommonTokenStream(lexer)
    parser = AnsiipythoniumParser(tokens)
    tree = parser.prog()
    # print("tree")
    # pprint(vars(tree))

    listener = ASTListener()
    walker = ParseTreeWalker()

    walker.walk(listener, tree)
    # print("listener 2")
    # pprint(vars(listener))
    # print("tree 2")
    # pprint(vars(tree))

    codegen = CodeGenerator()
    codegen.generate(listener.ast)
    print(codegen.module)

