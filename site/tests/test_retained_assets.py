"""Old HTML must still fetch its fingerprinted assets after publication."""
import functools
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

spec = importlib.util.spec_from_file_location('reader_server', Path(__file__).resolve().parents[1]/'serve.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class RetainedAssetsTests(unittest.TestCase):
    def test_cold_delayed_request_after_pointer_switch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); releases = root/'.releases'; releases.mkdir()
            old = releases/'old'; old.mkdir(); new = releases/'new'; new.mkdir()
            data = b'console.log("old page script")'
            name = 'reader-js.' + hashlib.sha256(data).hexdigest()[:16] + '.js'
            (old/name).write_bytes(data)
            (old/'index.html').write_text('<script src="/' + name + '"></script>')
            (new/'index.html').write_text('new page')
            live = root/'out'; live.symlink_to('.releases/old', target_is_directory=True)
            with server.Server(('127.0.0.1', 0), functools.partial(server.Handler, directory=str(live))) as httpd:
                thread = Thread(target=httpd.serve_forever, daemon=True); thread.start()
                url = 'http://127.0.0.1:' + str(httpd.server_address[1])
                try:
                    with urlopen(url, timeout=2) as response:
                        self.assertIn(name, response.read().decode())
                    # No asset request has occurred yet; the cache is cold.
                    pointer = root/'next'; pointer.symlink_to('.releases/new', target_is_directory=True)
                    pointer.replace(live)
                    with urlopen(url + '/' + name, timeout=2) as response:
                        self.assertEqual(response.read(), data)
                        self.assertIn('immutable', response.headers['Cache-Control'])
                    with urlopen(url, timeout=2) as response:
                        self.assertEqual(response.read(), b'new page')
                    (old/'old-only.html').write_text('retired')
                    with self.assertRaises(HTTPError):
                        urlopen(url + '/old-only.html', timeout=2)
                finally:
                    httpd.shutdown(); thread.join(2)


if __name__ == '__main__':
    unittest.main()
