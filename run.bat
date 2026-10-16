@echo off
setlocal
title IELTS Master
cd /d "%~dp0"

rem Prefer the project virtual environment created by setup.bat
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python 3 was not found.
  echo Install Python 3.9+ from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^),
  echo then double-click setup.bat once.
  pause
  exit /b 1
)

%PY% ielts_client\app.py %*
if errorlevel 1 (
  echo.
  echo [ERROR] Launch failed. See the message above or userdata\app.log
  pause
)
