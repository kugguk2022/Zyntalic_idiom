@echo off
REM Start the Zyntalic desktop app with a high max text chars limit
set ZYNTALIC_MAX_TEXT_CHARS=100000000
python run_desktop.py
