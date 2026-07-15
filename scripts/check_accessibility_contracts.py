#!/usr/bin/env python3
"""Accessibility gate: every generated component/layout region carries an
accessible name; keyboardRequired designs make interactive wrappers focusable."""
import sys
from pathlib import Path

import yaml

from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator
from utag_core.schemas.design import DesignYaml

import utag_generators  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    text = (ROOT / "design.yaml").read_text()
    design = DesignYaml.model_validate(yaml.safe_load(text))
    module = ModuleSpec(name="design", description="design.yaml",
                        provenance={"design_yaml": text})
    files = get_generator("react-component-library").generate(module)
    problems = []
    for rel, content in sorted(files.items()):
        # routes are compositions; their layouts/components carry the labels
        if not rel.startswith("generated/routes/") and "aria-label" not in content:
            problems.append(f"{rel}: no aria-label")
        if design.accessibility.keyboardRequired and rel.startswith("generated/components/") \
                and "tabIndex" not in content and "<table" not in content:
            problems.append(f"{rel}: keyboardRequired but no tabIndex")
    for p in problems:
        print(f"FAIL {p}", file=sys.stderr)
    print(f"check_accessibility_contracts: {len(files)} files, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
