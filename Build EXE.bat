@echo off
title MarkVue - Build EXE
chcp 65001 >nul 2>&1

echo.
echo   ========================================
echo       MarkVue EXE Builder
echo   ========================================
echo.

set "DIR=%~dp0"

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
echo   Install from https://www.python.org/downloads/
echo   Check "Add Python to PATH" during install.
echo.
pause
exit /b 1

:found_py
echo   [OK] Python found:
%PY% --version
echo.

:: ===== Check files =====
if not exist "%DIR%MarkVue.html" (
    echo   [ERROR] MarkVue.html not found in:
    echo          %DIR%
    echo.
    pause
    exit /b 1
)
echo   [OK] MarkVue.html found

if not exist "%DIR%markvue_app.py" (
    echo   [ERROR] markvue_app.py not found in:
    echo          %DIR%
    echo.
    pause
    exit /b 1
)
echo   [OK] markvue_app.py found
echo.

:: ===== Install PyInstaller =====
echo   [1/3] Checking PyInstaller...
%PY% -m PyInstaller --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] PyInstaller already installed
    goto :do_build
)

echo   [1/3] Installing PyInstaller...
%PY% -m pip install pyinstaller --quiet --disable-pip-version-check 2>nul
if %errorlevel% equ 0 goto :pip_ok

echo   [WARN] Retrying with --user ...
%PY% -m pip install pyinstaller --user --quiet 2>nul
if %errorlevel% equ 0 goto :pip_ok

echo   [ERROR] Cannot install PyInstaller.
echo   Run manually:  pip install pyinstaller
echo.
pause
exit /b 1

:pip_ok
echo   [OK] PyInstaller installed
echo.

:do_build
:: ===== Clean previous build =====
echo   [2/3] Building EXE (may take 1~2 minutes)...
echo.

cd /d "%DIR%"

:: Remove old build artifacts to avoid conflicts
if exist "%DIR%build" rmdir /s /q "%DIR%build" >nul 2>&1
if exist "%DIR%dist\MarkVue.exe" del /q "%DIR%dist\MarkVue.exe" >nul 2>&1

:: Run PyInstaller
%PY% -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name MarkVue ^
    --add-data "MarkVue.html;." ^
    --clean ^
    --noconfirm ^
    markvue_app.py

echo.

:: ===== Verify =====
if not exist "%DIR%dist\MarkVue.exe" (
    echo   [ERROR] Build failed. Check errors above.
    echo.
    echo   Common fixes:
    echo     1. Close any running MarkVue.exe first
    echo     2. Run:  pip install --upgrade pyinstaller
    echo     3. Temporarily disable antivirus
    echo.
    pause
    exit /b 1
)

echo   ========================================
echo       BUILD SUCCESSFUL
echo   ========================================
echo.
echo   [3/3] Output:
echo         %DIR%dist\MarkVue.exe
echo.
echo   Next steps:
echo     1. Double-click MarkVue.exe to launch
echo     2. Drag .md files onto MarkVue.exe to open them
echo     3. Run "Associate .md Files.bat" to set as default app
echo.

explorer "%DIR%dist"
pause
