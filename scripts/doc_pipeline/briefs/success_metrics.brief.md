---
audience: PM hiring managers, AI product leads
depth: synthesizing
mode: plugin
plugin_command: /metrics-review
framework: 
word_count_floor: 600
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: SUCCESS_METRICS.md

Produce a structured Success Metrics document. Categorize metrics as Leading vs Lagging. Required definitions and targets: hallucination rate (faithfulness < target), citation existence rate (target 100% blocked by gate), gate latency (p95 target), eval throughput, time-to-first-copy. Reject vanity metrics; every metric must be measurable from the WORM log or eval report. Forward-looking targets are acceptable since BrandGuard is pre-MVP.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
