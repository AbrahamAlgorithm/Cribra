"""Tests for structured field extraction (Phase 2.2). Written in Milestone 2.

All OpenAI calls are mocked — no real network calls in the automated suite
(see the Milestone 2 update doc for the separate live smoke test).
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace

import pytest

from app.ingestion import field_extractor
from app.ingestion.schema import DocumentSegment


def _fake_chat_response(payload: dict) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])


class _FakeChatAPI:
    def __init__(self, payload: dict):
        self.payload = payload
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _fake_chat_response(self.payload)


class _FakeOpenAIClient:
    def __init__(self, payload: dict):
        self.chat = SimpleNamespace(completions=_FakeChatAPI(payload))


# --- is_text_sufficient -------------------------------------------------------


def test_is_text_sufficient_true_for_long_meaningful_text():
    text = "CERTIFICATE OF INCORPORATION " * 20
    assert field_extractor.is_text_sufficient(text)


def test_is_text_sufficient_false_for_short_text():
    assert not field_extractor.is_text_sufficient("CAC")


def test_is_text_sufficient_false_for_garbage_text():
    garbage = "@#$%^&*()_+" * 30
    assert not field_extractor.is_text_sufficient(garbage)


# --- process_segment: non-certificate types never call the LLM ---------------


def test_process_segment_non_certificate_skips_llm_entirely():
    segment = DocumentSegment(
        document_type="Key Personnel CVs",
        page_start=0,
        page_end=0,
        text="CURRICULUM VITAE\nJane Doe, Site Engineer",
        source_path="/tmp/bundle.pdf",
    )
    result = field_extractor.process_segment(segment)

    assert result.extraction_method == "text"
    assert result.normalized_text == segment.text
    assert result.holder_name is None
    assert result.identifier is None


# --- process_segment: certificate type, sufficient text -> text extraction ---


def test_process_segment_certificate_with_sufficient_text(monkeypatch):
    payload = {
        "document_type": "CAC Certificate",
        "holder_name": "Example Contractors Ltd",
        "identifier": "RC1234567",
        "issue_date": "2020-01-15",
        "expiry_date": "2030-01-15",
    }
    fake_client = _FakeOpenAIClient(payload)
    monkeypatch.setattr(field_extractor, "_get_client", lambda: fake_client)

    segment = DocumentSegment(
        document_type="CAC Certificate",
        page_start=0,
        page_end=0,
        text="CERTIFICATE OF INCORPORATION " * 20,
        source_path="/tmp/bundle.pdf",
    )
    result = field_extractor.process_segment(segment)

    assert result.extraction_method == "text"
    assert result.holder_name == "Example Contractors Ltd"
    assert result.identifier == "RC1234567"
    assert str(result.issue_date) == "2020-01-15"
    assert str(result.expiry_date) == "2030-01-15"

    call = fake_client.chat.completions.calls[0]
    assert call["model"] == "gpt-4o"
    assert call["temperature"] == 0
    assert call["response_format"] == {"type": "json_object"}


# --- process_segment: certificate type, insufficient text + PDF -> vision ----


def test_process_segment_certificate_with_insufficient_text_uses_vision(monkeypatch, tmp_path):
    payload = {
        "document_type": "Tax Clearance Certificate",
        "holder_name": "Example Contractors Ltd",
        "identifier": "TCC998877",
        "issue_date": "2023-03-01",
        "expiry_date": "2026-03-01",
    }
    fake_client = _FakeOpenAIClient(payload)
    monkeypatch.setattr(field_extractor, "_get_client", lambda: fake_client)
    monkeypatch.setattr(field_extractor, "render_page_image", lambda path, page: b"\x89PNG fake-bytes")

    pdf_path = tmp_path / "bundle.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    segment = DocumentSegment(
        document_type="Tax Clearance Certificate",
        page_start=2,
        page_end=2,
        text="blurry scan",  # too short to be "sufficient"
        source_path=str(pdf_path),
    )
    result = field_extractor.process_segment(segment)

    assert result.extraction_method == "vision"
    assert result.identifier == "TCC998877"

    call = fake_client.chat.completions.calls[0]
    assert call["messages"][1]["content"][1]["type"] == "image_url"


# --- process_segment: certificate type, insufficient text + DOCX -> best-effort text ---


def test_process_segment_certificate_docx_insufficient_text_falls_back_to_text(monkeypatch, caplog):
    payload = {
        "document_type": "PENCOM Compliance Certificate",
        "holder_name": None,
        "identifier": None,
        "issue_date": None,
        "expiry_date": None,
    }
    fake_client = _FakeOpenAIClient(payload)
    monkeypatch.setattr(field_extractor, "_get_client", lambda: fake_client)

    segment = DocumentSegment(
        document_type="PENCOM Compliance Certificate",
        page_start=0,
        page_end=0,
        text="short",
        source_path="/tmp/bundle.docx",
    )
    with caplog.at_level(logging.WARNING, logger="app.ingestion.field_extractor"):
        result = field_extractor.process_segment(segment)

    assert result.extraction_method == "text"
    assert "no vision fallback available" in caplog.text.lower()
