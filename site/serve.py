#!/usr/bin/env python3.12
"""Serve the built site.

    python3.12 site/serve.py [port]

Static files only, no application. If this process dies the worst case is a
dead bookmark, which is why it is a systemd unit with Restart=always and why
there is nothing here that can lose data.
"""
import functools
import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "out"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8901


class Handler(http.server.SimpleHTTPRequestHandler):
    # Python's mimetypes does not know woff2 and falls back to
    # application/octet-stream, which some browsers refuse to use as a font.
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".woff2": "font/woff2", ".svg": "image/svg+xml"}

    def end_headers(self):
        # The SVGs and fonts are content-addressed by nothing, so keep the
        # cache short enough that a rebuild shows up without a hard refresh.
        if self.path.startswith("/assets/") or self.path.startswith("/fonts/"):
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
    os.chdir(ROOT)
    handler = functools.partial(Handler, directory=str(ROOT))
    with Server(("127.0.0.1", PORT), handler) as httpd:
        print(f"serving {ROOT} on 127.0.0.1:{PORT}", flush=True)
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
