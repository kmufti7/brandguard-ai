# BrandGuard AI: Session 4 Eval Report

Output of `scripts/run_eval_report.py` against the full golden dataset (20 scenarios). Scores recomputed live against the real Anthropic API; deterministic metrics will be byte-identical across runs.

**Generated:** `2026-05-10T02:17:22.342981+00:00`

## Per-metric averages

| Metric | Average | Notes |
|--------|---------|-------|
| faithfulness (LLM) | 0.674 | ragas semantics, Claude Haiku 4.5 judge |
| answer_relevance (LLM) | 0.450 | ragas semantics, Claude Haiku 4.5 judge |
| context_precision (deterministic) | 0.119 | retrieved ∩ expected / retrieved |
| context_recall (deterministic) | 0.258 | retrieved ∩ expected / expected |
| citation_existence (deterministic) | 0.950 | mirrors gate's citation existence rule |
| brand_voice_alignment (deterministic) | 0.920 | em dashes, intensifiers, autopay/unlimited disclosures, numbers in pricing context |

## Per-scenario breakdown

| ID | Expected | Observed | KS | Faith | Rel | Prec | Rec | CitEx | BV | BV violations |
|----|----------|----------|----|-------|-----|------|-----|-------|----|---------------|
| G001 | ALLOW | ALLOW | no | 0.80 | 0.35 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G002 | ALLOW | ALLOW | no | 1.00 | 0.20 | 0.12 | 0.33 | 1.00 | 0.80 | §4.8 em dash present |
| G003 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.12 | 0.33 | 1.00 | 0.80 | §4.8 em dash present |
| G004 | ALLOW | ALLOW | no | 1.00 | 0.15 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G005 | ALLOW | ALLOW | no | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.80 | §4.8 em dash present |
| G006 | ALLOW | ALLOW | no | 1.00 | 0.85 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G007 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G008 | ALLOW | ALLOW | no | 1.00 | 0.85 | 0.25 | 0.67 | 1.00 | 1.00 |  |
| G009 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G010 | ALLOW | ALLOW | no | 1.00 | 0.75 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G011 | ALLOW | ALLOW | no | 1.00 | 0.65 | 0.12 | 0.50 | 1.00 | 1.00 |  |
| G012 | ALLOW | ALLOW | no | 0.00 | 0.00 | 0.12 | 0.50 | 1.00 | 0.80 | §4.8 em dash present |
| G013 | ALLOW | ALLOW | no | 1.00 | 0.45 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G014 | ALLOW | ALLOW | no | 1.00 | 0.35 | 0.00 | 0.00 | 1.00 | 1.00 |  |
| G015 | ALLOW | ALLOW | no | 1.00 | 0.85 | 0.12 | 0.33 | 1.00 | 1.00 |  |
| G016 | BLOCK | BLOCK | no | 0.00 | 0.60 | 0.00 | 0.00 | 0.00 | 1.00 |  |
| G017 | BLOCK | BLOCK | no | 0.00 | 0.60 | 0.00 | 0.00 | 1.00 | 0.80 | autopay disclosure missing while quoting $[45] |
| G018 | BLOCK | BLOCK | no | 0.00 | 0.85 | 0.12 | 0.50 | 1.00 | 0.80 | §4.2 'unlimited' without 100 GB soft cap and 5 Mbps post-cap |
| G019 | BLOCK | n/a | YES | n/a | n/a | 1.00 | 1.00 | 1.00 | 1.00 |  |
| G020 | ALLOW | BLOCK | no | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.60 | §4.8 em dash present; §4.2 'unlimited' without 100 GB soft cap and 5 Mbps post-cap |

## Identified mismatches (expected vs observed)

- **G020**: expected `ALLOW`, observed `BLOCK`

## Notes on metric design

- **LLM-judged metrics** (faithfulness, answer_relevance) follow ragas semantics. They are appropriate for offline regression but never gate releases (per DNA §8).
- **Deterministic metrics** (context precision/recall, citation existence, brand voice) produce byte-identical scores across runs and are safe for release-gate comparisons.
- **Brand voice alignment is deterministic, not rubric-scored.** The rules we can encode in code (em dashes, filler intensifiers, autopay disclosure, unlimited disclosure, numbers in pricing context) are scored mechanically. Principles that resist mechanical encoding (§3 personality traits, tone-by-context judgment) are not in this metric: they remain human-reviewer territory.
