"""Run the actual reader script in Chromium with controlled Storage responses."""
import json
from pathlib import Path
import shutil
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = '''<!doctype html><html><body>
<script id="page-state" type="application/json">{"position":0,"url":"/","title":"Home","src":"README.md"}</script>
<button id="open-contents"></button><button id="close-contents"></button>
<aside id="sidebar"><button id="dismiss-contents"></button><button id="collapse-contents"></button>
<input id="contents-search"><div id="search-results"></div><div id="contents-tree"></div></aside>
<div class="reading-shell"></div><div class="read-progress"><span></span></div>
<button id="motion-toggle"></button><button id="reset-progress"></button>
<button data-finish></button><pre><code class="language-python">print(1)</code></pre>
</body></html>'''


class ReaderStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=shutil.which('chromium'), headless=True,
                                             args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def page(self, progress=None, motion=None, reduced=True):
        context = self.browser.new_context(reduced_motion='reduce' if reduced else 'no-preference')
        self.addCleanup(context.close)
        page = context.new_page()
        page.set_content(HTML)
        # A Storage-interface double isolates the input schema from browser
        # origin policy. This does not claim a cross-reload persistence test.
        page.evaluate("""() => {
          const values = new Map();
          Object.defineProperty(window, 'localStorage', {value: {
            getItem: key => values.has(key) ? values.get(key) : null,
            setItem: (key, value) => values.set(key, String(value))
          }});
        }""")
        for key, value in [('engineering-guide:progress:v1', progress), ('engineering-guide:still', motion)]:
            if value is not None:
                page.evaluate('([k,v]) => localStorage.setItem(k,v)', [key, value])
        page.add_script_tag(path=str(ROOT/'app.js'))
        return page

    def test_invalid_progress_does_not_disable_reader(self):
        for value in ('null', 'true', '1', '"text"', '[]', '{}', '{', '{"completed":[1],"last":null}'):
            with self.subTest(value=value):
                page = self.page(progress=value)
                self.assertEqual(page.locator('.copy-code').count(), 1)
                page.locator('[data-finish]').click()
                stored = json.loads(page.evaluate("localStorage.getItem('engineering-guide:progress:v1')"))
                self.assertEqual(stored, {'completed': ['README.md'], 'last': None})

    def test_valid_progress_remains(self):
        value = {'completed': ['README.md'], 'last': {'url': '/lesson.html', 'title': 'Lesson'}}
        page = self.page(progress=json.dumps(value))
        self.assertTrue(page.locator('[data-finish]').is_disabled())
        self.assertEqual(json.loads(page.evaluate("localStorage.getItem('engineering-guide:progress:v1')")), value)

    def test_boolean_override_and_system_default(self):
        for value, expected in ((None, 'Static visuals'), ('false', 'Motion on'), ('true', 'Static visuals'), ('null', 'Static visuals'), ('1', 'Static visuals'), ('{', 'Static visuals')):
            with self.subTest(value=value):
                page = self.page(motion=value)
                self.assertEqual(page.locator('#motion-toggle').inner_text(), expected)
        page = self.page(motion='false')
        page.emulate_media(reduced_motion='no-preference')
        page.emulate_media(reduced_motion='reduce')
        self.assertEqual(page.locator('#motion-toggle').inner_text(), 'Motion on')
        page = self.page()
        page.emulate_media(reduced_motion='no-preference')
        page.wait_for_function("document.getElementById('motion-toggle').textContent === 'Motion on'")

    def test_blocked_storage_does_not_disable_reader(self):
        page = self.page()
        page.evaluate("() => { localStorage.setItem = () => { throw new Error('blocked'); }; }")
        page.locator('#motion-toggle').click()
        self.assertEqual(page.locator('#motion-toggle').inner_text(), 'Motion on')
        page.locator('[data-finish]').click()
        self.assertTrue(page.locator('[data-finish]').is_disabled())


if __name__ == '__main__':
    unittest.main()
