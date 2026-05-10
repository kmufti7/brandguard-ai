---
audience: PM hiring managers, AI product leads
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 700
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: USE_CASES.md

Produce 4-5 concrete use case scenarios for BrandGuard AI. Each scenario has: (a) trigger event (a marketer needs to do X), (b) workflow through the system (which agents fire, what they produce, what the gate decides), (c) expected outcome (what the user receives), (d) what would go wrong without BrandGuard (the failure mode this scenario prevents). Use the actual SKUs (Essentials, Pro, Family, Unlimited+, Business) and the actual gate rules (citation existence, autopay disclosure, unlimited disclosure).

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
