"""Tests for per-page text resolution (Milestone 2, finalized architecture).

Text-first, GPT-4o vision fallback, cached and concurrent. Written after
real testing against a fully-scanned 158-page field-collected submission
found that segmentation cannot rely on text extraction alone — see
SPEC.md Section 8, Milestone 2. All OpenAI calls are mocked here; the real
API is exercised in a separate manual smoke test against the real document.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.ingestion import page_resolver, vision_cache


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content)


class _FakeAsyncChatAPI:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[_FakeChoice(self.response_text)])


class _FakeAsyncOpenAIClient:
    def __init__(self, response_text: str):
        self.chat = SimpleNamespace(completions=_FakeAsyncChatAPI(response_text))


@pytest.fixture(autouse=True)
def _isolated_vision_cache(tmp_path, monkeypatch):
    """Point the cache at a throwaway dir so tests don't pollute the real one."""
    from app.config import Settings, get_settings

    isolated = Settings(vision_cache_dir=str(tmp_path / "vision_cache"))
    monkeypatch.setattr("app.ingestion.vision_cache.get_settings", lambda: isolated)
    yield


def test_resolve_pages_sufficient_text_never_calls_vision(monkeypatch):
    fake_client = _FakeAsyncOpenAIClient("should not be used")
    monkeypatch.setattr(page_resolver, "_get_async_client", lambda: fake_client)

    sufficient_text = "CERTIFICATE OF INCORPORATION " * 20
    texts, methods = page_resolver.resolve_pages_sync("/tmp/bundle.pdf", [sufficient_text])

    assert methods == ["text"]
    assert texts[0] == sufficient_text
    assert fake_client.chat.completions.calls == []


def test_resolve_pages_insufficient_text_uses_vision(monkeypatch, tmp_path):
    fake_client = _FakeAsyncOpenAIClient("TAX CLEARANCE CERTIFICATE\nTCC998877")
    monkeypatch.setattr(page_resolver, "_get_async_client", lambda: fake_client)
    monkeypatch.setattr(page_resolver, "render_page_image", lambda path, index: b"fake-png-bytes")

    pdf_path = tmp_path / "bundle.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    texts, methods = page_resolver.resolve_pages_sync(str(pdf_path), ["short"])

    assert methods == ["vision"]
    assert "TAX CLEARANCE" in texts[0]
    assert len(fake_client.chat.completions.calls) == 1


def test_resolve_pages_caches_vision_result_by_image_hash(monkeypatch, tmp_path):
    fake_client = _FakeAsyncOpenAIClient("cached transcription")
    monkeypatch.setattr(page_resolver, "_get_async_client", lambda: fake_client)
    monkeypatch.setattr(page_resolver, "render_page_image", lambda path, index: b"same-bytes-every-time")

    pdf_path = tmp_path / "bundle.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    # Two separate pages that happen to render to the same image bytes
    # (contrived for the test, but proves the cache key is image-content-based).
    texts, methods = page_resolver.resolve_pages_sync(str(pdf_path), ["short1", "short2"])

    assert methods == ["vision", "vision"]
    assert texts[0] == texts[1] == "cached transcription"
    # Only one real API call — the second page hit the cache.
    assert len(fake_client.chat.completions.calls) == 1


def test_resolve_pages_docx_insufficient_text_has_no_vision_fallback(monkeypatch, caplog):
    import logging

    fake_client = _FakeAsyncOpenAIClient("should not be used")
    monkeypatch.setattr(page_resolver, "_get_async_client", lambda: fake_client)

    with caplog.at_level(logging.WARNING, logger="app.ingestion.page_resolver"):
        texts, methods = page_resolver.resolve_pages_sync("/tmp/bundle.docx", ["short"])

    assert methods == ["text"]
    assert texts == ["short"]
    assert fake_client.chat.completions.calls == []
    assert "no vision fallback available" in caplog.text.lower()


def test_resolve_pages_empty_input_returns_empty():
    assert page_resolver.resolve_pages_sync("/tmp/bundle.pdf", []) == ([], [])


def test_resolve_pages_preserves_order_across_mixed_pages(monkeypatch, tmp_path):
    fake_client = _FakeAsyncOpenAIClient("vision text")
    monkeypatch.setattr(page_resolver, "_get_async_client", lambda: fake_client)
    monkeypatch.setattr(page_resolver, "render_page_image", lambda path, index: f"page-{index}".encode())

    pdf_path = tmp_path / "bundle.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    sufficient = "CERTIFICATE OF INCORPORATION " * 20
    pages = [sufficient, "short", sufficient, "short"]

    texts, methods = page_resolver.resolve_pages_sync(str(pdf_path), pages)

    assert methods == ["text", "vision", "text", "vision"]
    assert texts[0] == sufficient
    assert texts[2] == sufficient


# --- vision_cache -------------------------------------------------------------


def test_vision_cache_roundtrip(tmp_path, monkeypatch):
    from app.config import Settings

    isolated = Settings(vision_cache_dir=str(tmp_path / "cache"))
    monkeypatch.setattr(vision_cache, "get_settings", lambda: isolated)

    image_hash = vision_cache.hash_image(b"some image bytes")
    assert vision_cache.get_cached(image_hash) is None

    vision_cache.set_cached(image_hash, "transcribed text")
    assert vision_cache.get_cached(image_hash) == "transcribed text"


def test_vision_cache_hash_is_content_addressed():
    assert vision_cache.hash_image(b"a") == vision_cache.hash_image(b"a")
    assert vision_cache.hash_image(b"a") != vision_cache.hash_image(b"b")
