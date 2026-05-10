"""D4 timing tests.

Two assertions:
  - The workflow result surfaces a `node_timings_ms` dict with non-negative
    floats for every executed node.
  - The aggregation logic in `eval_harness.aggregate_timings` computes
    averages, p95, and throughput correctly on a small mocked input.
"""

from __future__ import annotations

import json
from pathlib import Path

from brandguard.agents.rag_copy_generation import build_index
from brandguard.eval.eval_harness import aggregate_timings
from brandguard.llm import make_dispatch_llm
from brandguard.workflow import WorkflowDeps, cleanup_worm_db, run_workflow

_TINY_CORPUS = [
    {
        "customer_id": "1",
        "first_name": "A",
        "last_name": "X",
        "email": "a@x.example",
        "state": "CA",
        "age_bracket": "25-34",
        "tenure_months": 24,
        "current_sku": "Business",
        "monthly_data_gb": 45.0,
        "international_usage": True,
        "hotspot_usage": True,
        "autopay_enrolled": True,
        "household_size": 1,
        "churn_risk": "low",
        "lifetime_value_usd": 1500.0,
        "acquisition_channel": "online",
        "last_support_contact_days_ago": 10,
    }
]


def _allow_path_mock_llm():
    filter_reply = json.dumps({"state": ["CA"], "sku": ["Business"]})
    copy_reply = (
        "COPY:\n"
        "Strand Business: $55.00 per line per month with autopay. "
        "[fact_sheet:business:price]\n\n"
        "CITATIONS:\n"
        "- [fact_sheet:business:price]\n"
    )
    return make_dispatch_llm(
        default=copy_reply,
        dispatch={"filter extractor": filter_reply, "copy generator": copy_reply},
    )


def test_workflow_returns_node_timings(tmp_path: Path):
    """Each executed node populates a non-negative float in node_timings_ms."""
    db_path = str(tmp_path / "timing.db")
    deps = WorkflowDeps(
        llm=_allow_path_mock_llm(),
        corpus=_TINY_CORPUS,
        faiss_index=build_index(),
        worm_db_path=db_path,
    )
    try:
        result = run_workflow(
            audience_query="business customers in CA",
            campaign_brief="Promote Strand Business renewal.",
            deps=deps,
        )
    finally:
        cleanup_worm_db(db_path)

    timings = result.get("node_timings_ms")
    assert isinstance(timings, dict), "expected node_timings_ms dict on result"
    expected_nodes = {
        "audience_discovery",
        "rag_copy_generation",
        "legal_brand_review_gate",
    }
    assert expected_nodes.issubset(
        timings.keys()
    ), f"missing nodes: {expected_nodes - timings.keys()}"
    for node, value in timings.items():
        assert isinstance(
            value, float
        ), f"{node} timing is {type(value).__name__}, expected float"
        assert value >= 0.0, f"{node} timing went negative: {value}"

    # The same elapsed_ms values are also persisted in the WORM TOOL_EXECUTED exit payloads.
    exit_payloads = [
        json.loads(e["payload"])
        for e in result["worm_chain"]
        if e["event_type"] == "TOOL_EXECUTED"
        and json.loads(e["payload"]).get("phase") == "exit"
    ]
    nodes_with_elapsed = {p["node"] for p in exit_payloads if "elapsed_ms" in p}
    assert nodes_with_elapsed == expected_nodes


def test_aggregate_timings_computes_averages_p95_and_throughput():
    """Mocked per-scenario timings produce the expected aggregate shape."""
    per_scenario = [
        {
            "audience_discovery": 100.0,
            "rag_copy_generation": 1000.0,
            "legal_brand_review_gate": 1.0,
        },
        {
            "audience_discovery": 200.0,
            "rag_copy_generation": 1500.0,
            "legal_brand_review_gate": 2.0,
        },
        {
            "audience_discovery": 300.0,
            "rag_copy_generation": 2000.0,
            "legal_brand_review_gate": 3.0,
        },
        {
            "audience_discovery": 400.0,
            "rag_copy_generation": 2500.0,
            "legal_brand_review_gate": 4.0,
        },
    ]
    summary = aggregate_timings(per_scenario, wall_clock_seconds=12.0)

    # Averages: simple arithmetic mean.
    assert summary["per_node"]["audience_discovery"]["avg_ms"] == 250.0
    assert summary["per_node"]["rag_copy_generation"]["avg_ms"] == 1750.0
    assert summary["per_node"]["legal_brand_review_gate"]["avg_ms"] == 2.5

    # n is the count of scenarios that executed each node.
    for node in (
        "audience_discovery",
        "rag_copy_generation",
        "legal_brand_review_gate",
    ):
        assert summary["per_node"][node]["n"] == 4

    # p95 with 4 points and linear-interp percentile: rank = 0.95 * 3 = 2.85 between idx 2 and 3.
    # audience_discovery sorted = [100, 200, 300, 400]; p95 = 300 + 0.85 * (400-300) = 385.0
    assert abs(summary["per_node"]["audience_discovery"]["p95_ms"] - 385.0) < 1e-9

    # Throughput: 4 scenarios / 12 s * 60 = 20.0 per minute.
    assert summary["throughput_per_minute"] == 20.0
    assert summary["wall_clock_seconds"] == 12.0
    assert summary["scenario_count"] == 4

    # Per-scenario total avg = mean of (1101, 1702, 2303, 2904) = 2002.5
    assert abs(summary["per_scenario_total_avg_ms"] - 2002.5) < 1e-9
