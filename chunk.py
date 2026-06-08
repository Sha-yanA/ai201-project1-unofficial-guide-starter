"""
Chunking pipeline.

Implements the strategy from planning.md:
  - Chunk size: 400–500 characters (~100–125 tokens)
  - Overlap: 50 characters
  - Self-contained units (reviews, Reddit comments) that fit within max_chars
    are kept whole. Longer units (Alligator article paragraphs, long Reddit
    posts) are split at sentence boundaries with overlap so context is not lost
    across chunk boundaries.
  - A single sentence that exceeds max_chars is hard-split as a last resort.

Usage:
    python chunk.py          # runs full pipeline and prints stats + sample chunks
    from chunk import chunk_units   # import into embed.py
"""

import re

CHUNK_MAX_CHARS = 500
CHUNK_OVERLAP_CHARS = 50


def _hard_split(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split a single oversized block on character count with overlap."""
    parts = []
    start = 0
    step = max_chars - overlap
    while start < len(text):
        parts.append(text[start : start + max_chars].strip())
        start += step
    return [p for p in parts if p]


def chunk_text(
    text: str,
    max_chars: int = CHUNK_MAX_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    """
    Split a single text string into chunks.

    Splitting order:
      1. If text fits in max_chars, return it as-is (preserves whole reviews).
      2. Otherwise split at sentence boundaries (.  !  ?) with overlap.
      3. If a single sentence exceeds max_chars, hard-split on character count.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # Tokenise into sentences on terminal punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If sentence alone exceeds max_chars, flush current and hard-split it
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(sentence, max_chars, overlap))
            continue

        candidate = (current + " " + sentence).strip() if current else sentence

        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            # Seed the next chunk with the trailing overlap of the current one
            # so key context (e.g. the dining hall name) isn't cut off.
            tail = current[-overlap:].lstrip() if len(current) > overlap else current
            current = (tail + " " + sentence).strip()
            # If tail + sentence still exceeds max_chars, just use the sentence
            if len(current) > max_chars:
                current = sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


def chunk_units(
    units: list[dict],
    max_chars: int = CHUNK_MAX_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> list[dict]:
    """
    Apply chunking to every ingested unit and return the final chunk list.
    Each chunk inherits its parent unit's source metadata unchanged.
    """
    chunks: list[dict] = []

    for unit in units:
        text = unit["text"]
        meta = {k: v for k, v in unit.items() if k != "text"}

        for part in chunk_text(text, max_chars, overlap):
            if part.strip():
                chunks.append({"text": part, **meta})

    return chunks


if __name__ == "__main__":
    import json
    from ingest import ingest_documents

    print("Running ingestion + chunking pipeline...")
    units = ingest_documents()
    chunks = chunk_units(units)

    lengths = [len(c["text"]) for c in chunks]

    print(f"\nPipeline summary")
    print(f"  Units ingested : {len(units)}")
    print(f"  Chunks produced: {len(chunks)}")
    print(f"  Min chars      : {min(lengths)}")
    print(f"  Max chars      : {max(lengths)}")
    print(f"  Avg chars      : {sum(lengths) // len(lengths)}")

    # Count how many units were split vs kept whole
    split_count = sum(1 for u in units if len(u["text"]) > CHUNK_MAX_CHARS)
    print(f"  Units split    : {split_count} / {len(units)}")

    print("\nSample chunks (first 3):")
    for chunk in chunks[:3]:
        preview = chunk["text"][:120].replace("\n", " ")
        print(f"  [{chunk['source']} | {chunk['location']}]")
        print(f"  {preview!r}")
        print()

    with open("chunks_debug.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print("Saved to chunks_debug.json")