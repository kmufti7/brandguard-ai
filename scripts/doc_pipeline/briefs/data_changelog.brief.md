---
audience: Reviewers tracing corpus changes
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 300
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: DATA_CHANGELOG.md

Produce a corpus version history. v1 (Session 2B): seed=42, distribution 444 low / 54 medium / 2 high churn-risk. v2 (Session 4, O1): same seed=42, threshold dropped from 4 to 3, autopay-not-enrolled weight bumped from +1 to +2 (DJ-005). New distribution 306 / 164 / 30. Both versions reproducible from scripts/corpus_generator.py.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
