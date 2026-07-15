import subprocess
import json
from pathlib import Path

def test_cli_import_openapi_tools(tmp_path):
    out_file = tmp_path / "openapi-tools.json"
    csv_file = tmp_path / "openapi-tools.md"
    csv_file.write_text("| Tool Name | Category |\n| --- | --- |\n| TestTool | Docs |\n")
    
    # We call the CLI entrypoint directly.
    from utag_cli.main import main
    
    # We can mock sys.argv or just call main
    # Wait, main() uses sys.argv if not passed, but we can pass it
    try:
        main(["intel", "import-openapi-tools", "--csv", str(csv_file), "--out", str(out_file)])
    except SystemExit as e:
        assert e.code == 0
        
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "primitives" in data
    assert "providers" in data
    assert len(data["providers"]) > 0

def test_cli_primitives(tmp_path):
    out_file = tmp_path / "primitives.json"
    from utag_cli.main import main
    try:
        main(["intel", "primitives", "--out", str(out_file)])
    except SystemExit as e:
        assert e.code == 0
        
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "primitives" in data

def test_cli_gaps(tmp_path):
    out_file = tmp_path / "gaps.md"
    from utag_cli.main import main
    try:
        main(["intel", "gaps", "--against", "utag", "--out", str(out_file)])
    except SystemExit as e:
        assert e.code == 0
        
    assert out_file.exists()
