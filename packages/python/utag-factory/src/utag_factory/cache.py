"""Exact (Redis, TTL) + semantic (sqlite-vec, cosine threshold) caches.

Key material and the 0.94 threshold come from the canonical template. The
default embedder is a deterministic feature-hash of character n-grams —
offline and honest about being lexical, not semantic; real model embeddings
plug in via the same EmbedderPort (the Flash `embed` tool is that slot).
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Protocol

from utag_core.schemas.factory import CacheConfig

from utag_factory.config import parse_duration_s
from utag_factory.store import VectorStore


class EmbedderPort(Protocol):
    dim: int

    def embed(self, text: str) -> list[float]: ...


class FeatureHashEmbedder:
    """Deterministic char-trigram feature hashing, L2-normalized.

    ponytail: lexical similarity only — good enough to make near-identical
    prompts hit; swap for a model embedder (Flash `embed`) for true semantics.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        t = f"  {text.lower()}  "
        for i in range(len(t) - 2):
            gram = t[i:i + 3]
            h = int.from_bytes(hashlib.blake2b(gram.encode(), digest_size=4).digest(), "big")
            v[h % self.dim] += 1.0 if (h >> 31) & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


def material_digest(material: dict[str, str], required_keys: list[str]) -> str:
    missing = [k for k in required_keys if k not in material]
    if missing:
        raise ValueError(f"cache key material missing {missing}; required: {required_keys}")
    canon = json.dumps({k: material[k] for k in sorted(required_keys)}, sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


class ExactCache:
    def __init__(self, redis, cfg: CacheConfig):
        self.r = redis
        self.ttl_s = int(parse_duration_s(cfg.exact.ttl))

    def get(self, digest: str) -> str | None:
        v = self.r.get(f"utag:cache:{digest}")
        return v.decode() if isinstance(v, bytes) else v

    def put(self, digest: str, value: str) -> None:
        self.r.setex(f"utag:cache:{digest}", self.ttl_s, value)


class SemanticCache:
    def __init__(self, vectors: VectorStore, embedder: EmbedderPort, cfg: CacheConfig):
        self.vectors = vectors
        self.embedder = embedder
        self.threshold = cfg.semantic.similarity_threshold
        self.ttl_s = parse_duration_s(cfg.semantic.ttl)
        self.required_keys = cfg.semantic.key_material

    def get(self, text: str, material: dict[str, str]) -> str | None:
        digest = material_digest(material, self.required_keys)
        for _key, similarity, meta in self.vectors.search(
                self.embedder.embed(text), k=5, max_age_s=self.ttl_s):
            if similarity >= self.threshold and meta.get("material_digest") == digest:
                return meta["value"]
        return None

    def put(self, text: str, material: dict[str, str], value: str) -> None:
        digest = material_digest(material, self.required_keys)
        self.vectors.add(key=digest, vector=self.embedder.embed(text),
                         metadata={"material_digest": digest, "value": value})
