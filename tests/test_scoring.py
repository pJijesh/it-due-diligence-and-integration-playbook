import json
from pathlib import Path

import pytest

from dd_playbook.assessment import Answer
from dd_playbook.bank import Question
from dd_playbook.config import DEFAULT_CONFIG, load_config
from dd_playbook.errors import InputError
from dd_playbook.scoring import score_assessment

ROOT = Path(__file__).resolve().parent.parent


def q(qid, domain, weight):
    return Question(qid, domain, "Question?", "why", "evidence", weight, "flag")


BANK = [q("A-1", "Alpha", 4), q("A-2", "Alpha", 1), q("B-1", "Beta", 5), q("B-2", "Beta", 2)]


def ans(qid, score, evidence=True, red_flag=False):
    return Answer(qid, score, "", evidence, red_flag)


def test_known_weighted_scores_and_rag():
    answers = {
        "A-1": ans("A-1", 3),  # 4 * 3/4 = 3.0
        "A-2": ans("A-2", 4, evidence=False),  # capped to 2: 1 * 2/4 = 0.5
        "B-1": ans("B-1", 1),  # 5 * 1/4 = 1.25
        "B-2": ans("B-2", None),  # NA
    }
    res = score_assessment(BANK, answers, load_config())
    alpha, beta = res["domains"]
    assert alpha["score"] == 70.0
    assert alpha["rag"] == "GREEN"
    assert beta["score"] == 25.0
    assert beta["rag"] == "RED"
    assert beta["coverage_pct"] == pytest.approx(71.4, abs=0.1)
    assert res["overall"]["score"] == 47.5
    assert res["overall"]["rag"] == "RED"
    assert res["overall"]["answers_without_evidence"] == 1
    assert res["overall"]["questions_answered"] == 3


def test_red_flag_register_contents():
    answers = {"A-1": ans("A-1", 3), "B-1": ans("B-1", 1), "B-2": ans("B-2", 0, red_flag=True)}
    res = score_assessment(BANK, answers, load_config())
    flags = {f["id"]: f for f in res["red_flags"]}
    assert set(flags) == {"B-1", "B-2"}
    assert flags["B-1"]["severity"] == "Critical"
    assert "high-weight" in flags["B-1"]["triggers"][0]
    # weight 2 with score 0: only flagged because the assessor marked it
    assert flags["B-2"]["triggers"] == ["assessor marked the red-flag condition as observed"]
    assert [f["id"] for f in res["red_flags"]] == ["B-1", "B-2"]


def test_zero_score_triggers_when_weight_is_high_enough():
    bank = [q("X-1", "X", 3), q("X-2", "X", 2)]
    res = score_assessment(bank, {"X-1": ans("X-1", 0), "X-2": ans("X-2", 0)}, load_config())
    assert [f["id"] for f in res["red_flags"]] == ["X-1"]
    assert "scored 0" in res["red_flags"][0]["triggers"][0]


def test_unevidenced_cap_creates_a_flag_that_evidence_would_remove():
    bank = [q("X-1", "X", 5)]
    cfg = load_config()
    cfg["unevidenced_score_cap"] = 1
    capped = score_assessment(bank, {"X-1": ans("X-1", 3, evidence=False)}, cfg)
    assert capped["overall"]["score"] == 25.0
    assert len(capped["red_flags"]) == 1
    evidenced = score_assessment(bank, {"X-1": ans("X-1", 3, evidence=True)}, cfg)
    assert evidenced["overall"]["score"] == 75.0
    assert evidenced["red_flags"] == []


def test_cap_can_be_disabled():
    bank = [q("X-1", "X", 5)]
    cfg = load_config()
    cfg["unevidenced_score_cap"] = None
    res = score_assessment(bank, {"X-1": ans("X-1", 4, evidence=False)}, cfg)
    assert res["overall"]["score"] == 100.0


def test_critical_flag_stops_a_green_status():
    bank = [q("X-1", "X", 5), q("X-2", "X", 5), q("X-3", "X", 5), q("X-4", "X", 5)]
    answers = {
        "X-1": ans("X-1", 4),
        "X-2": ans("X-2", 4),
        "X-3": ans("X-3", 4),
        "X-4": ans("X-4", 0),
    }
    res = score_assessment(bank, answers, load_config())
    assert res["domains"][0]["score"] == 75.0
    assert res["domains"][0]["rag"] == "AMBER"
    cfg = load_config()
    cfg["cap_green_on_critical_flag"] = False
    res = score_assessment(bank, answers, cfg)
    assert res["domains"][0]["rag"] == "GREEN"


def test_low_coverage_gives_insufficient_data():
    answers = {"A-2": ans("A-2", 4)}  # weight 1 of 5 in Alpha: 20 percent coverage
    res = score_assessment(BANK, answers, load_config())
    by_name = {d["domain"]: d for d in res["domains"]}
    assert by_name["Alpha"]["rag"] == "INSUFFICIENT DATA"
    assert by_name["Alpha"]["coverage_pct"] == 20.0
    assert by_name["Beta"]["rag"] == "NOT ASSESSED"


def test_thresholds_are_configurable():
    bank = [q("X-1", "X", 3)]
    answers = {"X-1": ans("X-1", 2)}  # 50.0
    assert score_assessment(bank, answers, load_config())["overall"]["rag"] == "AMBER"
    cfg = load_config()
    cfg["rag"] = {"green_min": 90, "amber_min": 60}
    assert score_assessment(bank, answers, cfg)["overall"]["rag"] == "RED"
    cfg["rag"] = {"green_min": 50, "amber_min": 20}
    assert score_assessment(bank, answers, cfg)["overall"]["rag"] == "GREEN"


def test_result_is_independent_of_answer_order():
    answers = {"A-1": ans("A-1", 3), "A-2": ans("A-2", 2), "B-1": ans("B-1", 1), "B-2": ans("B-2", 4)}
    a = score_assessment(BANK, answers, load_config())
    b = score_assessment(BANK, dict(reversed(list(answers.items()))), load_config())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_default_config_file_matches_code_defaults():
    on_disk = json.loads((ROOT / "data" / "scoring-config.json").read_text(encoding="utf-8"))
    assert on_disk == DEFAULT_CONFIG


def test_config_override_file(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"rag": {"green_min": 80}}', encoding="utf-8")
    cfg = load_config(p)
    assert cfg["rag"] == {"green_min": 80, "amber_min": 50}


@pytest.mark.parametrize(
    "text, message",
    [
        ("{not json", "not valid JSON"),
        ("[1, 2]", "JSON object"),
        ('{"rags": {}}', "Unknown setting 'rags'"),
        ('{"rag": {"green_min": 40, "amber_min": 50}}', "lower than"),
        ('{"min_coverage": 3}', "min_coverage"),
        ('{"red_flags": {"high_weight": 9}}', "high_weight"),
        ('{"cap_green_on_critical_flag": "yes"}', "true or false"),
    ],
)
def test_bad_config(tmp_path, text, message):
    p = tmp_path / "c.json"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(InputError, match=message):
        load_config(p)


def test_missing_config_file(tmp_path):
    with pytest.raises(InputError, match="not found"):
        load_config(tmp_path / "missing.json")
