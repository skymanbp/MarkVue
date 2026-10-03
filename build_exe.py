#!/usr/bin/env python3
"""Build dist/MarkVue.exe with PyInstaller.

The one place the build options live: "Build EXE.bat" and CI both run it.

    python build_exe.py            # windowed release build
    python build_exe.py --debug    # with a console, for troubleshooting
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# MarkVue runs on the Edge WebView2 backend (clr). pywebview can also drive
# Qt / GTK / CEF, and --collect-all webview pulls in whichever of those is
# installed on the build machine (PyQt5 alone adds ~35 MB), so they are
# excluded: the exe stays ~18 MB wherever it is built.
EXCLUDED_BACKENDS = ["PyQt5", "PyQt6", "PySide2", "PySide6", "qtpy", "gi", "cefpython3"]


def command(debug=False):
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile"]
    if not debug:
        cmd.append("--windowed")
    cmd += [
        "--name", "MarkVue",
        "--add-data", f"MarkVue.html{os.pathsep}.",
        "--hidden-import", "webview",
        "--hidden-import", "clr",
        "--collect-all", "webview",
    ]
    for mod in EXCLUDED_BACKENDS:
        cmd += ["--exclude-module", mod]
    return cmd + ["--clean", "--noconfirm", "markvue_app.py"]


if __name__ == "__main__":
    sys.exit(subprocess.call(command("--debug" in sys.argv[1:]), cwd=ROOT))
