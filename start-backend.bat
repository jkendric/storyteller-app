@echo off
title Storyteller Backend
cd /d "%~dp0backend"

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

:: Create data directories if they don't exist
if not exist "data" mkdir data
if not exist "data\audio" mkdir data\audio
if not exist "data\voice_samples" mkdir data\voice_samples

:: Start the server
echo.
echo Starting Storyteller Backend on http://localhost:8001
echo Press Ctrl+C to stop
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
