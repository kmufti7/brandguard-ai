# BrandGuard AI: Eval Report (Deterministic, commit-stable)

Committed artifact (Q1 split per DJ-008). Deterministic metrics only. Run against the full golden dataset (20 scenarios). Scores are byte-identical across runs.

## Per-metric averages (deterministic)

| Metric | Average | Notes |
|--------|---------|-------|
| context_precision | 0.119 | retrieved ∩ expected / retrieved |
| context_recall | 0.258 | retrieved ∩ expected / expected |
| citation_existence | 0.950 | mirrors gate's citation existence rule |
| brand_voice_alignment | 0.950 | em dashes, intensifiers, autopay/unlimited disclosures, numbers |

## Throughput and Latency (D4)

| Node | Avg (ms) | p95 (ms) | n |
|------|----------|----------|---|
| audience_discovery | 889.0 | 1653.8 | 19 |
| legal_brand_review_gate | 0.6 | 0.9 | 19 |
| rag_copy_generation | 1921.9 | 3101.7 | 19 |

- Per-scenario average total latency: **2811.5 ms**
- Throughput: **12.41 scenarios/minute**
- Wall-clock runtime: **96.73 s** for 20 scenarios

## Gate decision breakdown (deterministic)

| ID | Expected | Observed | KS |
|----|----------|----------|----|
| G001 | ALLOW | ALLOW | no |
| G002 | ALLOW | ALLOW | no |
| G003 | ALLOW | ALLOW | no |
| G004 | ALLOW | ALLOW | no |
| G005 | ALLOW | ALLOW | no |
| G006 | ALLOW | ALLOW | no |
| G007 | ALLOW | ALLOW | no |
| G008 | ALLOW | ALLOW | no |
| G009 | ALLOW | ALLOW | no |
| G010 | ALLOW | ALLOW | no |
| G011 | ALLOW | ALLOW | no |
| G012 | ALLOW | BLOCK | no |
| G013 | ALLOW | ALLOW | no |
| G014 | ALLOW | ALLOW | no |
| G015 | ALLOW | ALLOW | no |
| G016 | BLOCK | BLOCK | no |
| G017 | BLOCK | BLOCK | no |
| G018 | BLOCK | BLOCK | no |
| G019 | BLOCK | n/a | YES |
| G020 | ALLOW | ALLOW | no |

_Environment: Python 3.12.13, machine arm64._
