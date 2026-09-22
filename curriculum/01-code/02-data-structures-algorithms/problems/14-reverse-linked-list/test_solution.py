import unittest
from solution import Node, reverse_list

class ReverseTests(unittest.TestCase):
    def test_identity_and_involution(self):
        for size in [0, 1, 2, 3, 10000]:
            nodes = [Node(7) for _ in range(size)]
            for left, right in zip(nodes, nodes[1:]):
                left.next = right
            head = nodes[0] if nodes else None
            reversed_head = reverse_list(head)
            current = reversed_head
            for expected in reversed(nodes):
                self.assertIs(current, expected)
                current = current.next
            self.assertIsNone(current)
            self.assertIs(reverse_list(reversed_head), head)
            self.assertTrue(all(node.next is (nodes[i+1] if i+1 < size else None)
                                for i, node in enumerate(nodes)))

    def test_invalid_input_is_not_partially_mutated(self):
        a, b, c = Node(1), Node(2), Node(3)
        a.next, b.next, c.next = b, c, b
        with self.assertRaises(ValueError):
            reverse_list(a)
        self.assertIs(a.next, b)
        self.assertIs(b.next, c)
        self.assertIs(c.next, b)
        c.next = 42
        with self.assertRaises(ValueError):
            reverse_list(a)
        self.assertIs(a.next, b)
        self.assertEqual(c.next, 42)
        a.next = a
        with self.assertRaises(ValueError):
            reverse_list(a)
        with self.assertRaises(ValueError):
            reverse_list("bad")

if __name__ == "__main__":
    unittest.main()
