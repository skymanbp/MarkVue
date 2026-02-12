@echo off
title MarkVue Launcher

:: ============================================
::  MarkVue Launcher for Windows
::  Double-click to run. No dependencies needed.
:: ============================================

echo.
echo   ========================================
echo       MarkVue - Markdown Viewer v2.0
echo   ========================================
echo.

set "HTML_FILE=%~dp0MarkVue.html"
set "PY_LAUNCHER=%~dp0markvue.py"
set "PORT=8899"
set "OPEN_FILE="

:: Check if a .md file was dragged onto this bat
if not "%~1"=="" (
    set "OPEN_FILE=%~1"
    echo   [INFO] File detected: %~nx1
    echo.
)

:: Check if MarkVue.html exists
if not exist "%HTML_FILE%" (
    echo   [ERROR] MarkVue.html not found!
    echo   Please make sure MarkVue.html is in the same folder.
    echo.
    pause
    exit /b 1
)

:: Try Python 3 first (better experience with local server)
where python >nul 2>&1
if %errorlevel% equ 0 (
    if exist "%PY_LAUNCHER%" (
        echo   [OK] Python detected. Starting local server...
        echo   [OK] URL: http://localhost:%PORT%
        echo   [TIP] Press Ctrl+C to stop
        echo.
        if defined OPEN_FILE (
            python "%PY_LAUNCHER%" "%OPEN_FILE%"
        ) else (
            python "%PY_LAUNCHER%"
        )
        goto :end
    )
)

:: Try Python via py launcher
where py >nul 2>&1
if %errorlevel% equ 0 (
    if exist "%PY_LAUNCHER%" (
        echo   [OK] Python detected. Starting local server...
        echo   [OK] URL: http://localhost:%PORT%
        echo   [TIP] Press Ctrl+C to stop
        echo.
        if defined OPEN_FILE (
            py "%PY_LAUNCHER%" "%OPEN_FILE%"
        ) else (
            py "%PY_LAUNCHER%"
        )
        goto :end
    )
)

:: Fallback: open HTML directly in browser (still fully functional!)
echo   [OK] Opening in browser (no Python needed)
echo.
start "" "%HTML_FILE%"

echo   [OK] MarkVue is now open in your browser.
echo.
echo   TIP: Install Python for enhanced server mode,
echo        but the HTML file works perfectly on its own!
echo.

timeout /t 3 >nul

:end
