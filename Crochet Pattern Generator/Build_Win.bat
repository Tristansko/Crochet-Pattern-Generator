@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Build script for Windows
REM Usage: double-click or run from cmd in the project folder.

REM 1) Create and activate venv
python -m venv .venv
call .venv\Scripts\activate

REM 2) Install requirements and PyInstaller
pip install --upgrade pip
pip install -r requirements.txt pyinstaller

REM 3) Build with the provided spec (best packaging for matplotlib)
if exist Crochet_Pattern_Generator.spec (
    pyinstaller Crochet_Pattern_Generator.spec
) else (
    REM Fallback: build directly from the script as one-file windowed app
    pyinstaller --onefile --noconsole --name CrochetPatternGenerator Crochet_Pattern_Generator.py
)

echo.
echo Build complete. See the 'dist' folder.
pause
