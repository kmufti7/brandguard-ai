"""Run a live end-to-end pass and write the result to docs/session3_e2e_sample.md.

This script makes real Anthropic API calls. It is the source of truth for the
Session 3 e2e artifact (and is re-run during Session 4 to refresh the WORM
chain integrity check, K2). To regenerate:

    source .venv/bin/activate
    ANTHROPIC_API_KEY=... python scripts/run_e2e_sample.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from brandguard.workflow import WorkflowDeps, cleanup_worm_db, run_workflow

DOCS_PATH = Path(__file__).resolve().parents[1] / "docs" / "session3_e2e_sample.md"
DB_PATH = "brandguard_worm_e2e.db"

AUDIENCE_QUERY = (
    "Strand Business customers in California with at least 12 months of tenure "
    "who use international data."
)
CAMPAIGN_BRIEF = (
    "Promote Strand Business renewal benefits to existing customers. Highlight "
    "the per-line price (with autopay), the included high-speed data, and "
    "international data inclusions. Keep it under 120 words."
)


def main() -> None:
    cleanup_worm_db(DB_PATH)
    deps = WorkflowDeps(worm_db_path=DB_PATH)
    result = run_workflow(AUDIENCE_QUERY, CAMPAIGN_BRIEF, deps=deps)

    final = result["final_state"]
    chain = result["worm_chain"]

    lines: list[str] = []
    lines.append("# BrandGuard AI: Session 3 End-to-End Sample\n")
    lines.append(
        "This file is the recorded output of one live end-to-end run on the synthetic"
    )
    lines.append(
        "Strand Wireless corpus. Regenerate with `scripts/run_e2e_sample.py`.\n"
    )

    lines.append("## Inputs\n")
    lines.append("**Audience query**\n")
    lines.append(f"> {AUDIENCE_QUERY}\n")
    lines.append("**Campaign brief**\n")
    lines.append(f"> {CAMPAIGN_BRIEF}\n")

    lines.append("## Audience Discovery output\n")
    lines.append("**Extracted filter**\n")
    lines.append("```json")
    lines.append(json.dumps(final.get("audience_filter") or {}, indent=2))
    lines.append("```\n")
    matched = final.get("matched_records") or []
    lines.append(f"**Match count:** {len(matched)}\n")
    if matched:
        lines.append("**Sample matched record (first record only)**\n")
        lines.append("```json")
        lines.append(json.dumps(matched[0], indent=2))
        lines.append("```\n")

    lines.append("## RAG Copy Generation output\n")
    retrieved = [c.get("anchor") for c in (final.get("retrieved_chunks") or [])]
    lines.append("**Retrieved anchors (top-K)**\n")
    for a in retrieved:
        lines.append(f"- `{a}`")
    lines.append("")

    lines.append("**Generated copy**\n")
    lines.append("```")
    lines.append(final.get("generated_copy") or "")
    lines.append("```\n")

    lines.append("**Cited anchors**\n")
    for c in final.get("citations") or []:
        lines.append(f"- `{c}`")
    lines.append("")

    lines.append("## Legal/Brand Review Gate decision\n")
    lines.append(f"**Decision:** `{final.get('gate_decision')}`\n")
    reasons = final.get("gate_reasons") or []
    if reasons:
        lines.append("**Reasons:**")
        for r in reasons:
            lines.append(f"- {r}")
        lines.append("")
    else:
        lines.append("No blocking reasons.\n")

    lines.append("## WORM log entries (this run)\n")
    lines.append(
        f"Trace ID: `{result['trace_id']}`. {len(chain)} entries on the chain.\n"
    )
    lines.append("| # | event_type | node | phase | extra |")
    lines.append("|---|-----------|------|-------|-------|")
    for i, entry in enumerate(chain, 1):
        payload = json.loads(entry["payload"])
        node = payload.get("node", "")
        phase = payload.get("phase", "")
        extras = []
        if "decision" in payload:
            extras.append(f"decision={payload['decision']}")
        if "match_count" in payload:
            extras.append(f"match_count={payload['match_count']}")
        if "copy_chars" in payload:
            extras.append(f"copy_chars={payload['copy_chars']}")
        if "failed_rules" in payload and payload["failed_rules"]:
            extras.append(f"failed_rules={payload['failed_rules']}")
        lines.append(
            f"| {i} | {entry['event_type']} | {node} | {phase} | {', '.join(extras)} |"
        )
    lines.append("")

    # K2: verify_chain() integrity check on the WORM repository.
    worm_repo = result.get("worm_repo")
    db = result.get("_db")
    chain_ok = worm_repo.verify_chain() if worm_repo is not None else None
    chain_check_ts = datetime.now(timezone.utc).isoformat()
    if db is not None:
        db.close()

    lines.append("## WORM Chain Integrity (K2)\n")
    lines.append(f"- **`verify_chain()` result:** `{chain_ok}`")
    lines.append(f"- **Entry count:** {len(chain)}")
    lines.append(f"- **Verified at:** `{chain_check_ts}`")
    lines.append("")
    lines.append(
        "The WORM repository's HMAC-SHA256 hash chain is recomputed end-to-end. "
        "A `True` result confirms (a) every `prev_hash` matches the previous entry's "
        "`entry_hash` and (b) every `entry_hash` matches a fresh recomputation. "
        "SQLite triggers physically reject UPDATE/DELETE, so tamper-evidence is "
        "enforced at the storage layer in addition to the application-layer check."
    )
    lines.append("")

    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {DOCS_PATH.relative_to(Path.cwd())}")
    print(f"verify_chain(): {chain_ok}")
    cleanup_worm_db(DB_PATH)


if __name__ == "__main__":
    main()
