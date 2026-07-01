@echo off
echo Starting Elder Fall Detection App...
echo Using Python from venv...
cd /d "%~dp0"
"venv\Scripts\python.exe" "app.py"
if %errorlevel% neq 0 (
    echo.
    echo Application failed to start!
    echo Please make sure you have installed the requirements using:
    echo venv\Scripts\pip install -r requirements.txt
    pause
)
pause
