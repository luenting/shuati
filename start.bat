@echo off
cd /d "%~dp0"
title shuati-server

echo ============================================
echo    Shuati Server - Starting
echo ============================================
echo.

call python convert.py
if errorlevel 1 (
    echo [ERROR] convert failed!
    pause
    exit /b 1
)

echo Starting service...
start /B python app.py > "%TEMP%\shuati.log" 2>&1
timeout /t 3 /nobreak >nul

echo [OK] Server started: http://localhost:5588
echo      To stop: stop.bat
echo.
pause
