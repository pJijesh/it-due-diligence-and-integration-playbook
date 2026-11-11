"""Regenerate the committed example outputs from the example inputs.

Run from the repository root:  python scripts/regenerate_examples.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dd_playbook.cli import main  # noqa: E402

TARGET = "Brightwater Fixings Ltd"
ACQUIRER = "Larkfield Components Group"
OUT = ROOT / "examples" / "output"

SCORE_ARGS = [
    "score",
    str(ROOT / "examples" / "brightwater-assessment.csv"),
    "--bank",
    str(ROOT / "data" / "question-bank.csv"),
    "--target",
    TARGET,
    "--acquirer",
    ACQUIRER,
    "--out",
    str(OUT),
]
SYNERGY_ARGS = [
    "synergy",
    str(ROOT / "examples" / "brightwater-synergy.csv"),
    "--title",
    f"{ACQUIRER} and {TARGET}: synergy and cost summary",
    "--out",
    str(OUT),
]

if __name__ == "__main__":
    code = main(SCORE_ARGS) or main(SYNERGY_ARGS)
    sys.exit(code)
