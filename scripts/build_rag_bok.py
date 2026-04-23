"""Build vector RAG index for Bank of Korea (한은) reports.

Source:
    C:/Users/USER/Desktop/한국은행보고서/extracted_text/*.txt   (~3,224 files, pre-extracted)
    C:/Users/USER/Desktop/한국은행보고서/bok_reports.db         (optional metadata enrichment)

Pipeline:
    txt -> clean PDF artifacts -> chunk -> Ollama BGE-M3 embed -> numpy + jsonl

Output (~/.ky-platform/data/rag_bok/):
    vectors.npy       shape (N, 1024) float32
    chunks.jsonl      one record per chunk (text + metadata)
    meta.json         build manifest

Usage:
    python scripts/build_rag_bok.py                     # full build
    python scripts/build_rag_bok.py --limit 50          # pilot
    python scripts/build_rag_bok.py --healthcheck       # verify index
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import requests

_THIS = Path(__file__).resolve()
_REPO = _THIS.parent.parent
_CORE = _REPO / "packages" / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from ky_core.rag.chunker import chunk_document  # noqa: E402
from ky_core.rag.models import Chunk  # noqa: E402


logger = logging.getLogger("build_rag_bok")

DEFAULT_SOURCE = Path(r"C:/Users/USER/Desktop/한국은행보고서")
DEFAULT_OUTPUT = Path.home() / ".ky-platform" / "data" / "rag_bok"
OLLAMA_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "bge-m3"
EMBED_DIM = 1024
MAX_CHARS_PER_CHUNK = 2500  # safety cap; Korean ~1.5k tokens, within BGE-M3 8k limit
CHECKPOINT_EVERY = 5000

SAMPLE_QUERIES = [
    "금리 인상기 물가 안정",
    "가계부채 증가의 거시경제적 영향",
    "중국 부동산 시장 리스크",
    "미국 연준 통화정책 방향",
]


# --------------------------------------------------------------------------- #
# Text cleaning                                                               #
# --------------------------------------------------------------------------- #

_DUP_CHAR_RE = re.compile(r"(.)\1{3,}")  # 4+ same char -> 1 (kills "해해해해해" title stroking)
_BLANK_LINE_RE = re.compile(r"\n{3,}")


def clean_bok_text(text: str) -> str:
    """Strip PDF extraction artifacts from BOK reports.

    Common issues:
    - title text stroking: "해해해해해외외외외외경경경경제..." -> "해외경제..."
    - excessive blank lines
    """
    text = _DUP_CHAR_RE.sub(r"\1", text)
    text = _BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- #
# Metadata                                                                    #
# --------------------------------------------------------------------------- #

_YEAR_RE = re.compile(r"(19|20)\d{2}")
_CATEGORY_HINTS = {
    "해외경제포커스": "해외경제 포커스",
    "해외경제_포커스": "해외경제 포커스",
    "국제경제리뷰": "국제경제리뷰",
    "조사통계월보": "조사통계월보",
    "경제전망": "경제전망보고서",
    "통화신용정책": "통화신용정책보고서",
    "금융안정보고서": "금융안정보고서",
    "금융시스템리뷰": "금융시스템리뷰",
    "지역경제보고서": "지역경제보고서",
    "경제상황": "경제상황 평가",
    "국민계정": "국민계정리뷰",
    "BOK경제리뷰": "BOK 경제리뷰",
    "BOK이슈": "BOK 이슈리뷰",
}


def guess_metadata_from_filename(filename: str) -> Dict[str, Optional[str]]:
    """Best-effort metadata extraction from filename."""
    stem = Path(filename).stem
    meta: Dict[str, Optional[str]] = {
        "report_title": stem.replace("_", " "),
        "category": None,
        "year": None,
    }
    # year
    m = _YEAR_RE.search(stem)
    if m:
        meta["year"] = m.group(0)
    # category hints
    compact = stem.replace(" ", "").replace("_", "")
    for key, label in _CATEGORY_HINTS.items():
        if key in compact:
            meta["category"] = label
            break
    return meta


def load_db_lookup(db_path: Path) -> Dict[str, Dict[str, str]]:
    """Load BOK DB rows keyed by a normalised title/filename stem for fuzzy match."""
    lookup: Dict[str, Dict[str, str]] = {}
    if not db_path.exists():
        logger.warning("DB not found: %s (filename-only metadata will be used)", db_path)
        return lookup
    conn = sqlite3.connect(str(db_path))
    conn.text_factory = bytes
    cur = conn.cursor()
    cur.execute("SELECT category, title, date, department, pdf_filename FROM bok_reports")
    for cat, title, date, dept, pdf in cur.fetchall():
        def _d(b):
            if not isinstance(b, bytes):
                return b or ""
            for enc in ("utf-8", "cp949", "euc-kr"):
                try:
                    return b.decode(enc)
                except Exception:
                    pass
            return ""
        stem = Path(_d(pdf)).stem.replace(" ", "").replace("_", "").lower()
        if not stem:
            continue
        lookup[stem] = {
            "category": _d(cat),
            "title": _d(title),
            "date": _d(date).replace("등록일", "").strip(),
            "department": _d(dept),
        }
    conn.close()
    logger.info("loaded %s DB rows for metadata enrichment", len(lookup))
    return lookup


def enrich_with_db(txt_name: str, base_meta: Dict, db_lookup: Dict) -> Dict:
    """Try to find matching DB row by normalised filename stem."""
    key = Path(txt_name).stem.replace(" ", "").replace("_", "").lower()
    if key in db_lookup:
        row = db_lookup[key]
        base_meta = dict(base_meta)
        if row.get("category"):
            base_meta["category"] = row["category"]
        if row.get("title"):
            base_meta["report_title"] = row["title"]
        if row.get("date"):
            base_meta["date"] = row["date"]
        if row.get("department"):
            base_meta["department"] = row["department"]
    return base_meta


# --------------------------------------------------------------------------- #
# Chunking                                                                    #
# --------------------------------------------------------------------------- #

def _split_oversized(chunks: List[Chunk]) -> List[Chunk]:
    """Re-split any chunk whose text exceeds MAX_CHARS_PER_CHUNK (Korean PDFs often
    produce word-boundary-free text that yields huge 'words'). Splits by char index
    with 400-char overlap, preserving metadata."""
    out: List[Chunk] = []
    for c in chunks:
        if len(c.text) <= MAX_CHARS_PER_CHUNK:
            out.append(c)
            continue
        # Split into overlapping windows
        step = MAX_CHARS_PER_CHUNK - 400
        sub_idx = 0
        for start in range(0, len(c.text), step):
            sub_text = c.text[start : start + MAX_CHARS_PER_CHUNK]
            if len(sub_text) < 200 and sub_idx > 0:
                break
            out.append(Chunk(
                chunk_id=f"{c.chunk_id}.s{sub_idx:02d}",
                source_file=c.source_file,
                estimated_work=c.estimated_work,
                chunk_index=c.chunk_index * 100 + sub_idx,
                text=sub_text,
                word_count=len(sub_text.split()),
                page_start=c.page_start,
                page_end=c.page_end,
                estimated_author=c.estimated_author,
                source_path=c.source_path,
            ))
            sub_idx += 1
    return out


def load_and_chunk(
    txt_path: Path,
    target_words: int,
    overlap_words: int,
) -> List[Chunk]:
    try:
        raw = txt_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = txt_path.read_text(encoding="cp949", errors="ignore")
    text = clean_bok_text(raw)
    if not text or len(text) < 200:
        return []
    pages = [(None, text)]
    chunks = chunk_document(
        txt_path,
        pages,
        target_words=target_words,
        overlap_words=overlap_words,
    )
    return _split_oversized(chunks)


# --------------------------------------------------------------------------- #
# Embedding                                                                   #
# --------------------------------------------------------------------------- #

def _truncate(t: str) -> str:
    return t[:MAX_CHARS_PER_CHUNK] if len(t) > MAX_CHARS_PER_CHUNK else t


def ollama_embed_raw(texts: List[str], model: str = EMBED_MODEL, timeout: int = 300) -> np.ndarray:
    # BGE-M3 supports 8192 tokens; Ollama defaults to 4096, so we force the context up.
    resp = requests.post(
        OLLAMA_URL,
        json={"model": model, "input": texts, "options": {"num_ctx": 8192}},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    embs = data.get("embeddings")
    if not embs or len(embs) != len(texts):
        raise RuntimeError(f"embedding shape: got {len(embs) if embs else 0} for {len(texts)}")
    return np.asarray(embs, dtype=np.float32)


def ollama_embed(texts: List[str], model: str = EMBED_MODEL) -> np.ndarray:
    """Embed with automatic batch-halving on HTTP errors and defensive truncation."""
    clean = [_truncate(t) if t else " " for t in texts]
    try:
        return ollama_embed_raw(clean, model=model)
    except (requests.HTTPError, requests.Timeout, RuntimeError) as exc:
        # On failure, halve the batch and retry recursively; eventually isolates bad items.
        if len(clean) == 1:
            logger.warning("single-item embed failed (%d chars): %s -- zero vector", len(clean[0]), exc)
            return np.zeros((1, EMBED_DIM), dtype=np.float32)
        mid = len(clean) // 2
        logger.warning("batch of %d failed (%s), splitting", len(clean), exc)
        left = ollama_embed(clean[:mid], model)
        right = ollama_embed(clean[mid:], model)
        return np.vstack([left, right])


def embed_batched(
    texts: List[str],
    batch_size: int = 128,
    log_every: int = 10,
    checkpoint_path: Optional[Path] = None,
    resume_from: int = 0,
) -> np.ndarray:
    n = len(texts)
    out = np.zeros((n, EMBED_DIM), dtype=np.float32)
    if resume_from > 0 and checkpoint_path and checkpoint_path.exists():
        prev = np.load(checkpoint_path)
        out[:min(len(prev), n)] = prev[:min(len(prev), n)]
        print(f"[embed] resumed from {resume_from:,} (checkpoint {checkpoint_path.name})")
    t0 = time.time()
    last = t0
    for i in range(resume_from, n, batch_size):
        batch = texts[i : i + batch_size]
        out[i : i + len(batch)] = ollama_embed(batch)
        now = time.time()
        done = i + len(batch)
        step_done = done - resume_from
        # checkpoint
        if checkpoint_path and step_done and step_done % CHECKPOINT_EVERY < batch_size:
            np.save(checkpoint_path, out[:done])
        if (i // batch_size) % log_every == 0 or done >= n:
            rate = step_done / (now - t0) if now > t0 else 0
            eta = (n - done) / rate if rate > 0 else 0
            print(
                f"[embed] {done:,}/{n:,} "
                f"({rate:.1f}/s, eta {eta/60:.1f}min, step {now - last:.1f}s)",
                flush=True,
            )
            last = now
    return out


# --------------------------------------------------------------------------- #
# Index I/O                                                                   #
# --------------------------------------------------------------------------- #

def write_artifacts(
    chunks: List[Chunk],
    chunk_meta_extras: List[Dict],
    vectors: np.ndarray,
    index_dir: Path,
    source_path: Path,
    build_seconds: float,
    files_total: int,
    files_failed: List[str],
) -> Dict:
    index_dir.mkdir(parents=True, exist_ok=True)
    # vectors
    vec_path = index_dir / "vectors.npy"
    np.save(vec_path, vectors)
    # chunks.jsonl
    chunks_path = index_dir / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as fh:
        for c, extra in zip(chunks, chunk_meta_extras):
            rec = c.to_record()
            rec.update(extra)
            fh.write(json.dumps(rec, ensure_ascii=False))
            fh.write("\n")
    # meta
    meta = {
        "version": 1,
        "source_label": "bok_reports",
        "source_path": str(source_path),
        "embedder": {"model": EMBED_MODEL, "dim": EMBED_DIM, "backend": "ollama"},
        "build_seconds": round(build_seconds, 1),
        "files_total": files_total,
        "files_indexed": files_total - len(files_failed),
        "files_failed_count": len(files_failed),
        "chunks": len(chunks),
        "vectors_shape": list(vectors.shape),
        "vectors_bytes": vec_path.stat().st_size,
        "chunks_bytes": chunks_path.stat().st_size,
    }
    (index_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return meta


def load_index(index_dir: Path):
    vectors = np.load(index_dir / "vectors.npy")
    chunks: List[Dict] = []
    with (index_dir / "chunks.jsonl").open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return vectors, chunks


def search(query: str, vectors: np.ndarray, chunks: List[Dict], top_k: int = 5):
    q_vec = ollama_embed([query])[0]
    q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
    v_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8)
    scores = v_norm @ q_norm
    top_idx = np.argsort(-scores)[:top_k]
    return [(float(scores[i]), chunks[i]) for i in top_idx]


# --------------------------------------------------------------------------- #
# Commands                                                                    #
# --------------------------------------------------------------------------- #

def run_build(args: argparse.Namespace) -> int:
    source_root = Path(args.source).expanduser().resolve()
    text_dir = source_root / "extracted_text"
    db_path = source_root / "bok_reports.db"
    out_dir = Path(args.output).expanduser().resolve()

    print(f"[build] source  = {source_root}")
    print(f"[build] texts   = {text_dir}")
    print(f"[build] output  = {out_dir}")
    print(f"[build] embedder= {EMBED_MODEL} via Ollama")

    if not text_dir.is_dir():
        print(f"[build] ERROR: {text_dir} not found")
        return 2

    # Probe Ollama
    try:
        probe = ollama_embed(["probe"])
        assert probe.shape == (1, EMBED_DIM), f"dim mismatch: {probe.shape}"
        print(f"[build] Ollama OK (dim={EMBED_DIM})")
    except Exception as exc:
        print(f"[build] ERROR: Ollama/{EMBED_MODEL} not reachable: {exc}")
        return 3

    # Discover files
    txt_files = sorted(text_dir.glob("*.txt"))
    if args.limit:
        txt_files = txt_files[: args.limit]
    print(f"[build] {len(txt_files)} txt files queued")

    # DB lookup (optional)
    db_lookup = load_db_lookup(db_path)

    # Chunk all files
    t0 = time.time()
    all_chunks: List[Chunk] = []
    all_extras: List[Dict] = []
    failed: List[str] = []
    empty_count = 0

    for i, path in enumerate(txt_files, 1):
        try:
            chunks = load_and_chunk(path, args.target_words, args.overlap_words)
        except Exception as exc:
            logger.warning("chunk failed: %s - %s", path.name, exc)
            failed.append(path.name)
            continue
        if not chunks:
            empty_count += 1
            continue
        base_meta = guess_metadata_from_filename(path.name)
        meta = enrich_with_db(path.name, base_meta, db_lookup)
        for c in chunks:
            all_chunks.append(c)
            all_extras.append({
                "source_type": "bok_report",
                "report_title": meta.get("report_title"),
                "category": meta.get("category"),
                "year": meta.get("year"),
                "date": meta.get("date"),
                "department": meta.get("department"),
            })
        if i % 200 == 0 or i == len(txt_files):
            elapsed = time.time() - t0
            print(
                f"[chunk] {i}/{len(txt_files)} files, "
                f"{len(all_chunks):,} chunks, {elapsed:.0f}s"
            )

    print(
        f"[chunk] done: {len(txt_files)} files, "
        f"{len(all_chunks):,} chunks ({len(failed)} failed, {empty_count} empty) "
        f"in {time.time() - t0:.0f}s"
    )
    if not all_chunks:
        print("[build] no chunks produced")
        return 4

    # Embed with checkpointing
    print(f"[embed] start: {len(all_chunks):,} chunks, batch_size={args.batch_size}", flush=True)
    t_embed = time.time()
    texts = [c.text for c in all_chunks]
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = out_dir / "vectors_checkpoint.npy"
    resume_from = 0
    if args.resume and checkpoint.exists():
        prev = np.load(checkpoint)
        resume_from = len(prev)
        print(f"[embed] checkpoint found: resuming from {resume_from:,}", flush=True)
    vectors = embed_batched(
        texts,
        batch_size=args.batch_size,
        checkpoint_path=checkpoint,
        resume_from=resume_from,
    )
    print(f"[embed] done in {time.time() - t_embed:.0f}s ({len(texts) / (time.time() - t_embed + 1e-6):.1f} chunks/s)")
    # clean checkpoint on success
    if checkpoint.exists():
        checkpoint.unlink()

    # Persist
    meta = write_artifacts(
        all_chunks,
        all_extras,
        vectors,
        index_dir=out_dir,
        source_path=source_root,
        build_seconds=time.time() - t0,
        files_total=len(txt_files),
        files_failed=failed,
    )
    print(f"[build] wrote {meta['chunks']:,} chunks, {meta['vectors_bytes']/1e6:.1f}MB vectors")
    print(f"[build] total {meta['build_seconds']:.0f}s")

    # Validation
    print("\n[validate] sample queries")
    vectors, chunks_list = load_index(out_dir)
    for q in SAMPLE_QUERIES:
        print(f"  query: {q}")
        try:
            results = search(q, vectors, chunks_list, top_k=3)
            for rank, (score, rec) in enumerate(results, 1):
                title = (rec.get("report_title") or rec.get("source_file") or "?")[:60]
                year = rec.get("year") or "?"
                print(f"    {rank}. {score:.3f} [{year}] {title}")
        except Exception as exc:
            print(f"    ERROR: {exc}")

    return 0


def run_healthcheck(out_dir: Path) -> int:
    if not out_dir.is_dir():
        print(f"[hc] {out_dir} does not exist -- run build first")
        return 1
    meta_path = out_dir / "meta.json"
    if not meta_path.exists():
        print(f"[hc] meta.json not found in {out_dir}")
        return 1
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print(f"[hc] chunks={meta['chunks']:,}, files={meta['files_indexed']}/{meta['files_total']}, dim={meta['embedder']['dim']}")
    vectors, chunks = load_index(out_dir)
    print(f"[hc] loaded vectors {vectors.shape}, {len(chunks):,} chunk records")
    q = "한국은행 기준금리 결정"
    results = search(q, vectors, chunks, top_k=3)
    print(f"[hc] sample query: {q}")
    for rank, (score, rec) in enumerate(results, 1):
        print(f"    {rank}. {score:.3f} {(rec.get('report_title') or rec.get('source_file') or '?')[:60]}")
    return 0


# --------------------------------------------------------------------------- #

def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=str(DEFAULT_SOURCE))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--target-words", type=int, default=500)
    p.add_argument("--overlap-words", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--resume", action="store_true", help="resume embedding from checkpoint if present")
    p.add_argument("--healthcheck", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    out = Path(args.output).expanduser().resolve()
    if args.healthcheck:
        return run_healthcheck(out)
    return run_build(args)


if __name__ == "__main__":
    raise SystemExit(main())
