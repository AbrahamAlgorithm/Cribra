# Cribra Backend

Cribra reads an **evaluation checklist** and a contractor's **submission documents**
and produces a structured, evidence-backed **Technical Compliance Evaluation Report**.
It is a verification tool, not a decision-maker — the procurement officer reviews the
report and makes the decision.

The full, authoritative specification lives in [SPEC.md](SPEC.md). All LLM prompts are
documented in [PROMPTS.md](PROMPTS.md).

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
tests/             pytest suites + fixtures
evaluation/        Evaluation harness (Precision/Recall/F1 vs expert ground truth)
data/chroma/       Persistent ChromaDB storage (gitignored)
```

## Status

Milestone 0 (project scaffolding) complete. See SPEC.md Section 8 for the milestone
roadmap; API endpoints beyond `/health` land in Milestones 1 and 5.
