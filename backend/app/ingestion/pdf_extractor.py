"""PDF text extraction via PyMuPDF (fitz). Implemented in Milestone 2.

Provides per-page text (segmentation in `segmentation.py` needs page boundaries,
not just a flat blob) and page rasterization for the vision fallback in
`field_extractor.py`.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from app.config import get_settings


def extract_pages(path: str | Path) -> list[str]:
    """Return the raw extracted text of each page, in order."""
    with fitz.open(path) as doc:
        return [page.get_text() for page in doc]


def page_count(path: str | Path) -> int:
    with fitz.open(path) as doc:
        return doc.page_count


def render_page_image(path: str | Path, page_number: int, zoom: float | None = None, rotation: int = 0) -> bytes:
    """Rasterize a single page (0-indexed) to PNG bytes for GPT-4o vision input.

    The default zoom comes from config. `1.5` renders at about 108 DPI, which
    is often a better speed/size tradeoff than 144 DPI for large scanned
    bundles while still keeping certificate text legible.

    `rotation` (0/90/180/270) exists for page_resolver.py's refusal-retry
    path: a real genuinely upside-down scan in the field-collected bundle
    got a flat refusal from GPT-4o at 0deg, and rotating to the correct
    orientation resolved it on the first try — see page_resolver.py.
    """
    if zoom is None:
        zoom = get_settings().pdf_render_zoom
    with fitz.open(path) as doc:
        page = doc[page_number]
        matrix = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pixmap = page.get_pixmap(matrix=matrix)
        return pixmap.tobytes("png")
