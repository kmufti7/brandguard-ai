---
audience: AI product leads, integration architects
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 600
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: INTEGRATION_SURFACE.md

Describe how BrandGuard AI plugs into existing marketing tech stacks at the entry point. One paragraph per integration target: Salesforce Marketing Cloud (audience inputs from data extensions), Marketo (audience smart lists, generated copy back to Email Programs), Adobe Campaign (segment outputs), Iterable (template population). For each: what BrandGuard consumes (audience definition format), what it produces (gate-approved copy + citations + WORM trace ID), and what the integration boundary is (no auto-publish; HITL approval still required).

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
