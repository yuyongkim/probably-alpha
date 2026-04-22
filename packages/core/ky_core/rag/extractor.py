"""PDF / TXT text extraction.

Primary: PyMuPDF (fitz) — fast, robust on most PDFs.
Fallback: pdfplumber — slower but handles a few oddballs PyMuPDF chokes on.
TXT files are read directly with utf-8 / utf-8-sig / latin-1 fallback.

`extract_text` returns a list of (page_number, page_text) tuples so downstream
chunkers can track `page_start` / `page_end` metadata. For TXT files a single
(None, full_text) entry is returned.

Scanned/image-only PDFs are detected early and skipped — pdfplumber tends to
hang on them and we don't ship OCR in this phase.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Pages = list of (page_no_or_None, text). page_no is 1-based for PDFs.
Pages = List[Tuple[Optional[int], str]]

SUPPORTED_SUFFIXES = {".pdf", ".txt"}

# When PyMuPDF returns fewer than this many characters for the first
# `_SCAN_PROBE_PAGES` pages, we treat the PDF as a scanned/image-only file
# and skip it (pdfplumber would hang without OCR).
_SCAN_PROBE_PAGES = 10
_SCAN_MIN_CHARS_PER_PAGE = 40
# Hard time budget per document for the pdfplumber fallback, in seconds.
_PDFPLUMBER_BUDGET_SEC = 120.0


def _extract_pdf_pymupdf(path: Path) -> Tuple[Pages, int]:
    """Return (pages_with_text, total_page_count)."""
    import fitz  # PyMuPDF

    pages: Pages = []
    doc = fitz.open(str(path))
    total = 0
    try:
        total = doc.page_count
        for i, page in enumerate(doc, start=1):
            try:
                text = page.get_text("text") or ""
            except Exception as exc:  # defensive: one bad page shouldn't kill the doc
                logger.debug("pymupdf: bad page %s in %s: %s", i, path.name, exc)
                text = ""
            if text.strip():
                pages.append((i, text))
    finally:
        doc.close()
    return pages, total


def _looks_like_scanned_pdf(path: Path) -> bool:
    """Cheap probe: open the first `_SCAN_PROBE_PAGES` pages with PyMuPDF and
    check the text density. Returns True if the PDF is almost certainly an
    image-only scan (at which point pdfplumber would hang without OCR)."""
    try:
        import fitz
    except Exception:
        return False
    try:
        doc = fitz.open(str(path))
    except Exception:
        return False
    try:
        probe = min(_SCAN_PROBE_PAGES, doc.page_count)
        if probe == 0:
            return True
        total_chars = 0
        for i in range(probe):
            try:
                text = doc[i].get_text("text") or ""
            except Exception:
                text = ""
            total_chars += len(text.strip())
        # very low density → treat as scan
        return (total_chars / probe) < _SCAN_MIN_CHARS_PER_PAGE
    finally:
        doc.close()


def _extract_pdf_pdfplumber(path: Path) -> Pages:
    """pdfplumber fallback with a soft time budget. We check the wall clock
    between pages and bail out (returning whatever text we've got) when the
    budget is exhausted — some PDFs cause pdfplumber to grind for minutes per
    page."""
    import time

    import pdfplumber

    pages: Pages = []
    start = time.time()
    budget_hit = False
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            if time.time() - start > _PDFPLUMBER_BUDGET_SEC:
                logger.warning(
                    "pdfplumber: time budget hit on page %s of %s, stopping early",
                    i,
                    path.name,
                )
                budget_hit = True
                break
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                logger.debug("pdfplumber: bad page %s in %s: %s", i, path.name, exc)
                text = ""
            if text.strip():
                pages.append((i, text))
    if budget_hit and not pages:
        # We got nothing usable within the budget — better to surface as a failure.
        return []
    return pages


def _extract_txt(path: Path) -> Pages:
    for enc in ("utf-8", "utf-8-sig", "cp949", "latin-1"):
        try:
            text = path.read_text(encoding=enc)
            return [(None, text)]
        except UnicodeDecodeError:
            continue
    # last resort
    text = path.read_bytes().decode("utf-8", errors="replace")
    return [(None, text)]


def extract_text(path: Path) -> Pages:
    """Extract text from a PDF or TXT file.

    Returns a list of (page_no, text) tuples — possibly empty if extraction
    yielded nothing usable. Never raises for empty PDFs; only raises if both
    PDF backends fail hard.
    """
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return _extract_txt(path)
    if suffix != ".pdf":
        raise ValueError(f"unsupported file type: {path.suffix}")

    # Try PyMuPDF first.
    pymu_pages: Pages = []
    pymu_total = 0
    try:
        pymu_pages, pymu_total = _extract_pdf_pymupdf(path)
    except Exception as exc:
        logger.warning("pymupdf failed for %s (%s) — will try fallback", path.name, exc)

    if pymu_pages:
        return pymu_pages

    # pymupdf returned empty. Probe for scan-only PDFs and skip them early.
    logger.info("pymupdf returned no text for %s (%s pages)", path.name, pymu_total)
    if _looks_like_scanned_pdf(path):
        logger.info(
            "skipping %s — appears to be image-only / scanned (no OCR in this phase)",
            path.name,
        )
        return []

    # Fallback to pdfplumber for the non-scan "PyMuPDF choked" case only.
    try:
        return _extract_pdf_pdfplumber(path)
    except Exception as exc:
        logger.error("pdfplumber also failed for %s: %s", path.name, exc)
        return []


def iter_knowledge_files(root: Path) -> Iterable[Path]:
    """Yield all PDF/TXT files under `root`, deterministic sort."""
    if not root.is_dir():
        raise FileNotFoundError(f"knowledge root not found: {root}")
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(p)
    files.sort(key=lambda p: str(p).lower())
    return files
