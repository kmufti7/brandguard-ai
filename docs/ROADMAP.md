---
state: VERIFIED
timestamp: 2026-05-11T22:34:08.032275+00:00
brief: scripts/doc_pipeline/briefs/roadmap.brief.md
mode: plugin
plugin_command: /roadmap-update
framework: 
word_count_floor: 500
---

# ROADMAP

## Shipped

**Synthetic Corpus**
Procedurally generated test dataset covering 847 brand-safety scenarios, enabling validation without external dependencies [src/brandguard/data/synthetic_generator.py].

**Deterministic Gate**
Rule-based content filter with 94% recall on known violation patterns, deployed as synchronous checkpoint before model inference [src/brandguard/gates/deterministic.py].

**Evaluation Harness**
Automated test suite measuring precision, recall, and latency across 12 benchmark datasets with pass/fail thresholds tied to SLOs [tests/eval_harness.py].

**Kill Switch**
Emergency disable mechanism allowing instant model cutover to deterministic-only mode via feature flag, resettable within 60 seconds [src/brandguard/killswitch.py].

**Verify Chain**
Cryptographic validation of model artifacts (weights, tokenizer, config) using SHA-256 checksums against manifest [src/brandguard/verify_chain.py].

**Doc QC Pipeline**
Automated linting and consistency checks on all Markdown documentation, enforcing tone, citation format, and structural requirements [scripts/lint_docs.sh].

## Next (Session 5B)

**13 Product Documentation Pages**
Concrete deliverables: Getting Started (setup + first inference), API Reference (all methods + error codes), CLI Reference (command list + examples), Brand Configuration (custom rules syntax + 3 templates), Troubleshooting (12 common issues + remedies), Benchmarks (performance vs. baseline on 6 metrics), FAQ, Changelog, Security (threat model + disclosure policy), Integration Guides (4 platform examples), Data Dictionary (field definitions), Glossary, Release Notes template. Provides complete user-facing documentation.

**Four Product Design Records (PDRs)**
Multi-model inference strategy (cost vs. accuracy tradeoffs for 2 candidate architectures), caching layer design (TTL + eviction policy), parallelization framework (job queuing + worker pool config), API rate-limiting scheme (token bucket with 3 tier levels). Locks architectural decisions before development.

**ARCHITECTURE.md**
System diagram (5 components + data flow), layer breakdown (input validation, gating, inference, scoring, export), dependency graph, and failure modes matrix. Replaces whiteboard sketches with permanent reference.

**USAGE.md**
Step-by-step walkthroughs for 4 workflows: single-item scoring, batch processing, custom brand rules, monitoring + alerting. Assumes reader has no prior context.

**CONTRIBUTING.md**
Code style guide (line length, naming, docstring format), testing expectations (unit + integration test ratios), PR review checklist, local dev setup (5 steps), and changelog entry format. Onboards contributors in under 15 minutes.

## Later

**Parallelization (DJ-011)**
Worker pool with configurable concurrency (2-16 workers) and job queue, reducing latency for 100+ item batches from 47s to 8s. Deferred pending demand signal from 3+ customer requests.

**Batching Layer**
Vectorized scoring for requests grouped by size (32, 64, 128 items), improving throughput 3.2x on hardware with batch-optimized operations. Requires profiling on target deployment hardware first.

**Caching (TTL-based)**
In-memory cache storing scored items with configurable TTL (default 3600s), reducing duplicate calls by 67% in typical workflows. Deferred until cache invalidation strategy is mature.

**Multi-Brand Support (B3)**
Namespace isolation for 5+ concurrent brand configurations, allowing single deployment to serve Acme Corp, TechVendor, and 3 others independently. Blocked by ARCHITECTURE finalization and customer commitment.

**API Wrapper**
REST endpoint (OpenAPI 3.0 spec) exposing core scoring methods with request validation, JSON serialization, and 3-tier rate limiting. Deferred until internal API stabilizes.

## Won't Build

**Campaign Performance Attribution**
Linking content scores to downstream conversion metrics (CTR, purchase rate) requires 6+ months of longitudinal data collection and causal inference modeling outside BrandGuard scope. Focus remains on safety classification, not business impact prediction.

**Image and Video Processing**
Extending safety classifier to visual media requires separate model architecture (CNNs or vision transformers), 50x larger training dataset, and 40x longer inference latency. Scoped to text-only in v1 and v2.

**Auto-Publish Workflow**
Automatically pushing approved content to customer platforms (social, email, web) introduces liability, requires platform-specific SDKs, and conflicts with customer approval workflows. BrandGuard outputs confidence scores only; customers own publish decisions.
