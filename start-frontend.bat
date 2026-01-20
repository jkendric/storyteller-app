@echo off
title Storyteller Frontend
cd /d "%~dp0frontend"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

:: Start the dev server
echo.
echo Starting Storyteller Frontend on http://localhost:5173
echo Press Ctrl+C to stop
echo.
npm run dev
