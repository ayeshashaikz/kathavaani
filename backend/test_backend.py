"""
Unit and integration test suite for KathaVaani backend core.
Tests extraction, chunking, voice lookups, caching, and FastAPI endpoints.
"""

import os
import io
from fastapi.testclient import TestClient

from backend.main import app
from backend.extractor import extract_from_txt, extract_from_pdf, clean_text
from backend.text_chunker import chunk_text_by_sentences, split_into_sentences
from backend.config import VOICES_FILE, is_api_key_configured
import fitz

client = TestClient(app)


def test_voices_configuration_file():
    """Verify voices.json exists, has 2 narrators and 10 supported languages."""
    assert os.path.exists(VOICES_FILE), "voices.json file must exist"
    response = client.get("/api/voices")
    assert response.status_code == 200
    data = response.json()
    
    assert "narrators" in data
    assert "female" in data["narrators"]
    assert "male" in data["narrators"]
    
    assert "languages" in data
    expected_langs = ["en-IN", "hi-IN", "te-IN", "ta-IN", "kn-IN", "ml-IN", "mr-IN", "bn-IN", "gu-IN", "pa-IN"]
    for lang in expected_langs:
        assert lang in data["languages"]
        assert lang in data["mappings"]
        assert "female" in data["mappings"][lang]
        assert "male" in data["mappings"][lang]


def test_health_check_endpoint():
    """Verify /api/health returns operational status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["api_key_configured"] is True
    assert "timbre-v2.5" in data["tts_model"]


def test_txt_extraction():
    """Verify text extraction from plain text bytes."""
    sample_text = (
        "Chapter 1: The Old Bookshop.\n\n"
        "It was a quiet evening when the bells above the door rang softly. "
        "The scent of antique cedar and aged parchment filled the room.\n\n"
        "A traveller stepped inside, holding a leather-bound journal."
    )
    result = extract_from_txt(sample_text.encode("utf-8"), filename="test_book.txt")
    assert result["file_type"] == "txt"
    assert result["total_pages"] >= 1
    assert result["is_scanned"] is False
    assert len(result["pages"]) >= 1
    assert "The Old Bookshop" in result["pages"][0]["text"]


def test_pdf_extraction_and_scanned_detection():
    """Verify PyMuPDF extraction with both text-based PDF and empty/scanned PDF."""
    # 1. Create in-memory text PDF using PyMuPDF
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "KathaVaani Page One. The story begins here.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "KathaVaani Page Two. The journey continues.")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = extract_from_pdf(pdf_bytes, filename="test_book.pdf")
    assert result["file_type"] == "pdf"
    assert result["total_pages"] == 2
    assert result["is_scanned"] is False
    assert "Page One" in result["pages"][0]["text"]
    assert "Page Two" in result["pages"][1]["text"]

    # 2. Test empty / scanned PDF detection
    empty_doc = fitz.open()
    empty_doc.new_page()  # blank page without text
    empty_pdf_bytes = empty_doc.tobytes()
    empty_doc.close()

    scanned_result = extract_from_pdf(empty_pdf_bytes, filename="blank_scanned.pdf")
    assert scanned_result["is_scanned"] is True
    assert "scanned document" in scanned_result["message"]


def test_sentence_chunking():
    """Verify sentence-boundary chunking for English and Indic punctuation."""
    # English test
    eng_text = (
        "Bukowski wanted to be a writer. But for decades his work was rejected by almost every publisher. "
        "His work was crude, they said. Yet he never stopped writing at his beat-up typewriter."
    )
    chunks = chunk_text_by_sentences(eng_text, max_chars=120)
    assert len(chunks) >= 2
    # Ensure no chunk exceeds max_chars
    for c in chunks:
        assert len(c) <= 120

    # Indic test with Purna Virama (।)
    hindi_text = (
        "एक बार की बात है। एक छोटे से शहर में एक पुरानी किताबों की दुकान थी। "
        "वहाँ हर शाम किताबों के पन्ने अपनी कहानियाँ सुनाते थे।"
    )
    indic_chunks = chunk_text_by_sentences(hindi_text, max_chars=60)
    assert len(indic_chunks) >= 2
    for c in indic_chunks:
        assert len(c) <= 60


def test_api_extract_endpoint_txt():
    """Verify POST /api/extract with a TXT file."""
    sample_content = b"KathaVaani sample story line one. Line two follows."
    files = {"file": ("story.txt", io.BytesIO(sample_content), "text/plain")}
    response = client.post("/api/extract", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "story.txt"
    assert data["total_pages"] == 1
    assert "sample story line one" in data["pages"][0]["text"]


def test_api_synthesize_endpoint_with_cache():
    """Verify POST /api/synthesize produces MP3 audio and populates cache."""
    request_payload = {
        "text": "Welcome to KathaVaani old bookshop. Let us begin our story.",
        "language": "en-IN",
        "narrator": "female",
        "speed": 1.0
    }
    response = client.post("/api/synthesize", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["voice_used"] == "Nalini"
    assert data["total_chunks"] >= 1
    assert data["duration_seconds"] > 0
    assert data["download_url"].startswith("/api/audio/")

    # Second identical call should hit the cache!
    response2 = client.post("/api/synthesize", json=request_payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["cache_hits"] >= 1

    # Test downloading the audio file
    download_url = data["download_url"]
    audio_resp = client.get(download_url)
    assert audio_resp.status_code == 200
    assert audio_resp.headers["content-type"] == "audio/mpeg"
    assert len(audio_resp.content) > 1000


if __name__ == "__main__":
    tests = [
        test_voices_configuration_file,
        test_health_check_endpoint,
        test_txt_extraction,
        test_pdf_extraction_and_scanned_detection,
        test_sentence_chunking,
        test_api_extract_endpoint_txt,
        test_api_synthesize_endpoint_with_cache,
    ]
    print(f"Running {len(tests)} test cases for KathaVaani backend core...")
    for t in tests:
        print(f"-> Running {t.__name__}...")
        t()
        print(f"   PASS: {t.__name__}")
    print("\nALL BACKEND CORE TESTS PASSED SUCCESSFULLY!")
