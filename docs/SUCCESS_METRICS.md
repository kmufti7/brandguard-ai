---
state: VERIFIED
timestamp: 2026-05-11T22:35:46.696852+00:00
brief: scripts/doc_pipeline/briefs/success_metrics.brief.md
mode: plugin
plugin_command: /metrics-review
framework: 
word_count_floor: 600
---

# SUCCESS METRICS

## Executive Summary

This document establishes measurable success criteria for BrandGuard, the AI-powered content moderation system. Metrics are categorized as Leading Indicators (predictive of desired outcomes) or Lagging Indicators (confirmatory of results). All targets reflect pre-MVP positioning and are grounded in observable outputs from WORM logs, evaluation reports, and system telemetry. Vanity metrics are explicitly excluded; every metric must be quantifiable and actionable within a defined measurement window.

## Metrics Framework

### Leading Indicators

Leading indicators predict system performance and user outcomes before measurable business results materialize. These metrics guide product development and operational tuning.

**1. Hallucination Rate (Faithfulness Score)**

**Definition:** Percentage of generated explanations or citations that contain factual errors, unsupported claims, or information not derivable from source material. Measured by human review of a stratified sample of model outputs flagged during evaluation.

**Measurement Source:** Eval report hallucination audit; WORM log annotations for explanation text.

**Target:** < 5% by end of Q2. Pre-MVP baseline is < 12% acceptable.

**Rationale:** Lower hallucination directly reduces user distrust and support burden. This metric drives model selection and prompt engineering decisions.

**Owner:** Model Fidelity Team

---

**2. Citation Existence Rate**

**Definition:** Percentage of content moderation decisions that include at least one valid reference to source material (URL, document ID, or policy section) when a citation is required by the gate logic. Measured as: (decisions with valid citations / total decisions requiring citations) × 100.

**Measurement Source:** WORM log citation field population; automated validation against source document registry.

**Target:** 100% compliance at gate. Non-compliance blocks deployment.

**Rationale:** Citations are a hard requirement for user trust and regulatory defensibility. This is a gate metric, not an aspirational target.

**Owner:** Data Quality & Compliance

---

**3. Gate Latency (p95)**

**Definition:** Time elapsed from content submission to gate completion, measured at the 95th percentile across all requests in a measurement window. Includes model inference, citation retrieval, and policy lookup.

**Measurement Source:** WORM log request timestamps and completion markers.

**Target:** p95 < 800 milliseconds by end of Q3.

**Current Baseline:** p95 approx. 1,200 ms (unoptimized).

**Rationale:** Sub-second response enables real-time moderation workflows. This metric drives infrastructure and batching decisions.

**Owner:** Platform Engineering

---

**4. Evaluation Throughput**

**Definition:** Number of unique content samples processed through the full evaluation pipeline per calendar day, measured as a 7-day rolling average. Includes hallucination audit, citation validation, and policy alignment review.

**Measurement Source:** Eval report ingestion logs; unique content IDs processed.

**Target:** 500 samples/day by Q2 end.

**Current Baseline:** 180 samples/day (manual eval).

**Rationale:** Higher throughput enables faster iteration cycles and confidence in metric stability. Supports pre-MVP validation at scale.

**Owner:** Eval & QA

---

**5. Time-to-First-Copy (TTFC)**

**Definition:** Duration from initial product requirement definition to first production deployment of a new moderation policy or model variant. Measured in calendar days.

**Measurement Source:** Project tracking system (Jira or equivalent); deployment logs.

**Target:** < 14 days by Q2.

**Current Baseline:** 35-45 days (including manual integration).

**Rationale:** Faster iteration enables rapid response to emerging brand risks and competitive product changes.

**Owner:** Product & Engineering

---

### Lagging Indicators

Lagging indicators confirm outcomes and guide business decisions once results are observable.

**1. User Adoption Rate**

**Definition:** Percentage of eligible brand partners who have activated and used BrandGuard at least once in a 30-day window. Measured as: (partners with >= 1 moderation decision in period / total activated partners) × 100.

**Measurement Source:** Usage analytics; WORM decision logs.

**Target:** 65% by end of Q3 (post-MVP).

**Rationale:** Adoption validates product-market fit and customer satisfaction. Low adoption signals onboarding friction or insufficient value perception.

**Owner:** Customer Success

---

**2. False Positive Rate (User-Reported)**

**Definition:** Percentage of moderation decisions flagged as incorrect by end users within 30 days of decision issuance. Measured as: (user appeals with "correct decision override" / total decisions) × 100.

**Measurement Source:** Customer support tickets; user feedback API.

**Target:** < 8% within 90 days of launch.

**Rationale:** Excessive false positives erode user trust and create support cost. This metric directly impacts brand perception.

**Owner:** Product & Support

---

**3. Policy Alignment Score**

**Definition:** Percentage of moderation decisions that align with stated brand policy as verified by manual audit of a stratified monthly sample (minimum 100 decisions). Alignment = decision outcome matches expected policy application.

**Measurement Source:** Audit reports; policy documentation crosswalk.

**Target:** >= 92% by end of Q2.

**Rationale:** Misalignment indicates model drift or policy encoding errors. Drives retraining and prompt refinement cycles.

**Owner:** Policy & Compliance

---

**4. System Uptime**

**Definition:** Percentage of calendar time in which the gate is available and responding to requests within SLA latency, measured monthly. Excludes scheduled maintenance windows announced >= 24 hours in advance.

**Measurement Source:** Infrastructure monitoring; WORM heartbeat logs.

**Target:** >= 99.5% monthly uptime.

**Rationale:** Uptime directly correlates with customer trust and contractual SLA compliance.

**Owner:** Platform Engineering

---

## Metric Refresh Cadence

- Leading indicators: reviewed weekly by owning teams; aggregated monthly.
- Lagging indicators: reviewed monthly; escalated to executive steering if any metric falls > 10% below target for two consecutive periods.
- All targets are reviewed quarterly and adjusted based on competitive benchmarking and customer feedback.

## Exclusions: Vanity Metrics

The following are explicitly rejected as success measures:

- Total content samples processed (without quality context).
- Page views or session count (not tied to business outcome).
- Number of policies created (without adoption or impact data).
- Average response time (p95 is the relevant measure for user experience).

---

**Document Owner:** Product Management  
**Last Updated:** [Date]  
**Next Review:** 30 days
