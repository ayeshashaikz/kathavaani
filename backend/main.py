"""
FastAPI application for KathaVaani backend.
Exposes endpoints for text extraction, sentence-chunked Gnani TTS synthesis,
voice mapping lookups, and MP3 audio delivery.
"""

import json
import logging
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import (
    BACKEND_DIR,
    OUTPUT_DIR,
    CACHE_DIR,
    VOICES_FILE,
    GNANI_MODEL,
    is_api_key_configured
)
from backend.extractor import extract_text_from_file
from backend.text_chunker import chunk_text_by_sentences
from backend.tts_client import GnaniTTSClient, GnaniTTSError
from backend.audio_stitcher import AudioStitcher

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kathavaani.api")

# Initialize FastAPI application
app = FastAPI(
    title="KathaVaani API",
    description="Vintage-bookshop audiobook engine powered by Gnani Timbre v2.5",
    version="1.0.0"
)

# Enable CORS for local and web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load voices configuration
def load_voices_config() -> dict:
    if not VOICES_FILE.exists():
        raise FileNotFoundError(f"voices.json not found at {VOICES_FILE}")
    with open(VOICES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

voices_config = load_voices_config()

# Shared services
tts_client = GnaniTTSClient()
audio_stitcher = AudioStitcher(tts_client=tts_client)


# --- Pydantic Request & Response Schemas ---

class SynthesizeRequest(BaseModel):
    pages: Optional[List[str]] = Field(
        default=None,
        description="List of text strings, one per page (1-indexed matching start_page/end_page)"
    )
    text: Optional[str] = Field(
        default=None,
        description="Direct plain text to synthesize if not using pages array"
    )
    start_page: int = Field(default=1, ge=1, description="Starting page (1-indexed)")
    end_page: int = Field(default=1, ge=1, description="Ending page (inclusive)")
    language: str = Field(default="en-IN", description="Language code (e.g., 'en-IN', 'hi-IN', 'te-IN')")
    narrator: str = Field(default="female", description="Narrator identifier ('female' or 'male')")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Narration speed multiplier")


class SynthesizeResponse(BaseModel):
    status: str
    audio_id: str
    download_url: str
    voice_used: str
    narrator: str
    language: str
    duration_seconds: float
    total_chunks: int
    cache_hits: int
    newly_synthesized: int
    file_size_bytes: int


# --- API Routes ---

@app.get("/api/health")
def health_check():
    """Health check endpoint providing backend readiness and cache statistics."""
    cache_files = list(Path(CACHE_DIR).glob("*.wav"))
    output_files = list(Path(OUTPUT_DIR).glob("*.mp3"))
    return {
        "status": "online",
        "api_key_configured": is_api_key_configured(),
        "tts_model": GNANI_MODEL,
        "cached_chunks_count": len(cache_files),
        "generated_audiobooks_count": len(output_files)
    }


@app.get("/voices")
@app.get("/api/voices")
def get_voices():
    """Returns which narrators are available for each language."""
    return voices_config


@app.post("/extract")
@app.post("/api/extract")
async def extract_book_text(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT book manuscript and extract text per page.
    Automatically detects scanned documents without digital text layers.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ("pdf", "txt", "text"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '.{ext}'. KathaVaani supports PDF and TXT files only."
        )

    try:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Max file size safeguard (e.g. 50 MB)
        if len(file_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds maximum limit of 50MB.")

        result = extract_text_from_file(file_bytes=file_bytes, filename=file.filename)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to extract text from %s: %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(exc)}")


@app.post("/synthesize", response_model=SynthesizeResponse)
@app.post("/api/synthesize", response_model=SynthesizeResponse)
def synthesize_audiobook(payload: SynthesizeRequest):
    """
    Synthesizes selected pages into an audiobook MP3:
    1. Resolves narrator & language to exact Gnani voice.
    2. Gathers text for chosen page range.
    3. Chunks text at sentence ends.
    4. Synthesizes each chunk via Gnani Timbre v2.5 with disk caching.
    5. Stitches audio into an MP3 file via pydub + ffmpeg.
    """
    # 1. Resolve narrator and language mapping
    mappings = voices_config.get("mappings", {})
    lang_mappings = mappings.get(payload.language)

    if not lang_mappings:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language code '{payload.language}'. Check /voices for available languages."
        )

    narrator_clean = payload.narrator.lower().strip()
    voice_name = lang_mappings.get(narrator_clean)
    if not voice_name:
        alias_map = {
            "male": "narrator_male",
            "female": "narrator_female",
            "narrator_male": "male",
            "narrator_female": "female"
        }
        alt_key = alias_map.get(narrator_clean)
        if alt_key:
            voice_name = lang_mappings.get(alt_key)

    if not voice_name:
        raise HTTPException(
            status_code=400,
            detail=f"Narrator '{payload.narrator}' is not available for language '{payload.language}'."
        )

    # 2. Gather target text from pages or direct text
    combined_text = ""
    if payload.pages:
        total_available = len(payload.pages)
        start_idx = payload.start_page - 1
        end_idx = min(payload.end_page, total_available)

        if start_idx >= total_available:
            raise HTTPException(
                status_code=400,
                detail=f"start_page ({payload.start_page}) exceeds total available pages ({total_available})."
            )

        selected_pages = payload.pages[start_idx:end_idx]
        combined_text = "\n\n".join(selected_pages).strip()
    elif payload.text:
        combined_text = payload.text.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'pages' array or 'text' string must be provided for synthesis."
        )

    if not combined_text:
        raise HTTPException(status_code=400, detail="Extracted text for the selected range is empty.")

    # 3. Chunk text at sentence ends
    chunks = chunk_text_by_sentences(combined_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Text chunking resulted in no synthesizable content.")

    # 4. Synthesize, cache, and stitch into MP3
    try:
        stitch_result = audio_stitcher.process_and_stitch(
            chunks=chunks,
            voice=voice_name,
            language=payload.language,
            speed=payload.speed
        )

        return SynthesizeResponse(
            status="success",
            audio_id=stitch_result["audio_id"],
            download_url=f"/api/audio/{stitch_result['filename']}",
            voice_used=voice_name,
            narrator=payload.narrator,
            language=payload.language,
            duration_seconds=stitch_result["duration_seconds"],
            total_chunks=stitch_result["total_chunks"],
            cache_hits=stitch_result["cache_hits"],
            newly_synthesized=stitch_result["newly_synthesized"],
            file_size_bytes=stitch_result["file_size_bytes"]
        )

    except GnaniTTSError as tts_err:
        logger.error("Gnani TTS Error: %s", tts_err)
        raise HTTPException(status_code=502, detail=f"Gnani TTS service failure: {str(tts_err)}")
    except Exception as exc:
        logger.exception("Synthesis pipeline failure: %s", exc)
        raise HTTPException(status_code=500, detail=f"Audio processing failure: {str(exc)}")


@app.get("/audio/{filename}")
@app.get("/api/audio/{filename}")
def stream_audio(filename: str):
    """Streams or downloads a synthesized MP3 audiobook file."""
    # Sanitize filename to prevent directory traversal
    safe_filename = Path(filename).name
    file_path = Path(OUTPUT_DIR) / safe_filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio file '{safe_filename}' not found.")

    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=safe_filename,
        headers={"Accept-Ranges": "bytes"}
    )


# --- Sample Books Catalog & Voice Preview ---

SAMPLE_BOOKS = [
    {
        "id": "sample-te",
        "title": "బంగారు మామిడిపండ్లు",
        "author": "తెనాలి రామకృష్ణ (Tenali Ramakrishna)",
        "language_name": "Telugu (తెలుగు)",
        "default_language": "te-IN",
        "filename": "telugu_tenali_ramakrishna.txt"
    },
    {
        "id": "sample-hi",
        "title": "पंच परमेश्वर",
        "author": "मुंशी प्रेमचंद (Munshi Premchand)",
        "language_name": "Hindi (हिन्दी)",
        "default_language": "hi-IN",
        "filename": "hindi_panch_parmeshwar.txt"
    },
    {
        "id": "sample-en",
        "title": "The Tale of Charles",
        "author": "Mark Manson",
        "language_name": "English",
        "default_language": "en-IN",
        "filename": "sample.txt"
    }
]

PREVIEW_PHRASES = {
    "te-IN": "కథావాణి పాత పుస్తకాల దుకాణానికి స్వాగతం. మీ పుస్తకం వినడానికి సిద్ధంగా ఉంది.",
    "hi-IN": "कथावाणी में आपका स्वागत है। आपकी पुस्तक सुनने के लिए तैयार है।",
    "en-IN": "Welcome to KathaVaani. Your book is ready to be spoken in its true voice.",
    "ta-IN": "கதாவாணிக்கு வரவேற்கிறோம். உங்கள் புத்தகம் கேட்க தயாராக உள்ளது.",
    "kn-IN": "ಕಥಾವಾಣಿಗೆ ಸುಸ್ವಾಗತ. ನಿಮ್ಮ ಪುಸ್ತಕ ಕೇಳಲು ಸಿದ್ಧವಾಗಿದೆ.",
    "ml-IN": "കഥാവാണിയിലേക്ക് സ്വാഗതം. നിങ്ങളുടെ പുസ്തകം കേൾക്കാൻ തയ്യാറാണ്.",
    "mr-IN": "कथावाणीमध्ये आपले स्वागत आहे. आपले पुस्तक ऐकण्यासाठी सज्ज आहे.",
    "bn-IN": "কথা বাণীতে আপনাকে স্বাগতম। আপনার বই শোনার জন্য প্রস্তুত।",
    "gu-IN": "કથાવાણીમાં આપનું સ્વાગત છે. તમારું પુસ્તક સાંભળવા માટે તૈયાર છે.",
    "pa-IN": "ਕਥਾਵਾਣੀ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਤੁਹਾਡੀ ਕਿਤਾਬ ਸੁਣਨ ਲਈ ਤਿਆਰ ਹੈ।"
}


class PreviewVoiceRequest(BaseModel):
    language: str = Field(default="en-IN")
    narrator: str = Field(default="female")


@app.get("/api/samples")
def get_sample_books():
    """Returns curated public-domain sample books across Indian languages."""
    return SAMPLE_BOOKS


@app.get("/api/samples/{sample_id}")
def get_sample_book_content(sample_id: str):
    """Retrieves and extracts text from a curated sample book."""
    match = next((b for b in SAMPLE_BOOKS if b["id"] == sample_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Sample book '{sample_id}' not found")

    file_path = BACKEND_DIR.parent / "assets" / "books" / match["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Book file '{match['filename']}' not found on server")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    return extract_text_from_file(file_bytes=file_bytes, filename=match["filename"])


@app.post("/preview-voice")
@app.post("/api/preview-voice")
def preview_voice(payload: PreviewVoiceRequest):
    """Synthesizes or loads a 2-second voice preview in the chosen language & narrator."""
    mappings = voices_config.get("mappings", {})
    lang_mappings = mappings.get(payload.language)
    if not lang_mappings:
        raise HTTPException(status_code=400, detail=f"Unsupported language code '{payload.language}'")

    narrator_clean = payload.narrator.lower().strip()
    voice_name = lang_mappings.get(narrator_clean)
    if not voice_name:
        alias_map = {
            "male": "narrator_male",
            "female": "narrator_female",
            "narrator_male": "male",
            "narrator_female": "female"
        }
        alt_key = alias_map.get(narrator_clean)
        if alt_key:
            voice_name = lang_mappings.get(alt_key)

    if not voice_name:
        raise HTTPException(status_code=400, detail=f"Narrator '{payload.narrator}' is not configured for '{payload.language}'")

    phrase = PREVIEW_PHRASES.get(payload.language, PREVIEW_PHRASES["en-IN"])

    try:
        stitch_result = audio_stitcher.process_and_stitch(
            chunks=[phrase],
            voice=voice_name,
            language=payload.language,
            speed=1.0
        )
        return {
            "status": "success",
            "audio_url": f"/api/audio/{stitch_result['filename']}",
            "voice": voice_name,
            "language": payload.language,
            "phrase": phrase
        }
    except Exception as exc:
        logger.exception("Voice preview failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(exc)}")


# --- Static Files & Single Page App Serving ---

FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
IMAGES_DIR = BACKEND_DIR.parent / "images"

if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    """Serves the KathaVaani vintage parlour single-page application."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "KathaVaani API is active. index.html not found."})


