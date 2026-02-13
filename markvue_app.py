#!/usr/bin/env python3
"""
MarkVue — Native Desktop Application v3.1
==========================================
Architecture:
  - Hidden embedded HTTP server on localhost (random port)
  - pywebview native window loads from http://127.0.0.1:{port}
  - All CDN resources load normally (no file:// restrictions)
  - File open/save via pywebview native dialogs (JS-Python bridge)
  - User sees a native desktop window, not a browser

This is the same approach Electron uses internally.
"""

import os
import sys
import json
import socket
import threading
import time
import traceback
import webbrowser
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from functools import partial
from datetime import datetime

APP_NAME = "MarkVue"
VERSION = "3.1.0"
DEFAULT_PORT = 18737  # obscure port to avoid conflicts

# ========== Logging ==========

LOG_PATH = None

def init_log():
    global LOG_PATH
    try:
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent
        LOG_PATH = str(base / "markvue-error.log")
    except Exception:
        LOG_PATH = os.path.join(os.path.expanduser("~"), "markvue-error.log")

def log(msg):
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass

def log_exception():
    log(traceback.format_exc())


# ========== Resources ==========

def get_resource_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.resolve()


# ========== HTTP Server ==========

# Global state shared between server and pywebview
_initial_file_path = None
_initial_file_content = None
_initial_file_name = None
_api_ref = None  # reference to Api instance


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves MarkVue.html + provides file I/O API endpoints."""

    def __init__(self, *args, resource_dir=None, **kwargs):
        self.resource_dir = resource_dir or str(get_resource_dir())
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        # API: get initial file
        if path == '/api/initial-file':
            if _initial_file_content is not None:
                data = json.dumps({
                    'content': _initial_file_content,
                    'filename': _initial_file_name,
                    'path': _initial_file_path,
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(204)
                self.end_headers()
            return

        # Serve root as MarkVue.html
        if path in ('/', '/index.html'):
            self.path = '/MarkVue.html'
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
                if not os.path.isdir(os.path.dirname(fp)):
                    self._json(400, {'error': 'Parent dir missing'})
                    return

                with open(fp, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
                self._json(200, {'ok': True, 'path': fp})
                log(f"Saved: {fp}")
            except Exception as e:
                log(f"save error: {e}")
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
            return os.path.join(self.resource_dir, 'MarkVue.html')
        return os.path.join(self.resource_dir, path)

    def log_message(self, fmt, *args):
        pass  # silent


def find_free_port(start=DEFAULT_PORT):
    for p in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return start


def start_server(port, resource_dir):
    handler = partial(Handler, resource_dir=resource_dir, directory=resource_dir)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
            log(f"Server listening on 127.0.0.1:{port}")
            httpd.serve_forever()
    except Exception:
        log_exception()


def wait_for_server(port, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                s.connect(('127.0.0.1', port))
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.05)
    return False


# ========== pywebview API ==========

class Api:
    """Native file dialog API exposed to JS via pywebview."""

    def __init__(self, window_ref):
        self._window = window_ref
        self.current_path = None

    def open_file_dialog(self):
        try:
            import webview
            result = self._window().create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=('Markdown Files (*.md;*.markdown;*.txt;*.mdx;*.rmd)',
                            'All Files (*.*)'),
            )
            if not result:
                return None
            filepath = result[0] if isinstance(result, (list, tuple)) else result
            return self._read_file(filepath)
        except Exception as e:
            log(f"open_file_dialog error: {e}")
            return {'error': str(e)}

    def save_file(self, content):
        if not self.current_path:
            return self.save_file_as(content)
        try:
            with open(self.current_path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            log(f"Saved: {self.current_path}")
            return {'ok': True, 'path': self.current_path,
                    'filename': os.path.basename(self.current_path)}
        except Exception as e:
            return {'error': str(e)}

    def save_file_as(self, content):
        try:
            import webview
            suggested = os.path.basename(self.current_path) if self.current_path else 'untitled.md'
            result = self._window().create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested,
                file_types=('Markdown Files (*.md)', 'All Files (*.*)'),
            )
            if not result:
                return None
            filepath = result if isinstance(result, str) else result[0]
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            self.current_path = filepath
            return {'ok': True, 'path': filepath,
                    'filename': os.path.basename(filepath)}
        except Exception as e:
            return {'error': str(e)}

    def set_title(self, title):
        try:
            self._window().set_title(title)
        except Exception:
            pass

    def _read_file(self, filepath):
        filepath = os.path.abspath(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        self.current_path = filepath
        return {'content': content, 'filename': os.path.basename(filepath), 'path': filepath}


# ========== Path Resolution ==========

def resolve_filepath():
    log(f"sys.argv = {sys.argv}")
    if len(sys.argv) < 2:
        return None
    for arg in sys.argv[1:]:
        if arg.startswith('--'):
            continue
        arg = arg.strip().strip('"').strip("'")
        if not arg:
            continue
        try:
            p = Path(arg).resolve()
            if p.is_file() and p.suffix.lower() in (
                '.md', '.markdown', '.txt', '.text', '.mdx', '.rmd'
            ):
                log(f"Resolved: {p}")
                return str(p)
        except Exception:
            continue
    non_flags = [a for a in sys.argv[1:] if not a.startswith('--')]
    joined = ' '.join(non_flags).strip().strip('"').strip("'")
    if joined:
        try:
            p = Path(joined).resolve()
            if p.is_file():
                return str(p)
        except Exception:
            pass
    return None


# ========== Main ==========

def main():
    global _initial_file_path, _initial_file_content, _initial_file_name, _api_ref

    init_log()
    log("=" * 40)
    log(f"{APP_NAME} v{VERSION} starting")

    resource_dir = get_resource_dir()
    html_file = resource_dir / "MarkVue.html"
    log(f"html={html_file} exists={html_file.is_file()}")

    if not html_file.is_file():
        msg = (f"MarkVue.html not found.\n"
               f"Expected: {resource_dir}\n"
               f"Rebuild with Build EXE.bat")
        log(f"FATAL: {msg}")
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk(); r.withdraw()
            messagebox.showerror(APP_NAME, msg)
        except Exception:
            pass
        sys.exit(1)

    # Resolve file from command line
    filepath = resolve_filepath()
    log(f"filepath = {filepath}")

    # Load initial file into global state (server reads this)
    if filepath and os.path.isfile(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                _initial_file_content = f.read()
            _initial_file_path = os.path.abspath(filepath)
            _initial_file_name = os.path.basename(filepath)
            log(f"Loaded: {_initial_file_name} ({len(_initial_file_content)} chars)")
        except Exception as e:
            log(f"Read error: {e}")

    # Start embedded HTTP server (hidden, user never sees it)
    port = find_free_port()
    threading.Thread(
        target=start_server,
        args=(port, str(resource_dir)),
        daemon=True,
    ).start()

    if not wait_for_server(port):
        log("WARNING: Server not ready after 5s")

    url = f"http://127.0.0.1:{port}" + ("?file=1" if filepath else "")
    log(f"URL: {url}")

    # Try pywebview (native window)
    try:
        import webview
        log("pywebview available")
    except ImportError:
        # Fallback: open in system browser
        log("pywebview not available, opening browser")
        webbrowser.open(url)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        return

    # Window title
    title = f"{os.path.basename(filepath)} — {APP_NAME}" if filepath else APP_NAME

    # Create API + window
    window_holder = [None]
    api = Api(lambda: window_holder[0])
    if filepath:
        api.current_path = filepath
    _api_ref = api

    window = webview.create_window(
        title=title,
        url=url,
        js_api=api,
        width=1280,
        height=800,
        min_size=(640, 400),
        text_select=True,
    )
    window_holder[0] = window
    log("Window created, starting event loop")

    webview.start(debug=('--debug' in sys.argv))
    log("Exiting")


if __name__ == '__main__':
    try:
        main()
    except Exception:
        init_log()
        log("FATAL:")
        log_exception()
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk(); r.withdraw()
            messagebox.showerror(APP_NAME,
                f"Crash log: {LOG_PATH}\n\n{traceback.format_exc()[-400:]}")
        except Exception:
            pass
        sys.exit(1)
