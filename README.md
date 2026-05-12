---
state: VERIFIED
timestamp: 2026-05-12T00:09:00.966391+00:00
brief: scripts/doc_pipeline/briefs/readme.brief.md
mode: encoded
plugin_command: 
framework: working_backwards
word_count_floor: 800
---

# BrandGuard AI README

## Product Overview

You can now describe your audience in plain English, and BrandGuard AI will segment it from a 500-record synthetic customer database, generate campaign copy with mandatory source citations, route it through a deterministic legal and brand review gate, and produce a tamper-evident audit trail of every decision. No guesswork. No unsigned claims. A marketer types "Active business customers in Texas with annual revenue over $2M" into the Audience Discovery Agent, the system returns a filtered segment with record counts and matching criteria, feeds that segment into the RAG Copy Generation Agent along with brand voice guidelines and product fact sheets, receives draft campaign copy tagged with citations to those exact sources, submits the copy to the Legal/Brand Review Gate, and either ships it (if all citations resolve and required disclosures are present) or fails safely with a specific rejection reason. Every step writes to an append-only HMAC-SHA256-verified log. This is the first governed marketing AI product built on a deterministic review architecture instead of post-hoc auditing.

## How It Works: Four Native Components

**Audience Discovery Agent** extracts filter logic from natural language queries using an LLM, then applies those filters deterministically over the synthetic CRM corpus. The agent outputs segment membership with counts and decision traces so you know exactly why records matched.

**RAG Copy Generation Agent** retrieves relevant sections from the brand voice documentation (data/brand_voice.md) and product fact sheets using FAISS vector retrieval, then generates campaign copy with required citations embedded. Every claim ties back to a source. The LLM cannot generate citations; it can only include retrieval results, so hallucinations are bounded by what the corpus contains.

**Legal/Brand Review Gate** applies three deterministic rules in fail-closed mode per ADR-003. First, every citation anchor must resolve to an actual section in the sourced documents. Second, if the campaign mentions autopay, automatic renewal, or recurring charges, the copy must include the FTC-required plain-language disclosure. Third, unlimited plans must disclose data throttling thresholds if any apply. No LLM interprets these rules. A Python checker runs the validation in order and rejects the entire campaign if any rule fails, producing a specific error message so you know what to fix.

**Hallucination Evaluation Harness** measures faithfulness using ragas-style LLM-judged metrics (answer relevance, faithfulness scores) and three deterministic checks: citation coverage (percentage of claims with citations), citation validity (all citations resolve), and fact consistency (no contradictions between campaign text and source fact sheets). The harness runs on every generated campaign and writes results to eval_output/eval_report_llm.md.

BrandGuard AI also inherits governance primitives from its upstream kernel, intelliflow-core: the WORM Logger provides cryptographic append-only storage using HMAC-SHA256 hash chains and SQLite triggers that prevent deletion or modification of audit records; the Kill-Switch Guard allows immediate circuit-breaking of unsafe LLM outputs; the Token FinOps Tracker measures and caps LLM inference costs per campaign. These upstream governance components are reused as-is, not reimplemented.

The Doc QC pipeline (Author, Critic, Verifier, and Orchestrator agents) that produced this README also runs on every internal document you produce, ensuring consistency with brand voice, factual accuracy against decision records, and compliance with citation rules before publication.

## Lineage Disclosure

BrandGuard AI consumes intelliflow-core as its upstream governance kernel. The WORM Logger, Kill-Switch Guard, and Token FinOps Tracker components are inherited directly; BrandGuard adds four native agents and the deterministic Legal/Brand Review Gate on top. BrandGuard is a distinct product, not a module or extension of intelliflow-core. The upstream kernel provides the tamper-evidence and safety primitives; BrandGuard builds the marketing AI workflows.

## Setup

Requires Python 3.11 or later (3.12 used in development).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ../intelliflow-core
pip install -e .[dev]
pytest -q
```

The `[dev]` extra includes pytest, ragas, FAISS, and documentation dependencies. The intelliflow-core package must be installed first so that governance imports resolve correctly.

## Quick Example

```python
from brandguard.workflow import run_workflow

result = run_workflow(
    audience_query="Active business customers in Texas with annual revenue over $2M",
    campaign_brief="Q2 enterprise promotion for Unlimited+ plan"
)

print(result.audience_segment)      # List of matching CRM records
print(result.generated_copy)        # Brand-safe campaign text with citations
print(result.review_gate_decision)  # APPROVED or REJECTED with reason
print(result.audit_log_hash)        # HMAC-SHA256 chain hash for this run
```

The `run_workflow` function in src/brandguard/workflow.py orchestrates the four agents in sequence. It returns a result object containing the segment, the copy, the gate decision, and the cryptographic log hash. If the review gate rejects the copy, the decision field includes the rule that failed and the missing or invalid citation.

## How To Read The Evaluation Evidence

Two reports document product behavior:

- **docs/eval_report_deterministic.md** contains committed, reproducible results: citation validity rates, disclosure detection accuracy, and deterministic metric scores. This file is stable across commits.
- **eval_output/eval_report_llm.md** is regenerated each time you run the evaluation suite. It contains ragas-style LLM-judged faithfulness and relevance scores. This file is gitignored because LLM outputs vary slightly.

Run `pytest src/brandguard/eval/ -q` to regenerate the LLM report. Start with the deterministic report to understand baseline guarantees, then read the LLM report to see production hallucination metrics.

## Documentation Map

**Product Documentation**

- docs/PRODUCT_OVERVIEW.md: Feature summary and value proposition.
- docs/USER_PERSONAS.md: Marketer, compliance officer, and product manager workflows.
- docs/USE_CASES.md: Email campaigns, social ads, and promotion rules.
- docs/SUCCESS_METRICS.md: How to measure adoption, safety, and campaign performance.
- docs/ROADMAP.md: Planned features for Q2 and Q3 2026.

**Engineering Documentation**

- docs/ARCHITECTURE.md: Detailed component design, data flow, and interface contracts.
- docs/USAGE.md: API reference and common patterns.
- docs/CONTRIBUTING.md: Pull request process and code review standards.
- docs/MLOPS_PLAYBOOK.md: Model serving, retraining, and inference monitoring.
- docs/INTEGRATION_SURFACE.md: How to connect BrandGuard to your CRM and approval systems.

**Governance Documentation**

- docs/decision_journal.md: Append-only Decision Journal with 17+ entries documenting design choices, trade-offs, and reviewed assumptions.
- docs/adr/: Architecture Decision Records ADR-001 through ADR-004 covering LLM safety, determinism, and citation requirements.
- docs/pdr/: Product Decision Records PDR-001 through PDR-004 covering feature scope and user experience choices.

**Brand & Style**

- data/brand_voice.md: Eight voice principles and writing style guide for Strand Wireless brand communications.

## License

Copyright 2026 Kaizen Works, LLC. Licensed under the Apache License, Version 2.0. See LICENSE for full terms.
