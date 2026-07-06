@echo off
chcp 65001 >nul
title 刷题系统
cd /d "%~dp0"

echo ============================================
echo    📚 刷题系统 - 启动
echo ============================================
echo.

call python convert.py
if %errorlevel% neq 0 (
    echo [错误] 题库转换失败!
    pause
    exit /b 1
)

echo 启动服务中...
start /B python app.py > "%TEMP%\shuati.log" 2>&1
timeout /t 3 /nobreak >nul

echo ✅ 刷题系统已启动！
echo    访问地址: http://localhost:5588
echo    关闭服务: stop.bat
echo.
pause
