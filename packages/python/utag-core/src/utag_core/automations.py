"""Automation layer (v2.14.0 Phase 7).

Automations are `AutomationManifest` YAML files in `.utag/automations/`; their
`entrypoints` are the shell commands to run. Each automation maps 1:1 to a
GitHub workflow: `.utag/automations/<id>.yaml` <-> `.github/workflows/<id>.yml`.
Runs record Phase 4 evidence (span `utag.run`, one event per command).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from utag_core.observe import Recorder
from utag_core.schemas.core import AutomationManifest

AUTOMATIONS_DIR = ".utag/automations"
WORKFLOWS_DIR = ".github/workflows"

# obvious plaintext credential shapes; ${{ secrets.* }} references are fine
_SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"(?i:(api_key|token|password)\s*[:=]\s*['\"][^'\"$\s{][^'\"]{7,}['\"]))")


def load_automations(root: Path) -> dict[str, AutomationManifest]:
    out = {}
    for path in sorted((root / AUTOMATIONS_DIR).glob("*.yaml")):
        manifest = AutomationManifest.model_validate(yaml.safe_load(path.read_text()))
        if manifest.id != path.stem:
            raise ValueError(f"{path}: manifest id {manifest.id!r} != filename stem {path.stem!r}")
        out[manifest.id] = manifest
    return out


def run_automation(manifest: AutomationManifest, root: Path) -> tuple[int, Recorder]:
    rec = Recorder()
    rc = 0
    with rec.span("utag.run", automation=manifest.id):
        for command in manifest.entrypoints:
            proc = subprocess.run(command, shell=True, cwd=root)
            rec.event("utag.automation.step", automation=manifest.id,
                      command=command, exit=str(proc.returncode))
            if proc.returncode != 0:
                rc = proc.returncode
                break
    rec.metric("utag_runs_total", 1, automation=manifest.id)
    rec.flush()
    return rc, rec


def automation_problems(root: Path) -> list[str]:
    """Doctor: manifests valid, 1:1 workflow mapping, no plaintext secrets."""
    problems = []
    try:
        automations = load_automations(root)
    except Exception as e:  # noqa: BLE001
        return [str(e)]
    workflows = {p.stem: p for p in sorted((root / WORKFLOWS_DIR).glob("*.yml"))}
    for aid, manifest in automations.items():
        if not manifest.entrypoints:
            problems.append(f"automation {aid}: no entrypoints")
        if aid not in workflows:
            problems.append(f"automation {aid}: no matching workflow {WORKFLOWS_DIR}/{aid}.yml")
    for wid, path in workflows.items():
        if wid not in automations:
            problems.append(f"workflow {wid}: no matching automation manifest")
        text = path.read_text()
        if _SECRET_PATTERN.search(text):
            problems.append(f"workflow {wid}: plaintext secret-looking value")
        try:
            if not yaml.safe_load(text).get("jobs"):
                problems.append(f"workflow {wid}: no jobs")
        except yaml.YAMLError as e:
            problems.append(f"workflow {wid}: unparseable YAML: {e}")
    return problems
