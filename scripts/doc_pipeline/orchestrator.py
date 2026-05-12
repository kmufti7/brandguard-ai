"""Doc QC Orchestrator: wires Author -> Critic -> Verifier with revision loop.

State machine (DJ-007):

    DRAFTED -> CRITIQUED -> (PASS) -> REVISED [unused, marker for cycle]
                         -> (FAIL) -> REVISED -> CRITIQUED -> ...
    CRITIQUED (PASS) + VERIFIER (PASS) -> VERIFIED -> commit
    Max 3 critique/revise cycles. If no VERIFIED after 3 cycles -> FAILED.

Cross-cutting concerns:

  * WORM logging. Every state transition writes a TOOL_EXECUTED entry to the
    same intelliflow_core WORM logger that the runtime workflow uses. The
    chain is a single one per project; segmented by trace_id of the form
    `doc_pipeline:<doc_name>:<run_uuid>`. This is the DJ-007 architectural
    note: one chain, segmented by prefix (vs separate chains per pipeline).

  * Same fail-closed discipline as the legal/brand gate. Verifier failure
    blocks state transition to VERIFIED. Critic failure under SCORE_FLOOR
    triggers revision, not commit.

CLI:
    python -m scripts.doc_pipeline.orchestrator \\
        --brief BRIEF.md --rubric RUBRIC.md --output OUTPUT.md

Exit 0 on VERIFIED, non-zero on FAILED.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from intelliflow_core.v2.storage.db import DatabaseSessionManager
from intelliflow_core.v2.storage.worm_logger import WORMLogRepository

from scripts.doc_pipeline.author_agent import author_draft
from scripts.doc_pipeline.critic_agent import (
    critique,
    revision_feedback_from_critique,
)
from scripts.doc_pipeline.verifier import verify

REPO_ROOT = Path(__file__).resolve().parents[2]
BANNED_PHRASES_PATH = REPO_ROOT / "scripts" / "doc_pipeline" / "banned_phrases.txt"
DEFAULT_WORM_DB = str(REPO_ROOT / "brandguard_worm.db")
MAX_CYCLES = (
    5  # DJ-021: raised from 3 after Session 5B; long-form docs need the headroom.
)


def _patch_frontmatter_state(doc_path: Path, new_state: str) -> None:
    """DJ-017: rewrite the doc's frontmatter `state:` field. Idempotent.

    The Author Agent writes `state: DRAFTED` or `state: REVISED` when it
    drafts/revises. The orchestrator owns the transition to VERIFIED, so
    when verifier passes we must rewrite the frontmatter to match the
    sidecar truth.
    """
    import re as _re

    text = doc_path.read_text(encoding="utf-8")
    patched = _re.sub(
        r"^(state:\s*)\S+",
        rf"\g<1>{new_state}",
        text,
        count=1,
        flags=_re.MULTILINE,
    )
    if patched != text:
        doc_path.write_text(patched, encoding="utf-8")


@dataclass
class StateTransition:
    cycle: int
    state: str
    timestamp: str
    detail: dict[str, Any] = field(default_factory=dict)


def _log(worm: WORMLogRepository, trace_id: str, transition: StateTransition) -> None:
    worm.log_event(
        trace_id,
        "TOOL_EXECUTED",
        {
            "pipeline": "doc_qc",
            "cycle": transition.cycle,
            "state": transition.state,
            "detail": transition.detail,
        },
    )


def run_pipeline(
    brief_path: Path,
    rubric_path: Path,
    output_path: Path,
    worm_db_path: str = DEFAULT_WORM_DB,
    max_cycles: int = MAX_CYCLES,
) -> dict[str, Any]:
    """Run the doc QC pipeline end-to-end. Returns the final result dict."""
    doc_slug = output_path.stem.lower()
    trace_id = f"doc_pipeline:{doc_slug}:{uuid.uuid4()}"

    db = DatabaseSessionManager(worm_db_path)
    worm = WORMLogRepository(db)
    history: list[StateTransition] = []

    worm.log_event(
        trace_id,
        "WORKFLOW_START",
        {"pipeline": "doc_qc", "doc_slug": doc_slug, "brief": str(brief_path)},
    )

    qc_dir = REPO_ROOT / "docs" / "_qc"
    qc_dir.mkdir(parents=True, exist_ok=True)
    failed_dir = qc_dir / "failed"
    failed_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1: initial DRAFT.
    draft_result = author_draft(brief_path, output_path)
    t = StateTransition(
        cycle=0,
        state="DRAFTED",
        timestamp=datetime.now(timezone.utc).isoformat(),
        detail=draft_result,
    )
    history.append(t)
    _log(worm, trace_id, t)

    final_state = "DRAFTED"
    final_critique: dict[str, Any] = {}
    final_verifier: dict[str, Any] = {}

    for cycle in range(1, max_cycles + 1):
        # Critic cycle.
        critique_json_path = qc_dir / f"{doc_slug}.critique.{cycle}.json"
        critique_result = critique(output_path, rubric_path, critique_json_path)
        t = StateTransition(
            cycle=cycle,
            state="CRITIQUED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            detail={
                "overall_pass": critique_result["overall_pass"],
                "scores": {
                    name: data.get("score")
                    for name, data in critique_result.get("dimensions", {}).items()
                },
            },
        )
        history.append(t)
        _log(worm, trace_id, t)
        final_critique = critique_result

        if not critique_result["overall_pass"]:
            if cycle >= max_cycles:
                # Final cycle exhausted, Critic still failing. Mark FAILED.
                final_state = "FAILED"
                break
            # Revise based on critic feedback.
            feedback = revision_feedback_from_critique(critique_result)
            revise_result = author_draft(
                brief_path, output_path, revision_feedback=feedback
            )
            t = StateTransition(
                cycle=cycle,
                state="REVISED",
                timestamp=datetime.now(timezone.utc).isoformat(),
                detail=revise_result,
            )
            history.append(t)
            _log(worm, trace_id, t)
            continue

        # Critic passed. Run Verifier.
        verifier_result = verify(output_path, BANNED_PHRASES_PATH, REPO_ROOT)
        final_verifier = verifier_result.to_dict()

        if verifier_result.passed:
            final_state = "VERIFIED"
            _patch_frontmatter_state(output_path, "VERIFIED")
            t = StateTransition(
                cycle=cycle,
                state="VERIFIED",
                timestamp=datetime.now(timezone.utc).isoformat(),
                detail={"verifier": final_verifier},
            )
            history.append(t)
            _log(worm, trace_id, t)
            break

        # Verifier failed even though Critic passed. Feed failures back to Author.
        if cycle >= max_cycles:
            final_state = "FAILED"
            break
        feedback = "Verifier blocked the doc on these checks (must fix):\n" + "\n".join(
            f"  - [{f['rule_id']} L{f['line_number']}] {f['message']}"
            for f in final_verifier["failures"]
        )
        revise_result = author_draft(
            brief_path, output_path, revision_feedback=feedback
        )
        t = StateTransition(
            cycle=cycle,
            state="REVISED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            detail=revise_result,
        )
        history.append(t)
        _log(worm, trace_id, t)

    # On FAILED, move the doc to the failed/ subdir; don't clobber an existing
    # committed version.
    if final_state == "FAILED":
        failed_target = failed_dir / f"{doc_slug}.{uuid.uuid4().hex[:8]}.md"
        output_path.replace(failed_target)

    worm.log_event(
        trace_id,
        "WORKFLOW_END",
        {"pipeline": "doc_qc", "final_state": final_state, "cycles": cycle},
    )
    chain_ok = worm.verify_chain()
    db.close()

    # Write the .qc.json sidecar.
    qc_sidecar = output_path.with_suffix(".qc.json")
    if final_state == "FAILED":
        qc_sidecar = failed_dir / f"{doc_slug}.qc.json"
    qc_sidecar.write_text(
        json.dumps(
            {
                "doc_slug": doc_slug,
                "trace_id": trace_id,
                "final_state": final_state,
                "cycles_used": cycle,
                "final_critique": final_critique,
                "final_verifier": final_verifier,
                "state_history": [asdict(h) for h in history],
                "worm_chain_verified": chain_ok,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "final_state": final_state,
        "trace_id": trace_id,
        "cycles_used": cycle,
        "qc_sidecar": str(qc_sidecar),
        "worm_chain_verified": chain_ok,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Doc QC Orchestrator")
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--rubric", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--worm-db", default=DEFAULT_WORM_DB)
    parser.add_argument("--max-cycles", type=int, default=MAX_CYCLES)
    args = parser.parse_args()

    result = run_pipeline(
        args.brief, args.rubric, args.output, args.worm_db, args.max_cycles
    )
    print(json.dumps(result, indent=2))
    return 0 if result["final_state"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(_cli())
