@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing required packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install pygame-ce opencv-python mediapipe matplotlib pandas bcrypt openpyxl
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo Starting MS RehaGame...
".venv\Scripts\python.exe" launch_game.py

if errorlevel 1 (
    echo.
    echo The game exited with an error.
    pause
)

endlocal
