@echo off
title MarkVue - File Association Setup
chcp 65001 >nul 2>&1

echo.
echo   ========================================
echo       MarkVue File Association Setup
echo   ========================================
echo.
echo   This will set MarkVue as the default app
echo   for opening .md (Markdown) files.
echo.

:: ===== Locate MarkVue.exe =====
set "EXE_PATH="

:: Check if MarkVue.exe is next to this script
if exist "%~dp0MarkVue.exe" (
    set "EXE_PATH=%~dp0MarkVue.exe"
    goto :found_exe
)

:: Check dist subfolder
if exist "%~dp0dist\MarkVue.exe" (
    set "EXE_PATH=%~dp0dist\MarkVue.exe"
    goto :found_exe
)

echo   [ERROR] MarkVue.exe not found.
echo.
echo   Please put this script in the same folder as
echo   MarkVue.exe, or in the folder containing dist\.
echo.
echo   Expected locations:
echo     %~dp0MarkVue.exe
echo     %~dp0dist\MarkVue.exe
echo.
pause
exit /b 1

:found_exe
echo   [OK] Found: %EXE_PATH%
echo.
echo   The following file types will be associated:
echo     .md  .markdown  .mdx  .rmd
echo.
echo   Press any key to continue, or close this window to cancel.
pause >nul
echo.

:: ===== Register application =====
echo   [1/3] Registering MarkVue application...

:: Create ProgID
reg add "HKCU\Software\Classes\MarkVue.Markdown" /ve /d "Markdown Document" /f >nul 2>&1
reg add "HKCU\Software\Classes\MarkVue.Markdown\DefaultIcon" /ve /d "\"%EXE_PATH%\",0" /f >nul 2>&1
reg add "HKCU\Software\Classes\MarkVue.Markdown\shell\open\command" /ve /d "\"%EXE_PATH%\" \"%%1\"" /f >nul 2>&1

echo   [OK] Application registered

:: ===== Associate file extensions =====
echo   [2/3] Associating file extensions...

for %%E in (.md .markdown .mdx .rmd) do (
    reg add "HKCU\Software\Classes\%%E" /ve /d "MarkVue.Markdown" /f >nul 2>&1
)

:: Set via UserChoice (Windows 10/11 style)
:: Note: UserChoice is protected by a hash on Win10+, so we use the
:: OpenWithProgids approach which adds MarkVue to "Open with" menu
:: and the Classes approach above for direct association.

for %%E in (.md .markdown .mdx .rmd) do (
    reg add "HKCU\Software\Classes\%%E\OpenWithProgids" /v "MarkVue.Markdown" /t REG_NONE /d "" /f >nul 2>&1
)

:: Register in Applications list
reg add "HKCU\Software\Classes\Applications\MarkVue.exe\shell\open\command" /ve /d "\"%EXE_PATH%\" \"%%1\"" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\MarkVue.exe\SupportedTypes" /v ".md" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\MarkVue.exe\SupportedTypes" /v ".markdown" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\MarkVue.exe\SupportedTypes" /v ".mdx" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\MarkVue.exe\SupportedTypes" /v ".rmd" /t REG_SZ /d "" /f >nul 2>&1

echo   [OK] Extensions associated

:: ===== Refresh shell =====
echo   [3/3] Refreshing file explorer...

:: Notify Windows of the change
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.md\UserChoice" /f >nul 2>&1

:: Force refresh icon cache
ie4uinit.exe -show >nul 2>&1

echo   [OK] Done
echo.
echo   ========================================
echo       SETUP COMPLETE
echo   ========================================
echo.
echo   MarkVue is now associated with .md files.
echo.
echo   If double-clicking a .md file still opens another app:
echo     1. Right-click any .md file
echo     2. Choose "Open with" then "Choose another app"
echo     3. Select "MarkVue" and check "Always use this app"
echo.
echo   To undo: run "Remove File Association.bat"
echo.
pause
