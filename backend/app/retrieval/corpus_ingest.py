"""Requirement corpus ingestion: extract, preprocess, chunk (tagged with a
citation reference per chunk), embed, and store in ChromaDB.

Implemented in Milestone 3. This is the "same chunking pipeline" phases.md
Phase 3 refers to — reuses `app.ingestion.chunker`, `preprocess`, and the
PDF/DOCX extractors built in Milestone 2, applied to the requirement corpus
(`requirement_corpus/`) instead of a contractor submission.
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion import chunker, docx_extractor, pdf_extractor, preprocess
from app.retrieval.section_index import build_reference_index
from app.retrieval.vector_store import get_vector_store

_EXTRACTORS = {
    ".pdf": pdf_extractor.extract_pages,
    ".docx": docx_extractor.extract_pages,
}

_CHUNK_STEP = chunker.DEFAULT_CHUNK_SIZE - chunker.DEFAULT_OVERLAP


def ingest_document(
    path: str | Path, document_name: str, use_bare_number_sections: bool = False
) -> int:
    """Chunk, embed, and store one corpus document. Returns the chunk count.

    `use_bare_number_sections` should be True only for PPA 2007 (or any
    future corpus document using its bare "2.  The Council shall" numbering
    convention) — see `section_index.build_reference_index`.

    Uses deterministic ids (`{document_name}::chunk::{i}`) so re-ingesting
    the same document after a content or chunking change upserts cleanly
    rather than duplicating — see `vector_store.reset_collection` for a full
    rebuild instead.
    """
    path_str = str(path)
    suffix = Path(path_str).suffix.lower()
    extractor = _EXTRACTORS.get(suffix)
    if extractor is None:
        raise ValueError(f"Unsupported corpus file type: '{suffix}'")

    pages = extractor(path_str)
    cleaned_pages = preprocess.clean_pages(pages)
    full_text = "\n".join(cleaned_pages)

    reference_index = build_reference_index(
        cleaned_pages, document_name, use_bare_number_sections=use_bare_number_sections
    )
    chunks = chunker.chunk_text(full_text)

    if not chunks:
        return 0

    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    for i, chunk in enumerate(chunks):
        start_word = i * _CHUNK_STEP
        texts.append(chunk)
        metadatas.append(
            {
                "document_name": document_name,
                "section_reference": reference_index.lookup(start_word),
                "source_path": path_str,
                "chunk_index": i,
            }
        )
        ids.append(f"{document_name}::chunk::{i}")

    get_vector_store().add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(texts)


def ingest_default_checklist() -> int:
    """Embed the 10-item default checklist's own descriptions as corpus chunks.

    phases.md Phase 3 names three corpus sources: "PPA 2007, BPP SBD,
    default checklist descriptions" — this is the third. Real finding while
    spot-checking retrieval: the BPP SBD is a blank template (its Evaluation
    and Qualification Criteria section is bracketed placeholder text —
    "[The Procuring Entity will provide the preliminary evaluation
    criteria...]"), so it doesn't actually contain the specific numeric
    thresholds the default checklist cites (e.g. "3-5 completed jobs in the
    last 5 years"). Those came from the field interview, live only in
    `routes_requirements.DEFAULT_CHECKLIST` — without ingesting them too,
    Milestone 4B would have nothing concrete to retrieve and cite for
    exactly the numbers the checklist itself asserts.
    """
    from app.api.routes_requirements import DEFAULT_CHECKLIST

    document_name = "Default BPP Technical Compliance Checklist"
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []
    for name, description, _is_mandatory in DEFAULT_CHECKLIST:
        texts.append(f"{name}: {description}")
        metadatas.append(
            {
                "document_name": document_name,
                "section_reference": f"{document_name}, {name}",
                "source_path": "app/api/routes_requirements.py",
                "chunk_index": 0,
            }
        )
        ids.append(f"{document_name}::chunk::{name}")

    get_vector_store().add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return len(texts)
