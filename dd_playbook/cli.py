"""Command line interface: template, score and synergy."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from . import __version__
from .assessment import load_assessment, template_text
from .bank import load_bank
from .config import load_config
from .errors import InputError
from .render import render_score_summary, render_synergy_summary
from .scoring import score_assessment
from .synergy import analyse, load_assumptions, load_synergy

EXIT_INPUT_ERROR = 2


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _json_text(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=True) + "\n"


def _flags_csv(flags: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["id", "severity", "domain", "weight", "answer_score", "effective_score", "evidence_seen", "triggers", "question", "red_flag_if", "notes"])
    for f in flags:
        w.writerow(
            [
                f["id"],
                f["severity"],
                f["domain"],
                f["weight"],
                f["answer_score"],
                f["effective_score"],
                "yes" if f["evidence_seen"] else "no",
                "; ".join(f["triggers"]),
                f["question"],
                f["red_flag_if"],
                f["notes"],
            ]
        )
    return buf.getvalue()


def cmd_template(args: argparse.Namespace) -> int:
    questions, _ = load_bank(args.bank)
    out = Path(args.out)
    if out.exists() and not args.force:
        raise InputError(
            f"{out} already exists. Choose another name with --out, or pass --force to overwrite it "
            "(this would erase any answers already entered)."
        )
    _write(out, template_text(questions, worksheet=args.worksheet))
    kind = "worksheet" if args.worksheet else "template"
    print(f"Wrote {kind} with {len(questions)} questions to {out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    questions, bank_hash = load_bank(args.bank)
    cfg = load_config(args.config)
    answers, notes, assess_hash = load_assessment(args.assessment, questions)
    result = score_assessment(questions, answers, cfg, notes["missing_ids"])
    inputs = {
        "assessment_file": Path(args.assessment).name,
        "assessment_sha256": assess_hash,
        "bank_sha256": bank_hash,
    }
    out_dir = Path(args.out)
    summary = render_score_summary(result, args.target, args.acquirer, inputs)
    payload = {"tool_version": __version__, "target": args.target, "acquirer": args.acquirer, "inputs": inputs, **result}
    _write(out_dir / "summary.md", summary)
    _write(out_dir / "scores.json", _json_text(payload))
    _write(out_dir / "red-flags.csv", _flags_csv(result["red_flags"]))
    o = result["overall"]
    print(
        f"Overall {o['score']:.1f} ({o['rag']}), {o['questions_answered']} of {o['questions_in_bank']} questions answered, "
        f"{o['red_flags']} red flag(s) ({o['critical_red_flags']} critical)."
    )
    if notes["missing_ids"]:
        print(f"Note: {len(notes['missing_ids'])} bank question(s) were not in the assessment file and were treated as not assessed.")
    print(f"Wrote {out_dir / 'summary.md'}, {out_dir / 'scores.json'} and {out_dir / 'red-flags.csv'}")
    return 0


def _money(value: float, sym: str) -> str:
    return f"{'-' if value < 0 else ''}{sym}{abs(value):,.0f}"


def cmd_synergy(args: argparse.Namespace) -> int:
    assumptions = load_assumptions(args.assumptions, args.savings_start_month)
    items, digest = load_synergy(args.file)
    result = analyse(items, assumptions)
    payload = {
        "tool_version": __version__,
        "title": args.title,
        "inputs": {"synergy_file": Path(args.file).name, "synergy_sha256": digest},
        **result,
    }
    out_dir = Path(args.out)
    _write(out_dir / "synergy-summary.md", render_synergy_summary(result, args.title, args.currency))
    _write(out_dir / "synergy.json", _json_text(payload))
    n, a = result["nominal"], result["risk_adjusted"]
    sym = args.currency
    print(
        f"One-off costs {_money(n['one_off_costs_total'], sym)} (risk-adjusted {_money(a['one_off_costs_total'], sym)}); "
        f"run-rate savings {_money(n['run_rate_savings_total'], sym)} (risk-adjusted {_money(a['run_rate_savings_total'], sym)})."
    )
    for label, sc in (("As stated", n), ("Risk-adjusted", a)):
        pb = sc["payback"]
        text = f"month {pb['month']}" if pb["month"] is not None else pb["status"]
        print(f"{label}: payback {text}; three-year net {_money(sc['three_year_net'], sym)}.")
    print(f"Wrote {out_dir / 'synergy-summary.md'} and {out_dir / 'synergy.json'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dd_playbook",
        description="IT due diligence aids: assessment template, scoring and a synergy model.",
    )
    parser.add_argument("--version", action="version", version=f"dd_playbook {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{template,score,synergy}")

    t = sub.add_parser("template", help="write a blank assessment CSV from the question bank")
    t.add_argument("--bank", help="question bank CSV (default: data/question-bank.csv)")
    t.add_argument("--out", default="assessment.csv", help="file to write (default: assessment.csv)")
    t.add_argument("--worksheet", action="store_true", help="include question text, red-flag condition and weight for use while interviewing")
    t.add_argument("--force", action="store_true", help="overwrite an existing file")
    t.set_defaults(func=cmd_template)

    s = sub.add_parser("score", help="score a completed assessment")
    s.add_argument("assessment", help="completed assessment CSV")
    s.add_argument("--bank", help="question bank CSV (default: data/question-bank.csv)")
    s.add_argument("--config", help="JSON file overriding RAG thresholds and red-flag rules")
    s.add_argument("--out", default="dd-output", help="output folder (default: dd-output)")
    s.add_argument("--target", help="target company name for the summary heading")
    s.add_argument("--acquirer", help="acquirer name for the summary heading")
    s.set_defaults(func=cmd_score)

    y = sub.add_parser("synergy", help="compute totals, payback and a three-year view from a synergy CSV")
    y.add_argument("file", help="synergy CSV with columns item, type, amount, year, confidence")
    y.add_argument("--assumptions", help="JSON file overriding confidence factors and the savings start month")
    y.add_argument("--savings-start-month", type=int, help="month of the stated year in which run-rate savings begin, 1 to 12 (default 7)")
    y.add_argument("--currency", default="£", help="currency symbol for the output (default: pound sign)")
    y.add_argument("--title", help="title for the summary")
    y.add_argument("--out", default="dd-output", help="output folder (default: dd-output)")
    y.set_defaults(func=cmd_synergy)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except InputError as exc:
        print(exc.format(), file=sys.stderr)
        return EXIT_INPUT_ERROR
    except BrokenPipeError:  # pragma: no cover
        return 0
    except OSError as exc:
        print(f"Error: could not write output: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR
