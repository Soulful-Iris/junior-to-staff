from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    left: "Node | None" = None
    right: "Node | None" = None

def validate_bst(root):
    stack = [(root, None, None)] if root is not None else []
    visited_nodes = set()
    is_bst = True
    while stack:
        node, lower, upper = stack.pop()
        if not isinstance(node, Node) or node in visited_nodes or type(node.value) is not int:
            raise ValueError("expected an integer-valued tree without repeated nodes")
        visited_nodes.add(node)
        value = node.value
        if (lower is not None and value <= lower) or (upper is not None and value >= upper):
            is_bst = False
        if node.right is not None:
            stack.append((node.right, value, upper))
        if node.left is not None:
            stack.append((node.left, lower, value))
    return is_bst
