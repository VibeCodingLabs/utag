"""`utag design` CLI + gates: validate/tokens/components/app/snapshot, typecheck, a11y."""
from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from utag_cli.main import main as cli_main

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli_main(list(argv))
    return rc, buf.getvalue()


def test_design_validate():
    rc, out = run_cli("design", "validate", "--input", str(ROOT / "design.yaml"))
    assert rc == 0 and '"valid": true' in out


def test_design_validate_rejects_bad(tmp_path):
    bad = tmp_path / "design.yaml"
    bad.write_text("id: x\nnope: true\n")
    rc, _ = run_cli("design", "validate", "--input", str(bad))
    assert rc == 1


def test_design_app_and_snapshot_deterministic(tmp_path):
    rc, _ = run_cli("design", "app", "--input", str(ROOT / "design.yaml"), "--out", str(tmp_path / "ui"))
    assert rc == 0
    assert (tmp_path / "ui/styles/tokens.css").is_file()
    assert (tmp_path / "ui/generated/components/RunStatusCard.tsx").is_file()
    for d in ("s1", "s2"):
        assert run_cli("design", "snapshot", "--input", str(ROOT / "design.yaml"),
                       "--out", str(tmp_path / d))[0] == 0
    assert (tmp_path / "s1/snapshot.md").read_bytes() == (tmp_path / "s2/snapshot.md").read_bytes()


def test_generated_ui_and_accessibility_gates():
    for script in ("check_generated_ui.py", "check_accessibility_contracts.py"):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, f"{script}: {proc.stdout}{proc.stderr}"


def test_generated_ui_typechecks(tmp_path):
    """Capability-gated like the tsc validator: skips (visibly) without npx."""
    if shutil.which("npx") is None:
        pytest.skip("npx unavailable — typecheck gate skipped")
    rc, _ = run_cli("design", "components", "--input", str(ROOT / "design.yaml"), "--out", str(tmp_path))
    assert rc == 0
    # scratch dir has no node_modules: shim react's ambient types so tsc still
    # strictly checks our generated interfaces/props; the fully-resolved
    # typecheck runs against the real UI package (Phase 8)
    shim = tmp_path / "react-shim.d.ts"
    shim.write_text(
        'declare module "react" {\n'
        "  export type ReactNode = unknown;\n"
        "  export type Context<T> = { Provider: (props: { value: T; children?: unknown }) => unknown };\n"
        "  const React: {\n"
        "    createElement: (...args: unknown[]) => unknown;\n"
        "    createContext: <T>(v: T) => Context<T>;\n"
        "    useContext: <T>(c: Context<T>) => T;\n"
        "    useState: <T>(v: T) => [T, (f: (prev: T) => T) => void];\n"
        "  };\n"
        "  export default React;\n"
        "}\n"
        'declare module "react-router-dom" {\n'
        "  export const NavLink: (props: { to: string; children?: unknown }) => unknown;\n"
        "}\n"
        "declare namespace React {\n"
        "  type ReactNode = unknown;\n"
        "  type Context<T> = { Provider: (props: { value: T; children?: unknown }) => unknown };\n"
        "}\n"
        "declare namespace JSX {\n"
        "  interface IntrinsicElements { [element: string]: Record<string, unknown>; }\n"
        "  type Element = unknown;\n"
        "}\n")
    files = [str(shim)] + [str(p) for p in tmp_path.rglob("*.tsx")] \
        + [str(p) for p in tmp_path.rglob("*.ts") if not p.name.endswith(".d.ts")]
    proc = subprocess.run(
        ["npx", "-y", "-p", "typescript", "tsc", "--noEmit", "--jsx", "react",
         "--esModuleInterop", "--strict", "--skipLibCheck", *files],
        capture_output=True, text=True, timeout=300)
    # repo convention (see validators.validate_typescript): scratch dirs have no
    # node_modules, so unresolved-module TS2307 is tolerated; anything else fails
    errors = [l for l in proc.stdout.splitlines() if "error TS" in l and "TS2307" not in l]
    assert errors == [], "\n".join(errors)
