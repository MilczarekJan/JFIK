class Node:
    pass

class IntNum(Node):
    def __init__(self, value):
        self.value: int = value

class Delcaration(Node):
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
