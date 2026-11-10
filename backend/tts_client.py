"""
Gnani Timbre v2.5 Text-to-Speech REST API client.
Handles synthesis requests with exponential backoff retries, rate-limiting adaptation,
and strict credential protection.
"""

import time
import random
import logging
from typing import Optional
import requests

from backend.config import (
    GNANI_API_KEY,
    GNANI_TTS_URL,
    GNANI_MODEL,
    MAX_RETRIES,
    INITIAL_BACKOFF_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    AUDIO_CONTAINER,
    AUDIO_SAMPLE_RATE,
    is_api_key_configured
)

logger = logging.getLogger("kathavaani.tts")


class GnaniTTSError(Exception):
    """Custom exception raised when Gnani TTS synthesis fails."""
    pass


class GnaniTTSClient:
    """Client for Gnani Timbre v2.5 REST API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GNANI_API_KEY
        if not self.api_key:
            logger.warning("GnaniTTSClient initialized without an API key.")

    def synthesize(
        self,
        text: str,
        voice: str = "Nalini",
        language: str = "en-IN",
        speed: float = 1.0,
        container: str = AUDIO_CONTAINER,
        sample_rate: int = AUDIO_SAMPLE_RATE
    ) -> bytes:
        """
        Synthesizes text using Gnani Timbre v2.5.
        Returns raw audio bytes (e.g. WAV or MP3).
        Retries on transient errors and rate limits with exponential backoff.
        """
        if not self.api_key:
            raise GnaniTTSError("GNANI_API_KEY is not configured in .env file.")

        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text payload cannot be empty.")

        headers = {
            "Content-Type": "application/json",
            "X-API-Key-ID": self.api_key
        }

        payload = {
            "text": cleaned_text,
            "voice": voice,
            "model": GNANI_MODEL,
            "language": language,
            "speed": max(0.5, min(2.0, float(speed))),
            "audio_config": {
                "sample_rate": sample_rate,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": container
            }
        }

        backoff = INITIAL_BACKOFF_SECONDS
        last_error_message = ""

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    GNANI_TTS_URL,
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS
                )

                # Successful audio synthesis
                if response.status_code == 200:
                    if len(response.content) < 100:
                        raise GnaniTTSError(f"TTS returned unexpectedly small audio payload: {len(response.content)} bytes")
                    return response.content

                # Rate limiting (HTTP 429) - wait and backoff
                if response.status_code == 429:
                    jitter = random.uniform(0.2, 0.8)
                    sleep_time = backoff + jitter
                    logger.warning(
                        "Gnani rate limit encountered (429). Backing off for %.2fs (attempt %d/%d)",
                        sleep_time, attempt, MAX_RETRIES
                    )
                    time.sleep(sleep_time)
                    backoff *= 2.0
                    continue

                # Transient server errors (500, 502, 503, 504)
                if response.status_code in (500, 502, 503, 504):
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = backoff + jitter
                    logger.warning(
                        "Gnani server error (%d). Retrying in %.2fs (attempt %d/%d)",
                        response.status_code, sleep_time, attempt, MAX_RETRIES
                    )
                    time.sleep(sleep_time)
                    backoff *= 2.0
                    continue

                # Client error (400, 401, 403, 404, etc.) - do not retry bad inputs
                err_text = response.text.strip()
                last_error_message = f"HTTP {response.status_code}: {err_text}"
                logger.error("Gnani TTS client error: %s", last_error_message)
                raise GnaniTTSError(last_error_message)

            except requests.RequestException as exc:
                last_error_message = f"Network exception: {str(exc)}"
                logger.warning(
                    "Network error on attempt %d/%d: %s. Retrying in %.2fs",
                    attempt, MAX_RETRIES, last_error_message, backoff
                )
                if attempt < MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    raise GnaniTTSError(f"Connection failed after {MAX_RETRIES} attempts: {last_error_message}")

        raise GnaniTTSError(f"Synthesis failed after {MAX_RETRIES} attempts. {last_error_message}")

