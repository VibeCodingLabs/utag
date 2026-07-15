"""Shared runtime wiring: build config, redis, queue, store, worker from env.

Redis is imported lazily so the surfaces import cleanly without a live server;
`connect()` is what actually needs Redis.
"""
from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path

from utag_factory.config import FactoryConfig, load_config
from utag_factory.queue import StreamQueue
from utag_factory.store import JobStore, VectorStore
from utag_factory.worker import Worker


def consumer_name(cfg: FactoryConfig, index: int = 0) -> str:
    return cfg.profile.queue.consumer_name_template.format(
        hostname=socket.gethostname(), pid=os.getpid(), worker_index=index)


@dataclass
class Runtime:
    cfg: FactoryConfig
    queue: StreamQueue
    store: JobStore

    def worker(self, name: str) -> Worker:
        return Worker(self.cfg, self.store, self.queue, name=name)

    def vectors(self) -> VectorStore:
        return VectorStore(self.cfg.data_dir() / "vectors.db")


def connect(root: Path | None = None, name_index: int = 0, worker_name: str | None = None) -> Runtime:
    import redis  # lazy

    cfg = load_config(root)
    r = redis.from_url(cfg.redis_url)
    queue = StreamQueue(r, cfg.profile.queue,
                        consumer_name=worker_name or consumer_name(cfg, name_index))
    queue.ensure_groups()
    store = JobStore(cfg.data_dir() / "jobs.db")
    return Runtime(cfg=cfg, queue=queue, store=store)
