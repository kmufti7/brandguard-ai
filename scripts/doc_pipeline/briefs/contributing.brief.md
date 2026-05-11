---
audience: External contributors
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 400
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: CONTRIBUTING.md

Produce a short CONTRIBUTING guide. Cover: testing protocol (pytest must pass before PR), the doc QC pipeline (any new doc routes through it, per DJ-007), DJ entries for architectural decisions (P23), the project's style discipline (point readers to scripts/doc_pipeline/banned_phrases.txt for the banned word list and brand_voice.md section 4 for the punctuation rules; DO NOT quote any specific banned word by name in this doc), the P25 pre-pass discipline.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
