@echo off
cd /d "%~dp0"
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'app.py' -RedirectStandardOutput \"$env:TEMP\shuati.log\" -RedirectStandardError \"$env:TEMP\shuati.log\""
echo [OK] Server started: http://localhost:5588
echo      To stop: stop.bat