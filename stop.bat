@echo off
chcp 65001 >nul
title 刷题系统 - 关闭

echo ============================================
echo    📚 刷题系统 - 关闭
echo ============================================
echo.

powershell -Command "Get-NetTCPConnection -LocalPort 5588 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
if %errorlevel% equ 0 (
    echo ✅ 刷题系统已关闭！
) else (
    echo ⚠️  未检测到运行中的服务（可能已关闭）
)
timeout /t 2 /nobreak >nul
