# MarkVue — Local Markdown Viewer / 本地 Markdown 查看器

> **A native desktop Markdown editor and previewer.**
> Build as EXE, set as default app, double-click any .md file to open.
> No external browser: an embedded server on 127.0.0.1 (port 18737+) stays hidden inside the window. Just a normal application.
>
> **原生桌面 Markdown 编辑器与预览器。**
> 打包为 EXE，设为默认程序，双击 .md 文件即可打开。
> 不打开外部浏览器：内部隐藏运行一个只监听 127.0.0.1 的服务器（端口 18737 起）。就是一个普通软件。

---

## Quick Start / 快速上手

**Step 1** -- Download MarkVue.exe / 下载 MarkVue.exe

```
https://github.com/skymanbp/MarkVue/releases/latest

Download MarkVue.exe. For step 3, also download Associate.md.Files.bat.
下载 MarkVue.exe。需要第 3 步的话，一并下载 Associate.md.Files.bat。
```

Current release / 当前版本 **v0.0.5**. SHA-256 published with v0.0.5 /
该版本发布的校验值:

```
SHA-256  1867e037d8495aa4121fcad3e1c65a2be221dffa49d35ddc833805a39e12b93a  MarkVue.exe
```

Check it with `Get-FileHash MarkVue.exe -Algorithm SHA256` in PowerShell.
在 PowerShell 中用 `Get-FileHash MarkVue.exe -Algorithm SHA256` 核对。

**Step 2** -- Move to a permanent location / 放到固定位置

```
Move MarkVue.exe to e.g. C:\Tools\MarkVue.exe
将 MarkVue.exe 移动到如 C:\Tools\MarkVue.exe
```

**Step 3** -- Set as default app / 设为默认程序

```
Copy Associate.md.Files.bat next to MarkVue.exe, double-click it.
把 Associate.md.Files.bat 复制到 MarkVue.exe 旁边，双击运行。

Or: right-click any .md file -> Open with -> Choose another app
    -> select MarkVue -> check "Always use this app"
或者：右键 .md 文件 -> 打开方式 -> 选择其他应用
      -> 选 MarkVue -> 勾选"始终使用此应用"
```

**Done.** Double-click any `.md` file and it opens in MarkVue.

**完成。** 双击任意 `.md` 文件即可在 MarkVue 中打开。

Building from source instead: see [Build EXE](#build-exe--构建-exe).
想从源码自己构建：见 [Build EXE](#build-exe--构建-exe)。

---

## Architecture / 架构

MarkVue uses pywebview to embed a browser engine directly inside a native
window. The HTML/CSS/JS rendering runs locally in the window, not in an
external browser. In the native app, Open / Save / Save As go through
pywebview's JS bridge to real OS file dialogs, so the open file stays linked
by path; a file dragged in from Explorer is linked too (the window passes its
real path to the page). In plain-browser mode the File System Access pickers
are used, and a file passed on the command line is written back through the
local /api/save endpoint.

Settings (theme, language, view, split) and the unsaved draft are kept in
`%LOCALAPPDATA%\MarkVue\settings.json` when MarkVue runs as the app or through
markvue.py, shared by every open window. Opened straight from disk,
MarkVue.html keeps them in the browser's local storage instead.

MarkVue 使用 pywebview 将浏览器引擎直接嵌入原生窗口中。HTML/CSS/JS 渲染
在窗口内部运行，不打开外部浏览器。原生应用里，打开 / 保存 / 另存为通过
pywebview 的 JS 桥接调用系统文件对话框，打开的文件按路径保持关联（从资源管理
器拖入的文件同样关联）。纯浏览器模式使用 File System Access 选择器；命令行传入
的文件通过本地 /api/save 接口写回。

设置（主题、语言、视图、分栏比例）与未保存的草稿，在桌面应用或 markvue.py 下
保存在 `%LOCALAPPDATA%\MarkVue\settings.json`，所有打开的窗口共用一份；直接
双击 MarkVue.html 打开时则保存在浏览器的本地存储里。

The embedded server is locked down / 内置服务器做了最小化与加固:

- Only `/` (MarkVue.html), `/api/initial-file`, `/api/save`, `/api/store` and
  `/asset/<file>` exist; nothing else in the program folder is reachable.
- Every request needs a loopback `Host` header (DNS-rebinding guard).
- `/api/save` accepts only same-origin `application/json`, and only writes
  files that MarkVue itself opened — never an arbitrary path.
- `/api/store` writes only MarkVue's own settings file, under the same
  same-origin JSON rule, and only `markvue-*` keys.
- `/asset/` serves images that sit next to the open document (so relative
  `![](img.png)` works) and refuses to leave that folder.

- 只有 `/`（MarkVue.html）、`/api/initial-file`、`/api/save`、`/api/store`、
  `/asset/<文件>` 五个路径，程序目录中的其他文件一律不可访问。
- 所有请求必须带回环地址的 `Host` 头（防 DNS 重绑定）。
- `/api/save` 只接受同源的 `application/json`，且只写 MarkVue 自己打开过的文件。
- `/api/store` 只写 MarkVue 自己的设置文件，同样只接受同源 JSON，且只认 `markvue-*` 键。
- `/asset/` 提供文档同目录下的图片（相对路径 `![](img.png)` 可用），不会越出该目录。

Both launch methods share this one server implementation (markvue.py imports
it from markvue_app.py). `python -m unittest discover -s tests` checks the
guards. / 两种启动方式共用同一份服务器实现（markvue.py 从 markvue_app.py 导入），
`python -m unittest discover -s tests` 可验证这些防护。

```
Server mode (markvue.py)     Native mode (current)
  Python HTTP server           Embedded HTTP server
  -> browser on localhost      -> native window (pywebview)
  -> port 8899                 -> port 18737+, loopback only
  -> depends on Chrome         -> system WebView2; libs from CDN
```

---

## All Launch Methods / 所有启动方式

### 1. MarkVue.exe (recommended)

A standalone native application. Double-click to launch, or double-click
any .md file after setting up file association.

独立原生应用。双击启动，或设置文件关联后双击 .md 文件打开。

### 2. Launch MarkVue.bat

Detects Python automatically:
- If `python` is on PATH: runs markvue_app.py — native window when pywebview
  is installed, otherwise your system browser
- Otherwise: opens MarkVue.html directly in browser

自动检测 Python：
- 如果 PATH 中有 `python`：运行 markvue_app.py —— 装了 pywebview 就打开原生窗口，
  否则打开系统浏览器
- 否则：直接在浏览器中打开 HTML

### 3. Double-click MarkVue.html

Opens in any browser. Needs an internet connection — the rendering libraries
load from CDN. Best in a Chromium-based browser; Firefox and Safari have no
File System Access API, so Save falls back to a download.

在任何浏览器中打开。需要联网——渲染库从 CDN 加载。Chromium 内核浏览器体验最好；
Firefox 和 Safari 没有 File System Access API，保存会降级为下载。

### 4. Python server mode

```bash
python markvue.py                  # Launch / 启动
python markvue.py README.md        # Open file / 打开文件
python markvue.py -p 3000          # Custom port / 指定端口
```

---

## Features / 功能

### Core / 核心

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| GitHub-style rendering | Full GFM syntax, heading anchors (`#标题` links work) / 完整 GFM 语法，标题锚点可跳转 |
| Real-time preview | 120ms debounce, stale renders discarded / 输入即渲染，丢弃过期渲染 |
| Code highlighting | 36 languages bundled by highlight.js 11.9.0, copy button / highlight.js 11.9.0 默认包内置 36 种语言，一键复制 |
| LaTeX math | KaTeX `$…$` / `$$…$$`; `$5 and $6` and `$HOME` in code stay text / 行内与块级公式，货币符号与代码里的 `$` 不会误判 |
| Mermaid diagrams | Flowcharts, sequence, gantt; rendered once and cached / 流程图、时序图、甘特图，结果缓存 |
| Clickable task lists | Tick a box in the preview, the source updates / 预览里勾选，源码同步 |
| Relative images | `![](img.png)` next to the open file just works / 文档同目录图片直接显示 |
| Links | http(s) links open in the system browser, `#anchors` jump inside the preview / 外链用系统浏览器打开，锚点在预览内跳转 |
| File dialogs | Native dialogs in the app, WebView pickers in a browser / 原生对话框，浏览器里用 WebView 选择器 |
| Offline | Works without the CDN: shell loads, preview shows plain text with a notice / 无网络时界面照常，预览降级为纯文本并提示 |

### Extended / 扩展功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| Command palette | `Ctrl+K`, searchable in Chinese or English / 中英文都能搜 |
| Outline navigation | Auto TOC sidebar, highlights the section you are reading / 大纲侧栏，随滚动高亮 |
| Slide mode | Split by `---`, arrow keys, Home/End, progress bar / 幻灯片模式 |
| Clipboard image paste | Ctrl+V screenshot / 粘贴截图 |
| Find and replace | Case toggle, regex toggle, Enter / Shift+Enter to step / 区分大小写、正则，回车逐个跳转 |
| Smart editing | Enter continues lists and quotes, Tab / Shift+Tab indents blocks, Ctrl+B toggles bold off again, undo keeps working / 列表自动续写，块缩进，加粗可切换，撤销有效 |
| Zen mode | Focused writing, Esc leaves / 专注写作，Esc 退出 |
| Save / Save As | Ctrl+S writes back, Ctrl+Shift+S picks a new location / 写回或另存 |
| Unsaved-change guard | Asks before closing, opening or creating over unsaved work / 关闭、打开、新建前提醒未保存 |
| Export | Markdown, standalone HTML, real text PDF via the print dialog / Markdown、独立 HTML、通过打印对话框生成可选择文字的 PDF |
| Theme | Follows the OS until you pick one; no flash on start / 跟随系统，启动不闪烁 |
| Language | English by default; one click (toolbar `中` / `EN`, status bar, or palette) switches the whole UI and sample to 中文, remembered / 默认英文，一键切换中文并记忆 |
| Resizable split | Drag divider, double-click to reset, remembered / 拖动分栏，双击复位，自动记忆 |
| Draft auto-save | Unsaved text is kept 1.5 s after you stop typing and comes back when MarkVue next starts without a file / 停止输入 1.5 秒后保存草稿，下次不带文件启动时恢复 |

---

## Keyboard Shortcuts / 快捷键

| Shortcut / 快捷键 | Action / 功能 |
|--------------------|----------------|
| `Ctrl+K` | Command palette / 命令面板 |
| `Ctrl+N` | New file / 新建 |
| `Ctrl+O` | Open file / 打开文件 |
| `Ctrl+S` | Save / 保存 |
| `Ctrl+Shift+S` | Save as / 另存为 |
| `Ctrl+E` | Export HTML / 导出 HTML |
| `Ctrl+P` | Export PDF (print dialog) / 导出 PDF（打印对话框） |
| `Ctrl+F` / `Ctrl+H` | Find / replace / 查找、替换 |
| `Ctrl+B` / `Ctrl+I` / `` Ctrl+` `` | Bold / italic / inline code (toggle) / 粗体、斜体、行内代码（可切换） |
| `Ctrl+1` ~ `Ctrl+3` | Heading level / 标题级别 |
| `Ctrl+Shift+L` | Insert link / 插入链接 |
| `Tab` / `Shift+Tab` | Indent / outdent (multi-line) / 缩进、反缩进 |
| `Ctrl+Shift+O` | Outline / 大纲 |
| `Ctrl+\` | Split ⇄ preview only / 分屏与仅预览切换 |
| `Esc` | Close palette, find bar, slides, zen / 关闭面板、查找栏、幻灯片、禅模式 |

The interface is English by default; the `中` button in the toolbar (or the
status bar, or the palette command "Language") switches it to Chinese and the
choice is remembered. / 界面默认英文，工具栏的 `中` 按钮（或状态栏、命令面板的
"语言"）切换为中文，选择会被记住。

On macOS use `⌘` instead of `Ctrl`. / macOS 上用 `⌘` 代替 `Ctrl`。

---

## Build EXE / 构建 EXE

Optional — the release already ships a built MarkVue.exe (Quick Start step 1).
Requirements: Python 3.8+ (only for building; EXE runs independently).

可选 —— release 里已经有构建好的 MarkVue.exe（快速上手第 1 步）。
前提：Python 3.8+（仅构建时需要，EXE 独立运行）。

```
1. Double-click "Build EXE.bat"  /  双击 "Build EXE.bat"
2. Wait 2-3 minutes  /  等待 2-3 分钟
3. Output: dist/MarkVue.exe  /  生成 dist/MarkVue.exe
```

The build options live in `build_exe.py` (`python build_exe.py` does the same
without the bat). Release EXEs are built by CI from a version tag with that
script and checked with `MarkVue.exe --self-test report.json`, which tests the
bundle without opening a window.

打包参数统一在 `build_exe.py`（不用 bat 时直接 `python build_exe.py`）。发布用的
EXE 由 CI 按版本标签用同一脚本构建，并用 `MarkVue.exe --self-test report.json`
在不开窗口的情况下自检。

The script excludes pywebview's Qt backend, so a build machine that happens
to have PyQt5 installed still produces the small Edge WebView2 build
(~18 MB, not ~53 MB).

脚本会排除 pywebview 的 Qt 后端，所以构建机器上即使装了 PyQt5，产出的仍然是
基于 Edge WebView2 的小体积版本（约 18 MB，而不是约 53 MB）。

For troubleshooting, build with console: `Build EXE.bat --debug`

排查问题时用调试模式：`Build EXE.bat --debug`

---

## File Association / 文件关联

After building the EXE:

1. Put `MarkVue.exe` and `Associate .md Files.bat` in the same folder.
2. Double-click `Associate .md Files.bat`.
3. MarkVue is registered and added to the "Open with" menu for .md, .markdown,
   .mdx and .rmd. On Windows 10/11 the double-click default is hash-protected,
   so you may still need to pick it once: right-click a .md file -> Open with
   -> Choose another app -> select MarkVue -> check "Always use this app".

To undo: run `Remove File Association.bat`.

构建后：
1. 将 `MarkVue.exe` 和 `Associate .md Files.bat` 放在同一文件夹。
2. 双击 `Associate .md Files.bat`。
3. MarkVue 会被注册并加入 .md、.markdown、.mdx、.rmd 的"打开方式"菜单。
   Windows 10/11 的双击默认程序受哈希保护，可能还需手动指定一次：右键 .md
   文件 -> 打开方式 -> 选择其他应用 -> 选 MarkVue -> 勾选"始终使用此应用"。

撤销：运行 `Remove File Association.bat`。

---

## Project Structure / 项目结构

```
MarkVue/
  MarkVue.html                Core rendering engine
                              核心渲染引擎
  markvue_app.py              Native app source (pywebview)
                              原生应用源码
  markvue.py                  Server mode (optional, browser-based)
                              服务器模式（可选）
  Build EXE.bat               Build standalone EXE
                              构建 EXE
  Launch MarkVue.bat          Smart launcher
                              智能启动器
  Associate .md Files.bat     Set as default for .md
                              设为默认程序
  Remove File Association.bat Undo association
                              撤销关联
  build_exe.py                Build options (used by the bat and CI)
                              打包参数（bat 与 CI 共用）
  tests/test_server.py        Server guard tests (stdlib unittest)
                              服务器防护测试
  scripts/check_doc_drift.py  Checks this README against the code (CI)
                              文档与代码一致性检查（CI 运行）
  .github/workflows/          CI (tests, docs, build + self-test) and release
                              持续集成与发布
  CHANGELOG.md                Release notes / 更新日志
  README.md                   This file / 本文件
  LICENSE                     Apache License 2.0
                              Apache 2.0 许可证
  NOTICE                      Attribution and statement of changes
                              署名与改动说明
```

---

## Tech Stack / 技术栈

- Native window: pywebview (EdgeChromium on Windows)
- Markdown: Marked.js 15 (pinned)
- Code: highlight.js 11.9
- Math: KaTeX 0.16
- Diagrams: Mermaid 10
- Security: DOMPurify 3.4 (every rendered fragment is sanitized)
- PDF: the WebView's own print engine (text stays selectable, pages break cleanly)

---

## License / 许可证

Apache License 2.0 — see [LICENSE](LICENSE).

MarkVue is a fork of [ThisIs-Developer/Markdown-Viewer](https://github.com/ThisIs-Developer/Markdown-Viewer),
which is licensed under Apache-2.0. Attribution and the statement of changes
are in [NOTICE](NOTICE).

Apache License 2.0 —— 见 [LICENSE](LICENSE)。

MarkVue 派生自 [ThisIs-Developer/Markdown-Viewer](https://github.com/ThisIs-Developer/Markdown-Viewer)，
该项目采用 Apache-2.0 许可。署名与改动说明见 [NOTICE](NOTICE)。
