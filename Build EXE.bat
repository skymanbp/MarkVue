@echo off
title MarkVue - Build EXE
chcp 65001 >nul 2>&1

echo.
echo   ========================================
echo       MarkVue EXE Builder  (Native GUI)
echo   ========================================
echo.

set "DIR=%~dp0"

set "WINDOWED=--windowed"
set "MODE=Release"
if "%1"=="--debug" (
    set "WINDOWED="
    set "MODE=Debug (console visible)"
)

:: ===== Find Python =====
set "PY="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python"
    goto :found_py
)
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=py -3"
    goto :found_py
)
echo   [ERROR] Python 3 not found.
echo   https://www.python.org/downloads/
pause
exit /b 1

:found_py
echo   [OK] Python:
%PY% --version
echo   [OK] Mode: %MODE%
echo.

:: ===== Check source files =====
if not exist "%DIR%MarkVue.html" (
    echo   [ERROR] MarkVue.html not found
    pause
    exit /b 1
)
if not exist "%DIR%markvue_app.py" (
    echo   [ERROR] markvue_app.py not found
    pause
    exit /b 1
)
echo   [OK] Source files found
echo.

:: ===== Install dependencies =====
echo   [1/3] Installing dependencies...
echo         (pyinstaller, pywebview)
echo.
%PY% -m pip install pyinstaller pywebview --quiet --disable-pip-version-check 2>nul
if %errorlevel% neq 0 (
    %PY% -m pip install pyinstaller pywebview --user --quiet 2>nul
)
echo   [OK] Dependencies ready
echo.

:: ===== Build =====
echo   [2/3] Building EXE (may take 2~3 minutes)...
echo.

cd /d "%DIR%"
if exist "%DIR%build" rmdir /s /q "%DIR%build" >nul 2>&1
if exist "%DIR%dist\MarkVue.exe" del /q "%DIR%dist\MarkVue.exe" >nul 2>&1

%PY% -m PyInstaller ^
    --onefile %WINDOWED% ^
    --name MarkVue ^
    --add-data "MarkVue.html;." ^
    --hidden-import webview ^
    --hidden-import clr ^
    --collect-all webview ^
    --clean --noconfirm ^
    markvue_app.py

echo.

if not exist "%DIR%dist\MarkVue.exe" (
    echo   [ERROR] Build failed. See errors above.
    echo.
    echo   Try:  Build EXE.bat --debug
    pause
    exit /b 1
)

echo   ========================================
echo       BUILD SUCCESSFUL
echo   ========================================
echo.
echo   Output: %DIR%dist\MarkVue.exe
echo.
echo   This is a native desktop app.
echo   No browser, no server, no port.
echo.
echo   Setup:
echo     1. Move MarkVue.exe to a permanent folder
echo     2. Copy "Associate .md Files.bat" next to it
echo     3. Run "Associate .md Files.bat"
echo     4. Double-click any .md file
echo.

explorer "%DIR%dist"
pause
