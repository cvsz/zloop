from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Protocol
import json
import sqlite3
import time


class DurableStateStore(Protocol):
    def save_record(self, loop_id: str, record: Dict[str, Any]) -> None: ...
    def load_record(self, loop_id: str) -> Dict[str, Any] | None: ...
    def put_idempotency(self, key: str, status: str, result: Dict[str, Any] | None = None) -> None: ...
    def get_idempotency(self, key: str) -> Dict[str, Any] | None: ...


class SQLiteStateStore:
    """Durable local reference backend with atomic checkpoints and idempotency records."""

    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS loop_state (
                    loop_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    record_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS idempotency (
                    key TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    updated_at REAL NOT NULL
                );
                """
            )

    def save_record(self, loop_id: str, record: Dict[str, Any]) -> None:
        payload = json.dumps(record, ensure_ascii=False, sort_keys=True)
        now = time.time()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT version FROM loop_state WHERE loop_id = ?", (loop_id,)
            ).fetchone()
            version = 1 if row is None else int(row["version"]) + 1
            conn.execute(
                """
                INSERT INTO loop_state(loop_id, version, record_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(loop_id) DO UPDATE SET
                    version = excluded.version,
                    record_json = excluded.record_json,
                    updated_at = excluded.updated_at
                """,
                (loop_id, version, payload, now),
            )
            conn.execute("COMMIT")

    def load_record(self, loop_id: str) -> Dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record_json FROM loop_state WHERE loop_id = ?", (loop_id,)
            ).fetchone()
        if row is None:
            return None
        data = json.loads(row["record_json"])
        if not isinstance(data, dict) or data.get("loop_id") != loop_id:
            raise ValueError("corrupt loop checkpoint")
        return data

    def put_idempotency(self, key: str, status: str, result: Dict[str, Any] | None = None) -> None:
        if status not in {"NOT_STARTED", "IN_PROGRESS", "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_FINAL"}:
            raise ValueError(f"invalid idempotency status: {status}")
        result_json = None if result is None else json.dumps(result, ensure_ascii=False, sort_keys=True)
        now = time.time()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT status FROM idempotency WHERE key = ?", (key,)).fetchone()
            if existing is not None and existing["status"] == "SUCCEEDED" and status != "SUCCEEDED":
                conn.execute("ROLLBACK")
                raise ValueError("cannot move a succeeded idempotency record backwards")
            conn.execute(
                """
                INSERT INTO idempotency(key, status, result_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    status = excluded.status,
                    result_json = excluded.result_json,
                    updated_at = excluded.updated_at
                """,
                (key, status, result_json, now),
            )
            conn.execute("COMMIT")

    def get_idempotency(self, key: str) -> Dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status, result_json, updated_at FROM idempotency WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        return {
            "key": key,
            "status": row["status"],
            "result": None if row["result_json"] is None else json.loads(row["result_json"]),
            "updated_at": row["updated_at"],
        }
