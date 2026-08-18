@echo off
setlocal
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."

echo ============================================================
echo Zyntalic Server Startup
echo ============================================================
echo.
echo (Use this script in cmd/PowerShell. For bash/WSL, run scripts\start_server.sh)
echo.

REM The port comes from zyntalic\netconfig.py so this script cannot drift away from the launcher.
REM Set ZYNTALIC_PORT in the environment to override; do not hardcode a number here again.
for /f %%p in ('python -c "from zyntalic.netconfig import resolve_port; print(resolve_port())"') do set ZPORT=%%p
if "%ZPORT%"=="" (
    echo Could not resolve the Zyntalic port. Is Python on PATH and the repo installed?
    exit /b 1
)

echo Checking port %ZPORT%...

REM This script used to taskkill whatever held the port, sight unseen. With the wrong port
REM configured that silently killed an unrelated local API and then reported success. Refuse
REM instead, and let the operator decide -- 'python -m scripts.admin_cli restart' will stop a
REM confirmed Zyntalic process for you.
python -m scripts.admin_cli check-port --port %ZPORT% >nul 2>&1
if not errorlevel 1 (
    echo.
    echo Port %ZPORT% is already in use.
    echo   To see what is there:  python -m scripts.admin_cli status
    echo   To restart Zyntalic:   python -m scripts.admin_cli restart
    echo   To use another port:   set ZYNTALIC_PORT=8005 ^&^& scripts\start_server.bat
    exit /b 1
)

echo Starting Zyntalic server...
echo.
echo Server will be available at: http://127.0.0.1:%ZPORT%
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
python -m scripts.run_desktop
