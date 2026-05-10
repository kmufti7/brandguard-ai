"""Audience Discovery Agent.

Per ADR-001: a free-text audience description is converted to a structured
filter dict by an LLM, and the filter is then applied to the synthetic CRM
corpus by deterministic Python. The LLM never filters records directly.

Two-step contract:

1. LLM step (extract_filter): given a natural-language query, return a JSON
   filter dict. Allowed keys are restricted by the prompt to the schema below.
   Anything outside the schema is dropped.

2. Deterministic step (apply_filter): given a filter dict and the corpus,
   return the records that match every active predicate.

Filter schema (all keys optional; unspecified keys mean "no constraint"):

    state                 list[str] of two-letter US state codes (e.g. ["CA","TX"])
    sku                   list[str] of SKU names (Essentials/Pro/Family/Unlimited+/Business)
    age_bracket           list[str] of brackets (18-24, 25-34, ..., 65+)
    tenure_min_months     int (inclusive lower bound)
    tenure_max_months     int (inclusive upper bound)
    monthly_data_gb_min   float (inclusive lower bound)
    monthly_data_gb_max   float (inclusive upper bound)
    international_usage   bool
    hotspot_usage         bool
    autopay_enrolled      bool
    household_size_min    int
    household_size_max    int
    churn_risk            list[str] subset of ["low","medium","high"]
    lifetime_value_min    float
    lifetime_value_max    float
    acquisition_channel   list[str] subset of ["online","retail","partner","referral"]
    last_support_within_days  int (matches records where last_support_contact_days_ago <= N)

The LLM is instructed to return ONLY a JSON object using these keys.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brandguard.llm import LLMCall, default_complete, parse_json_object

DEFAULT_CORPUS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "synthetic_crm_corpus.json"
)

ALLOWED_FILTER_KEYS = {
    "state",
    "sku",
    "age_bracket",
    "tenure_min_months",
    "tenure_max_months",
    "monthly_data_gb_min",
    "monthly_data_gb_max",
    "international_usage",
    "hotspot_usage",
    "autopay_enrolled",
    "household_size_min",
    "household_size_max",
    "churn_risk",
    "lifetime_value_min",
    "lifetime_value_max",
    "acquisition_channel",
    "last_support_within_days",
}

VALID_SKUS = {"Essentials", "Pro", "Family", "Unlimited+", "Business"}
VALID_AGE_BRACKETS = {"18-24", "25-34", "35-44", "45-54", "55-64", "65+"}
VALID_RISK = {"low", "medium", "high"}
VALID_CHANNELS = {"online", "retail", "partner", "referral"}


SYSTEM_PROMPT = """You are an audience-segmentation filter extractor for Strand Wireless.

Your job: convert a marketer's free-text audience description into a JSON filter object.
You do NOT filter records yourself. You only emit the filter spec.

Allowed keys (omit any key that the user did not constrain):
  state (list of two-letter US state codes)
  sku (list of: Essentials, Pro, Family, Unlimited+, Business)
  age_bracket (list of: 18-24, 25-34, 35-44, 45-54, 55-64, 65+)
  tenure_min_months (int, inclusive)
  tenure_max_months (int, inclusive)
  monthly_data_gb_min (float)
  monthly_data_gb_max (float)
  international_usage (bool)
  hotspot_usage (bool)
  autopay_enrolled (bool)
  household_size_min (int)
  household_size_max (int)
  churn_risk (list subset of: low, medium, high)
  lifetime_value_min (float)
  lifetime_value_max (float)
  acquisition_channel (list subset of: online, retail, partner, referral)
  last_support_within_days (int)

Return ONLY a JSON object. No prose, no markdown fences. If the user's description
maps to no constraints (totally generic), return {}.
"""


def extract_filter(query: str, llm: LLMCall | None = None) -> dict[str, Any]:
    """Call the LLM to convert a free-text audience query into a filter dict.

    Returns a sanitized filter: only keys in ALLOWED_FILTER_KEYS, with values
    coerced to expected types where reasonable. Unknown keys are silently
    dropped to keep the deterministic apply step well-defined.
    """
    if llm is None:
        llm = default_complete

    raw = llm(SYSTEM_PROMPT, query, 512)
    parsed = parse_json_object(raw)
    return _sanitize_filter(parsed)


def _sanitize_filter(raw_filter: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in raw_filter.items():
        if key not in ALLOWED_FILTER_KEYS:
            continue
        if key == "sku":
            out[key] = [v for v in _as_list(value) if v in VALID_SKUS]
        elif key == "age_bracket":
            out[key] = [v for v in _as_list(value) if v in VALID_AGE_BRACKETS]
        elif key == "churn_risk":
            out[key] = [v for v in _as_list(value) if v in VALID_RISK]
        elif key == "acquisition_channel":
            out[key] = [v for v in _as_list(value) if v in VALID_CHANNELS]
        elif key == "state":
            out[key] = [v.upper() for v in _as_list(value) if isinstance(v, str)]
        elif isinstance(value, bool):
            out[key] = value
        elif isinstance(value, (int, float)):
            out[key] = value
        elif isinstance(value, str) and value.isdigit():
            out[key] = int(value)
    return out


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def apply_filter(
    filter_dict: dict[str, Any], corpus: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Deterministic predicate evaluation. Returns records that match every active predicate."""
    return [r for r in corpus if _record_matches(r, filter_dict)]


def _record_matches(record: dict[str, Any], f: dict[str, Any]) -> bool:
    if "state" in f and f["state"] and record["state"] not in f["state"]:
        return False
    if "sku" in f and f["sku"] and record["current_sku"] not in f["sku"]:
        return False
    if (
        "age_bracket" in f
        and f["age_bracket"]
        and record["age_bracket"] not in f["age_bracket"]
    ):
        return False
    if "tenure_min_months" in f and record["tenure_months"] < f["tenure_min_months"]:
        return False
    if "tenure_max_months" in f and record["tenure_months"] > f["tenure_max_months"]:
        return False
    if (
        "monthly_data_gb_min" in f
        and record["monthly_data_gb"] < f["monthly_data_gb_min"]
    ):
        return False
    if (
        "monthly_data_gb_max" in f
        and record["monthly_data_gb"] > f["monthly_data_gb_max"]
    ):
        return False
    if (
        "international_usage" in f
        and record["international_usage"] != f["international_usage"]
    ):
        return False
    if "hotspot_usage" in f and record["hotspot_usage"] != f["hotspot_usage"]:
        return False
    if "autopay_enrolled" in f and record["autopay_enrolled"] != f["autopay_enrolled"]:
        return False
    if "household_size_min" in f and record["household_size"] < f["household_size_min"]:
        return False
    if "household_size_max" in f and record["household_size"] > f["household_size_max"]:
        return False
    if (
        "churn_risk" in f
        and f["churn_risk"]
        and record["churn_risk"] not in f["churn_risk"]
    ):
        return False
    if (
        "lifetime_value_min" in f
        and record["lifetime_value_usd"] < f["lifetime_value_min"]
    ):
        return False
    if (
        "lifetime_value_max" in f
        and record["lifetime_value_usd"] > f["lifetime_value_max"]
    ):
        return False
    if (
        "acquisition_channel" in f
        and f["acquisition_channel"]
        and record["acquisition_channel"] not in f["acquisition_channel"]
    ):
        return False
    if "last_support_within_days" in f:
        days = record.get("last_support_contact_days_ago")
        if days is None or days > f["last_support_within_days"]:
            return False
    return True


def load_corpus(path: Path | str = DEFAULT_CORPUS_PATH) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def discover_audience(
    query: str,
    corpus: list[dict[str, Any]] | None = None,
    llm: LLMCall | None = None,
) -> dict[str, Any]:
    """Top-level entry: extract filter via LLM, apply deterministically."""
    if corpus is None:
        corpus = load_corpus()
    filter_dict = extract_filter(query, llm=llm)
    matched = apply_filter(filter_dict, corpus)
    return {
        "query": query,
        "filter": filter_dict,
        "matched_records": matched,
        "match_count": len(matched),
    }
