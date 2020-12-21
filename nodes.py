import bpy

from nodes_for_python.utils import *

def as_output(x):
    return x.o0 if isinstance(x, BaseNode) else x

def as_node(x):
    return x.node if isinstance(x, NodeIO) else x

class NodeIOTemplate:
    def __init__(self, index, name, identifier, type, default_value):
        self.index = index
        self.name = name
        self.identifier = identifier
        self.type = type
        self.default_value = default_value
        self.min_value = None
        self.max_value = None

class NodeInputTemplate(NodeIOTemplate):
    
    def __init__(self, index, name, identifier, type, default_value):
        super().__init__(index, name, identifier, type, default_value)
        self.i_name = "i" + str(index)

    def __str__(self):
        return 'InputTemplate(name='+self.name+')'

class NodeOutputTemplate(NodeIOTemplate):
    
    def __init__(self, index, name, identifier, type, default_value):
        super().__init__(index, name, identifier, type, default_value)
        self.o_name = "o" + str(index)

    def __str__(self):
        return 'OutputTemplate(name='+self.name+')'

    def is_vector_type(self):
        return self.type == 'VECTOR' or self.type == 'RGBA'

    def is_numeric_type(self):
        return self.type == 'VALUE'

class NodeLink:
    def __init__(self, input, output):
        self.input = input
        self.output = output

class NodeIO:
    def __init__(self, node, template):
        self.node = node
        self.template = template
        self.value = None

class NodeInput(NodeIO):
    
    def __init__(self, node, template):
        super().__init__(node, template)
        self.link = None

    def __str__(self):
        return 'Input('+self.template.name+'/'+str(self.value)+')'
        
    def set_value(self, value):
        if isinstance(value, NodeOutput) or isinstance(value, BaseNode):
            self.__remove_link()
            self.__add_link(as_output(value))
        else:
            self.value = value
                
    def __remove_link(self):
        if self.link:
            links = self.link.output.links
            self.link.output.links = [l for l in links if l.input is not self]

    def __add_link(self, output):
        self.link = NodeLink(self, output)
        output.links.append(self.link)

class NodeOutput(NodeIO):
    
    def __init__(self, node, template):
        super().__init__(node, template)
        self.links = []

    def __str__(self):
        return 'Output('+self.template.name+')'

    def __add__(self, other):
        ns = self.node.node_system
        
        if self.template.is_vector_type():
            return ns.vector_add(self, other)
        else:
            return ns.math_add(self, other)

    def __radd__(self, other):
        return self + other
    
    def __sub__(self, other):
        ns = self.node.node_system
        
        if self.template.is_vector_type():
            return ns.vector_substract(self, other)
        else:
            return ns.math_substract(self, other)

    def __rsub__(self, other):
        return (self * -1) + other
    
    def __mul__(self, other):
        ns = self.node.node_system

        if is_numeric(other):
            if self.template.is_vector_type():
                return ns.vector_scale(self, other)
            else:
                return ns.math_multiply(self, other)
        else:
            if self.template.is_vector_type():
                return ns.vector_multiply(self, other)
            else:
                return ns.math_multiply(self, other)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        ns = self.node.node_system
        
        if self.template.is_vector_type():
            return ns.vector_divide(self, other)
        else:
            return ns.math_divide(self, other)

    def __matmul__(self, other):
        ns = self.node.node_system        
        return ns.vector_dot_product(self, other)

    def __xor__(self, other):
        ns = self.node.node_system        
        return ns.vector_cross_product(self, other)

    def __floordiv__(self, other):
        ns = self.node.node_system        
        return ns.vector_project(self, other)

    def __or__(self, other):
        ns = self.node.node_system        
        return ns.vector_reflect(self, other)

    def __gt__(self, other):
        ns = self.node.node_system        
        other = as_output(other)
        if is_numeric(other):
            if self.template.is_vector_type():
                return ns.vector_length(self) > other
            else:
                return ns.math_greater_than(self, other)
        else:
            if self.template.is_vector_type() and other.template.is_vector_type():
                return ns.vector_length(self) > ns.vector_length(other)
            elif self.template.is_vector_type():
                return ns.vector_length(self) > other
            elif other.template.is_vector_type():
                return self > ns.vector_length(other)
            else:
                return ns.math_greater_than(self, other)

    def __lt__(self, other):
        ns = self.node.node_system        
        other = as_output(other)
        if is_numeric(other):
            if self.template.is_vector_type():
                return ns.vector_length(self) < other
            else:
                return ns.math_less_than(self, other)
        else:
            if self.template.is_vector_type() and other.template.is_vector_type():
                return ns.vector_length(self) < ns.vector_length(other)
            elif self.template.is_vector_type():
                return ns.vector_length(self) < other
            elif other.template.is_vector_type():
                return self < ns.vector_length(other)
            else:
                return ns.math_less_than(self, other)

    def __mod__(self, other):
        ns = self.node.node_system
        if self.template.is_vector_type():
            return ns.vector_modulo(self, other)
        else:
            return ns.math_modulo(self, other)

    def __neg__(self):
        return self * -1

    def __abs__(self):
        ns = self.node.node_system        
        if self.template.is_vector_type():
            return ns.vector_absolute(self)
        else:
            return ns.math_absolute(self)

    def __pow__(self, other):
        ns = self.node.node_system        
        return ns.math_power(self, other)

class BaseNode:    
    def __init__(self):
        self.inputs = [NodeInput(self, t) for t in self.input_templates]
        self.outputs = [NodeOutput(self, t) for t in self.output_templates]

        for i in self.inputs:
            self.__dict__[i.template.i_name] = i

        for o in self.outputs:
            self.__dict__[o.template.o_name] = o
            self.__dict__[o.template.name] = o

        self.frame = None

    def __setattr__(self, name, value):
        if getattr(self, "inputs", None):
            for i in self.inputs:
                if i.template.name == name or i.template.i_name == name:
                    i.set_value(value)
                    return

        self.__dict__[name] = value

    def __str__(self):
        return self.__class__.__name__
    
    def get_input_nodes(self):
        return [i.link.output.node for i in self.inputs if i.link]

    def __first_output(self):
        return self.o0

    def __add__(self, other):
        return self.__first_output() + other

    def __radd__(self, other):
        return self.__first_output() + other

    def __sub__(self, other):
        return self.__first_output() - other

    def __rsub__(self, other):
        return other - self.__first_output()

    def __mul__(self, other):
        return self.__first_output() * other

    def __rmul__(self, other):
        return self.__first_output() * other

    def __truediv__(self, other):
        return self.__first_output() / other

    def __matmul__(self, other):
        return self.__first_output() * other

    def __xor__(self, other):
        return self.__first_output() | other

    def __floordiv__(self, other):
        return self.__first_output() // other

    def __or__(self, other):
        return self.__first_output() | other

    def __gt__(self, other):
        return self.__first_output() > other

    def __lt__(self, other):
        return self.__first_output() < other

    def __mod__(self, other):
        return self.__first_output() % other

    def __neg__(self):
        return - self.__first_output()

    def __abs__(self):
        return abs(self.__first_output())

    def __pow__(self, other):
        return self.__first_output() ** other
