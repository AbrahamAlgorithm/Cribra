"""
locate_certificates.py — free, full-bundle scan to find candidate CAC/PENCOM/ITF/NSITF pages

WHY THIS SCRIPT
---------------
compare_ocr_vs_vision.py's stride sample caught a Tax Clearance certificate
but missed CAC, PENCOM, ITF, and NSITF entirely — pure luck of which pages
the stride landed on. Those four are the highest-stakes pages in the whole
system (Milestone 4A's deterministic expiry rule depends on reading them
correctly), so guessing isn't good enough.

This runs Tesseract (free — no API cost) across ALL 158 pages, using a
loose/fuzzy keyword net (broader than compare_ocr_vs_vision.py's exact
matches) to flag candidate pages for each certificate type, plus reports
which pages produced empty/near-empty text (Tesseract failures — these
need a vision pass regardless of the final architecture, since we can't
even tell what they are yet).

Once this prints candidate page numbers, run a real vision call on JUST
those specific pages to confirm date/RC-number extraction quality — a
handful of targeted calls, not a full 158-page spend.

USAGE
-----
    python locate_certificates.py tests/fixtures/real/Technical_Submission.pdf
"""

import sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
import io

# Loose keyword net — broader than the exact-match list, includes partial/
# fragment terms likely to survive noisy OCR, and near-neighbor terms.
CANDIDATES = {
    "CAC": ["CORPORATE AFFAIRS", "INCORPORATION", "RC NO", "RC:", "REGISTRATION NO", "BUSINESS NAME"],
    "TAX CLEARANCE": ["TAX CLEARANCE", "FEDERAL INLAND REVENUE", "FIRS", "TIN"],
    "PENCOM": ["PENSION", "PENCOM", "PEN COM", "RETIREMENT SAVINGS"],
    "ITF": ["INDUSTRIAL TRAINING", "ITF"],
    "NSITF": ["SOCIAL INSURANCE", "NSITF", "EMPLOYEE COMPENSATION"],
    "AUDITED ACCOUNTS": ["AUDITED", "FINANCIAL STATEMENT", "DIRECTORS REPORT", "BALANCE SHEET"],
    "CV / PERSONNEL": ["CURRICULUM VITAE", "PERSONAL DATA", "DATE OF BIRTH", "QUALIFICATION"],
    "PROFESSIONAL REGISTRATION": ["COREN", "CORBON", "REGISTERED ENGINEER", "PROFESSIONAL BODY"],
    "SIMILAR PROJECTS": ["AWARD LETTER", "COMPLETION CERTIFICATE", "CONTRACT SUM", "CERTIFICATE OF COMPLETION"],
    "EQUIPMENT": ["EQUIPMENT SCHEDULE", "PLANT AND MACHINERY", "OWNED", "LEASED"],
}


def render_page_image(page, zoom: float = 2.0) -> bytes:
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def main():
    if len(sys.argv) < 2:
        print("Usage: python locate_certificates.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    print(f"\n=== Scanning all {total_pages} pages with Tesseract (free, no API calls) ===\n")

    hits: dict[str, list[int]] = {k: [] for k in CANDIDATES}
    empty_or_failed: list[int] = []

    for i, page in enumerate(doc):
        png_bytes = render_page_image(page)
        img = Image.open(io.BytesIO(png_bytes))
        text = pytesseract.image_to_string(img).strip()

        if len(text) < 20:
            empty_or_failed.append(i + 1)
            continue

        upper = text.upper()
        for doc_type, keywords in CANDIDATES.items():
            if any(kw in upper for kw in keywords):
                hits[doc_type].append(i + 1)

        if (i + 1) % 20 == 0:
            print(f"  ...scanned {i + 1}/{total_pages} pages")

    print("\n=== Candidate Pages by Document Type ===\n")
    for doc_type, pages in hits.items():
        if pages:
            print(f"{doc_type:28s} -> pages {pages}")
        else:
            print(f"{doc_type:28s} -> NO CANDIDATES FOUND (may need vision-only search, or absent from bundle)")

    print(f"\n=== Pages with near-empty/failed Tesseract output ({len(empty_or_failed)} total) ===")
    print(f"{empty_or_failed}")
    print(
        "\nThese pages produced <20 chars from Tesseract — could be blank pages, "
        "very poor scans, rotated pages, or a certificate Tesseract couldn't read "
        "at all. Worth a targeted vision check on these specifically, since a "
        "certificate hiding in this list would currently be invisible to "
        "classification entirely."
    )

    print(
        "\n=== Next step ===\n"
        "For CAC / PENCOM / ITF / NSITF specifically: if candidates were found "
        "above, run a real vision call on just those page numbers to confirm "
        "clean extraction of RC number / certificate number / expiry date — "
        "these are the fields Milestone 4A's deterministic rule depends on. "
        "If NO candidates were found for one of these four, check the "
        "'near-empty/failed' list above first — the certificate may be sitting "
        "there, unreadable by Tesseract, and only vision will reveal it."
    )


if __name__ == "__main__":
    main()