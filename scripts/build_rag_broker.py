"""Build the broker-report RAG index.

Primary source policy:
    Google Drive report folder -> local extracted/exported files -> TF-IDF index

The app does not query Drive at request time. Mirror or export the Drive folder
contents locally first, then point this script at the local folder. It supports:
    - PDF/TXT files: full text extraction and chunking.
    - CSV metadata exports: catalogue chunks from rows containing title/link.
    - CSV manifests with pdf_direct_url: optional PDF download/cache/extract.
    - page-text CSV exports: chunks from page text columns when present.

Output:
    ~/.ky-platform/data/rag_broker/{index.pkl,chunks.jsonl,meta.json}
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

_THIS = Path(__file__).resolve()
_REPO = _THIS.parent.parent
_CORE_PKG = _REPO / "packages" / "core"
if str(_CORE_PKG) not in sys.path:
    sys.path.insert(0, str(_CORE_PKG))

from ky_core.rag.chunker import chunk_document  # noqa: E402
from ky_core.rag.extractor import extract_text  # noqa: E402
from ky_core.rag.index import build_index  # noqa: E402
from ky_core.rag.models import Chunk  # noqa: E402

logger = logging.getLogger("build_rag_broker")

DEFAULT_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1EsI54xFmHaL_wn5ebA-V3q6iIDbMKy6R"
DEFAULT_OUTPUT = Path.home() / ".ky-platform" / "data" / "rag_broker"
SUPPORTED_DOCS = {".pdf", ".txt"}
SUPPORTED_TABLES = {".csv", ".json", ".jsonl"}


@dataclass(slots=True)
class BrokerChunk(Chunk):
    report_category: str = ""
    report_subcategory: str = ""
    broker: str = ""
    symbol: str = ""
    published: str = ""
    source_url: str = ""
    pdf_url: str = ""
    drive_url: str = ""
    source_type: str = "broker_report"

    def to_record(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("source_path", None)
        return d


@dataclass
class BuildStats:
    files_seen: int = 0
    files_indexed: int = 0
    files_failed: List[str] = field(default_factory=list)
    catalogue_rows: int = 0
    page_text_rows: int = 0
    pdf_rows_seen: int = 0
    pdfs_downloaded: int = 0
    pdfs_reused: int = 0
    pdfs_indexed: int = 0
    pdfs_failed: int = 0


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _hash_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def _truthy(value: Any) -> bool:
    return _clean(value).lower() in {"1", "true", "yes", "y", "pdf"}


def _first(row: Dict[str, Any], *names: str) -> str:
    lower = {str(k).lower().replace("\ufeff", ""): v for k, v in row.items()}
    for name in names:
        key = name.lower()
        if key in lower and _clean(lower[key]):
            return _clean(lower[key])
    return ""


def _category_from_path(path: Path, root: Path) -> tuple[str, str]:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    joined = "/".join(parts).lower()
    category = ""
    if "stock" in joined or "company" in joined:
        category = "stock"
    elif "industry" in joined:
        category = "industry"
    elif "bond" in joined:
        category = "bond"
    elif "economic" in joined:
        category = "economic"
    elif "market" in joined:
        category = "market"
    elif "investment" in joined or "strategy" in joined:
        category = "investment"
    subcategory = parts[-2] if len(parts) > 1 else ""
    return category, subcategory


def _guess_title_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip()


def _safe_filename(value: str, *, max_len: int = 120) -> str:
    keep: List[str] = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_", ".", " "):
            keep.append(ch)
        else:
            keep.append("_")
    name = "".join(keep).strip(" ._")
    name = "_".join(name.split())
    return (name[:max_len].strip("._") or "report")


def _pdf_cache_path(
    *,
    cache_dir: Path,
    category: str,
    broker: str,
    published: str,
    title: str,
    pdf_url: str,
) -> Path:
    digest = _hash_id(pdf_url)
    stem = _safe_filename("_".join(part for part in (published, broker, title, digest) if part))
    return cache_dir / (category or "uncategorized") / f"{stem}.pdf"


def _download_pdf(url: str, dest: Path, *, timeout: float) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (KY-Platform Broker RAG)",
            "Accept": "application/pdf,*/*",
        },
    )
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, tmp.open("wb") as fh:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "pdf" not in ctype and not url.lower().endswith(".pdf"):
                logger.debug("download content-type is not pdf for %s: %s", url, ctype)
            while True:
                block = resp.read(1024 * 256)
                if not block:
                    break
                fh.write(block)
        if tmp.stat().st_size <= 0:
            tmp.unlink(missing_ok=True)
            raise ValueError("empty pdf download")
        tmp.replace(dest)
        return True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"pdf download failed: {exc}") from exc


def _make_chunk_from_text(
    *,
    text: str,
    source_file: str,
    chunk_index: int,
    title: str,
    category: str,
    subcategory: str = "",
    broker: str = "",
    symbol: str = "",
    published: str = "",
    source_url: str = "",
    pdf_url: str = "",
    drive_url: str = "",
    page_start: Optional[int] = None,
    page_end: Optional[int] = None,
) -> BrokerChunk:
    chunk_id = f"{source_file}::{chunk_index:05d}"
    return BrokerChunk(
        chunk_id=chunk_id,
        source_file=source_file,
        estimated_work=title or source_file,
        chunk_index=chunk_index,
        text=text,
        word_count=max(1, len(text.split())),
        page_start=page_start,
        page_end=page_end,
        report_category=category,
        report_subcategory=subcategory,
        broker=broker,
        symbol=symbol,
        published=published,
        source_url=source_url,
        pdf_url=pdf_url,
        drive_url=drive_url,
    )


def _wrap_chunks(
    chunks: Iterable[Chunk],
    *,
    category: str,
    subcategory: str,
    broker: str = "",
    symbol: str = "",
    published: str = "",
    source_url: str = "",
    pdf_url: str = "",
    drive_url: str = "",
) -> List[BrokerChunk]:
    out: List[BrokerChunk] = []
    for c in chunks:
        out.append(
            BrokerChunk(
                chunk_id=c.chunk_id,
                source_file=c.source_file,
                estimated_work=c.estimated_work,
                chunk_index=c.chunk_index,
                text=c.text,
                word_count=c.word_count,
                page_start=c.page_start,
                page_end=c.page_end,
                estimated_author=c.estimated_author,
                source_path=c.source_path,
                report_category=category,
                report_subcategory=subcategory,
                broker=broker,
                symbol=symbol,
                published=published,
                source_url=source_url,
                pdf_url=pdf_url,
                drive_url=drive_url,
            )
        )
    return out


def _iter_files(root: Path) -> List[Path]:
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in (SUPPORTED_DOCS | SUPPORTED_TABLES)
    ]
    files.sort(key=lambda p: str(p).lower())
    return files


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc, newline="") as fh:
                return list(csv.DictReader(fh))
        except UnicodeDecodeError:
            continue
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def _chunks_from_csv(
    path: Path,
    root: Path,
    stats: BuildStats,
    *,
    download_pdfs: bool,
    pdf_cache_dir: Path,
    max_pdf_downloads: int,
    request_timeout: float,
    target_words: int,
    overlap_words: int,
) -> List[BrokerChunk]:
    rows = _read_csv_rows(path)
    out: List[BrokerChunk] = []
    base_category, base_subcategory = _category_from_path(path, root)
    rel = str(path.relative_to(root)).replace("\\", "/")

    for row_idx, row in enumerate(rows):
        text = _first(row, "page_text", "page_texts", "페이지텍스트", "text", "content", "본문")
        title = _first(row, "title", "제목", "report_title", "파일명", "filename") or _guess_title_from_path(path)
        category = _first(row, "research_type", "category", "카테고리") or base_category
        subcategory = _first(row, "industry", "업종", "sector", "subcategory") or base_subcategory
        broker = _first(row, "company", "broker", "증권사")
        symbol = _first(row, "symbol", "ticker", "종목코드")
        published = _first(row, "date", "published", "작성일", "발행일")
        source_url = _first(row, "link", "source_url", "url")
        pdf_url = _first(row, "pdf_direct_url", "pdf_url")
        drive_url = _first(row, "pdf_drive_link", "drive_url")
        has_pdf = _truthy(_first(row, "has_pdf")) or bool(pdf_url)
        if has_pdf:
            stats.pdf_rows_seen += 1

        if text:
            source_file = f"{rel}#row{row_idx}"
            out.append(
                _make_chunk_from_text(
                    text=text,
                    source_file=source_file,
                    chunk_index=0,
                    title=title,
                    category=category,
                    subcategory=subcategory,
                    broker=broker,
                    symbol=symbol,
                    published=published,
                    source_url=source_url,
                    pdf_url=pdf_url,
                    drive_url=drive_url,
                    page_start=int(_first(row, "page_number", "페이지번호") or 0) or None,
                )
            )
            stats.page_text_rows += 1
            continue

        if download_pdfs and pdf_url:
            if max_pdf_downloads and stats.pdfs_downloaded >= max_pdf_downloads:
                pass
            else:
                pdf_path = _pdf_cache_path(
                    cache_dir=pdf_cache_dir,
                    category=category,
                    broker=broker,
                    published=published,
                    title=title,
                    pdf_url=pdf_url,
                )
                try:
                    downloaded = _download_pdf(pdf_url, pdf_path, timeout=request_timeout)
                    if downloaded:
                        stats.pdfs_downloaded += 1
                    else:
                        stats.pdfs_reused += 1
                    pages = extract_text(pdf_path)
                    pdf_chunks = _wrap_chunks(
                        chunk_document(
                            pdf_path,
                            pages,
                            target_words=target_words,
                            overlap_words=overlap_words,
                            knowledge_root=pdf_cache_dir,
                        ),
                        category=category,
                        subcategory=subcategory,
                        broker=broker,
                        symbol=symbol,
                        published=published,
                        source_url=source_url,
                        pdf_url=pdf_url,
                        drive_url=drive_url,
                    )
                    if pdf_chunks:
                        out.extend(pdf_chunks)
                        stats.pdfs_indexed += 1
                        continue
                except Exception as exc:  # noqa: BLE001
                    stats.pdfs_failed += 1
                    logger.warning("pdf row failed %s: %s", pdf_url, exc)

        if title or source_url or pdf_url:
            catalogue_text = " | ".join(
                part
                for part in (
                    f"제목: {title}" if title else "",
                    f"분류: {category}/{subcategory}" if category or subcategory else "",
                    f"증권사: {broker}" if broker else "",
                    f"종목: {symbol}" if symbol else "",
                    f"발행일: {published}" if published else "",
                    f"원문: {source_url}" if source_url else "",
                )
                if part
            )
            source_file = f"{rel}#row{row_idx}"
            out.append(
                _make_chunk_from_text(
                    text=catalogue_text,
                    source_file=source_file,
                    chunk_index=0,
                    title=title,
                    category=category,
                    subcategory=subcategory,
                    broker=broker,
                    symbol=symbol,
                    published=published,
                    source_url=source_url,
                    pdf_url=pdf_url,
                    drive_url=drive_url,
                )
            )
            stats.catalogue_rows += 1
    return out


def _flatten_json_strings(obj: Any, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten_json_strings(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _flatten_json_strings(v, f"{prefix}.{i}" if prefix else str(i))
    elif isinstance(obj, str) and len(obj.strip()) >= 80:
        yield prefix, obj.strip()


def _chunks_from_json(path: Path, root: Path) -> List[BrokerChunk]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: List[Any] = []
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        rows = [json.loads(text)]

    category, subcategory = _category_from_path(path, root)
    rel = str(path.relative_to(root)).replace("\\", "/")
    out: List[BrokerChunk] = []
    for row_no, obj in enumerate(rows):
        for idx, (key, value) in enumerate(_flatten_json_strings(obj)):
            title = key or _guess_title_from_path(path)
            source_file = f"{rel}#{row_no}.{_hash_id(key + value)}"
            out.append(
                _make_chunk_from_text(
                    text=value,
                    source_file=source_file,
                    chunk_index=idx,
                    title=title,
                    category=category,
                    subcategory=subcategory,
                )
            )
    return out


def _chunks_from_document(
    path: Path,
    root: Path,
    *,
    target_words: int,
    overlap_words: int,
) -> List[BrokerChunk]:
    pages = extract_text(path)
    if not pages:
        return []
    category, subcategory = _category_from_path(path, root)
    return _wrap_chunks(
        chunk_document(
            path,
            pages,
            target_words=target_words,
            overlap_words=overlap_words,
            knowledge_root=root,
        ),
        category=category,
        subcategory=subcategory,
    )


def run_build(args: argparse.Namespace) -> int:
    source_path = Path(args.source_path).expanduser().resolve()
    index_dir = Path(args.output).expanduser().resolve()
    if not source_path.is_dir():
        print(f"[broker-rag] ERROR: source path not found: {source_path}")
        print("[broker-rag] Mirror/export the Drive folder locally first.")
        return 2

    t0 = time.time()
    stats = BuildStats()
    files = _iter_files(source_path)
    if args.limit:
        files = files[: args.limit]
    stats.files_seen = len(files)
    print(f"[broker-rag] source={source_path}")
    print(f"[broker-rag] drive_primary={args.drive_folder_url}")
    print(f"[broker-rag] files={len(files)} output={index_dir}")

    chunks: List[BrokerChunk] = []
    for i, path in enumerate(files, 1):
        rel = str(path.relative_to(source_path)).replace("\\", "/")
        try:
            suffix = path.suffix.lower()
            if suffix == ".csv":
                new_chunks = _chunks_from_csv(
                    path,
                    source_path,
                    stats,
                    download_pdfs=args.download_pdfs,
                    pdf_cache_dir=Path(args.pdf_cache_dir).expanduser().resolve(),
                    max_pdf_downloads=args.max_pdf_downloads,
                    request_timeout=args.request_timeout,
                    target_words=args.target_words,
                    overlap_words=args.overlap_words,
                )
            elif suffix in {".json", ".jsonl"}:
                new_chunks = _chunks_from_json(path, source_path)
            elif suffix in SUPPORTED_DOCS:
                new_chunks = _chunks_from_document(
                    path,
                    source_path,
                    target_words=args.target_words,
                    overlap_words=args.overlap_words,
                )
            else:
                new_chunks = []
            if new_chunks:
                chunks.extend(new_chunks)
                stats.files_indexed += 1
            if i % 50 == 0 or i == len(files):
                print(f"[broker-rag] {i}/{len(files)} files, chunks={len(chunks):,}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed %s: %s", rel, exc)
            stats.files_failed.append(rel)

    if not chunks:
        print("[broker-rag] ERROR: no chunks produced")
        return 3

    meta = build_index(
        chunks,
        index_dir=index_dir,
        source_label="broker_reports",
        source_path=str(source_path),
        files_total=stats.files_seen,
        files_failed=stats.files_failed,
    )
    meta.update(
        {
            "drive_folder_url": args.drive_folder_url,
            "catalogue_rows": stats.catalogue_rows,
            "page_text_rows": stats.page_text_rows,
            "pdf_rows_seen": stats.pdf_rows_seen,
            "pdfs_downloaded": stats.pdfs_downloaded,
            "pdfs_reused": stats.pdfs_reused,
            "pdfs_indexed": stats.pdfs_indexed,
            "pdfs_failed": stats.pdfs_failed,
            "pdf_cache_dir": str(Path(args.pdf_cache_dir).expanduser().resolve()),
            "build_seconds_total": round(time.time() - t0, 1),
        }
    )
    (index_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[broker-rag] done chunks={meta['chunks']:,} files_indexed={stats.files_indexed}/"
        f"{stats.files_seen} failed={len(stats.files_failed)}"
    )
    if args.download_pdfs:
        print(
            f"[broker-rag] pdf rows={stats.pdf_rows_seen:,} downloaded={stats.pdfs_downloaded:,} "
            f"reused={stats.pdfs_reused:,} indexed={stats.pdfs_indexed:,} failed={stats.pdfs_failed:,}"
        )
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build broker-report RAG index")
    p.add_argument("--source-path", required=True, help="local mirror/export of the Drive report folder")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--drive-folder-url", default=DEFAULT_DRIVE_FOLDER_URL)
    p.add_argument("--target-words", type=int, default=500)
    p.add_argument("--overlap-words", type=int, default=100)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument(
        "--download-pdfs",
        action="store_true",
        help="follow pdf_direct_url rows in CSV manifests, cache PDFs, and index extracted text",
    )
    p.add_argument(
        "--pdf-cache-dir",
        default=str(Path.home() / ".ky-platform" / "data" / "broker_pdf_cache"),
    )
    p.add_argument(
        "--max-pdf-downloads",
        type=int,
        default=0,
        help="cap new PDF downloads for smoke tests; 0 means unlimited",
    )
    p.add_argument("--request-timeout", type=float, default=45.0)
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)
    return run_build(args)


if __name__ == "__main__":
    raise SystemExit(main())
