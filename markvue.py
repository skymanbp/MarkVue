#!/usr/bin/env python3
"""
MarkVue - Local Markdown Viewer (Server Mode)
==============================================
Optional Python launcher: serves MarkVue.html on 127.0.0.1 and opens it in
your default browser. Without Python, just double-click MarkVue.html.

The HTTP server itself lives in markvue_app.py and is shared with the
native desktop app, so both modes have the same (locked-down) endpoints.

Usage:
    python markvue.py                  # Launch
    python markvue.py README.md        # Open a file
    python markvue.py -p 3000          # Custom port
    python markvue.py -n               # No auto-open browser
"""

import os
import sys
import signal
import argparse
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from markvue_app import (  # noqa: E402
    APP_NAME, VERSION, DOC, find_free_port, load_initial_file,
    start_server, wait_for_server,
)

DEFAULT_PORT = 8899
SCRIPT_DIR = Path(__file__).parent.resolve()
HTML_FILE = SCRIPT_DIR / "MarkVue.html"


class C:
    B = '\033[94m'; G = '\033[92m'; Y = '\033[93m'
    CY = '\033[96m'; BD = '\033[1m'; DM = '\033[2m'; E = '\033[0m'


def banner(port, filepath=None):
    print(f"""
{C.CY}{C.BD}  ==========================================
       {APP_NAME} - Markdown Viewer v{VERSION}
  =========================================={C.E}

  {C.G}OK{C.E} Server running
  {C.G}OK{C.E} URL: {C.BD}http://localhost:{port}{C.E}""")
    if filepath:
        print(f"  {C.B}>>{C.E} File: {C.BD}{os.path.basename(filepath)}{C.E}")
    print(f"  {C.DM}   Press Ctrl+C to stop{C.E}\n")


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
        if not fp.is_file():
            print(f"ERROR: File not found: {args.file}")
            sys.exit(1)
        initial_file = load_initial_file(str(fp))
        if initial_file is None:
            print(f"ERROR: Could not read: {args.file}")
            sys.exit(1)

    port = find_free_port(args.port)
    if port is None:
        print(f"ERROR: No free port in {args.port}-{args.port + 99} on 127.0.0.1")
        sys.exit(1)
    banner(port, initial_file)

    t = threading.Thread(target=start_server, args=(port, str(SCRIPT_DIR)), daemon=True)
    t.start()
    wait_for_server(port)

    url = f"http://localhost:{port}/" + ("?file=1" if initial_file else "")
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
