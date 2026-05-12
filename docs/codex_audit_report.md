# BrandGuard AI: External Audit Report (Session 6)

**Date:** 2026-05-11
**Auditor:** Codex-substitute self-audit (no Codex CLI available in this environment; a general-purpose review agent ran the audit in plan mode). Findings classified CRITICAL / IMPORTANT / MINOR.
**Scope:** `src/`, `scripts/`, `tests/`, `docs/`, `data/`, `README.md`, dependency manifests.

---

## Summary

| Severity | Count | Remediated this session | Deferred |
|----------|-------|-------------------------|----------|
| CRITICAL | 2 | 2 | 0 |
| IMPORTANT | 4 | 4 | 0 |
| MINOR | 6 | 2 | 4 |
| **Total** | **12** | **8** | **4** |

Deferred items are minor and tracked in the Session 6 Log scope-drift flags / backlog. The headline finding: the Doc QC Verifier checks citations, em dashes, and word count but does NOT check whether a generated doc's prose matches the actual codebase. USAGE.md and ARCHITECTURE.md passed the Verifier in Session 5B while describing fabricated APIs and infrastructure. Root cause: their briefs did not include the real API surface. Fix: brief tightening (codified as DJ-022).

---

## CRITICAL

### C1. `docs/USAGE.md` described a fabricated API

The Session 5B USAGE.md referenced `run_governance_workflow()`, `brandguard.governance.workflow_orchestrator`, `MarketingAsset`, `brandguard.models`, a three-gate architecture, `brandguard.evaluation.report_engine`, `brandguard.chain.worm_chain.WORMChain`, and directories `src/brandguard/governance/rules/` and `report_cache/`. None exist. The real entry point is `run_workflow(audience_query, campaign_brief)` in `src/brandguard/workflow.py`; the gate emits `ALLOW`/`BLOCK`; WORM is the SQLite logger from intelliflow-core.

**Remediation (done):** rewrote `scripts/doc_pipeline/briefs/usage.brief.md` with the actual API surface baked in (hard accuracy rules + the real `run_workflow` return shape), then re-ran USAGE.md through the Doc QC pipeline. New USAGE.md describes the real API and passes the Verifier with the new prose-path resolver active.

### C2. `docs/ARCHITECTURE.md` described fabricated infrastructure

The Session 5B ARCHITECTURE.md referenced Pinecone, OpenAI `text-embedding-3-small`, S3 Object Lock WORM storage with concrete bucket URIs, an HTTP review endpoint, asyncio orchestration, a Redis health-check thread, PagerDuty/Jira hooks, fine-tuned 7B/3B models, `APPROVE|REVISE|BLOCK` decisions, FCC `47 CFR` recordkeeping claims, and several nonexistent source files. The actual stack: a 3-node LangGraph workflow (`audience_discovery -> rag_copy_generation -> legal_brand_review_gate`), in-memory FAISS (`IndexFlatIP`), `fastembed` BGE-small embeddings, a local JSON corpus, SQLite WORM via intelliflow-core, and `ALLOW`/`BLOCK` decisions only.

**Remediation (done):** rewrote `scripts/doc_pipeline/briefs/architecture.brief.md` with the real component structure, the real dependency stack, and explicit "do not invent infrastructure" rules. Re-ran ARCHITECTURE.md through the pipeline. New ARCHITECTURE.md matches the real architecture and passes the Verifier.

---

## IMPORTANT

### I1. `README.md` Quick Example used incorrect API surface

`run_workflow(...)` returns a `dict`, not an object; the Quick Example used `result.audience_segment` / `result.generated_copy` / `result.review_gate_decision` / `result.audit_log_hash` attribute access. Gate decisions are `ALLOW`/`BLOCK`, not `APPROVED`/`REJECTED`. The doc also pointed `pytest` at `src/brandguard/eval/` (no tests there; `pyproject.toml` sets `testpaths = ["tests"]`) and described the `[dev]` extra as including FAISS/ragas (the `dev` extra is only `pytest` + `ruff`).

**Remediation (done):** updated `scripts/doc_pipeline/briefs/readme.brief.md` with the exact `run_workflow` return shape (dict with `final_state`, `worm_chain`, `trace_id`, `node_timings_ms`; `final_state` is itself a dict with `audience_filter`, `matched_records`, `generated_copy`, `citations`, `gate_decision`) and the real `pytest` and dependency facts. Re-ran README.md through the pipeline.

### I2. `ragas` declared as a dependency but never imported

`pyproject.toml` and `requirements.txt` pinned `ragas>=0.2.0`, but `eval_harness.py` implements its own LLM-judged faithfulness/answer-relevance prompts ("ragas semantics, locally implemented prompts") and no module imports `ragas`. The dependency pulled a large transitive tree for nothing.

**Remediation (done):** removed `ragas` from `pyproject.toml` and `requirements.txt`. The "ragas semantics" wording stays in the eval harness docstrings (the metric definitions are ragas's; the implementation is local). Codified as DJ-023.

### I3. `run_workflow` non-kill-switch path leaked an open SQLite connection

`workflow.py` returned `worm_repo` and `_db` (an open `DatabaseSessionManager`) without closing in the success branch; the kill-switch branch closed it. `scripts/run_eval_report.py` never closed `_db` either, so a 20-scenario report run leaked 20 connections.

**Remediation (done):** `run_workflow` now closes the DB before returning in both branches. The success result still returns the WORM chain (already materialized via `get_chain()`) and a `worm_chain_verified` boolean (computed via `verify_chain()` before close), but no longer hands callers an open connection. `run_e2e_sample.py` and `run_eval_report.py` updated accordingly.

### I4. `discover_audience()` was dead code

`src/brandguard/agents/audience_discovery.py` defined `discover_audience()` (the ADR-001 "top-level entry" contract) but nothing called it; the workflow calls `extract_filter` + `apply_filter` directly.

**Remediation (done):** kept `discover_audience()` (it expresses the ADR-001 contract and `test_audience_discovery.py` references it) but added a test asserting it composes extract + apply correctly, so it is no longer dead. (Verified: `test_discover_audience_composes_extract_and_apply` is in the suite.)

---

## MINOR

### M1. Test coverage gaps (deferred to backlog)

No test exercises `rag_copy_generation.generate_copy()` end-to-end (only chunking/retrieval are tested); `_parse_generation`'s `COPY:`/`CITATIONS:` parsing is untested; `eval_harness` JSON-parsing edges are lightly tested; the orchestrator's full FAIL -> revise -> re-critique loop and FAILED-move-to-`failed/` branch are not directly tested; `_sanitize_filter` coercion edges are untested; the gate's fail-closed `except Exception -> BLOCK` path is untested. **Status: deferred** (backlog B19; not blocking the resume).

### M2. `intelliflow_core.v2.*` import path (deferred, upstream)

Every BrandGuard source file imports from `intelliflow_core.v2.runtime.*` / `.v2.storage.*` because the upstream repo uses `v2` as its package directory name. This is not BrandGuard's "v2 naming label" (which refers to the IntelliFlow generation label dropped in Session 2A.1), but it surfaces the string `v2` in BrandGuard source. **Status: deferred** (flag for the intelliflow-core repo; out of BrandGuard's control).

### M3. Stray WORM SQLite files in repo root (remediated)

`brandguard_worm_5b.db` and `brandguard_worm_6.db` sat in the working tree (gitignored, so untracked, but untidy). **Status: removed.**

### M4. Docstring drift (remediated)

`orchestrator.py` module docstring said "Max 3 critique/revise cycles" but `MAX_CYCLES = 5` since DJ-021. **Status: fixed.** Also `eval_harness.py` `score_scenario` passes retrieval anchor IDs (not chunk bodies) to the faithfulness judge, which weakens that metric. **Status: documented in the docstring as a known limitation; deferred** (B20: surface chunk bodies in the workflow result so the judge sees real text).

### M5. Fragile JSON/markdown parsing (deferred, low risk)

`llm.parse_json_object`'s brace-matching does not handle braces inside JSON string values; `_parse_generation`'s `COPY:`/`CITATIONS:` regex swallows everything after `COPY:` if the model omits the `CITATIONS:` header. Both are acceptable for the current constrained prompts. **Status: deferred** (B21). No security issues found: no `eval`/`exec`/`subprocess`/`pickle`, no SQL string interpolation, no path traversal, API key read only from `os.environ`.

### M6. `egg-info/PKG-INFO` stale (cosmetic, deferred)

`*.egg-info/PKG-INFO` was generated from an earlier README and still says "v2 SDK". egg-info is gitignored; regenerates on next build. **Status: deferred** (cosmetic).

---

## What the audit confirmed clean

- No `eval`/`exec`/`subprocess`/`os.system`/`pickle`; no SQL string interpolation; no path traversal (paths derived from `__file__` parents); API key read only from `os.environ`.
- Em-dash scan of `src/`, `scripts/`, `docs/`, `README.md`, `data/` clean.
- Banned-phrase hits are all legitimate (the words appear only in stoplist definitions in `author_agent.py`, `eval_harness.py`, and `brand_voice.md`'s prohibited-language list).
- No "module of" / "extension of" / "vertical of" subordinating language in prose; README explicitly says BrandGuard is "not a module or extension of intelliflow-core".
- Only synthetic data and the fictional "Strand Wireless" brand are used throughout.
