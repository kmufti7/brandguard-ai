"""Generate docs/session4_eval_report.md by running the eval harness against
the full golden dataset.

This script makes real Anthropic API calls. Each scenario triggers:
  - 1 audience-discovery LLM call (filter extraction)
  - 1 RAG generation LLM call (unless `injected_copy` is set)
  - 2 ragas-style judge LLM calls (faithfulness, answer_relevance)

For 20 scenarios that totals roughly 60-80 LLM calls. Cost on Haiku is small.

Usage:
    source .venv/bin/activate
    ANTHROPIC_API_KEY=... python scripts/run_eval_report.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brandguard.agents.rag_copy_generation import build_index
from brandguard.eval.eval_harness import (
    averages,
    load_golden_dataset,
    score_scenario,
)
from brandguard.llm import default_complete, make_dispatch_llm
from brandguard.workflow import WorkflowDeps, cleanup_worm_db, run_workflow

REPORT_PATH = Path(__file__).resolve().parents[1] / "docs" / "session4_eval_report.md"
DB_PATH = "brandguard_worm_eval.db"

# A short campaign brief used for every scenario. Eval is comparing scoring
# behavior across audience queries; brief is held constant so brief-driven
# variance does not muddy the metrics.
DEFAULT_BRIEF = (
    "Write a brief promotional message for the matched audience. Keep it under "
    "120 words and follow Strand Wireless brand voice."
)


def _llm_for_scenario(scenario: dict[str, Any]):
    """If a scenario carries `injected_copy`, return a dispatch LLM that returns
    the injected text on copy generation. Filter extraction goes through the
    real LLM regardless. ALLOW scenarios use the real LLM end-to-end.
    """
    injected = scenario.get("injected_copy")
    if not injected:
        return default_complete

    def _dispatch(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        if "copy generator" in system_prompt:
            return injected
        return default_complete(system_prompt, user_prompt, max_tokens)

    return _dispatch


def _run_one(scenario: dict[str, Any], faiss_index) -> dict[str, Any]:
    """Run the workflow + score one scenario."""
    cleanup_worm_db(DB_PATH)
    deps = WorkflowDeps(
        llm=_llm_for_scenario(scenario),
        faiss_index=faiss_index,
        worm_db_path=DB_PATH,
    )
    workflow_result = run_workflow(
        scenario["audience_query"],
        DEFAULT_BRIEF,
        deps=deps,
    )
    # Real LLM-judged metrics on top of the deterministic ones.
    score = score_scenario(
        scenario, workflow_result, llm=default_complete, skip_llm_judged=False
    )
    cleanup_worm_db(DB_PATH)
    return {
        "scenario": scenario,
        "score": score,
        "kill_switch_triggered": workflow_result.get("kill_switch_triggered", False),
    }


def main() -> None:
    scenarios = load_golden_dataset()
    faiss_index = build_index()

    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        rows.append(_run_one(scenario, faiss_index))

    avg = averages([r["score"] for r in rows])

    lines: list[str] = []
    lines.append("# BrandGuard AI: Session 4 Eval Report\n")
    lines.append(
        "Output of `scripts/run_eval_report.py` against the full golden dataset "
        f"({len(scenarios)} scenarios). Scores recomputed live against the real "
        "Anthropic API; deterministic metrics will be byte-identical across runs."
    )
    lines.append(f"\n**Generated:** `{datetime.now(timezone.utc).isoformat()}`\n")

    lines.append("## Per-metric averages\n")
    lines.append("| Metric | Average | Notes |")
    lines.append("|--------|---------|-------|")
    lines.append(
        f"| faithfulness (LLM) | {_fmt_avg(avg['faithfulness'])} | ragas semantics, Claude Haiku 4.5 judge |"
    )
    lines.append(
        f"| answer_relevance (LLM) | {_fmt_avg(avg['answer_relevance'])} | ragas semantics, Claude Haiku 4.5 judge |"
    )
    lines.append(
        f"| context_precision (deterministic) | {_fmt_avg(avg['context_precision'])} | retrieved ∩ expected / retrieved |"
    )
    lines.append(
        f"| context_recall (deterministic) | {_fmt_avg(avg['context_recall'])} | retrieved ∩ expected / expected |"
    )
    lines.append(
        f"| citation_existence (deterministic) | {_fmt_avg(avg['citation_existence'])} | mirrors gate's citation existence rule |"
    )
    lines.append(
        f"| brand_voice_alignment (deterministic) | {_fmt_avg(avg['brand_voice_alignment'])} | em dashes, intensifiers, autopay/unlimited disclosures, numbers in pricing context |"
    )
    lines.append("")

    lines.append("## Per-scenario breakdown\n")
    lines.append(
        "| ID | Expected | Observed | KS | Faith | Rel | Prec | Rec | CitEx | BV | BV violations |"
    )
    lines.append(
        "|----|----------|----------|----|-------|-----|------|-----|-------|----|---------------|"
    )
    for row in rows:
        s = row["scenario"]
        sc = row["score"]
        violations_short = (
            "; ".join(sc["brand_voice_violations"])
            if sc["brand_voice_violations"]
            else ""
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    s["id"],
                    s["expected_gate_decision"],
                    str(sc["gate_decision"] or "n/a"),
                    "YES" if row["kill_switch_triggered"] else "no",
                    _fmt(sc["faithfulness"]),
                    _fmt(sc["answer_relevance"]),
                    _fmt(sc["context_precision"]),
                    _fmt(sc["context_recall"]),
                    _fmt(sc["citation_existence"]),
                    _fmt(sc["brand_voice_alignment"]),
                    violations_short.replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.append("")

    # Identified failures: scenarios where expected != observed (excluding KS where expected=BLOCK and KS triggered).
    lines.append("## Identified mismatches (expected vs observed)\n")
    mismatches: list[dict[str, Any]] = []
    for row in rows:
        s = row["scenario"]
        sc = row["score"]
        expected = s["expected_gate_decision"]
        observed = sc["gate_decision"]
        ks_handled = row["kill_switch_triggered"] and expected == "BLOCK"
        if ks_handled:
            continue
        if expected != observed and observed is not None:
            mismatches.append(
                {"id": s["id"], "expected": expected, "observed": observed}
            )
        elif observed is None and expected != "BLOCK":
            mismatches.append({"id": s["id"], "expected": expected, "observed": "None"})

    if mismatches:
        for m in mismatches:
            lines.append(
                f"- **{m['id']}**: expected `{m['expected']}`, observed `{m['observed']}`"
            )
    else:
        lines.append("None. Every scenario produced the expected gate decision.")
    lines.append("")

    lines.append("## Notes on metric design\n")
    lines.append(
        "- **LLM-judged metrics** (faithfulness, answer_relevance) follow ragas semantics. "
        "They are appropriate for offline regression but never gate releases (per DNA §8)."
    )
    lines.append(
        "- **Deterministic metrics** (context precision/recall, citation existence, brand voice) "
        "produce byte-identical scores across runs and are safe for release-gate comparisons."
    )
    lines.append(
        "- **Brand voice alignment is deterministic, not rubric-scored.** The rules we can encode "
        "in code (em dashes, filler intensifiers, autopay disclosure, unlimited disclosure, numbers "
        "in pricing context) are scored mechanically. Principles that resist mechanical encoding "
        "(§3 personality traits, tone-by-context judgment) are not in this metric: they remain "
        "human-reviewer territory."
    )
    lines.append("")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(Path.cwd())}")


def _fmt(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "n/a"


def _fmt_avg(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
