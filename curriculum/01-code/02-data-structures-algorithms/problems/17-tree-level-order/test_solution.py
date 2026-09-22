import random
import unittest
from solution import Node, tree_level_order

class LevelTests(unittest.TestCase):
    def test_examples_depth_and_identity(self):
        root = Node("a", Node("b", right=Node("d")), Node("c"))
        self.assertEqual(tree_level_order(root), [["a"], ["b", "c"], ["d"]])
        self.assertEqual(tree_level_order(Node(0, Node("x"), Node("x"))), [[0], ["x", "x"]])
        self.assertEqual(tree_level_order(None), [])
        deep = None
        for i in reversed(range(3000)):
            deep = Node(i, right=deep)
        self.assertEqual(tree_level_order(deep), [[i] for i in range(3000)])

    def test_reject_graphs_and_malformed_links(self):
        child = Node(1)
        for root in [42, Node(0, left=42), Node(0, child, child)]:
            with self.assertRaises(ValueError):
                tree_level_order(root)
        root = Node(0)
        root.left = root
        with self.assertRaises(ValueError):
            tree_level_order(root)
        self.assertIs(root.left, root)

    def test_dfs_depth_oracle(self):
        rng = random.Random(117)
        def build(depth):
            if depth == 0 or rng.random() < .25:
                return None
            return Node(rng.randrange(4), build(depth - 1), build(depth - 1))
        def visit(node, depth, levels):
            if node is None:
                return
            if depth == len(levels):
                levels.append([])
            levels[depth].append(node.value)
            visit(node.left, depth + 1, levels)
            visit(node.right, depth + 1, levels)
        for _ in range(200):
            root = build(6)
            expected = []
            visit(root, 0, expected)
            self.assertEqual(tree_level_order(root), expected)

if __name__ == "__main__":
    unittest.main()
