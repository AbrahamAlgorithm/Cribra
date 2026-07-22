"""
dump_page_range.py — free Tesseract text preview across a page range

Prints a short preview of each page's text so you can scan for content
the keyword lists might have missed (e.g. similar-project evidence phrased
in unexpected vocabulary) — no vision cost, no need to upload anything,
just paste the printed output back.

USAGE
-----
    python dump_page_range.py tests/fixtures/real/Technical_Submission.pdf 108 158
"""

import sys
import io
import fitz
import pytesseract
from PIL import Image


def main():
    if len(sys.argv) < 4:
        print("Usage: python dump_page_range.py <pdf_path> <start_page_1indexed> <end_page_1indexed>")
        sys.exit(1)

    pdf_path, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    doc = fitz.open(pdf_path)

    for i in range(start - 1, min(end, len(doc))):
        page = doc[i]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img).strip()
        preview = text[:200].replace("\n", " ") if text else "(empty / failed)"
        print(f"--- Page {i + 1} ---")
        print(preview)
        print()


if __name__ == "__main__":
    main()