@echo off
title MCP System Setup
color 0B
echo.
echo =========================================
echo   MCP SYSTEM - SETUP
echo   Modular Capability Programs
echo =========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+
    pause & exit /b 1
)

echo [1/5] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Installing backend dependencies...
pip install -r requirements.txt

echo [3/5] Creating .env from template...
if not exist .env (
    copy .env.example .env
    echo [INFO] .env created. Please edit it with your API keys!
)

echo [4/5] Setting up frontend...
cd ..\frontend
if exist package.json (
    call npm install
) else (
    echo [WARN] Frontend not initialized yet. Run: npx create-next-app@latest .
)

echo [5/5] Setup complete!
echo.
echo =========================================
echo   NEXT STEPS:
echo   1. Edit backend\.env with your API keys
echo   2. Start PostgreSQL database
echo   3. Run: start_backend.bat
echo =========================================
pause
