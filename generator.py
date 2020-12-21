import bpy

from nodes_for_python.system import as_node, GroupNode, GroupInputNode, GroupOutputNode

class NodeGenerator:
    
    def generate(self, nodes, material, replace = True):
        nodes = self.__to_nodes(nodes)
        material = self.__get_material(material, replace)
        real_nodes = self.__generate_node_tree(nodes, material.node_tree)
        return material

    def generate_group(self, nodes, group):
        nodes = self.__to_nodes(nodes)
        group = self.__get_group(group)
        real_nodes = self.__generate_node_tree(nodes, group)
        return group

    def __to_nodes(self, nodes):
        if isinstance(nodes, set) or isinstance(nodes, list):
            nodes = set(as_node(n) for n in nodes)
        else:
            nodes = set((as_node(nodes),))

        parents = set(n for n in nodes)
        while parents:
            parents = set(a for p in parents for a in p.get_input_nodes() if a not in nodes)
            nodes.update(parents)

        return nodes

    def __get_material(self, material, replace):
        if isinstance(material, bpy.types.Material):
            material = material.name
        
        if material in bpy.data.materials:
            material = bpy.data.materials[material]
            if replace:
                material.node_tree.nodes.clear()
        else:
            material = bpy.data.materials.new(material)
            material.use_nodes = True
            material.node_tree.nodes.clear()
    
        return material

    def __get_group(self, group):
        if isinstance(group, bpy.types.ShaderNodeTree):
            group = group.name
        
        if group in bpy.data.node_groups:
            group = bpy.data.node_groups[group]
            group.nodes.clear()
        else:
            group = bpy.data.node_groups.new(group, 'ShaderNodeTree')
        
        group.inputs.clear()
        group.outputs.clear()

        return group
        
    def __generate_node_tree(self, nodes, node_tree):
        links = [i.link for n in nodes for i in n.inputs if i.link]
        
        nodes_to_real_nodes = dict()
        for node in nodes:
            real_node = self.__make_real_node(node, node_tree)
            nodes_to_real_nodes[node] = real_node

        for link in links:
            input = link.input
            output = link.output
            input_node = nodes_to_real_nodes[input.node]
            output_node = nodes_to_real_nodes[output.node]
            real_input = input_node.inputs[input.template.index]
            real_output = output_node.outputs[output.template.index]
            node_tree.links.new(real_input, real_output)
        
        return nodes_to_real_nodes.values()

    def __group_io(self, template, io):
        socket = io.new("NodeSocket" + template.type, template.identifier)
        if template.default_value is not None:
            print(template.type, template.identifier, template.default_value)
            socket.default_value = template.default_value
        if template.min_value is not None:
            socket.min_value = template.min_value
        if template.max_value is not None:
            socket.max_value = template.max_value

    def __make_real_node(self, node, node_tree):
        real_node = node_tree.nodes.new(node.class_name)

        if isinstance(node, GroupInputNode):
            for o in node.outputs:
                self.__group_io(o.template, node_tree.inputs)
        elif isinstance(node, GroupOutputNode):
            for i in node.inputs:
                self.__group_io(i.template, node_tree.outputs)
        else:

            for prop in node.own_props:
                try:
                    value = getattr(node, prop)
                    setattr(real_node, prop, value)
                except:
                    pass

            for ri, i in zip(real_node.inputs, node.inputs):
                if i.value is not None:
                    ri.default_value = self.__checked_value(i, i.value)
            for ro, o in zip(real_node.outputs, node.outputs):
                if o.value is not None:
                    ro.default_value = self.__checked_value(o, o.value)

            if isinstance(node, GroupNode):
                real_node.node_tree = node.group

        return real_node

    def __checked_value(self, input, value):
        if input.template.type == 'RGBA':
            return self.__tuple(value, 4)
        elif input.template.type == 'VECTOR':
            return self.__tuple(value, 3)
        elif input.template.type == 'STRING':
            return str(value)
        elif input.template.type == 'VALUE':
            return value
        else:
            return value

    def __tuple(self, value, dim):
        if isinstance(value, list) or isinstance(value, tuple):
            return value[:dim]
        else:
            return [value] * dim

