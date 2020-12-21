import bpy
import inspect

def get_shader_names():
    return [s.__name__ for s in bpy.types.ShaderNode.__subclasses__()]    

def get_properties(node):
    return dict(inspect.getmembers(node))

def get_own_properties(parent_props, node):
    return {name: value for name, value in inspect.getmembers(node) if name not in parent_props}

def get_input_types(node):
    result = set()
    if hasattr(node,"inputs"):
        for i in range(len(node.inputs)):
            result.add(node.input_template(i).type)
    return result

def get_output_types(node):
    result = set()
    if hasattr(node,"outputs"):
        for i in range(len(node.outputs)):
            result.add(node.output_template(i).type)
    return result

def unique_names(templates):
    counts = {}
    for t in templates:
        if t.name in counts:
            prev = counts[t.name]
            counts[t.name] = (prev[0]+1,1)
        else:
            counts[t.name] = (1, 1)
    for t in templates:
        prev = counts[t.name]
        if prev[0] > 1:
            index = prev[1]
            counts[t.name] = (prev[0], index+1)
            t.name = t.name + str(index)

def is_numeric(value):
    return isinstance(value, int) or isinstance(value, float)

def is_vector_type(self):
    return self.template.type == 'VECTOR' or self.template.type == 'RGBA'

def is_numeric_type(self):
    return self.template.type == 'VALUE'

def get_all_ancestors(nodes):
    collect = set(nodes)
    while nodes:
        nodes = set(i.node for n in nodes for i in n.inputs if i.node not in collect)
        collect.update(nodes)
    return collect
