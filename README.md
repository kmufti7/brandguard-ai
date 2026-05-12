---
state: VERIFIED
timestamp: 2026-05-12T00:19:15.960939+00:00
brief: scripts/doc_pipeline/briefs/readme.brief.md
mode: encoded
plugin_command: 
framework: working_backwards
word_count_floor: 800
---

# BrandGuard AI README

## Product Overview

**Marketers at Strand Wireless can now describe an audience in plain English, and the system will deliver a brand-safe campaign within minutes, with every step logged immutably.** You write "target Midwest families, income 75k–150k, with kids, Android users," and BrandGuard AI extracts a machine-readable filter, runs it against a synthetic CRM corpus of 500 customer records, generates on-brand campaign copy with required citations to Strand's voice guidelines and product fact sheets, routes the output through a deterministic legal and brand review gate, and produces an audit trail that survives tampering. If the copy violates a brand rule, the gate blocks it and tells you why. If it passes, you get ALLOW, the final copy, and a cryptographically verified log chain.

The system does this by combining four native components: an Audience Discovery Agent that extracts filters from natural language; a RAG Copy Generation Agent that retrieves brand voice and product data to write copy; a Legal/Brand Review Gate that applies three deterministic compliance rules without any LLM in the path; and a Hallucination Evaluation Harness that judges whether the generated copy is faithful to the source material. These components sit on top of intelliflow-core, an upstream governance kernel that provides tamper-evident logging, financial tracking, and emergency kill-switch capability. The entire system is documented through a Doc QC pipeline (Author / Critic / Verifier / Orchestrator) that ensures consistency between source code, governance records, and user-facing prose.

## Architecture

BrandGuard AI is built from four purpose-built components plus three governance primitives inherited from intelliflow-core.

**Audience Discovery Agent.** The LLM reads your natural-language audience description and extracts a filter expression that names CRM fields and constraints (e.g., `region == 'Midwest' AND income_bracket == '75k-150k' AND has_children == True`). Once the filter is extracted, a deterministic Python evaluator applies it against a 500-record synthetic CRM corpus. The result is a list of matched customer IDs and their attributes. No LLM is involved in the filtering itself; the LLM generates the filter once, and a pure function applies it. This design removes LLM variance from a critical path.

**RAG Copy Generation Agent.** The system retrieves relevant fragments from the Strand Wireless brand voice document (data/brand_voice.md, which defines eight voice principles and seven citable sections) and from the product fact sheets for the five SKUs (Essentials, Pro, Family, Unlimited+, Business). A FAISS vector index makes retrieval fast. The LLM then generates campaign copy that weaves these sources together. Every claim in the output must include a citation to either the brand voice doc (e.g., [brand_voice:§3] for the value proposition section) or a fact sheet field (e.g., [fact_sheet:Pro:network_coverage]). Citations are not optional; the downstream Legal/Brand Review Gate will reject any copy that omits them.

**Legal/Brand Review Gate.** This is a deterministic, LLM-free router that applies three rules and fails closed. Rule 1: every citation in the generated copy must exist and resolve. Rule 2: if the copy mentions autopay, the disclosure "Autopay required; see terms" must appear. Rule 3: if the copy mentions unlimited data, the disclosure "Unlimited subject to fair-use policies" must appear. The gate outputs either ALLOW or BLOCK, along with a list of reasons if a block occurs. No LLM logic is in this path, per ADR-003. This ensures that compliance decisions are auditable and deterministic.

**Hallucination Evaluation Harness.** This component measures whether the generated copy is faithful to its sources. It uses ragas-style metrics: an LLM-judged faithfulness score (does the copy accurately reflect the brand voice and product data?) and answer-relevance score (does the copy address the campaign brief?). It also computes three deterministic metrics: citation count, citation resolution rate, and gate pass rate. The harness produces a JSON report for each run.

**Governance Primitives from intelliflow-core.** BrandGuard AI reuses three governance services from its upstream kernel:

- WORM Logger: writes every step (audience filter, retrieved documents, generated copy, gate decision, and final state) to an append-only SQLite database with HMAC-SHA256 hash chaining. Each log entry is cryptographically linked to the previous one, so tampering is detectable.
- Kill-Switch Guard: if a financial threshold is exceeded or a security flag is triggered, the kill-switch halts all inference immediately.
- Token FinOps Tracker: records LLM token usage (input and output) and cost per run, enabling quota management and cost attribution.

**Doc QC Pipeline.** This README and all governance documents were produced by a four-stage pipeline: Author writes the prose, Critic checks it against brief and brand voice, Verifier resolves all citations and ensures they exist, and Orchestrator integrates feedback and commits the final version. This pipeline is documented in the Decision Journal (docs/decision_journal.md).

## Lineage Disclosure

BrandGuard AI consumes intelliflow-core as its upstream governance kernel. Intelliflow-core provides the WORM Logger, Kill-Switch Guard, and Token FinOps Tracker that BrandGuard AI relies on for audit, safety, and cost tracking. BrandGuard AI adds its own agents (Audience Discovery, RAG Copy Generation, Hallucination Evaluation) and its own Legal/Brand Review Gate. The two products are separate; BrandGuard AI is a purpose-built marketing product that uses intelliflow-core's governance layer, not an extension or module of it.

## Setup

BrandGuard AI requires Python 3.11 or later (development was done with Python 3.12).

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. Activate it:
   ```bash
   source .venv/bin/activate
   ```

3. Install the upstream intelliflow-core kernel:
   ```bash
   pip install -e ../intelliflow-core
   ```

4. Install BrandGuard AI and its development dependencies:
   ```bash
   pip install -e .[dev]
   ```

5. Run the test suite:
   ```bash
   pytest -q
   ```

Tests are located in `tests/` and are run from the repository root.

## Quick Example

Here is a minimal workflow invocation:

```python
from brandguard.workflow import run_workflow

result = run_workflow(
    audience_query="Target families in the Midwest, household income 75k–150k, with children, Android preference.",
    campaign_brief="Promote the Family plan for back-to-school season."
)

# Inspect the result
print(f"Gate Decision: {result['final_state']['gate_decision']}")  # 'ALLOW' or 'BLOCK'
print(f"Generated Copy:\n{result['final_state']['generated_copy']}")
print(f"WORM Chain Verified: {result['worm_chain_verified']}")  # True if hash chain is intact
print(f"Trace ID: {result['trace_id']}")  # Unique identifier for this run
print(f"Citations: {result['final_state']['citations']}")  # List of citation anchors
print(f"Gate Reasons: {result['final_state']['gate_reasons']}")  # If BLOCK, why

# If gate_decision is 'BLOCK', inspect gate_reasons:
if result['final_state']['gate_decision'] == 'BLOCK':
    for reason in result['final_state']['gate_reasons']:
        print(f"  - {reason}")
```

The `run_workflow` function returns a dictionary with these top-level keys:

- `final_state`: a dict containing `audience_filter`, `matched_records`, `generated_copy`, `citations`, `gate_decision`, and `gate_reasons`.
- `worm_chain`: list of tamper-evident log entries.
- `worm_chain_verified`: boolean indicating whether the HMAC hash chain is intact.
- `trace_id`: a UUID that ties all logs for this run together.
- `node_timings_ms`: dict of milliseconds spent in each stage (discovery, RAG, gate, eval).
- `kill_switch_triggered`: boolean indicating whether the financial or security kill-switch was activated.

## How To Read The Evaluation Evidence

BrandGuard AI publishes two evaluation reports:

- **Deterministic Metrics:** see docs/eval_report_deterministic.md. This file is committed to version control and does not change unless you commit a new evaluation run. It reports citation resolution rate, gate pass rate, and correctness of the three deterministic compliance rules.
- **LLM-Judged Metrics:** see eval_output/eval_report_llm.md. This file is gitignored and regenerates each time you run `pytest` with evaluation enabled. It reports faithfulness and answer-relevance scores as computed by a separate LLM-based judge.

The Q1 split between deterministic and LLM-judged metrics ensures that compliance assertions are not dependent on LLM judgement, and that inference quality is tracked separately.

## Documentation Map

**Product Documentation:**
- docs/PRODUCT_OVERVIEW.md: high-level product narrative, personas, and use cases.
- docs/USER_PERSONAS.md: detailed profiles of campaign managers and compliance officers.
- docs/USE_CASES.md: concrete scenarios for Strand Wireless marketing teams.
- docs/SUCCESS_METRICS.md: OKRs and success criteria for Q1–Q3 2026.
- docs/ROADMAP.md: planned features and deprecations.

**Engineering Documentation:**
- docs/ARCHITECTURE.md: system design, data flow, and component specifications.
- docs/USAGE.md: configuration options, environment variables, and API reference.
- docs/CONTRIBUTING.md: branch strategy, coding standards, and review process.
- docs/MLOPS_PLAYBOOK.md: model serving, retraining, and monitoring.
- docs/INTEGRATION_SURFACE.md: webhook formats, event schemas, and downstream connectors.

**Governance Documentation:**
- docs/decision_journal.md: Decision Journal, append-only log of 21+ architectural and process decisions (entries DJ-001 through DJ-017 are current).
- docs/adr/: Architecture Decision Records ADR-001 through ADR-004, covering legal gate design, citation mechanics, LLM-free routing, and eval methodology.
- docs/pdr/: Product Decision Records PDR-001 through PDR-004, covering audience discovery, synthetic CRM design, brand voice versioning, and roadmap.
- data/brand_voice.md: Strand Wireless brand voice guide, including eight voice principles and seven citable sections (§1 through §7).

## License

BrandGuard AI is released under the Apache License 2.0. Copyright 2026 Kaizen Works, LLC.
