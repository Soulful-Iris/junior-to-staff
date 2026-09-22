import random
import unittest
from solution import Node, validate_bst

class BSTTests(unittest.TestCase):
    def test_ancestor_bounds_and_empty(self):
        self.assertTrue(validate_bst(None))
        self.assertTrue(validate_bst(Node(2, Node(1), Node(3))))
        self.assertFalse(validate_bst(Node(10, Node(5), Node(15, Node(6), Node(20)))))
        self.assertFalse(validate_bst(Node(2, Node(2))))
        self.assertTrue(validate_bst(Node(0, Node(-(10**100)), Node(10**100))))
        deep = None
        for value in reversed(range(5000)):
            deep = Node(value, right=deep)
        self.assertTrue(validate_bst(deep))

    def test_structural_errors_even_after_order_failure(self):
        shared = Node(2)
        cycle = Node(1)
        cycle.left = cycle
        for root in [Node(True), Node(2, Node(4), 42), Node(1, shared, shared), cycle, 42]:
            with self.assertRaises(ValueError):
                validate_bst(root)

    def test_inorder_oracle(self):
        rng = random.Random(118)
        def build(depth):
            if depth == 0 or rng.random() < .3:
                return None
            return Node(rng.randrange(-10, 11), build(depth - 1), build(depth - 1))
        def inorder(node):
            return [] if node is None else inorder(node.left) + [node.value] + inorder(node.right)
        for _ in range(400):
            root = build(5)
            values = inorder(root)
            expected = all(a < b for a, b in zip(values, values[1:]))
            self.assertEqual(validate_bst(root), expected)

if __name__ == "__main__":
    unittest.main()
