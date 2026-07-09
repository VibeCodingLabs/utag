import sys
from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"
sys.path.insert(0, str(Path(__file__).parent))
