import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dd_playbook.cli import main

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"
BANK = ROOT / "data" / "question-bank.csv"


def run_module(*args, cwd=ROOT):
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    return subprocess.run(
        [sys.executable, "-m", "dd_playbook", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env
    )


def test_end_to_end_score_matches_committed_example(tmp_path):
    out = tmp_path / "out"
    proc = run_module(
        "score", str(EX / "brightwater-assessment.csv"),
        "--target", "Brightwater Fixings Ltd", "--acquirer", "Larkfield Components Group",
        "--out", str(out),
    )
    assert proc.returncode == 0, proc.stderr
    assert "Overall 53.4 (AMBER)" in proc.stdout
    for name in ("summary.md", "scores.json", "red-flags.csv"):
        assert (out / name).read_bytes() == (EX / "output" / name).read_bytes(), name


def test_end_to_end_synergy_matches_committed_example(tmp_path):
    out = tmp_path / "out"
    title = "Larkfield Components Group and Brightwater Fixings Ltd: synergy and cost summary"
    proc = run_module("synergy", str(EX / "brightwater-synergy.csv"), "--title", title, "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    assert "not within 36 months" in proc.stdout
    for name in ("synergy-summary.md", "synergy.json"):
        assert (out / name).read_bytes() == (EX / "output" / name).read_bytes(), name


def test_example_expected_headline_values():
    data = json.loads((EX / "output" / "scores.json").read_text(encoding="utf-8"))
    assert data["overall"]["score"] == 53.4
    assert data["overall"]["red_flags"] == 15
    assert data["overall"]["critical_red_flags"] == 7
    rags = {d["domain"]: d["rag"] for d in data["domains"]}
    assert rags["Cyber security"] == "RED"
    assert rags["IT spend"] == "GREEN"
    ids = {f["id"] for f in data["red_flags"]}
    assert {"SEC-01", "PPL-02", "APP-02", "SUP-02", "SVC-04"} <= ids
    syn = json.loads((EX / "output" / "synergy.json").read_text(encoding="utf-8"))
    assert syn["nominal"]["one_off_costs_total"] == 815000
    assert syn["nominal"]["run_rate_savings_total"] == 59000


def test_example_assessment_covers_real_bank_ids():
    with open(BANK, newline="", encoding="utf-8") as fh:
        bank_ids = {r["id"] for r in csv.DictReader(fh)}
    with open(EX / "brightwater-assessment.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert {r["id"] for r in rows} == bank_ids


def test_template_then_score_round_trip(tmp_path):
    path = tmp_path / "blank.csv"
    assert run_module("template", "--out", str(path)).returncode == 0
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    assert rows[0].keys() == {"id", "answer_score", "notes", "evidence_seen"}
    # A blank template has nothing scored: a clear error, exit status 2.
    proc = run_module("score", str(path), "--out", str(tmp_path / "o"))
    assert proc.returncode == 2
    assert "no scored answers" in proc.stderr
    # Fill every answer with 4 and evidence yes: perfect score.
    for r in rows:
        r["answer_score"], r["evidence_seen"] = "4", "yes"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "answer_score", "notes", "evidence_seen"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    proc = run_module("score", str(path), "--out", str(tmp_path / "o"))
    assert proc.returncode == 0, proc.stderr
    data = json.loads((tmp_path / "o" / "scores.json").read_text(encoding="utf-8"))
    assert data["overall"]["score"] == 100.0 and data["overall"]["rag"] == "GREEN"
    assert data["red_flags"] == []


def test_template_does_not_overwrite_without_force(tmp_path):
    path = tmp_path / "a.csv"
    path.write_text("my answers", encoding="utf-8")
    proc = run_module("template", "--out", str(path))
    assert proc.returncode == 2
    assert "already exists" in proc.stderr
    assert path.read_text(encoding="utf-8") == "my answers"
    assert run_module("template", "--out", str(path), "--force", "--worksheet").returncode == 0
    assert path.read_text(encoding="utf-8").startswith("id,domain,question")


def test_worksheet_can_be_scored(tmp_path):
    path = tmp_path / "w.csv"
    run_module("template", "--out", str(path), "--worksheet")
    text = path.read_text(encoding="utf-8").replace(",NA,,no,", ",3,,yes,", 5)
    path.write_text(text, encoding="utf-8")
    proc = run_module("score", str(path), "--out", str(tmp_path / "o"))
    assert proc.returncode == 0, proc.stderr
    assert "5 of 104 questions answered" in proc.stdout


def test_score_with_config_changes_status(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text('{"rag": {"green_min": 90, "amber_min": 60}}', encoding="utf-8")
    out = tmp_path / "o"
    code = main(["score", str(EX / "brightwater-assessment.csv"), "--config", str(cfg), "--out", str(out)])
    assert code == 0
    data = json.loads((out / "scores.json").read_text(encoding="utf-8"))
    assert data["overall"]["rag"] == "RED"
    assert data["settings"]["rag"]["green_min"] == 90


def test_partial_assessment_notes_missing_questions(tmp_path):
    p = tmp_path / "p.csv"
    p.write_text("id,answer_score,notes,evidence_seen\nSEC-01,0,none,yes\nSEC-03,4,fine,yes\n", encoding="utf-8")
    proc = run_module("score", str(p), "--out", str(tmp_path / "o"))
    assert proc.returncode == 0
    assert "102 bank question(s) were not in the assessment file" in proc.stdout
    summary = (tmp_path / "o" / "summary.md").read_text(encoding="utf-8")
    assert "INSUFFICIENT DATA" in summary


@pytest.mark.parametrize(
    "args, message",
    [
        (["score", "missing.csv"], "Assessment not found"),
        (["synergy", "missing.csv"], "Synergy file not found"),
        (["template", "--bank", "missing.csv"], "Question bank not found"),
        (["score", str(EX / "brightwater-assessment.csv"), "--config", "missing.json"], "Config file not found"),
        (["synergy", str(EX / "brightwater-synergy.csv"), "--savings-start-month", "20"], "savings_start_month"),
    ],
)
def test_clear_errors_and_exit_status_2(tmp_path, args, message):
    proc = run_module(*args, "--out", str(tmp_path / "o")) if args[0] != "template" else run_module(*args, "--out", str(tmp_path / "t.csv"))
    assert proc.returncode == 2
    assert message in proc.stderr
    assert "Traceback" not in proc.stderr


def test_malformed_assessment_lists_problems(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("id,answer_score,notes,evidence_seen\nSEC-01,9,,yes\nNOPE-1,2,,yes\n", encoding="utf-8")
    proc = run_module("score", str(p), "--out", str(tmp_path / "o"))
    assert proc.returncode == 2
    assert "2 problems found" in proc.stderr
    assert not (tmp_path / "o").exists()


def test_default_bank_found_from_another_folder(tmp_path):
    proc = run_module("template", "--out", str(tmp_path / "t.csv"), cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_help_and_version():
    assert "usage" in run_module("--help").stdout.lower()
    assert run_module("--version").stdout.startswith("dd_playbook ")
    assert run_module().returncode == 2
