@echo off
title MCP Frontend - Port 3000
color 0B
echo.
echo =========================================
echo   MCP SYSTEM FRONTEND
echo   Next.js running on http://localhost:3000
echo =========================================
echo.
cd frontend
call npm run dev
pause
