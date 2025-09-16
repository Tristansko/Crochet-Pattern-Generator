#!/usr/bin/env bash
set -euo pipefail

# Build script for macOS/Linux
# Usage: chmod +x build_mac.sh && ./build_mac.sh

# 1) Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install requirements and PyInstaller
pip install --upgrade pip
pip install -r requirements.txt pyinstaller

# 3) Build with the provided spec (best packaging for matplotlib)
if [[ -f "Crochet_Pattern_Generator.spec" ]]; then
  pyinstaller Crochet_Pattern_Generator.spec
else
  # Fallback: build directly from the script as one-file windowed app
  pyinstaller --onefile --noconsole --name CrochetPatternGenerator Crochet_Pattern_Generator.py
fi

echo ""
echo "Build complete. See the 'dist' folder."
