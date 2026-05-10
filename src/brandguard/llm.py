"""Anthropic LLM client wrapper for BrandGuard agents.

Single thin wrapper so agents can be tested with a mock callable instead of
hitting the network. Production callers use `default_complete`; tests inject
their own callable matching the same signature.
"""

from __future__ import annotations

import os
from typing import Any, Callable

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

LLMCall = Callable[[str, str, int], str]


def default_complete(
    system_prompt: str, user_prompt: str, max_tokens: int = 1024
) -> str:
    """Real Anthropic SDK call. Reads ANTHROPIC_API_KEY from environment.

    Raises RuntimeError with a clear message if the key is missing so callers
    can decide whether to skip or fail.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it in the environment or "
            "inject a mock LLM call into the agent constructor."
        )

    import anthropic  # local import so callers without the SDK still import the module

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


def make_static_llm(reply: str) -> LLMCall:
    """Test helper: return a callable that ignores prompts and returns `reply`."""

    def _static(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        return reply

    return _static


def make_dispatch_llm(default: str, dispatch: dict[str, str]) -> LLMCall:
    """Test helper: returns a callable that picks reply by substring match in user_prompt.

    Useful when one workflow run involves two LLM calls (filter extraction + copy gen)
    and the same mock needs to serve both.
    """

    def _dispatch(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        for needle, reply in dispatch.items():
            if needle in user_prompt or needle in system_prompt:
                return reply
        return default

    return _dispatch


def parse_json_object(raw: str) -> dict[str, Any]:
    """Tolerantly extract a JSON object from an LLM response.

    Models often wrap JSON in prose or ```json fences. This finds the first
    `{` and the matching closing `}` and parses the slice.
    """
    import json

    start = raw.find("{")
    if start < 0:
        raise ValueError(f"No JSON object found in LLM response: {raw[:200]}")
    depth = 0
    for i in range(start, len(raw)):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError(f"Unbalanced braces in LLM response: {raw[:200]}")
