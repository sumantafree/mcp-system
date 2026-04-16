@echo off
title MCP Backend - Port 8000
color 0A
echo.
echo =========================================
echo   MCP SYSTEM BACKEND
echo   FastAPI running on http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo =========================================
echo.
cd backend
call venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
