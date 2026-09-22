import unittest
from solution import Node, cycle_entry

class CycleTests(unittest.TestCase):
    def test_every_small_prefix_and_cycle_length(self):
        self.assertIsNone(cycle_entry(None))
        for size in range(1, 25):
            for entry_index in range(-1, size):
                nodes = [Node(7) for _ in range(size)]
                for left, right in zip(nodes, nodes[1:]):
                    left.next = right
                if entry_index >= 0:
                    nodes[-1].next = nodes[entry_index]
                before = [node.next for node in nodes]
                expected = nodes[entry_index] if entry_index >= 0 else None
                self.assertIs(cycle_entry(nodes[0]), expected)
                self.assertTrue(all(node.next is link for node, link in zip(nodes, before)))

    def test_long_chain_and_invalid_links(self):
        head = None
        for _ in range(10000):
            head = Node(1, head)
        self.assertIsNone(cycle_entry(head))
        for bad in [42, "node", Node(1, 42)]:
            with self.assertRaises(ValueError):
                cycle_entry(bad)

if __name__ == "__main__":
    unittest.main()
