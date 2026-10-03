#!/usr/bin/env python3
"""Check README.md and CHANGELOG.md against the code they describe.

Standard library only (CI runs it before installing anything). Exits 1 and
lists every finding when a document has drifted:

  paths      every file in README's project tree exists, and every tracked
             top-level entry is in the tree
  links      relative links and #anchors in README / CHANGELOG / NOTICE resolve
  routes     the server endpoints README lists are the ones markvue_app serves
  shortcuts  the Ctrl shortcuts README lists are the ones MarkVue.html handles
  libraries  the library versions README names are the ones the page loads
  formats    the extensions README says are associated are the ones the
             association script registers
  build      README's build claims hold in build_exe.py (Qt backends excluded)
  tests      the test command README shows is the one that runs the tests
  version    markvue_app.VERSION heads CHANGELOG; README's current release and
             SHA-256 belong to the latest v* tag, when tags are available
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
findings = []


def find(check, msg):
    findings.append(f"[{check}] {msg}")


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


README = read("README.md")
CHANGELOG = read("CHANGELOG.md")
HTML = read("MarkVue.html")
APP = read("markvue_app.py")


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    return out.stdout if out.returncode == 0 else None


def check_paths():
    m = re.search(r"```\nMarkVue/\n(.*?)```", README, re.S)
    if not m:
        return find("paths", "README has no MarkVue/ project tree")
    # Names may contain spaces ("Remove File Association.bat"), so each entry
    # line (two-space indent, then ASCII) is matched against the files on disk.
    on_disk = sorted((str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*")
                      if ".git" not in p.parts), key=len, reverse=True)
    listed = set()
    for line in m.group(1).splitlines():
        if not re.match(r"^  [A-Za-z.]", line):
            continue                              # continuation (translation) lines
        entry = line[2:]
        name = next((p for p in on_disk if entry.rstrip("/") == p or entry.startswith((p + " ", p + "/ "))), None)
        if name is None:
            find("paths", f"README tree lists {entry.split('  ')[0].strip()}, which does not exist")
            continue
        listed.add(name.split("/")[0])
    tracked = git("ls-files")
    if tracked is not None:
        tops = {p.split("/")[0] for p in tracked.splitlines() if p}
        for top in sorted(tops - listed - {".gitignore"}):
            find("paths", f"tracked {top} is missing from README's tree")


def anchors(text):
    out = set()
    for h in re.findall(r"^#+ (.+)$", text, re.M):
        out.add(re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-"))
    return out


def check_links():
    for doc in ("README.md", "CHANGELOG.md", "NOTICE"):
        prose = re.sub(r"`[^`\n]*`", "", read(doc))          # examples in inline code are not links
        for target in re.findall(r"\]\(([^)\s]+)\)", prose):
            if re.match(r"(https?|mailto):", target):
                continue
            path, _, frag = target.partition("#")
            dest = ROOT / path if path else ROOT / doc
            if not dest.exists():
                find("links", f"{doc} links to {target}: no such file")
            elif frag and frag not in anchors(dest.read_text(encoding="utf-8")):
                find("links", f"{doc} links to {target}: no such heading")


def check_routes():
    served = set(re.findall(r"""['"](/api/[\w-]+)['"]""", APP))
    if "'/asset/'" in APP:
        served.add("/asset/")
    section = README.split("The embedded server is locked down", 1)[-1].split("\n- 只有", 1)[0]
    documented = set(re.findall(r"`(/api/[\w-]+)`", section))
    if "`/asset/" in section:
        documented.add("/asset/")
    for r in sorted(served - documented):
        find("routes", f"markvue_app serves {r}, README's endpoint list does not name it")
    for r in sorted(documented - served):
        find("routes", f"README names {r}, markvue_app does not serve it")


def handled_shortcuts():
    out = set()
    for fn in ("function editorKeydown", "function initKeyboard"):
        start = HTML.index(fn)
        body = HTML[start:HTML.index("\n}\n", start)]
        for key, neg in re.findall(r"k === '(\w)' && (!?)e\.shiftKey", body):
            out.add(("Ctrl+" if neg else "Ctrl+Shift+") + key.upper())
        if "e.key === '`'" in body:
            out.add("Ctrl+`")
        if "e.key === '\\\\'" in body:
            out.add("Ctrl+\\")
        m = re.search(r"/\^\[(\d)-(\d)\]\$/", body)
        if m:
            out |= {f"Ctrl+{i}" for i in range(int(m.group(1)), int(m.group(2)) + 1)}
    return out


def check_shortcuts():
    table = README.split("## Keyboard Shortcuts", 1)[-1].split("\n## ", 1)[0]
    documented = set()
    for row in re.findall(r"^\| (.+?) \|", table, re.M):
        keys = [a or b for a, b in re.findall(r"`` (Ctrl\+.) ``|`(Ctrl\+[^`]+)`", row)]
        rng = re.match(r"`Ctrl\+(\d)` ~ `Ctrl\+(\d)`", row)
        if rng:
            keys = [f"Ctrl+{i}" for i in range(int(rng.group(1)), int(rng.group(2)) + 1)]
        documented |= set(keys)
    handled = handled_shortcuts()
    for k in sorted(handled - documented):
        find("shortcuts", f"MarkVue.html handles {k}, README's table does not list it")
    for k in sorted(documented - handled):
        find("shortcuts", f"README lists {k}, MarkVue.html does not handle it")


def check_libraries():
    # every URL of a library (a script and its stylesheet) must carry the same version
    patterns = {"Marked.js": r"marked@([\d.]+)/", "highlight.js": r"highlight\.js/([\d.]+)/",
                "KaTeX": r"katex@([\d.]+)/", "Mermaid": r"mermaid@([\d.]+)/",
                "DOMPurify": r"dompurify@([\d.]+)/"}
    stack = README.split("## Tech Stack", 1)[-1].split("\n## ", 1)[0]
    loaded = {}
    for name, pat in patterns.items():
        versions = sorted(set(re.findall(pat, HTML)))
        if not versions:
            find("libraries", f"MarkVue.html no longer loads {name}")
            continue
        if len(versions) > 1:
            find("libraries", f"MarkVue.html loads {name} at several versions: {versions}")
        loaded[name] = versions[0]
        said = re.search(rf"{re.escape(name)} ([\d.]+)", stack)
        if not said:
            find("libraries", f"README's Tech Stack does not name {name}")
        elif any(not (v + ".").startswith(said.group(1) + ".") for v in versions):
            find("libraries", f"README says {name} {said.group(1)}, the page loads {versions}")
    hl = re.search(r"highlight\.js ([\d.]+) default", README)
    if hl and "highlight.js" in loaded and hl.group(1) != loaded["highlight.js"]:
        find("libraries", f"README's features table says highlight.js {hl.group(1)}, the page loads {loaded['highlight.js']}")


def check_formats():
    bat = read("Associate .md Files.bat")
    loops = [set(x.split()) for x in re.findall(r"for %%E in \(([^)]*)\)", bat)]
    loops += [set(re.findall(r'SupportedTypes" /v "(\.\w+)"', bat))]
    registered = loops[0] if loops else set()
    for other in loops[1:]:
        if other != registered:
            find("formats", f"the association script registers {sorted(registered)} in one place and {sorted(other)} in another")
    m = re.search(r"added to the \"Open with\" menu for (.+?)\. On Windows", README.replace("\n", " "))
    said = set(re.findall(r"\.\w+", m.group(1))) if m else set()
    if registered != said:
        find("formats", f"README says {sorted(said)}, the association script registers {sorted(registered)}")


def check_build():
    tree = ast.parse(read("build_exe.py"))
    excluded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "EXCLUDED_BACKENDS" for t in node.targets):
            excluded = set(ast.literal_eval(node.value))
    if "PyQt5" in README and "PyQt5" not in excluded:
        find("build", "README says the build excludes PyQt5; build_exe.py does not")
    if "build_exe.py" not in read("Build EXE.bat"):
        find("build", "Build EXE.bat does not run build_exe.py")


def check_tests():
    for cmd in re.findall(r"`(python -m unittest[^`]*)`", README):
        if cmd != "python -m unittest discover -s tests":
            find("tests", f"README shows `{cmd}`; the tests run with `python -m unittest discover -s tests`")


def check_version():
    m = re.search(r'^VERSION = "([\d.]+)"', APP, re.M)
    version = m.group(1) if m else None
    head = re.search(r"^## ([\d.]+) — (\S+)", CHANGELOG, re.M)
    if not head or head.group(1) != version:
        find("version", f"CHANGELOG's first section is {head and head.group(1)}, markvue_app says {version}")
    tags = git("tag", "--list", "v*", "--sort=-v:refname")
    if not tags:
        return
    latest = tags.split()[0]
    cur = re.search(r"Current release / 当前版本 \*\*(v[\d.]+)\*\*", README)
    if not cur or cur.group(1) != latest:
        find("version", f"README's current release is {cur and cur.group(1)}, the latest tag is {latest}")
    sha = re.search(r"SHA-256 published with (v[\d.]+)", README)
    if not sha or sha.group(1) != latest:
        find("version", f"README's SHA-256 is for {sha and sha.group(1)}, the latest tag is {latest}")


for fn in (check_paths, check_links, check_routes, check_shortcuts, check_libraries,
           check_formats, check_build, check_tests, check_version):
    fn()

if findings:
    print("\n".join(findings))
    print(f"\ncheck_doc_drift: {len(findings)} finding(s)")
    sys.exit(1)
print("check_doc_drift: 0 findings (paths, links, routes, shortcuts, libraries, formats, build, tests, version)")
