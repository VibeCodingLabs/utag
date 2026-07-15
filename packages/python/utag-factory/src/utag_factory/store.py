"""State layer: sqlite (WAL) job store + sqlite-vec vector store, per the
template's JobStorePort/VectorStorePort. Payloads live here — the queue carries
pointers only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec

from utag_core.schemas.factory import FactoryJob, JobStatus


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    return db


class JobStore:
    """sqlite-backed job records + payloads (pointers-only queue contract)."""

    def __init__(self, path: Path):
        self.db = _connect(path)
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, record TEXT NOT NULL,"
            " status TEXT NOT NULL, kind TEXT NOT NULL, updated_at TEXT NOT NULL);"
            "CREATE TABLE IF NOT EXISTS payloads (ref TEXT PRIMARY KEY, body TEXT NOT NULL,"
            " sha256 TEXT NOT NULL);"
            "CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);")
        self.db.commit()

    def put_payload(self, job_id: str, payload: dict) -> tuple[str, str]:
        body = json.dumps(payload, sort_keys=True)
        sha = hashlib.sha256(body.encode()).hexdigest()
        ref = f"payload:{job_id}"
        self.db.execute("INSERT OR REPLACE INTO payloads VALUES (?, ?, ?)", (ref, body, sha))
        self.db.commit()
        return ref, sha

    def get_payload(self, ref: str) -> dict:
        row = self.db.execute("SELECT body, sha256 FROM payloads WHERE ref = ?", (ref,)).fetchone()
        if row is None:
            raise KeyError(f"no payload {ref!r}")
        body, sha = row
        if hashlib.sha256(body.encode()).hexdigest() != sha:
            raise ValueError(f"payload {ref!r} digest mismatch")
        return json.loads(body)

    def put_result(self, job_id: str, result: dict) -> None:
        body = json.dumps(result, sort_keys=True)
        sha = hashlib.sha256(body.encode()).hexdigest()
        self.db.execute("INSERT OR REPLACE INTO payloads VALUES (?, ?, ?)",
                        (f"result:{job_id}", body, sha))
        self.db.commit()

    def get_result(self, job_id: str) -> dict:
        return self.get_payload(f"result:{job_id}")

    def put(self, job: FactoryJob) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?)",
            (job.id, job.model_dump_json(exclude_none=True), job.status.value,
             job.kind.value, job.updated_at))
        self.db.commit()

    def get(self, job_id: str) -> FactoryJob:
        row = self.db.execute("SELECT record FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(f"no job {job_id!r}")
        return FactoryJob.model_validate_json(row[0])

    def transition(self, job_id: str, status: JobStatus, **fields) -> FactoryJob:
        job = self.get(job_id)
        job = job.model_copy(update={"status": status, "updated_at": _now_iso(), **fields})
        self.put(job)
        return job

    def counts_by_status(self) -> dict[str, int]:
        rows = self.db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
        return dict(rows)

    def list_ids(self, status: JobStatus | None = None) -> list[str]:
        if status is None:
            rows = self.db.execute("SELECT id FROM jobs ORDER BY id").fetchall()
        else:
            rows = self.db.execute("SELECT id FROM jobs WHERE status = ? ORDER BY id",
                                   (status.value,)).fetchall()
        return [r[0] for r in rows]


class VectorStore:
    """sqlite-vec cosine store: keys + metadata + float32 embeddings."""

    def __init__(self, path: Path, dim: int = 256):
        self.dim = dim
        self.db = _connect(path)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        self.db.executescript(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vectors USING vec0("
            f"embedding float[{dim}] distance_metric=cosine);"
            "CREATE TABLE IF NOT EXISTS vector_meta (rowid INTEGER PRIMARY KEY,"
            " key TEXT NOT NULL, metadata TEXT NOT NULL, created_s REAL NOT NULL);")
        self.db.commit()

    def add(self, key: str, vector: list[float], metadata: dict) -> int:
        if len(vector) != self.dim:
            raise ValueError(f"vector dim {len(vector)} != store dim {self.dim}")
        cur = self.db.execute("INSERT INTO vectors(embedding) VALUES (?)",
                              (sqlite_vec.serialize_float32(vector),))
        rowid = cur.lastrowid
        self.db.execute("INSERT INTO vector_meta VALUES (?, ?, ?, ?)",
                        (rowid, key, json.dumps(metadata, sort_keys=True), time.time()))
        self.db.commit()
        return rowid

    def search(self, vector: list[float], k: int = 5,
               max_age_s: float | None = None) -> list[tuple[str, float, dict]]:
        """Returns (key, cosine_similarity, metadata) best-first."""
        rows = self.db.execute(
            "SELECT v.rowid, v.distance, m.key, m.metadata, m.created_s"
            " FROM vectors v JOIN vector_meta m ON m.rowid = v.rowid"
            " WHERE v.embedding MATCH ? AND v.k = ?",
            (sqlite_vec.serialize_float32(vector), k)).fetchall()
        out = []
        now = time.time()
        for _rowid, distance, key, metadata, created_s in rows:
            if max_age_s is not None and now - created_s > max_age_s:
                continue
            out.append((key, 1.0 - distance, json.loads(metadata)))
        return out
