"""CLI end-to-end: fixture -> generate -> validated artifact on disk."""
import json
from pathlib import Path

from utag_cli.main import main

FIXTURE = Path(__file__).parents[2] / "fixtures" / "prompts" / "categorize-file.prompt.yaml"


def test_cli_generate_pydantic(tmp_path, capsys):
    rc = main(["generate", "--input", str(FIXTURE), "--target", "pydantic-models",
               "--out", str(tmp_path)])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is True
    files = list(tmp_path.glob("*.py"))
    assert files and "class CategorizeFileInput" in files[0].read_text()


def test_cli_generate_skill(tmp_path):
    rc = main(["generate", "--input", str(FIXTURE), "--target", "agent-skill",
               "--out", str(tmp_path)])
    assert rc == 0
    skill = tmp_path / "categorize-file" / "SKILL.md"
    assert skill.exists() and skill.read_text().startswith("---\nname: categorize-file")


def test_cli_targets(capsys):
    assert main(["targets"]) == 0
    assert "pydantic-models" in capsys.readouterr().out


def test_cli_validate_bad_yaml(tmp_path):
    bad = tmp_path / "bad.yaml"; bad.write_text("a: [1,")
    assert main(["validate", "--kind", "yaml", "--path", str(bad)]) == 1
