@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ===============================================
echo   Church Service System - Reset Local DB
echo ===============================================
echo.

echo [1/2] Stopping only Church Service System server processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ps=Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and $_.CommandLine -and ($_.CommandLine -match 'run\.py|serve\.py') -and ($_.CommandLine -notmatch 'reset_local\.py') }; foreach($p in $ps){ try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; Write-Host ('Stopped PID ' + $p.ProcessId) } catch {} }"

timeout /t 1 /nobreak >nul

echo [2/2] Resetting local database...
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv is missing. Run launch_fresh.bat first.
  goto :FAIL
)
.venv\Scripts\python.exe scripts\reset_local.py
if errorlevel 1 goto :FAIL

echo.
echo Database reset successfully.
echo Local Super Admin: johnnader
 echo Local password: John@2026!
echo Please change the password after login.
echo.
pause
exit /b 0

:FAIL
echo.
echo RESET FAILED.
pause
exit /b 1