from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import content_checks


class ContentChecksTests(unittest.TestCase):
    def test_missing_source_is_caught_before_link_stripping(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'Missing source reference'):
                content_checks.source_references(Path(directory), [{'src':'README.md','text':'[fixture](missing.py)'}])

    def test_exact_visual_and_empty_inventory_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); (out/'gallery').mkdir()
            (out/'gallery/index.html').write_text('<article></article>')
            (out/'index.html').write_text('<article class="lesson-body"><img src="/assets/mermaid/wrong.svg"></article>')
            item = {'output':'index.html','presentation':'authored-lesson','mermaid':['required.svg'],'source_images':[], 'code_inclusions':[]}
            with self.assertRaisesRegex(ValueError, 'Missing displayed diagrams'):
                content_checks.validate(out, {'pages':{'README.md':item}, 'assets':{}})
            with self.assertRaisesRegex(ValueError, 'Empty expected'):
                content_checks.validate(out, {'pages':{}, 'assets':{}})
            item['mermaid'] = ['wrong.svg']
            content_checks.validate(out, {'pages':{'README.md':item}, 'assets':{}})
            (out/'unexpected.html').write_text('surprise')
            with self.assertRaisesRegex(ValueError, 'Page inventory mismatch'):
                content_checks.validate(out, {'pages':{'README.md':item}, 'assets':{}})
