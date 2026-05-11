---
state: VERIFIED
timestamp: 2026-05-11T22:36:52.142980+00:00
brief: scripts/doc_pipeline/briefs/readme.brief.md
mode: encoded
plugin_command: 
framework: working_backwards
word_count_floor: 800
---

# BrandGuard AI README

## Product Overview

Marketing teams at Strand Wireless can now deploy governed AI agents that enforce brand compliance rules in real time, before marketing content reaches customers. A marketer writes copy, uploads an image, or proposes a campaign, and BrandGuard AI returns a compliance decision within milliseconds: approved, rejected, or flagged for human review. The system applies legal guardrails, brand voice standards, regulatory rules, and fact-sheet accuracy constraints to every asset, eliminating the delays of manual review cycles while preserving human judgment where it matters most.

BrandGuard AI achieves this through a four-component architecture: a governance rules engine that interprets brand policy in code form; a decision journal that logs every compliance decision with full reasoning; a fact-sheet registry that anchors product claims to vetted data; and a legal review gate that intercepts content before publication. These components are built on top of the intelliflow-core governance kernel, an open-source library that provides deterministic policy evaluation, audit trails, and appeal workflows. BrandGuard AI does not subordinate that upstream contribution. Instead, it extends intelliflow-core with marketing-specific rule schemas, guardrails tuned for telecom regulation, and Strand Wireless brand voice enforcement. The result is a system that speaks in Strand's authentic voice, respects legal boundaries, and gives compliance teams verifiable proof of every decision.

Lineage matters. BrandGuard AI consumes intelliflow-core (available at github.com/kaizen-works/intelliflow-core) as its governance kernel. That kernel was designed for deterministic rule evaluation in high-stakes domains. By reusing it, BrandGuard AI inherits proven audit capabilities, policy-as-code patterns, and cross-functional review mechanisms. This document describes the BrandGuard layer: how it wraps and extends intelliflow-core to make marketing AI compliant by default.

## Quick Start

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/kaizen-works/brandguard-ai.git
cd brandguard-ai
pip install -e .
```

BrandGuard AI requires Python 3.9+. It integrates with intelliflow-core 1.2.0 or later.

### First Decision

Create a simple brand policy rule and run a compliance check:

```python
from brandguard.governance import BrandPolicy
from brandguard.engine import ComplianceEngine

policy = BrandPolicy(
    brand_voice_section=1,
    legal_precedents=["DJ-001", "DJ-003"],
    fact_sheet_registry={"wireless_plan_unlimited": "fact_sheet:wireless_plan_unlimited:speed_limit"}
)

engine = ComplianceEngine(policy=policy)
decision = engine.evaluate(
    content="Get unlimited data on the fastest 5G network.",
    content_type="marketing_copy"
)

print(decision.status)  # "approved", "rejected", or "review_required"
print(decision.reasoning)
```

The `ComplianceEngine` returns a structured decision object. All decisions are logged to the decision journal (in `docs/decision_journal.md`) for audit purposes.

### Configuration

Brand policies live in `src/brandguard/policies/`. Each policy file maps compliance rules to specific brand domains: voice, legal, regulatory, and product accuracy. See the product documentation map below for detailed rule syntax.

## Architecture

BrandGuard AI consists of four components:

1. **Governance Rules Engine** (src/brandguard/governance/)
   - Interprets brand policy as executable rules
   - Evaluates content against Strand Wireless voice standards
   - Enforces legal and regulatory constraints
   - Returns deterministic compliance decisions

2. **Decision Journal** (docs/decision_journal.md)
   - Immutable log of all compliance decisions
   - Includes decision rationale, timestamp, and policy version
   - Supports post-hoc audit and appeal workflows
   - Currently contains 17 entries (DJ-001 through DJ-017)

3. **Fact-Sheet Registry** (src/brandguard/registry/)
   - Maps product claims to vetted marketing facts
   - Prevents over-claim and ensures consistency
   - Integrated with legal review gate to validate product statements
   - Sources data from Strand Wireless fact sheets

4. **Legal Review Gate** (src/brandguard/governance/legal_brand_review_gate.py)
   - Intercepts content before publication
   - Escalates claims that require legal sign-off
   - Routes ambiguous decisions to human reviewers
   - Maintains chain of custody for compliant assets

These components are implemented on top of intelliflow-core, which provides the underlying deterministic policy engine, audit trail mechanisms, and appeal infrastructure.

## Brand Voice Integration

BrandGuard AI enforces Strand Wireless brand voice during every compliance decision. The brand voice guide (data/brand_voice.md) defines seven sections covering tone, vocabulary, visual principles, technical accuracy, and regulatory candor. When a marketer submits content, the compliance engine measures conformance to these sections and either approves the asset, suggests revisions, or flags it for human review.

Example: A proposed email campaign uses the phrase "unleash your connectivity." The governance rules engine consults section 2 of the brand voice guide and identifies that "unleash" violates Strand's commitment to plain English and specificity. The engine rejects the asset and suggests: "Experience reliably fast 5G speeds, measured in Mbps, not metaphors."

## Contributing

Contributors should understand the governance framework before modifying rules or adding new policy types.

1. Read `docs/README_PRODUCT.md` for product architecture and user flows
2. Read `docs/README_ENGINEERING.md` for contributor guide, testing patterns, and dependency graph
3. Review existing decision journal entries (DJ-001 through DJ-017) to understand precedent
4. Add new rules to the appropriate policy file in src/brandguard/policies/
5. Write tests in tests/ that validate rule behavior against realistic marketing scenarios
6. Submit a pull request with a justification that references relevant decision journal entries or architectural records (ADR-001 through ADR-004)

All contributions must preserve the lineage to intelliflow-core and maintain audit trail integrity.

## Documentation Map

**Product Documentation:**
- `docs/README_PRODUCT.md`: User workflows, API reference, example policies

**Engineering Documentation:**
- `docs/README_ENGINEERING.md`: Architecture deep-dive, contributor guide, testing, dependency tree

**Governance:**
- `docs/decision_journal.md`: All compliance decisions and policy changes (DJ-001 through DJ-017)
- `docs/adr/`: Architectural decision records (ADR-001 through ADR-004)

**Brand Voice:**
- `data/brand_voice.md`: Seven-section Strand Wireless voice and style guide

## License

BrandGuard AI is copyright 2024 Kaizen Works, LLC and distributed under the Apache License 2.0. See LICENSE file for terms.
