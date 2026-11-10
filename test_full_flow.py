"""
test_full_flow.py
Tests the complete end-to-end flow with assets/books/sample.txt
once with narrator_female and once with narrator_male.
"""

from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_full_flow_with_both_narrators():
    print("=" * 70)
    print("TESTING FULL FLOW: Upload -> Scope -> Language -> Narrator -> MP3")
    print("=" * 70)

    # 1. Test /voices endpoint
    resp = client.get("/voices")
    assert resp.status_code == 200, f"/voices failed: {resp.status_code}"
    voices_data = resp.json()
    print("✓ Step 1: GET /voices -> Verified available narrators & languages")
    assert "en-IN" in voices_data["mappings"]

    # 2. Upload sample.txt to /extract
    sample_file_path = "assets/books/sample.txt"
    with open(sample_file_path, "rb") as f:
        resp = client.post("/extract", files={"file": ("sample.txt", f, "text/plain")})
    assert resp.status_code == 200, f"/extract failed: {resp.text}"
    extract_data = resp.json()
    total_pages = extract_data["total_pages"]
    print(f"✓ Step 2: POST /extract -> Extracted {total_pages} page(s) from sample.txt")

    # 3. Reading Nook: Select Page Scope (page 1, capped at max 5)
    selected_page_text = extract_data["pages"][0]["text"]
    print("✓ Step 3: Scope selected -> Page 1 (within max 5 cap)")

    # 4. Narrator Choice: Test with FEMALE (narrator_female)
    print("\n--- FLOW A: Narrator Female (Kavya / narrator_female) ---")
    
    # 4a. Hear a sample preview
    prev_resp = client.post("/preview-voice", json={"language": "en-IN", "narrator": "narrator_female"})
    assert prev_resp.status_code == 200, f"Preview failed: {prev_resp.text}"
    print(f"✓ Hear a sample preview -> OK: {prev_resp.json()['audio_url']}")

    # 4b. Synthesize full page with narrator_female
    synth_payload_female = {
        "pages": [selected_page_text],
        "start_page": 1,
        "end_page": 1,
        "language": "en-IN",
        "narrator": "narrator_female",
        "speed": 1.0
    }
    synth_resp = client.post("/synthesize", json=synth_payload_female)
    assert synth_resp.status_code == 200, f"Synthesize failed: {synth_resp.text}"
    res_female = synth_resp.json()
    print(f"✓ Synthesized successfully with narrator_female!")
    print(f"  - Audio ID: {res_female['audio_id']}")
    print(f"  - Duration: {res_female['duration_seconds']}s")
    print(f"  - Total chunks: {res_female['total_chunks']}")
    print(f"  - Download URL: {res_female['download_url']}")

    # 4c. Verify download endpoint
    dl_resp = client.get(res_female['download_url'])
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "audio/mpeg"
    assert len(dl_resp.content) > 1000
    print(f"✓ Downloaded MP3 verified: {len(dl_resp.content):,} bytes")

    # 5. Narrator Choice: Test with MALE (narrator_male)
    print("\n--- FLOW B: Narrator Male (Kabir / narrator_male) ---")
    
    # 5a. Hear a sample preview
    prev_resp_m = client.post("/preview-voice", json={"language": "en-IN", "narrator": "narrator_male"})
    assert prev_resp_m.status_code == 200, f"Preview failed: {prev_resp_m.text}"
    print(f"✓ Hear a sample preview -> OK: {prev_resp_m.json()['audio_url']}")

    # 5b. Synthesize full page with narrator_male
    synth_payload_male = {
        "pages": [selected_page_text],
        "start_page": 1,
        "end_page": 1,
        "language": "en-IN",
        "narrator": "narrator_male",
        "speed": 1.0
    }
    synth_resp_m = client.post("/synthesize", json=synth_payload_male)
    assert synth_resp_m.status_code == 200, f"Synthesize failed: {synth_resp_m.text}"
    res_male = synth_resp_m.json()
    print(f"✓ Synthesized successfully with narrator_male!")
    print(f"  - Audio ID: {res_male['audio_id']}")
    print(f"  - Duration: {res_male['duration_seconds']}s")
    print(f"  - Total chunks: {res_male['total_chunks']}")
    print(f"  - Download URL: {res_male['download_url']}")

    # 5c. Verify download endpoint
    dl_resp_m = client.get(res_male['download_url'])
    assert dl_resp_m.status_code == 200
    assert dl_resp_m.headers["content-type"] == "audio/mpeg"
    assert len(dl_resp_m.content) > 1000
    print(f"✓ Downloaded MP3 verified: {len(dl_resp_m.content):,} bytes")

    print("\n" + "=" * 70)
    print("ALL FLOWS COMPLETED & VERIFIED WITH BOTH NARRATORS!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_flow_with_both_narrators()

