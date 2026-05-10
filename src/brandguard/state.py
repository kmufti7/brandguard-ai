"""BrandGuard workflow state.

Subclasses IntelliFlowState from intelliflow-core. The shared base provides
workflow_id, step_name, timestamp, metadata, trace_id, plus pydantic-frozen
semantics. BrandGuard adds the per-stage payloads that flow through the
audience -> copy -> gate pipeline.

State is frozen. Each node returns a new state via state.model_copy(update={...}).
"""

from __future__ import annotations

from typing import Any

from intelliflow_core.v2.runtime.state import IntelliFlowState


class BrandGuardState(IntelliFlowState):
    audience_query: str | None = None
    audience_filter: dict[str, Any] | None = None
    matched_records: list[dict[str, Any]] | None = None

    campaign_brief: str | None = None
    retrieved_chunks: list[dict[str, Any]] | None = None
    generated_copy: str | None = None
    citations: list[str] | None = None

    gate_decision: str | None = None
    gate_reasons: list[str] | None = None
