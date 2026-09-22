from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    left: "Node | None" = None
    right: "Node | None" = None

from collections import deque

def tree_level_order(root):
    if root is None:
        return []
    if not isinstance(root, Node):
        raise ValueError("root must be Node or None")
    queue = deque([root])
    seen = {root}
    result = []
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.value)
            for child in (node.left, node.right):
                if child is None:
                    continue
                if not isinstance(child, Node) or child in seen:
                    raise ValueError("expected a tree without malformed or repeated nodes")
                seen.add(child)
                queue.append(child)
        result.append(level)
    return result
