from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    left: "Node | None" = None
    right: "Node | None" = None

def lowest_common_ancestor(root, p, q):
    if not isinstance(p, Node) or not isinstance(q, Node):
        raise ValueError("queries must be Node references")
    if root is None:
        return None
    stack = [(root, False)]
    seen, states = set(), {}
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
        left_mask, left_candidate = states.get(node.left, (0, None))
        right_mask, right_candidate = states.get(node.right, (0, None))
        mask = left_mask | right_mask | (1 if node is p else 0) | (2 if node is q else 0)
        candidate = left_candidate if left_candidate is not None else right_candidate
        if candidate is None and mask == 3:
            candidate = node
        states[node] = mask, candidate
    mask, candidate = states[root]
    return candidate if mask == 3 else None
