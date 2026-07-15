"""Flash cloud_burst adapter: agent tools that run on autoscaling RunPod workers.

Each tool is a runpod-flash Endpoint (scale-to-zero, workers=(0, N) from the
cloud_burst profile). The remote worker *is* the sandbox — an ephemeral machine,
destroyed after idle. Capability-gated on `RUNPOD_API_KEY`; import of runpod_flash
is lazy so the package works without the optional dependency.

v1 scope: the tool catalog (run-python, embed, batch-generate) + local dispatch.
Model serving (weights volume + vLLM streaming) is the fast-follow — see
Specs/v2.16.0-factory.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from utag_factory.config import FactoryConfig


def flash_available() -> bool:
    if os.environ.get("RUNPOD_API_KEY") is None:
        return False
    try:
        import runpod_flash  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class FlashToolSpec:
    """Declarative tool manifest — governs what a burst tool is before it exists."""
    name: str
    kind: str            # run-python | embed | batch-generate
    resource: str        # cpu | gpu
    min_workers: int
    max_workers: int
    idle_timeout_s: int = 60


def catalog(cfg: FactoryConfig) -> list[FlashToolSpec]:
    """Burst tools sized from the cloud_burst profile (max workers, scale-to-zero)."""
    burst = cfg.profile.profiles.get("cloud_burst", cfg.worker_profile)
    return [
        FlashToolSpec("run-python", "run-python", "cpu",
                      min_workers=0, max_workers=burst.max_workers),
        FlashToolSpec("embed", "embed", "gpu",
                      min_workers=0, max_workers=burst.max_embedding_workers),
        FlashToolSpec("batch-generate", "batch-generate", "cpu",
                      min_workers=0, max_workers=burst.max_workers),
    ]


def build_endpoints(cfg: FactoryConfig):
    """Construct runpod-flash Endpoints for the catalog. Requires the optional
    `flash` extra + RUNPOD_API_KEY; raises a clear error otherwise."""
    if not flash_available():
        raise RuntimeError(
            "flash burst unavailable: set RUNPOD_API_KEY and install "
            "utag-factory[flash] (runpod-flash)")
    from runpod_flash import CpuInstanceType, Endpoint, GpuGroup  # lazy

    endpoints = {}
    for spec in catalog(cfg):
        if spec.resource == "cpu":
            kw = dict(cpu=CpuInstanceType.CPU5C_4_8)
        else:
            kw = dict(gpu=GpuGroup.ADA_24)
        endpoints[spec.name] = _endpoint_for(spec, Endpoint, kw)
    return endpoints


def _endpoint_for(spec: FlashToolSpec, Endpoint, kw):
    workers = (spec.min_workers, spec.max_workers)

    if spec.kind == "run-python":
        @Endpoint(name=f"utag-{spec.name}", workers=workers,
                  idle_timeout=spec.idle_timeout_s, **kw)
        async def run_python(data):
            import subprocess
            import sys
            import tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as td:
                script = Path(td) / "s.py"
                script.write_text(data["script"])
                proc = subprocess.run([sys.executable, str(script)],
                                      capture_output=True, text=True,
                                      timeout=data.get("timeout", 600))
                return {"stdout": proc.stdout, "stderr": proc.stderr,
                        "exit_code": proc.returncode}
        return run_python

    if spec.kind == "embed":
        @Endpoint(name=f"utag-{spec.name}", workers=workers,
                  idle_timeout=spec.idle_timeout_s,
                  dependencies=["sentence-transformers"], **kw)
        async def embed(data):
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(data.get("model", "all-MiniLM-L6-v2"))
            return {"vectors": model.encode(data["texts"]).tolist()}
        return embed

    @Endpoint(name=f"utag-{spec.name}", workers=workers,
              idle_timeout=spec.idle_timeout_s, dependencies=["utag-generators"], **kw)
    async def batch_generate(data):
        import utag_generators  # noqa: F401
        from utag_core.registry import get_generator
        from utag_generators.ingest import ingest_prompt_yaml
        out = {}
        for item in data["items"]:
            module = ingest_prompt_yaml(item["prompt_yaml"], "flash")
            out[item["id"]] = get_generator(item["target"]).generate(module)
        return out
    return batch_generate
