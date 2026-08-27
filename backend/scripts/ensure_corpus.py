"""Ensure the requirement corpus is embedded in ChromaDB before the app starts.

Run as a standalone step in the container's startup command (see Dockerfile)
— deliberately NOT a FastAPI startup hook, so it can never fire during
`TestClient(app)` in the test suite (no OpenAI calls in automated tests).

Cloud Run gives the container no persistent disk by default, so a fresh
instance's `data/chroma` is empty every cold start. The corpus is small and
fixed (PPA 2007, BPP SBD, the default checklist's own descriptions — see
app/retrieval/corpus_ingest.py), so re-ingesting on an empty store is cheap
and simpler than wiring up persistent cloud storage for this deployment.
Idempotent: skips entirely if the collection already has content (e.g. local
docker-compose with a persisted volume, or a warm instance).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.corpus_ingest import ingest_default_checklist, ingest_document  # noqa: E402
from app.retrieval.vector_store import get_vector_store  # noqa: E402

CORPUS_DIR = Path(__file__).resolve().parent.parent / "requirement_corpus"


def main() -> None:
    store = get_vector_store()
    existing = store._collection.count()
    if existing > 0:
        print(f"[ensure_corpus] Collection already has {existing} chunks — skipping ingestion.")
        return

    print("[ensure_corpus] Collection is empty — ingesting requirement corpus...")

    ppa_path = CORPUS_DIR / "Public-Procurement-Act-2007.pdf"
    n = ingest_document(ppa_path, "Public Procurement Act 2007", use_bare_number_sections=True)
    print(f"[ensure_corpus]   {ppa_path.name}: {n} chunks")

    # Distinct document_name per file — required, not cosmetic: ingest_document
    # builds chunk ids as "{document_name}::chunk::{i}", so giving both BPP
    # files the same name collides their ids and silently overwrites part of
    # the first file's chunks with the second's (caught by comparing the
    # ingested total against the actual collection count before this fix).
    for filename, document_name in (
        ("3.7-BPP-6.2.1.v.b.1-SBD-for-Procurement-of-Works-Large-Building (2).pdf", "BPP Standard Bidding Document"),
        (
            "3.7-Forms-BPP-6.2.1.v.b.1-SBD-for-Procurement-of-Works-Large-Building (1).pdf",
            "BPP Standard Bidding Document — Forms",
        ),
    ):
        path = CORPUS_DIR / filename
        n = ingest_document(path, document_name)
        print(f"[ensure_corpus]   {path.name}: {n} chunks")

    n = ingest_default_checklist()
    print(f"[ensure_corpus]   Default checklist descriptions: {n} chunks")

    total = store._collection.count()
    print(f"[ensure_corpus] Done — {total} chunks in collection.")


if __name__ == "__main__":
    main()
