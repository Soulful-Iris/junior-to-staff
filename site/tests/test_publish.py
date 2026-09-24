"""Publication failure controls use only temporary directories."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('reader_publish', Path(__file__).resolve().parents[1]/'publish.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.live, self.marker = self.root/'out', self.root/'last-deployed'
        old = self.root/'old'; old.mkdir(); (old/'index.html').write_text('old')
        self.live.symlink_to('old', target_is_directory=True)
        self.marker.write_text('abcdef0\n')
        self.stage = self.root/'stage'; self.stage.mkdir()
        (self.stage/'index.html').write_text('new')

    def publish(self):
        return p.publish(self.stage, self.live, 'abcdef1', self.marker)

    def assert_old(self):
        self.assertEqual((self.live/'index.html').read_text(), 'old')
        self.assertEqual(self.marker.read_text(), 'abcdef0\n')

    def test_success_retains_old_release(self):
        release = self.publish()
        self.assertEqual(self.live.resolve(), release)
        self.assertEqual((self.live/'index.html').read_text(), 'new')
        self.assertEqual((self.root/'old/index.html').read_text(), 'old')
        self.assertEqual(self.marker.read_text(), 'abcdef1\n')

    def test_failure_at_each_rename_preserves_old(self):
        for failure in (1, 2, 3):
            with self.subTest(operation=failure):
                calls = [0]
                original = p.os.replace
                def fail(source, destination):
                    calls[0] += 1
                    if calls[0] == failure:
                        raise OSError('injected rename failure')
                    return original(source, destination)
                with patch.object(p.os, 'replace', side_effect=fail), self.assertRaises(OSError):
                    self.publish()
                self.assert_old()
                if not self.stage.exists():
                    self.stage.mkdir(); (self.stage/'index.html').write_text('new')

    def test_failed_post_switch_smoke_restores_old(self):
        calls = [0]
        def smoke(root):
            calls[0] += 1
            if calls[0] == 2:
                raise OSError('injected post-switch failure')
        with patch.object(p, 'smoke', side_effect=smoke), self.assertRaises(OSError):
            self.publish()
        self.assert_old()

    def test_keyboard_interrupt_does_not_delete_a_release(self):
        with patch.object(p, 'record', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            self.publish()
        self.assert_old()
        self.assertEqual(len(list((self.root/'.releases').glob('*/index.html'))), 1)

    def test_incomplete_stage_is_rejected_before_publication(self):
        (self.stage/'index.html').unlink()
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_old()


if __name__ == '__main__':
    unittest.main()
