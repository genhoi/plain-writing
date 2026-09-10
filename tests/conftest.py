from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "skill" / "reference"


def rules(findings) -> set[str]:
    return {f.rule for f in findings}


@pytest.fixture
def reference():
    return REFERENCE
