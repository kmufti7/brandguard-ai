"""Eval harness tests.

Covers:
  - Deterministic metrics: citation existence (ALLOW + BLOCK paths), brand voice
    alignment (clean vs known-violating sample), context precision/recall.
  - Golden dataset structural integrity (every scenario has every required key,
    BLOCK scenarios name a failed rule).
  - LLM-judged metric callable surface (interface only; mocked, no API calls).
  - End-to-end eval: run harness against 3 golden scenarios, assert non-null
    score report.
"""

from __future__ import annotations

import json
from pathlib import Path

from brandguard.eval.eval_harness import (
    answer_relevance_score,
    brand_voice_alignment,
    citation_existence_score,
    context_precision_recall,
    faithfulness_score,
    load_golden_dataset,
    score_scenario,
)
from brandguard.llm import make_static_llm

GOLDEN = load_golden_dataset()
REQUIRED_KEYS = {
    "id",
    "audience_query",
    "expected_filter",
    "expected_anchor_pool",
    "expected_gate_decision",
    "expected_failed_rules",
    "notes",
}


def test_citation_existence_score_allow_and_block_paths():
    score_clean = citation_existence_score(
        citations=["[fact_sheet:pro:price]", "[fact_sheet:pro:data]"],
        copy_text="Strand Pro is $45 with autopay. [fact_sheet:pro:price]",
    )
    assert score_clean == 1.0

    score_hallucinated = citation_existence_score(
        citations=["[fact_sheet:fake_sku:price]"],
        copy_text="copy referencing [fact_sheet:fake_sku:price]",
    )
    assert score_hallucinated == 0.0

    score_partial = citation_existence_score(
        citations=["[fact_sheet:pro:price]", "[fact_sheet:fake:fake]"],
        copy_text="",
    )
    assert score_partial == 0.5


def test_brand_voice_alignment_flags_known_violations():
    """A copy sample that triples up on principle violations must score low and list them."""
    # The em dash is constructed via escape to keep this test file clean against
    # the global em-dash grep. The eval harness still detects U+2014 in copy.
    em_dash = chr(0x2014)
    bad_copy = (
        f"Get our amazing Strand Pro plan for $45 a month{em_dash}best-in-class value with "
        "unlimited data, no contracts."
    )
    result = brand_voice_alignment(bad_copy)
    assert result.score < 1.0
    joined = " ".join(result.violations)
    assert "em dash" in joined
    assert "amazing" in joined or "best-in-class" in joined
    assert "autopay disclosure missing" in joined
    assert "unlimited" in joined.lower()


def test_brand_voice_alignment_clean_copy_scores_one():
    clean_copy = (
        "Strand Pro is $45 per line per month with autopay. 50 GB of high-speed "
        "data, then 1 Mbps. [fact_sheet:pro:price] [fact_sheet:pro:data]"
    )
    result = brand_voice_alignment(clean_copy)
    assert result.score == 1.0
    assert result.violations == []


def test_context_precision_recall_set_math():
    pr = context_precision_recall(
        retrieved_anchors=[
            "[fact_sheet:pro:price]",
            "[fact_sheet:pro:data]",
            "[brand_voice:§4]",
        ],
        expected_anchor_pool=["[fact_sheet:pro:price]", "[fact_sheet:pro:data]"],
    )
    # 2 of 3 retrieved are in expected = 2/3 precision; both expected are retrieved = 1.0 recall.
    assert abs(pr["context_precision"] - 2 / 3) < 1e-9
    assert pr["context_recall"] == 1.0


def test_golden_dataset_structural_integrity():
    """Every scenario has every required key. BLOCK scenarios name at least one failed rule."""
    assert len(GOLDEN) >= 20, f"Need >=20 scenarios, got {len(GOLDEN)}"
    for scenario in GOLDEN:
        missing = REQUIRED_KEYS - set(scenario.keys())
        assert not missing, f"{scenario.get('id')} missing keys: {missing}"
        if scenario["expected_gate_decision"] == "BLOCK":
            assert scenario[
                "expected_failed_rules"
            ], f"BLOCK scenario {scenario['id']} must name at least one failed rule"


def test_llm_judged_metrics_use_injected_llm():
    """Faithfulness and answer-relevance accept a callable LLM and parse JSON correctly."""
    mock = make_static_llm('{"score": 0.85, "explanation": "ok"}')
    f = faithfulness_score(
        "Strand Pro is $45 with autopay.", ["pro price chunk"], llm=mock
    )
    r = answer_relevance_score(
        "Pro pricing", "Strand Pro is $45 with autopay.", llm=mock
    )
    assert f == 0.85
    assert r == 0.85


def test_score_scenario_against_three_golden_items_with_mocked_workflow_results():
    """End-to-end eval: 3 golden scenarios, mocked workflow_result, assert score report shape."""
    selected = [s for s in GOLDEN if s["id"] in ("G001", "G002", "G005")]
    assert len(selected) == 3

    # Mocked workflow_result shaped like the real run_workflow output.
    def _mock_result(scenario):
        return {
            "final_state": {
                "audience_filter": scenario["expected_filter"],
                "matched_records": [],
                "generated_copy": (
                    "Strand "
                    f"{scenario['expected_filter'].get('sku', ['Pro'])[0]} "
                    "with autopay. [fact_sheet:pro:price]"
                ),
                "citations": ["[fact_sheet:pro:price]"],
                "retrieved_chunks": [
                    {"anchor": a} for a in scenario["expected_anchor_pool"]
                ],
                "gate_decision": "ALLOW",
                "gate_reasons": [],
            },
            "kill_switch_triggered": False,
        }

    rows = [score_scenario(s, _mock_result(s), skip_llm_judged=True) for s in selected]
    assert len(rows) == 3
    for row in rows:
        assert row["scenario_id"] in {"G001", "G002", "G005"}
        # Deterministic metrics always populate.
        assert isinstance(row["context_precision"], float)
        assert isinstance(row["context_recall"], float)
        assert isinstance(row["citation_existence"], float)
        assert isinstance(row["brand_voice_alignment"], float)
        # LLM-judged metrics are None when skipped.
        assert row["faithfulness"] is None
        assert row["answer_relevance"] is None
