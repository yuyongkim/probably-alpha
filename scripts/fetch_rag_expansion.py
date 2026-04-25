"""Fetch additional sources for the book/research RAG layer.

Sources (auto-downloadable):
  A) Howard Marks memos — scraped from Oaktree's public memo archive
  B) Older Buffett letters (1977-2003) — Berkshire Hathaway HTML letters,
     saved as .txt so they index alongside the PDFs
  C) Munger speeches — a hand-curated list of canonical transcripts
     (USC 2007, Harvard 1995 "Psychology of Human Misjudgment", etc.)

Output dir: <KNOWLEDGE_ROOT>/extra_2026/
After this finishes, rebuild the book RAG:
    python scripts/build_rag.py --source knowledge \
        --source-path "C:/Users/USER/Desktop/QuantPlatform/knowledge"

Sources that CANNOT be auto-fetched (need user-provided PDFs dropped into
<KNOWLEDGE_ROOT>/extra_2026/):
  D) Hedge Fund Wizards (Schwager 2012), Unknown Market Wizards (2020)
  E) Korean trader books / interviews (정채진, 김동주, 이상기, etc.)
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger("fetch_rag_expansion")

DEFAULT_KNOWLEDGE_ROOT = Path("C:/Users/USER/Desktop/QuantPlatform/knowledge")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}


# ---------------------------------------------------------------------------
# B) Older Buffett letters — Berkshire Hathaway publishes 1977-2003 as HTML.
# 2004+ are PDFs (already in knowledge/). Save HTML letters as .txt so the
# extractor picks them up.
# ---------------------------------------------------------------------------

BUFFETT_HTML_YEARS = list(range(1977, 1998))           # 1977-1997 = HTML
BUFFETT_PDF_YEARS = list(range(1998, 2004))            # 1998-2003 = PDF
BUFFETT_HTML_URL = "https://www.berkshirehathaway.com/letters/{year}.html"
BUFFETT_PDF_URL = "https://www.berkshirehathaway.com/letters/{year}pdf.pdf"


def _strip_html(html: str) -> str:
    # Cheap HTML→text — no bs4 dependency. Drops scripts/styles, then tags.
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</p\s*>", "\n\n", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), html)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def fetch_buffett_old_letters(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0

    # 1977-1997: HTML letters
    for year in BUFFETT_HTML_YEARS:
        target = out_dir / f"buffett_letter_{year}.txt"
        if target.exists() and target.stat().st_size > 5000:
            logger.info("buffett %d already present (skipped)", year)
            continue
        url = BUFFETT_HTML_URL.format(year=year)
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
        except Exception as exc:
            logger.warning("buffett %d FAIL: %s", year, exc)
            continue
        try:
            html = r.content.decode("utf-8")
        except UnicodeDecodeError:
            html = r.content.decode("windows-1252", errors="replace")
        text = _strip_html(html)
        if len(text) < 1000:
            logger.warning("buffett %d looks empty (%d chars), skipped", year, len(text))
            continue
        header = f"Warren Buffett — Berkshire Hathaway Shareholder Letter ({year})\n"
        header += f"Source: {url}\n\n"
        target.write_text(header + text, encoding="utf-8")
        saved += 1
        logger.info("buffett %d saved (%d chars, html)", year, len(text))
        time.sleep(0.5)

    # 1998-2003: try PDF first, then HTML fallback (`<year>htm.html`).
    # URL patterns vary slightly by year:
    #   1998:  1998pdf.pdf
    #   1999:  no PDF — only 1999htm.html
    #   2000-2002: <year>pdf.pdf
    #   2003: 2003ltr.pdf
    pdf_url_overrides = {
        2003: "https://www.berkshirehathaway.com/letters/2003ltr.pdf",
    }
    for year in BUFFETT_PDF_YEARS:
        pdf_target = out_dir / f"buffett_letter_{year}.pdf"
        txt_target = out_dir / f"buffett_letter_{year}.txt"
        if pdf_target.exists() and pdf_target.stat().st_size > 30_000:
            logger.info("buffett %d already present (skipped)", year)
            continue
        if txt_target.exists() and txt_target.stat().st_size > 5000:
            logger.info("buffett %d already present (skipped)", year)
            continue
        # Attempt PDF
        pdf_url = pdf_url_overrides.get(year, BUFFETT_PDF_URL.format(year=year))
        got_pdf = False
        try:
            r = requests.get(pdf_url, headers=HEADERS, timeout=30)
            if r.ok and r.content.startswith(b"%PDF"):
                pdf_target.write_bytes(r.content)
                saved += 1
                logger.info("buffett %d saved (%.1f KB, pdf)", year, len(r.content) / 1024)
                got_pdf = True
        except Exception as exc:
            logger.debug("buffett %d pdf attempt failed: %s", year, exc)
        if got_pdf:
            time.sleep(0.5)
            continue
        # HTML fallback — `<year>htm.html`
        html_url = f"https://www.berkshirehathaway.com/letters/{year}htm.html"
        try:
            r = requests.get(html_url, headers=HEADERS, timeout=30)
            r.raise_for_status()
        except Exception as exc:
            logger.warning("buffett %d FAIL (both pdf and html): %s", year, exc)
            continue
        try:
            html = r.content.decode("utf-8")
        except UnicodeDecodeError:
            html = r.content.decode("windows-1252", errors="replace")
        text = _strip_html(html)
        if len(text) < 1000:
            logger.warning("buffett %d looks empty (%d chars), skipped", year, len(text))
            continue
        header = f"Warren Buffett — Berkshire Hathaway Shareholder Letter ({year})\n"
        header += f"Source: {html_url}\n\n"
        txt_target.write_text(header + text, encoding="utf-8")
        saved += 1
        logger.info("buffett %d saved (%d chars, html fallback)", year, len(text))
        time.sleep(0.5)

    return saved


# ---------------------------------------------------------------------------
# A) Howard Marks memos — Oaktree's public memo archive at
# oaktreecapital.com/insights/memos. The page renders an anchor list of
# /docs/default-source/memos/<slug>.pdf links. We scrape the listing page
# and download all PDFs.
# ---------------------------------------------------------------------------

OAKTREE_MEMOS_LIST_URL = "https://www.oaktreecapital.com/insights/memos"
OAKTREE_PDF_RE = re.compile(
    r'href="(?P<href>[^"]*/memos/[^"]+\.pdf)"', re.I
)


def fetch_marks_memos(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(OAKTREE_MEMOS_LIST_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as exc:
        logger.error("oaktree listing fetch failed: %s", exc)
        return 0
    html = r.text
    hrefs = sorted({m.group("href") for m in OAKTREE_PDF_RE.finditer(html)})
    if not hrefs:
        logger.warning(
            "oaktree listing page had 0 memo PDF links — page is likely "
            "JS-rendered. Falling back to known mirror list."
        )
        hrefs = _known_marks_memo_urls()
    saved = 0
    for href in hrefs:
        url = urljoin(OAKTREE_MEMOS_LIST_URL, href)
        slug = Path(urlparse(url).path).stem
        target = out_dir / f"marks_memo_{slug}.pdf"
        if target.exists() and target.stat().st_size > 50_000:
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            target.write_bytes(r.content)
            saved += 1
            logger.info("marks memo saved: %s (%.1f KB)", slug, len(r.content) / 1024)
        except Exception as exc:
            logger.warning("marks memo %s FAIL: %s", slug, exc)
        time.sleep(0.5)
    return saved


def _known_marks_memo_urls() -> list[str]:
    # Hand-curated fallback when the JS-rendered page hides the list.
    # Oaktree uses a stable URL pattern:
    #   /docs/default-source/memos/<slug>.pdf
    # We only seed the most cited ones; the live scrape covers the rest
    # when the listing page renders properly.
    base = "https://www.oaktreecapital.com/docs/default-source/memos/"
    slugs = [
        "the-most-important-thing",
        "youcantpredictyoucanprepare",
        "us-its-them",
        "dare-to-be-great",
        "dare-to-be-great-ii",
        "the-race-to-the-bottom",
        "the-race-is-on",
        "expert-opinion",
        "risk",
        "risk-revisited",
        "risk-revisited-again",
        "the-truth-about-investing",
        "the-realist-s-creed",
        "the-illusion-of-knowledge",
        "the-anatomy-of-a-correction",
        "on-the-couch",
        "liquidity",
        "the-long-view",
        "the-value-of-predictions",
        "the-value-of-predictions-or-where-d-all-this-rain-come-from",
        "deja-vu-all-over-again",
        "yes-but-what-have-you-done-for-me-lately",
        "what-worries-me",
        "you-bet",
        "memo-to-oaktree-clients-the-most-important-thing",
        "the-happy-medium",
        "diversification-of-sources-of-return",
        "ditto",
        "what-now",
        "the-tide-goes-out",
        "calibrating",
        "expert-opinion",
        "yet-again",
        "thinking-about-macro",
        "the-route-to-performance",
        "first-quarter-performance",
        "fewer-losers-or-more-winners",
        "the-most-important-thing-is-",
        "us-and-them",
        "this-time-its-different",
    ]
    return [base + s + ".pdf" for s in slugs]


# ---------------------------------------------------------------------------
# C) Munger speeches — a curated list of canonical transcripts. These are
# scraped from various stable hosts (Munger's own talks, USC, Harvard).
# We save as .txt so they index without OCR.
# ---------------------------------------------------------------------------

MUNGER_SPEECHES = [
    {
        "name": "munger_psychology_of_human_misjudgment_1995",
        "title": "Charlie Munger — The Psychology of Human Misjudgment (Harvard, 1995, revised 2005)",
        # Stable mirrors of the speech transcript
        "urls": [
            "https://www.farnamstreetblog.com/wp-content/uploads/2015/06/The-Psychology-of-Human-Misjudgment.pdf",
            "https://www.rbcpa.com/Mungerspeech_june_95.pdf",
        ],
        "format": "pdf",
    },
    {
        "name": "munger_usc_law_school_2007",
        "title": "Charlie Munger — USC Law School Commencement (2007)",
        "urls": [
            "https://genius.com/Charlie-munger-usc-law-school-commencement-speech-annotated",
        ],
        "format": "html",
    },
    {
        "name": "munger_lessons_for_investors_2003",
        "title": "Charlie Munger — Academic Economics: Strengths and Faults (2003 UCSB)",
        "urls": [
            "https://old.ycombinator.com/munger.html",
        ],
        "format": "html",
    },
    {
        "name": "munger_practical_thought_about_practical_thought_1996",
        "title": "Charlie Munger — Practical Thought About Practical Thought? (1996)",
        "urls": [
            "https://thealchemyofadvice.files.wordpress.com/2015/06/practicalthoughtaboutpracticalthought1.pdf",
        ],
        "format": "pdf",
    },
]


def fetch_munger_speeches(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for spec in MUNGER_SPEECHES:
        name = spec["name"]
        fmt = spec["format"]
        ext = ".pdf" if fmt == "pdf" else ".txt"
        target = out_dir / f"{name}{ext}"
        if target.exists() and target.stat().st_size > (50_000 if fmt == "pdf" else 5000):
            logger.info("munger %s already present", name)
            continue
        ok = False
        for url in spec["urls"]:
            try:
                r = requests.get(url, headers=HEADERS, timeout=60)
                r.raise_for_status()
            except Exception as exc:
                logger.warning("munger %s url FAIL (%s): %s", name, url, exc)
                continue
            if fmt == "pdf":
                if not r.content.startswith(b"%PDF"):
                    logger.warning("munger %s — %s did not return a PDF", name, url)
                    continue
                target.write_bytes(r.content)
            else:
                try:
                    html = r.content.decode("utf-8")
                except UnicodeDecodeError:
                    html = r.content.decode("windows-1252", errors="replace")
                text = _strip_html(html)
                if len(text) < 1000:
                    logger.warning("munger %s — %s body too short", name, url)
                    continue
                header = f"{spec['title']}\nSource: {url}\n\n"
                target.write_text(header + text, encoding="utf-8")
            saved += 1
            ok = True
            logger.info("munger %s saved from %s", name, url)
            break
        if not ok:
            logger.warning("munger %s — all URLs failed", name)
        time.sleep(0.5)
    return saved


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--knowledge-root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
        help="Root knowledge dir (default: %(default)s)",
    )
    p.add_argument("--skip-marks", action="store_true")
    p.add_argument("--skip-buffett", action="store_true")
    p.add_argument("--skip-munger", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    out_dir = args.knowledge_root / "extra_2026"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("output dir: %s", out_dir)

    counts = {}
    if not args.skip_buffett:
        counts["buffett"] = fetch_buffett_old_letters(out_dir)
    if not args.skip_marks:
        counts["marks"] = fetch_marks_memos(out_dir)
    if not args.skip_munger:
        counts["munger"] = fetch_munger_speeches(out_dir)

    logger.info("done. saved per source: %s", counts)
    logger.info(
        "next: drop Wizards 4/5 and Korean trader PDFs into %s, "
        "then rebuild RAG: python scripts/build_rag.py --source knowledge "
        "--source-path \"%s\"",
        out_dir,
        args.knowledge_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
