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


# New ReturnStatement AST node
class ReturnStatement(Node):
    def __init__(self, value):
        self.value = value


# AST nodes for function support
class FunctionDeclaration(Node):
    def __init__(self, return_type, name, parameters, body):
        self.return_type = return_type
        self.name = name
        self.parameters = parameters  # List of Parameter objects
        self.body = body  # List of statements


class Parameter(Node):
    def __init__(self, type_, name):
        self.type_ = type_
        self.name = name


class FunctionCall(Node):
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments  # List of expressions


class StructDeclaration(Node):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields  # List of Field objects


class StructVarDeclaration(Node):
    def __init__(self, struct_type_name, var_name):
        self.struct_type_name = struct_type_name
        self.var_name = var_name


class Field(Node):
    def __init__(self, type_, name):
        self.type_ = type_
        self.name = name


class StructAccess(Node):
    def __init__(self, struct_var, field_name):
        self.struct_var = struct_var  # Variable representing a struct
        self.field_name = field_name  # Name of the field to access


class StructFieldAssignment:
    def __init__(self, struct_var, field_name, value):
        self.struct_var = struct_var  # This is a Variable reference
        self.field_name = field_name
        self.value = value