---
audience: PM hiring managers
depth: synthesizing
mode: plugin
plugin_command: /roadmap-update
framework: 
word_count_floor: 500
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: ROADMAP.md

Produce a roadmap in Shipped / Next / Later / Won't Build format. Shipped: items already in repo (synthetic corpus, deterministic gate, eval harness, kill switch, verify_chain, doc QC pipeline). Next (Session 5B): 13 docs, 4 PDRs, ARCHITECTURE/USAGE/CONTRIBUTING. Later: parallelization (DJ-011), batching, caching, multi-brand support (B3), API wrapper (B4). Won't Build: no campaign performance attribution, no image/video, no auto-publish. Each item has one-line rationale.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
