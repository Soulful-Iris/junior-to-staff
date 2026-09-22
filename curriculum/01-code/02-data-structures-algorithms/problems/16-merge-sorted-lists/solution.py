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

def _validate(head):
    slow = fast = head
    while fast is not None:
        fast = _next(_next(fast))
        slow = _next(slow)
        if fast is not None and slow is fast:
            raise ValueError("chains must be acyclic")
    current, tail, previous_value = head, None, None
    while current is not None:
        if type(current.value) is not int:
            raise ValueError("values must be integers")
        if previous_value is not None and previous_value > current.value:
            raise ValueError("chains must be nondecreasing")
        previous_value = current.value
        tail, current = current, current.next
    return tail

def merge_sorted_lists(first, second):
    first_tail, second_tail = _validate(first), _validate(second)
    if first_tail is not None and first_tail is second_tail:
        raise ValueError("chains must not share nodes")
    dummy = Node(0)
    tail = dummy
    while first is not None and second is not None:
        if first.value <= second.value:
            chosen, first = first, first.next
        else:
            chosen, second = second, second.next
        tail.next = chosen
        tail = chosen
    tail.next = first if first is not None else second
    return dummy.next
