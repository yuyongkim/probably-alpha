"""Broker report RAG over the Google Drive research corpus.

The Drive folder is the primary source of truth; the local TF-IDF artefacts live
under ``~/.ky-platform/data/rag_broker`` and optional dense GPU vectors live
under ``~/.ky-platform/data/rag_broker_vec`` so API queries do not depend on
live Drive access.
"""
from .retriever import BrokerReportRetriever, search_broker_reports
from .vector import (
    BrokerReportVectorRetriever,
    get_broker_vector_retriever,
    search_broker_report_vectors,
)

__all__ = [
    "BrokerReportRetriever",
    "BrokerReportVectorRetriever",
    "get_broker_vector_retriever",
    "search_broker_reports",
    "search_broker_report_vectors",
]
