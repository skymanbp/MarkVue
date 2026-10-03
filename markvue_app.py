#!/usr/bin/env python3
"""
MarkVue — Native Desktop Application
====================================
Architecture:
  - Hidden embedded HTTP server on 127.0.0.1 (port 18737+)
  - pywebview native window loads from http://127.0.0.1:{port}
  - All CDN resources load normally (no file:// restrictions)
  - File open/save go through the pywebview JS bridge (native dialogs);
    the HTTP /api/save endpoint is the fallback for plain-browser mode
  - User sees a native desktop window, not a browser

This is the same approach Electron uses internally.

The server is deliberately minimal and locked down:
  - Only "/" (MarkVue.html), "/api/*" and "/asset/*" exist. Nothing else
    in the program directory is reachable.
  - Every request must carry a loopback Host header (DNS-rebinding guard).
  - /api/save only accepts same-origin JSON and only writes to files that
    were opened through MarkVue itself (never an arbitrary path).
  - /asset/<rel> serves images next to the open document and refuses to
    leave that directory.

markvue.py (browser/server mode) imports the server pieces from here, so
both launch methods share one implementation.
"""

import os
import sys
import json
import socket
import threading
import time
import mimetypes
import traceback
import webbrowser
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from functools import partial
from datetime import datetime

APP_NAME = "MarkVue"
VERSION = "0.1.0"
DEFAULT_PORT = 18737  # obscure port to avoid conflicts

MARKDOWN_SUFFIXES = ('.md', '.markdown', '.txt', '.text', '.mdx', '.rmd')

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
    if not LOG_PATH:
        return
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


# ========== Document state (shared by server + JS bridge) ==========

class DocState:
    """Which file is open, and which paths the app is allowed to write."""

    def __init__(self):
        self.lock = threading.Lock()
        self.path = None          # absolute path of the open document (or None)
        self.allowed = set()      # absolute paths MarkVue itself opened/created
        self.initial = None       # dict served once by /api/initial-file

    def register(self, path):
        path = os.path.abspath(path)
        with self.lock:
            self.path = path
            self.allowed.add(path)
        return path

    def is_allowed(self, path):
        with self.lock:
            return os.path.abspath(path) in self.allowed

    def asset_root(self):
        with self.lock:
            return os.path.dirname(self.path) if self.path else None


DOC = DocState()


# ========== Settings (theme, language, view, split, draft) ==========

def default_settings_path():
    """%LOCALAPPDATA%\\MarkVue\\settings.json (or ~/.markvue/settings.json)."""
    base = os.environ.get('LOCALAPPDATA')
    root = Path(base) / APP_NAME if base else Path.home() / '.markvue'
    return root / 'settings.json'


class SettingsStore:
    """The page's settings and draft, kept in a JSON file.

    The desktop window cannot keep them itself: pywebview runs WebView2 in
    private mode, which discards localStorage when the window closes, and
    two windows get different ports (different storage origins) anyway.
    The server injects the current values into the page (window.MV_STORE)
    and the page writes changes back through POST /api/store. The file is
    re-read on every write, so several open windows share one set.
    """

    MAX_VALUE = 20 * 1024 * 1024        # the draft is the largest value

    def __init__(self, path=None):
        self.path = Path(path) if path else default_settings_path()
        self.lock = threading.Lock()

    def load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)} \
                if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @staticmethod
    def valid(key, value):
        return (isinstance(key, str) and key.startswith('markvue-') and len(key) <= 64
                and (value is None or (isinstance(value, str) and len(value) <= SettingsStore.MAX_VALUE)))

    def set(self, key, value):
        """Store a string value, or remove the key when value is None."""
        with self.lock:
            data = self.load()
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + f'.{os.getpid()}.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, self.path)


STORE = SettingsStore()


def inject_store(html_bytes, values):
    """Put `window.MV_STORE = {...}` at the top of <head>, before any page script."""
    payload = json.dumps(values, ensure_ascii=False).replace('<', '\\u003c')
    tag = f'<script>window.MV_STORE = {payload};</script>'.encode('utf-8')
    marker = b'<meta charset="UTF-8">'
    if marker not in html_bytes:
        return html_bytes
    return html_bytes.replace(marker, marker + tag, 1)


def read_text(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def write_text(path, content):
    # newline='' keeps the document's own line endings untouched
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def load_initial_file(path):
    """Read the file given on the command line into DOC (served by /api/initial-file)."""
    try:
        content = read_text(path)
    except Exception as e:
        log(f"Read error: {e}")
        return None
    abspath = DOC.register(path)
    DOC.initial = {
        'content': content,
        'filename': os.path.basename(abspath),
        'path': abspath,
    }
    log(f"Loaded: {abspath} ({len(content)} chars)")
    return abspath


# ========== HTTP Server ==========

class Handler(http.server.BaseHTTPRequestHandler):
    """Serves MarkVue.html + a tiny JSON API. Nothing else."""

    server_version = f"{APP_NAME}/{VERSION}"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, resource_dir=None, **kwargs):
        self.resource_dir = str(resource_dir or get_resource_dir())
        super().__init__(*args, **kwargs)

    # ----- guards -----

    def _port(self):
        try:
            return self.server.server_address[1]
        except Exception:
            return None

    def _same_origin(self, value):
        """True if a Host/Origin value points at this loopback server."""
        if not value:
            return False
        v = value.strip().lower()
        if v.startswith('http://'):
            v = v[len('http://'):]
        v = v.rstrip('/')
        port = self._port()
        return v in {f'127.0.0.1:{port}', f'localhost:{port}', f'[::1]:{port}'}

    def _check_host(self):
        if self._same_origin(self.headers.get('Host')):
            return True
        self._json(403, {'error': 'Forbidden host'})
        return False

    # ----- responses -----

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self._send(code, body, 'application/json; charset=utf-8')

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def _not_found(self):
        self._send(404, b'Not Found', 'text/plain; charset=utf-8')

    # ----- routes -----

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._check_host():
            return
        path = urllib.parse.urlparse(self.path).path

        if path in ('/', '/index.html', '/MarkVue.html'):
            html = os.path.join(self.resource_dir, 'MarkVue.html')
            try:
                with open(html, 'rb') as f:
                    body = f.read()
            except OSError:
                self._not_found()
                return
            self._send(200, inject_store(body, STORE.load()), 'text/html; charset=utf-8')
            return

        if path == '/api/initial-file':
            if DOC.initial is not None:
                self._json(200, DOC.initial)
            else:
                self.send_response(204)
                self.send_header('Content-Length', '0')
                self.end_headers()
            return

        if path.startswith('/asset/'):
            self._serve_asset(path[len('/asset/'):])
            return

        self._not_found()

    def do_POST(self):
        if not self._check_host():
            return
        path = urllib.parse.urlparse(self.path).path

        if path not in ('/api/save', '/api/store'):
            self._not_found()
            return

        # Cross-site POSTs always carry an Origin header; refuse foreign ones.
        origin = self.headers.get('Origin')
        if origin and not self._same_origin(origin):
            self._json(403, {'error': 'Forbidden origin'})
            return
        ctype = (self.headers.get('Content-Type') or '').split(';')[0].strip().lower()
        if ctype != 'application/json':
            self._json(415, {'error': 'Expected application/json'})
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
        except Exception as e:
            self._json(400, {'error': f'Bad request: {e}'})
            return

        if path == '/api/store':
            self._store(body)
            return

        filepath = body.get('path', '') if isinstance(body, dict) else ''
        content = body.get('content', '') if isinstance(body, dict) else ''
        if not filepath or not isinstance(content, str):
            self._json(400, {'error': 'No path'})
            return

        fp = os.path.abspath(filepath)
        if not DOC.is_allowed(fp):
            # Only files MarkVue itself opened may be written back.
            self._json(403, {'error': 'Path was not opened by MarkVue'})
            return

        try:
            write_text(fp, content)
        except Exception as e:
            log(f"save error: {e}")
            self._json(500, {'error': str(e)})
            return

        log(f"Saved: {fp}")
        self._json(200, {'ok': True, 'path': fp, 'filename': os.path.basename(fp)})

    def _store(self, body):
        key = body.get('key') if isinstance(body, dict) else None
        value = body.get('value') if isinstance(body, dict) else None
        if not SettingsStore.valid(key, value):
            self._json(400, {'error': 'Bad setting'})
            return
        try:
            STORE.set(key, value)
        except OSError as e:
            log(f"store error: {e}")
            self._json(500, {'error': str(e)})
            return
        self._json(200, {'ok': True})

    def _serve_asset(self, rel):
        """Serve a file that sits next to the open document (images etc.)."""
        root = DOC.asset_root()
        if not root:
            self._not_found()
            return
        rel = urllib.parse.unquote(rel).replace('\\', '/').strip('/')
        if not rel:
            self._not_found()
            return
        full = os.path.normpath(os.path.join(root, rel))
        try:
            if os.path.commonpath([os.path.realpath(root), os.path.realpath(full)]) != os.path.realpath(root):
                self._json(403, {'error': 'Outside document folder'})
                return
        except ValueError:
            self._not_found()
            return
        if not os.path.isfile(full):
            self._not_found()
            return
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        try:
            with open(full, 'rb') as f:
                body = f.read()
        except OSError:
            self._not_found()
            return
        self._send(200, body, ctype)

    def log_message(self, fmt, *args):
        pass  # silent


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def find_free_port(start=DEFAULT_PORT):
    for p in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return None


def start_server(port, resource_dir):
    handler = partial(Handler, resource_dir=resource_dir)
    try:
        with ThreadedServer(("127.0.0.1", port), handler) as httpd:
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

def _dialog(kind):
    """webview.FileDialog.OPEN / SAVE (pywebview >= 5.1); the old constants are deprecated."""
    import webview
    fd = getattr(webview, 'FileDialog', None)
    return getattr(fd, kind) if fd else getattr(webview, f'{kind}_DIALOG')


class Api:
    """Native file dialogs exposed to JS as window.pywebview.api."""

    def __init__(self, window_ref):
        self._window = window_ref
        self.dirty = False   # mirrored from JS so the close handler never has to call into the page

    # --- open ---

    def open_file_dialog(self):
        try:
            result = self._window().create_file_dialog(
                _dialog('OPEN'),
                file_types=('Markdown Files (*.md;*.markdown;*.txt;*.mdx;*.rmd)',
                            'All Files (*.*)'),
            )
            if not result:
                return None
            filepath = result[0] if isinstance(result, (list, tuple)) else result
            return self.open_path(filepath)
        except Exception as e:
            log(f"open_file_dialog error: {e}")
            return {'error': str(e)}

    def open_path(self, filepath):
        """Open a file by absolute path (used for drag-and-drop from Explorer)."""
        try:
            filepath = os.path.abspath(filepath)
            if not os.path.isfile(filepath):
                return {'error': 'File not found'}
            content = read_text(filepath)
            DOC.register(filepath)
            return {'content': content, 'filename': os.path.basename(filepath), 'path': filepath}
        except Exception as e:
            log(f"open_path error: {e}")
            return {'error': str(e)}

    # --- save ---

    def save_file(self, content, path=None):
        """Write back to `path`. Only paths MarkVue opened are accepted."""
        if not path or not DOC.is_allowed(path):
            return self.save_file_as(content, path)
        try:
            path = os.path.abspath(path)
            write_text(path, content)
            DOC.register(path)
            log(f"Saved: {path}")
            return {'ok': True, 'path': path, 'filename': os.path.basename(path)}
        except Exception as e:
            return {'error': str(e)}

    def save_file_as(self, content, suggested=None):
        try:
            name = os.path.basename(suggested) if suggested else 'untitled.md'
            if not name.lower().endswith(MARKDOWN_SUFFIXES):
                name = os.path.splitext(name)[0] + '.md'
            kwargs = {'save_filename': name,
                      'file_types': ('Markdown Files (*.md)', 'All Files (*.*)')}
            cur = DOC.path
            if cur:
                kwargs['directory'] = os.path.dirname(cur)
            result = self._window().create_file_dialog(_dialog('SAVE'), **kwargs)
            if not result:
                return None
            filepath = result if isinstance(result, str) else result[0]
            filepath = os.path.abspath(filepath)
            write_text(filepath, content)
            DOC.register(filepath)
            log(f"Saved as: {filepath}")
            return {'ok': True, 'path': filepath, 'filename': os.path.basename(filepath)}
        except Exception as e:
            return {'error': str(e)}

    # --- misc ---

    def set_title(self, title):
        try:
            self._window().set_title(str(title))
        except Exception:
            pass

    def set_dirty(self, flag):
        self.dirty = bool(flag)

    def open_external(self, url):
        """Open an http(s) link in the system browser."""
        try:
            u = str(url)
            if u.lower().startswith(('http://', 'https://', 'mailto:')):
                webbrowser.open(u)
                return True
        except Exception:
            pass
        return False

    def version(self):
        return VERSION


def enable_file_drop(window):
    """Hand the real path of a file dropped from Explorer to the page.

    Page scripts never see a dropped file's path; pywebview (>= 5) adds it
    as `pywebviewFullPath` only for a Python-side DOM handler. The page
    waits briefly for this call (window.mvDroppedPath) and otherwise falls
    back to reading the file's contents without a link to disk.
    """
    try:
        from webview.dom import DOMEventHandler
    except ImportError:
        return

    def on_drop(event):
        for f in (event.get('dataTransfer') or {}).get('files') or []:
            path = f.get('pywebviewFullPath')
            if path:
                window.evaluate_js(f"window.mvDroppedPath && window.mvDroppedPath({json.dumps(path)})")
                return

    try:
        # prevent_default only: the page's own drop listener must still run
        window.dom.document.events.drop += DOMEventHandler(on_drop, True, False)
    except Exception:
        log_exception()


# ========== Path Resolution ==========

def resolve_filepath(argv=None):
    argv = sys.argv if argv is None else argv
    log(f"argv = {argv}")
    if len(argv) < 2:
        return None
    for arg in argv[1:]:
        if arg.startswith('--'):
            continue
        arg = arg.strip().strip('"').strip("'")
        if not arg:
            continue
        try:
            p = Path(arg).resolve()
            if p.is_file() and p.suffix.lower() in MARKDOWN_SUFFIXES:
                log(f"Resolved: {p}")
                return str(p)
        except Exception:
            continue
    # Unquoted path with spaces split across several argv entries
    non_flags = [a for a in argv[1:] if not a.startswith('--')]
    joined = ' '.join(non_flags).strip().strip('"').strip("'")
    if joined:
        try:
            p = Path(joined).resolve()
            if p.is_file():
                return str(p)
        except Exception:
            pass
    return None


def show_error(msg):
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(APP_NAME, msg)
    except Exception:
        pass


# ========== Main ==========

def main():
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
        show_error(msg)
        sys.exit(1)

    # Resolve file from command line
    filepath = resolve_filepath()
    log(f"filepath = {filepath}")
    if filepath:
        filepath = load_initial_file(filepath)

    # Start embedded HTTP server (hidden, user never sees it)
    port = find_free_port()
    if port is None:
        msg = f"No free port in {DEFAULT_PORT}-{DEFAULT_PORT + 99} on 127.0.0.1"
        log(f"FATAL: {msg}")
        show_error(msg)
        sys.exit(1)
    threading.Thread(
        target=start_server,
        args=(port, str(resource_dir)),
        daemon=True,
    ).start()

    if not wait_for_server(port):
        log("WARNING: Server not ready after 5s")

    url = f"http://127.0.0.1:{port}/" + ("?file=1" if filepath else "")
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

    title = f"{os.path.basename(filepath)} — {APP_NAME}" if filepath else APP_NAME

    window_holder = [None]
    api = Api(lambda: window_holder[0])

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

    # Ask before closing a window with unsaved changes.
    def on_closing():
        if not api.dirty:
            return True
        ask = getattr(window, 'create_confirmation_dialog', None)
        if ask is None:
            return True  # old pywebview: cannot ask, do not block the user
        try:
            return bool(ask(APP_NAME, "有未保存的更改。确定要关闭吗？\nUnsaved changes will be lost. Close anyway?"))
        except Exception:
            return True

    try:
        window.events.closing += on_closing
    except Exception:
        log("closing event not supported by this pywebview")

    window.events.loaded += lambda: enable_file_drop(window)

    log("Window created, starting event loop")
    webview.start(debug=('--debug' in sys.argv))
    log("Exiting")


def self_test(report_path):
    """Check a build without opening a window; write a JSON report.

    A windowed exe has no console, so the result goes to a file. Covers what
    a frozen bundle can miss: pywebview and its Windows backend, the bundled
    MarkVue.html, and one round through the server (page with settings
    injected, a settings write). Returns the exit code (0 = all passed).
    """
    import tempfile
    import urllib.request
    checks = {}

    def run(name, fn):
        try:
            res = fn()
            checks[name] = {'ok': res is not False, 'detail': '' if res in (None, True, False) else str(res)}
        except Exception as e:
            checks[name] = {'ok': False, 'detail': f'{type(e).__name__}: {e}'}

    run('import webview', lambda: __import__('webview').__name__)
    run('import webview.dom', lambda: bool(__import__('webview.dom')))
    if sys.platform == 'win32':
        run('import winforms backend', lambda: bool(__import__('webview.platforms.winforms')))
    run('MarkVue.html bundled', lambda: (get_resource_dir() / 'MarkVue.html').is_file())

    def server_round():
        with tempfile.TemporaryDirectory() as d:
            store = SettingsStore(os.path.join(d, 'settings.json'))   # never the user's file
            store.set('markvue-theme', 'light')
            globals()['STORE'] = store
            port = find_free_port(28900)
            threading.Thread(target=start_server, args=(port, str(get_resource_dir())), daemon=True).start()
            assert wait_for_server(port)
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5) as r:
                page = r.read().decode('utf-8')
            assert 'window.MV_STORE = {"markvue-theme": "light"}' in page, 'settings not injected'
            assert '<title>MarkVue</title>' in page
    run('server', server_round)

    ok = all(c['ok'] for c in checks.values())
    report = {'version': VERSION, 'frozen': bool(getattr(sys, 'frozen', False)),
              'python': sys.version.split()[0], 'ok': ok, 'checks': checks}
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    return 0 if ok else 1


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        sys.exit(self_test(sys.argv[2]))
    try:
        main()
    except Exception:
        init_log()
        log("FATAL:")
        log_exception()
        show_error(f"Crash log: {LOG_PATH}\n\n{traceback.format_exc()[-400:]}")
        sys.exit(1)
