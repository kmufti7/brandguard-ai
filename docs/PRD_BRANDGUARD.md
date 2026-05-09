# BrandGuard AI: Product Requirements Document

**Version:** 0.1 (paper architecture)
**Last updated:** 2026-05-09
**Owner:** Kaizen Works, LLC
**Author:** Kamil Mufti
**Status:** Pre-MVP

---

## 1. Product Overview

BrandGuard AI is a marketing AI product that lets marketers describe an audience in natural language, segment it from an internal CRM corpus, generate brand-safe campaign copy with required citations, and route every output through a fail-closed legal/brand review gate before publication. Each step writes to a tamper-evident audit log; each request is metered for cost; every model output is evaluated for hallucination against a deterministic citation check before release.

The product is positioned as a governed marketing AI platform. Marketing teams that adopt agentic copy generation typically lose visibility into brand-voice drift, citation provenance, and legal exposure. BrandGuard treats those losses as design constraints and ships with the controls in place from day one rather than retrofitted.

---

## 2. Problem Statement

Marketing organizations adopting LLM-based copy generation face four recurring failures:

1. **Audience targeting is opaque.** Marketers describe a segment in natural language, but the resulting audience either lacks segmentation logic or cannot be audited.
2. **Brand voice drifts.** Without grounded retrieval, generated copy reflects the foundation model's tone instead of the brand's voice document.
3. **Citations are absent or fabricated.** Copy referring to product specifications cannot be traced back to source documents.
4. **Legal review is bolted on after the fact.** Reviewers see only finished copy, not the retrieval grounding or the segmentation logic that produced it.

BrandGuard addresses each failure with a dedicated component and a shared audit trail.

---

## 3. Target Users

BrandGuard targets two audiences: marketing teams who use the product, and AI product managers evaluating governed marketing AI for adoption.

| User | Goal | What BrandGuard provides |
|------|------|-------------------------|
| Marketing manager | Generate campaign copy for a defined segment without creative-team round trips | Audience Discovery Agent + RAG Copy Generation Agent |
| Brand lead | Enforce brand voice across generated copy | Brand voice document as RAG source; citation-required output |
| Legal/compliance reviewer | Approve or reject copy with full context (segmentation, retrieval grounding, citations) | Legal/Brand Review Gate with WORM audit trail |
| ML/platform owner | Measure hallucination rate and cost per request | Hallucination Evaluation Harness + Token FinOps Tracker |
| AI product manager (evaluator) | Assess whether a governed marketing AI product meets brand-safety, audit, and hallucination-control requirements before procurement | Documented architecture, ADRs, hallucination eval harness output, WORM audit trail, fail-closed legal/brand gate |

---

## 4. Scope

### In scope (MVP)

- Natural-language audience discovery against a synthetic CRM corpus of 500 records, telecom-flavored
- RAG copy generation against a brand voice document and a product fact sheet (single product line, 3-5 SKUs)
- Human-in-the-loop legal/brand review gate with fail-closed semantics
- Hallucination evaluation harness with ragas metrics and deterministic citation checks
- WORM audit log for every component decision
- Per-request token cost tracking
- Kill-switch primitive applied to the legal review gate

### Out of scope (MVP)

- **Multi-brand support.** MVP supports a single brand voice document. Multi-brand routing, per-brand approval policies, and brand-isolation tenancy are out of scope.
- **API wrapper / hosted service.** BrandGuard ships as a library and CLI for the paper-architecture and code phases. A hosted REST or gRPC surface is not in MVP scope.
- **Traction claims.** This product makes no claims about user adoption, customer logos, MRR, or pilot deployments. Anyone reading this PRD should treat all language about deployment as descriptive of capability, not of adoption.
- **Customer deployments.** No live customer data, no production tenants, no customer references. MVP runs on synthetic telecom-flavored data only.

---

## 5. Components

### 5.1 Native components

#### Audience Discovery Agent

Natural-language query → segmented audience over a 500-record synthetic CRM corpus. Returns a structured audience definition (segmentation criteria, record IDs, count) and a human-readable summary. Backed by FAISS local vector store. See ADR-001.

#### RAG Copy Generation Agent

Generates campaign copy grounded in a brand voice document and product fact sheet. Output is required to include inline citations linking each factual claim to a retrieved source chunk. Generation that fails the citation check is not returned to the caller. See ADR-002.

#### Legal/Brand Review Gate

Human-in-the-loop approval step with fail-closed semantics. Extends the Kill-Switch Guard primitive from `intelliflow-core` v2. Routing decisions (route to reviewer, auto-pass on whitelist, auto-block on blacklist) use deterministic rule evaluation, not LLM-judged classification. See ADR-003.

#### Hallucination Evaluation Harness

ragas-based evaluation framework. Tracks faithfulness, answer relevance, context precision, and context recall. Hallucination scoring is paired with a deterministic citation check; a high faithfulness score from ragas is necessary but not sufficient for release. See ADR-004.

### 5.2 Reused governance primitives (from `intelliflow-core` v2)

#### WORM Logger

Write-once, read-many audit log. Every component (audience query, retrieval call, generation call, review decision, eval result) appends an immutable record. Used for legal review context, post-hoc audit, and the input to evaluation regression tests.

#### Kill-Switch Guard

Fail-closed enforcement primitive. The Legal/Brand Review Gate extends this primitive: if any precondition for release is missing or unverifiable, the output is blocked rather than released.

#### Token FinOps Tracker

Per-request token counting and cost attribution. Tracks input tokens, output tokens, model identifier, and component identifier per call. Aggregated cost reports are queryable by component and by audience segment.

---

## 6. Success Criteria

The MVP is considered complete when all five criteria below are met. Each criterion has a deterministic check; none rely on LLM judgment.

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test suite | 12 or more tests passing across the four native components | `pytest` exit code 0; test count surfaced in CI output |
| Hallucination evaluation | A ragas evaluation report exists for the golden dataset and is reproducible run-over-run | ragas report artifact committed under `evals/`; rerun produces consistent metric scores within tolerance |
| Citation enforcement | Deterministic citation check rejects any generation with an uncited factual claim | Unit tests cover positive and negative cases; release-time check is the gate, not an LLM judge |
| Lineage disclosure | README clearly discloses `intelliflow-core` v2 as the upstream governance kernel and links the IntelliFlow OS repo | Manual README review against lineage policy |
| Audit cleanliness | Codex audit pass on the project (architecture, lineage, language rules, scope discipline) returns clean | Codex audit run; report filed under `audits/` |

---

## 7. Non-Goals

- BrandGuard does not perform marketing performance attribution (open rate, conversion, ROI). It produces copy and segments; downstream systems measure performance.
- BrandGuard does not generate images, video, or any non-text asset.
- BrandGuard does not replace a marketing operations platform. It feeds one.
- BrandGuard does not auto-publish copy. Human approval through the Legal/Brand Review Gate is required for release.
- BrandGuard does not learn from approved/rejected reviews in MVP. Reviewer feedback is logged but not used for online learning.

---

## 8. Compliance Posture

BrandGuard ships with these compliance properties:

- **Brand-safety enforcement** through deterministic verification rules at the Legal/Brand Review Gate
- **Human-in-the-loop legal review** as a hard requirement before any output is released
- **Citation-required output** enforced at generation time; uncited claims fail the gate
- **Hallucination evaluation harness** with deterministic citation checks paired alongside ragas metrics
- **Audit trail** via WORM Logger covering every component decision

BrandGuard does NOT claim:

- GDPR compliance (the product handles synthetic data only in MVP; production GDPR posture requires data residency and DSAR workflow that are out of MVP scope)
- Brand-safety certification from any third-party body
- Marketing operations platform certification (BrandGuard is not a marketing automation tool)

These are deliberate omissions. Compliance certifications are scoped product claims, not implementation details, and BrandGuard does not assert any that it has not earned.

---

## 9. Open Questions

None open as of 2026-05-09. All architectural decisions for paper architecture phase are recorded in the ADRs under `docs/adr/`.
