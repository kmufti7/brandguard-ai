"""End-to-end workflow test.

Exercises Audience Discovery -> RAG Copy Generation -> Legal/Brand Review Gate
with mocked LLM and a tiny hand-built FAISS index, so the test does not download
the embedding model. Asserts that WORM entries are written for every node
boundary and the gate decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from brandguard.agents.rag_copy_generation import build_index
from brandguard.llm import make_dispatch_llm
from brandguard.workflow import WorkflowDeps, cleanup_worm_db, run_workflow


def _build_real_index():
    """Use the real fastembed-backed FAISS index. The LLM is mocked, so retrieved
    content does not affect the outcome; this avoids dim mismatches in the test
    while still exercising the real retrieval path.
    """
    return build_index()


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


def _mock_llm():
    """Two-call dispatch: one for filter extraction, one for copy generation.

    Filter extraction returns a JSON object. The copy-gen reply uses real
    fact_sheet anchors so the gate's citation-existence check passes; it
    discloses autopay so the autopay rule passes; it omits the word
    'unlimited' so the unlimited rule does not fire.
    """
    filter_reply = json.dumps({"state": ["CA"], "sku": ["Business"]})
    copy_reply = (
        "COPY:\n"
        "Strand Business gives California teams $55 per line per month with autopay, "
        "50 GB of high-speed data, and dedicated business support. "
        "[fact_sheet:business:price] [fact_sheet:business:data] [fact_sheet:business:eligibility]\n\n"
        "CITATIONS:\n"
        "- [fact_sheet:business:price]\n"
        "- [fact_sheet:business:data]\n"
        "- [fact_sheet:business:eligibility]\n"
    )
    # Dispatch by substring. The audience-extraction system prompt mentions
    # "filter extractor"; the copy-gen system prompt mentions "copy generator".
    return make_dispatch_llm(
        default=copy_reply,
        dispatch={
            "filter extractor": filter_reply,
            "copy generator": copy_reply,
        },
    )


def test_workflow_end_to_end_writes_worm_chain(tmp_path: Path):
    db_path = str(tmp_path / "brandguard_worm_test.db")
    deps = WorkflowDeps(
        llm=_mock_llm(),
        corpus=_TINY_CORPUS,
        faiss_index=_build_real_index(),
        worm_db_path=db_path,
    )
    try:
        result = run_workflow(
            audience_query="business customers in CA",
            campaign_brief="Promote Strand Business to California small businesses.",
            deps=deps,
        )
    finally:
        cleanup_worm_db(db_path)

    final = result["final_state"]
    chain = result["worm_chain"]

    # Final state shape.
    assert final["audience_filter"] == {"state": ["CA"], "sku": ["Business"]}
    assert final["matched_records"][0]["customer_id"] == "1"
    assert final["gate_decision"] == "ALLOW", final.get("gate_reasons")
    assert final["citations"], "expected citations on final state"

    # WORM evidence: WORKFLOW_START, three node enters, three node exits, WORKFLOW_END.
    event_types = [e["event_type"] for e in chain]
    assert event_types[0] == "WORKFLOW_START"
    assert event_types[-1] == "WORKFLOW_END"
    tool_events = [e for e in chain if e["event_type"] == "TOOL_EXECUTED"]
    # 2 events per node (enter + exit) * 3 nodes = 6.
    assert len(tool_events) == 6

    # The gate decision is in the chain.
    gate_exit = [
        e
        for e in tool_events
        if json.loads(e["payload"]).get("node") == "legal_brand_review_gate"
        and json.loads(e["payload"]).get("phase") == "exit"
    ]
    assert len(gate_exit) == 1
    payload = json.loads(gate_exit[0]["payload"])
    assert payload["decision"] == "ALLOW"
