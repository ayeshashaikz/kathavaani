"""
Text chunking module for KathaVaani.
Splits literature into natural sentence-level chunks (respecting Indic and Latin punctuation)
without exceeding TTS character limits.
"""

import re
from typing import List
from backend.config import MAX_CHUNK_CHARS, MIN_CHUNK_CHARS


# Sentence delimiter regex supporting English and Indic scripts
# Matches: . ! ? | and Indic Purna Virama (। U+0964) and Double Danda (॥ U+0965)
SENTENCE_END_PATTERN = re.compile(r'([.!?।॥]+[\s\n]+|[\n]{2,})')


def split_into_sentences(text: str) -> List[str]:
    """Splits text into individual sentences preserving punctuation."""
    if not text:
        return []

    raw_tokens = SENTENCE_END_PATTERN.split(text.strip())
    sentences: List[str] = []
    current_sentence = ""

    for token in raw_tokens:
        if not token:
            continue
        if SENTENCE_END_PATTERN.match(token):
            current_sentence += token.strip()
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            current_sentence = ""
        else:
            current_sentence += token

    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    return sentences


def subdivide_long_sentence(sentence: str, max_chars: int) -> List[str]:
    """
    Subdivides an unusually long single sentence at clause boundaries
    (commas, semicolons, dashes) or word boundaries.
    """
    sub_clauses = re.split(r'([,;:—–-]\s+)', sentence)
    chunks: List[str] = []
    current = ""

    for clause in sub_clauses:
        if len(current) + len(clause) <= max_chars:
            current += clause
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(clause) <= max_chars:
                current = clause
            else:
                # Word-level fallback
                words = clause.split()
                w_current = ""
                for w in words:
                    if len(w_current) + len(w) + 1 <= max_chars:
                        w_current = f"{w_current} {w}".strip()
                    else:
                        if w_current.strip():
                            chunks.append(w_current.strip())
                        w_current = w
                current = w_current

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_text_by_sentences(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """
    Groups sentences into speech chunks under max_chars.
    Breaks strictly at sentence boundaries whenever possible.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    sentences = split_into_sentences(cleaned)
    chunks: List[str] = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If a single sentence exceeds the maximum threshold, subdivide it
        if len(sentence) > max_chars:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            sub_chunks = subdivide_long_sentence(sentence, max_chars)
            chunks.extend(sub_chunks)
            continue

        # If appending this sentence fits within max_chars
        candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            # Commit current chunk and start a new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

