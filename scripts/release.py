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
    import json
    from utag_core.ir import ModuleSpec
    from utag_generators.targets.udc import assemble
    h = hashlib.sha256()
    udc_mod = ModuleSpec(name="acme_design", description="UDC-derived",
                         provenance={"udc_json": json.dumps(assemble(Path("fixtures/kits/udc")),
                                                            sort_keys=True)})
    tax_mod = ModuleSpec(name="tax", provenance={
        "taxonomy_md": Path("fixtures/kits/taxonomies/master_mapped_taxonomy.md").read_text(),
        "tools": "job_repo_audit"})
    for fx in sorted(Path("fixtures/prompts").glob("*.yaml")):
        m = ingest_prompt_yaml(fx.read_text(), str(fx))
        for t in sorted(GENERATORS):
            if t == "generator":
                continue
            mod = tax_mod if t == "taxonomy-skill" else (udc_mod if t.startswith("udc-") else m)
            for rel, content in sorted(get_generator(t).generate(mod).items()):
                h.update(rel.encode()); h.update(content.encode())
    return h.hexdigest()


def main() -> int:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    if proc.returncode:
        failed = [l for l in proc.stdout.splitlines() if l.startswith("FAILED")]
        print("\n".join(failed) or proc.stdout[-2000:])
        print(f"release: DO-NOT-RELEASE ({len(failed) or '?'} test failures — named above)")
        return proc.returncode
    a, b = golden_hash(), golden_hash()
    if a != b:
        print("release: DO-NOT-RELEASE (non-deterministic output)"); return 1
    print(f"release: RELEASE  golden={a[:16]}  tests=green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
