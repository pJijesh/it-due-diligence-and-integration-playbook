import csv
from pathlib import Path

import pytest

from dd_playbook.bank import BANK_COLUMNS, load_bank
from dd_playbook.errors import InputError

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "data" / "question-bank.csv"

EXPECTED_DOMAINS = {
    "Governance and strategy",
    "Infrastructure and cloud",
    "Applications and ERP",
    "Data and data protection",
    "Cyber security",
    "People and skills",
    "Suppliers, contracts and licences",
    "IT spend",
    "Service management and continuity",
    "Integration readiness",
}


def test_bank_size_and_columns():
    with open(BANK, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == BANK_COLUMNS
        rows = list(reader)
    assert 90 <= len(rows) <= 120


def test_bank_domains_weights_and_unique_ids():
    questions, digest = load_bank(BANK)
    assert len(digest) == 64
    assert {q.domain for q in questions} == EXPECTED_DOMAINS
    assert len({q.id for q in questions}) == len(questions)
    assert all(1 <= q.weight <= 5 for q in questions)
    for q in questions:
        assert q.question.endswith("?")
        assert q.why_it_matters and q.evidence_to_request and q.red_flag_if


def test_every_domain_has_enough_questions():
    questions, _ = load_bank(BANK)
    counts = {}
    for q in questions:
        counts[q.domain] = counts.get(q.domain, 0) + 1
    assert min(counts.values()) >= 8


def _write(tmp_path, text):
    p = tmp_path / "bank.csv"
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_bank_file(tmp_path):
    with pytest.raises(InputError, match="not found"):
        load_bank(tmp_path / "nope.csv")


def test_bank_missing_column(tmp_path):
    p = _write(tmp_path, "id,domain,question\nA-1,D,Q?\n")
    with pytest.raises(InputError, match="missing required column"):
        load_bank(p)


def test_bank_bad_weight_and_duplicate(tmp_path):
    header = ",".join(BANK_COLUMNS)
    p = _write(
        tmp_path,
        header + "\nA-1,D,Q?,w,e,9,r\nA-2,D,Q?,w,e,x,r\nA-3,D,Q?,w,e,3,r\nA-3,D,Q?,w,e,3,r\n",
    )
    with pytest.raises(InputError) as exc:
        load_bank(p)
    text = exc.value.format()
    assert "from 1 to 5, got 9" in text
    assert "whole number" in text
    assert "duplicate id A-3" in text


def test_empty_bank(tmp_path):
    with pytest.raises(InputError, match="empty"):
        load_bank(_write(tmp_path, ""))
