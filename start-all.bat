@echo off
echo Starting Storyteller Application...
echo.

:: Start backend in a new window
start "Storyteller Backend" cmd /k "%~dp0start-backend.bat"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak > nul

:: Start frontend in a new window
start "Storyteller Frontend" cmd /k "%~dp0start-frontend.bat"

echo.
echo Both services are starting in separate windows.
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8001/docs
echo.
pause
