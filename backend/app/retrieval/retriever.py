"""Query embedding + similarity search over the requirement corpus, via a
genuine LangChain retriever (`Chroma.as_retriever`), top-k configurable
(default 4). Implemented in Milestone 3.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.retrievers import BaseRetriever

from app.retrieval.vector_store import get_vector_store

DEFAULT_TOP_K = 4


@dataclass
class RetrievedChunk:
    text: str
    document_name: str
    section_reference: str


def get_retriever(k: int = DEFAULT_TOP_K) -> BaseRetriever:
    return get_vector_store().as_retriever(search_kwargs={"k": k})


def retrieve(query: str, k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Embed `query` and return the top-k most relevant corpus chunks."""
    documents = get_retriever(k=k).invoke(query)
    return [
        RetrievedChunk(
            text=document.page_content,
            document_name=document.metadata.get("document_name", ""),
            section_reference=document.metadata.get("section_reference", ""),
        )
        for document in documents
    ]
