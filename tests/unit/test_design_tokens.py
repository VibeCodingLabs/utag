"""design-tokens-css + tailwind-v4-theme: deterministic, contracted variable families."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import utag_generators  # noqa: F401
from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator
from utag_core.schemas.design import CssVariableManifest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def module():
    return ModuleSpec(name="design", description="d",
                      provenance={"design_yaml": (ROOT / "design.yaml").read_text()})


def test_tokens_css_families_and_determinism(module):
    gen = get_generator("design-tokens-css")
    files = gen.generate(module)
    assert files == gen.generate(module)  # deterministic
    tokens = files["styles/tokens.css"]
    for family in ("--utag-color-", "--utag-space-", "--utag-radius-",
                   "--utag-font-", "--utag-shadow-", "--utag-motion-"):
        assert family in tokens, f"missing family {family}"
    assert files["styles/dark.css"].count("--utag-color-bg") == 2  # data-theme + media query
    assert "prefers-reduced-motion" in files["styles/motion.css"]


def test_css_variable_manifest_validates(module):
    files = get_generator("design-tokens-css").generate(module)
    manifest = CssVariableManifest.model_validate_json(files["styles/css-variables.manifest.json"])
    assert manifest.source_design == "utag-console"
    names = {v.name for v in manifest.variables}
    assert names == set(json.loads(files["styles/tokens.json"]))


def test_tailwind_theme_maps_to_utag_vars(module):
    css = get_generator("tailwind-v4-theme").generate(module)["styles/tailwind.css"]
    assert css.startswith('@import "tailwindcss";')
    assert "@theme {" in css
    assert "--color-bg: var(--utag-color-bg);" in css
    assert "--font-sans: var(--utag-font-sans);" in css


def test_missing_design_yaml_rejected():
    with pytest.raises(ValueError, match="design_yaml"):
        get_generator("design-tokens-css").generate(ModuleSpec(name="x", description="d"))
