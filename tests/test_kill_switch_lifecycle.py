"""Kill-switch lifecycle tests (K1).

Asserts the default-armed switch trips on an empty audience query, that the trip
is captured in the WORM chain with no per-node enter/exit pairs, and that a
normal query still flows through to ALLOW (regression).
"""

from __future__ import annotations

import json
from pathlib import Path

from intelliflow_core.v2.runtime.kill_switch import KillSwitchGuard

from brandguard.agents.rag_copy_generation import build_index
from brandguard.llm import make_dispatch_llm
from brandguard.workflow import (
    WorkflowDeps,
    cleanup_worm_db,
    default_kill_switch,
    run_workflow,
)

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


def test_default_kill_switch_trips_on_empty_query(tmp_path: Path):
    """An empty audience query trips the default rule before any LLM call."""
    db_path = str(tmp_path / "ks_trip.db")
    deps = WorkflowDeps(
        llm=_allow_path_mock_llm(),
        corpus=_TINY_CORPUS,
        faiss_index=build_index(),
        worm_db_path=db_path,
    )
    try:
        result = run_workflow(
            audience_query="   ", campaign_brief="anything", deps=deps
        )
    finally:
        cleanup_worm_db(db_path)

    assert result["kill_switch_triggered"] is True
    assert "audience_query_required" in result["failed_rules"]
    assert result["final_state"] is None


def test_kill_switch_trip_writes_clean_worm_chain(tmp_path: Path):
    """When the switch trips, WORM contains START + KILL_SWITCH_TRIGGERED + END.

    No node enter/exit pairs because no node body executed.
    """
    db_path = str(tmp_path / "ks_chain.db")
    deps = WorkflowDeps(
        llm=_allow_path_mock_llm(),
        corpus=_TINY_CORPUS,
        faiss_index=build_index(),
        worm_db_path=db_path,
    )
    try:
        result = run_workflow(audience_query="", campaign_brief="brief", deps=deps)
    finally:
        cleanup_worm_db(db_path)

    chain = result["worm_chain"]
    event_types = [e["event_type"] for e in chain]
    assert event_types == ["WORKFLOW_START", "KILL_SWITCH_TRIGGERED", "WORKFLOW_END"]

    # No TOOL_EXECUTED entries should exist on the chain.
    assert not [e for e in chain if e["event_type"] == "TOOL_EXECUTED"]

    # The KILL_SWITCH_TRIGGERED payload names the failed rule.
    ks_entry = next(e for e in chain if e["event_type"] == "KILL_SWITCH_TRIGGERED")
    payload = json.loads(ks_entry["payload"])
    assert "audience_query_required" in payload["failed_rules"]


def test_normal_query_still_reaches_allow(tmp_path: Path):
    """Regression: armed default switch does not block a non-empty query."""
    db_path = str(tmp_path / "ks_pass.db")
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

    assert result["kill_switch_triggered"] is False
    final = result["final_state"]
    assert final["gate_decision"] == "ALLOW", final.get("gate_reasons")


def test_default_kill_switch_factory_has_one_rule():
    """Sanity: the factory returns a guard with the audience_query_required rule."""
    guard = default_kill_switch()
    assert isinstance(guard, KillSwitchGuard)
    assert [r.rule_id for r in guard.rules] == ["audience_query_required"]
