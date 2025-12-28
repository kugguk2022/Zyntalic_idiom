@echo off
REM Thin wrapper to keep backward compatibility. Delegates to scripts/start_server.bat.
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
if exist scripts\start_server.bat (
    call scripts\start_server.bat
) else (
    echo scripts\start_server.bat not found. Please reinstall or run python -m scripts.run_desktop
    exit /b 1
)
