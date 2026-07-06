@echo off
chcp 65001 >nul
title 刷题系统 - 关闭

echo ============================================
echo    📚 刷题系统 - 关闭
echo ============================================
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5588') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo ✅ 刷题系统已关闭！
timeout /t 2 /nobreak >nul
