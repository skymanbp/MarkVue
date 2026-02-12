#!/usr/bin/env python3
"""
MarkVue Desktop Launcher
=========================
This script is designed to be packaged into a standalone .exe via PyInstaller.
It embeds MarkVue.html, starts a local server, and opens the browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import signal
import socket
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from functools import partial

APP_NAME = "MarkVue"
VERSION = "2.0.0"
PORT = 8899
ICON = None  # Will be set if icon exists

# ========== Locate Resources ==========
def get_resource_dir():
    """Get the directory containing MarkVue.html"""
    # When running as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    # When running as script
    return Path(__file__).parent.resolve()

RESOURCE_DIR = get_resource_dir()
HTML_FILE = RESOURCE_DIR / "MarkVue.html"

# ========== HTTP Server ==========
class MarkVueHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, initial_file=None, **kwargs):
        self.initial_file = initial_file
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

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
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(data.encode('utf-8'))
                    return
                except Exception:
                    pass
            self.send_response(204)
            self.end_headers()
            return

        if parsed.path in ('/', '/index.html'):
            self.path = '/' + HTML_FILE.name

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/save':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode('utf-8'))
                filepath = body.get('path', '')
                content = body.get('content', '')
                if not filepath or not os.path.exists(filepath):
                    self._err(400, 'Invalid path')
                    return
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                return
            except Exception as e:
                self._err(500, str(e))
                return
        self.send_error(404)

    def _err(self, code, msg):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': msg}).encode('utf-8'))

    def translate_path(self, path):
        path = urllib.parse.unquote(path.split('?', 1)[0].split('#', 1)[0]).strip('/')
        if not path or path == 'index.html':
            return str(HTML_FILE)
        return str(RESOURCE_DIR / path)

    def log_message(self, fmt, *args):
        pass


def find_port(start=PORT):
    for p in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', p))
                return p
        except OSError:
            continue
    return start


def start_server(port, initial_file=None):
    handler = partial(MarkVueHandler, initial_file=initial_file, directory=str(RESOURCE_DIR))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        httpd.serve_forever()


# ========== Tray-like Window ==========
class MarkVueApp:
    """Minimal tkinter window that acts as a control panel."""

    def __init__(self, port, initial_file=None):
        self.port = port
        self.initial_file = initial_file
        self.url = f"http://localhost:{port}" + ("?file=1" if initial_file else "")

        # Start server
        self.server_thread = threading.Thread(
            target=start_server,
            args=(port, initial_file),
            daemon=True
        )
        self.server_thread.start()

        # Open browser
        webbrowser.open(self.url)

        # Create control window
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("380x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#111621")

        # Try to set icon
        try:
            icon_path = RESOURCE_DIR / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

        # Prevent closing from X, minimize instead
        self.root.protocol("WM_DELETE_WINDOW", self.minimize)

        self.build_ui()

    def build_ui(self):
        bg = "#111621"
        fg = "#c9d1d9"
        accent = "#63b3ed"

        # Title
        title = tk.Label(
            self.root, text=f"📝 {APP_NAME}", font=("Segoe UI", 16, "bold"),
            bg=bg, fg=accent
        )
        title.pack(pady=(20, 4))

        # Status
        status = tk.Label(
            self.root, text=f"✅ 服务运行中  ·  端口 {self.port}",
            font=("Segoe UI", 10), bg=bg, fg="#86efac"
        )
        status.pack(pady=(0, 4))

        url_label = tk.Label(
            self.root, text=self.url, font=("Consolas", 9),
            bg=bg, fg="#7d8590", cursor="hand2"
        )
        url_label.pack(pady=(0, 16))
        url_label.bind("<Button-1>", lambda e: webbrowser.open(self.url))

        # Buttons frame
        btn_frame = tk.Frame(self.root, bg=bg)
        btn_frame.pack(pady=(0, 10))

        btn_style = dict(
            font=("Segoe UI", 10), bg="#1a1f2e", fg=fg,
            activebackground="#222842", activeforeground="#fff",
            bd=0, padx=16, pady=6, cursor="hand2", relief="flat"
        )

        open_btn = tk.Button(
            btn_frame, text="🌐 打开浏览器",
            command=lambda: webbrowser.open(self.url), **btn_style
        )
        open_btn.pack(side="left", padx=4)

        hide_btn = tk.Button(
            btn_frame, text="📥 最小化",
            command=self.minimize, **btn_style
        )
        hide_btn.pack(side="left", padx=4)

        quit_btn = tk.Button(
            btn_frame, text="⏹ 退出",
            command=self.quit, **btn_style
        )
        quit_btn.pack(side="left", padx=4)

        # Hint
        hint = tk.Label(
            self.root, text="关闭此窗口会最小化到后台，点击「退出」彻底关闭",
            font=("Segoe UI", 8), bg=bg, fg="#484f58"
        )
        hint.pack(side="bottom", pady=(0, 10))

    def minimize(self):
        self.root.withdraw()
        # On Windows, show in taskbar notification
        self.root.after(100, self._show_restore_hint)

    def _show_restore_hint(self):
        """Re-show the window after a brief hide (simple tray simulation)."""
        # For a real tray icon, pystray would be needed.
        # This simple approach just minimizes to taskbar.
        self.root.iconify()
        self.root.deiconify()
        self.root.state('iconic')

    def quit(self):
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


# ========== Main ==========
def main():
    if not HTML_FILE.exists():
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                APP_NAME,
                f"未找到 MarkVue.html\n请确保它与程序在同一目录。\n\n查找路径: {RESOURCE_DIR}"
            )
        except Exception:
            print(f"ERROR: MarkVue.html not found in {RESOURCE_DIR}")
        sys.exit(1)

    # Check if a file was passed as argument (e.g., dragged onto .exe)
    initial_file = None
    if len(sys.argv) > 1:
        fp = Path(sys.argv[1]).resolve()
        if fp.exists() and fp.suffix.lower() in ('.md', '.markdown', '.txt', '.text'):
            initial_file = str(fp)

    port = find_port()
    app = MarkVueApp(port, initial_file)
    app.run()


if __name__ == '__main__':
    main()
