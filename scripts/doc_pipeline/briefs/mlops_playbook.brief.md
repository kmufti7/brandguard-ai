---
audience: ML/platform engineers
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 700
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: MLOPS_PLAYBOOK.md

Describe BrandGuard's MLOps discipline. Required: dataset versioning protocol (corpus seed=42, regenerable, committed; brand voice / fact sheet versioned as plain markdown). Drift monitoring philosophy (eval harness as regression detector; faithfulness/relevance baseline + tolerance band). Deployment cadence (HITL gate prevents auto-deploy; reviewer is the rate limit). Tie back to specific files: scripts/corpus_generator.py, scripts/run_eval_report.py, src/brandguard/eval/eval_harness.py.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
