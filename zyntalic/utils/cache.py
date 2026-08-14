"""Concurrent, persistent cache for deterministic translations.

The original cache rewrote one growing JSON document for every translated
sentence. SQLite keeps writes proportional to the changed entry, supports
multiple request threads safely, and needs no additional dependency.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from zyntalic.embeddings import embed_text

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / "data" / "cache"
CACHE_PATH = Path(os.getenv("ZYNTALIC_CACHE_PATH", str(CACHE_DIR / "translations.sqlite3")))
LEGACY_CACHE_PATH = CACHE_DIR / "translations.json"
CACHE_VERSION = os.getenv("ZYNTALIC_CACHE_VERSION", "2")

_local = threading.local()
_init_lock = threading.Lock()
_initialized = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_options(options: dict[str, Any] | None = None) -> dict[str, Any]:
    if not options:
        return {}
    normalized: dict[str, Any] = {}
    for key, value in options.items():
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        normalized[key] = value
    return normalized


def _key(
    source: str,
    engine: str,
    mirror_rate: float,
    options: dict[str, Any] | None = None,
    *,
    namespace: str = "translation",
) -> str:
    payload = json.dumps(
        {
            "cache_version": CACHE_VERSION,
            "namespace": namespace,
            "engine": engine,
            "mirror_rate": round(float(mirror_rate), 4),
            "source": (source or "").strip(),
            "options": _normalize_options(options),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.blake2s(payload.encode("utf-8"), digest_size=16).hexdigest()


def _open_connection() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(CACHE_PATH), timeout=5.0)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


def _connection() -> sqlite3.Connection:
    init_cache()
    connection = getattr(_local, "connection", None)
    if connection is None:
        connection = _open_connection()
        _local.connection = connection
    return connection


def _migrate_legacy_json(connection: sqlite3.Connection) -> None:
    """Import an old JSON cache once when a fresh database is created."""
    if not LEGACY_CACHE_PATH.exists():
        return
    existing = connection.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]
    if existing:
        return
    try:
        legacy = json.loads(LEGACY_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(legacy, dict):
        return
    now = _utc_now()
    entries = []
    for value in legacy.values():
        if not isinstance(value, dict) or not value.get("source"):
            continue
        cache_key = _key(
            str(value["source"]),
            str(value.get("engine") or "core"),
            float(value.get("mirror_rate", 0.3)),
            value.get("options") if isinstance(value.get("options"), dict) else None,
            namespace="response",
        )
        payload = {"rows": [value], "created_at": value.get("created_at") or now}
        entries.append(
            (cache_key, json.dumps(payload, ensure_ascii=False, separators=(",", ":")), now)
        )
    if entries:
        connection.executemany(
            "INSERT OR IGNORE INTO cache_entries(cache_key, payload, updated_at) VALUES (?, ?, ?)",
            entries,
        )
        connection.commit()


def init_cache() -> None:
    """Initialize the SQLite cache once per process."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        connection = _open_connection()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
            _migrate_legacy_json(connection)
        finally:
            connection.close()
        _initialized = True


def close_cache() -> None:
    """Close the connection owned by the current worker thread."""
    connection = getattr(_local, "connection", None)
    if connection is not None:
        connection.close()
        delattr(_local, "connection")


def save_cache() -> None:
    """Compatibility hook; SQLite writes are committed atomically per operation."""
    connection = getattr(_local, "connection", None)
    if connection is not None:
        connection.commit()


def _get_payload(cache_key: str) -> dict[str, Any] | None:
    row = (
        _connection()
        .execute("SELECT payload FROM cache_entries WHERE cache_key = ?", (cache_key,))
        .fetchone()
    )
    if row is None:
        return None
    try:
        payload = json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _put_payload(cache_key: str, payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    connection = _connection()
    connection.execute(
        """
        INSERT INTO cache_entries(cache_key, payload, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            payload = excluded.payload,
            updated_at = excluded.updated_at
        """,
        (cache_key, serialized, _utc_now()),
    )
    connection.commit()


def get_cached_translation(
    source: str,
    engine: str,
    mirror_rate: float,
    options: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    payload = _get_payload(_key(source, engine, mirror_rate, options))
    return dict(payload) if payload else None


def put_cached_translation(
    source: str,
    target: str,
    engine: str,
    mirror_rate: float,
    anchors: list | None = None,
    embedding: list[float] | None = None,
    mirror_text: str | None = None,
    sidecar: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Store one translation while preserving the original public cache API."""
    if embedding is None:
        embedding = embed_text(target or "", dim=300)
    entry = {
        "source": source or "",
        "target": target or "",
        "engine": engine,
        "mirror_rate": float(mirror_rate),
        "anchors": anchors or [],
        "embedding": embedding,
        "mirror_text": mirror_text or "",
        "sidecar": sidecar or {},
        "options": _normalize_options(options),
        "created_at": _utc_now(),
    }
    _put_payload(_key(source, engine, mirror_rate, options), entry)
    return dict(entry)


def get_cached_response(
    source: str,
    engine: str,
    mirror_rate: float,
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]] | None:
    """Return all rows for an exact input request, including multi-sentence text."""
    payload = _get_payload(_key(source, engine, mirror_rate, options, namespace="response"))
    rows = payload.get("rows") if payload else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return None
    return [dict(row) for row in rows]


def put_cached_response(
    source: str,
    rows: Sequence[dict[str, Any]],
    engine: str,
    mirror_rate: float,
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Store a complete request result with one constant-time database upsert."""
    stored_rows = [dict(row) for row in rows]
    payload = {"rows": stored_rows, "created_at": _utc_now()}
    _put_payload(_key(source, engine, mirror_rate, options, namespace="response"), payload)
    return stored_rows


def cache_size() -> int:
    return int(_connection().execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0])


def cache_info() -> dict[str, Any]:
    return {
        "backend": "sqlite-wal",
        "entries": cache_size(),
        "version": CACHE_VERSION,
    }
