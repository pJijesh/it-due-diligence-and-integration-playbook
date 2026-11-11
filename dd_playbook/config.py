"""Scoring configuration: defaults and loading from a JSON file."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from .csvio import read_bytes, decode
from .errors import InputError

DEFAULT_CONFIG = {
    "rag": {"green_min": 70, "amber_min": 50},
    "min_coverage": 0.6,
    "unevidenced_score_cap": 2,
    "red_flags": {"high_weight": 4, "low_score": 1, "zero_score_min_weight": 3},
    "critical_weight": 5,
    "cap_green_on_critical_flag": True,
}


def _merge(base: dict, override: dict, path: str, problems: list[str]) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        where = f"{path}.{key}" if path else key
        if key not in base:
            problems.append(f"Unknown setting '{where}'. Allowed: {', '.join(sorted(base))}.")
            continue
        if isinstance(base[key], dict):
            if not isinstance(value, dict):
                problems.append(f"Setting '{where}' must be an object.")
                continue
            out[key] = _merge(base[key], value, where, problems)
        else:
            out[key] = value
    return out


def _check_number(value, where: str, lo: float, hi: float, problems: list[str], integer: bool = False) -> None:
    ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    if ok and integer and int(value) != value:
        ok = False
    if not ok or not lo <= value <= hi:
        kind = "a whole number" if integer else "a number"
        problems.append(f"Setting '{where}' must be {kind} from {lo:g} to {hi:g}, got {value!r}.")


def validate(cfg: dict) -> None:
    problems: list[str] = []
    rag = cfg["rag"]
    _check_number(rag["green_min"], "rag.green_min", 0, 100, problems)
    _check_number(rag["amber_min"], "rag.amber_min", 0, 100, problems)
    if not problems and rag["amber_min"] >= rag["green_min"]:
        problems.append("Setting 'rag.amber_min' must be lower than 'rag.green_min'.")
    _check_number(cfg["min_coverage"], "min_coverage", 0, 1, problems)
    cap = cfg["unevidenced_score_cap"]
    if cap is not None:
        _check_number(cap, "unevidenced_score_cap", 0, 4, problems, integer=True)
    rf = cfg["red_flags"]
    _check_number(rf["high_weight"], "red_flags.high_weight", 1, 5, problems, integer=True)
    _check_number(rf["low_score"], "red_flags.low_score", 0, 4, problems, integer=True)
    _check_number(rf["zero_score_min_weight"], "red_flags.zero_score_min_weight", 1, 5, problems, integer=True)
    _check_number(cfg["critical_weight"], "critical_weight", 1, 5, problems, integer=True)
    if not isinstance(cfg["cap_green_on_critical_flag"], bool):
        problems.append("Setting 'cap_green_on_critical_flag' must be true or false.")
    if problems:
        raise InputError(problems)


def load_config(path: Path | None = None) -> dict:
    """Return the defaults, or the defaults overridden by a JSON file."""
    if path is None:
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        validate(cfg)
        return cfg
    path = Path(path)
    text = decode(read_bytes(path, "Config file"), path, "Config file")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(f"Config file is not valid JSON ({path}): {exc.msg} at line {exc.lineno}, column {exc.colno}.")
    if not isinstance(data, dict):
        raise InputError(f"Config file must contain a JSON object ({path}).")
    problems: list[str] = []
    cfg = _merge(DEFAULT_CONFIG, data, "", problems)
    if problems:
        raise InputError(problems)
    validate(cfg)
    return cfg
