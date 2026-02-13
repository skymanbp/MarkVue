# MarkVue — Local Markdown Viewer / 本地 Markdown 查看器

> **A native desktop Markdown editor and previewer.**
> Build as EXE, set as default app, double-click any .md file to open.
> No browser, no server, no port. Just a normal application.
>
> **原生桌面 Markdown 编辑器与预览器。**
> 打包为 EXE，设为默认程序，双击 .md 文件即可打开。
> 不需要浏览器、不启动服务器、不占用端口。就是一个普通软件。

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
external browser. File open and save use native system dialogs through a
Python-to-JavaScript bridge.

MarkVue v3 使用 pywebview 将浏览器引擎直接嵌入原生窗口中。HTML/CSS/JS 渲染
在窗口内部运行，不打开外部浏览器。文件打开和保存通过 Python-JS 桥接调用系统
原生对话框。

```
Previous versions            v3 (current)
  Python HTTP server           No server
  -> browser on localhost      -> native window (pywebview)
  -> port 8899                 -> no port
  -> depends on Chrome         -> self-contained
```

---

## All Launch Methods / 所有启动方式

### 1. MarkVue.exe (recommended)

A standalone native application. Double-click to launch, or double-click
any .md file after setting up file association.

独立原生应用。双击启动，或设置文件关联后双击 .md 文件打开。

### 2. Launch MarkVue.bat

Detects Python and available libraries automatically:
- If pywebview is installed: opens native window
- If only Python: starts server mode (opens in browser)
- If no Python: opens MarkVue.html directly in browser

自动检测 Python 和可用的库：
- 如果装了 pywebview：打开原生窗口
- 如果只有 Python：启动服务器模式（在浏览器中打开）
- 如果没有 Python：直接在浏览器中打开 HTML

### 3. Double-click MarkVue.html

Opens in any browser. All features work. No dependencies.

在任何浏览器中打开。全部功能可用。无依赖。

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
| Code highlighting | 100+ languages, copy button / 100+ 语言，一键复制 |
| LaTeX math | KaTeX, inline and block / 行内与块级公式 |
| Mermaid diagrams | Flowcharts, sequence, gantt / 流程图、时序图、甘特图 |
| Native file dialogs | Open, save, save-as / 原生打开、保存、另存为对话框 |

### Extended / 扩展功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| Command palette | `Ctrl+K` fuzzy search / 模糊搜索命令 |
| Outline navigation | Auto TOC sidebar / 大纲侧栏 |
| Slide mode | Split by `---` / 幻灯片模式 |
| Clipboard image paste | Ctrl+V screenshot / 粘贴截图 |
| Find and replace | Full-text / 全文查找替换 |
| Zen mode | Focused writing / 专注写作 |
| Save to file | Ctrl+S native save / 原生保存 |
| Resizable split | Drag divider / 拖动分栏 |

---

## Keyboard Shortcuts / 快捷键

| Shortcut / 快捷键 | Action / 功能 |
|--------------------|----------------|
| `Ctrl+K` | Command palette / 命令面板 |
| `Ctrl+O` | Open file / 打开文件 |
| `Ctrl+S` | Save / 保存 |
| `Ctrl+Shift+S` | Save as / 另存为 |
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
3. Now .md files open with MarkVue when double-clicked.

To undo: run `Remove File Association.bat`.

构建后：
1. 将 `MarkVue.exe` 和 `Associate .md Files.bat` 放在同一文件夹。
2. 双击 `Associate .md Files.bat`。
3. 此后 .md 文件双击用 MarkVue 打开。

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

MIT License
