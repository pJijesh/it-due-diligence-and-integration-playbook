"""Synergy and cost model: totals, risk adjustment, payback and a three-year view.

Conventions (also documented in docs/synergy-and-cost-model.md):

* A one-off item is a cost to achieve. Its amount is spent evenly across the
  twelve months of the stated year.
* A run-rate item is an annual recurring saving (negative means an extra
  recurring cost). It starts to be realised in the stated month of the stated
  year (default month 7, a mid-year convention) and continues to the end of the
  36-month horizon.
* The risk-adjusted view multiplies savings by a factor that falls with lower
  confidence, and multiplies costs (including negative run-rate items, which
  are extra recurring costs) by an uplift that rises with lower confidence. The default factors are illustrative assumptions, not benchmarks.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .csvio import decode, read_bytes, read_rows
from .errors import InputError

REQUIRED_COLUMNS = ["item", "type", "amount", "year", "confidence"]
CONFIDENCES = ("high", "medium", "low")
HORIZON_YEARS = 3
HORIZON_MONTHS = HORIZON_YEARS * 12

DEFAULT_ASSUMPTIONS = {
    "savings_factor": {"high": 0.9, "medium": 0.6, "low": 0.3},
    "cost_uplift": {"high": 1.0, "medium": 1.15, "low": 1.3},
    "savings_start_month": 7,
}

ONE_OFF = "one-off"
RUN_RATE = "run-rate"


@dataclass(frozen=True)
class Item:
    item: str
    kind: str
    amount: float
    year: int
    confidence: str


def load_assumptions(path: Path | None, savings_start_month: int | None = None) -> dict:
    cfg = copy.deepcopy(DEFAULT_ASSUMPTIONS)
    problems: list[str] = []
    if path is not None:
        path = Path(path)
        text = decode(read_bytes(path, "Assumptions file"), path, "Assumptions file")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InputError(f"Assumptions file is not valid JSON ({path}): {exc.msg} at line {exc.lineno}, column {exc.colno}.")
        if not isinstance(data, dict):
            raise InputError(f"Assumptions file must contain a JSON object ({path}).")
        for key, value in data.items():
            if key not in cfg:
                problems.append(f"Unknown assumption '{key}'. Allowed: {', '.join(sorted(cfg))}.")
            elif isinstance(cfg[key], dict):
                if not isinstance(value, dict):
                    problems.append(f"Assumption '{key}' must be an object with keys {', '.join(CONFIDENCES)}.")
                    continue
                for conf, number in value.items():
                    if conf not in CONFIDENCES:
                        problems.append(f"Assumption '{key}' has unknown level '{conf}'. Allowed: {', '.join(CONFIDENCES)}.")
                    else:
                        cfg[key][conf] = number
            else:
                cfg[key] = value
    if savings_start_month is not None:
        cfg["savings_start_month"] = savings_start_month
    for conf in CONFIDENCES:
        f = cfg["savings_factor"][conf]
        u = cfg["cost_uplift"][conf]
        if not _is_number(f) or not 0 <= f <= 1:
            problems.append(f"Assumption 'savings_factor.{conf}' must be a number from 0 to 1, got {f!r}.")
        if not _is_number(u) or not 1 <= u <= 5:
            problems.append(f"Assumption 'cost_uplift.{conf}' must be a number from 1 to 5, got {u!r}.")
    m = cfg["savings_start_month"]
    if isinstance(m, bool) or not isinstance(m, int) or not 1 <= m <= 12:
        problems.append(f"Assumption 'savings_start_month' must be a whole number from 1 to 12, got {m!r}.")
    if problems:
        raise InputError(problems)
    return cfg


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _norm_type(value: str) -> str | None:
    v = re.sub(r"[\s_\-]+", "", value.strip().lower())
    if v == "oneoff":
        return ONE_OFF
    if v == "runrate":
        return RUN_RATE
    return None


def _parse_amount(value: str) -> float | None:
    v = value.strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    if v.startswith("(") and v.endswith(")"):
        v = "-" + v[1:-1]
    try:
        number = float(v)
    except ValueError:
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def load_synergy(path: Path) -> tuple[list[Item], str]:
    rows, _, digest = read_rows(Path(path), "Synergy file", REQUIRED_COLUMNS)
    problems: list[str] = []
    items: list[Item] = []
    for row in rows:
        line = row["_line"]
        name = row["item"]
        where = f"Synergy file line {line}"
        if not name:
            problems.append(f"{where}: item name is empty.")
            continue
        kind = _norm_type(row["type"])
        if kind is None:
            problems.append(f"{where} ({name}): type must be 'one-off' or 'run-rate', got '{row['type']}'.")
        amount = _parse_amount(row["amount"])
        if amount is None:
            problems.append(f"{where} ({name}): amount must be a number, got '{row['amount']}'.")
        try:
            year = int(row["year"])
            if not 1 <= year <= HORIZON_YEARS:
                raise ValueError
        except ValueError:
            problems.append(f"{where} ({name}): year must be 1, 2 or 3, got '{row['year']}'.")
            year = None
        conf = row["confidence"].strip().lower()
        if conf not in CONFIDENCES:
            problems.append(f"{where} ({name}): confidence must be high, medium or low, got '{row['confidence']}'.")
        if kind == ONE_OFF and amount is not None and amount < 0:
            problems.append(f"{where} ({name}): a one-off amount is a cost and must not be negative, got {row['amount']}.")
        if kind and amount is not None and year is not None and conf in CONFIDENCES:
            items.append(Item(name, kind, amount, year, conf))
    if not items and not problems:
        problems.append("Synergy file has a header but no items.")
    if problems:
        raise InputError(problems)
    return items, digest


def _run_rate_factor(it: Item, assumptions: dict) -> float:
    """Savings are haircut by confidence. Extra recurring costs (negative amounts) are uplifted instead."""
    if it.amount < 0:
        return assumptions["cost_uplift"][it.confidence]
    return assumptions["savings_factor"][it.confidence]


def _scenario(items: list[Item], assumptions: dict, adjusted: bool) -> dict:
    start = assumptions["savings_start_month"]
    cost = [0.0] * HORIZON_MONTHS
    saving = [0.0] * HORIZON_MONTHS
    one_off_total = 0.0
    run_rate_total = 0.0
    for it in items:
        if it.kind == ONE_OFF:
            amount = it.amount * (assumptions["cost_uplift"][it.confidence] if adjusted else 1.0)
            one_off_total += amount
            first = 12 * (it.year - 1)
            for m in range(first, first + 12):
                cost[m] += amount / 12
        else:
            amount = it.amount * (_run_rate_factor(it, assumptions) if adjusted else 1.0)
            run_rate_total += amount
            first = 12 * (it.year - 1) + (start - 1)
            for m in range(first, HORIZON_MONTHS):
                saving[m] += amount / 12

    cumulative = []
    running = 0.0
    for m in range(HORIZON_MONTHS):
        running += saving[m] - cost[m]
        cumulative.append(running)

    years = []
    cum_year = 0.0
    for y in range(HORIZON_YEARS):
        c = sum(cost[12 * y : 12 * y + 12])
        s = sum(saving[12 * y : 12 * y + 12])
        cum_year += s - c
        years.append(
            {
                "year": y + 1,
                "one_off_costs": round(c, 2),
                "savings_realised": round(s, 2),
                "net": round(s - c, 2),
                "cumulative_net": round(cum_year, 2),
            }
        )

    payback = _payback(cost, cumulative)
    return {
        "one_off_costs_total": round(one_off_total, 2),
        "run_rate_savings_total": round(run_rate_total, 2),
        "three_year_net": round(cumulative[-1], 2),
        "payback": payback,
        "years": years,
    }


def _payback(cost: list[float], cumulative: list[float]) -> dict:
    """Payback is the month after which the cumulative net position stays at or above zero."""
    if sum(cost) <= 0:
        return {"month": None, "status": "no one-off costs, so payback is not defined"}
    negative = [m for m, value in enumerate(cumulative, start=1) if value < -1e-9]
    if not negative:
        return {"month": 1, "status": "cumulative position is never negative"}
    last = negative[-1]
    if last >= HORIZON_MONTHS:
        return {"month": None, "status": f"not within {HORIZON_MONTHS} months"}
    return {"month": last + 1, "status": "paid back"}


def analyse(items: list[Item], assumptions: dict) -> dict:
    nominal = _scenario(items, assumptions, adjusted=False)
    adjusted = _scenario(items, assumptions, adjusted=True)

    by_conf = []
    for conf in CONFIDENCES:
        sel = [i for i in items if i.confidence == conf]
        one_off = sum(i.amount for i in sel if i.kind == ONE_OFF)
        run_rate = sum(i.amount for i in sel if i.kind == RUN_RATE)
        by_conf.append(
            {
                "confidence": conf,
                "items": len(sel),
                "one_off_costs": round(one_off, 2),
                "run_rate_savings": round(run_rate, 2),
                "risk_adjusted_one_off_costs": round(one_off * assumptions["cost_uplift"][conf], 2),
                "risk_adjusted_run_rate_savings": round(
                    sum(i.amount * _run_rate_factor(i, assumptions) for i in sel if i.kind == RUN_RATE), 2
                ),
            }
        )

    run_total = nominal["run_rate_savings_total"]
    cost_total = nominal["one_off_costs_total"]
    low_run = sum(i.amount for i in items if i.kind == RUN_RATE and i.confidence == "low")
    positive_run = sum(i.amount for i in items if i.kind == RUN_RATE and i.amount > 0)
    low_share = (100 * low_run / positive_run) if positive_run > 0 else 0.0

    observations = []
    if run_total <= 0:
        observations.append("Net run-rate savings are zero or negative, so the programme does not pay back on savings alone.")
    else:
        uplift = 100 * (adjusted["one_off_costs_total"] / cost_total - 1) if cost_total else 0.0
        kept = 100 * adjusted["run_rate_savings_total"] / run_total
        if kept <= 0:
            observations.append(
                f"Risk adjustment removes all of the net run-rate savings (they turn negative) and adds {uplift:.0f}% to one-off costs."
            )
        else:
            observations.append(
                f"Risk adjustment keeps {kept:.0f}% of the stated net run-rate savings and adds {uplift:.0f}% to one-off costs."
            )
    if low_share >= 30:
        observations.append(f"{low_share:.0f}% of positive run-rate savings are rated low confidence: treat the headline savings as a range, not a point.")
    pb_n = nominal["payback"]["month"]
    pb_a = adjusted["payback"]["month"]
    if pb_n is not None and pb_a is None:
        observations.append(f"Payback is month {pb_n} on stated numbers but not within {HORIZON_MONTHS} months once risk-adjusted.")
    elif pb_n is not None and pb_a is not None and pb_a - pb_n >= 6:
        observations.append(f"Risk adjustment moves payback from month {pb_n} to month {pb_a}.")

    return {
        "items": [
            {"item": i.item, "type": i.kind, "amount": i.amount, "year": i.year, "confidence": i.confidence}
            for i in items
        ],
        "assumptions": assumptions,
        "nominal": nominal,
        "risk_adjusted": adjusted,
        "by_confidence": by_conf,
        "low_confidence_share_of_run_rate_pct": round(low_share, 1),
        "observations": observations,
    }
