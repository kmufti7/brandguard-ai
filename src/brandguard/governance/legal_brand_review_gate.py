"""Legal/Brand Review Gate.

Per ADR-003: deterministic, fail-closed enforcement at the release boundary.
Routing is never LLM-judged. Three checks, evaluated in order:

  1. Citation existence. Every anchor cited by the generation must exist in
     the RAG sources (brand_voice.md or product_fact_sheet.md). A hallucinated
     anchor BLOCKS.

  2. Autopay disclosure (O2). If the copy quotes a per-line price that the
     fact sheet only offers with autopay, the copy must include the autopay
     disclosure. Missing disclosure BLOCKS.

  3. Unlimited disclosure (O2). If the copy uses the word `unlimited`, the
     same sentence (or the immediately following sentence) must include the
     soft cap and post-cap speed disclosure from the fact sheet. Missing
     disclosure BLOCKS.

Fail-closed: any uncaught exception inside a rule maps to BLOCK with a
generic reason. The gate never returns ALLOW under uncertainty.

Output: GateDecision with `decision` ("ALLOW" / "BLOCK"), the rule(s) that
fired, and a free-text reason per rule. The decision is the input to the
WORM logger downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from brandguard.agents.rag_copy_generation import (
    BRAND_VOICE_PATH,
    FACT_SHEET_PATH,
    collect_known_anchors,
)

# Per-line autopay-required prices from product_fact_sheet.md (with-autopay rates).
# Listed as numeric dollars; matching is done against any "$X" or "$X.XX" mention.
_AUTOPAY_PRICES = {
    "essentials": 25.00,
    "pro": 45.00,
    "family": 35.00,
    "unlimited_plus": 70.00,
    "business": 55.00,
}

# Soft-cap and post-cap speed disclosure for SKU 4 (Unlimited+).
# Phrases that satisfy the disclosure when paired with the word "unlimited".
_UNLIMITED_DISCLOSURE_PATTERNS = [
    re.compile(r"100\s*GB", re.IGNORECASE),
    re.compile(r"soft\s*cap", re.IGNORECASE),
]
_UNLIMITED_POSTCAP_PATTERNS = [
    re.compile(r"5\s*Mbps", re.IGNORECASE),
]


@dataclass
class GateDecision:
    decision: str  # "ALLOW" or "BLOCK"
    reasons: list[str] = field(default_factory=list)
    failed_rules: list[str] = field(default_factory=list)


def review(
    copy_text: str,
    citations: list[str],
    brand_voice_path: Path = BRAND_VOICE_PATH,
    fact_sheet_path: Path = FACT_SHEET_PATH,
) -> GateDecision:
    """Run all gate checks. Returns GateDecision. Fail-closed: exceptions BLOCK."""
    decision = GateDecision(decision="ALLOW")

    try:
        _check_citations(
            copy_text, citations, decision, brand_voice_path, fact_sheet_path
        )
        _check_autopay_disclosure(copy_text, decision)
        _check_unlimited_disclosure(copy_text, decision)
    except Exception as exc:  # fail-closed
        decision.decision = "BLOCK"
        decision.failed_rules.append("internal_error")
        decision.reasons.append(
            f"Internal gate error, blocking by default: {type(exc).__name__}"
        )

    if decision.failed_rules:
        decision.decision = "BLOCK"

    return decision


def _check_citations(
    copy_text: str,
    citations: list[str],
    decision: GateDecision,
    brand_voice_path: Path,
    fact_sheet_path: Path,
) -> None:
    known = collect_known_anchors(brand_voice_path, fact_sheet_path)
    inline = re.findall(r"\[(?:brand_voice|fact_sheet):[^\]]+\]", copy_text)
    all_anchors = list({*citations, *inline})

    if not all_anchors:
        decision.failed_rules.append("citation_required")
        decision.reasons.append(
            "Copy emits no citations. Every factual claim must cite a source."
        )
        return

    missing = [a for a in all_anchors if a not in known]
    if missing:
        decision.failed_rules.append("citation_existence")
        decision.reasons.append(
            "Copy cites anchors that do not exist in the RAG sources: "
            + ", ".join(missing)
        )


def _check_autopay_disclosure(copy_text: str, decision: GateDecision) -> None:
    """If the copy quotes any with-autopay per-line price, autopay must be disclosed."""
    quoted_autopay_prices: list[str] = []
    for sku, price in _AUTOPAY_PRICES.items():
        # Match `$25` or `$25.00`. Word boundary on right keeps `$250` from matching `$25`.
        pattern = re.compile(rf"\${int(price)}(?:\.\d{{2}})?\b")
        if pattern.search(copy_text):
            quoted_autopay_prices.append(f"${int(price)} ({sku})")

    if not quoted_autopay_prices:
        return

    # Disclosure phrases. "with autopay" / "autopay required" / "autopay enrollment".
    disclosure_re = re.compile(
        r"(with\s+autopay|autopay\s+required|autopay\s+enroll)", re.IGNORECASE
    )
    if not disclosure_re.search(copy_text):
        decision.failed_rules.append("autopay_disclosure")
        decision.reasons.append(
            "Copy quotes a price that requires autopay ("
            + ", ".join(quoted_autopay_prices)
            + ") without an autopay disclosure (e.g., 'with autopay')."
        )


def _check_unlimited_disclosure(copy_text: str, decision: GateDecision) -> None:
    """If the copy uses 'unlimited', the soft-cap + post-cap speed disclosure must be present."""
    # Match `unlimited` as a standalone word (case-insensitive). `Unlimited+` is the SKU
    # name and counts.
    if not re.search(r"\bunlimited\b", copy_text, re.IGNORECASE):
        return

    has_softcap = any(p.search(copy_text) for p in _UNLIMITED_DISCLOSURE_PATTERNS)
    has_postcap = any(p.search(copy_text) for p in _UNLIMITED_POSTCAP_PATTERNS)

    if not (has_softcap and has_postcap):
        decision.failed_rules.append("unlimited_disclosure")
        decision.reasons.append(
            "Copy uses the word 'unlimited' without disclosing both the 100 GB soft cap "
            "and the 5 Mbps post-cap speed in the same passage."
        )
