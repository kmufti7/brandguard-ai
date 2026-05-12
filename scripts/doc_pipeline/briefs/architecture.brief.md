---
audience: Engineers, platform owners
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 1200
evidence_sources: src/brandguard/, docs/adr/, docs/decision_journal.md, data/
---

# Brief: ARCHITECTURE.md

Produce a comprehensive technical ARCHITECTURE document for BrandGuard AI describing the ACTUAL system. Required sections:

1. **System overview.** A LangGraph `StateGraph` with THREE nodes wired in order: `audience_discovery -> rag_copy_generation -> legal_brand_review_gate`, then END. State is `BrandGuardState` (subclasses `IntelliFlowState` from intelliflow-core; pydantic, frozen; each node returns a `model_copy(update=...)`). Cross-cutting: a WORM logger writes a `TOOL_EXECUTED` enter/exit pair per node (the exit payload also carries `elapsed_ms`) plus `WORKFLOW_START`/`WORKFLOW_END`; a Kill-Switch Guard is checked on entry to every node (default rule: `audience_query_required`); on a tripped switch `run_workflow` catches `KillSwitchTriggered`, writes a `KILL_SWITCH_TRIGGERED` event, and returns `kill_switch_triggered=True` with `final_state=None`.

2. **Component deep dive (one subsection each):**
   - Audience Discovery Agent (`src/brandguard/agents/audience_discovery.py`): an LLM extracts a structured filter dict; `_sanitize_filter` drops invalid keys/SKUs; `apply_filter` evaluates the filter deterministically over `data/synthetic_crm_corpus.json` (500 records, seed=42, 17 fields). The LLM never filters records directly.
   - RAG Copy Generation Agent (`src/brandguard/agents/rag_copy_generation.py`): chunks `data/brand_voice.md` by `§N` section and `data/product_fact_sheet.md` by `[fact_sheet:<sku>:<field>]` anchor; embeds chunks with `fastembed` BGE-small (`BAAI/bge-small-en-v1.5`); builds an in-memory FAISS `IndexFlatIP` (normalized inner product); retrieves top-K; the LLM generates copy with inline citation anchors; brand voice is BOTH a retrieval source AND a deterministic system-prompt summary (per ADR-002).
   - Legal/Brand Review Gate (`src/brandguard/governance/legal_brand_review_gate.py`): deterministic, fail-closed, no LLM in the routing path (per ADR-003). Three rules: citation existence (every anchor must resolve to the RAG sources), autopay disclosure (a with-autopay price quoted without the autopay disclosure BLOCKs), unlimited disclosure (the word "unlimited" without the 100 GB soft-cap + 5 Mbps post-cap disclosure BLOCKs; these constants are parsed from `data/product_fact_sheet.md` at import, per the K3 fix). Returns a `GateDecision` with `decision` "ALLOW" or "BLOCK".
   - Hallucination Evaluation Harness (`src/brandguard/eval/eval_harness.py`): five metrics. Two LLM-judged (faithfulness, answer relevance; ragas semantics, locally implemented prompts via the Anthropic SDK). Three deterministic (context precision/recall as set math on retrieval anchors; citation existence mirroring the gate; brand voice alignment as principle-encoded checks). Golden dataset: `data/golden_dataset.json`, 20 scenarios. Eval report is split (Q1 / DJ-008): `docs/eval_report_deterministic.md` committed, `eval_output/eval_report_llm.md` gitignored.

3. **Reused governance primitives (from intelliflow-core, the upstream governance kernel):** WORM Logger (HMAC-SHA256 hash chain, append-only SQLite triggers, `verify_chain()` recomputes the chain), Kill-Switch Guard (`GovernanceRule` list, `intercept(state)` raises `KillSwitchTriggered` on any failure), Token FinOps Tracker (per-request token accounting; not yet integrated into the workflow, tracked in the backlog). These are imported, not reimplemented.

4. **Doc QC pipeline (`scripts/doc_pipeline/`):** Author Agent (drafts/revises from a brief; plugin or encoded mode), Critic Agent (rubric-bounded LLM grader, returns JSON, pass floor 7/10 per dimension), Verifier (deterministic Python: banned phrases, em dashes, citation existence including PDR and prose-path resolvers, word count floor, doc-to-doc links; NO LLM), Orchestrator (DRAFTED -> CRITIQUED -> REVISED -> ... -> VERIFIED or FAILED after 5 cycles; WORM-logged transitions; trace_id prefix `doc_pipeline:<slug>:<uuid>` segments the shared WORM chain). Author and Critic are fresh Anthropic API calls with role-isolated system prompts, not nested Claude Code processes (DJ-016); the pipeline runs on or off Claude Code.

5. **Data flow:** corpus + audience query -> filter -> matched records -> (brand voice + fact sheet) -> retrieved chunks -> generated copy + citations -> gate decision -> WORM log. Every step appends to the WORM chain.

6. **Scaling strategy (per DJ-011):** RAG copy generation is ~75% of per-scenario latency, audience discovery ~25%, the gate sub-millisecond (Session 4.1 timing data). Order: parallelize across scenarios, then batch LLM calls, then cache embeddings/retrieval, then vertical (bigger model) last.

## Hard accuracy rules

- There is NO Pinecone, NO OpenAI embeddings, NO S3 Object Lock, NO HTTP review endpoint, NO `main.py`, NO asyncio review orchestrator, NO Redis health check, NO PagerDuty/Jira hooks, NO fine-tuned models, NO `APPROVE|REVISE|BLOCK` (gate decisions are "ALLOW"/"BLOCK"). Do not invent infrastructure or regulatory citations.
- Real files: `src/brandguard/workflow.py`, `state.py`, `llm.py`, `agents/audience_discovery.py`, `agents/rag_copy_generation.py`, `governance/legal_brand_review_gate.py`, `eval/eval_harness.py`. There is NO `analysis/`, NO `retrieval/`, NO `runtime/`, NO `orchestration/`, NO `governance/worm_logger.py` (the WORM logger lives in intelliflow-core, not BrandGuard).
- intelliflow-core is the upstream governance kernel; BrandGuard is not a module or extension of it.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred. No em dashes. No filler intensifiers from the banned phrase list. DO NOT emit [file:path] citation anchors; reference files in prose by name. Only name paths that actually exist. Reference DJ entries by [DJ-NNN] (DJ-001 through DJ-023 exist) and ADR entries by [ADR-NNN] (ADR-001 through ADR-004 exist).
