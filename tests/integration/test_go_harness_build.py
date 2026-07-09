"""End-to-end: go-harness compiles to a static binary; env overrides defaults
(twelve-factor III); go:embed artifacts readable from the binary. Capability-gated."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.registry import get_generator
from utag_generators.ingest import ingest_prompt_yaml

FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "generate-cobra.prompt.yaml"
GO = shutil.which("go")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    if not GO:
        pytest.skip("go toolchain unavailable")
    td = tmp_path_factory.mktemp("goharness")
    module = ingest_prompt_yaml(FIXTURE.read_text(), str(FIXTURE))
    for rel, content in get_generator("go-harness").generate(module).items():
        p = td / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    env = {**os.environ, "GOFLAGS": "-mod=mod", "CGO_ENABLED": "0"}
    for cmd in (["go", "mod", "tidy"], ["go", "vet", "./..."],
                ["go", "build", "-o", "harness", "."]):
        r = subprocess.run(cmd, cwd=td, env=env, capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, f"{cmd}: {r.stderr[-1500:]}"
    return td / "harness"


def test_binary_is_static_and_runs(built):
    r = subprocess.run([str(built), "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "control-plane" in r.stdout


def test_settings_struct_defaults(built):
    out = json.loads(subprocess.run([str(built), "config"], capture_output=True, text=True).stdout)
    assert out == {"log-level": "info", "port": 8080, "provider": "anthropic",
                   "endpoint": "", "max-attempts": 3}


def test_twelve_factor_env_overrides_defaults(built):
    env = {**os.environ, "UTAG_LOG_LEVEL": "debug", "UTAG_PORT": "9999",
           "UTAG_MAX_ATTEMPTS": "7"}
    out = json.loads(subprocess.run([str(built), "config"], env=env,
                                    capture_output=True, text=True).stdout)
    assert (out["log-level"], out["port"], out["max-attempts"]) == ("debug", 9999, 7)


def test_flag_beats_env(built):
    env = {**os.environ, "UTAG_PORT": "9999"}
    out = json.loads(subprocess.run([str(built), "config", "--port", "7777"], env=env,
                                    capture_output=True, text=True).stdout)
    assert out["port"] == 7777  # viper precedence: flag > env


def test_go_embed_artifacts_in_binary(built):
    ls = subprocess.run([str(built), "artifacts"], capture_output=True, text=True).stdout
    assert "generate_cobra.openapi.json" in ls and "generate-cobra.prompt.yaml" in ls
    cat = subprocess.run([str(built), "artifacts", "generate_cobra.openapi.json"],
                         capture_output=True, text=True).stdout
    assert json.loads(cat)["openapi"] == "3.1.1"
