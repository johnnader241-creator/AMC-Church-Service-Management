@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

REM Local bootstrap credentials (development only). Existing users are never overwritten.
if not defined BOOTSTRAP_ADMIN_USERNAME set "BOOTSTRAP_ADMIN_USERNAME=johnnader"
if not defined BOOTSTRAP_ADMIN_EMAIL set "BOOTSTRAP_ADMIN_EMAIL=johnnader@local.test"
if not defined BOOTSTRAP_ADMIN_PASSWORD set "BOOTSTRAP_ADMIN_PASSWORD=John@2026!"

echo ===============================================
echo   Church Service System - Local Launcher
echo ===============================================
echo.

REM 1) Find a usable Python launcher.
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo [ERROR] Python is not installed or is not in PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo Then run this file again.
    goto :FAIL
)

echo [1/5] Python: !PY!
!PY! --version
if errorlevel 1 goto :FAIL

REM 2) Create virtual environment.
if not exist ".venv\Scripts\python.exe" (
    echo [2/5] Creating virtual environment...
    !PY! -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create .venv.
        goto :FAIL
    )
) else (
    echo [2/5] Virtual environment already exists.
)

set "VPY=%CD%\.venv\Scripts\python.exe"

REM 3) Upgrade pip and install dependencies using the venv Python directly.
echo [3/5] Installing/checking dependencies...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] pip upgrade failed. Check your Internet connection or Python installation.
    goto :FAIL
)
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    goto :FAIL
)

REM 4) Initialize local data.
if not exist data mkdir data
echo [4/5] Initializing local database...
"%VPY%" scripts\bootstrap.py
if errorlevel 1 (
    echo [ERROR] Database initialization failed.
    echo If you have an old .venv, delete the .venv folder and run this file again.
    goto :FAIL
)

REM 5) Start the app.
echo [5/5] Starting the application...
echo.
echo Open: http://127.0.0.1:5000
echo Close this window to stop the server.
echo.
"%VPY%" run.py
if errorlevel 1 goto :FAIL

goto :EOF

:FAIL
echo.
echo ===============================================
echo   STARTUP FAILED
echo ===============================================
echo.
pause
exit /b 1