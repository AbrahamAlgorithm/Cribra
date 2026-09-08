"""Pre-transcribe every page of one or more PDFs into the vision cache.

Why this exists: a fully scanned bundle needs one GPT-4o vision call per
page, and the account's TPM ceiling — not local CPU — sets the floor on how
fast that can go. A cold 158-page run is rate-limit-bound for roughly ten
minutes; the same run against a warm cache took 40-70 seconds end to end.
Nothing about an evaluation is slow once the pages are cached, so the fix
for a live demo is to pay that cost once, ahead of time, off the clock.

Run it before a demo/defence, not during:

    python scripts/warm_vision_cache.py tests/fixtures/real/Technical_Submission.pdf

Safe to re-run and safe to interrupt: every page is written to the cache as
soon as it is transcribed, so a second run only fetches what is still
missing. `docker-compose.yml` bind-mounts the same directory, so warming
here also warms the container.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fitz

from app.config import get_settings
from app.ingestion import page_resolver, vision_cache


async def warm(path: str) -> None:
    page_count = fitz.open(path).page_count
    print(f"\n{path} — {page_count} pages", flush=True)

    semaphore = asyncio.Semaphore(get_settings().openai_vision_concurrency)
    document_hash = vision_cache.hash_file(path)
    done = fetched = cached = refused = 0
    started = time.monotonic()

    async def one(page_number: int) -> None:
        # _transcribe_page already short-circuits on a cache hit, so there is
        # no cheaper way to ask "is this page cached?" — asking it is the check.
        nonlocal done, fetched, cached, refused
        text, avoided_openai = await page_resolver._transcribe_page(path, page_number, semaphore, document_hash)
        done += 1
        if not text:
            refused += 1
        elif avoided_openai:
            cached += 1
        else:
            fetched += 1
            elapsed = time.monotonic() - started
            eta = (page_count - done) * (elapsed / done)
            print(
                f"  [{done}/{page_count}] page {page_number}: {len(text)} chars"
                f"  (~{eta / 60:.1f} min left)",
                flush=True,
            )

    await asyncio.gather(*(one(i) for i in range(page_count)))
    print(
        f"  {cached} already cached, {fetched} newly transcribed, "
        f"{refused} unreadable (refused at every rotation) "
        f"— {(time.monotonic() - started) / 60:.1f} min"
    )


async def main(paths: list[str]) -> None:
    if not paths:
        print(__doc__)
        raise SystemExit(2)
    missing = [p for p in paths if not Path(p).is_file()]
    if missing:
        raise SystemExit(f"No such file(s): {', '.join(missing)}")
    print(f"Vision cache: {get_settings().vision_cache_dir}")
    for path in paths:
        await warm(path)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
