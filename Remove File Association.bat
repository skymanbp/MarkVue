@echo off
title MarkVue - Remove File Association
chcp 65001 >nul 2>&1

echo.
echo   ========================================
echo       Remove MarkVue File Association
echo   ========================================
echo.
echo   This will remove MarkVue as the default app
echo   for .md files and restore Windows defaults.
echo.
echo   Press any key to continue, or close to cancel.
pause >nul
echo.

echo   Removing registry entries...

reg delete "HKCU\Software\Classes\MarkVue.Markdown" /f >nul 2>&1

for %%E in (.md .markdown .mdx .rmd) do (
    reg delete "HKCU\Software\Classes\%%E" /f >nul 2>&1
)

reg delete "HKCU\Software\Classes\Applications\MarkVue.exe" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.md\UserChoice" /f >nul 2>&1

echo.
echo   [OK] MarkVue file association removed.
echo   You may need to set a new default app for .md files.
echo.
pause
