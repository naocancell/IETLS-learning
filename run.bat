@echo off
setlocal
title IELTS Master
cd /d "%~dp0ielts_client"

set "VENV_PY=C:\Users\WALLCE\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"

if exist "%VENV_PY%" (
    "%VENV_PY%" app.py
) else (
    python app.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Launch failed.
    pause
)
