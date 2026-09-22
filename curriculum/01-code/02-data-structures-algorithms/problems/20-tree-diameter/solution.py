from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    left: "Node | None" = None
    right: "Node | None" = None

def tree_diameter(root):
    if root is None:
        return 0
    stack = [(root, False)]
    seen, heights = set(), {}
    best = 0
    while stack:
        node, expanded = stack.pop()
        if not expanded:
            if not isinstance(node, Node) or node in seen:
                raise ValueError("expected a tree without malformed or repeated nodes")
            seen.add(node)
            stack.append((node, True))
            if node.right is not None:
                stack.append((node.right, False))
            if node.left is not None:
                stack.append((node.left, False))
            continue
        left = heights.get(node.left, 0)
        right = heights.get(node.right, 0)
        heights[node] = 1 + max(left, right)
        best = max(best, left + right)
    return best
