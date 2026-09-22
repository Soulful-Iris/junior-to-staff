import random
import unittest
from collections import deque
from solution import Node, tree_diameter

class DiameterTests(unittest.TestCase):
    def test_units_and_deep_chain(self):
        self.assertEqual(tree_diameter(None), 0)
        self.assertEqual(tree_diameter(Node(1)), 0)
        root = Node("a", Node("b", Node("d"), Node("e")), Node("c"))
        self.assertEqual(tree_diameter(root), 3)
        chain = None
        for _ in range(5000):
            chain = Node(7, chain)
        self.assertEqual(tree_diameter(chain), 4999)
        # Diameter is entirely below root, so root-height alone is insufficient.
        fork = Node(0, Node(0, Node(0, Node(0))), Node(0, right=Node(0, right=Node(0))))
        self.assertEqual(tree_diameter(Node(0, fork)), 6)

    def test_invalid_structure(self):
        child = Node(1)
        root = Node(0)
        root.left = root
        for invalid in [root, Node(0, child, child), Node(0, right=42), 42]:
            with self.assertRaises(ValueError):
                tree_diameter(invalid)

    def test_all_pairs_distance_oracle(self):
        rng = random.Random(120)
        for _ in range(150):
            nodes = [Node(7) for _ in range(rng.randrange(1, 30))]
            adjacent = {node: [] for node in nodes}
            slots = [(nodes[0], "left"), (nodes[0], "right")]
            for child in nodes[1:]:
                parent, side = slots.pop(rng.randrange(len(slots)))
                setattr(parent, side, child)
                adjacent[parent].append(child)
                adjacent[child].append(parent)
                slots.extend([(child, "left"), (child, "right")])
            expected = 0
            for start in nodes:
                queue, seen = deque([(start, 0)]), {start}
                while queue:
                    node, distance = queue.popleft()
                    expected = max(expected, distance)
                    for neighbor in adjacent[node]:
                        if neighbor not in seen:
                            seen.add(neighbor)
                            queue.append((neighbor, distance + 1))
            self.assertEqual(tree_diameter(nodes[0]), expected)

if __name__ == "__main__":
    unittest.main()
