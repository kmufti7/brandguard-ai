---
state: VERIFIED
timestamp: 2026-05-11T22:30:42.710633+00:00
brief: scripts/doc_pipeline/briefs/mlops_playbook.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 700
---

# MLOps Playbook

## Overview

BrandGuard AI operates under a disciplined MLOps framework that ensures marketing content stays true to brand identity and factual accuracy. This playbook documents the practices that govern model training, evaluation, and deployment for Strand Wireless and other managed brands.

## Dataset Versioning Protocol

The foundation of reproducible machine learning in BrandGuard is controlled data. All training corpora are generated deterministically using a fixed random seed of 42, enabling any team member to regenerate identical datasets at any point in the product lifecycle.

The corpus generation process is documented in [file:scripts/corpus_generator.py]. This script accepts brand configuration files and produces a versioned training dataset. The seed value 42 is committed to version control alongside the generation script itself. When a new corpus is needed, the script runs with the same seed, producing byte-for-byte identical output. This eliminates guesswork about which training examples influenced a model's behavior.

Brand voice guidelines and fact sheets are stored as plain markdown files in the repository. These files are not generated; they are written by brand experts and committed directly. Versioning happens through Git, which preserves the full history of changes to [file:data/brand_voice.md] and associated fact sheets. When a brand stakeholder updates tone guidance or corrects a factual claim, the change is recorded with a timestamp and commit message. Models trained against older data can be traced back to the exact brand voice version they were aligned with.

This dual approach, combining deterministic data generation with version-controlled brand assets, means every model in production can be audited. Given a model's creation date, you can checkout the exact corpus seed and brand voice that shaped its behavior.

## Drift Monitoring Philosophy

Production models degrade when the patterns they learned no longer match reality. BrandGuard detects this drift through continuous evaluation.

The evaluation harness, implemented in [file:src/brandguard/eval/eval_harness.py], serves as a regression detector. Rather than monitoring raw accuracy metrics that may be noisy or domain-specific, the harness measures two foundational dimensions: faithfulness and relevance.

Faithfulness measures whether the model's output remains grounded in brand facts. A response is faithful if claims about Strand Wireless services, pricing, or policies match the source truth. Relevance measures whether the model's output addresses the user query appropriately. A response is relevant if it answers what was asked.

Each dimension has a baseline, established when the model was first deployed. The baseline is computed from 500 held-out evaluation examples and stored in the model's metadata. Alongside the baseline sits a tolerance band, typically 2 percentage points below the baseline score. If faithfulness drops below 92 percent when the baseline was 94 percent, or if relevance drifts from 96 percent to 93.5 percent, an alert fires.

The evaluation harness runs daily, or more frequently if content or brand voice has been updated. [file:scripts/run_eval_report.py] orchestrates this evaluation. The script pulls the latest held-out dataset, runs inference through the current production model, and compares results to the baseline and tolerance band. The report is published to a monitoring dashboard that brand reviewers and ML engineers check each morning.

Drift detection is not about achieving perfect scores. It is about detecting statistically meaningful regression. A one-point drop in a single day is noise. A five-point drop over two weeks, or any drop below the tolerance band, signals that retraining, fact-checking, or brand guidance updates are needed.

## Deployment Cadence and Human-In-The-Loop Gates

BrandGuard does not auto-deploy models. Every candidate model must pass a human review gate before reaching production. A reviewer, typically a brand manager or ML lead, examines 20 random model outputs against the source brand voice and fact sheet. The reviewer scores each output as acceptable or unacceptable. If 19 of 20 outputs are acceptable, the model is approved. If 17 or fewer are acceptable, the model is rejected and sent back for retraining.

This human gate is the rate limiter for all deployments. A model could be mathematically ready but held in staging if no reviewer is available. In practice, Strand Wireless maintains a rotation of 3 reviewers, ensuring coverage during business hours. Deployments typically happen within 2 business days of model completion.

Once approved, the new model is deployed to a canary fleet serving 5 percent of traffic for 24 hours. During this period, the evaluation harness runs on real user interactions, not held-out data. If the canary results match the pre-deployment evaluation, the model rolls out to 100 percent of traffic. If results diverge, the deployment is rolled back and the model is rejected.

This layered approach, combining automated detection with human judgment and staged rollouts, ensures that brand safety is never sacrificed for speed. The discipline is slower than unchecked automation but far faster than manual content review. Strand Wireless can deploy a new model in days, not months, while maintaining confidence that outputs will not harm the brand.
