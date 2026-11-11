"""Markdown rendering for the score summary and the synergy summary."""

from __future__ import annotations

DISCLAIMER = (
    "This is a structured diligence aid, not legal, tax or HR advice. Legal, tax, financial and HR "
    "diligence run alongside IT diligence and are out of scope here."
)


def _cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _table(headers: list[str], rows: list[list[object]], align: list[str] | None = None) -> list[str]:
    align = align or ["l"] * len(headers)
    sep = ["---:" if a == "r" else "---" for a in align]
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for r in rows:
        out.append("| " + " | ".join(_cell(c) for c in r) + " |")
    return out


def render_score_summary(result: dict, target: str | None, acquirer: str | None, inputs: dict) -> str:
    o = result["overall"]
    cfg = result["settings"]
    title = f"IT due diligence summary: {target}" if target else "IT due diligence summary"
    lines = [f"# {title}", ""]
    meta = []
    if acquirer:
        meta.append(f"Acquirer: {acquirer}")
    if target:
        meta.append(f"Target: {target}")
    if meta:
        lines += [" | ".join(meta), ""]
    lines += [
        "## Headline",
        "",
        f"- Overall weighted score: **{o['score']:.1f} out of 100**, status **{o['rag']}**.",
        f"- Questions answered: {o['questions_answered']} of {o['questions_in_bank']} "
        f"({o['coverage_pct']:.1f}% of total weight).",
        f"- Red flags: **{o['red_flags']}** ({o['critical_red_flags']} critical).",
        f"- Scored answers without evidence seen: {o['answers_without_evidence']} "
        f"(capped at {cfg['unevidenced_score_cap']} in the maths)."
        if cfg["unevidenced_score_cap"] is not None
        else f"- Scored answers without evidence seen: {o['answers_without_evidence']} (no cap applied).",
        "",
        "## Domain scores",
        "",
    ]
    rows = []
    for d in result["domains"]:
        score = "n/a" if d["score"] is None else f"{d['score']:.1f}"
        rows.append([d["domain"], score, d["rag"], f"{d['answered']} of {d['questions']}", d["red_flags"]])
    lines += _table(["Domain", "Score", "Status", "Answered", "Red flags"], rows, ["l", "r", "l", "r", "r"])
    lines += ["", "## Red-flag register", ""]
    if result["red_flags"]:
        rows = []
        for f in result["red_flags"]:
            rows.append(
                [
                    f["id"],
                    f["severity"],
                    f["question"],
                    "; ".join(f["triggers"]),
                    f["notes"] or "(no notes)",
                ]
            )
        lines += _table(["ID", "Severity", "Question", "Why flagged", "Assessor notes"], rows)
    else:
        lines.append("No red flags were triggered by the scored answers.")
    lines += ["", "## Evidence gaps on high-weight questions", ""]
    if result["unevidenced_high_weight"]:
        lines.append(
            "These answers carry high weight but no evidence was seen, so they are scored on the capped value. "
            "Request the evidence before relying on them."
            if cfg["unevidenced_score_cap"] is not None
            else "These answers carry high weight but no evidence was seen."
        )
        lines.append("")
        rows = [[u["id"], u["answer_score"], u["effective_score"], u["evidence_to_request"]] for u in result["unevidenced_high_weight"]]
        lines += _table(["ID", "Stated score", "Scored as", "Evidence to request"], rows, ["l", "r", "r", "l"])
    else:
        lines.append("None. Every high-weight answer has evidence seen.")
    if result["not_in_assessment_file"]:
        lines += [
            "",
            f"Note: {len(result['not_in_assessment_file'])} question(s) in the bank were not in the assessment file "
            "and are treated as not assessed.",
        ]
    rag = cfg["rag"]
    lines += [
        "",
        "## How this was calculated",
        "",
        "Each answer is scored 0 to 4. A domain score is the weight-averaged score of its answered questions, "
        f"as a percentage. Status is GREEN at {rag['green_min']} or above, AMBER at {rag['amber_min']} or above, "
        "otherwise RED. "
        f"A domain with less than {round(100 * cfg['min_coverage'])}% of its weight answered shows INSUFFICIENT DATA. "
        + (
            "A domain or overall result with a critical red flag cannot be GREEN. "
            if cfg["cap_green_on_critical_flag"]
            else ""
        )
        + "A question is flagged when its weight is "
        f"{cfg['red_flags']['high_weight']} or more and the scored value is {cfg['red_flags']['low_score']} or less, "
        f"when it scores 0 and has weight {cfg['red_flags']['zero_score_min_weight']} or more, or when the assessor marks the red-flag condition as observed.",
        "",
        f"Inputs: assessment SHA-256 `{inputs['assessment_sha256'][:16]}`, question bank SHA-256 `{inputs['bank_sha256'][:16]}`.",
        "",
        DISCLAIMER,
        "",
    ]
    return "\n".join(lines)


def _money(value: float, sym: str) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}{sym}{abs(value):,.0f}"


def _payback_text(pb: dict) -> str:
    if pb["month"] is None:
        return pb["status"]
    year = (pb["month"] - 1) // 12 + 1
    return f"month {pb['month']} (year {year})"


def render_synergy_summary(result: dict, title: str | None, sym: str) -> str:
    n = result["nominal"]
    a = result["risk_adjusted"]
    lines = [f"# {title or 'Synergy and cost summary'}", "", "## Headline", ""]
    rows = [
        ["One-off costs to achieve", _money(n["one_off_costs_total"], sym), _money(a["one_off_costs_total"], sym)],
        ["Run-rate savings (annual, once all in effect)", _money(n["run_rate_savings_total"], sym), _money(a["run_rate_savings_total"], sym)],
        ["Net position after 3 years", _money(n["three_year_net"], sym), _money(a["three_year_net"], sym)],
        ["Payback", _payback_text(n["payback"]), _payback_text(a["payback"])],
    ]
    lines += _table(["Measure", "As stated", "Risk-adjusted"], rows, ["l", "r", "r"])
    lines += ["", "## Three-year view", ""]
    for label, sc in (("As stated", n), ("Risk-adjusted", a)):
        lines += [f"**{label}**", ""]
        rows = [
            [f"Year {y['year']}", _money(y["one_off_costs"], sym), _money(y["savings_realised"], sym), _money(y["net"], sym), _money(y["cumulative_net"], sym)]
            for y in sc["years"]
        ]
        lines += _table(["Year", "One-off costs", "Savings realised", "Net", "Cumulative net"], rows, ["l", "r", "r", "r", "r"])
        lines.append("")
    lines += ["## By confidence", ""]
    rows = [
        [
            c["confidence"],
            c["items"],
            _money(c["one_off_costs"], sym),
            _money(c["risk_adjusted_one_off_costs"], sym),
            _money(c["run_rate_savings"], sym),
            _money(c["risk_adjusted_run_rate_savings"], sym),
        ]
        for c in result["by_confidence"]
    ]
    lines += _table(
        ["Confidence", "Items", "One-off costs", "Costs, adjusted", "Run-rate savings", "Savings, adjusted"],
        rows,
        ["l", "r", "r", "r", "r", "r"],
    )
    lines += ["", "## Observations", ""]
    lines += [f"- {o}" for o in result["observations"]]
    asm = result["assumptions"]
    lines += [
        "",
        "## Assumptions",
        "",
        "One-off costs are spread evenly across the stated year. "
        f"Run-rate savings start in month {asm['savings_start_month']} of the stated year and continue to month 36. "
        "Payback is the month after which the cumulative net position stays at or above zero. "
        "Savings factors: "
        + ", ".join(f"{k} {v:g}" for k, v in asm["savings_factor"].items())
        + ". Cost uplifts (also applied to negative run-rate items, which are extra recurring costs): "
        + ", ".join(f"{k} {v:g}" for k, v in asm["cost_uplift"].items())
        + ". These factors are illustrative assumptions, not benchmarks: set your own.",
        "",
        DISCLAIMER,
        "",
    ]
    return "\n".join(lines)
