"""Build dense vector RAG for broker/research reports on local GPU.

Input:
    ~/.ky-platform/data/rag_broker/chunks.jsonl

Output:
    ~/.ky-platform/data/rag_broker_vec/{vectors.npy,chunks.jsonl,meta.json}

This complements the TF-IDF broker index. TF-IDF stays useful for exact ticker,
broker, and phrase matches; this dense index is for semantic Korean/English
research queries.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

_THIS = Path(__file__).resolve()
_REPO = _THIS.parent.parent
_CORE_PKG = _REPO / "packages" / "core"
if str(_CORE_PKG) not in sys.path:
    sys.path.insert(0, str(_CORE_PKG))

logger = logging.getLogger("build_rag_broker_vec")

DEFAULT_SOURCE_INDEX = Path.home() / ".ky-platform" / "data" / "rag_broker"
DEFAULT_OUTPUT = Path.home() / ".ky-platform" / "data" / "rag_broker_vec"
DEFAULT_MODEL = "BAAI/bge-m3"


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_chunks(path: Path, limit: int = 0) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
            if limit and len(chunks) >= limit:
                break
    return chunks


def _text_for_embedding(rec: Dict[str, Any], *, max_chars: int) -> str:
    title = rec.get("estimated_work") or rec.get("source_file") or ""
    broker = rec.get("broker") or ""
    category = rec.get("report_category") or ""
    published = rec.get("published") or ""
    text = rec.get("text") or ""
    prefix = " | ".join(part for part in (str(title), str(broker), str(category), str(published)) if part)
    body = str(text)
    if max_chars and len(body) > max_chars:
        body = body[:max_chars]
    if prefix:
        return f"{prefix}\n{body}"
    return body


def _load_sentence_model(model_name: str, device: str):
    try:
        import torch
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "sentence_transformers and torch are required for GPU broker vector RAG"
        ) from exc

    if device.startswith("cuda") and torch.cuda.is_available():
        try:
            torch.set_float32_matmul_precision("high")
            torch.backends.cuda.matmul.allow_tf32 = True
        except Exception:
            pass
    model = SentenceTransformer(model_name, device=device)
    if device.startswith("cuda") and torch.cuda.is_available():
        try:
            model.half()
        except Exception as exc:  # noqa: BLE001
            logger.info("model.half() skipped: %s", exc)
    return model


def run_build(args: argparse.Namespace) -> int:
    source_index = Path(args.source_index).expanduser().resolve()
    source_chunks = source_index / "chunks.jsonl"
    output_dir = Path(args.output).expanduser().resolve()
    if not source_chunks.is_file():
        print(f"[broker-vec] ERROR: chunks not found: {source_chunks}")
        return 2

    chunks = _load_chunks(source_chunks, limit=args.limit)
    if not chunks:
        print("[broker-vec] ERROR: no chunks loaded")
        return 3

    texts = [_text_for_embedding(rec, max_chars=args.max_chars) for rec in chunks]
    print(f"[broker-vec] chunks={len(chunks):,}")
    print(f"[broker-vec] model={args.model} device={args.device} batch={args.batch_size}")

    t0 = time.time()
    model = _load_sentence_model(args.model, args.device)
    if args.max_seq_length:
        model.max_seq_length = args.max_seq_length
        print(f"[broker-vec] max_seq_length={model.max_seq_length} max_chars={args.max_chars}")
    vectors = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
        device=args.device,
    )
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
        raise RuntimeError(f"bad vector shape: {vectors.shape}")

    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "vectors.npy", vectors)
    with (output_dir / "chunks.jsonl").open("w", encoding="utf-8") as fh:
        for rec in chunks:
            fh.write(json.dumps(rec, ensure_ascii=False))
            fh.write("\n")

    source_meta_path = source_index / "meta.json"
    source_meta = {}
    if source_meta_path.is_file():
        source_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
        shutil.copyfile(source_meta_path, output_dir / "source_meta.json")

    meta = {
        "version": 1,
        "source_label": "broker_reports_dense",
        "source_index": str(source_index),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "build_seconds": round(time.time() - t0, 1),
        "chunks": len(chunks),
        "vectors_shape": list(vectors.shape),
        "vectors_bytes": int((output_dir / "vectors.npy").stat().st_size),
        "chunks_bytes": int((output_dir / "chunks.jsonl").stat().st_size),
        "model": args.model,
        "device": args.device,
        "batch_size": args.batch_size,
        "max_seq_length": args.max_seq_length,
        "max_chars": args.max_chars,
        "normalized": True,
        "source_broker_chunks": source_meta.get("chunks"),
        "source_drive_folder_url": source_meta.get("drive_folder_url"),
    }
    (output_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"[broker-vec] done shape={vectors.shape} output={output_dir} "
        f"seconds={meta['build_seconds']}"
    )
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build GPU dense vector index for broker RAG")
    p.add_argument("--source-index", default=str(DEFAULT_SOURCE_INDEX))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--device", default="cuda")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument(
        "--max-seq-length",
        type=int,
        default=512,
        help="cap transformer tokens; 512 is enough for report retrieval and avoids CPU/GPU stalls",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=1800,
        help="cap body characters before tokenization; metadata/title is always preserved",
    )
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)
    return run_build(args)


if __name__ == "__main__":
    raise SystemExit(main())
