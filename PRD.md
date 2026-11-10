KathaVaani: Product Requirements Document

Working title. A vintage-bookshop web app that turns a book into an audiobook in the language it is written in, built on Gnani Timbre TTS for The Great Indian AI Internship Challenge. Submission deadline: 10 November 2026, 11:59 PM IST.

1. Summary

KathaVaani lets a reader walk into a virtual old bookshop, hand over a book, choose how many pages they want, confirm the book's language, pick a narrator character, and receive an audiobook they can listen to in the browser or download for later. The text is read in its own language, with no translation step, and spoken with Gnani Timbre v2.5.

The product is both useful and memorable: useful because many people prefer to listen in their own language, and memorable because the whole experience looks and feels like a cozy second-hand bookshop, with page-turn transitions and golden wooden buttons.

2. Problem

Millions of Indians are more comfortable listening than reading, and books in Telugu, Hindi, Tamil, Bengali and other Indian languages are often available only as text.

Audiobooks in Indian languages are limited, and existing tools feel like utilities, not experiences.

Visually impaired readers, commuters, and people with low reading fluency need a simple way to listen.

3. Goals and Non-Goals

Goals

A working end-to-end flow: upload, choose pages, choose language and narrator, generate audio, listen, download.

A strong visual identity: old bookshop theme, page-turn transitions, golden-wood buttons.

Clear use of Gnani models, named in the submission.

A 2-3 minute demo that tells a human story.

Qualify for the Indian-language and real-world impact award categories.

Non-Goals (for this submission)

User accounts, login or payments.

Full-length book processing in real time.

OCR for scanned books, and translation between languages.

Mobile app. The site should work in a mobile browser but is designed desktop-first.

Storing user data in a database.

4. Target Users

User | Need

User

Need

Regional-language listener | Hear books written in their own language

Regional-language listener

Hear books written in their own language

Visually impaired reader | Accessible audio from text books

Visually impaired reader

Accessible audio from text books

Student | Listen to a chapter in their mother tongue while commuting

Student

Listen to a chapter in their mother tongue while commuting

Casual reader | Enjoy a calm, aesthetic way to "read" by listening

Casual reader

Enjoy a calm, aesthetic way to "read" by listening

5. User Flow

Each step is one screen, and moving between screens uses a page-turn animation.

Shop front. Illustrated bookshop entrance with the project name on the sign and an "Enter the shop" button.

Counter. "Upload your book" button. Accepts PDF and TXT. Shows the detected title and page count.

Reading nook. Choose how many pages to read (slider with a capped maximum) and confirm the book's language from a shelf of spine-style buttons.

Choose your narrator. Two illustrated characters, a male and a female, each with a name, a one-line personality and a voice preview button.

Binding your book. Loading screen with a progress bar and status lines such as "Preparing chapter 1" and "Recording chapter 1".

Library. Audio player, translated text beside it, download button, and a shelf of audiobooks generated in this session.

6. Functional Requirements

6.1 Upload and extraction

FR-1: The user can upload a PDF or TXT file.

FR-2: The system extracts text page by page and shows the title (or filename) and page count.

FR-3: If a PDF has no text layer (a scanned book), the app shows a friendly message that scanned books are not supported yet.

FR-4: A small set of public-domain sample books in different supported languages is available so the user can try the app without uploading.

6.2 Page selection

FR-5: The user chooses how many pages to convert, starting from a chosen page.

FR-6: The maximum is capped (default suggestion: a small number such as 5 pages) to protect API credits and keep generation fast. The cap is a config value.

6.3 Language selection

FR-7: The user confirms the language the book is written in, chosen from the languages Gnani supports, because the voice language must match the text. Playground listing: Bengali, English, Gujarati, Hindi, Kannada, Malayalam, Marathi, Punjabi, Tamil, Telugu. The final list must be confirmed against the TTS Available Voices page.

FR-8: Any language without a matching voice for the chosen narrator is disabled or shown with a note.

6.4 Narrator selection

FR-9: The user picks one of two characters. Each character maps to one Gnani voice per language, configured in a lookup table.

FR-10: A "hear a sample" button plays a short pre-generated line in the chosen language.

6.5 Text preparation

FR-11: Extracted text is cleaned (page numbers, headers and line breaks inside sentences removed) and split into chunks at sentence ends, within the TTS length limit.

FR-12: There is no translation step: the text is spoken in the book's own language. A book in a language without a Gnani voice shows a friendly message.

6.6 Audio generation

FR-13: Each chunk is sent to Gnani Timbre v2.5 via the TTS REST API with the chosen voice and language.

FR-14: Chunk size respects the API's maximum text length, to be confirmed in the TTS REST docs.

FR-15: Audio chunks are joined into one file per chapter or selection and exported as MP3.

FR-16: Every chunk's audio is cached on disk, so repeated runs and demos do not use extra credits and failed runs can resume.

FR-17: Failed API calls are retried with backoff, and the user sees a clear message if a chunk still fails.

6.7 Listening and download

FR-18: The Library screen has an in-browser audio player with play, pause, seek and speed control.

FR-19: The book text is shown next to the player. Stretch goal: highlight the current paragraph.

FR-20: The user can download the MP3 and the text.

FR-21: A shelf lists audiobooks generated during the session, so the user can replay them without regenerating.

7. Design Requirements

7.1 Visual identity

Warm, dim, cozy old bookshop: dark wood, aged paper, brass lamp glow.

Palette: deep brown, parchment cream, antique gold, muted green for ivy accents.

Typography: a serif display font such as Cinzel or IM Fell English for headings and a readable serif for body text.

Buttons look like golden wood: wood-grain gradient, gold border, inset shadow, and a slight press effect on click.

Language buttons look like book spines on a shelf.

The Library audio player is styled like a vintage record or cassette deck, or a bookmark-style bar.

7.2 Page-turn transitions

Each move to the next screen plays a book page-turn animation (CSS 3D flip or a small library such as StPageFlip), about 0.8 seconds.

A "reduce motion" setting or prefers-reduced-motion disables the animation.

7.3 Reference for layout

The language and settings screens follow the structure of the Gnani Playground (clear sections, all languages visible), but with the bookshop skin instead of the Gnani look.

7.4 Assets and licensing

Characters and backgrounds must be original, generated by the team, or properly licensed. Images saved from Pinterest or similar sites are not safe for a public submission, video or social post.

Sample books must be public domain.

8. Technical Approach

Layer | Choice

Layer

Choice

Frontend | HTML, CSS and JavaScript (or React) with CSS 3D transitions

Frontend

HTML, CSS and JavaScript (or React) with CSS 3D transitions

Backend | Python with FastAPI or Flask

Backend

Python with FastAPI or Flask

Text extraction | PyMuPDF for PDF, plain read for TXT

Text extraction

PyMuPDF for PDF, plain read for TXT

Language and voice matching | Lookup table of Gnani voices per language and narrator

Language and voice matching

Lookup table of Gnani voices per language and narrator

Text-to-speech | Gnani Timbre v2.5 via TTS REST

Text-to-speech

Gnani Timbre v2.5 via TTS REST

Audio stitching | pydub with ffmpeg

Audio stitching

pydub with ffmpeg

Storage | Local files on the server, with an audio cache keyed by hash of text, language and voice

Storage

Local files on the server, with an audio cache keyed by hash of text, language and voice

Pipeline

Upload file, then extract text per page.

Select the requested page range.

Split into chunks within the TTS length limit, breaking at sentence ends.

Check that the book's language has a Gnani voice for the chosen narrator.

Send each chunk to Gnani TTS REST with the voice for the chosen narrator and language.

Join the audio and export MP3.

Return the audio file and translated text to the frontend.

Security

The Gnani API key and the LLM key stay in server environment variables. They are never sent to the browser or committed to the repository.

Uploaded files are limited by size and type, and deleted after processing or on a timer.

Optional extras

TTS Streaming (SSE) for a faster first-play experience.

Voice cloning so users can listen in their own voice, with a consent note: users must only clone their own voice or one they have permission to use.

Speech-to-text (Prisma) for a voice command such as "go to chapter 2".

9. Gnani Models Used

To be named explicitly in the submission:

Gnani Timbre v2.5 (Text-to-Speech, REST): core of the product.

Optional, if built: Timbre streaming, voice cloning, Prisma speech-to-text.

Supporting tools: none beyond standard libraries for text extraction and audio joining. The app does not translate text.

10. Constraints and Open Items

Item | Action

Item

Action

API credit limit (playground shows 5k / 5k, unit not confirmed) | Check whether it counts characters, seconds or requests, and set the page cap accordingly

API credit limit (playground shows 5k / 5k, unit not confirmed)

Check whether it counts characters, seconds or requests, and set the page cap accordingly

Voice availability per language | Check the Available Voices page and fill the narrator-to-voice table

Voice availability per language

Check the Available Voices page and fill the narrator-to-voice table

TTS max text length per request | Check the TTS REST doc and set chunk size

TTS max text length per request

Check the TTS REST doc and set chunk size

Character and background artwork | Create or license original art

Character and background artwork

Create or license original art

Copyright on books | Demo only with public-domain books

Copyright on books

Demo only with public-domain books

Text extraction from Indian-language PDFs | Test one page per demo language, since PDF extraction can break non-Latin scripts, and prepare plain TXT versions as a fallback

Text extraction from Indian-language PDFs

Test one page per demo language, since PDF extraction can break non-Latin scripts, and prepare plain TXT versions as a fallback

11. Success Criteria

Must have (for submission)

A user can upload or choose a sample book, pick pages, language and narrator, and receive playable and downloadable audio.

At least three languages work end to end, including the demo language.

The bookshop theme and page-turn transitions are visible in the demo.

Gnani Timbre is named and used for all audio.

Should have

All supported languages work with at least one voice.

Library shelf with replay.

Speed control and translated text next to audio.

Nice to have

Sentence highlighting, voice cloning, streaming playback.

12. Build Plan (one day)

Block | Work

Block

Work

Hours 1-2 | Get Gnani API access working, test one paragraph through TTS, confirm voices, limits and credits

Hours 1-2

Get Gnani API access working, test one paragraph through TTS, confirm voices, limits and credits

Hours 3-5 | Backend pipeline: extract, chunk, TTS, stitch, cache

Hours 3-5

Backend pipeline: extract, chunk, TTS, stitch, cache

Hours 6-8 | Six frontend screens with the real flow and no animation

Hours 6-8

Six frontend screens with the real flow and no animation

Hour 9 | Bookshop styling, golden-wood buttons, spine-style language shelf

Hour 9

Bookshop styling, golden-wood buttons, spine-style language shelf

Hour 10 | Page-turn transitions

Hour 10

Page-turn transitions

Hour 11 | Testing across three languages, fixing errors, preparing the sample book cache

Hour 11

Testing across three languages, fixing errors, preparing the sample book cache

Hour 12 | One-page pitch, README, demo video, social post, form submission

Hour 12

One-page pitch, README, demo video, social post, form submission

Cut order if time runs short: page-turn animation polish first, then extra screens, then optional features. Never cut the working audio flow.

13. Submission Checklist

Matches the required fields of the submission form.

☐ Full name

☐ Registered email ID

☐ Teammate's registered email (if a team entry)

☐ Higher education institution name

☐ Project URL (GitHub, Drive or live link) containing a one-page solution pitch

☐ Demo video link (2-3 minutes)

☐ Bonus category: LinkedIn or X post tagging Gnani that describes the solution

☐ Joined the challenge Discord for updates

14. One-Page Pitch Outline

Problem: many people prefer to listen in their own language, and Indian-language books are often available only as text.

Solution: KathaVaani turns a book into an audiobook in an Indian language, with a narrator of your choice.

Gnani models used: Timbre v2.5 and any optional ones.

How it works: the pipeline in one short diagram or list.

Impact: who benefits and why.

Limits and next steps: page cap from free credits, no OCR yet, a queue for full-length books.

15. Demo Video Script (2-3 minutes)

(0:00-0:20) A person who loves stories in their mother tongue but finds long texts tiring to read.

(0:20-0:50) Enter the shop, upload a public-domain book, choose pages.

(0:50-1:20) Confirm the book's language (for example Telugu), pick a narrator, and play the voice preview.

(1:20-2:00) The binding screen, then the Library: play the audio with the text beside it.

(2:00-2:30) Download the file, show a second language, and close with the impact line.