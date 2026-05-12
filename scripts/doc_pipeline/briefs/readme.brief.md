---
audience: First-time repo visitors
depth: synthesizing
mode: encoded
plugin_command: 
framework: working_backwards
word_count_floor: 800
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: README.md

Produce a README that opens with Working-Backwards / PR-FAQ framing.

## Required structure (in order)

1. **Product Overview (lead).** What BrandGuard AI does for the marketer, written as if the product has shipped. A marketer describes an audience in natural language, the system segments it from a synthetic CRM corpus, generates brand-safe campaign copy with required citations, and routes it through a deterministic legal/brand review gate before release. Every step writes to a tamper-evident audit log.

2. **Architecture (how).** The FOUR native components: (a) Audience Discovery Agent (LLM extracts a filter, deterministic Python applies it over a 500-record synthetic CRM corpus); (b) RAG Copy Generation Agent (FAISS retrieval over the brand voice doc and product fact sheet, citation-required output); (c) Legal/Brand Review Gate (three deterministic rules, fail-closed: citation existence, autopay disclosure, unlimited disclosure; no LLM in the routing path per ADR-003); (d) Hallucination Evaluation Harness (ragas-style faithfulness and answer-relevance LLM-judged metrics plus three deterministic metrics). Plus the reused governance primitives from upstream intelliflow-core: WORM Logger (HMAC-SHA256 hash chain, append-only SQLite triggers), Kill-Switch Guard, Token FinOps Tracker. ALSO mention the Doc QC pipeline (Author / Critic / Verifier / Orchestrator) that produced this very README.

3. **Lineage disclosure.** BrandGuard AI consumes intelliflow-core as its upstream governance kernel. Do NOT subordinate BrandGuard. Use "upstream governance kernel", never "module of" / "extension of" / "vertical of".

4. **Setup.** Comes AFTER the product framing. Real steps: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -e ../intelliflow-core`, `pip install -e .[dev]`, `pytest -q`. Python 3.11+ (3.12 used in development).

5. **Quick example.** A short code snippet showing the actual API: `from brandguard.workflow import run_workflow`, then `run_workflow(audience_query="...", campaign_brief="...")`. Do NOT invent class names. The real entry point is `run_workflow` in `src/brandguard/workflow.py`.

6. **How To Read The Eval Evidence.** Point at `docs/eval_report_deterministic.md` (committed, commit-stable) and `eval_output/eval_report_llm.md` (gitignored, regenerates). Per the Q1 split.

7. **Documentation Map.** Point ONLY at files that exist. Product docs: `docs/PRODUCT_OVERVIEW.md`, `docs/USER_PERSONAS.md`, `docs/USE_CASES.md`, `docs/SUCCESS_METRICS.md`, `docs/ROADMAP.md`. Engineering: `docs/ARCHITECTURE.md`, `docs/USAGE.md`, `docs/CONTRIBUTING.md`, `docs/MLOPS_PLAYBOOK.md`, `docs/INTEGRATION_SURFACE.md`. Governance: `docs/decision_journal.md` (Decision Journal, append-only, 21+ entries), `docs/adr/` (ADR-001..ADR-004), `docs/pdr/` (PDR-001..PDR-004). Brand voice: `data/brand_voice.md` (eight-principle voice and style guide).

8. **License.** Apache License 2.0. Copyright 2026 Kaizen Works, LLC.

## Hard accuracy rules

- The package layout is `src/brandguard/__init__.py`, `src/brandguard/agents/`, `src/brandguard/governance/`, `src/brandguard/eval/`, `src/brandguard/workflow.py`, `src/brandguard/state.py`, `src/brandguard/llm.py`. There is NO `policies/`, NO `registry/`, NO `engine/` directory. Do not invent them.
- There is NO `ComplianceEngine` class, NO `BrandPolicy` class. The entry point is the function `run_workflow`.
- The brand voice doc has SEVEN citable sections (`§1` through `§7`) and EIGHT voice principles (principle 8 is the em-dash ban). Do not say "seven principles".
- Strand Wireless is a fictional brand for the synthetic corpus. Five SKUs: Essentials, Pro, Family, Unlimited+, Business.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. DO NOT emit [file:path] citation anchors; reference files in prose by name (e.g., src/brandguard/workflow.py) without the [file:...] syntax. The Verifier blocks unresolvable file citations and unresolvable backtick-quoted paths, so only name paths that actually exist.
