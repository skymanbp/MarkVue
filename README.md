# MarkVue — Local Markdown Viewer / 本地 Markdown 查看器

> **A fast, beautiful, feature-rich local Markdown editor and previewer.**
> Single-file, zero dependencies. Double-click the HTML to start.
>
> **快速、美观、功能丰富的本地 Markdown 编辑器与预览器。**
> 单文件运行，零依赖，双击 HTML 即用。

---

## Getting Started / 启动方式

### Method 1: Double-click HTML (simplest, zero dependencies)

Open `MarkVue.html` directly in any browser. All features work out of the box.

直接双击 `MarkVue.html`，在浏览器中打开即可使用全部功能。

### Method 2: Double-click BAT (recommended for Windows)

Double-click `Launch MarkVue.bat`:

- If Python is detected, a local server starts automatically (better experience).
- If Python is not installed, the HTML file opens directly in the browser (fully functional).
- You can drag a `.md` file onto the BAT to open it directly.

双击 `Launch MarkVue.bat`：

- 检测到 Python 时自动启动本地服务器（体验更好）。
- 没有 Python 时直接在浏览器中打开 HTML（功能完全一样）。
- 可将 `.md` 文件拖放到 BAT 上直接打开。

### Method 3: Build a standalone EXE (for distribution)

Double-click `Build EXE.bat` to generate `MarkVue.exe`. See the "Build EXE" section below.
The generated EXE can be shared with anyone — no Python or other dependencies required.

双击 `Build EXE.bat` 一键生成 `MarkVue.exe`，详见下方"打包为 EXE"章节。
生成的 EXE 可以分发给任何 Windows 用户，对方无需安装任何东西。

### Method 4: Python server mode (advanced)

```bash
python markvue.py                  # Launch / 启动
python markvue.py README.md        # Open a specific file / 打开指定文件
python markvue.py -p 3000          # Custom port / 指定端口
python markvue.py -n               # No auto-open browser / 不自动打开浏览器
```

---

## Features / 功能清单

### Core / 核心功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| GitHub-style rendering | Full GFM syntax support / 完整的 GFM 语法支持 |
| Real-time preview | Renders as you type, 100ms debounce / 输入即渲染，100ms 延迟 |
| Code highlighting | 100+ languages, one-click copy / 100+ 语言语法高亮，一键复制 |
| LaTeX math | KaTeX engine, inline `$...$` and block `$$...$$` / 行内与块级公式 |
| Mermaid diagrams | Flowcharts, sequence diagrams, gantt charts / 流程图、时序图、甘特图 |
| Tables and task lists | Full GFM extended syntax / 完整的 GFM 扩展语法 |

### Unique Features / 独有功能

| Feature / 功能 | Description / 说明 |
|----------------|---------------------|
| Command palette | `Ctrl+K` to fuzzy-search and run any command / 模糊搜索并执行任意命令 |
| Outline navigation | Auto-generated TOC sidebar, click to jump / 自动生成大纲侧栏，点击跳转 |
| Slide mode | Split by `---`, present as slides with keyboard nav / 一键变演示文稿，键盘翻页 |
| Clipboard image paste | Paste screenshots as Base64 with Ctrl+V / 截图后粘贴，自动转 Base64 |
| Find and replace | Full-text search with individual or batch replace / 全文搜索，逐个或全部替换 |
| Zen mode | Hides all UI, centered editor for focused writing / 隐藏 UI，居中编辑器，专注写作 |
| Formatting toolbar | Quick insert headings, lists, links, tables, code blocks / 快捷插入各种格式 |
| Auto-save | Saves to localStorage; survives browser close / 自动保存到浏览器，关闭后不丢失 |
| Save to file | `Ctrl+S` writes back to the original file (Chrome/Edge or server mode) / 直接保存回原文件 |
| Theme memory | Dark/light preference is remembered / 深色/浅色偏好自动记忆 |
| Smart word count | Handles mixed CJK and Latin text correctly / 自动识别中英文混合内容分别计数 |
| Resizable split pane | Drag the divider to adjust editor/preview width / 拖动分隔条自由调整宽度 |

### Export / 导出

- **Markdown (.md)** — Plain text / 纯文本
- **HTML (.html)** — Styled standalone page / 带样式的完整 HTML 页面
- **PDF (.pdf)** — PDF document / PDF 文档

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
| `Tab` | Insert indent / 插入缩进 |
| Left / Right arrow | Navigate slides / 幻灯片翻页 |
| `Esc` | Close dialog or exit slides / 退出弹窗或幻灯片 |

---

## Build Standalone EXE / 打包为独立 EXE

### Steps / 步骤

1. Make sure **Python 3.7+** is installed. / 确保已安装 Python 3.7+。
2. Double-click `Build EXE.bat`. / 双击 `Build EXE.bat`。
3. Wait 1-2 minutes. The output appears at `dist/MarkVue.exe`. / 等待 1-2 分钟，生成于 `dist/MarkVue.exe`。

```
dist/
  MarkVue.exe    <-- standalone executable, no dependencies
                     独立可执行文件，无任何依赖
```

### Using the EXE / 使用方式

- Double-click `MarkVue.exe` to launch. / 双击启动。
- Drag a `.md` file onto `MarkVue.exe` to open it. / 拖放 `.md` 文件到图标上直接打开。
- Copy it anywhere — single file, no extra dependencies. / 可复制到任意位置，单文件，无额外依赖。
- The control panel provides buttons to open browser, minimize, and quit. / 控制面板支持打开浏览器、最小化、退出。

The build only needs to be done once. The resulting EXE can be distributed to any Windows user who does not need Python installed.

打包只需执行一次，生成的 EXE 可以分发给任何 Windows 用户，对方不需要安装 Python。

---

## Project Structure / 项目结构

```
MarkVue/
  MarkVue.html          Core app (single file, open in browser)
                        核心应用（单文件，双击即用）
  Launch MarkVue.bat    Windows launcher (zero dependencies)
                        Windows 启动器（零依赖）
  markvue.py            Python server mode (optional)
                        Python 服务器模式（可选）
  markvue_app.py        Desktop app source for EXE packaging
                        EXE 打包用的桌面应用源码
  Build EXE.bat         One-click EXE build script
                        一键构建 EXE 的脚本
  README.md             This file / 本文件
```

---

## Tech Stack / 技术栈

- **Runtime**: Single HTML file, opens directly in any browser / 单个 HTML 文件，浏览器直接打开
- **Markdown**: [Marked.js](https://marked.js.org/)
- **Code highlighting**: [highlight.js](https://highlightjs.org/)
- **Math**: [KaTeX](https://katex.org/)
- **Diagrams**: [Mermaid](https://mermaid-js.github.io/)
- **Sanitization**: [DOMPurify](https://github.com/cure53/DOMPurify)
- **PDF export**: html2canvas + jsPDF
- **Fonts**: Playfair Display, DM Sans, Fira Code, Noto Sans SC

---

## License / 许可证

MIT License
