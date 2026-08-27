FROM python:3.13-slim

WORKDIR /app

# PyMuPDF/chromadb wheels cover standard platforms, but keep a compiler
# available as a fallback for any dependency without a prebuilt wheel for
# the build platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY requirement_corpus/ ./requirement_corpus/

ENV PYTHONUNBUFFERED=1
# Cloud Run injects $PORT at runtime; 8080 is its convention and the local
# default below when running this image directly (e.g. `docker run -p 8080:8080`).
ENV PORT=8080
EXPOSE 8080

# Corpus ingestion runs once per cold start (no persistent disk on Cloud Run
# by default — see scripts/ensure_corpus.py) before the server starts
# accepting traffic; idempotent, so a warm instance or a locally persisted
# volume (docker-compose) just skips it.
CMD ["sh", "-c", "python scripts/ensure_corpus.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
