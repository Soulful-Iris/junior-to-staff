import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('preservation', Path(__file__).resolve().parents[1]/'check_organization.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class PreservationTests(unittest.TestCase):
    def test_additions_allowed_missing_original_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'lesson.md').write_text('baseline')
            data = {'source_commit':'baseline', 'files':[{'destination':'lesson.md','source_sha256':hashlib.sha256(b'baseline').hexdigest()}]}
            (root/'new.md').write_text('legitimate new lesson')
            self.assertEqual(module.check_current(root, data)['changed_since_baseline'], [])
            (root/'lesson.md').write_text('reviewed correction')
            self.assertEqual(len(module.check_current(root, data)['changed_since_baseline']), 1)
            (root/'lesson.md').unlink()
            with self.assertRaises(ValueError): module.check_current(root, data)
