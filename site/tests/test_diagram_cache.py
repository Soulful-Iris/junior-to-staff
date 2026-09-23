import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import diagram_cache


class DiagramCacheTests(unittest.TestCase):
    def test_all_render_inputs_affect_identity(self):
        inputs = {"renderer": "theme-A", "lock": "version-A", "browser": "A", "fonts": "A"}
        first = diagram_cache.key("graph LR\nA-->B", inputs)
        self.assertEqual(first, diagram_cache.key("graph LR\r\nA-->B\n", inputs))
        for field in inputs:
            self.assertNotEqual(first, diagram_cache.key("graph LR\nA-->B", {**inputs, field: "B"}))
        self.assertNotEqual(first, diagram_cache.key("graph LR\nB-->A", inputs))

    def test_truncated_or_empty_cache_is_not_a_hit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "diagram.svg"
            self.assertFalse(diagram_cache.valid_svg(path))
            for bad in ("", "<svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 0 5"/>'):
                path.write_text(bad)
                self.assertFalse(diagram_cache.valid_svg(path))
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20"><text>valid</text></svg>')
            self.assertTrue(diagram_cache.valid_svg(path))
