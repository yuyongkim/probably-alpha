"""HTML scrapers for series with no stable API.

Stability is explicitly low — sites can change layout without notice.
Each scraper raises AdapterError on parse failure so the collector
records it instead of silently writing bad rows.
"""
from __future__ import annotations

from ky_adapters.scrapers.bdi import BDIScraperAdapter, BDIRow

__all__ = ["BDIScraperAdapter", "BDIRow"]
