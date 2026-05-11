---
state: VERIFIED
timestamp: 2026-05-10T23:41:40.207628+00:00
brief: scripts/doc_pipeline/briefs/product_overview.brief.md
mode: plugin
plugin_command: /write-spec
framework: 
word_count_floor: 600
---

# PRODUCT OVERVIEW: BrandGuard AI

## Problem Statement

Marketing teams using Large Language Models for copy generation face three converging risks that erode brand value and create legal exposure:

1. Brand-voice drift: LLM outputs diverge from established brand guidelines without detection, fragmenting customer perception and weakening brand equity. A marketer may approve 50 email variants without noticing cumulative tone drift until campaign performance suffers or brand audits flag inconsistency.

2. Citation opacity: Generated claims about products lack traceable provenance. When a marketing AI outputs "unlimited data speeds," there is no visible chain linking that statement to approved product facts. Legal and compliance teams cannot defend the claim's source in regulatory review or customer dispute. This creates unquantified legal exposure during FTC audits or warranty claims.

3. Audit defensibility gap: Current marketing AI tools (Jasper, Phrasee, Writer) log outputs but do not enforce immutable audit trails. If a generated claim becomes legally contested, the organization cannot prove which guardrails were active, which facts were consulted, or who approved the output. This gap compounds in regulated verticals (telecom, financial services) where proof of compliance governance is required.

These gaps translate directly to business risk: brand equity erosion reduces customer lifetime value; legal exposure triggers regulatory fines and remediation costs; audit failure during certification cycles delays product launches.

## Target User

This product targets four decision-maker personas:

1. **Marketing Manager (campaign owner)**: Needs confidence that AI-generated copy aligns with brand voice without manual review of every variant. Wants visibility into which facts support each claim.

2. **Brand Lead (governance owner)**: Enforces brand guidelines across channels. Requires proof that all generated copy passed deterministic brand and legal checks before publication.

3. **Legal/Compliance Reviewer**: Validates that marketing claims are factually sourced and that disclosure requirements (e.g., autopay terms, data limits) are present. Needs immutable audit logs for regulatory defense.

4. **AI Product Lead / Procurement Evaluator**: Assesses whether a governed marketing AI product meets enterprise security, auditability, and cost-control requirements. Compares against incumbent tools on governance depth and verifiability.

## Solution

BrandGuard AI is a four-component marketing AI system with three reused governance primitives from Anthropic's `intelliflow-core` kernel. Each component directly addresses a user need:

### Core Components

**Audience Discovery Agent**: LLM-powered audience segmentation that extracts structured filters (e.g., "customer tenure > 12 months AND plan type = Essentials") from natural-language briefs, then applies deterministic Python filters over a 500-record synthetic CRM corpus. Marketers describe their target segment in plain English; the system returns verified audience counts with explicit filter logic. Eliminates ambiguous targeting and provides audit trail of segmentation criteria.

**RAG Copy Generation Agent**: Retrieves brand voice guidelines and product fact sheets via FAISS semantic search, then generates marketing copy with required citations. Every claim in output includes inline references to source documents. Marketers verify facts are grounded; legal teams trace provenance. Typical generation latency is 2.6 seconds average, 4.7 seconds p95.

**Legal/Brand Review Gate**: Three deterministic rules enforce fail-closed guardrails: citation existence (all factual claims must cite source), autopay disclosure (if product includes recurring billing, disclosure text must be present), unlimited disclosure (if marketing mentions "unlimited" capability, product fact sheet must support it). Rules trigger blocking with no human review required. Gate latency is 0.9 ms p50, 1.9 ms p95.

**Evaluation Harness**: RAGAS-style metrics assess output quality via LLM-judged faithfulness (does generated copy reflect cited facts?) and answer relevance (does output address the campaign brief?). Deterministic metrics track gate pass/fail rates and citation density. Enables continuous monitoring of brand-voice drift and legal compliance.

### Governance Primitives (Reused from intelliflow-core)

**WORM Logger**: Append-only audit trail using HMAC-SHA256 hash chain and SQLite triggers. Every generation request, fact retrieval, gate decision, and approval is immutably logged with cryptographic integrity. Satisfies regulatory audit requirements and provides defense-in-depth for legal contests.

**Kill-Switch Guard**: Allows authorized users to immediately disable output generation if a policy violation is discovered post-publication. Prevents propagation of erroneous claims across campaigns.

**Token FinOps Tracker**: Monitors LLM API consumption per user, per campaign, per brand. Prevents cost overruns and surfaces high-utilization patterns for cost optimization.

## Competitive Positioning

BrandGuard AI differentiates against incumbent marketing AI products on governance depth and audit defensibility:

| Competitor | Strength | BrandGuard Differentiator |
|---|---|---|
| **Jasper** | Largest installed base, multi-language native support | Deterministic legal gate + WORM audit trail; citation-required output; kill-switch for post-publication remediation |
| **Phrasee** | Email optimization tuning via performance feedback loops | Fail-closed compliance gate with <2ms latency; immutable audit logs satisfy FTC/regulatory review without additional tooling |
| **Writer** | Fine-tuned models for brand voice, strong UX polish | Native integration of brand guidelines via FAISS RAG; deterministic fact verification; governed output vs. advisory warnings |
| **Persado** | Behavioral psychology-driven copy variants | Focus on compliance auditability over conversion optimization; stronger for regulated verticals (telecom, financial) than direct-response verticals |

**Where competitors are stronger**: Jasper and Writer have broader CMP (Campaign Management Platform) integrations and larger template libraries. Persado has deeper behavioral science tuning for conversion lift. BrandGuard is purposefully narrow: marketing copy generation + compliance, not full campaign orchestration or performance optimization.

**BrandGuard's moat**: Fail-closed deterministic gates (not warnings), immutable WORM logging, citation-required output. These are difficult to retrofit into LLM-first tools because they require system architecture changes. A marketer or legal team evaluating BrandGuard should ask: "Can competitor X prove to a regulator that every published claim was fact-checked?" The honest answer from Jasper/Writer/Phrasee is often "only with manual review." BrandGuard answers "yes, automatically, with immutable proof."

## Business Impact

**What BrandGuard AI Protects**

- **Brand Reputation**: Prevents tone/voice drift across campaigns by enforcing deterministic brand-gate rules. Quantifiable by reduction in brand-guideline violations flagged in post-campaign audits.
- **Legal Exposure**: Eliminates unsourced factual claims via citation-required output and deterministic disclosure gates. Reduces exposure to FTC enforcement (Telecom Act APD/DPD violations, Truth in Advertising Act claims).
- **Audit Defensibility**: WORM logger provides immutable proof of compliance governance. Satisfies SOC 2, ISO 27001, and regulatory audit requirements (HIPAA, GLBA, TCPA where applicable to telecom). Enables faster certification cycles.
- **Operational Risk**: Kill-switch guard allows rapid remediation if an erroneous claim reaches production, preventing full campaign rollout of a problematic variant.

**What BrandGuard AI Does NOT Measure**

- Campaign performance (click-through rate, conversion rate, revenue lift). BrandGuard is compliance/governance focused, not performance-optimization focused. Marketers still require A/B testing and analytics tools to measure campaign success.
- Conversion psychology or behavioral targeting. Persado and Phrasee optimize copy for persuasion; BrandGuard optimizes for legal/brand safety.
- Multi-channel orchestration, audience segmentation beyond CRM-based filters, or integration with email/social/web platforms. BrandGuard is copy-generation + gating, not a full marketing stack.

**Success Metrics for Procurement**: A PM evaluating BrandGuard should measure:
1. Time to legal approval of generated copy (reduction from manual review cycles).
2. Audit trail completeness (% of claims with visible citation + gate decision logged).
3. False-positive rate of deterministic gates (do rules block legitimate campaigns?).
4. Cost per generated variant (throughput: 9.5 scenarios/minute single-user serial; scale testing pending).

---

**Product Owner**: Kaizen Works, LLC  
**Author**: Kamil Mufti  
**License**: Apache 2.0  
**Governance Kernel**: intelliflow-core (WORM Logger, Kill-Switch Guard, Token FinOps Tracker)
