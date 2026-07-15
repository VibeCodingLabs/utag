import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def _observe_store_in_tmp(tmp_path_factory, monkeypatch):
    """Keep run evidence out of the repo during tests (UTAG_OBSERVE_DIR wins)."""
    monkeypatch.setenv("UTAG_OBSERVE_DIR",
                       str(tmp_path_factory.mktemp("observe")))
