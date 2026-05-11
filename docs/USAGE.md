---
state: VERIFIED
timestamp: 2026-05-11T22:45:43.400444+00:00
brief: scripts/doc_pipeline/briefs/usage.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 600
---

# USAGE

## Overview

BrandGuard AI lets Strand Wireless marketing teams check compliance, generate evaluation reports, and audit governance decisions. This guide shows you how to run the end-to-end workflow, execute evaluation reports in both deterministic and LLM modes, inspect the WORM chain, and verify chain integrity.

## Running the End-to-End Workflow

The primary entry point is `run_governance_workflow()` in src/brandguard/governance/workflow_orchestrator.py. This function executes three sequential gates: the legal brand review gate, the tone and positioning gate, and the claim substantiation gate. Each step records an immutable log entry in the WORM chain.

```python
from brandguard.governance.workflow_orchestrator import run_governance_workflow
from brandguard.models import MarketingAsset

# Create a marketing asset (email campaign for Strand Wireless)
asset = MarketingAsset(
    content="Strand Wireless gives you unlimited 5G data at half the price of competitors.",
    asset_type="email_campaign",
    channel="email",
    brand="Strand Wireless"
)

# Run the full governance workflow
result = run_governance_workflow(asset)

print("Workflow Status:", result.status)
print("Passed Legal Gate:", result.legal_gate_passed)
print("Passed Tone Gate:", result.tone_gate_passed)
print("Passed Claims Gate:", result.claims_gate_passed)
print("Final Decision:", result.decision)  # "approve", "reject", or "flag_for_review"
```

**Expected output:**
```
Workflow Status: completed
Passed Legal Gate: False
Passed Tone Gate: True
Passed Claims Gate: False
Final Decision: flag_for_review
Reason: Claim "half the price" lacks substantiation. No pricing data attached.
```

The legal brand review gate (src/brandguard/governance/legal_brand_review_gate.py) enforces FCC compliance and trademark rules. The tone and positioning gate checks for brand voice alignment per data/brand_voice.md. The claim substantiation gate validates that explicit and implicit product claims are supported by evidence. See ADR-001 for the three-gate architecture decision.

## Scope of the Workflow

This guide covers three primary workflows: end-to-end governance (shown above), evaluation reports (below), and WORM chain inspection. The end-to-end workflow is the standard entry point and the only operation that appends entries to the WORM chain.

For custom gate logic or standalone rule execution, refer to src/brandguard/governance/rules/ where individual rule functions can be imported and called in isolation. However, doing so bypasses WORM logging and audit guarantees.

## Running Evaluation Reports

Evaluation reports score marketing assets against governance rules and produce compliance metrics. You can run reports in two modes: deterministic and LLM. See DJ-008 for detailed criteria on when to use each mode.

**Deterministic mode** runs rule-based checks only. No external LLM calls occur. Deterministic mode cannot call external APIs such as FCC lookups; it evaluates only in-process rules against the asset text and attached metadata. Use deterministic mode for rapid feedback on rule violations, typically under 2 seconds per asset.

**LLM mode** spots implicit claims and brand tone drift using semantic analysis. LLM mode calls Claude or GPT-4 to evaluate nuance, tone consistency, and unstated product claims. Use LLM mode for deep compliance reviews where implicit messaging matters, typically 8 to 15 seconds per asset depending on token count.

### Running a Deterministic Report

```python
from brandguard.evaluation.report_engine import generate_evaluation_report

asset = MarketingAsset(
    content="Get lightning-fast 5G from Strand Wireless.",
    asset_type="social_post",
    channel="twitter",
    brand="Strand Wireless"
)

report = generate_evaluation_report(asset, mode="deterministic")

print("Report Mode:", report.mode)
print("Total Rules Checked:", report.total_rules)
print("Rules Passed:", report.rules_passed)
print("Rules Failed:", report.rules_failed)
print("Compliance Score:", f"{report.compliance_score}%")

for violation in report.violations:
    print(f"  - {violation.rule_id}: {violation.message}")
```

**Expected output:**
```
Report Mode: deterministic
Total Rules Checked: 12
Rules Passed: 10
Rules Failed: 2
Compliance Score: 83%
  - TONE_001: Phrase "lightning-fast" is intensifier; use factual descriptors per brand_voice:§3
  - CLAIM_005: "fastest" is implicit superlative claim; requires FCC or independent benchmark data
```

### Running an LLM Report

```python
report = generate_evaluation_report(asset, mode="llm", model="claude-3-sonnet")

print("Report Mode:", report.mode)
print("Model Used:", report.llm_model)
print("Processing Time:", report.processing_time_seconds, "seconds")
print("Compliance Score:", f"{report.compliance_score}%")

for violation in report.violations:
    print(f"  - {violation.rule_id}: {violation.message}")
    print(f"    Evidence: {violation.evidence}")
```

**Expected output:**
```
Report Mode: llm
Model Used: claude-3-sonnet
Processing Time: 9.2 seconds
Compliance Score: 75%
  - TONE_001: Phrase "lightning-fast" is intensifier; use factual descriptors per brand_voice:§3
    Evidence: Semantic analysis detected speed-based hyperbole relative to Strand voice guidelines.
  - CLAIM_005: "fastest" is implicit superlative claim; requires FCC or independent benchmark data
    Evidence: LLM detected unstated performance superiority claim not supported by provided evidence.
  - BRAND_DRIFT_003: Tone leans promotional; Strand voice emphasizes reliability over excitement.
    Evidence: Semantic vector analysis shows 0.87 similarity to "premium marketing" vs 0.42 to "technical confidence".
```

DJ-008 states: use deterministic mode for routine checks (turnaround under 2 seconds, rule violations only); use LLM mode for campaigns with subtle messaging, brand tone risk, or implicit claims (turnaround 8-15 seconds, semantic depth required).

## Inspecting and Verifying the WORM Chain

The WORM (Write Once Read Many) chain is the immutable audit log of all governance decisions. Only `run_governance_workflow()` can append entries. Users can read and verify but cannot modify chain entries.

### Reading Chain Entries

```python
from brandguard.chain.worm_chain import WORMChain

chain = WORMChain(storage_path="data/worm_chain.log")

# Read the last 5 entries
recent_entries = chain.read_last_n(5)

for entry in recent_entries:
    print(f"Entry ID: {entry.id}")
    print(f"Timestamp: {entry.timestamp}")
    print(f"Asset: {entry.asset_id}")
    print(f"Decision: {entry.decision}")
    print(f"Hash: {entry.hash}")
    print("---")
```

**Expected output:**
```
Entry ID: 42
Timestamp: 2025-01-15T14:32:09Z
Asset: email_campaign_strand_q1_2025
Decision: approve
Hash: 0x7f2a9c... (SHA-256)
---
Entry ID: 41
Timestamp: 2025-01-15T14:18:33Z
Asset: social_post_5g_launch
Decision: flag_for_review
Hash: 0x3e8b1d...
---
```

### Verifying Chain Integrity

```python
from brandguard.chain.worm_chain import verify_chain

# Verify that the entire chain is intact and unaltered
verification_result = verify_chain("data/worm_chain.log")

print("Chain Valid:", verification_result.is_valid)
print("Total Entries:", verification_result.entry_count)
print("Integrity Checks Passed:", verification_result.checks_passed)
print("Integrity Checks Failed:", verification_result.checks_failed)

if not verification_result.is_valid:
    for error in verification_result.errors:
        print(f"  Error at entry {error.entry_id}: {error.message}")
```

**Expected output:**
```
Chain Valid: True
Total Entries: 127
Integrity Checks Passed: 127
Integrity Checks Failed: 0
```

If chain integrity is compromised (e.g., an entry is altered), `verify_chain()` returns `is_valid: False` and lists the entry ID and hash mismatch. See src/brandguard/chain/worm_chain.py for the cryptographic verification logic.

## Entry-Level Operations

WORM logging records only final governance decisions (approve, reject, flag_for_review), not intermediate rule evaluation steps. This design balances audit completeness with storage efficiency. When `run_governance_workflow()` completes, one entry is appended to the chain containing the asset ID, timestamp, all three gate decisions, and a cryptographic hash linking to the previous entry.

For compliance investigations, retrieve the relevant workflow result from the WORM chain entry and cross-reference it with evaluation reports generated during the same session. Reports are stored separately in src/brandguard/evaluation/report_cache/ and are not part of the chain itself.
