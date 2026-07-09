from utag_core.registry import get_validator


def test_python_source_validator():
    assert get_validator("python-source")("x.py", "a = 1\n").valid
    assert not get_validator("python-source")("x.py", "def broken(:\n").valid


def test_yaml_validator():
    assert get_validator("yaml")("x.yaml", "a: 1\n").valid
    assert not get_validator("yaml")("x.yaml", "a: [1,\n").valid


def test_skill_md_validator_rules():
    v = get_validator("skill-md")
    good = "---\nname: my-skill\ndescription: Does a thing. Use when testing.\n---\n\nBody.\n"
    assert v("SKILL.md", good).valid
    assert not v("SKILL.md", good.replace("my-skill", "My_Skill")).valid       # bad name
    assert not v("SKILL.md", good.replace("Does a thing", "<b>x</b>")).valid   # angle brackets
    assert not v("SKILL.md", "no frontmatter").valid


def test_json_schema_2020_12_validator():
    v = get_validator("json-schema-2020-12")
    assert v("s.json", '{"type": "object"}').valid
    assert not v("s.json", '{"type": 42}').valid
