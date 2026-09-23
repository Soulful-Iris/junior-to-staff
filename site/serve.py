#!/usr/bin/env python3.12
"""Serve the current static release; retain fingerprinted assets for old pages."""
import functools
import http.server
import re
import socketserver
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent / "out"
IMMUTABLE = re.compile(r"(?:reader-(?:css|js)\.[0-9a-f]{16}\.(?:css|js)|assets/mermaid/[0-9a-f]{16,64}\.svg)")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".woff2": "font/woff2", ".svg": "image/svg+xml",
                      ".css": "text/css", ".js": "text/javascript"}

    def translate_path(self, path):
        current = Path(super().translate_path(path))
        if current.is_file() or current.is_dir():
            return str(current)
        relative = unquote(urlsplit(path).path).lstrip('/')
        # Only fingerprinted assets may fall back; never serve old HTML or an
        # arbitrary traversal path from a retained release.
        if IMMUTABLE.fullmatch(relative):
            releases = Path(self.directory).absolute().parent / '.releases'
            for release in sorted(releases.glob('*'), reverse=True):
                candidate = release / relative
                if candidate.is_file():
                    return str(candidate)
        return str(current)

    def end_headers(self):
        if IMMUTABLE.fullmatch(unquote(urlsplit(self.path).path).lstrip('/')):
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        elif self.path.startswith("/assets/") or self.path.startswith("/fonts/"):
            self.send_header("Cache-Control", "public, max-age=3600")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "404" in (args[1] if len(args) > 1 else ""):
            super().log_message(fmt, *args)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    if not ROOT.is_dir():
        print(f"no build at {ROOT} — run site/build.py first", file=sys.stderr)
        return 1
    handler = functools.partial(Handler, directory=str(ROOT))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8901
    with Server(("127.0.0.1", port), handler) as httpd:
        print(f"serving {ROOT} on 127.0.0.1:{port}", flush=True)
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
