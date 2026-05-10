---
audience: First-time repo visitors
depth: synthesizing
mode: encoded
plugin_command: 
framework: working_backwards
word_count_floor: 800
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: README.md

Produce a README that opens with Working-Backwards / PR-FAQ framing. First paragraph: what BrandGuard AI does for the user, written as if the product has shipped. Second paragraph: how it does that (the four-component architecture, plus reused governance primitives). Third paragraph: lineage disclosure (BrandGuard consumes intelliflow-core as upstream governance kernel; do NOT subordinate BrandGuard). Setup section comes AFTER the product framing. Pointers to product doc map and engineering doc map at the bottom. License: Apache 2.0, Kaizen Works LLC.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
