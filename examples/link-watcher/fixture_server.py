"""Controlled HTTP origin; change state.json while the server is running."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import time

class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        state = json.loads(Path('state.json').read_text()) if Path('state.json').exists() else {}
        time.sleep(min(max(float(state.get('delay_seconds', 0)), 0), 5))
        self.send_response(int(state.get('status', 200)))
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Retry-After', '30')
        self.end_headers()
        try:
            self.wfile.write(state.get('body', 'guide-v1: learning resource').encode())
        except BrokenPipeError:
            pass

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8765), Fixture).serve_forever()
