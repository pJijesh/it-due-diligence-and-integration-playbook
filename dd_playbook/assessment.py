"""Blank assessment templates and loading of completed assessments."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

from .bank import Question
from .csvio import read_rows
from .errors import InputError

TEMPLATE_COLUMNS = ["id", "answer_score", "notes", "evidence_seen"]
WORKSHEET_COLUMNS = ["id", "domain", "question", "red_flag_if", "weight", "answer_score", "notes", "evidence_seen", "red_flag"]
REQUIRED_COLUMNS = ["id", "answer_score", "notes", "evidence_seen"]

NA = "NA"


@dataclass(frozen=True)
class Answer:
    id: str
    score: int | None  # None means NA (not applicable or not assessed)
    notes: str
    evidence_seen: bool
    red_flag: bool


def template_text(questions: list[Question], worksheet: bool = False) -> str:
    """Return the blank assessment as CSV text.

    The plain template has exactly four columns. The worksheet adds the question,
    its red-flag condition and weight for reference while interviewing, plus an
    optional red_flag column. Reference columns are ignored when scoring.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    if worksheet:
        writer.writerow(WORKSHEET_COLUMNS)
        for q in questions:
            writer.writerow([q.id, q.domain, q.question, q.red_flag_if, q.weight, NA, "", "no", ""])
    else:
        writer.writerow(TEMPLATE_COLUMNS)
        for q in questions:
            writer.writerow([q.id, NA, "", "no"])
    return buf.getvalue()


def _parse_score(value: str) -> tuple[int | None, str | None]:
    v = value.strip()
    if v == "" or v.upper() == NA:
        return None, None
    try:
        number = int(v)
    except ValueError:
        return None, f"answer_score must be a whole number from 0 to 4 or NA, got '{value}'"
    if not 0 <= number <= 4:
        return None, f"answer_score must be from 0 to 4 or NA, got {number}"
    return number, None


def _parse_yes_no(value: str, column: str, blank_means: bool) -> tuple[bool, str | None]:
    v = value.strip().lower()
    if v == "":
        return blank_means, None
    if v in ("yes", "y"):
        return True, None
    if v in ("no", "n"):
        return False, None
    return blank_means, f"{column} must be yes or no, got '{value}'"


def load_assessment(path: Path, questions: list[Question]) -> tuple[dict[str, Answer], dict, str]:
    """Return (answers by id, load notes, sha256).

    Load notes report how many bank questions were missing from the file.
    """
    rows, header, digest = read_rows(Path(path), "Assessment", REQUIRED_COLUMNS)
    known = {q.id for q in questions}
    problems: list[str] = []
    answers: dict[str, Answer] = {}
    for row in rows:
        line = row["_line"]
        qid = row["id"]
        if not qid:
            problems.append(f"Assessment line {line}: id is empty.")
            continue
        if qid not in known:
            problems.append(f"Assessment line {line}: id '{qid}' is not in the question bank.")
            continue
        if qid in answers:
            problems.append(f"Assessment line {line}: id {qid} appears more than once.")
            continue
        score, err = _parse_score(row["answer_score"])
        if err:
            problems.append(f"Assessment line {line} ({qid}): {err}.")
        evidence, err = _parse_yes_no(row["evidence_seen"], "evidence_seen", blank_means=False)
        if err:
            problems.append(f"Assessment line {line} ({qid}): {err}.")
        red_flag, err = _parse_yes_no(row.get("red_flag", ""), "red_flag", blank_means=False)
        if err:
            problems.append(f"Assessment line {line} ({qid}): {err}.")
        answers[qid] = Answer(qid, score, row["notes"], evidence, red_flag)
    if problems:
        raise InputError(problems)
    if not any(a.score is not None for a in answers.values()):
        raise InputError(
            "The assessment has no scored answers: every answer_score is NA or blank. "
            "Score at least some questions from 0 to 4 before running 'score'."
        )
    missing = sorted(known - set(answers))
    return answers, {"missing_ids": missing}, digest
