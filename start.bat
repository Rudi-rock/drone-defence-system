@echo off
REM Drone Swarm Security System — Quick Start (Windows)

echo.
echo 🚁 Drone Swarm Security System - Startup
echo ========================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Install Python 3.9+ from python.org
    exit /b 1
)

echo ✓ Python is installed

REM Create/activate virtual environment
if not exist "backend_venv" (
    echo 📦 Creating virtual environment...
    python -m venv backend_venv
)

echo 📦 Installing dependencies...
call backend_venv\Scripts\activate.bat
pip install -q -r requirements.txt
pip install -q -r backend\requirements.txt

REM Start backend
echo.
echo 🚀 Starting Flask backend on http://localhost:5000
echo Press Ctrl+C in the backend window to stop
start "Drone Swarm Backend" python backend\app.py

REM Start frontend
echo 🌐 Starting frontend on http://localhost:3000
timeout /t 2 /nobreak
start "Drone Swarm Frontend" cmd /k "cd frontend && python -m http.server 3000"

echo.
echo ✨ System started!
echo.
echo 🎬 Open your browser:
echo    http://localhost:3000  (Frontend Dashboard)
echo    http://localhost:5000/api/health  (API Health Check)
echo.
echo To stop: Close the command windows or press Ctrl+C
echo.

timeout /t 300
