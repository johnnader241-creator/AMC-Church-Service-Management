@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run launch_fresh.bat to install dependencies.
  pause
  exit /b 1
)
"%CD%\.venv\Scripts\python.exe" serve.py
if errorlevel 1 (
  echo.
  echo Server failed to start.
  pause
)