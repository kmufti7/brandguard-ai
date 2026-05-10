# BrandGuard AI

**Status:** Pre-MVP, paper architecture phase
**License:** Apache 2.0
**Owner:** Kaizen Works, LLC
**Author:** Kamil Mufti

---

## Tagline

Audience discovery and brand-safe copy generation, governed by design.

---

## What It Is

BrandGuard AI is a marketing AI product that pairs natural-language audience discovery with brand-safe copy generation, gated by a deterministic legal/brand review step and measured by a hallucination evaluation harness. It targets marketing teams that need agentic copy production without giving up brand voice control or auditability.

The product is designed and built as a standalone agentic marketing platform: marketers ask for an audience, BrandGuard segments it from a CRM corpus, RAG-grounded copy is generated against approved brand voice and product fact sheets, the output passes through a fail-closed legal/brand gate before release, and every step is logged for audit.

---

## Architecture Overview

### Native components (built for BrandGuard)

1. **Audience Discovery Agent.** Natural language → segmented audience over a CRM corpus, with a FAISS local vector store and an explicit segmentation schema.
2. **RAG Copy Generation Agent.** Retrieval-augmented generation grounded on a brand voice document and product fact sheets. Citation-required output.
3. **Legal/Brand Review Gate.** Human-in-the-loop, fail-closed. Deterministic verification rules decide routing, not an LLM judge.
4. **Hallucination Evaluation Harness.** ragas-based eval framework with deterministic citation checks. Faithfulness, answer relevance, context precision, context recall.

### Reused governance primitives

BrandGuard reuses three governance primitives from the upstream `intelliflow-core` SDK:

1. **WORM Logger.** Write-once, read-many audit trail. Every component decision is appended.
2. **Kill-Switch Guard.** Fail-closed enforcement primitive that the Legal/Brand Review Gate extends.
3. **Token FinOps Tracker.** Per-request token accounting for cost attribution.

---

## Lineage Disclosure

BrandGuard AI consumes `intelliflow-core` as an upstream SDK (`pip install -e` pattern during development). The kernel provides cross-cutting governance primitives that apply equally to regulated and non-regulated AI domains: write-once audit logging, fail-closed enforcement, and per-token cost tracking. BrandGuard reuses three of those primitives and adds four marketing-specific components on top.

The kernel was originally factored out of regulated-industry work where audit-trail and fail-closed semantics are non-negotiable. Those same properties are useful in marketing AI for a different reason: brand reputation and legal exposure. Reusing the kernel keeps governance behavior consistent across products and avoids re-implementing the audit and kill-switch surfaces.

Upstream repository: [IntelliFlow OS](https://github.com/kmufti7/intelliflow-os) (link placeholder, replace with canonical URL when public).

---

## Setup

TBD in Session 2.

---

## How To Read The Eval Evidence

Two files. The split (DJ-008) keeps committed artifacts deterministic.

1. `docs/eval_report_deterministic.md`: committed; commit-stable metrics (context precision/recall, citation existence, brand voice alignment, throughput, latency). Regeneration produces byte-identical output.
2. `eval_output/eval_report_llm.md`: gitignored; LLM-judged metrics (faithfulness, answer relevance). Regenerate on demand via `python scripts/run_eval_report.py --both`. Scores drift run-to-run.

---

## License

Apache License 2.0. Copyright 2026 Kaizen Works, LLC. See `LICENSE` (added in Session 2).
