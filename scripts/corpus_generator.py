"""Synthetic CRM corpus generator for BrandGuard AI.

Produces 500 fictional Strand Wireless customer records as a single JSON list.
Output path: data/synthetic_crm_corpus.json. Records are reproducible: a fixed
seed (42) is set on both Python's `random` module and the Faker instance, so a
re-run produces byte-identical output. To regenerate, run from the project root:
`python scripts/corpus_generator.py` (Faker must be installed; `pip install -e .`).
"""

from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

from faker import Faker

SEED = 42
TARGET_COUNT = 500
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_crm_corpus.json"

# State weights are an approximate proxy for US population share. They are not
# calibrated to exact census data; the goal is realistic variety, not accuracy.
US_STATES_AND_WEIGHTS: list[tuple[str, float]] = [
    ("CA", 12.0),
    ("TX", 9.0),
    ("FL", 6.7),
    ("NY", 6.0),
    ("PA", 3.9),
    ("IL", 3.8),
    ("OH", 3.6),
    ("GA", 3.3),
    ("NC", 3.2),
    ("MI", 3.0),
    ("NJ", 2.7),
    ("VA", 2.6),
    ("WA", 2.4),
    ("AZ", 2.2),
    ("MA", 2.1),
    ("TN", 2.1),
    ("IN", 2.0),
    ("MD", 1.8),
    ("MO", 1.8),
    ("WI", 1.7),
    ("CO", 1.7),
    ("MN", 1.7),
    ("SC", 1.6),
    ("AL", 1.5),
    ("LA", 1.4),
    ("KY", 1.3),
    ("OR", 1.3),
    ("OK", 1.2),
    ("CT", 1.1),
    ("UT", 1.0),
    ("IA", 0.9),
    ("NV", 0.9),
    ("AR", 0.9),
    ("MS", 0.9),
    ("KS", 0.9),
    ("NM", 0.6),
    ("NE", 0.6),
    ("WV", 0.5),
    ("ID", 0.6),
    ("HI", 0.4),
    ("NH", 0.4),
    ("ME", 0.4),
    ("MT", 0.3),
    ("RI", 0.3),
    ("DE", 0.3),
    ("SD", 0.3),
    ("ND", 0.2),
    ("AK", 0.2),
    ("VT", 0.2),
    ("WY", 0.2),
    ("DC", 0.2),
]

AGE_BRACKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
AGE_BRACKET_WEIGHTS = [10.0, 22.0, 21.0, 18.0, 15.0, 14.0]

SKUS = ["Essentials", "Pro", "Family", "Unlimited+", "Business"]
SKU_WEIGHTS = [25.0, 30.0, 20.0, 18.0, 7.0]

ACQUISITION_CHANNELS = ["online", "retail", "partner", "referral"]
ACQUISITION_WEIGHTS = [45.0, 25.0, 18.0, 12.0]

# Synthetic email domain pool. None of these resolve to real email providers;
# `.example` is reserved by RFC 2606 specifically for documentation/test data.
EMAIL_DOMAINS = [
    "mailbox.example",
    "inbox.example",
    "post.example",
    "letters.example",
    "homeaddress.example",
]


def weighted_choice(choices: list, weights: list[float]) -> object:
    return random.choices(choices, weights=weights, k=1)[0]


def derive_monthly_data_gb(sku: str, age_bracket: str) -> float:
    """Return a realistic monthly usage figure (GB) shaped by SKU and age bracket."""
    sku_centers = {
        "Essentials": 3.0,
        "Pro": 25.0,
        "Family": 22.0,
        "Unlimited+": 75.0,
        "Business": 35.0,
    }
    age_multiplier = {
        "18-24": 1.30,
        "25-34": 1.20,
        "35-44": 1.05,
        "45-54": 0.95,
        "55-64": 0.80,
        "65+": 0.65,
    }
    center = sku_centers[sku] * age_multiplier[age_bracket]
    noise = random.gauss(0.0, center * 0.30)
    value = max(0.1, center + noise)
    return round(value, 1)


def derive_churn_risk(
    tenure_months: int,
    last_support_contact_days_ago: int | None,
    monthly_data_gb: float,
    sku: str,
    autopay_enrolled: bool,
) -> str:
    """Heuristic churn risk: short tenure, recent support contact, low usage, no autopay raise risk.

    Thresholds (Session 4 / O1 retune): high >= 3, medium >= 1, else low.
    The original Session 2B thresholds (high >= 4, medium >= 2) skewed too low
    on this synthetic corpus, producing only 2 high-risk records out of 500 and
    leaving retention scenarios untestable in the golden dataset.
    """
    score = 0
    if tenure_months < 6:
        score += 2
    elif tenure_months < 18:
        score += 1
    if last_support_contact_days_ago is not None and last_support_contact_days_ago < 30:
        score += 2
    elif (
        last_support_contact_days_ago is not None and last_support_contact_days_ago < 90
    ):
        score += 1
    sku_typical_usage = {
        "Essentials": 3.0,
        "Pro": 25.0,
        "Family": 22.0,
        "Unlimited+": 75.0,
        "Business": 35.0,
    }
    if monthly_data_gb < sku_typical_usage[sku] * 0.30:
        score += 1
    if not autopay_enrolled:
        score += 2  # autopay non-enrollment is a strong real-world churn signal
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"


def derive_lifetime_value(sku: str, tenure_months: int, churn_risk: str) -> float:
    """Approximate LTV: base monthly price * tenure * churn-risk modifier."""
    base_price = {
        "Essentials": 25.00,
        "Pro": 45.00,
        "Family": 35.00,
        "Unlimited+": 70.00,
        "Business": 55.00,
    }
    risk_modifier = {"low": 1.20, "medium": 1.00, "high": 0.70}
    ltv = base_price[sku] * max(tenure_months, 1) * risk_modifier[churn_risk]
    return round(ltv, 2)


def make_record(faker: Faker) -> dict:
    state_codes = [s for s, _ in US_STATES_AND_WEIGHTS]
    state_weights = [w for _, w in US_STATES_AND_WEIGHTS]

    first_name = faker.first_name()
    last_name = faker.last_name()
    age_bracket = weighted_choice(AGE_BRACKETS, AGE_BRACKET_WEIGHTS)
    state = weighted_choice(state_codes, state_weights)
    tenure_months = random.randint(0, 120)
    sku = weighted_choice(SKUS, SKU_WEIGHTS)
    monthly_data_gb = derive_monthly_data_gb(sku, age_bracket)
    international_usage = random.random() < 0.18
    hotspot_usage = random.random() < (
        0.55 if sku in ("Pro", "Unlimited+", "Business") else 0.20
    )
    autopay_enrolled = random.random() < 0.78
    household_size = (
        random.randint(1, 6)
        if sku == "Family"
        else random.choices([1, 2, 3, 4, 5, 6], weights=[55, 28, 9, 5, 2, 1], k=1)[0]
    )
    acquisition_channel = weighted_choice(ACQUISITION_CHANNELS, ACQUISITION_WEIGHTS)

    has_recent_support = random.random() < 0.45
    last_support_contact_days_ago = (
        random.randint(0, 365) if has_recent_support else None
    )

    churn_risk = derive_churn_risk(
        tenure_months,
        last_support_contact_days_ago,
        monthly_data_gb,
        sku,
        autopay_enrolled,
    )
    lifetime_value_usd = derive_lifetime_value(sku, tenure_months, churn_risk)

    email_local = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"
    email_domain = random.choice(EMAIL_DOMAINS)
    email = f"{email_local}@{email_domain}"

    return {
        "customer_id": str(uuid.UUID(int=random.getrandbits(128))),
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "state": state,
        "age_bracket": age_bracket,
        "tenure_months": tenure_months,
        "current_sku": sku,
        "monthly_data_gb": monthly_data_gb,
        "international_usage": international_usage,
        "hotspot_usage": hotspot_usage,
        "autopay_enrolled": autopay_enrolled,
        "household_size": household_size,
        "churn_risk": churn_risk,
        "lifetime_value_usd": lifetime_value_usd,
        "acquisition_channel": acquisition_channel,
        "last_support_contact_days_ago": last_support_contact_days_ago,
    }


def main() -> None:
    random.seed(SEED)
    Faker.seed(SEED)
    faker = Faker("en_US")

    records = [make_record(faker) for _ in range(TARGET_COUNT)]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(records)} records to {OUTPUT_PATH.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
