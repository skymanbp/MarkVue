@echo off
title MarkVue - Build EXE

echo.
echo   ========================================
echo       MarkVue EXE Builder
echo       Build a standalone executable
echo   ========================================
echo.

:: ===== Locate script directory =====
set "DIR=%~dp0"
echo   [INFO] Working directory: %DIR%
echo.

:: ===== Check Python =====
set PYTHON=
where python >nul 2>&1
if %errorlevel% equ 0 set PYTHON=python
if defined PYTHON goto :found_python

where py >nul 2>&1
if %errorlevel% equ 0 set PYTHON=py
if defined PYTHON goto :found_python

echo   [ERROR] Python not found!
echo.
echo   Please install Python 3.7+ first:
echo   https://www.python.org/downloads/
echo   Make sure to check "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo   [OK] Python found:
%PYTHON% --version
echo.

:: ===== Check MarkVue.html =====
echo   [INFO] Looking for: %DIR%MarkVue.html
if not exist "%DIR%MarkVue.html" goto :no_html
echo   [OK] MarkVue.html found
goto :check_app

:no_html
echo   [ERROR] MarkVue.html not found!
echo   Please put all files in the same folder:
echo     - MarkVue.html
echo     - markvue_app.py
echo     - Build EXE.bat
echo.
pause
exit /b 1

:check_app
:: ===== Check markvue_app.py =====
echo   [INFO] Looking for: %DIR%markvue_app.py
if not exist "%DIR%markvue_app.py" goto :no_app
echo   [OK] markvue_app.py found
echo.
goto :install_pyinstaller

:no_app
echo   [ERROR] markvue_app.py not found!
echo.
pause
exit /b 1

:install_pyinstaller
:: ===== Install PyInstaller =====
echo   [1/3] Installing PyInstaller...
%PYTHON% -m pip install pyinstaller --quiet --disable-pip-version-check
if %errorlevel% neq 0 goto :try_pip_user
echo   [OK] PyInstaller ready
echo.
goto :build

:try_pip_user
echo   [WARN] Retrying with --user flag...
%PYTHON% -m pip install pyinstaller --user --quiet
if %errorlevel% neq 0 goto :pip_fail
echo   [OK] PyInstaller ready
echo.
goto :build

:pip_fail
echo   [ERROR] Failed to install PyInstaller.
echo   Please run manually: pip install pyinstaller
echo.
pause
exit /b 1

:build
:: ===== Build EXE =====
echo   [2/3] Building EXE (this may take 1-2 minutes)...
echo.

cd /d "%DIR%"

%PYTHON% -m PyInstaller --onefile --windowed --name "MarkVue" --add-data "MarkVue.html;." --clean --noconfirm markvue_app.py

echo.

:: ===== Check result =====
if exist "%DIR%dist\MarkVue.exe" goto :success
goto :build_fail

:success
echo   ========================================
echo       BUILD SUCCESSFUL!
echo   ========================================
echo.
echo   [3/3] EXE location:
echo         %DIR%dist\MarkVue.exe
echo.
echo   How to use:
echo     - Double-click MarkVue.exe to launch
echo     - Drag .md files onto MarkVue.exe to open them
echo     - Single file, no dependencies needed
echo.
explorer "%DIR%dist"
goto :done

:build_fail
echo   [ERROR] Build failed!
echo   Check the error messages above.
echo.
echo   Common fixes:
echo   1. Make sure Python 3.7+ is properly installed
echo   2. Run: pip install pyinstaller
echo   3. Restart terminal and try again
echo.

:done
pause
