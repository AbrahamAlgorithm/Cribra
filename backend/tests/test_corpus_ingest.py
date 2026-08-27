"""Tests for requirement corpus ingestion (Milestone 3).

The vector store is mocked throughout — no real ChromaDB or OpenAI calls in
the automated suite. Real ingestion against the actual corpus documents is
verified separately (see the Milestone 3 update doc).
"""

from __future__ import annotations

import fitz
import pytest

from app.retrieval import corpus_ingest


class _FakeVectorStore:
    def __init__(self):
        self.calls: list[dict] = []

    def add_texts(self, texts, metadatas, ids):
        self.calls.append({"texts": texts, "metadatas": metadatas, "ids": ids})


def _build_pdf(tmp_path, text: str):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(50, 50, 550, 750), text, fontsize=11)
    path = tmp_path / "corpus_doc.pdf"
    doc.save(str(path))
    doc.close()
    return path


def test_ingest_document_chunks_and_tags_with_section_reference(monkeypatch, tmp_path):
    # Mock the extractor directly rather than relying on real PDF text
    # rendering/reflow (insert_textbox does not reliably preserve exact
    # line breaks on re-extraction) — this test is about corpus_ingest's
    # chunk-tagging logic, not PDF layout, and section_index.py already has
    # its own dedicated, precisely-controlled tests.
    fake_store = _FakeVectorStore()
    monkeypatch.setattr(corpus_ingest, "get_vector_store", lambda: fake_store)

    # Enough repetitions to span multiple 500-word chunks — a single small
    # chunk starting at word 0 would correctly be tagged with the "PART I"
    # reference active at its start, not "Section 2" (which begins a few
    # words later within that same chunk); this needs a *later* chunk,
    # whose start position falls after the Section 2 marker, to see it.
    pages = [
        "PART I—TEST PART\n"
        + "2.  This is a real section with enough words to form multiple chunks. " * 300
    ]
    monkeypatch.setitem(corpus_ingest._EXTRACTORS, ".pdf", lambda path: pages)

    path = tmp_path / "corpus_doc.pdf"
    path.write_bytes(b"%PDF-1.4 fake")

    count = corpus_ingest.ingest_document(path, "Test Document", use_bare_number_sections=True)

    assert count > 1
    assert len(fake_store.calls) == 1
    call = fake_store.calls[0]
    assert len(call["texts"]) == count
    assert all(m["document_name"] == "Test Document" for m in call["metadatas"])
    assert all("section_reference" in m for m in call["metadatas"])
    assert any("Section 2" in m["section_reference"] for m in call["metadatas"])
    # The very first chunk (starting at word 0) is still under "PART I".
    assert "PART I" in call["metadatas"][0]["section_reference"]


def test_ingest_document_uses_deterministic_ids(monkeypatch, tmp_path):
    fake_store = _FakeVectorStore()
    monkeypatch.setattr(corpus_ingest, "get_vector_store", lambda: fake_store)

    text = "Some corpus content. " * 100
    path = _build_pdf(tmp_path, text)

    corpus_ingest.ingest_document(path, "Doc A")

    ids = fake_store.calls[0]["ids"]
    assert ids == [f"Doc A::chunk::{i}" for i in range(len(ids))]


def test_ingest_document_rejects_unsupported_file_type(tmp_path):
    path = tmp_path / "corpus.txt"
    path.write_text("some text")
    with pytest.raises(ValueError):
        corpus_ingest.ingest_document(path, "Doc")


def test_ingest_document_empty_content_skips_vector_store_call(monkeypatch, tmp_path):
    fake_store = _FakeVectorStore()
    monkeypatch.setattr(corpus_ingest, "get_vector_store", lambda: fake_store)

    doc = fitz.open()
    doc.new_page()  # blank page, no text
    path = tmp_path / "empty.pdf"
    doc.save(str(path))
    doc.close()

    count = corpus_ingest.ingest_document(path, "Empty Doc")

    assert count == 0
    assert fake_store.calls == []


def test_ingest_default_checklist_embeds_all_ten_items(monkeypatch):
    from app.api.routes_requirements import DEFAULT_CHECKLIST

    fake_store = _FakeVectorStore()
    monkeypatch.setattr(corpus_ingest, "get_vector_store", lambda: fake_store)

    count = corpus_ingest.ingest_default_checklist()

    assert count == len(DEFAULT_CHECKLIST) == 10
    call = fake_store.calls[0]
    assert len(call["texts"]) == 10
    assert all(m["document_name"] == "Default BPP Technical Compliance Checklist" for m in call["metadatas"])
    names = [name for name, _desc, _mandatory in DEFAULT_CHECKLIST]
    assert any("CAC Certificate" in n for n in names)
    assert any(text.startswith("Similar Project Experience:") for text in call["texts"])
