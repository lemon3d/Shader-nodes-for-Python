import bpy
import inspect

from nodes_for_python.nodes import *
from nodes_for_python.utils import *

def get_node_input_templates(node):
    result = []
    for index, node_input in enumerate(node.inputs):
        identifier = node_input.name
        name = python_name(identifier)
        input_type = node_input.type
        default_value = node_input.default_value if hasattr(node_input, "default_value") else None
        template = NodeInputTemplate(index, name, identifier, input_type, default_value)
        result.append(template)
        
    unique_names(result)
    return result

def get_node_output_templates(node):
    result = []
    for index, node_output in enumerate(node.outputs):
        identifier = node_output.name
        name = python_name(identifier)
        output_type = node_output.type
        default_value = node_output.default_value if hasattr(node_output, "default_value") else None            
        template = NodeOutputTemplate(index, name, identifier, output_type, default_value)
        result.append(template)
        
    unique_names(result)
    return result

def python_name(name):
    return name.lower().replace(' ', '_')

class GroupNode(BaseNode):
    def __init__(self, node_system, group):
        if isinstance(group, str):
            group = bpy.data.node_groups[group]
        if not isinstance(group, bpy.types.ShaderNodeTree):
            return None
        
        self.group = group

        self.input_templates = get_node_input_templates(group)
        self.output_templates = get_node_output_templates(group)
        self.node_system = node_system
        self.class_name = "ShaderNodeGroup"
        self.own_props = dict()
        
        BaseNode.__init__(self)

class GroupInputNode(BaseNode):
    def __init__(self, node_system):
        self.class_name = "NodeGroupInput"
        self.name = "GroupInput"
        self.own_props = dict()
        self.input_templates = []
        self.output_templates = []
        self.inputs = []
        self.outputs = []
        self.node_system = node_system
        
        BaseNode.__init__(self)

    def add_output(self, identifier, type, default_value = None, min_value = None, max_value = None):
        """
        Adds an output to this group input node.
        identifier = name of this output (string)
        type = data type from the available socket type. See https://docs.blender.org/api/current/search.html?q=nodesocket. 
        Only provide the type suffix as parameter (eg, 'Color' if NodeSocketColor).
        default_value = the default value for this socket
        min_value = the minimum value for this socket
        max_value = the maximum value for this socket
        """
        index = len(self.outputs)
        name = python_name(identifier)
        template = NodeOutputTemplate(index, name, identifier, type, default_value)
        template.min_value = min_value
        template.max_value = max_value
        output = NodeOutput(self, template)
        self.outputs.append(output)
        self.__dict__[template.o_name] = output
        self.__dict__[template.name] = output

class GroupOutputNode(BaseNode):
    def __init__(self, node_system):
        self.class_name = "NodeGroupOutput"
        self.name = "GroupOutput"
        self.own_props = dict()
        self.input_templates = []
        self.output_templates = []
        self.inputs = []
        self.outputs = []
        self.node_system = node_system

        BaseNode.__init__(self)

    def add_input(self, identifier, type, default_value = None, min_value = None, max_value = None):
        """
        Adds an input to this group output node.
        identifier = name of this output (string)
        type = data type from the available socket type. See https://docs.blender.org/api/current/search.html?q=nodesocket. 
        Only provide the type suffix as parameter (eg, 'Color' if NodeSocketColor).
        default_value = the default value for this socket
        min_value = the minimum value for this socket
        max_value = the maximum value for this socket
        """
        index = len(self.inputs)
        name = python_name(identifier)
        template = NodeInputTemplate(index, name, identifier, type, default_value)
        template.min_value = min_value
        template.max_value = max_value
        input = NodeInput(self, template)
        self.inputs.append(input)
        self.__dict__[template.i_name] = input

class FrameNode(BaseNode):
    def __init__(self, node_system):
        self.class_name = "NodeFrame"
        self.name = "Frame"
        self.own_props = dict()
        self.input_templates = []
        self.output_templates = []
        self.inputs = []
        self.outputs = []
        self.node_system = node_system
        self.text = ""

        BaseNode.__init__(self)

class NodeSystem:

    def __init__(self):
        self.__initialize()
            
    def __initialize(self):
        shader_names = get_shader_names()

        sample_tree = bpy.data.node_groups.new("samples", 'ShaderNodeTree')
        sample_nodes = sample_tree.nodes
        for name in sorted(shader_names):
            try:
                if name == "ShaderNodeGroup":
                    pass
                else:
                    sample_nodes.new(name)
            except:
                pass

        fresnel = sample_nodes['Fresnel']
        fresnel_props = get_properties(fresnel)
        
        for node in sample_nodes:
            node_class = self.__initialize_node(fresnel_props, node)
            
        bpy.data.node_groups.remove(sample_tree)
        
    def __initialize_node(self, base_props, node):
        own_props = get_own_properties(base_props, node)
        if "label" not in own_props: own_props["label"] = None

        class_name = node.__class__.__name__
        name = class_name.replace("ShaderNode", "", 1)

        props = {}
        for k, v in own_props.items(): props[k] = v

        node_class = type(name, (BaseNode, ), props)
        setattr(self, name, node_class)

        node_class.class_name = class_name
        node_class.own_props = own_props
        node_class.input_templates = get_node_input_templates(node)
        node_class.output_templates = get_node_output_templates(node)
        node_class.node_system = self
        
        def __init__(self, **kwargs):
            BaseNode.__init__(self)
            for k, v in kwargs.items():
                getattr(self, k)
                setattr(self, k, v)
        
        node_class.__init__ = __init__

        self.__make_doc(node_class)

        return node_class
    
    def __make_doc(self, node_class):
        keys = sorted(node_class.own_props.keys())
        params = ", ".join(keys)
        doc = f"NodeSystem.{node_class.__name__}({params})\n"
        for k in keys:
            doc += f"    {k} = default value {node_class.own_props[k]}\n"
        node_class.__doc__ = f"""{doc}"""

    def Group(self, group):
        """
        Creates and returns a group node from the given group or group name
        """
        return GroupNode(self, group)
            
    def GroupInput(self):
        """
        Creates and returns a group input node
        """
        return GroupInputNode(self)
    
    def GroupOutput(self):
        """
        Creates and returns a group output node
        """
        return GroupOutputNode(self)

    def vector_math(self, operation, v1, v2 = None, v3 = None, v4 = None):
        """
        Creates and returns a VectorMath node.
        operation = operation type from the available ones. See https://docs.blender.org/api/current/bpy.types.ShaderNodeVectorMath.html.
        v1 = value for the first input (either a tuple(3) or a node or a node output).
        v2 = value for the second input (either a tuple(3) or a node or a node output).
        v3 = value for the third input (either a tuple(3) or a node or a node output).
        v4 = value for the fourth input (either a tuple(3) or a node or a node output).
        """
        result = self.VectorMath()
        result.operation = operation
        result.i0 = as_output(v1)
        if v2 is not None:
            result.i1 = as_output(v2)
        if v3 is not None:
            result.i2 = as_output(v3)
        if v4 is not None:
            result.i3 = as_output(v4)
        return result

    def vector_add(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 + v2.
        """
        return self.vector_math('ADD', v1, v2).outputs[0]

    def vector_substract(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 - v2.
        """
        return self.vector_math('SUBTRACT', v1, v2).outputs[0]

    def vector_multiply(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 * v2 when v2 is a vector.
        """
        return self.vector_math('MULTIPLY', v1, v2).outputs[0]

    def vector_divide(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 / v2.
        """
        return self.vector_math('DIVIDE', v1, v2).outputs[0]

    def vector_cross_product(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 ^ v2.
        """
        return self.vector_math('CROSS_PRODUCT', v1, v2).outputs[0]

    def vector_project(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 // v2.
        """
        return self.vector_math('PROJECT', v1, v2).outputs[0]

    def vector_reflect(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 | v2.
        """
        return self.vector_math('REFLECT', v1, v2).outputs[0]

    def vector_dot_product(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 @ v2.
        """
        return self.vector_math('DOT_PRODUCT', v1, v2).outputs[1]

    def vector_distance(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('DISTANCE', v1, v2).outputs[1]

    def vector_length(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('LENGTH', v).outputs[1]

    def vector_scale(self, v, s):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 * v2 when v2 is a value.
        """
        return self.vector_math('SCALE', v, v4=s).outputs[0]

    def vector_normalize(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('NORMALIZE', v).outputs[0]

    def vector_absolute(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to abs(v).
        """
        return self.vector_math('ABSOLUTE', v).outputs[0]

    def vector_minimum(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('MINIMUM', v1, v2).outputs[0]

    def vector_maximum(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('MAXIMUM', v1, v2).outputs[0]

    def vector_floor(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('FLOOR', v).outputs[0]

    def vector_ceil(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('CEIL', v).outputs[0]

    def vector_fraction(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('FRACT', v).outputs[0]

    def vector_modulo(self, v1, v2):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        Equivalent to v1 % v2.
        """
        return self.vector_math('MODULO', v1, v2).outputs[0]

    def vector_wrap(self, v1, v2, v3):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('WRAP', v1, v2, v3).outputs[0]

    def vector_snap(self, v1, v2, v3):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('SNAP', v1, v2).outputs[0]

    def vector_sine(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('SINE', v).outputs[0]

    def vector_cosine(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('COSINE', v).outputs[0]

    def vector_tangent(self, v):
        """
        Creates a VectorMath node and returns the corresponding output slot.
        """
        return self.vector_math('TANGENT', v).outputs[0]

    def vector_sum(self, vs):
        """
        Creates a node tree part that is the sum of the given entries.
        vs = a tuple or array of nodes or node outputs.
        """
        if len(vs) == 0:
            return None
        elif len(vs) == 1:
            return vs[0]
        else:
            a = self.vector_add(vs[0], vs[1])
            for v in vs[2:]:
                a = self.vector_add(a,v)
            return a

    def math(self, operation, v1, v2 = None, v3 = None):
        """
        Creates and returns a Math node.
        operation = operation type from the available ones. See https://docs.blender.org/api/current/bpy.types.ShaderNodeMath.html.
        v1 = value for the first input (either a value or a node or a node output).
        v2 = value for the second input (either a value or a node or a node output).
        v3 = value for the third input (either a value or a node or a node output).
        """
        result = self.Math()
        result.operation = operation
        result.i0 = as_output(v1)
        if v2 is not None:
            result.i1 = as_output(v2)
        if v3 is not None:
            result.i2 = as_output(v3)
        return result

    def math_add(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 + v2.
        """
        return self.math('ADD', v1, v2).outputs[0]

    def math_substract(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 - v2.
        """
        return self.math('SUBTRACT', v1, v2).outputs[0]

    def math_multiply(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 * v2.
        """
        return self.math('MULTIPLY', v1, v2).outputs[0]

    def math_divide(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 / v2.
        """
        return self.math('DIVIDE', v1, v2).outputs[0]

    def math_multiply_add(self, v1, v2, v3):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('MUTIPLY_ADD', v1, v2, v3).outputs[0]

    def math_power(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 ** v2.
        """
        return self.math('POWER', v1, v2).outputs[0]

    def math_logarithm(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('LOGARITHM', v1, v2).outputs[0]

    def math_square_root(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SQRT', v).outputs[0]

    def math_inverse_square_root(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 ** v2.
        """
        return self.math('INVERSE_SQRT', v).outputs[0]

    def math_absolute(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to abs(v).
        """
        return self.math('ABSOLUTE', v).outputs[0]

    def math_exponent(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('EXPONENT', v).outputs[0]

    def math_minimum(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('MINIMUM', v1, v2).outputs[0]

    def math_maximum(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('MAXIMUM', v1, v2).outputs[0]

    def math_greater_than(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 > v2.
        """
        return self.math('GREATER_THAN', v1, v2).outputs[0]

    def math_less_than(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 < v2.
        """
        return self.math('LESS_THAN', v1, v2).outputs[0]

    def math_sign(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SIGN', v).outputs[0]

    def math_compare(self, v1, v2, v3):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('COMPARE', v1, v2, v3).outputs[0]

    def math_smooth_min(self, v1, v2, v3):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SMOOTH_MIN', v1, v2, v3).outputs[0]

    def math_smooth_max(self, v1, v2, v3):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SMOOTH_MAX', v1, v2, v3).outputs[0]

    def math_round(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('ROUND', v).outputs[0]

    def math_floor(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('FLOOR', v).outputs[0]

    def math_ceil(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('CEIL', v).outputs[0]

    def math_truncate(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('TRUNC', v).outputs[0]

    def math_fraction(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('FRACT', v).outputs[0]

    def math_modulo(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        Equivalent to v1 % v2.
        """
        return self.math('MODULO', v1, v2).outputs[0]

    def math_wrap(self, v1, v2, v3):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('WRAP', v1, v2, v3).outputs[0]

    def math_snap(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SNAP', v1, v2).outputs[0]

    def math_ping_pong(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('PINGPONG', v1, v2).outputs[0]

    def math_sine(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SINE', v).outputs[0]

    def math_cosine(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('COSINE', v).outputs[0]

    def math_tangent(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('TANGENT', v).outputs[0]

    def math_arcsin(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('ARCSINE', v).outputs[0]

    def math_arccosin(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('ARCCOSINE', v).outputs[0]

    def math_arctangent(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('ARCTANGENT', v).outputs[0]

    def math_arctan2(self, v1, v2):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('ARCTAN2', v1, v2).outputs[0]

    def math_hyperbolic_sine(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('SINH', v).outputs[0]

    def math_hyperbolic_cosine(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('COSH', v).outputs[0]

    def math_hyperbolic_tangent(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('TANH', v).outputs[0]

    def math_to_radians(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('RADIANS', v).outputs[0]

    def math_to_degrees(self, v):
        """
        Creates a Math node and returns the corresponding output slot.
        """
        return self.math('DEGREES', v).outputs[0]

    def __combine(self, comb, abc):
        if is_numeric(abc) or isinstance(abc, BaseNode) or isinstance(abc, NodeOutput):
            comb.i0 = abc
            comb.i1 = abc
            comb.i2 = abc
        else :
            comb.i0 = abc[0]
            comb.i1 = abc[1]
            comb.i2 = abc[2]
        return comb
    
    def combine_xyz(self, xyz):
        """
        Creates and returns a CombineXYZ node.
        """
        return self.__combine(self.CombineXYZ(), xyz)

    def combine_hsv(self, hsv):
        """
        Creates and returns a CombineHSV node.
        """
        return self.__combine(self.CombineHSV(), hsv)

    def combine_rgb(self, rgb):
        """
        Creates and returns a CombineRGB node.
        """
        return self.__combine(self.CombineRGB(), rgb)

    def value(self, v):
        """
        Creates and returns a Value node.
        """
        node = self.Value()
        node.o0.value = v
        return node

    def rgb(self, rgba):
        """
        Creates and returns a RGB node.
        """
        node = self.RGB()
        node.o0.value = rgba
        return node

    def frame(self, name, text, nodes):
        frame = FrameNode(self)
        for n in nodes: as_node(n).frame = frame
        return frame

    def frame_all(self, name, text, nodes):
        return self.frame(name, text, get_all_ancestors(as_node(n) for n in nodes))

