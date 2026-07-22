"""Chunking with configurable size + overlap (start: 500 tokens / 50 overlap).

Implemented in Milestone 2.
"""

from __future__ import annotations

DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 50


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """Split text into overlapping chunks, sized by whitespace-token count.

    Whitespace-splitting is used as a token-count approximation rather than a
    real tokenizer — no tokenizer is pinned in requirements.txt (SPEC.md
    Section 2 fixes the tech stack) and this wasn't asked for. Close enough
    for English prose; SPEC.md Phase 3 already flags these sizes for
    empirical tuning once real documents are in.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and less than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = chunk_size - overlap
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start : start + chunk_size]))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks
