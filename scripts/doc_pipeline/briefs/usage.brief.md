---
audience: Engineers consuming the library
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 600
evidence_sources: src/brandguard/, scripts/, docs/decision_journal.md
---

# Brief: USAGE.md

Produce a USAGE doc that shows how to run BrandGuard AI end to end, using the ACTUAL API. Required sections:

1. **Run the workflow.** `from brandguard.workflow import run_workflow`; `result = run_workflow(audience_query="...", campaign_brief="...")`. The return is a DICT with keys: `final_state` (dict), `worm_chain` (list), `worm_chain_verified` (bool), `trace_id` (str), `node_timings_ms` (dict), `kill_switch_triggered` (bool). `final_state` is a dict with `audience_filter`, `matched_records`, `generated_copy`, `citations`, `gate_decision` (the string "ALLOW" or "BLOCK"), `gate_reasons`. Show reading `result["final_state"]["gate_decision"]` and `result["final_state"]["generated_copy"]`. Mention that the default kill-switch trips on an empty `audience_query` and the result then has `kill_switch_triggered=True` and `final_state=None`.

2. **Run the eval reports (Q1 split).** `python scripts/run_eval_report.py --both` writes `docs/eval_report_deterministic.md` (committed) and `eval_output/eval_report_llm.md` (gitignored). `--deterministic-only` and `--llm-only` are the other modes.

3. **Run the test suite.** `pytest -q` from the repo root. `pyproject.toml` sets `testpaths = ["tests"]`. Do NOT say to run pytest against `src/`.

4. **Run the doc QC pipeline.** `python -m scripts.doc_pipeline.orchestrator --brief BRIEF.brief.md --rubric RUBRIC.rubric.md --output OUT.md`. It produces a VERIFIED doc plus a `.qc.json` sidecar; up to 5 cycles (DJ-021). Exit 0 on VERIFIED, non-zero on FAILED.

5. **Inspect the WORM chain.** The `result["worm_chain"]` list and `result["worm_chain_verified"]` boolean. Mention that the WORM logger is the SQLite logger from intelliflow-core with an HMAC-SHA256 hash chain and append-only triggers; `verify_chain()` recomputes the chain.

## Hard accuracy rules

- Real entry point: the function `run_workflow` in `src/brandguard/workflow.py`. There is NO `run_governance_workflow`, NO `workflow_orchestrator` module, NO `MarketingAsset` class, NO `brandguard.models`, NO three-gate architecture (there is ONE gate, `legal_brand_review_gate.py`, with THREE rules: citation existence, autopay disclosure, unlimited disclosure).
- Real package layout: `src/brandguard/__init__.py`, `agents/`, `governance/`, `eval/`, `workflow.py`, `state.py`, `llm.py`. There is NO `governance/rules/`, NO `report_cache/`, NO `brandguard.chain.worm_chain`.
- Gate decisions are the strings "ALLOW" and "BLOCK". Not "APPROVED"/"REJECTED", not "APPROVE"/"REVISE"/"BLOCK".
- The eval harness is `src/brandguard/eval/eval_harness.py`; there is NO `report_engine`, NO `evaluation.report_engine.generate_evaluation_report`.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred. No em dashes. No filler intensifiers from the banned phrase list. DO NOT emit [file:path] citation anchors; reference files in prose by name. Only name paths that actually exist (the Verifier blocks unresolvable backtick-quoted paths).
