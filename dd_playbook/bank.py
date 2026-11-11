"""Load and validate the question bank."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .csvio import read_rows
from .errors import InputError

BANK_COLUMNS = [
    "id",
    "domain",
    "question",
    "why_it_matters",
    "evidence_to_request",
    "weight",
    "red_flag_if",
]

DEFAULT_BANK_RELATIVE = Path("data") / "question-bank.csv"


@dataclass(frozen=True)
class Question:
    id: str
    domain: str
    question: str
    why_it_matters: str
    evidence_to_request: str
    weight: int
    red_flag_if: str


def find_default_bank() -> Path:
    """Look for data/question-bank.csv in the current folder, then next to the package."""
    candidates = [
        Path.cwd() / DEFAULT_BANK_RELATIVE,
        Path(__file__).resolve().parent.parent / DEFAULT_BANK_RELATIVE,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise InputError(
        "Could not find the question bank at data/question-bank.csv. "
        "Run the command from the repository folder, install with 'pip install -e .' "
        "from a checkout, or pass the file with --bank."
    )


def load_bank(path: Path | None = None) -> tuple[list[Question], str]:
    """Return (questions in file order, sha256 of the file)."""
    bank_path = Path(path) if path else find_default_bank()
    rows, _, digest = read_rows(bank_path, "Question bank", BANK_COLUMNS)
    problems: list[str] = []
    seen: set[str] = set()
    questions: list[Question] = []
    for row in rows:
        line = row["_line"]
        qid = row["id"]
        if not qid:
            problems.append(f"Question bank line {line}: id is empty.")
            continue
        if qid in seen:
            problems.append(f"Question bank line {line}: duplicate id {qid}.")
            continue
        seen.add(qid)
        try:
            weight = int(row["weight"])
        except ValueError:
            problems.append(f"Question bank line {line} ({qid}): weight must be a whole number from 1 to 5, got '{row['weight']}'.")
            continue
        if not 1 <= weight <= 5:
            problems.append(f"Question bank line {line} ({qid}): weight must be from 1 to 5, got {weight}.")
            continue
        for col in ("domain", "question"):
            if not row[col]:
                problems.append(f"Question bank line {line} ({qid}): {col} is empty.")
        questions.append(
            Question(
                id=qid,
                domain=row["domain"],
                question=row["question"],
                why_it_matters=row["why_it_matters"],
                evidence_to_request=row["evidence_to_request"],
                weight=weight,
                red_flag_if=row["red_flag_if"],
            )
        )
    if not questions and not problems:
        problems.append("Question bank has a header but no questions.")
    if problems:
        raise InputError(problems)
    return questions, digest


def domains_in_order(questions: list[Question]) -> list[str]:
    """Domains in order of first appearance in the bank."""
    seen: list[str] = []
    for q in questions:
        if q.domain not in seen:
            seen.append(q.domain)
    return seen
