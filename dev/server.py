"""Simple dev server: serves the project root over HTTP with /, → preview.html.

Usage:
    .venv/bin/python dev/server.py
    # then open http://localhost:8080/

Why a custom server: preview.html lives in dev/ but references fonts at
../fonts/... A naive `python -m http.server` from dev/ can't reach above its
served root. This server serves from the project root and routes / to dev/preview.html
so the relative paths just work.
"""

import http.server
import os
import socketserver

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", 8080))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def end_headers(self):
        # Disable caching so iterations show up immediately
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/dev/preview.html"
        super().do_GET()

    def log_message(self, format, *args):
        # Quiet — comment this out if you want request logs
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Datatype Progress dev server")
        print(f"  http://localhost:{PORT}/")
        print(f"  serving from {PROJECT_ROOT}")
        print(f"  Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
