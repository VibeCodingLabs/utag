#!/usr/bin/env python3
"""release:check — full test suite + golden double-run hash comparison."""
from __future__ import annotations

import hashlib
import subprocess
import sys

sys.path.insert(0, ".")


def golden_hash() -> str:
    import utag_generators  # noqa: F401
    from pathlib import Path
    from utag_core.registry import GENERATORS, get_generator
    from utag_generators.ingest import ingest_prompt_yaml
    h = hashlib.sha256()
    for fx in sorted(Path("fixtures/prompts").glob("*.yaml")):
        m = ingest_prompt_yaml(fx.read_text(), str(fx))
        for t in sorted(GENERATORS):
            if t == "generator":
                continue
            for rel, content in sorted(get_generator(t).generate(m).items()):
                h.update(rel.encode()); h.update(content.encode())
    return h.hexdigest()


def main() -> int:
    rc = subprocess.run([sys.executable, "-m", "pytest", "-q"]).returncode
    if rc:
        print("release: DO-NOT-RELEASE (tests failed)"); return rc
    a, b = golden_hash(), golden_hash()
    if a != b:
        print("release: DO-NOT-RELEASE (non-deterministic output)"); return 1
    print(f"release: RELEASE  golden={a[:16]}  tests=green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
