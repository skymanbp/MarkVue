#!/usr/bin/env python3
"""
MarkVue - Local Markdown Viewer (Server Mode)
==============================================
Optional Python launcher with local HTTP server.
Without Python, just double-click MarkVue.html.

Server mode benefits:
  - Open .md files from command line
  - Save files back to disk (Ctrl+S)
  - Better font loading & caching

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
VERSION = "2.1.0"
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
        print(f"  {C.B}>>>{C.E} File: {C.BD}{os.path.basename(filepath)}{C.E}")
    print(f"  {C.DM}   Press Ctrl+C to stop{C.E}\n")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, initial_file=None, **kwargs):
        self.initial_file = initial_file
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # API: initial file content + path
        if parsed.path == '/api/initial-file':
            if self.initial_file and os.path.exists(self.initial_file):
                try:
                    with open(self.initial_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    data = json.dumps({
                        'content': content,
                        'filename': os.path.basename(self.initial_file),
                        'path': os.path.abspath(self.initial_file),
                    })
                    self._json_response(200, data)
                    return
                except Exception as e:
                    self.send_error(500, str(e))
                    return
            self.send_response(204)
            self.end_headers()
            return

        if parsed.path in ('/', '/index.html'):
            self.path = '/' + HTML_FILE.name

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        # API: save file
        if parsed.path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                filepath = body.get('path', '')
                content = body.get('content', '')

                # Security: only allow saving to files that exist
                # and are in accessible directories
                if not filepath or not os.path.exists(filepath):
                    self._json_response(400, json.dumps({'error': 'Invalid path'}))
                    return

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                self._json_response(200, json.dumps({'ok': True, 'path': filepath}))
                print(f"  {C.G}>>>{C.E} Saved: {filepath}")
                return
            except Exception as e:
                self._json_response(500, json.dumps({'error': str(e)}))
                return

        self.send_error(404)

    def _json_response(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))

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
                s.bind(('', p))
                return p
        except OSError:
            continue
    return start


def serve(port, initial_file=None):
    handler = partial(Handler, initial_file=initial_file, directory=str(SCRIPT_DIR))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(
        description=f'{APP_NAME} v{VERSION} - Local Markdown Viewer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python markvue.py                  Launch MarkVue
  python markvue.py README.md        Open and preview README.md
  python markvue.py --port 3000      Use port 3000
  python markvue.py -n               Don't auto-open browser
        """)
    parser.add_argument('file', nargs='?', help='Markdown file to open')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT)
    parser.add_argument('--no-browser', '-n', action='store_true')
    args = parser.parse_args()

    if not HTML_FILE.exists():
        print(f"{C.Y}ERROR: {HTML_FILE.name} not found. Keep it next to this script.{C.E}")
        sys.exit(1)

    initial_file = None
    if args.file:
        fp = Path(args.file).resolve()
        if not fp.exists():
            print(f"{C.Y}ERROR: File not found: {args.file}{C.E}")
            sys.exit(1)
        initial_file = str(fp)

    port = find_port(args.port)
    if port != args.port:
        print(f"{C.Y}WARN: Port {args.port} busy, using {port}{C.E}")

    banner(port, initial_file)

    t = threading.Thread(target=serve, args=(port, initial_file), daemon=True)
    t.start()

    url = f"http://localhost:{port}" + ("?file=1" if initial_file else "")
    if not args.no_browser:
        webbrowser.open(url)

    def shutdown(sig, frame):
        print(f"\n  {C.DM}Shutting down...{C.E}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        t.join()
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == '__main__':
    main()
