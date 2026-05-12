"""Tests for the Audience Discovery Agent."""

from __future__ import annotations

import json

from brandguard.agents.audience_discovery import (
    apply_filter,
    discover_audience,
    extract_filter,
)
from brandguard.llm import make_static_llm

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
        "churn_risk": "high",
        "lifetime_value_usd": 1500.0,
        "acquisition_channel": "online",
        "last_support_contact_days_ago": 10,
    },
    {
        "customer_id": "2",
        "first_name": "B",
        "last_name": "Y",
        "email": "b@y.example",
        "state": "NY",
        "age_bracket": "35-44",
        "tenure_months": 6,
        "current_sku": "Pro",
        "monthly_data_gb": 30.0,
        "international_usage": False,
        "hotspot_usage": False,
        "autopay_enrolled": True,
        "household_size": 2,
        "churn_risk": "low",
        "lifetime_value_usd": 300.0,
        "acquisition_channel": "retail",
        "last_support_contact_days_ago": None,
    },
]


def test_audience_filter_extraction_and_deterministic_apply():
    """LLM extracts a filter, deterministic code applies it. Sanitization drops invalid keys."""
    mock = make_static_llm(
        json.dumps(
            {
                "state": ["CA"],
                "sku": ["Business", "NotARealSKU"],
                "wat": "ignored",
            }
        )
    )
    filter_dict = extract_filter("high LTV business in CA", llm=mock)
    assert filter_dict["state"] == ["CA"]
    assert filter_dict["sku"] == ["Business"]
    assert "wat" not in filter_dict

    matched = apply_filter(filter_dict, _TINY_CORPUS)
    assert len(matched) == 1
    assert matched[0]["customer_id"] == "1"


def test_discover_audience_composes_extract_and_apply():
    """ADR-001 top-level entry: discover_audience() = extract_filter + apply_filter.

    (Audit I4: previously dead code; this test wires it into coverage.)
    """
    mock = make_static_llm(json.dumps({"churn_risk": ["high"]}))
    result = discover_audience("at-risk customers", corpus=_TINY_CORPUS, llm=mock)
    assert result["query"] == "at-risk customers"
    assert result["filter"] == {"churn_risk": ["high"]}
    assert result["match_count"] == 1
    assert result["matched_records"][0]["customer_id"] == "1"
