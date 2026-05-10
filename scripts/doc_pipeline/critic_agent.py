"""Critic Agent: grades a doc against a rubric and returns structured JSON.

Architecturally a fresh subagent per DJ-007: separate Anthropic API call,
separate system prompt, no shared state with Author or orchestrator. This is
where LLM-as-judge is acceptable in the project (DJ-006 / P22): the Critic's
judgment is offline, rubric-bounded, and never gates a release. The Verifier
(`verifier.py`) is the release-gating check, and it has no LLM in its path.

Rubric structure: each dimension is graded 0-10. A doc passes when every
dimension scores >= 7 (the score floor). The Critic also returns a list of
specific `issues` and `asks` per dimension, which the orchestrator passes
back to the Author for revision.

Output: JSON file with shape
    {
      "overall_pass": bool,
      "dimensions": {
        "<name>": {"score": int, "issues": [str], "asks": [str]},
        ...
      },
      "raw": "<the LLM's full response>"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from brandguard.llm import LLMCall, default_complete

SCORE_FLOOR = 7


_CRITIC_SYSTEM = """You are the Critic for the BrandGuard AI doc QC pipeline.

Your job: grade the supplied draft document against the supplied rubric. You
do NOT rewrite the doc. You grade it.

Rubric dimensions are numbered. For each dimension, output:
  - A score from 0 to 10 (integer).
  - 0-3 issues (specific, with line refs where possible).
  - 0-3 asks (concrete revisions the author should make).

You are not the brand voice police. You are not the legal gate. You score
honestly against the rubric. If the doc is excellent, score it 9 or 10. If
the doc is weak, score it 3 or 4 and be specific about why.

Output ONLY valid JSON. No prose, no markdown fences. Shape:

{
  "dimensions": {
    "<dimension_name>": {
      "score": <int 0..10>,
      "issues": ["<str>", ...],
      "asks": ["<str>", ...]
    },
    ...
  }
}
"""


def _extract_json(raw: str) -> dict[str, Any]:
    """Tolerantly find the first complete JSON object in the response."""
    start = raw.find("{")
    if start < 0:
        raise ValueError(f"No JSON object in critic response: {raw[:200]}")
    depth = 0
    for i in range(start, len(raw)):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError(f"Unbalanced braces in critic response: {raw[:200]}")


def critique(
    doc_path: Path,
    rubric_path: Path,
    output_path: Path,
    llm: LLMCall | None = None,
) -> dict[str, Any]:
    """Grade a doc against a rubric. Writes critique JSON to output_path."""
    if llm is None:
        llm = default_complete

    doc_text = doc_path.read_text(encoding="utf-8")
    rubric_text = rubric_path.read_text(encoding="utf-8")

    user_prompt = "Rubric:\n" + rubric_text + "\n\n---\n\nDraft document:\n" + doc_text

    raw = llm(_CRITIC_SYSTEM, user_prompt, 2048)

    try:
        parsed = _extract_json(raw)
    except Exception as exc:
        # Fail-closed: a critic that can't return valid JSON is treated as
        # a failure with a clear reason.
        result = {
            "overall_pass": False,
            "dimensions": {},
            "raw": raw,
            "parse_error": str(exc),
        }
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    dimensions = parsed.get("dimensions", {})
    overall_pass = all(
        isinstance(d, dict) and int(d.get("score", 0)) >= SCORE_FLOOR
        for d in dimensions.values()
    ) and bool(dimensions)

    result = {
        "overall_pass": overall_pass,
        "dimensions": dimensions,
        "raw": raw,
    }
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def revision_feedback_from_critique(critique_result: dict[str, Any]) -> str:
    """Turn a critique JSON into a feedback string for the Author."""
    lines: list[str] = []
    for dim, data in critique_result.get("dimensions", {}).items():
        score = data.get("score", "?")
        issues = data.get("issues", [])
        asks = data.get("asks", [])
        if int(score) >= SCORE_FLOOR and not issues and not asks:
            continue
        lines.append(f"Dimension '{dim}' scored {score}/10.")
        for issue in issues:
            lines.append(f"  Issue: {issue}")
        for ask in asks:
            lines.append(f"  Ask: {ask}")
    return "\n".join(lines) or "No actionable feedback; revise for clarity."


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Doc QC Critic Agent")
    parser.add_argument("--doc", required=True, type=Path)
    parser.add_argument("--rubric", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = critique(args.doc, args.rubric, args.output)
    print(json.dumps({"overall_pass": result["overall_pass"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
