@echo off
cd /d "%~dp0"
echo Checking MC2JTD setup...

:: Is Python installed??
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Download it from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

:: Create virtual environment (if missing)
if not exist ".venv" (
    echo First-time setup needed...
    echo Creating virtual environment...
    python -m venv .venv
    echo Activating virtual environment...
    call .venv\Scripts\activate
    echo Upgrading pip...
    python -m pip install --upgrade pip
    echo Installing required packages...
    python -m pip install -r requirements.txt
) else (
    echo Virtual environment found.
    call .venv\Scripts\activate
)

echo Starting MC2JTD...
python main.py
pause
