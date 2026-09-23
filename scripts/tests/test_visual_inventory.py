import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('visual_inventory', Path(__file__).resolve().parents[1]/'check_visuals.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class VisualInventoryTests(unittest.TestCase):
    def test_changed_visual_invalidates_inspection_not_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'v.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>One case</title></svg>')
            first = module.inventory(root, ['v.svg'], {})[0]
            self.assertEqual(first['status'], 'semantic-review-pending')
            reviews = {'v.svg': {'sha256': first['sha256'], 'review': 'Static case inspected'}}
            self.assertEqual(module.inventory(root, ['v.svg'], reviews)[0]['status'], 'static-inspected')
            (root/'v.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>Changed case</title></svg>')
            with self.assertRaisesRegex(ValueError, 'changed since inspection'):
                module.inventory(root, ['v.svg'], reviews)
            with self.assertRaisesRegex(ValueError, 'missing visual'):
                module.inventory(root, [], reviews)
