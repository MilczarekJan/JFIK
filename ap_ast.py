class Node:
    pass


class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class Declaration(Node):
    def __init__(self, type_, name, value):
        self.type_ = type_
        self.name = name
        self.value = value


class Assignment(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class Print(Node):
    def __init__(self, value):
        self.value = value


class Read(Node):
    def __init__(self, name):
        self.name = name


class Variable(Node):
    def __init__(self, name):
        self.name = name


class BinaryOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class Literal(Node):
    def __init__(self, value, type_):
        self.value = value
        self.type_ = type_


class ForLoop(Node):
    def __init__(self, var, cond, iter, body):
        self.var = var
        self.cond = cond
        self.iter = iter
        self.body = body
