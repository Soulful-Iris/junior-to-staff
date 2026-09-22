import itertools
import unittest
from solution import Node, merge_sorted_lists

def chain(values):
    nodes = [Node(value) for value in values]
    for left, right in zip(nodes, nodes[1:]):
        left.next = right
    return nodes

class MergeListTests(unittest.TestCase):
    def test_stable_identity_oracle(self):
        sequences = [values for n in range(4)
                     for values in itertools.combinations_with_replacement(range(3), n)]
        for left in sequences:
            for right in sequences:
                a, b = chain(left), chain(right)
                expected = sorted(a + b, key=lambda node: node.value)
                current = merge_sorted_lists(a[0] if a else None, b[0] if b else None)
                for node in expected:
                    self.assertIs(current, node)
                    current = current.next
                self.assertIsNone(current)

    def test_rejection_precedes_mutation(self):
        tail = Node(3)
        a, b = Node(1, tail), Node(2, tail)
        with self.assertRaises(ValueError):
            merge_sorted_lists(a, b)
        self.assertIs(a.next, tail)
        self.assertIs(b.next, tail)
        for bad in [Node(2, Node(1)), Node(True), Node(1, 42), 42]:
            with self.assertRaises(ValueError):
                merge_sorted_lists(a, bad)
            self.assertIs(a.next, tail)
        cycle = Node(1)
        cycle.next = cycle
        with self.assertRaises(ValueError):
            merge_sorted_lists(a, cycle)
        self.assertIs(cycle.next, cycle)

    def test_deep_chain(self):
        nodes = chain(range(10000))
        self.assertIs(merge_sorted_lists(None, nodes[0]), nodes[0])

if __name__ == "__main__":
    unittest.main()
