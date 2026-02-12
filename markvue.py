#!/usr/bin/env python3
"""
MarkVue - Local Markdown Viewer (Server Mode)
==============================================
Optional Python launcher with local HTTP server.
Without Python, just double-click MarkVue.html.

Usage:
    python markvue.py                  # Launch
    python markvue.py README.md        # Open a file
    python markvue.py -p 3000          # Custom port
    python markvue.py -n               # No auto-open browser
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import signal
import argparse
import urllib.parse
import socket
from pathlib import Path
from functools import partial

APP_NAME = "MarkVue"
VERSION = "2.2.0"
DEFAULT_PORT = 8899
SCRIPT_DIR = Path(__file__).parent.resolve()
HTML_FILE = SCRIPT_DIR / "MarkVue.html"

class C:
    B = '\033[94m'; G = '\033[92m'; Y = '\033[93m'
    CY = '\033[96m'; BD = '\033[1m'; DM = '\033[2m'; E = '\033[0m'

def banner(port, filepath=None):
    print(f"""
{C.CY}{C.BD}  ==========================================
       MarkVue - Markdown Viewer v{VERSION}
  =========================================={C.E}

  {C.G}OK{C.E} Server running
  {C.G}OK{C.E} URL: {C.BD}http://localhost:{port}{C.E}""")
    if filepath:
        print(f"  {C.B}>>{C.E} File: {C.BD}{os.path.basename(filepath)}{C.E}")
    print(f"  {C.DM}   Press Ctrl+C to stop{C.E}\n")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, initial_file=None, **kwargs):
        self.initial_file = initial_file
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/api/initial-file':
            if self.initial_file and os.path.isfile(self.initial_file):
                try:
                    with open(self.initial_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    self._json(200, {
                        'content': content,
                        'filename': os.path.basename(self.initial_file),
                        'path': os.path.abspath(self.initial_file),
                    })
                except Exception as e:
                    self._json(500, {'error': str(e)})
                return
            self.send_response(204)
            self.end_headers()
            return

        if path in ('/', '/index.html'):
            self.path = '/' + HTML_FILE.name
        super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                filepath = body.get('path', '')
                content = body.get('content', '')

                if not filepath:
                    self._json(400, {'error': 'No path'})
                    return

                fp = os.path.abspath(filepath)
                parent = os.path.dirname(fp)
                if not os.path.isdir(parent):
                    self._json(400, {'error': 'Parent directory does not exist'})
                    return

                with open(fp, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)

                self._json(200, {'ok': True, 'path': fp})
                print(f"  {C.G}>>{C.E} Saved: {fp}")
            except Exception as e:
                self._json(500, {'error': str(e)})
            return

        self.send_error(404)

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def translate_path(self, path):
        path = urllib.parse.unquote(path.split('?', 1)[0].split('#', 1)[0]).strip('/')
        if not path or path == 'index.html':
            return str(HTML_FILE)
        return str(SCRIPT_DIR / path)

    def log_message(self, fmt, *args):
        pass


def find_port(start):
    for p in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return start


def serve(port, initial_file=None):
    handler = partial(Handler, initial_file=initial_file, directory=str(SCRIPT_DIR))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=f'{APP_NAME} v{VERSION}')
    parser.add_argument('file', nargs='?', help='Markdown file to open')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT)
    parser.add_argument('--no-browser', '-n', action='store_true')
    args = parser.parse_args()

    if not HTML_FILE.exists():
        print(f"ERROR: {HTML_FILE.name} not found next to this script.")
        sys.exit(1)

    initial_file = None
    if args.file:
        fp = Path(args.file).resolve()
        if not fp.exists():
            print(f"ERROR: File not found: {args.file}")
            sys.exit(1)
        initial_file = str(fp)

    port = find_port(args.port)
    banner(port, initial_file)

    t = threading.Thread(target=serve, args=(port, initial_file), daemon=True)
    t.start()

    url = f"http://localhost:{port}" + ("?file=1" if initial_file else "")
    if not args.no_browser:
        webbrowser.open(url)

    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    try:
        t.join()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
