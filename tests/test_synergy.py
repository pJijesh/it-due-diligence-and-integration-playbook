import pytest

from dd_playbook.errors import InputError
from dd_playbook.synergy import Item, analyse, load_assumptions, load_synergy


def run(items, **kw):
    return analyse(items, load_assumptions(None, kw.get("start")))


def test_payback_month_and_three_year_net_known_values():
    # Cost 120000 spread over year 1 (10000 a month). Saving 60000 a year from month 7 (5000 a month).
    # Cumulative: -90000 at month 12, then +5000 a month, so it reaches zero at month 30.
    res = run([Item("c", "one-off", 120000, 1, "high"), Item("s", "run-rate", 60000, 1, "high")])
    n = res["nominal"]
    assert n["payback"] == {"month": 30, "status": "paid back"}
    assert n["three_year_net"] == 30000
    assert [y["cumulative_net"] for y in n["years"]] == [-90000, -30000, 30000]
    assert n["years"][0]["savings_realised"] == 30000


def test_risk_adjusted_values_known():
    # Savings x 0.9 = 4500 a month. Cumulative at month 12 is -93000. Month 32 is -3000, month 33 is +1500.
    res = run([Item("c", "one-off", 120000, 1, "high"), Item("s", "run-rate", 60000, 1, "high")])
    a = res["risk_adjusted"]
    assert a["run_rate_savings_total"] == 54000
    assert a["payback"]["month"] == 33
    assert a["three_year_net"] == 15000


def test_confidence_changes_risk_adjusted_totals():
    items = [
        Item("cost", "one-off", 100000, 1, "low"),
        Item("a", "run-rate", 100000, 1, "medium"),
    ]
    res = run(items)
    assert res["risk_adjusted"]["one_off_costs_total"] == 130000
    assert res["risk_adjusted"]["run_rate_savings_total"] == 60000
    assert res["nominal"]["one_off_costs_total"] == 100000
    med = [c for c in res["by_confidence"] if c["confidence"] == "medium"][0]
    assert med["risk_adjusted_run_rate_savings"] == 60000


def test_negative_run_rate_is_uplifted_not_haircut():
    res = run([Item("d", "run-rate", -12000, 1, "medium"), Item("c", "one-off", 1000, 1, "high")])
    assert res["risk_adjusted"]["run_rate_savings_total"] == -13800


def test_never_pays_back_within_horizon():
    res = run([Item("c", "one-off", 100000, 1, "high"), Item("s", "run-rate", 10000, 1, "high")])
    assert res["nominal"]["payback"]["month"] is None
    assert "not within 36 months" in res["nominal"]["payback"]["status"]


def test_no_costs_means_payback_not_defined():
    res = run([Item("s", "run-rate", 10000, 1, "high")])
    assert res["nominal"]["payback"]["month"] is None
    assert "no one-off costs" in res["nominal"]["payback"]["status"]


def test_savings_start_month_changes_payback():
    items = [Item("c", "one-off", 120000, 1, "high"), Item("s", "run-rate", 60000, 1, "high")]
    early = analyse(items, load_assumptions(None, 1))["nominal"]["payback"]["month"]
    late = analyse(items, load_assumptions(None, 12))["nominal"]["payback"]["month"]
    assert early < 30 < late


def test_low_confidence_observation():
    res = run([Item("a", "run-rate", 70000, 1, "low"), Item("b", "run-rate", 30000, 1, "high"), Item("c", "one-off", 1, 1, "high")])
    assert res["low_confidence_share_of_run_rate_pct"] == 70.0
    assert any("low confidence" in o for o in res["observations"])


def write(tmp_path, text):
    p = tmp_path / "s.csv"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_synergy_accepts_common_spellings(tmp_path):
    p = write(
        tmp_path,
        "item,type,amount,year,confidence\nA,One off,\"1,000\",1,High\nB,run_rate,(500),2,LOW\nC,runrate,£2000,3,medium\n",
    )
    items, _ = load_synergy(p)
    assert [(i.kind, i.amount, i.confidence) for i in items] == [
        ("one-off", 1000.0, "high"),
        ("run-rate", -500.0, "low"),
        ("run-rate", 2000.0, "medium"),
    ]


def test_load_synergy_reports_all_problems(tmp_path):
    p = write(
        tmp_path,
        "item,type,amount,year,confidence\nA,saving,100,1,high\nB,one-off,abc,1,high\nC,one-off,5,4,high\nD,one-off,5,1,certain\nE,one-off,-5,1,high\n,run-rate,1,1,high\n",
    )
    with pytest.raises(InputError) as exc:
        load_synergy(p)
    text = exc.value.format()
    for fragment in ("type must be", "amount must be a number", "year must be 1, 2 or 3", "confidence must be", "must not be negative", "item name is empty"):
        assert fragment in text


def test_load_synergy_structure_errors(tmp_path):
    with pytest.raises(InputError, match="missing required column.*confidence"):
        load_synergy(write(tmp_path, "item,type,amount,year\nA,one-off,1,1\n"))
    with pytest.raises(InputError, match="no items"):
        load_synergy(write(tmp_path, "item,type,amount,year,confidence\n"))
    with pytest.raises(InputError, match="not found"):
        load_synergy(tmp_path / "none.csv")


def test_nan_amount_rejected(tmp_path):
    with pytest.raises(InputError, match="amount must be a number"):
        load_synergy(write(tmp_path, "item,type,amount,year,confidence\nA,one-off,nan,1,high\n"))


def test_assumptions_file(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"savings_factor": {"low": 0.1}, "savings_start_month": 4}', encoding="utf-8")
    cfg = load_assumptions(p)
    assert cfg["savings_factor"] == {"high": 0.9, "medium": 0.6, "low": 0.1}
    assert cfg["savings_start_month"] == 4


@pytest.mark.parametrize(
    "text, message",
    [
        ("{oops", "not valid JSON"),
        ('{"nope": 1}', "Unknown assumption"),
        ('{"savings_factor": {"high": 2}}', "savings_factor.high"),
        ('{"cost_uplift": {"low": 0.5}}', "cost_uplift.low"),
        ('{"savings_factor": {"huge": 1}}', "unknown level"),
        ('{"savings_start_month": 13}', "savings_start_month"),
    ],
)
def test_bad_assumptions(tmp_path, text, message):
    p = tmp_path / "a.json"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(InputError, match=message):
        load_assumptions(p)


def test_start_month_override_validated():
    with pytest.raises(InputError, match="savings_start_month"):
        load_assumptions(None, 0)
