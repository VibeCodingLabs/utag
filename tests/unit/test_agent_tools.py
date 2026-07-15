"""Harness tools convert to valid, governed MCPToolContracts."""
from __future__ import annotations

import json

import pytest

from utag_core.agent_tools import CATALOG, build_catalog
from utag_core.schemas.mcp import MCPToolContract, PolicyStatus, SideEffect

EXPECTED = {"read", "bash", "edit", "ast_grep", "ast_edit", "ask", "debug", "eval",
            "github", "glob", "grep", "lsp", "browser", "task", "job", "irc",
            "todo", "web_search", "write", "learn", "manage_skill", "resolve",
            "generate_image"}


def test_all_harness_tools_present():
    assert set(CATALOG) == EXPECTED


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_every_tool_is_a_valid_contract(name):
    c = CATALOG[name]
    MCPToolContract.model_validate(c.model_dump())          # strict-schema valid
    assert c.name == name.replace("_", "-")                 # slug name
    assert c.extensions["harness_name"] == name             # original preserved
    assert c.description and c.input_schema["type"] == "object"
    assert c.input_schema["additionalProperties"] is False  # strict input schema


def test_side_effect_classification_is_sensible():
    def eff(n):
        return CATALOG[n].side_effect
    assert eff("read") == SideEffect.read
    assert eff("bash") == SideEffect.destructive and eff("eval") == SideEffect.destructive
    assert eff("write") == SideEffect.write and eff("edit") == SideEffect.write
    assert eff("web_search") == SideEffect.network and eff("browser") == SideEffect.network
    assert eff("ask") == SideEffect.none and eff("irc") == SideEffect.none


def test_dangerous_tools_are_review_gated():
    # destructive + network default to review; read/write/none auto-allowed
    for name in ("bash", "eval", "github", "browser", "web_search"):
        assert CATALOG[name].policy_status == PolicyStatus.review
    for name in ("read", "grep", "write", "edit", "ask"):
        assert CATALOG[name].policy_status == PolicyStatus.allowed


def test_auth_scopes_declared():
    assert "exec" in CATALOG["bash"].auth_scopes
    assert "repo" in CATALOG["github"].auth_scopes
    assert "fs:write" in CATALOG["write"].auth_scopes
    assert all(CATALOG[n].auth_scopes for n in CATALOG)     # every tool hints scopes


def test_catalog_is_a_deterministic_mcp_manifest():
    a = {"tools": [json.loads(c.model_dump_json(exclude_none=True)) for c in build_catalog()]}
    b = {"tools": [json.loads(c.model_dump_json(exclude_none=True)) for c in build_catalog()]}
    assert a == b and len(a["tools"]) == 23
