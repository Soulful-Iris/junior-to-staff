"""Catalog sensitivity checks; not tests of the lesson's technical truth."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_catalog as catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.chapter = 'curriculum/01-code/01-example'
        self.prompt = self.chapter+'/problems/01-demo/README.md'
        files = {
            self.chapter+'/README.md': '# Example\n', self.prompt: '# Demo\n',
            self.chapter+'/problems/01-demo/solution.py': 'pass\n',
            self.chapter+'/problems/01-demo/test_demo.py': 'pass\n',
            self.chapter+'/problems/design.md': '# Design\n',
            self.chapter+'/projects/build.md': '# Build\n',
            'README.md': f'# Home\n[Example]({self.chapter}/README.md)\n1 subject chapters · 1 coding bundles · 1 project entries · 1 design/architecture pages\n',
            'curriculum/README.md': '# Route\n[Example](01-code/01-example/README.md)\n',
            'indexes/coding.md': f'[Demo](../{self.prompt})\n',
            'indexes/projects.md': f'[Build](../{self.chapter}/projects/build.md)\n',
            'indexes/system-designs.md': f'[Design](../{self.chapter}/problems/design.md)\n',
        }
        for name, text in files.items(): self.write(name, text)
        self.bank = [{'number': 1, 'path': self.prompt, 'directory': str(Path(self.prompt).parent)}]
        self.write('indexes/problem-bank.json', json.dumps(self.bank))

    def write(self, name, text):
        p = self.root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)

    def test_complete_inventory_passes(self):
        self.assertEqual([], catalog.check(self.root, catalog.collect(self.root)))

    def test_empty_project_inventory_fails(self):
        (self.root/self.chapter/'projects/build.md').unlink()
        with self.assertRaisesRegex(ValueError, 'Empty'): catalog.collect(self.root)

    def test_new_project_cannot_hide_behind_old_counts(self):
        self.write(self.chapter+'/projects/new.md', '# New\n')
        errors = catalog.check(self.root, catalog.collect(self.root))
        self.assertTrue(any('new.md' in e for e in errors)); self.assertTrue(any('counts' in e for e in errors))

    def test_duplicate_registry_entry_fails(self):
        self.write('indexes/problem-bank.json', json.dumps(self.bank * 2))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): catalog.collect(self.root)

    def test_orphan_coding_bundle_fails(self):
        self.write(self.chapter+'/problems/02-new/README.md', '# New\n')
        with self.assertRaisesRegex(ValueError, 'orphan'): catalog.collect(self.root)

    def test_missing_implementation_fails(self):
        (self.root/Path(self.prompt).parent/'solution.py').unlink()
        with self.assertRaisesRegex(ValueError, 'Incomplete'): catalog.collect(self.root)

    def test_duplicate_or_missing_catalog_link_fails(self):
        p = self.root/'indexes/projects.md'; p.write_text(p.read_text()*2)
        self.write('indexes/system-designs.md', '# Missing design\n')
        errors = catalog.check(self.root, catalog.collect(self.root))
        self.assertEqual(2, len(errors))

    def test_unreachable_chapter_fails(self):
        self.write('curriculum/README.md', '# Empty route\n')
        self.assertTrue(catalog.check(self.root, catalog.collect(self.root)))
