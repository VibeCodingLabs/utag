import utag_generators
from utag_core.registry import get_generator
from utag_core.ir import ModuleSpec, TypeSpec, FieldSpec, OperationSpec, RequestSpec, ResponseSpec, ScalarKind

def _get_module():
    return ModuleSpec(
        name="docs_mod",
        description="A test module",
        types=[TypeSpec(name="User", fields=[FieldSpec(name="id", type=ScalarKind.string)])],
        operations=[
            OperationSpec(
                name="createUser",
                method="POST",
                path="/users",
                request=RequestSpec(body_type="User"),
                responses=[ResponseSpec(status_code=201, body_type="User")]
            )
        ]
    )

def test_docs_portal_static_generator_content():
    gen = get_generator("docs-portal-static")
    out = gen.generate(_get_module())
    assert "docs_mod-portal/index.html" in out
    
    html = out["docs_mod-portal/index.html"]
    assert "<!DOCTYPE html>" in html
    assert "<h1>docs_mod API Reference</h1>" in html
    assert "<h2>Types</h2>" in html
    assert "<h3>User</h3>" in html
    assert "<li><strong>id</strong>: <code>string</code></li>" in html
    assert "<h2>Operations</h2>" in html
    assert "<h3>POST /users</h3>" in html
    assert "Body: <code>User</code>" in html
    assert "<li>201: <code>User</code></li>" in html

def test_api_guides_generator_content():
    gen = get_generator("api-guides")
    out = gen.generate(_get_module())
    assert "docs_mod-guides/intro.md" in out
    assert "docs_mod-guides/auth.md" in out
    assert "# docs_mod API Guide" in out["docs_mod-guides/intro.md"]
    assert "# Authentication" in out["docs_mod-guides/auth.md"]

def test_agent_score_report_generator_content():
    gen = get_generator("agent-score-report")
    out = gen.generate(_get_module())
    assert "agent-score-report.md" in out
    content = out["agent-score-report.md"]
    assert "# Agent Readiness Score:" in content
    # In _get_module(), we didn't add descriptions to User or createUser, so there should be penalties
    assert "Missing description for operation createUser" in content
    assert "Missing description for type User" in content

def test_zudoku_generator_content():
    gen = get_generator("zudoku-compatible-site")
    out = gen.generate(_get_module())
    assert "docs_mod-zudoku/index.html" in out
    html = out["docs_mod-zudoku/index.html"]
    assert "zudoku" in html
    assert 'url: "./docs_mod.openapi.json"' in html

def test_api_changelog_generator_content():
    gen = get_generator("api-changelog")
    out = gen.generate(_get_module())
    assert "docs_mod-changelog.md" in out
    md = out["docs_mod-changelog.md"]
    assert "# docs_mod Changelog" in md
    assert "### Operations Added" in md
    assert "- `[POST] /users`" in md
    assert "### Types Added" in md
    assert "- `User`" in md
