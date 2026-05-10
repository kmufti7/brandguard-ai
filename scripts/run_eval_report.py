"""Generate the eval reports by running the harness against the full golden dataset.

Q1 split (DJ-008): two output artifacts.

  docs/eval_report_deterministic.md   commit-stable. Deterministic metrics
                                      only (context precision/recall,
                                      citation existence, brand voice
                                      alignment, throughput/latency).

  eval_output/eval_report_llm.md      gitignored. LLM-judged metrics
                                      (faithfulness, answer relevance) plus
                                      the per-scenario table. Regenerates on
                                      demand; scores drift with model
                                      variance.

CLI:
    --deterministic-only   only the committed report
    --llm-only             only the gitignored report
    --both                 default; both files plus the legacy combined
                           docs/session4_eval_report.md historical artifact

Each scenario triggers up to four LLM calls under --both: filter extraction,
RAG generation (unless `injected_copy` is set), faithfulness judge,
relevance judge. ~20 scenarios totals roughly 60-80 API calls. Haiku 4.5.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brandguard.agents.rag_copy_generation import build_index
from brandguard.eval.eval_harness import (
    aggregate_timings,
    averages,
    load_golden_dataset,
    score_scenario,
)
from brandguard.llm import default_complete, make_dispatch_llm
from brandguard.workflow import WorkflowDeps, cleanup_worm_db, run_workflow

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_REPORT_PATH = REPO_ROOT / "docs" / "session4_eval_report.md"
DETERMINISTIC_REPORT_PATH = REPO_ROOT / "docs" / "eval_report_deterministic.md"
LLM_REPORT_PATH = REPO_ROOT / "eval_output" / "eval_report_llm.md"
DB_PATH = "brandguard_worm_eval.db"

DEFAULT_BRIEF = (
    "Write a brief promotional message for the matched audience. Keep it under "
    "120 words and follow Strand Wireless brand voice."
)


def _llm_for_scenario(scenario: dict[str, Any]):
    injected = scenario.get("injected_copy")
    if not injected:
        return default_complete

    def _dispatch(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        if "copy generator" in system_prompt:
            return injected
        return default_complete(system_prompt, user_prompt, max_tokens)

    return _dispatch


def _run_one(
    scenario: dict[str, Any], faiss_index, skip_llm_judged: bool
) -> dict[str, Any]:
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
    score = score_scenario(
        scenario,
        workflow_result,
        llm=default_complete,
        skip_llm_judged=skip_llm_judged,
    )
    cleanup_worm_db(DB_PATH)
    return {
        "scenario": scenario,
        "score": score,
        "kill_switch_triggered": workflow_result.get("kill_switch_triggered", False),
        "node_timings_ms": dict(workflow_result.get("node_timings_ms") or {}),
    }


def _fmt(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "n/a"


def _fmt_avg(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _write_deterministic_report(rows, avg, timing_summary, scenario_count) -> None:
    DETERMINISTIC_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# BrandGuard AI: Eval Report (Deterministic, commit-stable)\n")
    lines.append(
        "Committed artifact (Q1 split per DJ-008). Deterministic metrics only. "
        f"Run against the full golden dataset ({scenario_count} scenarios). "
        "Scores are byte-identical across runs."
    )
    lines.append("")
    lines.append("## Per-metric averages (deterministic)\n")
    lines.append("| Metric | Average | Notes |")
    lines.append("|--------|---------|-------|")
    lines.append(
        f"| context_precision | {_fmt_avg(avg['context_precision'])} | retrieved ∩ expected / retrieved |"
    )
    lines.append(
        f"| context_recall | {_fmt_avg(avg['context_recall'])} | retrieved ∩ expected / expected |"
    )
    lines.append(
        f"| citation_existence | {_fmt_avg(avg['citation_existence'])} | mirrors gate's citation existence rule |"
    )
    lines.append(
        f"| brand_voice_alignment | {_fmt_avg(avg['brand_voice_alignment'])} | em dashes, intensifiers, autopay/unlimited disclosures, numbers |"
    )
    lines.append("")
    lines.append("## Throughput and Latency (D4)\n")
    lines.append("| Node | Avg (ms) | p95 (ms) | n |")
    lines.append("|------|----------|----------|---|")
    for node_name, stats in timing_summary["per_node"].items():
        lines.append(
            f"| {node_name} | {stats['avg_ms']:.1f} | {stats['p95_ms']:.1f} | {stats['n']} |"
        )
    lines.append("")
    lines.append(
        f"- Per-scenario average total latency: **{timing_summary['per_scenario_total_avg_ms']:.1f} ms**"
    )
    lines.append(
        f"- Throughput: **{timing_summary['throughput_per_minute']:.2f} scenarios/minute**"
    )
    lines.append(
        f"- Wall-clock runtime: **{timing_summary['wall_clock_seconds']:.2f} s** for "
        f"{timing_summary['scenario_count']} scenarios"
    )
    lines.append("")
    lines.append("## Gate decision breakdown (deterministic)\n")
    lines.append("| ID | Expected | Observed | KS |")
    lines.append("|----|----------|----------|----|")
    for row in rows:
        s = row["scenario"]
        sc = row["score"]
        lines.append(
            f"| {s['id']} | {s['expected_gate_decision']} | {str(sc['gate_decision'] or 'n/a')} | "
            f"{'YES' if row['kill_switch_triggered'] else 'no'} |"
        )
    lines.append("")
    lines.append(
        f"_Environment: Python {platform.python_version()}, machine "
        f"{platform.machine()}._"
    )
    lines.append("")
    DETERMINISTIC_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {DETERMINISTIC_REPORT_PATH.relative_to(Path.cwd())}")


def _write_llm_report(rows, avg) -> None:
    LLM_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# BrandGuard AI: Eval Report (LLM-judged, regenerable)\n")
    lines.append(
        "Regenerable artifact (Q1 split per DJ-008). LLM-judged metrics drift "
        "run-to-run because of model variance. Not committed; "
        f"file lives under `eval_output/` (gitignored). Generated: `{datetime.now(timezone.utc).isoformat()}`."
    )
    lines.append("")
    lines.append("## Per-metric averages (LLM-judged)\n")
    lines.append("| Metric | Average | Notes |")
    lines.append("|--------|---------|-------|")
    lines.append(
        f"| faithfulness | {_fmt_avg(avg['faithfulness'])} | ragas semantics, Claude Haiku 4.5 judge |"
    )
    lines.append(
        f"| answer_relevance | {_fmt_avg(avg['answer_relevance'])} | ragas semantics, Claude Haiku 4.5 judge |"
    )
    lines.append("")
    lines.append("## Per-scenario breakdown (full)\n")
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
    LLM_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {LLM_REPORT_PATH.relative_to(Path.cwd())}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BrandGuard AI eval report runner (Q1 split)"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--deterministic-only",
        action="store_true",
        help="Run only deterministic metrics; writes docs/eval_report_deterministic.md.",
    )
    mode.add_argument(
        "--llm-only",
        action="store_true",
        help="Run LLM-judged metrics too; writes eval_output/eval_report_llm.md (gitignored).",
    )
    mode.add_argument(
        "--both",
        action="store_true",
        help="Default. Writes both report files.",
    )
    args = parser.parse_args()

    if args.deterministic_only:
        run_deterministic, run_llm = True, False
    elif args.llm_only:
        run_deterministic, run_llm = False, True
    else:
        run_deterministic, run_llm = True, True

    scenarios = load_golden_dataset()
    faiss_index = build_index()
    skip_llm_judged = not run_llm

    wall_start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        rows.append(_run_one(scenario, faiss_index, skip_llm_judged=skip_llm_judged))
    wall_elapsed = time.perf_counter() - wall_start

    avg = averages([r["score"] for r in rows])
    timing_summary = aggregate_timings(
        [r["node_timings_ms"] for r in rows], wall_elapsed
    )

    if run_deterministic:
        _write_deterministic_report(rows, avg, timing_summary, len(scenarios))
    if run_llm:
        _write_llm_report(rows, avg)


if __name__ == "__main__":
    main()
