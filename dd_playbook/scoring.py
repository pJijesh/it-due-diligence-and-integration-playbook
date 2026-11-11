"""Weighted scoring, RAG status and the red-flag register."""

from __future__ import annotations

from .assessment import Answer
from .bank import Question, domains_in_order

RAG_ORDER = {"GREEN": 2, "AMBER": 1, "RED": 0}
SEVERITY_BY_WEIGHT = {5: "Critical", 4: "High", 3: "Medium", 2: "Low", 1: "Low"}
SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def effective_score(answer: Answer, cap: int | None) -> int | None:
    """The score used in the maths: unevidenced answers are capped."""
    if answer.score is None:
        return None
    if cap is not None and not answer.evidence_seen:
        return min(answer.score, cap)
    return answer.score


def rag_for(score: float, cfg: dict) -> str:
    rag = cfg["rag"]
    if score >= rag["green_min"]:
        return "GREEN"
    if score >= rag["amber_min"]:
        return "AMBER"
    return "RED"


def _percent(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def red_flag_triggers(q: Question, answer: Answer, eff: int, cfg: dict) -> list[str]:
    rf = cfg["red_flags"]
    reasons: list[str] = []
    if q.weight >= rf["high_weight"] and eff <= rf["low_score"]:
        reasons.append(f"high-weight item (weight {q.weight}) with a low score ({eff})")
    if answer.score == 0 and q.weight >= rf["zero_score_min_weight"]:
        reasons.append("scored 0, so the red-flag condition applies")
    if answer.red_flag:
        reasons.append("assessor marked the red-flag condition as observed")
    return reasons


def score_assessment(
    questions: list[Question],
    answers: dict[str, Answer],
    cfg: dict,
    missing_ids: list[str] | None = None,
) -> dict:
    """Compute the full result as a JSON-ready dictionary (no I/O)."""
    cap = cfg["unevidenced_score_cap"]
    critical_weight = cfg["critical_weight"]
    by_domain: dict[str, list[Question]] = {}
    for q in questions:
        by_domain.setdefault(q.domain, []).append(q)

    domain_results = []
    flags = []
    unevidenced = []
    total_weight = sum(q.weight for q in questions)
    answered_weight = 0
    earned_all = 0.0
    answered_count = 0
    scored_but_unevidenced = 0

    for domain in domains_in_order(questions):
        qs = by_domain[domain]
        d_total = sum(q.weight for q in qs)
        d_answered = 0
        d_earned = 0.0
        d_count = 0
        d_flags = []
        for q in qs:
            ans = answers.get(q.id)
            if ans is None or ans.score is None:
                continue
            eff = effective_score(ans, cap)
            d_answered += q.weight
            d_earned += q.weight * eff / 4
            d_count += 1
            if not ans.evidence_seen:
                scored_but_unevidenced += 1
                if q.weight >= cfg["red_flags"]["high_weight"]:
                    unevidenced.append(
                        {
                            "id": q.id,
                            "domain": q.domain,
                            "weight": q.weight,
                            "answer_score": ans.score,
                            "effective_score": eff,
                            "question": q.question,
                            "evidence_to_request": q.evidence_to_request,
                        }
                    )
            reasons = red_flag_triggers(q, ans, eff, cfg)
            if reasons:
                flag = {
                    "id": q.id,
                    "domain": q.domain,
                    "severity": SEVERITY_BY_WEIGHT[q.weight],
                    "weight": q.weight,
                    "answer_score": ans.score,
                    "effective_score": eff,
                    "evidence_seen": ans.evidence_seen,
                    "triggers": reasons,
                    "question": q.question,
                    "red_flag_if": q.red_flag_if,
                    "notes": ans.notes,
                }
                flags.append(flag)
                d_flags.append(flag)
        answered_weight += d_answered
        earned_all += d_earned
        answered_count += d_count
        coverage = d_answered / d_total if d_total else 0.0
        score = _percent(d_earned, d_answered)
        critical = [f for f in d_flags if f["weight"] >= critical_weight]
        if d_count == 0:
            rag = "NOT ASSESSED"
        elif coverage < cfg["min_coverage"]:
            rag = "INSUFFICIENT DATA"
        else:
            rag = rag_for(score, cfg)
            if rag == "GREEN" and critical and cfg["cap_green_on_critical_flag"]:
                rag = "AMBER"
        domain_results.append(
            {
                "domain": domain,
                "questions": len(qs),
                "answered": d_count,
                "coverage_pct": round(100 * coverage, 1),
                "score": round(score, 1) if d_count else None,
                "rag": rag,
                "red_flags": len(d_flags),
                "critical_red_flags": len(critical),
            }
        )

    overall_score = _percent(earned_all, answered_weight)
    overall_coverage = answered_weight / total_weight if total_weight else 0.0
    critical_all = [f for f in flags if f["weight"] >= critical_weight]
    if overall_coverage < cfg["min_coverage"]:
        overall_rag = "INSUFFICIENT DATA"
    else:
        overall_rag = rag_for(overall_score, cfg)
        if overall_rag == "GREEN" and critical_all and cfg["cap_green_on_critical_flag"]:
            overall_rag = "AMBER"

    flags.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["effective_score"], f["id"]))
    unevidenced.sort(key=lambda u: (-u["weight"], u["id"]))

    return {
        "overall": {
            "score": round(overall_score, 1),
            "rag": overall_rag,
            "questions_in_bank": len(questions),
            "questions_answered": answered_count,
            "coverage_pct": round(100 * overall_coverage, 1),
            "red_flags": len(flags),
            "critical_red_flags": len(critical_all),
            "answers_without_evidence": scored_but_unevidenced,
        },
        "domains": domain_results,
        "red_flags": flags,
        "unevidenced_high_weight": unevidenced,
        "not_in_assessment_file": sorted(missing_ids or []),
        "settings": cfg,
    }
