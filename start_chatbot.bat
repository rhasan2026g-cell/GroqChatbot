@echo off
rem Launch Groq Chat without a console window.
cd /d "%~dp0"

where pythonw >nul 2>nul
if errorlevel 1 (
    echo Python was not found on your PATH.
    echo Install Python 3.10 or newer, then run:  pip install -r requirements.txt
    pause
    exit /b 1
)

start "" pythonw "My Chatbot.py"
