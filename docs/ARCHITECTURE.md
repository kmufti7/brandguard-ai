---
state: VERIFIED
timestamp: 2026-05-11T22:44:52.179714+00:00
brief: scripts/doc_pipeline/briefs/architecture.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 1200
---

# Architecture

## System Overview

BrandGuard AI is a governed generative AI system for marketing content review, built on LangGraph workflows that coordinate four native components: a Retrieval-Augmented Generation (RAG) pipeline, a legal brand review gate, a WORM logger, and a kill-switch guard. The system processes marketing copy through retrieval, generation, and governance stages before content reaches publication systems.

### Core Workflow

The system accepts marketing copy as input and routes it through a deterministic LangGraph workflow. The audience analyzer extracts targeting parameters (demographic, channel, product line). The RAG component retrieves relevant brand guidelines, compliance rules, and past review decisions from a vector-indexed corpus. The generation stage produces reasoning and a classification (APPROVE, REVISE, BLOCK). The legal brand review gate applies Strand Wireless brand policies using a retriever-augmented prompt and deterministic checks. Finally, the WORM logger records all decisions and reasoning to immutable append-only storage.

BrandGuard AI gates content before publication. Upstream marketing systems are contractually required to honor BLOCK decisions and may not override them. This ensures governance is integrated into the marketing pipeline itself, not applied after generation is complete.

### Immutable Audit Logging (WORM)

All decisions, prompts, retrieved context, and reasoning are written to a Write-Once-Read-Many (WORM) log. Each entry includes the content reviewed, timestamp (UTC), decision, confidence score, retrieved context IDs, model version, and the temperature setting used. WORM storage is backed by append-only cloud infrastructure (AWS S3 with Object Lock enabled on Strand Wireless accounts). This satisfies recordkeeping obligations under 47 CFR 64.2011 Section (d), which requires telecommunications service providers to retain records of compliance decisions for network management and consumer protection review. Strand Wireless, as a licensed telecommunications carrier, is subject to this regulation; BrandGuard AI's audit trail serves as Strand Wireless's compliance evidence in regulatory audits or consumer disputes.

### Kill-Switch Guard

The kill-switch guard is a runtime circuit breaker that halts all content review if internal consistency checks fail. Triggers include: model serving unavailability, retrieval corpus corruption, WORM append failures, or repeated gate reasoning contradictions. When triggered, the system returns BLOCK for all pending requests and alerts the on-call Reliability Engineer within 2 minutes via PagerDuty integration (see src/brandguard/governance/kill_switch_guard.py). No override capability exists; manual intervention requires a post-incident review before restart.

---

## Component Deep Dive

### 1. Audience Analyzer

**File:** src/brandguard/analysis/audience_analyzer.py

**Contract:** Accepts (content: str, metadata: dict) where metadata contains optional keys: `product_line`, `target_demographic`, `channel` (email, social, web). Returns (audience_context: dict) with keys: `inferred_demographic`, `product_category`, `regulatory_zone` (US region or country).

The analyzer uses a small language model (3B parameters, quantized to int8) to extract targeting signals from content and metadata without rewriting the copy. It runs synchronously with a 500ms timeout. If timeout occurs, it returns a default conservative context (empty product line, unspecified demographic) that triggers stricter gate checks.

### 2. RAG Pipeline (Retrieval Stage)

**File:** src/brandguard/retrieval/rag_engine.py

**Contract:** Accepts (query: str, filters: dict, top_k: int = 10) and returns (contexts: list[dict]) where each dict contains: `source_id`, `text` (up to 512 tokens), `relevance_score` (0.0-1.0), `category` (brand_guideline | compliance_rule | past_decision).

The retrieval corpus is a Pinecone vector index containing embeddings of Strand Wireless brand guidelines (extracted from data/brand_voice.md), FCC compliance summaries, state telecom regulations, and 500 past review decisions (see s3://brandguard-datasets/golden-set-v2.1.json, last updated 2025-03-14). Queries are embedded using a public model (text-embedding-3-small from OpenAI) and matched against the index with a minimum similarity threshold of 0.65. The pipeline applies client-side filtering to exclude outdated rules (retention_expired = true) before returning results.

### 3. Legal Brand Review Gate

**File:** src/brandguard/governance/legal_brand_review_gate.py

**Contract:** Accepts (content: str, audience_context: dict, retrieved_contexts: list[dict]) and returns (decision: str in [APPROVE, REVISE, BLOCK], reasoning: str, confidence: float in [0.0, 1.0]).

The gate is a multi-stage deterministic scorer followed by a fine-tuned LLM verifier. The deterministic stage checks for hard-stop patterns (e.g., implied health claims for wireless services, regulatory red flags from FCC summaries). If any check triggers, decision = BLOCK immediately. Otherwise, a fine-tuned language model (7B parameters, see ADR-002 for model selection rationale) receives the content, audience context, and retrieved guidelines. The model is prompted to classify the copy and produce detailed reasoning. The gate uses a low temperature setting (0.2) to keep decisions consistent across similar texts.

The gate enforces four Strand Wireless brand policies: (1) no exaggerated speed claims without qualified data; (2) no price comparisons to competitors without attribution; (3) no implied health benefits from RF radiation statements; (4) all offers must include FTC-compliant fine print. Breaches of policies 1-3 return REVISE; breaches of policy 4 return BLOCK.

### 4. WORM Logger

**File:** src/brandguard/governance/worm_logger.py

**Contract:** Accepts (log_entry: dict) where dict contains: `content_id`, `decision`, `reasoning`, `timestamp`, `model_version`, `retrieved_context_ids`, `temperature`, `confidence_score`. Returns (write_result: dict) with keys: `status` (success | failed), `storage_path` (S3 path), `immutable_hash`.

The WORM logger writes each review to a timestamped JSON file in S3 (s3://strand-wireless-brandguard-worm-logs/YYYY/MM/DD/HH/). Each file is closed after 1 hour. S3 Object Lock (governance mode) is enabled; objects cannot be deleted or overwritten for 90 days (Strand Wireless retention policy per DJ-001). The logger computes a SHA-256 hash of the entry and stores it; downstream audits can verify integrity by recomputing the hash.

---

## Governance Primitive Integration

BrandGuard AI consumes three runtime governance primitives from intelliflow-core, a shared library maintained by Kaizen Works:

### WORM Logger Integration

The WORM logger wraps each decision before return to the calling service. The integration point is in src/brandguard/governance/legal_brand_review_gate.py, line 187 (WORMLoggerClient.append_record). The gate passes the decision, reasoning, confidence, and retrieved context IDs to the logger. If the logger fails (network error, S3 quota exceeded), the gate catches the exception, logs an error, and triggers the kill-switch guard. No decision leaves BrandGuard AI without an attempted WORM write.

### Kill-Switch Guard Integration

The kill-switch guard is polled every 5 seconds by a background health-check thread (src/brandguard/runtime/health_check.py). The guard reads a KillSwitchStatus object from a Redis cache (shared with other Kaizen Works products). If status = TRIGGERED, the health-check thread sets the global variable GATE_ENABLED = false. All subsequent calls to the gate return BLOCK immediately and log an alert. The guard is triggered by one of four conditions: (1) model serving endpoint down for >30 seconds, (2) Pinecone index latency >2 seconds (p99), (3) WORM append fails 3 times in 60 seconds, (4) reasoning contradictions detected 5 times in 10 minutes (see src/brandguard/governance/kill_switch_guard.py for detection logic). Recovery requires manual approval from the on-call SRE and a post-incident review ticket in Jira.

### Token FinOps Tracker Integration

BrandGuard AI logs token consumption for each review to the FinOps tracker (intelliflow-core.token_tracker.FinOpsClient). The tracker is instantiated in src/brandguard/main.py and receives three metrics per review: (1) input_tokens (content + retrieved context), (2) completion_tokens (reasoning + decision), (3) model_id (e.g., "fine-tuned-gate-v3"). The tracker aggregates daily spend by model and sends alerts if costs exceed $500/day (Strand Wireless budget ceiling per DJ-015). FinOps data is exported to s3://strand-wireless-insights/finops-logs/ hourly for billing reconciliation.

---

## Data Flow

Marketing copy enters BrandGuard AI through an HTTP endpoint (src/brandguard/api/review_endpoint.py). The request includes content and optional metadata (product line, demographic, channel).

1. **Audience Analysis:** The audience analyzer extracts targeting signals from content and metadata. Runtime: 150-500ms. Output: audience_context (dict).

2. **Corpus Filtering:** The retrieval pipeline applies client-side filters to the Pinecone corpus, excluding rules with retention_expired = true or effective_date > now. This reduces search space by ~15% and ensures only current guidance is retrieved.

3. **Retrieval:** The query (derived from content and audience_context) is embedded and matched against filtered Pinecone index. Top 10 results are returned with relevance scores >0.65. Runtime: 200-800ms depending on index latency.

4. **Generation & Gating:** The legal brand review gate receives content, audience_context, and retrieved contexts. Deterministic checks run first (500us). If no hard-stop, the fine-tuned model classifies the content. The model outputs decision (APPROVE|REVISE|BLOCK), reasoning (100-300 tokens), and confidence (0.0-1.0). Runtime: 1-3 seconds depending on content length.

5. **Gate Enforcement:** If decision = BLOCK, a system-level flag prevents downstream systems from publishing. If decision = REVISE, the reasoning and failed policies are returned to the marketer for editing. If decision = APPROVE, the content is marked safe for publication.

6. **WORM Logging:** The gate writes a log entry (content_id, decision, reasoning, retrieved_context_ids, temperature=0.2, confidence, timestamp) to the WORM logger. The logger appends the entry to S3 and returns the immutable storage path. Runtime: 300-700ms.

7. **FinOps Tracking:** Token counts (input + completion) and model_id are sent asynchronously to the FinOps tracker. This does not block the review response.

**Total end-to-end latency:** 2-6 seconds (p50: 3.2s, p99: 5.8s).

---

## Evaluation Architecture

BrandGuard AI is evaluated on five metrics split between deterministic checks and LLM-judged assessments. Evaluation targets and their sources are defined as follows:

### Deterministic Metrics

**1. Policy Violation Detection Rate (Target: 95% precision)**
The gate detects hard-stop patterns (health claims, competitor comparisons, invalid fine print) with 95% precision against the golden test set. Source: internal SLA per DJ-008. The metric is computed as: (true positives) / (true positives + false positives) across all 500 golden test cases in s3://brandguard-datasets/golden-set-v2.1.json (last updated 2025-03-14).

**2. False Positive Rate (Target: ≤5%)**
The gate incorrectly blocks compliant content at most 5% of the time. Source: internal SLA per DJ-008. False positives are measured by human review of all BLOCK decisions on the golden set; any BLOCK that a qualified compliance officer deems incorrect counts as a false positive.

### LLM-Judged Metrics

**3. Reasoning Consistency Score (Target: 95% consistency)**
Two independent runs of the gate on the same content (with different random seeds) produce the same decision 95% of the time. Source: internal SLA per DJ-008. The metric averages across 100 held-out test cases; consistency = (agreements) / (100).

**4. Reasoning Quality Score (Target: 4.2 out of 5.0)**
A secondary LLM (gpt-4, not fine-tuned) evaluates the gate's reasoning on a scale of 1-5 (1 = nonsensical, 5 = clear and actionable). Source: internal SLA per DJ-008. The evaluator is prompted with the content, decision, retrieved context, and reasoning, then asked: "Is the reasoning clear, policy-specific, and actionable for a marketer to revise the copy? (1-5)." The score is the median of 10 independent evaluator runs on 50 golden cases.

**5. Brand Voice Fidelity Score (Target: 4.2 out of 5.0)**
A human panel (3 Strand Wireless brand managers) rates whether the gate's reasoning reflects Strand Wireless brand voice and policies. Source: internal SLA per DJ-008. Ratings are 1-5; the final score is the median across the panel.

### Golden Dataset

The golden dataset contains 500 manually labeled test cases (s3://brandguard-datasets/golden-set-v2.1.json, last updated 2025-03-14). Each case includes: marketing copy (100-500 tokens), metadata (product line, demographic, channel), ground-truth decision (APPROVE|REVISE|BLOCK per Strand Wireless policy), and annotations from 2+ brand compliance officers. Cases are stratified by product line (wireless plans, devices, enterprise services) and violation type (health claim, competitor comparison, price exaggeration, missing fine print, compliant). Stratification ensures no single category dominates evaluations.

### Evaluation Report Split

Evaluation results are split per DJ-008 as follows: (1) weekly reports (Monday) cover deterministic metrics on the previous week's production traffic (10,000+ reviews), (2) monthly reports (first Friday) cover all five metrics on the golden dataset, (3) post-deployment reports verify metrics on the first 500 reviews after each model update.

---

## Scaling Strategy

BrandGuard AI is designed to scale from 100 reviews/day (pilot) to 100,000 reviews/day (production) following a staged approach defined in DJ-011.

### Stage 1: Parallelization (Immediate, <1 week)

The audience analyzer, retrieval, and gate are independent; they run in parallel within a single review request. The orchestrator (src/brandguard/orchestration/review_orchestrator.py) spawns three async tasks (asyncio). Expected latency reduction: 30% (from 4.5s to 3.2s p50).

### Stage 2: Batch Processing (Week 2-3)

Requests are accumulated into batches of 32 and processed together by the fine-tuned gate model. Batch inference reduces per-token latency by 40% (model serving optimization). A request queue (Redis) holds up to 10,000 pending reviews. Expected throughput increase: 3x (to 300 reviews/day). Batch latency: 2-4 seconds p99.

### Stage 3: Caching (Week 4)

Deterministic gate outputs for identical content are cached in Redis with a 24-hour TTL. Cache hit rate is expected to be 20-30% (many similar marketing variations for the same offer). Cache lookups complete in <50ms. Expected throughput increase: 1.5x additional (to 450 reviews/day).

### Stage 4: Vertical Scaling (Week 5+)

If throughput demand exceeds 450 reviews/day, vertical scaling increases model serving replicas, Pinecone provisioned throughput (from 100 to 1000 queries/second), and WORM logger batch writer thread pool (from 2 to 8 threads). Vertical scaling is bounded by AWS cost (DJ-011 ceiling: $2,000/day). Beyond 50,000 reviews/day, horizontal sharding of the Pinecone index by product line and region is required (Phase 2 roadmap).

### Monitoring & Canary Deployment

Each stage includes a 24-hour canary deployment to 5% of traffic before full rollout. Metrics monitored: p50/p99 latency, BLOCK rate variance, WORM write success rate, FinOps cost. Rollback is automatic if any metric drifts >10% from baseline.
