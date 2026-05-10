"""Hallucination + brand-voice evaluation harness.

Five metrics, intentionally split between LLM-judged and deterministic:

  LLM-judged (uses the same Anthropic client as the agents):
    1. faithfulness_score          ragas semantics: every claim in the generated
                                   copy is grounded in the retrieved context.
    2. answer_relevance_score      ragas semantics: the copy answers the audience
                                   query intent.

  Deterministic (no LLM):
    3. context_precision_recall    set-based comparison of retrieved anchors vs
                                   the scenario's expected_anchor_pool. Returns
                                   precision and recall (both in [0,1]).
    4. citation_existence_score    every cited anchor must exist in the RAG
                                   sources (collect_known_anchors). Hallucinated
                                   anchors fail. This is the same check the gate
                                   uses at release time, exposed as a metric so
                                   regression on the gate's input is observable.
    5. brand_voice_alignment       deterministic principle-adherence check
                                   against the rules we can encode mechanically:
                                   no em dashes, no filler intensifiers from a
                                   stoplist, autopay disclosure when an autopay
                                   price is quoted, unlimited disclosure when
                                   the word `unlimited` appears.

Why the split: ragas's faithfulness and answer_relevance use LLM-as-judge under
the hood (DNA §8 says LLM judgment is fine for offline evaluation but never
for release-gating). The deterministic metrics mirror the gate's semantics and
are reproducible across runs, models, and tokens.

The brand voice metric is intentionally deterministic, not rubric-scored. A
rubric ("does this sound on-brand?") would re-introduce LLM judgment for a
question we can answer in code; that would be less honest. Principles that
cannot be encoded mechanically (e.g., §3 personality traits) are not scored
here. They remain the human reviewer's domain.

Output schema (per scenario):

    {
      "scenario_id": "G001",
      "faithfulness": float in [0,1] | None,
      "answer_relevance": float in [0,1] | None,
      "context_precision": float in [0,1],
      "context_recall": float in [0,1],
      "citation_existence": float in [0,1],
      "brand_voice_alignment": float in [0,1],
      "brand_voice_violations": list[str],
      "gate_decision": "ALLOW" | "BLOCK",
      "gate_failed_rules": list[str],
      "kill_switch_triggered": bool,
    }
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brandguard.agents.rag_copy_generation import collect_known_anchors
from brandguard.llm import LLMCall, default_complete

GOLDEN_DATASET_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "golden_dataset.json"
)


# ----- Deterministic metrics -----


def context_precision_recall(
    retrieved_anchors: list[str],
    expected_anchor_pool: list[str],
) -> dict[str, float]:
    """Set-based precision/recall on retrieval anchors.

    precision = |retrieved ∩ expected| / |retrieved|
    recall    = |retrieved ∩ expected| / |expected|

    Returns 1.0 for the empty-numerator case (no retrieved or no expected).
    """
    retrieved = set(retrieved_anchors)
    expected = set(expected_anchor_pool)
    intersect = retrieved & expected
    precision = len(intersect) / len(retrieved) if retrieved else 1.0
    recall = len(intersect) / len(expected) if expected else 1.0
    return {"context_precision": precision, "context_recall": recall}


def citation_existence_score(
    citations: list[str],
    copy_text: str,
    known_anchors: set[str] | None = None,
) -> float:
    """1.0 if every cited and inline anchor exists in the RAG sources, else
    a partial score = (existing / total). 1.0 if no anchors at all.
    """
    if known_anchors is None:
        known_anchors = collect_known_anchors()
    inline = re.findall(r"\[(?:brand_voice|fact_sheet):[^\]]+\]", copy_text)
    all_anchors = set(citations) | set(inline)
    if not all_anchors:
        return 1.0
    existing = sum(1 for a in all_anchors if a in known_anchors)
    return existing / len(all_anchors)


# Filler intensifiers banned by brand_voice.md §4 rule 3.
_FILLER_INTENSIFIERS = [
    "amazing",
    "incredible",
    "best-in-class",
    "world-class",
    "next-generation",
    "cutting-edge",
    "revolutionary",
]

# Autopay-required prices from product_fact_sheet.md.
_AUTOPAY_PRICES = (25, 35, 45, 55, 70)
_AUTOPAY_DISCLOSURE_RE = re.compile(
    r"(with\s+autopay|autopay\s+required|autopay\s+enroll)",
    re.IGNORECASE,
)
_UNLIMITED_RE = re.compile(r"\bunlimited\b", re.IGNORECASE)
_SOFTCAP_RE = re.compile(r"100\s*GB", re.IGNORECASE)
_POSTCAP_RE = re.compile(r"5\s*Mbps", re.IGNORECASE)
_EM_DASH = chr(0x2014)


@dataclass
class BrandVoiceResult:
    score: float
    violations: list[str] = field(default_factory=list)


def brand_voice_alignment(copy_text: str) -> BrandVoiceResult:
    """Deterministic checks against the principles we can encode in code.

    Each violation deducts a fixed amount from a starting score of 1.0.
    Five mechanically-encodable principles:
      §4.2 Unlimited disclosure
      §4.3 No filler intensifiers
      §4.6 Numbers belong in copy (heuristic: at least one digit if pricing/data context)
      §4.8 No em dashes
      Autopay disclosure (cross-SKU note in fact sheet)
    """
    violations: list[str] = []

    # §4.8 em dashes
    if _EM_DASH in copy_text:
        violations.append("§4.8 em dash present")

    # §4.3 filler intensifiers
    lower = copy_text.lower()
    for word in _FILLER_INTENSIFIERS:
        if word in lower:
            violations.append(f"§4.3 filler intensifier '{word}'")

    # autopay disclosure
    quoted_autopay = [
        p for p in _AUTOPAY_PRICES if re.search(rf"\${p}(?:\.\d{{2}})?\b", copy_text)
    ]
    if quoted_autopay and not _AUTOPAY_DISCLOSURE_RE.search(copy_text):
        violations.append(f"autopay disclosure missing while quoting ${quoted_autopay}")

    # §4.2 unlimited disclosure (mirrors the gate)
    if _UNLIMITED_RE.search(copy_text):
        if not (_SOFTCAP_RE.search(copy_text) and _POSTCAP_RE.search(copy_text)):
            violations.append(
                "§4.2 'unlimited' without 100 GB soft cap and 5 Mbps post-cap"
            )

    # §4.6 numbers heuristic: if the copy mentions a price/data concept,
    # at least one digit should appear. We only enforce this when the copy
    # uses words like "price", "GB", "Mbps", "month".
    pricing_context = any(
        w in lower for w in ["price", "gb", "mbps", "month", "monthly", "data"]
    )
    if pricing_context and not re.search(r"\d", copy_text):
        violations.append("§4.6 pricing/data context without specific numbers")

    # Score: each violation deducts 0.20, floored at 0.0.
    score = max(0.0, 1.0 - 0.20 * len(violations))
    return BrandVoiceResult(score=score, violations=violations)


# ----- LLM-judged metrics (ragas semantics, locally implemented prompts) -----


_FAITHFULNESS_SYSTEM = """You are an evaluator scoring whether copy is faithful to retrieved context.

Given a copy paragraph and a list of retrieved chunks, return a JSON object:
  {"score": <float 0..1>, "explanation": "<one short sentence>"}

A score of 1.0 means every factual claim in the copy is supported by at least
one retrieved chunk. 0.0 means none of the claims are supported. Stylistic
phrasing is not a claim. Numbers, prices, and product features are claims.

Return ONLY JSON. No prose, no markdown fences.
"""

_RELEVANCE_SYSTEM = """You are an evaluator scoring whether copy answers the audience query intent.

Given an audience query and the generated copy, return a JSON object:
  {"score": <float 0..1>, "explanation": "<one short sentence>"}

A score of 1.0 means the copy directly addresses what the query asked about.
0.0 means the copy is off-topic. Partial relevance scores in between.

Return ONLY JSON. No prose, no markdown fences.
"""


def _parse_score_json(raw: str) -> float | None:
    """Extract a numeric score from an LLM JSON response."""
    start = raw.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(raw[start : i + 1])
                except Exception:
                    return None
                value = obj.get("score")
                if isinstance(value, (int, float)):
                    return max(0.0, min(1.0, float(value)))
                return None
    return None


def faithfulness_score(
    copy_text: str,
    retrieved_chunks: list[str],
    llm: LLMCall | None = None,
) -> float | None:
    """LLM-judged ragas-style faithfulness. Returns None if the call fails."""
    if not copy_text or not retrieved_chunks:
        return None
    if llm is None:
        llm = default_complete
    user_prompt = (
        "Copy:\n"
        + copy_text
        + "\n\nRetrieved chunks:\n"
        + "\n---\n".join(retrieved_chunks)
    )
    try:
        raw = llm(_FAITHFULNESS_SYSTEM, user_prompt, 256)
    except Exception:
        return None
    return _parse_score_json(raw)


def answer_relevance_score(
    audience_query: str,
    copy_text: str,
    llm: LLMCall | None = None,
) -> float | None:
    """LLM-judged ragas-style answer relevance. Returns None if the call fails."""
    if not audience_query or not copy_text:
        return None
    if llm is None:
        llm = default_complete
    user_prompt = f"Audience query:\n{audience_query}\n\nCopy:\n{copy_text}"
    try:
        raw = llm(_RELEVANCE_SYSTEM, user_prompt, 256)
    except Exception:
        return None
    return _parse_score_json(raw)


# ----- Scenario runner -----


def load_golden_dataset(path: Path | str = GOLDEN_DATASET_PATH) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def score_scenario(
    scenario: dict[str, Any],
    workflow_result: dict[str, Any],
    llm: LLMCall | None = None,
    skip_llm_judged: bool = False,
) -> dict[str, Any]:
    """Score one scenario from a workflow_result returned by run_workflow.

    `skip_llm_judged=True` zeroes out the LLM-judged metrics (returning None)
    so eval-tests can run without making API calls. The eval REPORT script
    sets it to False to capture real scores.
    """
    final = workflow_result.get("final_state") or {}
    copy_text = final.get("generated_copy") or ""
    citations = final.get("citations") or []
    retrieved_anchors = [
        c.get("anchor")
        for c in (final.get("retrieved_chunks") or [])
        if c.get("anchor")
    ]
    expected_anchors = scenario.get("expected_anchor_pool", [])

    pr = context_precision_recall(retrieved_anchors, expected_anchors)
    citation_score = citation_existence_score(citations, copy_text)
    bv = brand_voice_alignment(copy_text)

    if skip_llm_judged or not copy_text:
        faithfulness = None
        relevance = None
    else:
        chunk_texts = [a for a in retrieved_anchors]  # use anchor IDs as proxy text
        faithfulness = faithfulness_score(copy_text, chunk_texts, llm=llm)
        relevance = answer_relevance_score(
            scenario.get("audience_query", ""), copy_text, llm=llm
        )

    return {
        "scenario_id": scenario["id"],
        "faithfulness": faithfulness,
        "answer_relevance": relevance,
        "context_precision": pr["context_precision"],
        "context_recall": pr["context_recall"],
        "citation_existence": citation_score,
        "brand_voice_alignment": bv.score,
        "brand_voice_violations": bv.violations,
        "gate_decision": final.get("gate_decision"),
        "gate_failed_rules": final.get("gate_reasons", []),
        "kill_switch_triggered": workflow_result.get("kill_switch_triggered", False),
    }


def averages(score_rows: list[dict[str, Any]]) -> dict[str, float | None]:
    """Per-metric averages across a list of scored scenarios."""

    def _avg(key: str) -> float | None:
        vals = [r[key] for r in score_rows if isinstance(r.get(key), (int, float))]
        return sum(vals) / len(vals) if vals else None

    return {
        "faithfulness": _avg("faithfulness"),
        "answer_relevance": _avg("answer_relevance"),
        "context_precision": _avg("context_precision"),
        "context_recall": _avg("context_recall"),
        "citation_existence": _avg("citation_existence"),
        "brand_voice_alignment": _avg("brand_voice_alignment"),
    }


def _percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile, no numpy dep.

    Returns 0.0 on empty input. ``pct`` is in [0, 100].
    """
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    sorted_vals = sorted(values)
    rank = (pct / 100.0) * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return float(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac)


def aggregate_timings(
    per_scenario_timings: list[dict[str, float]],
    wall_clock_seconds: float,
) -> dict[str, Any]:
    """Aggregate per-node timings across many scenarios into a report-ready summary.

    Inputs:
        per_scenario_timings: one dict per scenario, mapping node_name to elapsed_ms.
                              Scenarios where a node did not execute (e.g. kill-switch
                              trip skipped a node) simply omit that key.
        wall_clock_seconds:   total runtime measured outside the scenarios.

    Returns:
        {
          "per_node": {node_name: {"avg_ms": float, "p95_ms": float, "n": int}},
          "per_scenario_total_avg_ms": float,
          "throughput_per_minute": float,
          "wall_clock_seconds": float,
          "scenario_count": int,
        }
    """
    nodes: set[str] = set()
    for row in per_scenario_timings:
        nodes.update(row.keys())

    per_node: dict[str, dict[str, float]] = {}
    for node in sorted(nodes):
        vals = [row[node] for row in per_scenario_timings if node in row]
        per_node[node] = {
            "avg_ms": statistics.mean(vals) if vals else 0.0,
            "p95_ms": _percentile(vals, 95.0),
            "n": len(vals),
        }

    per_scenario_totals = [sum(row.values()) for row in per_scenario_timings if row]
    avg_total = statistics.mean(per_scenario_totals) if per_scenario_totals else 0.0
    scenario_count = len(per_scenario_timings)
    throughput = (
        (scenario_count / wall_clock_seconds) * 60.0 if wall_clock_seconds > 0 else 0.0
    )

    return {
        "per_node": per_node,
        "per_scenario_total_avg_ms": avg_total,
        "throughput_per_minute": throughput,
        "wall_clock_seconds": wall_clock_seconds,
        "scenario_count": scenario_count,
    }
