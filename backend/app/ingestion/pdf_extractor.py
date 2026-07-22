"""PDF text extraction via PyMuPDF (fitz). Implemented in Milestone 2.

Provides per-page text (segmentation in `segmentation.py` needs page boundaries,
not just a flat blob) and page rasterization for the vision fallback in
`field_extractor.py`.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def extract_pages(path: str | Path) -> list[str]:
    """Return the raw extracted text of each page, in order."""
    with fitz.open(path) as doc:
        return [page.get_text() for page in doc]


def page_count(path: str | Path) -> int:
    with fitz.open(path) as doc:
        return doc.page_count


def render_page_image(path: str | Path, page_number: int, zoom: float = 2.0) -> bytes:
    """Rasterize a single page (0-indexed) to PNG bytes for GPT-4o vision input.

    zoom=2.0 roughly doubles the default 72 DPI render to ~144 DPI, which is
    enough for a vision model to read certificate text reliably without
    producing an unnecessarily large image.
    """
    with fitz.open(path) as doc:
        page = doc[page_number]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        return pixmap.tobytes("png")
