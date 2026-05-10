# BrandGuard AI: Session 4 Eval Report

> **Historical artifact.** This is the Session 4 combined report. As of Session 5A (Q1 split per DJ-008), eval evidence lives in two files: `docs/eval_report_deterministic.md` (committed, commit-stable metrics) and `eval_output/eval_report_llm.md` (gitignored, LLM-judged metrics that drift with model variance). This file is preserved as the historical record of the Session 4 run.

Output of `scripts/run_eval_report.py` against the full golden dataset (20 scenarios). Scores recomputed live against the real Anthropic API; deterministic metrics will be byte-identical across runs.

**Generated:** `2026-05-10T17:53:00.652980+00:00`

## Per-metric averages

| Metric | Average | Notes |
|--------|---------|-------|
| faithfulness (LLM) | 0.682 | ragas semantics, Claude Haiku 4.5 judge |
| answer_relevance (LLM) | 0.406 | ragas semantics, Claude Haiku 4.5 judge |
| context_precision (deterministic) | 0.119 | retrieved ∩ expected / retrieved |
| context_recall (deterministic) | 0.258 | retrieved ∩ expected / expected |
| citation_existence (deterministic) | 0.950 | mirrors gate's citation existence rule |
| brand_voice_alignment (deterministic) | 0.960 | em dashes, intensifiers, autopay/unlimited disclosures, numbers in pricing context |

## Throughput and Latency (D4)

Per-node and aggregate timings captured by `time.perf_counter()` around each node body in `src/brandguard/workflow.py`. Each node's elapsed_ms is also recorded in the WORM TOOL_EXECUTED exit payload.

**Per-node latency**

| Node | Avg (ms) | p95 (ms) | n |
|------|----------|----------|---|
| audience_discovery | 891.6 | 2093.7 | 19 |
| legal_brand_review_gate | 0.9 | 1.9 | 19 |
| rag_copy_generation | 2589.4 | 4675.0 | 19 |

**Aggregate**

- Per-scenario average total latency: **3481.9 ms**
- Throughput: **9.50 scenarios/minute**
- Wall-clock runtime: **126.32 s** for 20 scenarios

_Environment: Python 3.12.13, machine arm64, run at 2026-05-10._

## Per-scenario breakdown

| ID | Expected | Observed | KS | Faith | Rel | Prec | Rec | CitEx | BV | BV violations |
|----|----------|----------|----|-------|-----|------|-----|-------|----|---------------|
| G001 | ALLOW | ALLOW | no | 1.00 | 0.15 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G002 | ALLOW | ALLOW | no | 0.00 | 0.00 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G003 | ALLOW | ALLOW | no | 0.95 | 0.85 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G004 | ALLOW | ALLOW | no | 1.00 | 0.15 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G005 | ALLOW | ALLOW | no | 1.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G006 | ALLOW | ALLOW | no | 0.00 | 0.85 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G007 | ALLOW | ALLOW | no | 1.00 | 0.20 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G008 | ALLOW | ALLOW | no | 1.00 | 0.72 | 0.25 | 0.67 | 1.00 | 1.00 |  |
| G009 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G010 | ALLOW | ALLOW | no | 1.00 | 0.65 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G011 | ALLOW | ALLOW | no | 1.00 | 0.25 | 0.12 | 0.50 | 1.00 | 1.00 |  |
| G012 | ALLOW | BLOCK | no | 0.00 | 0.00 | 0.12 | 0.50 | 1.00 | 0.60 | §4.8 em dash present; §4.2 'unlimited' without 100 GB soft cap and 5 Mbps post-cap |
| G013 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G014 | ALLOW | ALLOW | no | 1.00 | 0.15 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G015 | ALLOW | ALLOW | no | 1.00 | 0.30 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G016 | BLOCK | BLOCK | no | 0.00 | 0.65 | 0.00 | 0.00 | 0.00 | 1.00 |  |
| G017 | BLOCK | BLOCK | no | 0.00 | 0.60 | 0.00 | 0.00 | 1.00 | 0.80 | autopay disclosure missing while quoting $[45] |
| G018 | BLOCK | BLOCK | no | 0.00 | 0.85 | 0.12 | 0.50 | 1.00 | 0.80 | §4.2 'unlimited' without 100 GB soft cap and 5 Mbps post-cap |
| G019 | BLOCK | n/a | YES | n/a | n/a | 1.00 | 1.00 | 1.00 | 1.00 |  |
| G020 | ALLOW | ALLOW | no | 1.00 | 0.65 | 0.00 | 0.00 | 1.00 | 1.00 |  |

## Identified mismatches (expected vs observed)

- **G012**: expected `ALLOW`, observed `BLOCK`

## Notes on metric design

- **LLM-judged metrics** (faithfulness, answer_relevance) follow ragas semantics. They are appropriate for offline regression but never gate releases (per DNA §8).
- **Deterministic metrics** (context precision/recall, citation existence, brand voice) produce byte-identical scores across runs and are safe for release-gate comparisons.
- **Brand voice alignment is deterministic, not rubric-scored.** The rules we can encode in code (em dashes, filler intensifiers, autopay disclosure, unlimited disclosure, numbers in pricing context) are scored mechanically. Principles that resist mechanical encoding (§3 personality traits, tone-by-context judgment) are not in this metric: they remain human-reviewer territory.
