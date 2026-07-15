from utag_cli.main import main

def test_openapi_normalize(capsys):
    try:
        main(["openapi", "normalize"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "normalized" in out

def test_openapi_bundle(capsys):
    try:
        main(["openapi", "bundle"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "bundled" in out

def test_openapi_diff(capsys):
    try:
        main(["openapi", "diff"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "diff computed" in out

def test_openapi_overlay(capsys):
    try:
        main(["openapi", "overlay", "apply"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "overlay applied" in out

def test_openapi_lint(capsys):
    try:
        main(["openapi", "lint"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "linted" in out

def test_openapi_agent_readiness(capsys):
    try:
        main(["openapi", "agent-readiness"])
    except SystemExit as e:
        assert e.code == 0
    out, err = capsys.readouterr()
    assert "readiness checked" in out
