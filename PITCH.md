# KathaVaani (कथावाणी) — One-Page Solution Pitch

> **The Great Indian AI Internship Challenge Submission**  
> *Category: Indian-Language TTS & Real-World Impact*  
> *Core Technology: Gnani Timbre v2.5 Text-to-Speech (REST)*

---

### 1. Problem Statement
Across India, hundreds of millions of people prefer listening to stories and literature in their mother tongue rather than reading dense text. Yet, rich literary treasuries in Telugu, Hindi, Tamil, Bengali, Marathi, Gujarati, and other regional languages exist almost exclusively in printed or digital text format. Current audiobook production is prohibitively expensive, slow, and largely restricted to English or simplified translations. Visually impaired individuals, commuters, and regional-language enthusiasts are left without an accessible, aesthetic gateway to their native literature.

---

### 2. The Solution: KathaVaani
**KathaVaani** is a vintage-bookshop web application that transforms written book manuscripts (PDF or plain text) into natural, soulful audiobooks in the **exact language the book was written in**. 

* **No Translation**: Literature preserves its original cultural nuance, idioms, and emotional weight.
* **Choice of Storytellers**: Listeners select between two curated narrator personas—**Kavya** (warm, lyrical, and melodic) and **Kabir** (deep, calm, and resonant).
* **Old Bookshop Aesthetic**: The entire experience is crafted like stepping into a cozy second-hand parlour, complete with wooden signboards, leather book spines, tactile golden-wood controls, and 3D page-turn transitions.

---

### 3. Gnani AI Models & Architecture
* **Primary TTS Engine**: **Gnani Timbre v2.5 (REST API)**
* **Acoustic Profiling**: Maps 2 narrator personas across 10 major Indian languages (Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, English).
* **Sequential Chunking Pipeline**: Intelligently decomposes text at native Indic and Latin sentence boundaries (`।`, `!`, `?`, `.`) into natural speech bursts under Gnani's 2,000-character ceiling.
* **Cryptographic Audio Cache**: Keys audio chunks by `SHA-256(text + voice + language + speed)`, preventing repeated API consumption and enabling instant zero-cost re-listening.
* **Audio Stitching**: Concatenates chunks with natural 250ms inter-sentence pauses using `pydub` and `ffmpeg` to export polished, downloadable MP3 master audiobooks.

---

### 4. Real-World Impact
1. **Accessibility for Visually Impaired Readers**: Turns physical text or PDFs into clear spoken words in their mother tongue with zero barrier to entry.
2. **Cultural Preservation**: Makes public-domain Indian literature, regional folklore, and historical treatises easily discoverable and listenable by the younger digital generation.
3. **Commuters & Multitaskers**: Enables students and professionals to listen to chapters during commutes without eye strain.

---

### 5. Constraints & Roadmap
* **Free Quota Optimization**: Default page selection is capped at 5 pages per run to conserve API credits while demonstrating complete end-to-end multi-chunk stitching.
* **Roadmap**: Adding OCR for historic scanned manuscripts, streaming synthesis via WebSockets/SSE for real-time playhead starts, and voice cloning for personalized family narration.

