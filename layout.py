import bpy
from mathutils import Vector
from collections import defaultdict

def _get_nodes(nodes):
    if isinstance(nodes, bpy.types.Material):
        return nodes.node_tree.nodes
    if isinstance(nodes, bpy.types.ShaderNodeTree):
        return nodes.nodes
    return nodes

class NodeLayout:
    
    def layout(self, nodes, hidden = False, hidden_size = False):
        
        nodes = _get_nodes(nodes)

        for n in nodes: n.hide = hidden
        
        cols = {n:0 for n in nodes}
        
        all_placed = False
        while not all_placed:
            all_placed = True
            for n in nodes:
                col_min = self.__min_col(cols, n)
                if cols[n] >= col_min:
                    cols[n] = col_min - 1
                    all_placed = False

        by_col = defaultdict(list)
        for n, col in cols.items():
            by_col[col].append(n)

        cols = sorted(by_col.keys(), reverse=True)

        widths = [50 + max(n.width for n in by_col[c]) for c in cols]
        x = widths[0]
        for i, c in enumerate(cols):
            x -= widths[i]
            for n in by_col[c]: n.location.x = x
            
        for col in cols:
            col_nodes = by_col[col]
            col_indices = [self.__avg_input_index(n) for n in col_nodes]
            indices = [i for i in range(len(col_nodes))]
            indices = sorted(indices, key=lambda i: col_indices[i])
            y = 0
            for i in indices:
                node = col_nodes[i]
                node.location.y = y
                delta = 100 if hidden and hidden_size else (2 * node.height + 100)
                y = node.location.y - delta

        for col in cols:
            col_nodes = by_col[col]
            height = abs(sum(n.location.y for n in col_nodes) / len(col_nodes))
            for n in col_nodes:
                n.location.y += height
            
    def layout2(self, nodes, hidden = False, hidden_size = False):
        
        for n in nodes: n.hide = hidden
        
        cols = {n:0 for n in nodes}
        
        all_placed = False
        while not all_placed:
            all_placed = True
            for n in nodes:
                col_min = self.__min_col(cols, n)
                if cols[n] >= col_min:
                    cols[n] = col_min - 1
                    all_placed = False

        by_col = defaultdict(list)
        for n, col in cols.items():
            by_col[col].append(n)

        cols = sorted(by_col.keys(), reverse=True)

        widths = [50 + max(n.width for n in by_col[c]) for c in cols]
        x = widths[0]
        for i, c in enumerate(cols):
            x -= widths[i]
            for n in by_col[c]: n.location.x = x
            
        for col in cols:
            col_nodes = by_col[col]
            col_indices = [self.__avg_input_index(n) for n in col_nodes]
            indices = [i for i in range(len(col_nodes))]
            indices = sorted(indices, key=lambda i: col_indices[i])
            y = 0
            for i in indices:
                node = col_nodes[i]
                node.location.y = y
                delta = 100 if hidden and hidden_size else (2 * node.height + 100)
                y = node.location.y - delta

        for col in cols:
            col_nodes = by_col[col]
            height = abs(sum(n.location.y for n in col_nodes) / len(col_nodes))
            for n in col_nodes:
                n.location.y += height
            
    def __no_ouputs(self, node):
        return sum(len(o.links) for o in node.outputs) == 0

    def __min_output_x(self, node):
        return min((l.to_node.location.x for o in node.outputs for l in o.links), default=0)

    def __min_col(self, cols, node):
        return min((cols[l.to_node] for o in node.outputs for l in o.links), default=0)

    def __avg_input_index(self, node):
        indices = [l.to_socket.getIndex() for o in node.outputs for l in o.links]
        return sum(indices) / len(indices) if indices else 0
        
