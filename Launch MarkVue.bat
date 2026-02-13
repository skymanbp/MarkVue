@echo off
title MarkVue Launcher

echo.
echo   ========================================
echo       MarkVue - Markdown Viewer
echo   ========================================
echo.

set "HTML_FILE=%~dp0MarkVue.html"
set "APP_FILE=%~dp0markvue_app.py"
set "PY_FILE=%~dp0markvue.py"
set "OPEN_FILE="

if not "%~1"=="" (
    set "OPEN_FILE=%~1"
    echo   [INFO] File: %~nx1
    echo.
)

if not exist "%HTML_FILE%" (
    echo   [ERROR] MarkVue.html not found!
    pause
    exit /b 1
)

:: Try native mode (pywebview)
set "PY="
where python >nul 2>&1
if %errorlevel% equ 0 set "PY=python"
if not defined PY (
    where py >nul 2>&1
    if %errorlevel% equ 0 set "PY=py"
)

if defined PY (
    if exist "%APP_FILE%" (
        %PY% -c "import webview" >nul 2>&1
        if %errorlevel% equ 0 (
            echo   [OK] Starting native window...
            if defined OPEN_FILE (
                %PY% "%APP_FILE%" "%OPEN_FILE%"
            ) else (
                %PY% "%APP_FILE%"
            )
            goto :end
        )
    )
    if exist "%PY_FILE%" (
        echo   [OK] Starting server mode...
        if defined OPEN_FILE (
            %PY% "%PY_FILE%" "%OPEN_FILE%"
        ) else (
            %PY% "%PY_FILE%"
        )
        goto :end
    )
)

:: Fallback: open HTML in browser
echo   [OK] Opening in browser...
start "" "%HTML_FILE%"
timeout /t 3 >nul

:end
