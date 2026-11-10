"""
test_audio.py
Full audio generation script for KathaVaani.
Reads the entire manuscript from assets/books/sample.txt,
splits it into sentence-level chunks, sends each chunk to Gnani Timbre v2.5 TTS REST API
with disk caching and retries, and joins all chunks into a complete, seamless MP3 audiobook
using pydub & ffmpeg.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 1. Load environment variables securely from .env in project root
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from backend.config import is_api_key_configured
from backend.text_chunker import chunk_text_by_sentences
from backend.audio_stitcher import AudioStitcher
from backend.tts_client import GnaniTTSClient

if not is_api_key_configured():
    print("[ERROR] GNANI_API_KEY is not set in .env file.", file=sys.stderr)
    sys.exit(1)

SAMPLE_FILE_PATH = PROJECT_ROOT / "assets" / "books" / "sample.txt"
OUTPUT_MP3_PATH = PROJECT_ROOT / "output_sample_audiobook.mp3"


def main():
    print("=" * 70)
    print("KathaVaani: Complete Audiobook Synthesis Pipeline")
    print("=" * 70)

    # Step 1: Read the entire sample book text
    print(f"\n[1/4] Reading full manuscript from {SAMPLE_FILE_PATH}...")
    if not SAMPLE_FILE_PATH.exists():
        print(f"[ERROR] Sample file not found at {SAMPLE_FILE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(SAMPLE_FILE_PATH, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    total_chars = len(full_text)
    total_words = len(full_text.split())
    print(f" Manuscript loaded: {total_chars:,} characters, {total_words:,} words across all paragraphs.")

    # Step 2: Split text into sentence-level chunks under TTS limit
    print("\n[2/4] Splitting text into natural sentence chunks (<= 650 chars)...")
    chunks = chunk_text_by_sentences(full_text, max_chars=650)
    print(f" Created {len(chunks)} speech chunks:")
    for idx, chunk in enumerate(chunks, start=1):
        preview = chunk.replace('\n', ' ')[:75]
        print(f"   Chunk {idx}/{len(chunks)} ({len(chunk)} chars): \"{preview}...\"")

    # Step 3: Synthesize chunks with Gnani Timbre v2.5 and disk caching
    print("\n[3/4] Synthesizing chunks with Gnani Timbre v2.5 (Voice: Nalini, Language: en-IN)...")
    print("      (Any previously synthesized chunks are instantly loaded from disk cache)")
    
    tts_client = GnaniTTSClient()
    stitcher = AudioStitcher(tts_client=tts_client)

    t0 = time.time()
    result = stitcher.process_and_stitch(
        chunks=chunks,
        voice="Nalini",
        language="en-IN",
        speed=1.0,
        pause_ms=250
    )
    elapsed = time.time() - t0

    # Step 4: Save master audiobook to root
    # Copy from backend/outputs to root output_sample_audiobook.mp3
    master_path = Path(result["output_path"])
    if master_path.exists():
        import shutil
        shutil.copyfile(master_path, OUTPUT_MP3_PATH)

    print("\n" + "=" * 70)
    print(" ENTIRE BOOK SYNTHESIS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f" Output File       : {OUTPUT_MP3_PATH}")
    print(f" Total Duration    : {result['duration_seconds']} seconds ({result['duration_seconds']/60:.1f} minutes)")
    print(f" Total Chunks      : {result['total_chunks']}")
    print(f" Disk Cache Hits   : {result['cache_hits']} chunks")
    print(f" Newly Synthesized : {result['newly_synthesized']} chunks")
    print(f" File Size         : {OUTPUT_MP3_PATH.stat().st_size:,} bytes")
    print(f" Processing Time   : {elapsed:.2f} seconds")
    print("=" * 70)


if __name__ == "__main__":
    main()
