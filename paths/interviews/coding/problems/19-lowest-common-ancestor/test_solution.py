import random
import unittest
from solution import Node, lowest_common_ancestor

class AncestorTests(unittest.TestCase):
    def test_identity_presence_and_depth(self):
        d, b, c = Node(7), Node(7), Node(7)
        b.left = d
        a = Node(7, b, c)
        self.assertIs(lowest_common_ancestor(a, d, b), b)
        self.assertIs(lowest_common_ancestor(a, d, c), a)
        self.assertIs(lowest_common_ancestor(a, d, d), d)
        self.assertIsNone(lowest_common_ancestor(a, d, Node(7)))
        self.assertIsNone(lowest_common_ancestor(None, b, c))
        nodes = [Node(1) for _ in range(5000)]
        for parent, child in zip(nodes, nodes[1:]):
            parent.right = child
        self.assertIs(lowest_common_ancestor(nodes[0], nodes[123], nodes[-1]), nodes[123])

    def test_invalid_structure_even_when_answer_seems_known(self):
        p = Node(1)
        cycle = Node(0)
        cycle.right = cycle
        for root in [Node(0, p, p), Node(0, p, 42), cycle, 42]:
            with self.assertRaises(ValueError):
                lowest_common_ancestor(root, p, p)
        with self.assertRaises(ValueError):
            lowest_common_ancestor(p, None, p)

    def test_root_path_oracle(self):
        rng = random.Random(119)
        for _ in range(50):
            nodes = [Node(7) for _ in range(rng.randrange(1, 25))]
            slots = [(nodes[0], "left"), (nodes[0], "right")]
            for child in nodes[1:]:
                position = rng.randrange(len(slots))
                parent, side = slots.pop(position)
                setattr(parent, side, child)
                slots.extend([(child, "left"), (child, "right")])
            def path(node, target):
                if node is None:
                    return None
                if node is target:
                    return [node]
                for child in (node.left, node.right):
                    found = path(child, target)
                    if found is not None:
                        return [node] + found
                return None
            queries = nodes + [Node(7)]
            for _ in range(30):
                p, q = rng.choice(queries), rng.choice(queries)
                pp, qp = path(nodes[0], p), path(nodes[0], q)
                expected = None
                if pp is not None and qp is not None:
                    for left, right in zip(pp, qp):
                        if left is not right:
                            break
                        expected = left
                self.assertIs(lowest_common_ancestor(nodes[0], p, q), expected)

if __name__ == "__main__":
    unittest.main()
