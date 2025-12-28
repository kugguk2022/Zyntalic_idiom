@echo off
echo ============================================================
echo Zyntalic Server Startup
echo ============================================================
echo.
echo (Use this script in cmd/PowerShell. For bash/WSL, run start_server.sh)
echo.
echo Checking for existing processes on port 8001...

:: Kill any process using port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8001" ^| find "LISTENING"') do (
    echo Killing process %%a on port 8001...
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo Starting Zyntalic server...
echo.
echo Server will be available at: http://127.0.0.1:8001
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
python -m run_desktop
