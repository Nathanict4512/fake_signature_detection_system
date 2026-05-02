@echo off
echo ================================================
echo Signature Verification System - Installation
echo ================================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo.
echo Installing required libraries...
echo This may take a few minutes...
echo.

python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some libraries
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ================================================
echo Installation completed successfully!
echo ================================================
echo.
echo To start the system, run: run.bat
echo.
pause
