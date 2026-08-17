"""Small, conservative spend gate for a public Hugging Face Space."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
from datetime import datetime, timezone


class AccessDenied(RuntimeError):
    pass


class SpendLimitReached(RuntimeError):
    pass


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be at least 1")
    return value


class SpendGate:
    """UTC-day and per-session accounting for the public model budget."""

    def __init__(self, db_path: str | None = None) -> None:
        self.daily_cap = _positive_int("ZYNTALIC_DAILY_RUN_CAP", 10)
        self.session_cap = _positive_int("ZYNTALIC_SESSION_RUN_CAP", 2)
        self.db_path = db_path or os.getenv("ZYNTALIC_LIMIT_DB", "/tmp/zyntalic-spend.sqlite3")
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=10, isolation_level=None)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS runs (day TEXT NOT NULL, session TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(day, session))"
            )

    @staticmethod
    def _session_key(session_id: str) -> str:
        return hashlib.sha256(session_id.encode("utf-8")).hexdigest()

    def consume(self, session_id: str) -> dict[str, int]:
        if not session_id:
            raise AccessDenied("A browser session is required.")
        day = datetime.now(timezone.utc).date().isoformat()
        session = self._session_key(session_id)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            total = connection.execute(
                "SELECT COALESCE(SUM(count), 0) FROM runs WHERE day = ?", (day,)
            ).fetchone()[0]
            row = connection.execute(
                "SELECT count FROM runs WHERE day = ? AND session = ?", (day, session)
            ).fetchone()
            session_count = row[0] if row else 0
            if total >= self.daily_cap:
                connection.execute("ROLLBACK")
                raise SpendLimitReached("The UTC daily experiment cap has been reached.")
            if session_count >= self.session_cap:
                connection.execute("ROLLBACK")
                raise SpendLimitReached("This session has reached its experiment cap.")
            connection.execute(
                "INSERT INTO runs(day, session, count) VALUES(?, ?, 1) ON CONFLICT(day, session) DO UPDATE SET count = count + 1",
                (day, session),
            )
            connection.execute("COMMIT")
        return {
            "daily_remaining": self.daily_cap - total - 1,
            "session_remaining": self.session_cap - session_count - 1,
        }
