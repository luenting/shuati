@echo off
cd /d "%~dp0"
title shuati-server

echo ============================================
echo    Shuati Server - Starting
echo ============================================
echo.

echo Starting service...
start /B python app.py
timeout /t 3 /nobreak >nul

echo [OK] Server started: http://localhost:5588
echo      To stop: stop.bat
echo.
pause
