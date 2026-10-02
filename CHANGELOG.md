# Changelog / 更新日志

## 0.1.0 — 2026-10-02

### Fixed / 修复
- List items lost inline formatting (`**bold**`, `` `code` `` showed as raw text) and task
  checkboxes never rendered: the custom renderer predated marked's token-object API.
  Marked is now pinned (15.0.12) and the renderer uses the current API.
  列表项丢失行内格式、任务复选框不显示：渲染器与 marked 新版 API 不匹配。现已固定版本并改写。
- The "复制" button on code blocks did nothing (its inline `onclick` was stripped by the
  sanitizer). Preview interactions now use event delegation.
  代码块复制按钮无效（内联 onclick 被净化器移除），改为事件委托。
- A new marked renderer was stacked on every keystroke (`marked.use` inside `render()`),
  slowing the editor down over time. 每次输入都叠加一层渲染器的性能泄漏。
- `$` inside code blocks (`$HOME`, `$PATH`) and prices like `$5 and $6` were turned into
  math. Math is now a proper tokenizer extension with pandoc-style boundaries.
  代码块里的 `$` 与货币符号被误判为公式。
- The H3 toolbar button inserted `## `. H3 按钮插入的是二级标题。
- Saved theme "light" caused a dark flash and a double render on start; the theme is now
  applied before first paint and follows the OS until the user picks one.
  浅色主题启动时闪烁并重复渲染；现启动前即应用，并默认跟随系统。
- Blocking CDN `<script>` tags left a blank window when offline; scripts are deferred and
  guarded, the shell loads instantly and the preview degrades to plain text with a notice.
  离线时窗口空白；脚本改为 defer 并加保护，离线降级为纯文本并提示。
- PDF export rasterised the dark preview onto a white page (unreadable) and cut lines in
  half across pages. Export now uses the print engine: selectable text, clean page breaks,
  always light colours. html2canvas and jsPDF are no longer loaded.
  PDF 导出在深色主题下不可读且跨页切行；改用打印引擎，文字可选、分页正确。
- Links in the preview navigated the whole app window away. http(s) links now open in the
  system browser; `#anchor` links jump inside the preview.
  预览里的链接会把整个窗口导航走；现在外链用系统浏览器打开，锚点在预览内跳转。
- Closing the native window, opening another file or creating a new one silently discarded
  unsaved changes. All three now ask first.
  关闭窗口、打开或新建会静默丢弃未保存内容；现在会先询问。

### Security / 安全
- `/api/save` accepted a POST from any website running in the user's browser (a
  `text/plain` body skips the CORS preflight) and wrote to any path on disk. It now
  requires same-origin JSON and only writes files MarkVue itself opened.
  任意网页都能向本地 `/api/save` 写任意文件；现在要求同源 JSON，且只写 MarkVue 打开过的文件。
- The loopback server served the whole program folder (including `markvue-error.log`) and
  accepted any `Host` header. It now serves only MarkVue.html plus the API, and requires a
  loopback Host (DNS-rebinding guard).
  服务器曾暴露整个程序目录并接受任意 Host；现只提供页面与 API，并校验 Host。
- DOMPurify bumped 3.0.6 → 3.4.16; Mermaid runs with `securityLevel: strict`.

### Added / 新增
- Bilingual interface: English by default, 中文 one click away (toolbar / status bar /
  palette), remembered across launches. The sample document exists in both languages.
  界面双语：默认英文，一键切换中文并记忆；示例文档中英各一份。
- Native Open / Save / Save As dialogs in the desktop app via the pywebview bridge
  (previously unused); the open file stays linked by path, drag-and-drop from Explorer too.
  桌面应用使用原生文件对话框，文件按路径关联。
- Relative images next to the open document render (`/asset/` endpoint, folder-confined).
  文档同目录的相对路径图片可显示。
- Clickable task lists: ticking a box in the preview updates the source. 预览里可勾选任务。
- Editing: Enter continues lists / quotes, Tab and Shift+Tab indent blocks, Ctrl+B/I toggle
  off again, Ctrl+1–3 heading levels, Ctrl+` inline code, toolbar actions stay undoable.
  列表自动续写、块缩进、格式可切换、标题快捷键、工具栏操作可撤销。
- Find & replace: case-sensitivity and regex toggles, Enter / Shift+Enter stepping,
  starts from the caret, Ctrl+H focuses replace. 查找替换支持大小写、正则。
- Outline highlights the section being read (scroll spy). 大纲随滚动高亮。
- Command palette searchable in Chinese and English, with mouse hover selection.
  命令面板中英文可搜。
- New file (Ctrl+N), Save As (Ctrl+Shift+S), Ctrl+P for PDF, Ctrl+\ to toggle preview-only,
  Esc closes whatever is open (palette, find bar, slides, zen).
- Status bar shows cursor line/column and the current theme. 状态栏显示光标位置与主题。
- Split ratio and view mode are remembered. 分栏比例与视图模式记忆。
- Mermaid output is cached per diagram; stale async renders are discarded.
- `tests/test_server.py` covers the server guards (stdlib only).

### UI / 界面
- Consistent Chinese labels across toolbar, panes and palette (English names remain as
  search aliases); SVG icons replace emoji in the chrome; tooltips no longer fire instantly;
  view switcher is a segmented control; table and math blocks get horizontal scrolling;
  accessible focus rings; narrow windows keep the view switcher and wrap the format bar.

## 0.0.5
- Previous release: see git history. 见提交历史。
