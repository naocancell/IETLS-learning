@echo off
setlocal
title IELTS Master - setup
cd /d "%~dp0"

set "BASE="
where py >nul 2>nul && set "BASE=py -3"
if not defined BASE (
  where python >nul 2>nul && set "BASE=python"
)
if not defined BASE (
  echo [ERROR] Python 3 was not found. Install Python 3.9+ from https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment .venv ...
  %BASE% -m venv .venv
  if errorlevel 1 goto :fail
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Retrying with the Tsinghua PyPI mirror ...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  if errorlevel 1 goto :fail
)

echo.
echo Setup finished. Start the app with run.bat or the .vbs file.
pause
exit /b 0

:fail
echo.
echo [ERROR] Setup failed. See the messages above.
pause
exit /b 1
