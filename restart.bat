@echo off
chcp 65001 >nul
title 刷题系统 - 重启

echo ============================================
echo    📚 刷题系统 - 重启
echo ============================================
echo.

echo 正在关闭服务...
call stop.bat
echo.
echo 正在启动服务...
call start.bat
