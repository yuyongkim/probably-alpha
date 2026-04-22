"""Build the knowledge-base RAG index.

Usage:
    # Full build from QuantPlatform/knowledge/
    python scripts/build_rag.py --source knowledge \
        --source-path "C:/Users/USER/Desktop/QuantPlatform/knowledge"

    # Health check (read-only)
    python scripts/build_rag.py --healthcheck

Writes artefacts to ~/.ky-platform/data/rag/:
    - index.pkl      TF-IDF vectoriser + sparse matrix + chunk ids
    - chunks.jsonl   one JSON record per chunk (metadata + text)
    - meta.json      build manifest

Prints a small validation block with sample queries at the end of a build.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List

# Make `ky_core` importable when running the script from the repo root
_THIS = Path(__file__).resolve()
_REPO = _THIS.parent.parent
_CORE_PKG = _REPO / "packages" / "core"
if str(_CORE_PKG) not in sys.path:
    sys.path.insert(0, str(_CORE_PKG))

from ky_core.rag import retriever as rag_retriever  # noqa: E402
from ky_core.rag.chunker import chunk_document  # noqa: E402
from ky_core.rag.extractor import extract_text, iter_knowledge_files  # noqa: E402
from ky_core.rag.index import build_index  # noqa: E402
from ky_core.rag.models import Chunk  # noqa: E402


logger = logging.getLogger("build_rag")


# --- validation fixtures -------------------------------------------------

SAMPLE_QUERIES = [
    "circle of competence",
    "VCP pattern Minervini",
    "risk of ruin position sizing",
]


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _humanise_bytes(n: int) -> str:
    step = 1024.0
    for unit in ("B", "KB", "MB", "GB"):
        if n < step:
            return f"{n:.1f} {unit}"
        n /= step
    return f"{n:.1f} TB"


# --- subcommands ---------------------------------------------------------

def run_healthcheck(index_dir: Path) -> int:
    print(f"[healthcheck] index_dir = {index_dir}")
    if not index_dir.is_dir():
        print("[healthcheck] index directory does not exist -run a build first.")
        return 1
    r = rag_retriever.Retriever(index_dir)
    if not r.is_ready():
        print("[healthcheck] index.pkl or chunks.jsonl missing -run a build first.")
        return 1
    meta = r.meta() or {}
    print(
        f"[healthcheck] ok - {meta.get('chunks')} chunks from "
        f"{meta.get('files_indexed')}/{meta.get('files_total')} files, "
        f"built_at {meta.get('built_at')}"
    )
    # try a live query so we surface pickle/version issues
    try:
        results = r.search("circle of competence", top_k=1)
        if results:
            top = results[0]
            print(
                f"[healthcheck] sample query ok - top result: "
                f"{top.source_file} (score {top.score:.4f})"
            )
        else:
            print("[healthcheck] sample query returned 0 results (unexpected)")
    except Exception as exc:
        print(f"[healthcheck] sample query FAILED: {exc}")
        return 2
    return 0


def run_build(args: argparse.Namespace) -> int:
    source_path = Path(args.source_path).expanduser().resolve()
    index_dir = Path(args.output).expanduser().resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    print(f"[build] source_label = {args.source}")
    print(f"[build] source_path  = {source_path}")
    print(f"[build] index_dir    = {index_dir}")

    if not source_path.is_dir():
        print(f"[build] ERROR: source_path does not exist: {source_path}")
        return 2

    t0 = time.time()
    files = list(iter_knowledge_files(source_path))
    print(f"[build] discovered {len(files)} candidate files")
    if args.limit:
        files = files[: args.limit]
        print(f"[build] --limit applied, using {len(files)} files")

    failed: List[str] = []
    all_chunks: List[Chunk] = []
    total_words = 0
    skipped_empty = 0

    for i, path in enumerate(files, start=1):
        rel = path.relative_to(source_path)
        t_file = time.time()
        try:
            pages = extract_text(path)
        except Exception as exc:
            logger.warning("extract failed: %s -%s", rel, exc)
            failed.append(str(rel))
            continue

        if not pages:
            logger.info("no text extracted from %s (likely scanned PDF)", rel)
            failed.append(str(rel))
            continue

        try:
            chunks = chunk_document(
                path,
                pages,
                target_words=args.target_words,
                overlap_words=args.overlap_words,
                knowledge_root=source_path,
            )
        except Exception as exc:
            logger.warning("chunk failed: %s -%s", rel, exc)
            failed.append(str(rel))
            continue

        if not chunks:
            skipped_empty += 1
            logger.info("no chunks from %s (too short)", rel)
            continue

        all_chunks.extend(chunks)
        total_words += sum(c.word_count for c in chunks)

        if i % 10 == 0 or i == len(files):
            elapsed = time.time() - t0
            print(
                f"[build] [{i}/{len(files)}] {rel.name[:60]!s:<62}"
                f" → {len(chunks):>4} chunks ({time.time() - t_file:.1f}s) "
                f"total={len(all_chunks):,} elapsed={elapsed:.0f}s"
            )

    print(
        f"[build] extraction done: {len(files) - len(failed)} indexed, "
        f"{len(failed)} failed, {skipped_empty} empty, "
        f"{len(all_chunks):,} total chunks"
    )

    if not all_chunks:
        print("[build] ERROR: no chunks produced -aborting")
        return 3

    print("[build] fitting TF-IDF and writing artefacts...")
    meta = build_index(
        all_chunks,
        index_dir=index_dir,
        source_label=args.source,
        source_path=str(source_path),
        files_total=len(files),
        files_failed=failed,
    )
    index_path = index_dir / "index.pkl"
    chunks_path = index_dir / "chunks.jsonl"
    print("[build] wrote:")
    print(f"  {index_path}   ({_humanise_bytes(index_path.stat().st_size)})")
    print(f"  {chunks_path}  ({_humanise_bytes(chunks_path.stat().st_size)})")
    print(f"  {index_dir / 'meta.json'}")
    print(
        f"[build] vocabulary={meta['vocabulary_size']:,} "
        f"matrix_nnz={meta['matrix_nnz']:,}"
    )

    # validation pass
    print("")
    print("[validate] running sample queries")
    r = rag_retriever.Retriever(index_dir)
    for q in SAMPLE_QUERIES:
        results = r.search(q, top_k=3)
        print(f"  query: {q!r}")
        if not results:
            print("    (no results)")
            continue
        for rank, res in enumerate(results, start=1):
            pages_str = ""
            if res.page_start is not None:
                pages_str = f" p.{res.page_start}"
                if res.page_end and res.page_end != res.page_start:
                    pages_str += f"-{res.page_end}"
            print(
                f"    {rank}. score={res.score:.4f}  {res.source_file}{pages_str}"
            )

    print(f"[build] done in {time.time() - t0:.0f}s")
    return 0


# --- CLI -----------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build the ky-platform RAG index")
    p.add_argument(
        "--source",
        default="knowledge",
        help="source label stored in meta.json (default: knowledge)",
    )
    p.add_argument(
        "--source-path",
        default=r"C:/Users/USER/Desktop/QuantPlatform/knowledge",
        help="directory to recursively scan for PDFs/TXT",
    )
    p.add_argument(
        "--output",
        default=str(Path.home() / ".ky-platform" / "data" / "rag"),
        help="index output directory (default: ~/.ky-platform/data/rag)",
    )
    p.add_argument("--target-words", type=int, default=500)
    p.add_argument("--overlap-words", type=int, default=100)
    p.add_argument("--limit", type=int, default=0, help="debug: max files to process")
    p.add_argument("--healthcheck", action="store_true", help="read-only check")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)
    if args.healthcheck:
        return run_healthcheck(Path(args.output).expanduser().resolve())
    return run_build(args)


if __name__ == "__main__":
    raise SystemExit(main())
