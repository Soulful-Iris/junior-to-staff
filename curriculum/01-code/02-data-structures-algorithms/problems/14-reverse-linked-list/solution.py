from dataclasses import dataclass

@dataclass(eq=False)
class Node:
    value: object
    next: "Node | None" = None

def _next(node):
    if node is None:
        return None
    if not isinstance(node, Node) or (node.next is not None and not isinstance(node.next, Node)):
        raise ValueError("links must be Node objects or None")
    return node.next

def reverse_list(head):
    slow = fast = head
    while fast is not None:
        fast = _next(_next(fast))
        slow = _next(slow)
        if fast is not None and slow is fast:
            raise ValueError("input must be acyclic")
    previous, current = None, head
    while current is not None:
        following = current.next
        current.next = previous
        previous, current = current, following
    return previous
