"""Tests for the requirement-corpus retriever (Milestone 3).

The LangChain vector store / retriever is mocked — no real ChromaDB or
OpenAI calls in the automated suite.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.retrieval import retriever


class _FakeRetriever:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.invoked_with: str | None = None

    def invoke(self, query: str) -> list[Document]:
        self.invoked_with = query
        return self.documents


def test_retrieve_maps_documents_to_retrieved_chunks(monkeypatch):
    documents = [
        Document(
            page_content="Contractors must submit 3-5 similar completed projects.",
            metadata={"document_name": "BPP SBD", "section_reference": "Clause 5.3"},
        ),
        Document(
            page_content="Equipment schedule requirements.",
            metadata={"document_name": "BPP SBD", "section_reference": "Clause 5.4"},
        ),
    ]
    fake_retriever = _FakeRetriever(documents)
    monkeypatch.setattr(retriever, "get_retriever", lambda k=4: fake_retriever)

    results = retriever.retrieve("similar project experience requirement")

    assert len(results) == 2
    assert results[0].text == documents[0].page_content
    assert results[0].document_name == "BPP SBD"
    assert results[0].section_reference == "Clause 5.3"
    assert fake_retriever.invoked_with == "similar project experience requirement"


def test_retrieve_handles_missing_metadata_gracefully(monkeypatch):
    documents = [Document(page_content="Some text", metadata={})]
    monkeypatch.setattr(retriever, "get_retriever", lambda k=4: _FakeRetriever(documents))

    results = retriever.retrieve("query")

    assert results[0].document_name == ""
    assert results[0].section_reference == ""


def test_retrieve_passes_k_through_to_get_retriever(monkeypatch):
    captured_k = []

    def fake_get_retriever(k=4):
        captured_k.append(k)
        return _FakeRetriever([])

    monkeypatch.setattr(retriever, "get_retriever", fake_get_retriever)

    retriever.retrieve("query", k=7)

    assert captured_k == [7]


def test_retrieve_default_k_is_four(monkeypatch):
    captured_k = []

    def fake_get_retriever(k=4):
        captured_k.append(k)
        return _FakeRetriever([])

    monkeypatch.setattr(retriever, "get_retriever", fake_get_retriever)

    retriever.retrieve("query")

    assert captured_k == [retriever.DEFAULT_TOP_K]
    assert retriever.DEFAULT_TOP_K == 4
