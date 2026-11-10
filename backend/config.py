"""
Configuration module for KathaVaani backend.
Safely loads environment variables and sets system paths and limits.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from project root
dotenv_path = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Security: Load API key (never print or expose)
GNANI_API_KEY = os.getenv("GNANI_API_KEY", "").strip()

# API Settings
GNANI_TTS_URL = os.getenv("GNANI_TTS_URL", "https://api.vachana.ai/api/v1/tts/inference")
GNANI_MODEL = os.getenv("GNANI_MODEL", "timbre-v2.5")

# Storage Directories
CACHE_DIR = BACKEND_DIR / "cache"
OUTPUT_DIR = BACKEND_DIR / "outputs"
VOICES_FILE = BACKEND_DIR / "voices.json"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Audio & Chunking Parameters
# Empirical tests confirm payload errors at >2000 chars; safe chunking target is 400-700 chars.
MAX_CHUNK_CHARS = 650
MIN_CHUNK_CHARS = 40
INTER_SENTENCE_PAUSE_MS = 250

# Request Resilience
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30.0

# Supported container format for Gnani inference
AUDIO_CONTAINER = "wav"
AUDIO_SAMPLE_RATE = 24000


def is_api_key_configured() -> bool:
    """Returns True if GNANI_API_KEY is configured with non-empty content."""
    return bool(GNANI_API_KEY and len(GNANI_API_KEY) > 8)

