"""
run.py — KathaVaani Parlour Server Launcher
Launches FastAPI backend and serves the vintage bookshop frontend.
"""

import sys
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from backend.config import is_api_key_configured, GNANI_MODEL

def main():
    print("=" * 65)
    print(" 📖 KathaVaani (कथावाणी) — Vintage Indian Audiobook Parlour 🎙️")
    print("=" * 65)
    print(f" -> TTS Engine: Gnani {GNANI_MODEL}")
    print(f" -> API Key Status: {'Configured' if is_api_key_configured() else 'Missing / Not Set'}")
    print(" -> Server URL: http://127.0.0.1:8000 (or http://localhost:8000)")
    print(" -> API Docs:   http://127.0.0.1:8000/docs")
    print("=" * 65)
    print(" Parlour is now open! Press Ctrl+C to stop.\n")

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
