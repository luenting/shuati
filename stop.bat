@echo off
cd /d "%~dp0"
title shuati-server - stop

echo ============================================
echo    Shuati Server - Stopping
echo ============================================
echo.

powershell -Command "Get-NetTCPConnection -LocalPort 5588 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
if errorlevel 1 (
    echo [WARN] No running service found on port 5588
) else (
    echo [OK] Server stopped
)
timeout /t 2 /nobreak >nul
