@echo off
cd /d %~dp0

start cmd /k python app.py
timeout /t 2 >nul
start cmd /k python mqtt\subscriber.py

start http://127.0.0.1:5000
