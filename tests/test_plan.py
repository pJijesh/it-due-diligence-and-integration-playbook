import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "data" / "integration-plan.csv"

PHASE_RANGES = {
    "Pre-close": (-60, -1),
    "Day 1": (0, 1),
    "Days 2 to 30": (2, 30),
    "Days 31 to 60": (31, 60),
    "Days 61 to 100": (61, 100),
}


def rows():
    with open(PLAN, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == ["phase", "workstream", "task", "owner_role", "dependency", "day_target"]
        return list(reader)


def test_plan_size_and_phases():
    r = rows()
    assert 55 <= len(r) <= 75
    assert {x["phase"] for x in r} == set(PHASE_RANGES)


def test_day_targets_fit_their_phase():
    for x in rows():
        lo, hi = PHASE_RANGES[x["phase"]]
        assert lo <= int(x["day_target"]) <= hi, x["task"]


def test_dependencies_exist_and_come_first():
    r = rows()
    day = {x["task"]: int(x["day_target"]) for x in r}
    assert len(day) == len(r), "task names must be unique"
    for x in r:
        assert x["owner_role"] and x["workstream"]
        if x["dependency"] != "None":
            assert x["dependency"] in day, f"unknown dependency for {x['task']}"
            assert day[x["dependency"]] <= int(x["day_target"]), x["task"]


def test_phases_are_in_date_order_in_file():
    days = [int(x["day_target"]) for x in rows()]
    phase_of = [x["phase"] for x in rows()]
    order = list(PHASE_RANGES)
    assert phase_of == sorted(phase_of, key=order.index)
    assert min(days) < 0 and max(days) == 100


def test_no_dependency_cycles():
    r = rows()
    dep = {x["task"]: x["dependency"] for x in r}
    for task in dep:
        seen = set()
        cur = task
        while cur != "None":
            assert cur not in seen, f"cycle at {task}"
            seen.add(cur)
            cur = dep[cur]
