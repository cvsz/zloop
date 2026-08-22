from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import sqlite3
import time
import uuid


@dataclass(frozen=True)
class Job:
    job_id: str
    payload: dict[str, Any]
    status: str
    attempts: int
    lease_owner: str | None
    lease_until: float | None
    deadline: float | None


class SQLiteJobQueue:
    """Durable local queue with leases, reclaim, retry, cancellation and deadlines."""

    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    available_at REAL NOT NULL,
                    lease_owner TEXT,
                    lease_until REAL,
                    deadline REAL,
                    updated_at REAL NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def enqueue(self, payload: dict[str, Any], *, job_id: str | None = None, deadline: float | None = None) -> str:
        jid = job_id or str(uuid.uuid4())
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs(job_id,payload_json,status,attempts,available_at,deadline,updated_at) VALUES(?,?,?,0,?,?,?)",
                (jid, json.dumps(payload, sort_keys=True), "READY", now, deadline, now),
            )
        return jid

    def lease(self, owner: str, *, lease_seconds: int = 60) -> Job | None:
        now = time.time()
        lease_until = now + lease_seconds
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "UPDATE jobs SET status='READY', lease_owner=NULL, lease_until=NULL, updated_at=? WHERE status='LEASED' AND lease_until <= ?",
                (now, now),
            )
            conn.execute(
                "UPDATE jobs SET status='EXPIRED', updated_at=? WHERE status IN ('READY','LEASED') AND deadline IS NOT NULL AND deadline <= ?",
                (now, now),
            )
            row = conn.execute(
                "SELECT * FROM jobs WHERE status='READY' AND available_at <= ? ORDER BY available_at, job_id LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                conn.execute("COMMIT")
                return None
            conn.execute(
                "UPDATE jobs SET status='LEASED', attempts=attempts+1, lease_owner=?, lease_until=?, updated_at=? WHERE job_id=?",
                (owner, lease_until, now, row["job_id"]),
            )
            conn.execute("COMMIT")
        return self.get(row["job_id"])

    def ack(self, job_id: str, owner: str) -> None:
        now = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='SUCCEEDED', lease_owner=NULL, lease_until=NULL, updated_at=? WHERE job_id=? AND status='LEASED' AND lease_owner=?",
                (now, job_id, owner),
            )
            if cur.rowcount != 1:
                raise RuntimeError("ack rejected: lease ownership mismatch")

    def retry(self, job_id: str, owner: str, *, delay_seconds: float = 0) -> None:
        now = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='READY', available_at=?, lease_owner=NULL, lease_until=NULL, updated_at=? WHERE job_id=? AND status='LEASED' AND lease_owner=?",
                (now + delay_seconds, now, job_id, owner),
            )
            if cur.rowcount != 1:
                raise RuntimeError("retry rejected: lease ownership mismatch")

    def cancel(self, job_id: str) -> None:
        now = time.time()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status='CANCELLED', lease_owner=NULL, lease_until=NULL, updated_at=? WHERE job_id=? AND status NOT IN ('SUCCEEDED','CANCELLED','EXPIRED')",
                (now, job_id),
            )
            if cur.rowcount != 1:
                current = self.get(job_id)
                if current is None:
                    raise KeyError(job_id)
                if current.status == "SUCCEEDED":
                    raise RuntimeError("cannot cancel succeeded job")

    def get(self, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return Job(
            job_id=row["job_id"], payload=json.loads(row["payload_json"]), status=row["status"],
            attempts=int(row["attempts"]), lease_owner=row["lease_owner"], lease_until=row["lease_until"], deadline=row["deadline"],
        )
