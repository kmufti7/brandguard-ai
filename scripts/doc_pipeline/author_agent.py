"""Author Agent: drafts a single doc from a structured brief.

Architecturally a fresh subagent per DJ-007: every call is a brand new
Anthropic API request with a role-specific system prompt and no shared state
with the orchestrator or the Critic. This is the "fresh subagent" semantic
achieved without spawning a separate Claude Code process: independent LLM
context, role isolation, no orchestrator memory leakage.

Two modes (DJ-014):

  plugin   The Author Agent's system prompt references an Anthropic
           Knowledge-Work plugin slash command (e.g. /write-spec). The plugin
           command name is embedded in the brief. The Author prompts the LLM
           to behave as the plugin would, using the brief as input. This mode
           exists because the Anthropic product-management plugin's slash
           commands are skills under the hood; the LLM can be primed to act
           as the skill given the skill's behavior described in the prompt.

  encoded  The Author Agent's system prompt embeds a framework definition
           inline (e.g. Jobs-to-be-Done, Working Backwards). This mode exists
           as a fallback for the pmprompt plugin which is blocked on an
           upstream manifest conflict (Session 5A pre-session notes).

Output: writes the draft to `output_path` with a small frontmatter block
recording state, timestamp, brief used, and mode used.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brandguard.llm import LLMCall, default_complete

# Plugin command system prompts. Keys correspond to brief frontmatter
# `plugin_command:` values. The text mirrors the documented skill behavior
# from the Anthropic Knowledge-Work plugin so the LLM behaves as the skill
# would when invoked from within Claude Code.
_PLUGIN_SYSTEM_PROMPTS: dict[str, str] = {
    "/write-spec": (
        "You are the write-spec skill from the Anthropic product-management "
        "Knowledge-Work plugin. Your job is to take a problem statement or "
        "feature idea and produce a structured product specification. Required "
        "structure: Problem Statement, Target User, Solution, Competitive "
        "Positioning, Business Impact. Be specific, not generic. "
        "CRITICAL: DO NOT emit [file:path] citation anchors. Reference files "
        "in prose by name (e.g., src/brandguard/...) without the [file:...] "
        "anchor syntax. The Verifier blocks unresolvable file citations. Do "
        "not use em dashes. Output only the spec, no preamble."
    ),
    "/roadmap-update": (
        "You are the roadmap-update skill from the Anthropic product-management "
        "plugin. Produce a roadmap in Shipped / Next / Later / Won't Build "
        "format with one-line rationale per item. Be concrete about scope; "
        "no vague intentions. DO NOT emit [file:path] citation anchors; reference "
        "files in prose by name (e.g., src/brandguard/...) without the [file:...] "
        "syntax. The Verifier blocks unresolvable file citations. Do not use em dashes."
    ),
    "/metrics-review": (
        "You are the metrics-review skill from the Anthropic product-management "
        "plugin. Produce a structured metrics document with Leading vs Lagging "
        "categorization, explicit definitions, and target values. Reject vanity "
        "metrics in favor of measurable, time-bound, actionable ones. DO NOT "
        "emit [file:path] citation anchors; reference files in prose by name "
        "without the [file:...] syntax. The Verifier blocks unresolvable file "
        "citations. Do not use em dashes."
    ),
    "/synthesize-research": (
        "You are the synthesize-research skill from the Anthropic product-"
        "management plugin. Take raw interview notes or survey data and produce "
        "structured insights with named themes and quoted evidence."
    ),
    "/competitive-brief": (
        "You are the competitive-brief skill from the Anthropic product-"
        "management plugin. Produce a competitive analysis brief with named "
        "competitors, positioning differences, and honest assessment of where "
        "the product is and is not differentiated."
    ),
}

# Encoded frameworks for mode=encoded. The brief's frontmatter `framework:`
# field names which framework to load.
_ENCODED_FRAMEWORKS: dict[str, str] = {
    "jtbd": (
        "Jobs-to-be-Done framework: structure each persona around the JOB the "
        "user is trying to accomplish (the progress they want), not their "
        "demographic profile. For each persona include: (a) name, role, "
        "company-size context; (b) the job statement (when [situation], I want "
        "to [motivation], so I can [expected outcome]); (c) day-in-the-life "
        "with named tools and time durations; (d) hiring criteria (what they "
        "look for in any product attempting this job); (e) fears about AI doing "
        "the job for them."
    ),
    "working_backwards": (
        "Working Backwards framework (Amazon): produce a one-paragraph PR-FAQ "
        "style README opener that reads as if the product has shipped. Lead "
        "with what the customer can now do. Then explain how. Then explain why "
        "it matters. Setup, contributor guide, and dependency notes come AFTER "
        "the product framing, not before. The lineage disclosure (intelliflow-"
        "core kernel) is preserved, not buried."
    ),
    "shape_up": (
        "Shape Up framework: scope is fixed (6-week appetite); features are "
        "shaped before they are built. Roadmap entries include the appetite "
        "(small batch / big batch) and the boundary (what's IN scope, what's "
        "explicitly OUT)."
    ),
}


def _frontmatter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def _parse_brief(brief_text: str) -> tuple[dict[str, str], str]:
    if not brief_text.startswith("---"):
        return {}, brief_text
    end = brief_text.find("\n---", 3)
    if end < 0:
        return {}, brief_text
    block = brief_text[3:end].strip()
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, brief_text[end + 4 :].lstrip()


def author_draft(
    brief_path: Path,
    output_path: Path,
    llm: LLMCall | None = None,
    revision_feedback: str | None = None,
) -> dict[str, Any]:
    """Draft (or revise) a doc based on a brief.

    `revision_feedback` is supplied by the orchestrator when the Critic's
    asks need to be incorporated. When None, this is a first-pass draft.
    """
    if llm is None:
        llm = default_complete

    brief_text = brief_path.read_text(encoding="utf-8")
    meta, body = _parse_brief(brief_text)
    mode = meta.get("mode", "encoded")

    if mode == "plugin":
        plugin = meta.get("plugin_command", "/write-spec")
        system_prompt = _PLUGIN_SYSTEM_PROMPTS.get(
            plugin, _PLUGIN_SYSTEM_PROMPTS["/write-spec"]
        )
    elif mode == "encoded":
        framework_key = meta.get("framework", "")
        framework_text = _ENCODED_FRAMEWORKS.get(framework_key, "")
        system_prompt = (
            "You are a documentation author for the BrandGuard AI project. "
            "BrandGuard AI is a governed marketing AI product owned by Kaizen "
            "Works, LLC. Fictional brand: Strand Wireless (US telecom). "
            "Follow the brand voice in data/brand_voice.md when writing prose. "
            "Be specific, not generic. Numbers and durations are preferred over "
            "vague language. Output ONLY the doc body in valid markdown. Do not "
            "include preamble.\n\n"
            "CITATION RULES (the deterministic Verifier will block any violation):\n"
            "- DO NOT emit [file:path] citation anchors at all. Reference files "
            "in prose by name (e.g., 'src/brandguard/governance/legal_brand_review_gate.py') "
            "without the [file:...] anchor syntax. The Verifier blocks any "
            "[file:...] citation whose path does not resolve, and you cannot "
            "verify file existence from this prompt.\n"
            "- [DJ-NNN] citations must reference DJ entries that exist in "
            "docs/decision_journal.md. The journal currently has 17 entries "
            "(DJ-001 through DJ-017). Do not reference DJ-018 or higher.\n"
            "- [ADR-NNN] citations: only ADR-001..ADR-004 exist.\n"
            "- [PDR-NNN] citations: PDR-001..PDR-004 are planned in Session 5B "
            "(reference them only if the brief asks you to anticipate them).\n"
            "- [brand_voice:§N] anchors must be 1-7 (the doc has 7 sections). "
            "[fact_sheet:<sku>:<field>] anchors must match the actual fact sheet.\n\n"
            "Do not use em dashes (use commas, colons, periods, or parentheses "
            "instead). Do not use these phrases: synergize, leverage AI, "
            "best-in-class, world-class, cutting-edge, revolutionize, seamlessly, "
            "robust solution, game-changer, paradigm shift, ecosystem, "
            "democratize, disrupt, holistic, unlock value.\n\n"
            + (f"Framework guidance:\n{framework_text}\n" if framework_text else "")
        )
    else:
        raise ValueError(f"unknown brief mode: {mode}")

    user_prompt_parts = [
        f"Doc title: {output_path.stem.replace('_', ' ').upper()}",
        f"Word count floor: {meta.get('word_count_floor', '600')}",
        "",
        "Brief:",
        body,
    ]
    if revision_feedback:
        user_prompt_parts.extend(
            [
                "",
                "Critic feedback to address in this revision:",
                revision_feedback,
            ]
        )
    user_prompt = "\n".join(user_prompt_parts)

    response = llm(system_prompt, user_prompt, 4096)

    state_meta = {
        "state": "REVISED" if revision_feedback else "DRAFTED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "brief": str(brief_path),
        "mode": mode,
        "plugin_command": meta.get("plugin_command", ""),
        "framework": meta.get("framework", ""),
        "word_count_floor": meta.get("word_count_floor", "600"),
    }
    output_path.write_text(
        _frontmatter(state_meta) + "\n\n" + response.strip() + "\n",
        encoding="utf-8",
    )
    return {
        "state": state_meta["state"],
        "output_path": str(output_path),
        "word_count": len(response.split()),
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Doc QC Author Agent")
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision-feedback", default=None)
    args = parser.parse_args()
    result = author_draft(
        args.brief, args.output, revision_feedback=args.revision_feedback
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
