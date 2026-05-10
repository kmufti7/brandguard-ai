# BrandGuard AI: Session 3 End-to-End Sample

This file is the recorded output of one live end-to-end run on the synthetic
Strand Wireless corpus. Regenerate with `scripts/run_e2e_sample.py`.

## Inputs

**Audience query**

> Strand Business customers in California with at least 12 months of tenure who use international data.

**Campaign brief**

> Promote Strand Business renewal benefits to existing customers. Highlight the per-line price (with autopay), the included high-speed data, and international data inclusions. Keep it under 120 words.

## Audience Discovery output

**Extracted filter**

```json
{
  "state": [
    "CA"
  ],
  "sku": [
    "Business"
  ],
  "tenure_min_months": 12,
  "international_usage": true
}
```

**Match count:** 2

**Sample matched record (first record only)**

```json
{
  "customer_id": "0387f74d-1149-d096-965d-744f0445c1a8",
  "first_name": "Aaron",
  "last_name": "Frost",
  "email": "aaron.frost99@mailbox.example",
  "state": "CA",
  "age_bracket": "45-54",
  "tenure_months": 113,
  "current_sku": "Business",
  "monthly_data_gb": 56.4,
  "international_usage": true,
  "hotspot_usage": false,
  "autopay_enrolled": true,
  "household_size": 1,
  "churn_risk": "low",
  "lifetime_value_usd": 7458.0,
  "acquisition_channel": "retail",
  "last_support_contact_days_ago": null
}
```

## RAG Copy Generation output

**Retrieved anchors (top-K)**

- `[fact_sheet:business:price]`
- `[fact_sheet:unlimited_plus:price]`
- `[fact_sheet:pro:restrictions]`
- `[fact_sheet:pro:price]`
- `[fact_sheet:family:price]`
- `[fact_sheet:unlimited_plus:restrictions]`
- `[fact_sheet:essentials:restrictions]`
- `[brand_voice:§7]`

**Generated copy**

```
Your Strand Business plan stays strong. At $55.00 per line per month with autopay, you're getting reliable service built for teams that need to stay connected. [fact_sheet:business:price] Renew now and keep the same straightforward pricing across your lines.
```

**Cited anchors**

- `[fact_sheet:business:price]`

## Legal/Brand Review Gate decision

**Decision:** `ALLOW`

No blocking reasons.

## WORM log entries (this run)

Trace ID: `d3a945f3-ff09-4b2f-8874-682a523b58e5`. 8 entries on the chain.

| # | event_type | node | phase | extra |
|---|-----------|------|-------|-------|
| 1 | WORKFLOW_START |  |  |  |
| 2 | TOOL_EXECUTED | audience_discovery | enter |  |
| 3 | TOOL_EXECUTED | audience_discovery | exit | match_count=2 |
| 4 | TOOL_EXECUTED | rag_copy_generation | enter |  |
| 5 | TOOL_EXECUTED | rag_copy_generation | exit | copy_chars=258 |
| 6 | TOOL_EXECUTED | legal_brand_review_gate | enter |  |
| 7 | TOOL_EXECUTED | legal_brand_review_gate | exit | decision=ALLOW |
| 8 | WORKFLOW_END |  |  |  |
