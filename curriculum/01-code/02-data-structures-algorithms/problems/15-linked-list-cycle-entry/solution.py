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

def cycle_entry(head):
    slow = fast = head
    while fast is not None:
        slow = _next(slow)
        fast = _next(_next(fast))
        if fast is not None and slow is fast:
            seeker = head
            while seeker is not slow:
                seeker = _next(seeker)
                slow = _next(slow)
            return seeker
    return None
