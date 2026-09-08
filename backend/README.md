# Cribra Backend

Cribra reads an **evaluation checklist** and a contractor's **submission documents**
and produces a structured, evidence-backed **Technical Compliance Evaluation Report**.
It is a verification tool, not a decision-maker — the procurement officer reviews the
report and makes the decision.

The full, authoritative specification lives in [SPEC.md](SPEC.md). All LLM prompts are
documented in [PROMPTS.md](PROMPTS.md).

## Deployed

- App: https://cribra-frontend-taqq76r7ua-uc.a.run.app
- API: https://cribra-backend-taqq76r7ua-uc.a.run.app

Both run on Google Cloud Run. The frontend bakes its API URL in at build
time (see `frontend/.env.example`), so a backend redeploy under a new URL
requires rebuilding the frontend image, not just redeploying it. Currently
deployed manually (`docker build` → push to Artifact Registry → `gcloud run
deploy`) rather than via the GitHub Actions workflow in this repo, which is
blocked on a GitHub account billing issue unrelated to the code.

## Tech Stack

Python 3.11+ · FastAPI · LangChain · GPT-4o (OpenAI) · PyMuPDF · python-docx ·
`text-embedding-3-small` · ChromaDB · pytest

## Setup

```bash
# 1. Create and activate a virtual environment (Python 3.11+)
python3.13 -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

## Run time, and warming the vision cache

The submission bundles are fully scanned, so every page needs one GPT-4o
vision call, and what bounds a cold run is the account's tokens-per-minute
ceiling rather than local CPU — on a 30,000 TPM account a cold 158-page
bundle is rate-limited for roughly ten minutes. Measured on the real
158-page submission:

| | ingestion |
|---|---|
| cold cache | ~10 min (rate-limit bound), often failing |
| warm cache | **8.7 s** |

So warm the cache **before** a demo, never during one:

```bash
python scripts/warm_vision_cache.py tests/fixtures/real/Technical_Submission.pdf
```

It is resumable and safe to re-run — only missing pages are fetched, and
`docker-compose.yml` bind-mounts the same directory, so warming on the host
also warms the container.

Two things to know about the cache, because both have bitten this project:

- Resolved page text is keyed by **document fingerprint + page number**, so a
  warm run reads small files and rasterizes nothing. Transcriptions are also
  still keyed by rendered-image hash (which is what the rotation-retry path
  needs), and that second key depends on `PDF_RENDER_ZOOM` — changing it
  forces every page to be rendered again. Leave it at `2.0`. It is not a cost
  lever either: `1.5` and `2.0` both resize to the same 6 tiles (1105 tokens)
  on GPT-4o's side, so lowering it saves nothing and only costs fidelity.
- Every run logs its hit rate (`Page resolution: N/M pages needed vision — X
  needed no OpenAI call (cached), Y called OpenAI`). If `X` is 0 on a document
  you have already processed, the cache is cold and the run will be slow —
  check `PDF_RENDER_ZOOM` and that `data/vision_cache` is mounted.

If you still see repeated `429 Too Many Requests` responses, lower
`OPENAI_VISION_CONCURRENCY` and `OPENAI_FIELD_EXTRACTION_CONCURRENCY` to `1`.
That trades throughput for reliability; it does not reduce total token cost.

## Run

```bash
uvicorn app.main:app --reload
```

Verify it's up:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

Interactive API docs: http://127.0.0.1:8000/docs

## Test

```bash
pytest
```

## Run with Docker

```bash
cp .env.example .env
# then edit .env and set OPENAI_API_KEY

docker compose up
```

The container ingests the requirement corpus (PPA 2007, BPP SBD, the default
checklist) into ChromaDB on first start (`scripts/ensure_corpus.py`) — a
named volume persists it, so subsequent restarts skip re-ingestion.
`data/vision_cache` and `data/uploads` are bind-mounted to the host, so the
vision cache is shared with direct `uvicorn` runs and survives
`docker compose down -v`. Verify:

```bash
curl http://127.0.0.1:8000/health
```

Building/running the image directly (without compose) works the same way,
but without persistence across container restarts:

```bash
docker build -t cribra-backend .
docker run -p 8080:8080 --env-file .env cribra-backend
```

## Project Layout

```
app/
  main.py          FastAPI entry point (/health + API routers)
  config.py        Environment-driven configuration
  api/             REST route handlers
  ingestion/       PDF/DOCX extraction, preprocessing, chunking, embedding
  retrieval/       ChromaDB vector store + similarity search
  reasoning/       Prompts, deterministic validation rules, LLM evaluator
  models/          Domain model (Evaluation, Requirement, Submission)
  storage/         Job/evaluation store
scripts/           One-off/startup scripts (e.g. corpus ingestion for Docker)
tests/             pytest suites + fixtures
evaluation/        Evaluation harness (Precision/Recall/F1 vs expert ground truth)
data/chroma/       Persistent ChromaDB storage (gitignored)
Dockerfile         Container image for the backend
docker-compose.yml Local run with a persisted ChromaDB volume
```
