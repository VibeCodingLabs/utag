"""Validator registry entries. Generation and validation stay decoupled.

In-process: pydantic, yaml, json-schema 2020-12, openapi-spec-validator, skill lint.
Subprocess (capability-gated): tsc for TS/Zod artifacts.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml as _yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as _oas_validate

from utag_core.registry import register_validator
from utag_core.report import Finding, Severity, ValidationReport

SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_ALLOWED_SKILL_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


@register_validator("python-source")
def validate_python_source(path: str, content: str) -> ValidationReport:
    try:
        compile(content, path, "exec")
        return ValidationReport.ok(path, "python-source", "compile")
    except SyntaxError as e:
        return ValidationReport.fail(path, "python-source", "compile", [
            Finding(severity=Severity.error, path=f"{path}:{e.lineno}", message=str(e.msg))])


@register_validator("yaml")
def validate_yaml(path: str, content: str) -> ValidationReport:
    try:
        _yaml.safe_load(content)
        return ValidationReport.ok(path, "yaml", "yaml.safe_load")
    except _yaml.YAMLError as e:
        return ValidationReport.fail(path, "yaml", "yaml.safe_load", [
            Finding(severity=Severity.error, path=path, message=str(e))])


@register_validator("json-schema-2020-12")
def validate_json_schema(path: str, content: str) -> ValidationReport:
    try:
        Draft202012Validator.check_schema(json.loads(content))
        return ValidationReport.ok(path, "json-schema-2020-12", "jsonschema.Draft202012")
    except Exception as e:
        return ValidationReport.fail(path, "json-schema-2020-12", "jsonschema.Draft202012", [
            Finding(severity=Severity.error, path=path, message=str(e))])


@register_validator("openapi-3.1")
def validate_openapi(path: str, content: str) -> ValidationReport:
    try:
        _oas_validate(json.loads(content) if path.endswith(".json") else _yaml.safe_load(content))
        return ValidationReport.ok(path, "openapi-3.1", "openapi-spec-validator")
    except Exception as e:
        return ValidationReport.fail(path, "openapi-3.1", "openapi-spec-validator", [
            Finding(severity=Severity.error, path=path, message=str(e))])


@register_validator("skill-md")
def validate_skill_md(path: str, content: str) -> ValidationReport:
    findings: list[Finding] = []
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        findings.append(Finding(severity=Severity.error, path=path, message="missing YAML frontmatter"))
        return ValidationReport.fail(path, "skill-md", "skill-lint", findings)
    fm_text, body = content[4:].split("\n---\n", 1)
    try:
        fm = _yaml.safe_load(fm_text) or {}
    except _yaml.YAMLError as e:
        return ValidationReport.fail(path, "skill-md", "skill-lint", [
            Finding(severity=Severity.error, path=path, message=f"frontmatter yaml: {e}")])
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not name or len(name) > 64 or not SKILL_NAME_RE.match(name):
        findings.append(Finding(severity=Severity.error, path=path,
                        message="name: required, <=64 chars, lowercase alnum + single hyphens"))
    if not desc or len(desc) > 1024:
        findings.append(Finding(severity=Severity.error, path=path,
                        message="description: required, <=1024 chars"))
    if any(ch in str(fm.get(k, "")) for k in ("name", "description") for ch in "<>"):
        findings.append(Finding(severity=Severity.error, path=path,
                        message="angle brackets forbidden in frontmatter"))
    for k in fm:
        if k not in _ALLOWED_SKILL_KEYS:
            findings.append(Finding(severity=Severity.warning, path=path,
                            message=f"unknown frontmatter key: {k}"))
    if len(body.splitlines()) > 500:
        findings.append(Finding(severity=Severity.warning, path=path,
                        message="body exceeds 500 lines (spec guidance)"))
    errors = [f for f in findings if f.severity == Severity.error]
    if errors:
        return ValidationReport.fail(path, "skill-md", "skill-lint", findings)
    r = ValidationReport.ok(path, "skill-md", "skill-lint")
    r.findings = findings  # keep warnings
    return r


def tsc_available() -> bool:
    return shutil.which("npx") is not None


@register_validator("typescript")
def validate_typescript(path: str, content: str) -> ValidationReport:
    """Capability-gated subprocess validator (spec: degrade gracefully without Node)."""
    if not tsc_available():
        r = ValidationReport.ok(path, "typescript", "tsc[skipped]")
        r.findings = [Finding(severity=Severity.info, path=path,
                              message="Node/npx unavailable; tsc validation skipped")]
        return r
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / Path(path).name
        f.write_text(content)
        proc = subprocess.run(
            ["npx", "-y", "-p", "typescript", "tsc", "--noEmit", "--strict",
             "--skipLibCheck", "--moduleResolution", "bundler", "--module", "esnext",
             str(f)],
            capture_output=True, text=True, timeout=300)
    if proc.returncode == 0:
        return ValidationReport.ok(path, "typescript", "tsc")
    # missing zod module in scratch dir is expected: only fail on syntax-class errors
    lines = [l for l in proc.stdout.splitlines() if "error TS" in l and "TS2307" not in l]
    if not lines:
        r = ValidationReport.ok(path, "typescript", "tsc")
        r.findings = [Finding(severity=Severity.info, path=path,
                              message="tsc: only unresolved-module (TS2307) diagnostics; syntax OK")]
        return r
    return ValidationReport.fail(path, "typescript", "tsc", [
        Finding(severity=Severity.error, path=path, message=l) for l in lines[:20]])


_DESIGN_SECTIONS = ["Overview", "Brand & Style", "Colors", "Typography", "Layout",
                    "Layout & Spacing", "Elevation & Depth", "Elevation", "Shapes",
                    "Components", "Do's and Don'ts"]


@register_validator("design-md")
def validate_design_md(path: str, content: str) -> ValidationReport:
    """DESIGN.md (google-labs-code/design.md alpha): frontmatter tokens + section rules."""
    findings: list[Finding] = []
    body = content
    if content.startswith("---\n"):
        try:
            fm_text, body = content[4:].split("\n---\n", 1)
            fm = _yaml.safe_load(fm_text) or {}
        except (_yaml.YAMLError, ValueError) as e:
            return ValidationReport.fail(path, "design-md", "design-lint", [
                Finding(severity=Severity.error, path=path, message=f"frontmatter: {e}")])
        colors = fm.get("colors") or {}
        if colors and "primary" not in colors:
            findings.append(Finding(severity=Severity.error, path=path,
                            message="colors defined but missing required `primary`"))
    headings = re.findall(r"^## (.+)$", body, flags=re.M)
    dupes = {h for h in headings if headings.count(h) > 1}
    for d in sorted(dupes):
        findings.append(Finding(severity=Severity.error, path=path,
                        message=f"duplicate section heading: {d} (spec: reject file)"))
    for h in headings:
        if h not in _DESIGN_SECTIONS:
            findings.append(Finding(severity=Severity.info, path=path,
                            message=f"unknown section preserved: {h} (spec: do not error)"))
    errors = [f for f in findings if f.severity == Severity.error]
    if errors:
        return ValidationReport.fail(path, "design-md", "design-lint", findings)
    r = ValidationReport.ok(path, "design-md", "design-lint")
    r.findings = findings
    return r


@register_validator("go-source")
def validate_go_source(path: str, content: str) -> ValidationReport:
    """gofmt -e: syntax + formatting for a single .go file. Capability-gated."""
    if not path.endswith(".go"):
        return ValidationReport.ok(path, "go-source", "skip[non-go]")
    if shutil.which("gofmt") is None:
        r = ValidationReport.ok(path, "go-source", "gofmt[skipped]")
        r.findings = [Finding(severity=Severity.info, path=path,
                              message="gofmt unavailable; go validation skipped")]
        return r
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "x.go"
        f.write_text(content)
        proc = subprocess.run(["gofmt", "-e", "-l", str(f)], capture_output=True, text=True, timeout=60)
    if proc.returncode == 0 and not proc.stdout.strip() and not proc.stderr.strip():
        return ValidationReport.ok(path, "go-source", "gofmt")
    msg = (proc.stderr or "file not gofmt-formatted").strip()
    return ValidationReport.fail(path, "go-source", "gofmt", [
        Finding(severity=Severity.error, path=path, message=msg[:500])])
