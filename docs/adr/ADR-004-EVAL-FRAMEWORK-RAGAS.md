# ADR-004: Eval Framework (ragas)

**Status:** Accepted (paper)
**Date:** 2026-05-09
**Deciders:** Kamil Mufti
**Component:** Hallucination Evaluation Harness

---

## Context

BrandGuard generates copy that makes factual claims. Even with RAG grounding and inline citations (ADR-002), the system needs an offline measurement framework that quantifies hallucination rate, retrieval relevance, and answer quality on a stable golden dataset. Without it, prompt changes, model swaps, and retrieval-tuning changes have no regression signal.

The eval framework has three jobs:

1. Score generations on a recurring basis (weekly minimum) against a curated golden dataset.
2. Detect regressions across configuration changes (model version, prompt template, retrieval parameters).
3. Provide a reproducible quality bar that the citation check (release-time) cannot, because release-time checks are per-output and binary, while eval is corpus-level and continuous.

The framework choice has to satisfy three constraints: it must be open-source, it must integrate with foundation-model-agnostic generation, and its hallucination scoring must be paired with deterministic checks at release time per DNA §8.

---

## Decision

Adopt `ragas` as the primary evaluation framework. Track four metrics: faithfulness, answer relevance, context precision, context recall. Pair every ragas hallucination measurement with a deterministic citation check; ragas alone is not sufficient to gate a release. Build a golden dataset of 20-30 marketing scenarios in Session 4.

### Why ragas (and why ragas over DeepEval)

- **Industry recognition.** ragas is the most widely cited open-source RAG eval framework in 2025-2026 practitioner literature. Choosing it gives BrandGuard a metric vocabulary that an evaluating AI PM can compare against published baselines.
- **Job description keyword match.** "ragas" appears as a named requirement in AI/ML hiring posts that mention RAG evaluation; DeepEval appears less often in that bracket. For a product whose audit and lineage discipline is part of its differentiation, using the framework that procurement-side evaluators recognize matters.
- **RAG-specific design.** ragas is purpose-built around retrieval-augmented generation: faithfulness, answer relevance, context precision, and context recall are first-class metrics. DeepEval is a broader LLM-eval framework whose RAG metrics are one module among many; the RAG-specific framing in ragas is a closer fit to BrandGuard's failure modes.
- **Better LangGraph integration.** ragas has more mature integration patterns with LangGraph-orchestrated pipelines, which BrandGuard's agent layer is likely to adopt. DeepEval integration is possible but less idiomatic.
- **Open-source, actively maintained, framework-agnostic.** Works with any generation backend BrandGuard might use; integrates with standard test runners; can be invoked from CI or scheduled jobs without a service dependency. Output schema is structured (per-metric scores per scenario), suitable for storage in WORM and for regression diffs.

### The four metrics

| Metric | What it measures | BrandGuard interpretation |
|--------|------------------|--------------------------|
| **Faithfulness** | Are claims in the generation supported by the retrieved context? | Hallucination signal. Low faithfulness = generation invented details. |
| **Answer Relevance** | Does the generation actually address the prompt? | Off-topic generation signal. |
| **Context Precision** | Are the retrieved chunks the right ones (signal-to-noise of retrieval)? | Retrieval tuning signal. Low precision = retriever pulling junk. |
| **Context Recall** | Did retrieval find all the chunks needed to answer? | Retrieval coverage signal. Low recall = missing source material. |

These four metrics are reported per scenario and aggregated across the golden dataset. A regression is defined as any metric dropping more than a configurable threshold (proposed: 5 percentage points) compared to the rolling 4-week baseline.

### Pairing rule: hallucination metrics MUST include deterministic citation checks (DNA §8)

Per DNA §8, decisions that gate release must be deterministic verification, not LLM-judged routing. ragas's faithfulness metric uses LLM-as-judge methodology under the hood: an LLM is asked whether a claim is supported by the context. This is appropriate for offline measurement (regression detection, trend tracking), but it is not appropriate as a release-time gate because:

1. LLM judgment is non-deterministic (same input, different scores across runs)
2. LLM judgment is non-reproducible across model versions
3. Release-time gating requires a yes/no answer that is auditable in code

The pairing rule:

- **At release time** (per generation): the deterministic citation check from ADR-002 is the authoritative pass/fail. ragas faithfulness is not consulted.
- **Offline** (per evaluation run): ragas faithfulness is the regression signal. The deterministic citation check is also recorded so that disagreement between the two can be inspected (e.g., a generation passes the deterministic check but ragas flags faithfulness; this surfaces tuning needs in the citation-match heuristic).

This dual-track design means the deterministic check protects every release while the ragas signal informs the longer-horizon question of whether the system is drifting.

### Golden dataset target: 20-30 marketing scenarios in Session 4

The golden dataset is the eval framework's input. MVP target: 20-30 marketing scenarios to be authored in Session 4. Each scenario contains:

- Audience description (natural-language input to the Audience Discovery Agent)
- Campaign brief (input to the RAG Copy Generation Agent)
- Expected source citations (which brand-voice sections and which fact-sheet entries should appear)
- Optional reference copy (a human-authored target for answer-relevance and qualitative review)

20-30 is the minimum for stable aggregate metrics across the four ragas measurements at this corpus size. Below 20 the metrics swing on individual scenario noise; above 30 the marginal regression detection benefit is small for the dataset-maintenance cost. Re-evaluate the upper bound when production traffic provides natural scenarios that can be promoted into the golden set.

The golden dataset is versioned and scenarios are immutable once added (additions only, no edits). This ensures that month-over-month metric movement reflects system change, not dataset change.

---

## Consequences

### Positive

- ragas is the standard RAG eval framework; using it gives BrandGuard a comparable and explainable metric vocabulary
- Four-metric coverage maps to BrandGuard's actual failure modes
- Pairing with deterministic citation checks keeps release-time decisions DNA §8-compliant
- Golden dataset is a small, owned artifact that grows with the product

### Negative / accepted trade-offs

- ragas runs cost foundation-model calls per scenario per metric; weekly evals on 20-30 scenarios across 4 metrics is the budget. Tracked via Token FinOps Tracker.
- Golden dataset authoring is a real Session 4 cost (estimated 1 day for 20 scenarios, more if reference copy is required)
- ragas faithfulness uses LLM-as-judge, which is a known noisy measurement. Mitigation: report rolling averages and treat single-run swings as noise unless they cross the 5-point threshold.
- The deterministic citation check and ragas faithfulness can disagree. By design, this disagreement is itself a signal worth investigating, not a contradiction to suppress.

---

## Alternatives Considered

- **DeepEval.** Broader LLM-eval framework with RAG metrics as a subset. Rejected as primary because (a) RAG-specific framing in ragas is a closer fit to BrandGuard's four failure modes, (b) ragas has stronger industry/hiring recognition for RAG eval, and (c) LangGraph integration is more idiomatic on the ragas side. DeepEval may be added later as a secondary harness for non-RAG eval surfaces, but it is not the primary release-time eval framework.
- **TruLens.** Comparable functionality, smaller community at this date. Same reasoning as DeepEval applies; ragas's RAG-specific metric set is closer to BrandGuard's needs.
- **Custom eval harness only (no framework).** Rejected: reinventing well-defined metrics has no upside; ragas's metric definitions are documented and comparable.
- **LLM-as-judge for the release gate.** Rejected: violates DNA §8. The release gate uses the deterministic citation check from ADR-002.
- **Larger golden dataset (100+ scenarios) at MVP.** Rejected: dataset maintenance is real work; 20-30 is sufficient for stable aggregate metrics and can grow with production traffic in later sessions.
