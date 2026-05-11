---
state: VERIFIED
timestamp: 2026-05-11T22:47:56.290779+00:00
brief: scripts/doc_pipeline/briefs/data_changelog.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 300
---

# CHANGELOG

## Overview

This document tracks corpus versions used in BrandGuard AI governance workflows for Strand Wireless. Each version is reproducible from scripts/corpus_generator.py using a fixed random seed. Changes reflect adjustments to churn-risk classification thresholds and behavioral weighting.

## Version 1 (Session 2B)

**Release Date:** Session 2B  
**Seed:** 42  
**Threshold:** 4  
**Distribution:**
- Low churn-risk: 444 customers
- Medium churn-risk: 54 customers
- High churn-risk: 2 customers

Version 1 established the baseline corpus for initial governance testing. The threshold of 4 was set to identify only the most severe churn indicators.

## Version 2 (Session 4, O1)

**Release Date:** Session 4, O1  
**Seed:** 42  
**Threshold:** 3  
**Autopay Non-Enrollment Weight:** Increased from +1 to +2  
**Distribution:**
- Low churn-risk: 306 customers
- Medium churn-risk: 164 customers
- High churn-risk: 30 customers

### Changes in Detail

The threshold reduction from 4 to 3 was implemented to detect at-risk behavior at smaller thresholds, expanding the medium and high-risk classifications. This adjustment is tracked in DJ-005, which documents the decision to increase sensitivity for early intervention.

The autopay non-enrollment weight was increased from +1 to +2. According to DJ-005, empirical findings show customers without automatic payment enrollment demonstrate stronger correlation with churn intent. Increasing this weight prioritizes this behavioral signal during classification.

These changes allow teams to catch at-risk customers sooner in the customer lifecycle, compared to Version 1's narrower focus on extreme cases.

### Validation Note

Version 2 incorporates adjusted behavioral weights intended to improve prediction accuracy for high-risk customer segments. For specific precision, recall, F1 scores, and performance validation comparing Version 1 and Version 2, see the evaluation documentation referenced in DJ-005.

## Reproducibility

Both versions are fully reproducible by running scripts/corpus_generator.py with seed=42 and the respective threshold and weight parameters listed above.

This changelog documents parameter changes and distributions only. For the full decision rationale, cost-benefit analysis, and performance validation behind Version 2, see DJ-005. Validation results and accuracy comparisons are maintained in separate evaluation reports.
