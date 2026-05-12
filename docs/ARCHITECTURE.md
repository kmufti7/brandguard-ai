---
state: VERIFIED
timestamp: 2026-05-12T00:20:10.406973+00:00
brief: scripts/doc_pipeline/briefs/architecture.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 1200
---

# ARCHITECTURE

## System Overview

BrandGuard AI is a governed marketing AI system that produces marketing copy for Strand Wireless products while enforcing legal and brand guardrails. The core workflow is a three-node LangGraph `StateGraph` wired in sequence: `audience_discovery -> rag_copy_generation -> legal_brand_review_gate`, then END.

The state object is `BrandGuardState`, which subclasses `IntelliFlowState` from intelliflow-core. It is a Pydantic frozen dataclass; each node returns a `model_copy(update=...)` to produce the next state. This immutable design ensures state transitions are auditable and deterministic.

Two cross-cutting systems instrument the workflow. The WORM Logger (imported from intelliflow-core) writes an append-only event chain to SQLite with HMAC-SHA256 chaining. It emits a `TOOL_EXECUTED` enter event and exit event per node; the exit event includes `elapsed_ms`. The workflow also emits `WORKFLOW_START` when `run_workflow()` is called and `WORKFLOW_END` when all nodes complete. The Kill-Switch Guard (also from intelliflow-core) is checked on entry to every node. It holds a list of `GovernanceRule` objects and calls `intercept(state)`. The default rule is `audience_query_required`, which passes only if the audience query is non-empty. If any rule fails, the guard raises `KillSwitchTrippedException`. The `run_workflow` function catches this exception, writes a `KILL_SWITCH_TRIGGERED` event to the WORM chain, and returns `kill_switch_triggered=True` with `final_state=None`.

## Component Deep Dive

### Audience Discovery Agent

The Audience Discovery Agent in src/brandguard/agents/audience_discovery.py accepts a natural-language audience query and extracts a structured filter dictionary via an LLM prompt. The filter keys are field names from the synthetic CRM corpus, and values are constraints (e.g., `{"state": "CA", "monthly_spend_usd": {"$gte": 100}}`).

The extracted filter is passed to `_sanitize_filter()`, which validates each key against the 17 known fields in the corpus and drops invalid keys. It also validates SKU references: any SKU in the filter must exist in data/product_fact_sheet.md. Invalid SKUs are dropped silently.

The sanitized filter is then applied by `apply_filter()`, which evaluates it deterministically over data/synthetic_crm_corpus.json. This corpus contains 500 customer records generated with seed=42 for reproducibility. The agent does not filter records itself; only the deterministic `apply_filter()` function does. The output is a list of matched records (typically 5 to 50 records per query) and a count.

### RAG Copy Generation Agent

The RAG Copy Generation Agent in src/brandguard/agents/rag_copy_generation.py retrieves brand and product knowledge to ground the LLM's copy generation.

It chunks two sources. The brand voice data/brand_voice.md is divided by section anchors (`§1` through `§7`), creating 7 chunks. The product fact sheet data/product_fact_sheet.md is chunked by the inline anchors `[fact_sheet:<sku>:<field>]` (for example, `[fact_sheet:strand_flex_100:autopay_disclosure]`), creating one chunk per anchor. Each chunk is a string.

Chunks are embedded using fastembed with the BGE-small model (`BAAI/bge-small-en-v1.5`), a lightweight 384-dimensional embedding. The embeddings are normalized and stored in an in-memory FAISS `IndexFlatIP` (flat index with inner-product similarity), which supports fast retrieval without quantization. At query time, the audience records and matched records from the prior node are embedded, and the top-K chunks (typically K=5 to 10) are retrieved.

The retrieved chunks and their anchor IDs are passed to the LLM. The LLM is prompted to generate marketing copy that directly addresses the audience segment, cites facts from the retrieved chunks using inline citation anchors (e.g., `[brand_voice:§3]` or `[fact_sheet:strand_flex_100:autopay_disclosure]`), and adheres to the Strand Wireless brand voice. The brand voice is used both as a retrieval source (so it can be cited in output) and as a deterministic summary in the system prompt [ADR-002]. This ensures copy tone, terminology, and narrative arc are consistent without requiring a second LLM inference.

The agent returns the generated copy and a list of citation anchors used.

### Legal and Brand Review Gate

The Legal and Brand Review Gate in src/brandguard/governance/legal_brand_review_gate.py is deterministic and fail-closed. It contains no LLM in its routing path [ADR-003]. It validates the copy returned by the RAG agent against three rules.

**Citation Existence Rule.** Every citation anchor in the output must resolve to one of the retrieved chunks from the RAG agent. The gate maintains a set of valid anchor IDs and checks that each cited anchor is in the set. If an anchor does not exist, the gate blocks the copy.

**Autopay Disclosure Rule.** Strand Wireless has a regulatory requirement: any price quoted for a plan with autopay must be accompanied by the autopay disclosure text. The gate scans the output text for price patterns and plan mentions. If a with-autopay price is found but the disclosure is absent, the gate blocks the copy. The disclosure text is parsed from data/product_fact_sheet.md at import time.

**Unlimited Disclosure Rule.** The word "unlimited" must be paired with the soft-cap and speed-throttle disclosure. Specifically, any mention of "unlimited" without the text "100 GB soft cap" and "5 Mbps post-cap" triggers a block. These constants are parsed from data/product_fact_sheet.md at import time (the K3 fix [DJ-014]) to ensure the disclosure text is always in sync with the actual product limits.

The gate returns a `GateDecision` object with `decision` set to either "ALLOW" or "BLOCK", plus a `reason` string explaining the decision for logging and debugging.

### Hallucination Evaluation Harness

The Hallucination Evaluation Harness in src/brandguard/eval/eval_harness.py measures copy quality against a golden dataset of 20 scenarios stored in data/golden_dataset.json. Each scenario specifies an audience query, expected matched records, and ground-truth marketing copy.

The harness computes five metrics. Two are LLM-judged: faithfulness (does the generated copy align with the facts in the retrieved chunks?) and answer relevance (does the copy address the audience segment?). These use locally implemented ragas semantics via the Anthropic SDK, not external APIs. Three are deterministic: context precision (what fraction of retrieved chunks are cited in the output, measured as set overlap), context recall (what fraction of ground-truth anchor references should have been retrieved), and citation existence (do all cited anchors resolve, mirroring the gate rule). The brand voice alignment metric is principle-encoded: it checks for banned phrases, em-dash violations, and tone consistency without LLM judgment.

The evaluation is run in two parts. Deterministic metrics and the evaluation report (`docs/eval_report_deterministic.md`) are committed to version control [DJ-008]. LLM-judged metrics are written to `eval_output/eval_report_llm.md`, which is gitignored to avoid storing API costs and inference data in the repo. The two reports are intended to be read together.

## Reused Governance Primitives

BrandGuard imports three governance primitives from intelliflow-core, the upstream governance kernel. These are not reimplemented in BrandGuard.

The WORM Logger is an append-only event store backed by SQLite. It computes HMAC-SHA256 hashes over each event payload and chains them: each event includes the hash of the prior event. The `verify_chain()` method recomputes the hash chain from the start; if any hash breaks, the chain is detected as tampered. This design prevents retroactive deletion or mutation of logged events.

The Kill-Switch Guard holds a list of `GovernanceRule` objects and exposes an `intercept(state)` method. Each rule can inspect the state and raise `KillSwitchTriggedException` if a condition fails. Rules are checked before each node executes. On exception, the workflow stops and logs the trigger event.

The Token FinOps Tracker is an accounting system that measures token usage per LLM request. It is imported from intelliflow-core but not yet integrated into the BrandGuard workflow; integration is tracked in the backlog.

## Documentation Quality Control Pipeline

BrandGuard includes a doc QC pipeline in scripts/doc_pipeline/ that automates the production of high-quality technical and marketing documentation for the product itself (e.g., this ARCHITECTURE document).

The pipeline has four agents. The Author Agent is invoked with a documentation brief and drafts or revises the doc in markdown. It is deployed as a fresh Anthropic API call with a role-isolated system prompt, not as a nested Claude Code process [DJ-016]. The Critic Agent is an LLM-judged rubric evaluator that scores the draft on multiple dimensions (clarity, accuracy, completeness, tone, grammar) and returns a JSON scorecard. The Verifier is a deterministic Python tool that checks banned phrases, em-dash usage, word count floor, citation anchors (including PDR entries and prose file-path resolvers), and cross-doc links. It requires zero LLM calls and blocks any violation. The Orchestrator manages the state machine: DRAFTED -> CRITIQUED -> REVISED -> VERIFIED or FAILED after 5 revision cycles.

All transitions in the pipeline are logged to the shared WORM chain with a trace_id prefix of the form `doc_pipeline:<slug>:<uuid>`. This segments the doc pipeline events from workflow events while keeping them in a single tamper-proof ledger.

The Author and Critic agents are designed to run both on and off Claude Code, so the pipeline can be invoked either as an in-IDE tool or as a standalone script.

## Data Flow

The end-to-end data flow is linear. An audience query and (optionally) a product SKU filter are provided by the user.

1. The audience query enters the Audience Discovery Agent, which extracts a filter and applies it to the synthetic CRM corpus (data/synthetic_crm_corpus.json). The result is a list of matched customer records.

2. The matched records are passed to the RAG Copy Generation Agent. The agent retrieves brand voice and fact sheet chunks relevant to the audience segment and product, then prompts the LLM to generate marketing copy with inline citations.

3. The generated copy and citations are passed to the Legal and Brand Review Gate, which validates citations, autopay disclosures, and unlimited disclosures. The gate returns an ALLOW or BLOCK decision.

4. All nodes write events to the WORM logger, creating a tamper-proof audit trail.

If the gate blocks the copy, the workflow returns the blocked decision and a reason. If it allows, the copy is returned as the final output.

## Scaling Strategy

Per [DJ-011], RAG copy generation accounts for approximately 75 percent of per-scenario latency, audience discovery for 25 percent, and the legal gate for less than 1 millisecond (based on timing data collected during Session 4.1). The recommended scaling order is:

1. Parallelize across independent scenarios. Each scenario (audience query + SKU pair) is independent; multiple scenarios can be processed concurrently by distributing them to separate workflow instances.

2. Batch LLM calls. The Audience Discovery and RAG Copy Generation agents are LLM-backed; requests from multiple scenarios can be batched into a single Anthropic API call.

3. Cache embeddings and retrieval results. The brand voice and fact sheet chunks are static; their embeddings can be computed once and reused across all scenarios. The FAISS index can be persisted to disk and loaded at startup.

4. Vertical scaling (larger embedding or generation models) is the last option and should only be considered if the three prior strategies are exhausted and additional latency reduction is required.
