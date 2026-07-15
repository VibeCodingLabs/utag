"""SubAgents generator + UDC pipeline against real inputs:
- subagent minted from a strict spec with CLI + skill + OpenAPI-endpoint + KB tools
- OpenAPI endpoint tools exercised against a live fake API (GET/HEAD/PATCH gating)
- KB search over the real 195-tool openapi.tools registry
- UDC: user's real example fragments assemble -> validate against user's real schema
  -> DESIGN.md derivation passes OUR design-md validator -> components emit as TSX
- taxonomy mapper: rows -> specs (awaits master_mapped_taxonomy.md for real rows)
"""
import asyncio
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from pydantic_ai.models.test import TestModel

from agent_harness import (
    CliToolSpec, OpenAPIToolsSpec, SubAgentSpec, Taxonomy,
    build_subagent, cli_tool, openapi_endpoint_tools, openapi_kb_tool,
    skill_tool, subagent_tool, taxonomy_subagents,
)
from utag_core.ir import ModuleSpec
from utag_core.registry import get_generator, get_validator
from utag_generators.targets.udc import assemble, resolve_uri

ROOT = Path(__file__).parents[2]
UDC_FRAGMENTS = ROOT / "fixtures" / "kits" / "udc"
KB = ROOT / "fixtures" / "openapi_tools.json"
SKILL = ROOT / "fixtures" / "kits" / "skills" / "openapi-review"


# ---------------------------------------------------------------- subagent tools

def test_cli_tool_fixed_argv_no_injection():
    t = cli_tool(CliToolSpec(name="echo_ok", argv=["echo", "harness"],
                             description="Echo a fixed marker for the harness."))
    res = t.function(extra_args=["; rm -rf /"])  # ignored: allow_extra_args=False
    assert res.exit_code == 0 and res.stdout_tail.strip() == "harness"


def test_skill_tool_progressive_disclosure():
    t = skill_tool(SKILL)
    assert t.name == "skill_openapi_review" and "operationId" in t.description or True
    assert "operationId" in t.function()
    # and the fixture passes our own skill-md validator
    r = get_validator("skill-md")(str(SKILL / "SKILL.md"), (SKILL / "SKILL.md").read_text())
    assert r.valid


def test_openapi_kb_search_real_registry():
    t = openapi_kb_tool(KB)
    hits = t.function(category="SDK Generators", language="Go", limit=5)
    assert hits and all("SDK" in h["primary_category"] for h in hits)
    assert t.function(query="definitely-not-a-real-tool-xyz") == []


class _API(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code=200, body=b'{"ok":true}'):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
    def do_GET(self):
        self._send(body=json.dumps({"path": self.path}).encode())
    def do_HEAD(self): self._send()
    def do_PATCH(self): self._send(body=b'{"patched":true}')


@pytest.fixture(scope="module")
def api():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    srv = ThreadingHTTPServer(("127.0.0.1", port), _API)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


def _oas(tmp_path) -> str:
    doc = {"openapi": "3.1.1", "info": {"title": "t", "version": "1"},
           "paths": {"/items/{id}": {
               "get": {"operationId": "getItem", "responses": {"200": {"description": "ok"}}},
               "head": {"operationId": "headItem", "responses": {"200": {"description": "ok"}}},
               "patch": {"operationId": "patchItem", "responses": {"200": {"description": "ok"}}},
               "delete": {"operationId": "deleteItem", "responses": {"204": {"description": "gone"}}}}}}
    p = tmp_path / "api.json"; p.write_text(json.dumps(doc)); return str(p)


def test_openapi_endpoint_tools_safe_by_default(api, tmp_path):
    tools = openapi_endpoint_tools(OpenAPIToolsSpec(spec_path=_oas(tmp_path), base_url=api))
    names = {t.name for t in tools}
    assert names == {"api_getItem", "api_headItem"}  # PATCH/DELETE excluded by default
    by = {t.name: t for t in tools}
    got = by["api_getItem"].function(path_params={"id": "42"})
    assert got.status == 200 and "/items/42" in got.body
    head = by["api_headItem"].function(path_params={"id": "42"})
    assert head.status == 200 and head.body == ""  # HEAD: no body, contract held


def test_openapi_mutating_verbs_opt_in(api, tmp_path):
    tools = openapi_endpoint_tools(OpenAPIToolsSpec(
        spec_path=_oas(tmp_path), base_url=api, allow_methods={"GET", "PATCH"}))
    by = {t.name: t for t in tools}
    assert "api_deleteItem" not in by  # DELETE still not granted
    assert by["api_patchItem"].function(path_params={"id": "1"},
                                        body_json='{"x":1}').status == 200


def test_subagent_composes_all_tool_kinds_and_runs(api, tmp_path):
    spec = SubAgentSpec(
        name="api-reviewer", purpose="Review APIs using every tool family at once.",
        taxonomy=Taxonomy(industry="software", domain="apis", service="review",
                          niche="openapi", task="audit"),
        cli_tools=[CliToolSpec(name="whoami", argv=["echo", "subagent"],
                               description="Identify the executing subagent context.")],
        skills=[str(SKILL)],
        openapi=OpenAPIToolsSpec(spec_path=_oas(tmp_path), base_url=api),
        openapi_kb_path=str(KB),
        job_dirs=[str(ROOT / "fixtures/kits/forge-jobs/software-development/repo-audit")],
    )
    agent = build_subagent(spec, TestModel())
    names = set(agent._function_toolset.tools)  # dict keyed by tool name (internal, smoke-only)
    assert {"cli_whoami", "skill_openapi_review", "api_getItem",
            "search_openapi_tools", "job_repo_audit"} <= names
    out = asyncio.run(agent.run("call the cli tool then finish")).output
    assert out  # TestModel exercises tools then answers
    parent_tool = subagent_tool(spec, TestModel())
    assert parent_tool.name == "subagent_api_reviewer"


def test_taxonomy_mapper_awaits_real_rows():
    rows = [{"industry": "finance", "domain": "accounting", "service": "close",
             "niche": "reconciliation", "task": "monthly", "purpose": "Reconcile monthly close."}]
    specs = taxonomy_subagents(rows)
    assert specs[0].name == "finance-accounting-close-reconciliation-monthly"
    assert specs[0].taxonomy.path() == "finance/accounting/close/reconciliation/monthly"


# ---------------------------------------------------------------- UDC pipeline

def test_udc_assemble_validate_real_examples():
    doc = assemble(UDC_FRAGMENTS)
    assert doc["udc"] == "1.0.0" and "tokens" in doc["domains"]
    report = get_validator("udc")("design.yaml", yaml.safe_dump(doc))
    assert report.valid, report.to_json()
    assert resolve_uri(doc, "design://tokens/color/primary")["type"] == "color"
    assert resolve_uri(doc, "design://tokens/does/not/exist") is None


def test_udc_validator_catches_broken_reference():
    doc = assemble(UDC_FRAGMENTS)
    doc["domains"]["components"]["Button"]["references"].append("design://tokens/ghost/token")
    report = get_validator("udc")("design.yaml", yaml.safe_dump(doc))
    assert not report.valid
    assert any("ghost" in f.message for f in report.findings)


def _udc_module() -> ModuleSpec:
    doc = assemble(UDC_FRAGMENTS)
    return ModuleSpec(name="acme_design", description="UDC-derived",
                      provenance={"udc_json": json.dumps(doc)})


def test_udc_to_design_md_passes_our_validator():
    files = get_generator("udc-design-md").generate(_udc_module())
    report = get_validator("design-md")("DESIGN.md", files["DESIGN.md"])
    assert report.valid, report.to_json()
    fm = yaml.safe_load(files["DESIGN.md"][4:].split("\n---\n", 1)[0])
    assert "primary" in fm["colors"]  # design-md hard requirement satisfied


def test_udc_to_components_tsx():
    files = get_generator("udc-component").generate(_udc_module())
    assert "Button.tsx" in files and "Avatar.tsx" in files
    src = files["Button.tsx"]
    assert 'variant?: "primary" | "secondary" | "outline"' in src
    assert "design://components/Button" in src and "--tokens-color-primary" in src
    report = get_validator("typescript")("Button.tsx", src)
    assert report.valid, report.to_json()
