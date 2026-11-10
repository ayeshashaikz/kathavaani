"""
Audio stitcher and disk cache module for KathaVaani.
Caches synthesized audio chunks on disk keyed by SHA-256 hash,
and joins chunks seamlessly into a single master MP3 using pydub & ffmpeg.
"""

import io
import os
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path

from pydub import AudioSegment

from backend.config import (
    CACHE_DIR,
    OUTPUT_DIR,
    INTER_SENTENCE_PAUSE_MS,
    AUDIO_CONTAINER
)
from backend.tts_client import GnaniTTSClient

logger = logging.getLogger("kathavaani.stitcher")


def get_chunk_hash(text: str, voice: str, language: str, speed: float) -> str:
    """Computes deterministic SHA-256 hash for caching."""
    normalized = f"{voice.strip().lower()}:{language.strip().lower()}:{speed:.2f}:{text.strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class AudioStitcher:
    """Manages audio caching, synthesis orchestration, and concatenation."""

    def __init__(self, tts_client: GnaniTTSClient = None):
        self.tts_client = tts_client or GnaniTTSClient()
        self.cache_dir = Path(CACHE_DIR)
        self.output_dir = Path(OUTPUT_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_or_synthesize_chunk(
        self,
        chunk_text: str,
        voice: str,
        language: str,
        speed: float = 1.0
    ) -> Tuple[bytes, bool]:
        """
        Retrieves chunk from disk cache or synthesizes via Gnani Timbre v2.5.
        Returns: (audio_bytes, was_cached: bool)
        """
        chunk_hash = get_chunk_hash(chunk_text, voice, language, speed)
        cache_file = self.cache_dir / f"{chunk_hash}.wav"

        # Check disk cache
        if cache_file.exists() and cache_file.stat().st_size > 100:
            logger.info("Cache HIT for chunk hash: %s", chunk_hash[:12])
            try:
                with open(cache_file, "rb") as f:
                    return f.read(), True
            except OSError as err:
                logger.warning("Failed to read cache file %s: %s", cache_file, err)

        # Cache MISS: Synthesize via API
        logger.info("Cache MISS for chunk hash: %s. Synthesizing...", chunk_hash[:12])
        audio_bytes = self.tts_client.synthesize(
            text=chunk_text,
            voice=voice,
            language=language,
            speed=speed,
            container=AUDIO_CONTAINER
        )

        # Store in disk cache
        try:
            with open(cache_file, "wb") as f:
                f.write(audio_bytes)
        except OSError as err:
            logger.warning("Failed to write to cache file %s: %s", cache_file, err)

        return audio_bytes, False

    def process_and_stitch(
        self,
        chunks: List[str],
        voice: str = "Nalini",
        language: str = "en-IN",
        speed: float = 1.0,
        pause_ms: int = INTER_SENTENCE_PAUSE_MS
    ) -> Dict[str, Any]:
        """
        Processes a list of text chunks:
        1. Sequentially synthesizes / fetches each chunk from cache.
        2. Combines them using pydub with subtle pauses between chunks.
        3. Exports to MP3 in outputs/ directory.
        """
        if not chunks:
            raise ValueError("No text chunks provided for audio stitching.")

        total_chunks = len(chunks)
        cache_hits = 0
        audio_segments: List[AudioSegment] = []
        silence_separator = AudioSegment.silent(duration=pause_ms)

        logger.info("Beginning audio synthesis for %d chunks (Voice: %s, Lang: %s)...", total_chunks, voice, language)

        for idx, chunk in enumerate(chunks, start=1):
            chunk = chunk.strip()
            if not chunk:
                continue

            audio_bytes, was_cached = self.get_or_synthesize_chunk(
                chunk_text=chunk,
                voice=voice,
                language=language,
                speed=speed
            )

            if was_cached:
                cache_hits += 1

            # Convert bytes to AudioSegment
            segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=AUDIO_CONTAINER)
            audio_segments.append(segment)

        if not audio_segments:
            raise RuntimeError("Audio synthesis produced no valid audio segments.")

        # Stitch segments together with silence pauses
        combined = audio_segments[0]
        for seg in audio_segments[1:]:
            combined = combined + silence_separator + seg

        # Generate unique audio output file
        audio_id = str(uuid.uuid4())
        output_filename = f"{audio_id}.mp3"
        output_path = self.output_dir / output_filename

        # Export as MP3 with 192k bitrate
        logger.info("Exporting stitched audio to %s...", output_path)
        combined.export(str(output_path), format="mp3", bitrate="192k")

        duration_seconds = len(combined) / 1000.0
        file_size_bytes = output_path.stat().st_size

        return {
            "audio_id": audio_id,
            "filename": output_filename,
            "output_path": str(output_path),
            "duration_seconds": round(duration_seconds, 2),
            "file_size_bytes": file_size_bytes,
            "total_chunks": total_chunks,
            "cache_hits": cache_hits,
            "newly_synthesized": total_chunks - cache_hits
        }

