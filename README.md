# MarkVue — Local Markdown Viewer / 本地 Markdown 查看器

> **A fast, beautiful, feature-rich local Markdown editor and previewer.**
> Build once as EXE, set as default app, double-click any .md file to open.
>
> **快速、美观、功能丰富的本地 Markdown 编辑器与预览器。**
> 一次打包为 EXE，设为默认程序，双击 .md 文件即可打开。

---

## Quick Start: Use as Default App / 快速上手：设为默认程序

The recommended workflow to use MarkVue like a normal desktop application:

推荐流程，让 MarkVue 像普通软件一样使用：

**Step 1** -- Build the EXE / 构建 EXE

```
Double-click "Build EXE.bat"
Wait 1-2 minutes -> dist/MarkVue.exe is created

双击 "Build EXE.bat"
等待 1-2 分钟 -> 生成 dist/MarkVue.exe
```

**Step 2** -- Move EXE to a permanent location / 把 EXE 放到固定位置

```
Example: C:\Tools\MarkVue.exe
示例：C:\Tools\MarkVue.exe
```

**Step 3** -- Associate .md files / 关联 .md 文件

```
Copy "Associate .md Files.bat" next to MarkVue.exe, then double-click it.
Or: right-click any .md file -> "Open with" -> "Choose another app"
    -> select MarkVue.exe -> check "Always use this app"

把 "Associate .md Files.bat" 复制到 MarkVue.exe 旁边，然后双击运行。
或者：右键任意 .md 文件 -> "打开方式" -> "选择其他应用"
      -> 选择 MarkVue.exe -> 勾选"始终使用此应用"
```

**Done.** Now double-click any `.md` file and it opens in MarkVue.

**完成。** 现在双击任意 `.md` 文件即可在 MarkVue 中打开。

---

## All Launch Methods / 所有启动方式

### 1. Double-click HTML (simplest, zero dependencies)

Open `MarkVue.html` directly in any browser. All features work immediately.

直接双击 `MarkVue.html`，在浏览器中打开，全部功能可用。

### 2. Double-click BAT (recommended for Windows without EXE)

Double-click `Launch MarkVue.bat`. It detects Python automatically:
if found, starts a local server; otherwise opens the HTML directly.

双击 `Launch MarkVue.bat`，自动检测 Python 并选择最佳模式。

### 3. MarkVue.exe (recommended, works like a normal app)

After building with `Build EXE.bat`:
- Double-click `MarkVue.exe` to launch.
- Drag `.md` files onto it to open.
- Set as default app for `.md` files (see above).
- Single file, no dependencies, can be copied anywhere.

构建后即可像普通软件一样使用，支持关联文件类型。

### 4. Python server mode (advanced)

```bash
python markvue.py                  # Launch / 启动
python markvue.py README.md        # Open a specific file / 打开指定文件
python markvue.py -p 3000          # Custom port / 指定端口
python markvue.py -n               # No auto-open browser / 不自动打开浏览器
```

---

## Features / 功能

### Core / 核心

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| GitHub-style rendering | Full GFM syntax / 完整 GFM 语法 |
| Real-time preview | 100ms debounce / 输入即渲染 |
| Code highlighting | 100+ languages, one-click copy / 100+ 语言，一键复制 |
| LaTeX math | KaTeX, inline `$...$` and block `$$...$$` / 行内与块级公式 |
| Mermaid diagrams | Flowcharts, sequence, gantt / 流程图、时序图、甘特图 |
| Tables and task lists | GFM extensions / 扩展语法 |

### Unique / 独有功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| Command palette | `Ctrl+K` fuzzy search / 模糊搜索执行命令 |
| Outline navigation | Auto TOC sidebar / 自动大纲侧栏 |
| Slide mode | Split by `---`, keyboard nav / 一键演示文稿 |
| Clipboard image paste | Ctrl+V screenshot to Base64 / 粘贴截图 |
| Find and replace | Full-text search and replace / 全文查找替换 |
| Zen mode | Distraction-free writing / 专注写作模式 |
| Save to file | `Ctrl+S` writes back to original file / 直接保存回原文件 |
| Auto-save | localStorage backup / 浏览器自动保存 |
| Resizable split | Drag divider / 拖动分隔条 |

### Export / 导出

- Markdown (.md) / HTML (.html) / PDF (.pdf)

---

## Keyboard Shortcuts / 快捷键

| Shortcut / 快捷键 | Action / 功能 |
|--------------------|----------------|
| `Ctrl+K` | Command palette / 命令面板 |
| `Ctrl+O` | Open file / 打开文件 |
| `Ctrl+S` | Save / 保存 |
| `Ctrl+Shift+S` | Export Markdown / 导出 Markdown |
| `Ctrl+Shift+E` | Export HTML / 导出 HTML |
| `Ctrl+F` | Find and replace / 查找替换 |
| `Ctrl+B` | Bold / 粗体 |
| `Ctrl+I` | Italic / 斜体 |
| `Ctrl+Shift+O` | Outline sidebar / 大纲侧栏 |

---

## Build EXE / 打包为 EXE

### Requirements / 前提

- Python 3.7+ (only needed to build; the EXE runs without Python)
- Python 3.7+（仅构建时需要，EXE 运行无需 Python）

### Steps / 步骤

1. Double-click `Build EXE.bat`. / 双击 `Build EXE.bat`。
2. Wait 1-2 minutes. / 等待 1-2 分钟。
3. Output: `dist/MarkVue.exe`. / 生成于 `dist/MarkVue.exe`。

### After building / 构建后

- Move `MarkVue.exe` to a permanent location (e.g. `C:\Tools\`).
- Copy `Associate .md Files.bat` next to it and run it.
- Now `.md` files open with MarkVue when double-clicked.

- 将 `MarkVue.exe` 移动到固定位置（如 `C:\Tools\`）。
- 把 `Associate .md Files.bat` 复制到旁边并运行。
- 此后双击 `.md` 文件即可用 MarkVue 打开。

To undo the association, run `Remove File Association.bat`.

取消关联请运行 `Remove File Association.bat`。

---

## Project Structure / 项目结构

```
MarkVue/
  MarkVue.html                Core app (single file, browser-ready)
                              核心应用（单文件，浏览器直接打开）
  Launch MarkVue.bat          Windows launcher (zero dependencies)
                              Windows 启动器（零依赖）
  markvue.py                  Python server mode (optional)
                              Python 服务器模式（可选）
  markvue_app.py              Source for EXE packaging
                              EXE 打包源码
  Build EXE.bat               Build standalone EXE
                              一键构建 EXE
  Associate .md Files.bat     Set MarkVue as default for .md
                              将 MarkVue 设为 .md 默认程序
  Remove File Association.bat Undo the association
                              取消文件关联
  README.md                   This file / 本文件
```

---

## Tech Stack / 技术栈

- Markdown: Marked.js
- Code highlighting: highlight.js
- Math: KaTeX
- Diagrams: Mermaid
- Sanitization: DOMPurify
- PDF export: html2canvas + jsPDF

---

## License / 许可证

MIT License
