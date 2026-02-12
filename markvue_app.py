#!/usr/bin/env python3
"""
MarkVue Desktop Application
============================
Standalone desktop app for MarkVue Markdown viewer.
Designed to be packaged into a single .exe via PyInstaller.

When packaged as EXE:
  - Can be set as default program for .md files
  - Double-click any .md file to open it in MarkVue
  - Drag files onto MarkVue.exe to open them
  - Runs a local HTTP server + opens browser automatically
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import socket
import urllib.parse
import time
import tkinter as tk
from pathlib import Path
from functools import partial

APP_NAME = "MarkVue"
VERSION = "2.2.0"
DEFAULT_PORT = 8899

# ========== Resource Location ==========

def get_resource_dir():
    """
    When frozen by PyInstaller, resources are in sys._MEIPASS.
    When running as script, resources are next to this file.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.resolve()

RESOURCE_DIR = get_resource_dir()
HTML_FILE = RESOURCE_DIR / "MarkVue.html"


# ========== HTTP Server ==========

class Handler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves MarkVue.html and provides file I/O API."""

    def __init__(self, *args, initial_file=None, **kwargs):
        self.initial_file = initial_file
        super().__init__(*args, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        # API: get initial file content + path
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

        # Redirect root to MarkVue.html
        if path in ('/', '/index.html'):
            self.path = '/' + HTML_FILE.name
        super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        # API: save file content back to disk
        if path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                filepath = body.get('path', '')
                content = body.get('content', '')

                if not filepath:
                    self._json(400, {'error': 'No path specified'})
                    return

                # Security: resolve to absolute, ensure parent dir exists
                fp = os.path.abspath(filepath)
                parent = os.path.dirname(fp)
                if not os.path.isdir(parent):
                    self._json(400, {'error': 'Parent directory does not exist'})
                    return

                with open(fp, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)

                self._json(200, {'ok': True, 'path': fp})
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
        return str(RESOURCE_DIR / path)

    def log_message(self, fmt, *args):
        pass  # Suppress console output


def find_free_port(start=DEFAULT_PORT):
    """Find an available TCP port starting from `start`."""
    for p in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return start


def run_server(port, initial_file=None):
    handler = partial(Handler, initial_file=initial_file, directory=str(RESOURCE_DIR))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.serve_forever()


# ========== GUI Control Panel ==========

class MarkVueApp:
    """
    Minimal tkinter window as a control panel.
    All English UI to avoid encoding issues on any Windows locale.
    """

    def __init__(self, port, filepath=None):
        self.port = port
        self.filepath = filepath
        self.url = f"http://127.0.0.1:{port}" + ("?file=1" if filepath else "")

        # Start HTTP server in background
        self.server_thread = threading.Thread(
            target=run_server, args=(port, filepath), daemon=True
        )
        self.server_thread.start()

        # Give server a moment to start
        time.sleep(0.3)

        # Open browser
        webbrowser.open(self.url)

        # Build tkinter window
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        self.root.configure(bg="#111621")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()

    def _build_ui(self):
        bg = "#111621"
        fg = "#c9d1d9"

        # Title
        tk.Label(
            self.root, text=APP_NAME,
            font=("Segoe UI", 18, "bold"), bg=bg, fg="#63b3ed"
        ).pack(pady=(18, 2))

        # Status
        tk.Label(
            self.root, text=f"Server running on port {self.port}",
            font=("Segoe UI", 10), bg=bg, fg="#86efac"
        ).pack(pady=(0, 2))

        # File info
        if self.filepath:
            name = os.path.basename(self.filepath)
            tk.Label(
                self.root, text=f"File: {name}",
                font=("Consolas", 9), bg=bg, fg="#7d8590"
            ).pack(pady=(0, 12))
        else:
            tk.Label(
                self.root, text=self.url,
                font=("Consolas", 9), bg=bg, fg="#7d8590", cursor="hand2"
            ).pack(pady=(0, 12))

        # Buttons
        btn_frame = tk.Frame(self.root, bg=bg)
        btn_frame.pack(pady=(0, 8))

        btn_cfg = dict(
            font=("Segoe UI", 10), bg="#1a1f2e", fg=fg,
            activebackground="#222842", activeforeground="#fff",
            bd=0, padx=16, pady=6, cursor="hand2", relief="flat"
        )

        tk.Button(
            btn_frame, text="Open Browser",
            command=lambda: webbrowser.open(self.url), **btn_cfg
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Minimize",
            command=self.minimize, **btn_cfg
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Quit",
            command=self.quit, **btn_cfg
        ).pack(side="left", padx=4)

        # Hint
        tk.Label(
            self.root,
            text="Closing the window minimizes to taskbar. Click Quit to exit.",
            font=("Segoe UI", 8), bg=bg, fg="#484f58"
        ).pack(side="bottom", pady=(0, 8))

    def minimize(self):
        self.root.iconify()

    def on_close(self):
        self.minimize()

    def quit(self):
        self.root.destroy()
        os._exit(0)

    def run(self):
        self.root.mainloop()


# ========== Entry Point ==========

def resolve_filepath():
    """
    Extract the file to open from command-line arguments.
    Handles: MarkVue.exe "C:\\path\\to\\file.md"
    Also handles: MarkVue.exe C:\\path\\to\\file.md (no quotes)
    """
    if len(sys.argv) < 2:
        return None

    # Join all args after argv[0] in case path has spaces and no quotes
    raw = ' '.join(sys.argv[1:])

    # Strip surrounding quotes if present
    raw = raw.strip('"').strip("'")

    fp = Path(raw).resolve()
    if fp.is_file():
        ext = fp.suffix.lower()
        if ext in ('.md', '.markdown', '.txt', '.text', '.mdx', '.rmd'):
            return str(fp)
    return None


def main():
    # Check HTML exists
    if not HTML_FILE.exists():
        try:
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                APP_NAME,
                f"MarkVue.html not found.\n\n"
                f"Expected location:\n{RESOURCE_DIR}\n\n"
                f"Please keep MarkVue.html next to the application."
            )
        except Exception:
            print(f"ERROR: MarkVue.html not found in {RESOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    filepath = resolve_filepath()
    port = find_free_port()

    app = MarkVueApp(port, filepath)
    app.run()


if __name__ == '__main__':
    main()
