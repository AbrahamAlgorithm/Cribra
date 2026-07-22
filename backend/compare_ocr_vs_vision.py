"""
compare_ocr_vs_vision.py — Cribra: is Tesseract good enough for segmentation classification?

CONTEXT
-------
diagnose_fixture.py confirmed: the real 158-page bundle has ZERO text layer
on every page. Segmentation can't run at all without SOME per-page text to
keyword-match against.

This script answers the one open question before committing to the Hybrid
architecture (local OCR for classification, vision reserved for certificate
field extraction): is Tesseract's output on our real scans clean enough to
recognize headers like "CERTIFICATE OF INCORPORATION" or "PENSION COMMISSION"?

It runs BOTH Tesseract and GPT-4o vision on the same small sample of real
pages and prints them side by side so you can eyeball the difference
directly, plus the real cost of the vision side (Tesseract is free).

SETUP (one-time, local only — nothing touches Docker/production yet)
----------------------------------------------------------------------
    brew install tesseract          # macOS
    pip install pytesseract --break-system-packages
    export OPENAI_API_KEY=sk-...

USAGE
-----
    python compare_ocr_vs_vision.py tests/fixtures/real/Technical_Submission.pdf --pages 0,1,2,20,21,50,51,100,101,157

    (Pick page indices spread across the bundle — start, a middle chunk,
    and the end — so you see variety, not just the first few pages.)

    If you don't know which pages might be certificates yet, just sample
    every ~15th page across the document with:
    python compare_ocr_vs_vision.py tests/fixtures/real/Technical_Submission.pdf --stride 15
"""

import argparse
import base64
import io
import time

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from openai import OpenAI

PRICE_PER_M_INPUT = 2.50
PRICE_PER_M_OUTPUT = 10.00


def render_page_image(page, zoom: float = 2.0) -> bytes:
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def run_tesseract(png_bytes: bytes) -> tuple[str, float]:
    start = time.time()
    img = Image.open(io.BytesIO(png_bytes))
    text = pytesseract.image_to_string(img)
    elapsed = time.time() - start
    return text.strip(), elapsed


def run_vision(client: OpenAI, png_bytes: bytes) -> tuple[str, float, float]:
    b64 = base64.b64encode(png_bytes).decode("utf-8")
    start = time.time()
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe all visible text on this document page exactly as it appears. Output plain text only."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }
        ],
    )
    elapsed = time.time() - start
    text = resp.choices[0].message.content or ""
    cost = (
        resp.usage.prompt_tokens / 1_000_000 * PRICE_PER_M_INPUT
        + resp.usage.completion_tokens / 1_000_000 * PRICE_PER_M_OUTPUT
    )
    return text.strip(), elapsed, cost


# Headers we actually need Tesseract to surface for keyword matching to work
KEYWORDS_TO_CHECK = [
    "CERTIFICATE OF INCORPORATION", "CORPORATE AFFAIRS COMMISSION",
    "TAX CLEARANCE", "FEDERAL INLAND REVENUE",
    "PENSION COMMISSION", "PENCOM",
    "INDUSTRIAL TRAINING FUND", "ITF",
    "NIGERIA SOCIAL INSURANCE", "NSITF",
    "CURRICULUM VITAE", "AUDITED", "EQUIPMENT",
]


def check_keywords(text: str) -> list[str]:
    upper = text.upper()
    return [kw for kw in KEYWORDS_TO_CHECK if kw in upper]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    parser.add_argument("--pages", type=str, default=None,
                         help="Comma-separated page indices (0-based), e.g. 0,1,20,50,157")
    parser.add_argument("--stride", type=int, default=None,
                         help="Sample every Nth page instead of specifying indices")
    args = parser.parse_args()

    doc = fitz.open(args.pdf_path)
    total_pages = len(doc)

    if args.pages:
        indices = [int(x) for x in args.pages.split(",")]
    elif args.stride:
        indices = list(range(0, total_pages, args.stride))
    else:
        indices = list(range(0, min(10, total_pages)))

    print(f"\n=== OCR vs Vision Comparison — {len(indices)} page(s) of {total_pages} ===\n")

    client = OpenAI()
    total_vision_cost = 0.0

    for idx in indices:
        if idx >= total_pages:
            continue
        page = doc[idx]
        png_bytes = render_page_image(page)

        tess_text, tess_time = run_tesseract(png_bytes)
        vision_text, vision_time, vision_cost = run_vision(client, png_bytes)
        total_vision_cost += vision_cost

        tess_hits = check_keywords(tess_text)
        vision_hits = check_keywords(vision_text)

        print(f"--- Page {idx + 1} ---")
        print(f"[Tesseract]  {tess_time:.2f}s, free   | keywords found: {tess_hits or 'NONE'}")
        print(f"  preview: {tess_text[:150].replace(chr(10), ' ')}...")
        print(f"[Vision]     {vision_time:.2f}s, ${vision_cost:.4f} | keywords found: {vision_hits or 'NONE'}")
        print(f"  preview: {vision_text[:150].replace(chr(10), ' ')}...")

        if tess_hits == vision_hits and tess_hits:
            print("  \u2705 Tesseract found the same keywords as vision \u2014 good enough for classification here.")
        elif not tess_hits and vision_hits:
            print("  \u26a0\ufe0f  Tesseract found nothing where vision succeeded \u2014 check scan quality on this page.")
        elif tess_hits and not vision_hits:
            print("  \u2139\ufe0f  Tesseract found keywords vision didn't surface in this transcription style \u2014 fine.")
        else:
            print("  \u26a0\ufe0f  Neither found a known keyword \u2014 may be a non-certificate page, or scan quality issue.")
        print()

    print("=== Summary ===")
    print(f"Sample vision cost (for comparison only): ${total_vision_cost:.4f}")
    print(
        "\nDecision guide:\n"
        "- If Tesseract matched vision's keyword hits on most/all sampled pages:\n"
        "  \u2192 Hybrid is validated. Use Tesseract for segmentation classification,\n"
        "    reserve vision for certificate field extraction only.\n"
        "- If Tesseract missed keywords vision caught on several pages:\n"
        "  \u2192 Scan quality may be too poor for Tesseract. Consider full vision\n"
        "    for classification too, with per-page caching to control repeat cost.\n"
        "- Either way: classify_page() may need fuzzy/partial keyword matching\n"
        "  (not just exact substring match) to tolerate OCR noise \u2014 check the\n"
        "  'preview' text above for typos in otherwise-correct keywords."
    )


if __name__ == "__main__":
    main()