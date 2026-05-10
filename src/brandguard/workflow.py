"""BrandGuard end-to-end workflow.

Wires three nodes via LangGraph:

    audience_discovery -> rag_copy_generation -> legal_brand_review_gate

Cross-cutting concerns:

  * WORM Logger from intelliflow-core writes at every node boundary
    (enter and exit) and at the final gate decision. The hash chain is
    HMAC-SHA256 with append-only SQLite triggers; chain integrity is
    verifiable end-to-end.

  * Kill-Switch Guard from intelliflow-core is checked on entry to every
    node. The default guard registers one conservative rule:
    `audience_query_required`. Callers can override `WorkflowDeps.kill_switch`
    to disarm the default or add stricter rules. When the switch trips,
    `run_workflow` catches `KillSwitchTriggered`, writes a
    `KILL_SWITCH_TRIGGERED` event to WORM with the failed rule IDs, then a
    final `WORKFLOW_END`, and returns a structured result with
    `kill_switch_triggered=True` instead of propagating the exception.

The workflow is deterministic in its routing: nodes always execute in
order, and the gate decision is always written to WORM regardless of
ALLOW/BLOCK outcome. There is no LLM-judged routing branch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from intelliflow_core.v2.runtime.contracts import GovernanceRule
from intelliflow_core.v2.runtime.exceptions import KillSwitchTriggered
from intelliflow_core.v2.runtime.kill_switch import KillSwitchGuard
from intelliflow_core.v2.runtime.state import IntelliFlowState
from intelliflow_core.v2.storage.db import DatabaseSessionManager
from intelliflow_core.v2.storage.worm_logger import WORMLogRepository
from langgraph.graph import END, StateGraph

from brandguard.agents.audience_discovery import (
    apply_filter,
    extract_filter,
    load_corpus,
)
from brandguard.agents.rag_copy_generation import build_index, generate_copy
from brandguard.governance.legal_brand_review_gate import review
from brandguard.llm import LLMCall
from brandguard.state import BrandGuardState


@dataclass
class WorkflowDeps:
    """Injectable dependencies. Tests can swap LLM, corpus, or storage.

    `kill_switch` defaults to None; if left None, `run_workflow` installs the
    default guard via `default_kill_switch()`. Pass `kill_switch=KillSwitchGuard()`
    explicitly (with no rules) to disarm it.
    """

    llm: LLMCall | None = None
    corpus: list[dict[str, Any]] | None = None
    faiss_index: Any | None = None
    worm_db_path: str = "brandguard_worm.db"
    kill_switch: KillSwitchGuard | None = None


def _audience_query_present(state: IntelliFlowState) -> bool:
    """Default kill-switch rule: audience_query must be a non-empty, non-whitespace string."""
    query = getattr(state, "audience_query", None)
    return isinstance(query, str) and bool(query.strip())


def default_kill_switch() -> KillSwitchGuard:
    """The default armed guard. One conservative rule: non-empty audience query."""
    guard = KillSwitchGuard(name="brandguard_default_kill_switch")
    guard.add_rule(
        GovernanceRule(
            rule_id="audience_query_required",
            description="Audience query must be a non-empty, non-whitespace string.",
            logic=_audience_query_present,
        )
    )
    return guard


def _audience_summary(matched: list[dict[str, Any]]) -> str:
    """One-sentence English summary of the matched audience for the LLM context."""
    if not matched:
        return "Empty audience."
    n = len(matched)
    skus = sorted({r["current_sku"] for r in matched})
    states = sorted({r["state"] for r in matched})
    risks = sorted({r["churn_risk"] for r in matched})
    return (
        f"{n} customers matched, on SKU(s) {', '.join(skus)} in state(s) "
        f"{', '.join(states)}, churn risk {', '.join(risks)}."
    )


def _build_audience_node(deps: WorkflowDeps, worm: WORMLogRepository):
    def node(state: BrandGuardState) -> dict[str, Any]:
        if deps.kill_switch is not None:
            deps.kill_switch.intercept(state)
        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {"node": "audience_discovery", "phase": "enter"},
        )

        if state.audience_query is None:
            raise ValueError("audience_query missing on state")

        corpus = deps.corpus if deps.corpus is not None else load_corpus()
        filter_dict = extract_filter(state.audience_query, llm=deps.llm)
        matched = apply_filter(filter_dict, corpus)

        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {
                "node": "audience_discovery",
                "phase": "exit",
                "filter": filter_dict,
                "match_count": len(matched),
            },
        )
        return {
            "audience_filter": filter_dict,
            "matched_records": matched,
            "step_name": "audience_discovery",
        }

    return node


def _build_copy_node(deps: WorkflowDeps, worm: WORMLogRepository):
    def node(state: BrandGuardState) -> dict[str, Any]:
        if deps.kill_switch is not None:
            deps.kill_switch.intercept(state)
        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {"node": "rag_copy_generation", "phase": "enter"},
        )

        if state.campaign_brief is None:
            raise ValueError("campaign_brief missing on state")

        index = deps.faiss_index if deps.faiss_index is not None else build_index()
        summary = _audience_summary(state.matched_records or [])
        result = generate_copy(
            campaign_brief=state.campaign_brief,
            audience_summary=summary,
            faiss_index=index,
            llm=deps.llm,
        )

        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {
                "node": "rag_copy_generation",
                "phase": "exit",
                "retrieved_anchors": result["retrieved_anchors"],
                "citations": result["citations"],
                "copy_chars": len(result["copy"]),
            },
        )
        return {
            "generated_copy": result["copy"],
            "citations": result["citations"],
            "retrieved_chunks": [{"anchor": a} for a in result["retrieved_anchors"]],
            "step_name": "rag_copy_generation",
        }

    return node


def _build_gate_node(deps: WorkflowDeps, worm: WORMLogRepository):
    def node(state: BrandGuardState) -> dict[str, Any]:
        if deps.kill_switch is not None:
            deps.kill_switch.intercept(state)
        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {"node": "legal_brand_review_gate", "phase": "enter"},
        )

        copy_text = state.generated_copy or ""
        citations = state.citations or []
        decision = review(copy_text, citations)

        # Gate decision is always logged, regardless of ALLOW or BLOCK.
        worm.log_event(
            state.trace_id,
            "TOOL_EXECUTED",
            {
                "node": "legal_brand_review_gate",
                "phase": "exit",
                "decision": decision.decision,
                "failed_rules": decision.failed_rules,
                "reasons": decision.reasons,
            },
        )
        return {
            "gate_decision": decision.decision,
            "gate_reasons": decision.reasons,
            "step_name": "legal_brand_review_gate",
        }

    return node


def build_workflow(deps: WorkflowDeps | None = None):
    """Compile the LangGraph workflow. Returns (compiled_graph, worm_repo, db_manager)."""
    if deps is None:
        deps = WorkflowDeps()

    db = DatabaseSessionManager(deps.worm_db_path)
    worm = WORMLogRepository(db)

    graph = StateGraph(BrandGuardState)
    graph.add_node("audience_discovery", _build_audience_node(deps, worm))
    graph.add_node("rag_copy_generation", _build_copy_node(deps, worm))
    graph.add_node("legal_brand_review_gate", _build_gate_node(deps, worm))

    graph.set_entry_point("audience_discovery")
    graph.add_edge("audience_discovery", "rag_copy_generation")
    graph.add_edge("rag_copy_generation", "legal_brand_review_gate")
    graph.add_edge("legal_brand_review_gate", END)

    return graph.compile(), worm, db


def run_workflow(
    audience_query: str,
    campaign_brief: str,
    deps: WorkflowDeps | None = None,
) -> dict[str, Any]:
    """One-shot entry point. Compiles the graph, runs it, returns final state + WORM chain.

    The default kill-switch is installed automatically when `deps.kill_switch` is None.
    On a tripped switch, the function catches `KillSwitchTriggered`, writes a
    `KILL_SWITCH_TRIGGERED` event to WORM, then a final `WORKFLOW_END`, and returns
    a structured result with `kill_switch_triggered=True` and `final_state=None`.
    """
    if deps is None:
        deps = WorkflowDeps()
    if deps.kill_switch is None:
        deps.kill_switch = default_kill_switch()

    compiled, worm, db = build_workflow(deps)
    initial = BrandGuardState(
        audience_query=audience_query, campaign_brief=campaign_brief
    )
    worm.log_event(initial.trace_id, "WORKFLOW_START", {"trace_id": initial.trace_id})

    try:
        final = compiled.invoke(initial)
    except KillSwitchTriggered as ks:
        failed_rule_ids = [r.rule_id for r in ks.failed_rules]
        failed_descriptions = [r.description for r in ks.failed_rules]
        worm.log_event(
            initial.trace_id,
            "KILL_SWITCH_TRIGGERED",
            {
                "failed_rules": failed_rule_ids,
                "reasons": failed_descriptions,
            },
        )
        worm.log_event(
            initial.trace_id,
            "WORKFLOW_END",
            {"trace_id": initial.trace_id, "status": "kill_switch"},
        )
        chain = worm.get_chain()
        db.close()
        return {
            "final_state": None,
            "trace_id": initial.trace_id,
            "worm_chain": chain,
            "kill_switch_triggered": True,
            "failed_rules": failed_rule_ids,
            "worm_repo": None,
        }

    worm.log_event(initial.trace_id, "WORKFLOW_END", {"trace_id": initial.trace_id})
    chain = worm.get_chain()
    return {
        "final_state": final,
        "trace_id": initial.trace_id,
        "worm_chain": chain,
        "kill_switch_triggered": False,
        "worm_repo": worm,
        "_db": db,
    }


def cleanup_worm_db(path: str = "brandguard_worm.db") -> None:
    """Delete a WORM SQLite file. Used by tests, not production callers."""
    Path(path).unlink(missing_ok=True)
    Path(path + "-wal").unlink(missing_ok=True)
    Path(path + "-shm").unlink(missing_ok=True)
