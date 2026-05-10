"""Tests for the Legal/Brand Review Gate.

Covers the three deterministic checks: citation existence, autopay disclosure (O2),
and unlimited disclosure (O2). Every block is reproducible and pinned to a rule_id.
"""

from __future__ import annotations

from brandguard.governance.legal_brand_review_gate import (
    _UNLIMITED_POST_CAP_MBPS,
    _UNLIMITED_SOFT_CAP_GB,
    review,
)


def test_parsed_constants_match_fact_sheet():
    """K3: soft-cap (GB) and post-cap speed (Mbps) parsed from fact sheet.

    The values must match the [fact_sheet:unlimited_plus:data] anchor.
    """
    assert _UNLIMITED_SOFT_CAP_GB == 100
    assert _UNLIMITED_POST_CAP_MBPS == 5


def test_gate_blocks_on_hallucinated_anchor():
    copy = "Strand Pro is $45 a month with autopay. [fact_sheet:fake_sku:price]"
    citations = ["[fact_sheet:fake_sku:price]"]
    decision = review(copy, citations)
    assert decision.decision == "BLOCK"
    assert "citation_existence" in decision.failed_rules


def test_gate_allows_on_valid_anchors_and_disclosed_autopay():
    copy = (
        "Strand Pro: $45 per line per month with autopay. 50 GB high-speed data, "
        "then 1 Mbps for the rest of the cycle. [fact_sheet:pro:price] "
        "[fact_sheet:pro:data]"
    )
    citations = ["[fact_sheet:pro:price]", "[fact_sheet:pro:data]"]
    decision = review(copy, citations)
    assert decision.decision == "ALLOW", decision.reasons
    assert decision.failed_rules == []


def test_gate_blocks_on_undisclosed_autopay_price():
    """O2: $45 is the with-autopay rate. Quoting it without 'with autopay' must BLOCK."""
    copy = "Strand Pro is just $45 a month. [fact_sheet:pro:price]"
    citations = ["[fact_sheet:pro:price]"]
    decision = review(copy, citations)
    assert decision.decision == "BLOCK"
    assert "autopay_disclosure" in decision.failed_rules


def test_gate_blocks_on_undisclosed_unlimited_claim():
    """O2: 'unlimited' without 100 GB soft cap and 5 Mbps post-cap disclosure must BLOCK."""
    copy = (
        "Strand Unlimited+ gives you unlimited data with autopay. "
        "[fact_sheet:unlimited_plus:price]"
    )
    citations = ["[fact_sheet:unlimited_plus:price]"]
    decision = review(copy, citations)
    assert decision.decision == "BLOCK"
    assert "unlimited_disclosure" in decision.failed_rules


def test_gate_allows_unlimited_when_softcap_and_postcap_disclosed():
    copy = (
        "Strand Unlimited+ is $70 per line with autopay. Unlimited data with a "
        "100 GB high-speed soft cap, then up to 5 Mbps if the local network is "
        "congested. [fact_sheet:unlimited_plus:price] [fact_sheet:unlimited_plus:data]"
    )
    citations = [
        "[fact_sheet:unlimited_plus:price]",
        "[fact_sheet:unlimited_plus:data]",
    ]
    decision = review(copy, citations)
    assert decision.decision == "ALLOW", decision.reasons
