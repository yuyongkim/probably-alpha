"""BOK (Bank of Korea) reports vector RAG — BGE-M3 embeddings via Ollama.

Separate from the TF-IDF ``rag/`` package which indexes investment literature.
BOK index is built by ``scripts/build_rag_bok.py`` and stored at
``~/.ky-platform/data/rag_bok/``.
"""
from .retriever import BOKRetriever, search_bok

__all__ = ["BOKRetriever", "search_bok"]
