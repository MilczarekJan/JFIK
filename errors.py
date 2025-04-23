from antlr4.error.ErrorListener import ErrorListener

class APErrorListener(ErrorListener):
    def __init__(self):
        super(APErrorListener, self).__init__()
        self.had_error = False

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.had_error = True
        print(f"[Syntax Error] line {line}:{column} - {msg}")

