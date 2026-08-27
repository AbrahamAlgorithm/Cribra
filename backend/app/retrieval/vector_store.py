"""ChromaDB persistent collection management, via LangChain's Chroma wrapper.

Implemented in Milestone 3. Uses `langchain_chroma.Chroma` (backed by the
already-pinned `chromadb` persistent client) + `langchain_openai.OpenAIEmbeddings`
so `retriever.py` can build a genuine LangChain retriever object, per
phases.md Phase 3 ("Build the LangChain retriever").
"""

from __future__ import annotations

import threading

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings

COLLECTION_NAME = "requirement_corpus"
EMBEDDING_MODEL = "text-embedding-3-small"

_vector_store: Chroma | None = None
_init_lock = threading.Lock()


def get_vector_store() -> Chroma:
    """Lazily construct the singleton Chroma client — locked (Milestone 6 prep,
    real-data finding): evaluator.py now evaluates requirements concurrently
    (ThreadPoolExecutor), and multiple threads racing to construct
    `chromadb.PersistentClient` for the same path at once threw a real
    `KeyError` inside chromadb's own shared-system-client registry
    (`SharedSystemClient._create_system_if_not_exists`) — not a hypothetical
    risk, reproduced on a real evaluation run. Double-checked locking so the
    lock is only paid once, at warmup.
    """
    global _vector_store
    if _vector_store is None:
        with _init_lock:
            if _vector_store is None:
                settings = get_settings()
                embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=settings.openai_api_key)
                _vector_store = Chroma(
                    collection_name=COLLECTION_NAME,
                    embedding_function=embeddings,
                    persist_directory=settings.chroma_persist_dir,
                )
    return _vector_store


def reset_collection() -> None:
    """Delete and recreate the collection — used for a clean corpus rebuild.

    `corpus_ingest.py` uses deterministic chunk IDs (document + chunk index),
    so re-ingesting the same document without a reset would upsert cleanly on
    its own; this is for the "start over completely" case (e.g. a document
    was removed from the corpus, or chunking logic changed).
    """
    get_vector_store().delete_collection()
    global _vector_store
    _vector_store = None
