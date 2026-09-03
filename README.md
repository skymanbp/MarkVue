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

**Step 1** -- Build the EXE / 构建 EXE

```
Double-click "Build EXE.bat", wait 2-3 minutes.
双击 "Build EXE.bat"，等待 2-3 分钟。
```

**Step 2** -- Move to a permanent location / 放到固定位置

```
Move dist/MarkVue.exe to e.g. C:\Tools\MarkVue.exe
将 dist/MarkVue.exe 移动到如 C:\Tools\MarkVue.exe
```

**Step 3** -- Set as default app / 设为默认程序

```
Copy "Associate .md Files.bat" next to MarkVue.exe, double-click it.
把 "Associate .md Files.bat" 复制到 MarkVue.exe 旁边，双击运行。

Or: right-click any .md file -> Open with -> Choose another app
    -> select MarkVue -> check "Always use this app"
或者：右键 .md 文件 -> 打开方式 -> 选择其他应用
      -> 选 MarkVue -> 勾选"始终使用此应用"
```

**Done.** Double-click any `.md` file and it opens in MarkVue.

**完成。** 双击任意 `.md` 文件即可在 MarkVue 中打开。

---

## Architecture / 架构

MarkVue v3 uses pywebview to embed a browser engine directly inside a native
window. The HTML/CSS/JS rendering runs locally in the window, not in an
external browser. File open and save use the WebView's File System Access
pickers; a file the app was launched with is written back through the app's
local /api/save endpoint.

MarkVue v3 使用 pywebview 将浏览器引擎直接嵌入原生窗口中。HTML/CSS/JS 渲染
在窗口内部运行，不打开外部浏览器。文件打开和保存使用 WebView 的 File System
Access 选择器；启动时传入的文件通过应用本地的 /api/save 接口写回。

```
Server mode (markvue.py)     v3 (current)
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
| GitHub-style rendering | Full GFM syntax / 完整 GFM 语法 |
| Real-time preview | 100ms debounce / 输入即渲染 |
| Code highlighting | 36 languages bundled by highlight.js 11.9.0, copy button / highlight.js 11.9.0 内置 36 种语言，一键复制 |
| LaTeX math | KaTeX, inline and block / 行内与块级公式 |
| Mermaid diagrams | Flowcharts, sequence, gantt / 流程图、时序图、甘特图 |
| File dialogs | WebView open/save pickers / WebView 打开、保存选择器 |

### Extended / 扩展功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| Command palette | `Ctrl+K` filter by name / 按名称筛选命令 |
| Outline navigation | Auto TOC sidebar / 大纲侧栏 |
| Slide mode | Split by `---` / 幻灯片模式 |
| Clipboard image paste | Ctrl+V screenshot / 粘贴截图 |
| Find and replace | Full-text / 全文查找替换 |
| Zen mode | Focused writing / 专注写作 |
| Save to file | Ctrl+S writes back to the open file / 写回已打开的文件 |
| Resizable split | Drag divider / 拖动分栏 |

---

## Keyboard Shortcuts / 快捷键

| Shortcut / 快捷键 | Action / 功能 |
|--------------------|----------------|
| `Ctrl+K` | Command palette / 命令面板 |
| `Ctrl+O` | Open file / 打开文件 |
| `Ctrl+S` | Save / 保存 |
| `Ctrl+Shift+S` | Export Markdown / 导出 Markdown |
| `Ctrl+E` | Export HTML / 导出 HTML |
| `Ctrl+F` | Find and replace / 查找替换 |
| `Ctrl+B` | Bold / 粗体 |
| `Ctrl+I` | Italic / 斜体 |
| `Ctrl+Shift+O` | Outline / 大纲 |

---

## Build EXE / 构建 EXE

Requirements: Python 3.8+ (only for building; EXE runs independently).
前提：Python 3.8+（仅构建时需要，EXE 独立运行）。

```
1. Double-click "Build EXE.bat"  /  双击 "Build EXE.bat"
2. Wait 2-3 minutes  /  等待 2-3 分钟
3. Output: dist/MarkVue.exe  /  生成 dist/MarkVue.exe
```

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
  README.md                   This file / 本文件
  LICENSE                     Apache License 2.0
                              Apache 2.0 许可证
  NOTICE                      Attribution and statement of changes
                              署名与改动说明
```

---

## Tech Stack / 技术栈

- Native window: pywebview (EdgeChromium on Windows)
- Markdown: Marked.js
- Code: highlight.js
- Math: KaTeX
- Diagrams: Mermaid
- Security: DOMPurify
- PDF: html2canvas + jsPDF

---

## License / 许可证

Apache License 2.0 — see [LICENSE](LICENSE).

MarkVue is a fork of [ThisIs-Developer/Markdown-Viewer](https://github.com/ThisIs-Developer/Markdown-Viewer),
which is licensed under Apache-2.0. Attribution and the statement of changes
are in [NOTICE](NOTICE).

Apache License 2.0 —— 见 [LICENSE](LICENSE)。

MarkVue 派生自 [ThisIs-Developer/Markdown-Viewer](https://github.com/ThisIs-Developer/Markdown-Viewer)，
该项目采用 Apache-2.0 许可。署名与改动说明见 [NOTICE](NOTICE)。
