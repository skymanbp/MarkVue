document.addEventListener("DOMContentLoaded", function () {
  // Initialize variables for performance optimization
  let markdownRenderTimeout = null;
  const RENDER_DELAY = 100; // ms debounce for editor input
  let syncScrollingEnabled = true; // Track sync scrolling state
  let isEditorScrolling = false; // Prevent scroll feedback loops
  let isPreviewScrolling = false; // Prevent scroll feedback loops
  let scrollSyncTimeout = null; // For debouncing scroll events
  const SCROLL_SYNC_DELAY = 10;

  // DOM Elements - cache for better performance
  const markdownEditor = document.getElementById("markdown-editor");
  const markdownPreview = document.getElementById("markdown-preview");
  const themeToggle = document.getElementById("theme-toggle");
  const importButton = document.getElementById("import-button");
  const fileInput = document.getElementById("file-input");
  const exportMd = document.getElementById("export-md");
  const exportHtml = document.getElementById("export-html");
  const exportPdf = document.getElementById("export-pdf");
  const copyHtmlButton = document.getElementById("copy-html-button");
  const dropzone = document.getElementById("dropzone");
  const toggleSyncButton = document.getElementById("toggle-sync");
  const editorPane = document.getElementById("markdown-editor");
  const previewPane = document.querySelector(".preview-pane");
  const readingTimeElement = document.getElementById("reading-time");
  const wordCountElement = document.getElementById("word-count");
  const charCountElement = document.getElementById("char-count");

  // Detect system color scheme preference and set initial theme
  const prefersDarkMode =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.setAttribute(
    "data-theme",
    prefersDarkMode ? "dark" : "light"
  );
  themeToggle.innerHTML = prefersDarkMode
    ? '<i class="bi bi-sun"></i>'
    : '<i class="bi bi-moon"></i>';

  // Initialize marked with GitHub Flavored Markdown
  const markedOptions = {
    gfm: true,
    breaks: false,
    pedantic: false,
    sanitize: false,
    smartypants: false,
    xhtml: false,
    headerIds: true,
    mangle: false,
  };

  // Add syntax highlighting for code blocks
  const renderer = new marked.Renderer();
  renderer.code = function (code, language) {
    const validLanguage = hljs.getLanguage(language) ? language : "plaintext";
    const highlightedCode = hljs.highlight(code, {
      language: validLanguage,
    }).value;
    return `<pre><code class="hljs ${validLanguage}">${highlightedCode}</code></pre>`;
  };

  // Configure marked with our options and renderer
  marked.setOptions({
    ...markedOptions,
    renderer: renderer,
    highlight: function (code, language) {
      const validLanguage = hljs.getLanguage(language) ? language : "plaintext";
      return hljs.highlight(code, { language: validLanguage }).value;
    },
  });

  // Sample markdown to start with
  const sampleMarkdown = `# Welcome to GitHub-Style Markdown Viewer

## Features
- **Live Preview** with GitHub styling
- **Import/Export** Markdown, HTML, and PDF
- **Syntax Highlighting** for code blocks
- **Dark Mode** support
- **Emoji** support 👍
- **Sync Scrolling** between editor and preview
- **Document Stats** showing reading time, word count, and character count

## Code Example
\`\`\`javascript
function renderMarkdown() {
  const markdown = markdownEditor.value;
  const html = marked.parse(markdown);
  const sanitizedHtml = DOMPurify.sanitize(html);
  markdownPreview.innerHTML = sanitizedHtml;
  
  // Apply syntax highlighting to code blocks
  markdownPreview.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
  });
}
\`\`\`

## Task List
- [x] Create Markdown editor
- [x] Implement live preview
- [x] Add GitHub styling
- [x] Support Dark Mode
- [x] Add sync scrolling
- [x] Add document statistics
- [ ] Add more features

## Table Example
| Feature | Status |
|---------|--------|
| Editor | ✅ |
| Preview | ✅ |
| Import | ✅ |
| Export | ✅ |
| Dark Mode | ✅ |
| Sync Scrolling | ✅ |
| Statistics | ✅ |

> **Note:** This is a fully client-side application. Your content stays in your browser.
`;

  // Set the sample markdown
  markdownEditor.value = sampleMarkdown;

  // Function to render markdown with debounce for performance
  function renderMarkdown() {
    try {
      const markdown = markdownEditor.value;
      const html = marked.parse(markdown);
      const sanitizedHtml = DOMPurify.sanitize(html);
      markdownPreview.innerHTML = sanitizedHtml;

      // Apply syntax highlighting to code blocks
      markdownPreview.querySelectorAll("pre code").forEach((block) => {
        try {
          hljs.highlightElement(block);
        } catch (e) {
          console.warn("Syntax highlighting failed for a code block:", e);
        }
      });

      // Process emojis to unicode characters
      processEmojis(markdownPreview);

      // Update stats after rendering
      updateDocumentStats();
    } catch (e) {
      console.error("Markdown rendering failed:", e);
      markdownPreview.innerHTML = `<div class="alert alert-danger">
              <strong>Error rendering markdown:</strong> ${e.message}
          </div>
          <pre>${markdownEditor.value}</pre>`;
    }
  }

  // Emoji handling function - simpler replacement for twemoji
  function processEmojis(element) {
    // This is a minimal implementation. For production, consider using a dedicated emoji library
    // if full emoji support is critical.
  }

  // Debounced render function for better performance
  function debouncedRender() {
    clearTimeout(markdownRenderTimeout);
    markdownRenderTimeout = setTimeout(renderMarkdown, RENDER_DELAY);
  }

  // Calculate reading time, word count, and character count
  function updateDocumentStats() {
    const text = markdownEditor.value;

    // Character count (including spaces)
    const charCount = text.length;
    charCountElement.textContent = charCount.toLocaleString();

    // Word count (splitting by whitespace)
    const wordCount = text.trim() === "" ? 0 : text.trim().split(/\s+/).length;
    wordCountElement.textContent = wordCount.toLocaleString();

    // Reading time calculation (average reading speed: 200 words per minute)
    const readingTimeMinutes = Math.ceil(wordCount / 200);
    readingTimeElement.textContent = readingTimeMinutes;
  }

  // Synchronized scrolling functions
  function syncEditorToPreview() {
    if (!syncScrollingEnabled || isPreviewScrolling) return;

    isEditorScrolling = true;
    clearTimeout(scrollSyncTimeout);

    scrollSyncTimeout = setTimeout(() => {
      const editorScrollRatio =
        editorPane.scrollTop /
        (editorPane.scrollHeight - editorPane.clientHeight);
      const previewScrollPosition =
        (previewPane.scrollHeight - previewPane.clientHeight) *
        editorScrollRatio;

      // Only scroll if the ratio is valid (prevents errors when content is smaller than container)
      if (!isNaN(previewScrollPosition) && isFinite(previewScrollPosition)) {
        previewPane.scrollTop = previewScrollPosition;
      }

      // Reset flag after a short delay to prevent feedback loops
      setTimeout(() => {
        isEditorScrolling = false;
      }, 50);
    }, SCROLL_SYNC_DELAY);
  }

  function syncPreviewToEditor() {
    if (!syncScrollingEnabled || isEditorScrolling) return;

    isPreviewScrolling = true;
    clearTimeout(scrollSyncTimeout);

    scrollSyncTimeout = setTimeout(() => {
      const previewScrollRatio =
        previewPane.scrollTop /
        (previewPane.scrollHeight - previewPane.clientHeight);
      const editorScrollPosition =
        (editorPane.scrollHeight - editorPane.clientHeight) *
        previewScrollRatio;

      // Only scroll if the ratio is valid
      if (!isNaN(editorScrollPosition) && isFinite(editorScrollPosition)) {
        editorPane.scrollTop = editorScrollPosition;
      }

      // Reset flag after a short delay
      setTimeout(() => {
        isPreviewScrolling = false;
      }, 50);
    }, SCROLL_SYNC_DELAY);
  }

  // Toggle sync scrolling
  function toggleSyncScrolling() {
    syncScrollingEnabled = !syncScrollingEnabled;
    if (syncScrollingEnabled) {
      toggleSyncButton.innerHTML = '<i class="bi bi-link-45deg"></i> Sync Off';
      toggleSyncButton.classList.add("sync-disabled");
      toggleSyncButton.classList.remove("sync-enabled");
      toggleSyncButton.classList.add("border-primary");
    } else {
      toggleSyncButton.innerHTML = '<i class="bi bi-link"></i> Sync On';
      toggleSyncButton.classList.add("sync-enabled");
      toggleSyncButton.classList.remove("sync-disabled");
      toggleSyncButton.classList.remove("border-primary");
    }
  }

  renderMarkdown();

  markdownEditor.addEventListener("input", debouncedRender);
  editorPane.addEventListener("scroll", syncEditorToPreview);
  previewPane.addEventListener("scroll", syncPreviewToEditor);
  toggleSyncButton.addEventListener("click", toggleSyncScrolling);

  themeToggle.addEventListener("click", function () {
    const theme =
      document.documentElement.getAttribute("data-theme") === "dark"
        ? "light"
        : "dark";
    document.documentElement.setAttribute("data-theme", theme);

    if (theme === "dark") {
      themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
    } else {
      themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
    }
  });

  // Import button click handler
  importButton.addEventListener("click", function () {
    fileInput.click();
  });

  // File input change handler
  fileInput.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      importMarkdownFile(file);
    }
    // Reset input to allow selecting the same file again
    this.value = "";
  });

  // Function to import markdown file
  function importMarkdownFile(file) {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      markdownEditor.value = e.target.result;
      renderMarkdown();
      // Hide dropzone after successful import
      dropzone.style.display = "none";
    };
    reader.onerror = function (e) {
      console.error("File reading failed:", e);
      alert("Failed to read the file. Please try again.");
    };
    reader.readAsText(file);
  }

  // Export as Markdown
  exportMd.addEventListener("click", function () {
    try {
      const blob = new Blob([markdownEditor.value], {
        type: "text/markdown;charset=utf-8",
      });
      saveAs(blob, "document.md");
    } catch (e) {
      console.error("Export failed:", e);
      alert("Export failed: " + e.message);
    }
  });

  // Export as HTML
  exportHtml.addEventListener("click", function () {
    try {
      const markdown = markdownEditor.value;
      const html = marked.parse(markdown);
      const sanitizedHtml = DOMPurify.sanitize(html);

      // Create a basic HTML document with current theme
      const isDarkTheme =
        document.documentElement.getAttribute("data-theme") === "dark";
      const cssTheme = isDarkTheme
        ? "https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.3.0/github-markdown-dark.min.css"
        : "https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.3.0/github-markdown.min.css";

      const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Markdown Export</title>
  <link rel="stylesheet" href="${cssTheme}">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/${
    isDarkTheme ? "github-dark" : "github"
  }.min.css">
  <style>
      body {
          background-color: ${isDarkTheme ? "#0d1117" : "#ffffff"};
          color: ${isDarkTheme ? "#c9d1d9" : "#24292e"};
      }
      .markdown-body {
          box-sizing: border-box;
          min-width: 200px;
          max-width: 980px;
          margin: 0 auto;
          padding: 45px;
          background-color: ${isDarkTheme ? "#0d1117" : "#ffffff"};
          color: ${isDarkTheme ? "#c9d1d9" : "#24292e"};
      }
      @media (max-width: 767px) {
          .markdown-body {
              padding: 15px;
          }
      }
  </style>
</head>
<body>
  <article class="markdown-body">
      ${sanitizedHtml}
  </article>
</body>
</html>`;

      const blob = new Blob([fullHtml], { type: "text/html;charset=utf-8" });
      saveAs(blob, "document.html");
    } catch (e) {
      console.error("HTML export failed:", e);
      alert("HTML export failed: " + e.message);
    }
  });

  // Export as PDF
  exportPdf.addEventListener("click", function () {
    try {
      if (!window.html2pdf) {
        alert(
          "PDF export library not loaded. Please check your internet connection and try again."
        );
        return;
      }

      const markdown = markdownEditor.value;
      const html = marked.parse(markdown);
      const sanitizedHtml = DOMPurify.sanitize(html);

      // Create a temporary element for PDF conversion
      const tempElement = document.createElement("div");
      tempElement.className = "markdown-body";
      tempElement.innerHTML = sanitizedHtml;
      tempElement.style.padding = "20px";

      // Apply styles for PDF export
      const currentTheme = document.documentElement.getAttribute("data-theme");
      if (currentTheme === "dark") {
        tempElement.style.backgroundColor = "#0d1117";
        tempElement.style.color = "#c9d1d9";
      } else {
        tempElement.style.backgroundColor = "#ffffff";
        tempElement.style.color = "#24292e";
      }

      // Append to body temporarily but hide it
      tempElement.style.position = "absolute";
      tempElement.style.left = "-9999px";
      document.body.appendChild(tempElement);

      // Configure PDF options
      const options = {
        margin: 10,
        filename: "document.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      };

      // Generate PDF with a loading indicator
      const originalText = exportPdf.innerHTML;
      exportPdf.innerHTML =
        '<i class="bi bi-hourglass-split"></i> Generating...';
      exportPdf.disabled = true;

      window
        .html2pdf()
        .from(tempElement)
        .set(options)
        .save()
        .then(() => {
          // Restore button state
          exportPdf.innerHTML = originalText;
          exportPdf.disabled = false;
          // Remove the temporary element
          document.body.removeChild(tempElement);
        })
        .catch((err) => {
          console.error("PDF generation error:", err);
          alert("Failed to generate PDF: " + err.message);
          document.body.removeChild(tempElement);
          exportPdf.innerHTML = originalText;
          exportPdf.disabled = false;
        });
    } catch (e) {
      console.error("PDF export error:", e);
      alert("PDF export failed: " + e.message);
    }
  });

  // Copy HTML button with modern Clipboard API
  copyHtmlButton.addEventListener("click", function () {
    try {
      const markdown = markdownEditor.value;
      const html = marked.parse(markdown);
      const sanitizedHtml = DOMPurify.sanitize(html);

      // Use Clipboard API with fallback
      copyToClipboard(sanitizedHtml);
    } catch (e) {
      console.error("Copy failed:", e);
      alert("Failed to copy HTML: " + e.message);
    }
  });

  // Modern clipboard API with fallback
  async function copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        showCopiedMessage();
      } else {
        // Fallback for browsers that don't support clipboard API
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand("copy");
        document.body.removeChild(textArea);

        if (successful) {
          showCopiedMessage();
        } else {
          throw new Error("Copy command was unsuccessful");
        }
      }
    } catch (err) {
      console.error("Copy failed:", err);
      alert("Failed to copy HTML: " + err.message);
    }
  }

  function showCopiedMessage() {
    const originalText = copyHtmlButton.innerHTML;
    copyHtmlButton.innerHTML = '<i class="bi bi-check-lg"></i> Copied!';

    setTimeout(() => {
      copyHtmlButton.innerHTML = originalText;
    }, 2000);
  }

  // Drag and drop functionality with improved event handling
  const dropEvents = ["dragenter", "dragover", "dragleave", "drop"];

  // Prevent default behavior for all drag events
  dropEvents.forEach((eventName) => {
    dropzone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Visual feedback during drag
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, highlight, false);
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, unhighlight, false);
  });

  function highlight() {
    dropzone.classList.add("active");
  }

  function unhighlight() {
    dropzone.classList.remove("active");
  }

  // Handle dropped files
  dropzone.addEventListener("drop", handleDrop, false);
  dropzone.addEventListener("click", function () {
    fileInput.click();
  });

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length) {
      // Check if the file is a markdown file
      const file = files[0];
      const isMarkdownFile =
        file.type === "text/markdown" ||
        file.name.endsWith(".md") ||
        file.name.endsWith(".markdown");

      if (isMarkdownFile) {
        importMarkdownFile(file);
      } else {
        alert("Please upload a Markdown file (.md or .markdown)");
      }
    }
  }

  // Add keyboard shortcuts for common operations
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      exportMd.click();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === "h") {
      e.preventDefault();
      exportHtml.click();
    }

    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "S") {
      e.preventDefault();
      toggleSyncScrolling();
    }
  });
});
