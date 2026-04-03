from __future__ import annotations

import os
from pathlib import Path


_LOADED = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _desktop_quantdb_roots() -> list[Path]:
    repo_root = _repo_root()
    return [
        repo_root.parent / 'QuantDB',
        Path.home() / 'Desktop' / 'QuantDB',
    ]


def _desktop_quantdb_env_candidates() -> list[Path]:
    candidates: list[Path] = []
    for root in _desktop_quantdb_roots():
        candidates.extend([
            root / '.env',
            root / 'mvp_platform' / '.env',
        ])
    return candidates


def _candidate_paths(path: Path | None = None) -> list[Path]:
    if path is not None:
        return [path]

    shared_env = os.getenv('SEPA_ENV_FILE', '').strip()
    shared_path = Path(shared_env) if shared_env else None
    root_env = _repo_root() / '.env'
    cwd_env = Path.cwd() / '.env'
    candidates = [shared_path, *_desktop_quantdb_env_candidates(), root_env, cwd_env]

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate is None:
            continue
        key = str(candidate)
        if key in seen:
            continue
        deduped.append(candidate)
        seen.add(key)
    return deduped


def _parse_env_line(raw: str) -> tuple[str, str] | None:
    line = raw.strip()
    if not line or line.startswith('#'):
        return None
    if line.startswith('export '):
        line = line[7:].strip()
    if '=' not in line:
        return None

    key, value = line.split('=', 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None

    if value and value[0] in {'"', "'"} and value[-1:] == value[0]:
        value = value[1:-1]
    else:
        comment_pos = value.find(' #')
        if comment_pos >= 0:
            value = value[:comment_pos].rstrip()
    return key, value


def load_env_file(path: Path | None = None, *, override: bool = False) -> bool:
    global _LOADED

    if _LOADED and path is None and not override:
        return False

    loaded = False
    for candidate in _candidate_paths(path):
        if not candidate.exists():
            continue
        for raw in candidate.read_text(encoding='utf-8-sig').splitlines():
            parsed = _parse_env_line(raw)
            if not parsed:
                continue
            key, value = parsed
            if not override and key in os.environ and os.environ[key]:
                continue
            os.environ[key] = value
        loaded = True
        break

    _LOADED = True
    return loaded
