from pathlib import Path

import pytest

from dd_playbook.assessment import REQUIRED_COLUMNS, TEMPLATE_COLUMNS, WORKSHEET_COLUMNS, load_assessment, template_text
from dd_playbook.bank import Question, load_bank
from dd_playbook.errors import InputError

ROOT = Path(__file__).resolve().parent.parent
BANK = [Question("A-1", "Alpha", "One?", "w", "e", 3, "r"), Question("A-2", "Alpha", "Two?", "w", "e", 2, "r")]


def write(tmp_path, text):
    p = tmp_path / "a.csv"
    p.write_text(text, encoding="utf-8")
    return p


def test_template_has_exactly_the_four_documented_columns():
    lines = template_text(BANK).splitlines()
    assert lines[0] == "id,answer_score,notes,evidence_seen"
    assert lines[1:] == ["A-1,NA,,no", "A-2,NA,,no"]
    assert TEMPLATE_COLUMNS == REQUIRED_COLUMNS


def test_worksheet_adds_reference_columns():
    lines = template_text(BANK, worksheet=True).splitlines()
    assert lines[0].split(",") == WORKSHEET_COLUMNS
    assert lines[1].startswith("A-1,Alpha,One?,r,3,NA,")


def test_template_of_real_bank_lists_every_question():
    questions, _ = load_bank(ROOT / "data" / "question-bank.csv")
    lines = template_text(questions).splitlines()
    assert len(lines) == len(questions) + 1


def test_load_valid_assessment_with_na_and_missing(tmp_path):
    p = write(tmp_path, "id,answer_score,notes,evidence_seen\nA-1,3,good,yes\n")
    answers, notes, digest = load_assessment(p, BANK)
    assert answers["A-1"].score == 3 and answers["A-1"].evidence_seen is True
    assert notes["missing_ids"] == ["A-2"]
    assert len(digest) == 64


def test_na_and_blank_scores_are_not_scored(tmp_path):
    p = write(tmp_path, "id,answer_score,notes,evidence_seen\nA-1,na,,no\nA-2,2,,Y\n")
    answers, _, _ = load_assessment(p, BANK)
    assert answers["A-1"].score is None
    assert answers["A-2"].score == 2 and answers["A-2"].evidence_seen is True


def test_bom_and_column_case_are_tolerated(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes("﻿ID,Answer_Score,Notes,Evidence_Seen\r\nA-1,4,x,yes\r\n".encode("utf-8"))
    answers, _, _ = load_assessment(p, BANK)
    assert answers["A-1"].score == 4


def test_all_problems_are_reported_together(tmp_path):
    p = write(
        tmp_path,
        "id,answer_score,notes,evidence_seen\nA-1,7,,yes\nZ-9,2,,yes\nA-2,2,,maybe\nA-2,1,,no\n",
    )
    with pytest.raises(InputError) as exc:
        load_assessment(p, BANK)
    text = exc.value.format()
    assert "from 0 to 4 or NA, got 7" in text
    assert "'Z-9' is not in the question bank" in text
    assert "evidence_seen must be yes or no" in text
    assert "appears more than once" in text
    assert "line 2" in text


def test_decimal_score_rejected(tmp_path):
    p = write(tmp_path, "id,answer_score,notes,evidence_seen\nA-1,2.5,,yes\n")
    with pytest.raises(InputError, match="whole number"):
        load_assessment(p, BANK)


def test_missing_column(tmp_path):
    p = write(tmp_path, "id,answer_score\nA-1,3\n")
    with pytest.raises(InputError, match="missing required column.*notes"):
        load_assessment(p, BANK)


def test_nothing_scored(tmp_path):
    p = write(tmp_path, "id,answer_score,notes,evidence_seen\nA-1,NA,,no\nA-2,NA,,no\n")
    with pytest.raises(InputError, match="no scored answers"):
        load_assessment(p, BANK)


def test_empty_and_missing_file(tmp_path):
    with pytest.raises(InputError, match="empty"):
        load_assessment(write(tmp_path, ""), BANK)
    with pytest.raises(InputError, match="not found"):
        load_assessment(tmp_path / "nope.csv", BANK)


def test_non_utf8_file(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes(b"id,answer_score,notes,evidence_seen\nA-1,3,caf\xe9,yes\n")
    with pytest.raises(InputError, match="UTF-8"):
        load_assessment(p, BANK)
