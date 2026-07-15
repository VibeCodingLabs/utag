"""Provider/model catalog via the public models.dev registry (154 providers;
same data family as Vercel AI Gateway's model pages): context/output limits,
costs, modalities, reasoning + tool-call capability, and the env var each
provider expects for its key. Cached under ~/.utag/cache with TTL; offline-safe.
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CATALOG_URL = "https://models.dev/api.json"
TTL_SECONDS = 24 * 3600


@dataclass
class ModelInfo:
    provider: str
    id: str
    name: str
    context: int
    output: int
    cost_in: float
    cost_out: float
    modalities_in: list[str]
    reasoning: bool
    tool_call: bool

    def row(self) -> tuple:
        return (self.provider, self.id, f"{self.context//1000}k", f"{self.output//1000}k",
                f"${self.cost_in}/${self.cost_out}",
                "+".join(self.modalities_in),
                "R" if self.reasoning else "·", "T" if self.tool_call else "·")


def load_catalog(cache_dir: Path, refresh: bool = False, url: str = CATALOG_URL) -> dict:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "models.json"
    if not refresh and cache.is_file() and time.time() - cache.stat().st_mtime < TTL_SECONDS:
        return json.loads(cache.read_text())
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "utag/2.9 (+github)",
                                                   "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        cache.write_text(json.dumps(data))
        return data
    except Exception:
        if cache.is_file():  # offline: serve stale honestly rather than fail
            return json.loads(cache.read_text())
        raise


def provider_env(catalog: dict, provider: str) -> list[str]:
    return list((catalog.get(provider) or {}).get("env") or [])


def models(catalog: dict, provider: str = "", query: str = "",
           tool_call_only: bool = False, limit: int = 50) -> list[ModelInfo]:
    out: list[ModelInfo] = []
    for pid, p in catalog.items():
        if provider and pid != provider:
            continue
        for mid, m in (p.get("models") or {}).items():
            if query and query.lower() not in (mid + " " + str(m.get("name", ""))).lower():
                continue
            if tool_call_only and not m.get("tool_call"):
                continue
            lim, cost = m.get("limit") or {}, m.get("cost") or {}
            out.append(ModelInfo(
                provider=pid, id=mid, name=str(m.get("name", mid)),
                context=int(lim.get("context") or 0), output=int(lim.get("output") or 0),
                cost_in=float(cost.get("input") or 0), cost_out=float(cost.get("output") or 0),
                modalities_in=list((m.get("modalities") or {}).get("input") or []),
                reasoning=bool(m.get("reasoning")), tool_call=bool(m.get("tool_call"))))
    out.sort(key=lambda x: (x.provider, -x.context, x.id))
    return out[:limit]
