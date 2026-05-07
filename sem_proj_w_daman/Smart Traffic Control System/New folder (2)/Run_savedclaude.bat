@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Virtual environment python not found at .venv\Scripts\python.exe
  echo Create it with: py -3 -m venv .venv
  pause
  exit /b 1
)

if not exist "savedclaude.py" (
  echo [ERROR] savedclaude.py was not found in this folder.
  pause
  exit /b 1
)

echo Running savedclaude.py with Desktop virtual environment...
".venv\Scripts\python.exe" "savedclaude.py"

echo.
echo Script finished. Press any key to close.
pause >nul
