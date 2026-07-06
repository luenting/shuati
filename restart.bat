@echo off
cd /d "%~dp0"
title shuati-server - restart

echo ============================================
echo    Shuati Server - Restarting
echo ============================================
echo.

echo Stopping...
call stop.bat
echo.
echo Starting...
call start.bat
