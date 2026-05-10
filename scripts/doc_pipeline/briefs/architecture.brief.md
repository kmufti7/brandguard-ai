---
audience: Engineers, platform owners
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 1200
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: ARCHITECTURE.md

Produce a comprehensive technical ARCHITECTURE document. Required sections: System Overview (LangGraph workflow wiring audience -> rag -> gate; WORM logging; kill-switch). Component Deep Dive (each of the four native components, file paths, contracts). Governance Primitive Integration (WORM Logger, Kill-Switch Guard, Token FinOps Tracker from intelliflow-core; how each is consumed). Data Flow (corpus -> filter -> retrieval -> generation -> gate -> WORM). Eval Architecture (5 metrics split deterministic vs LLM-judged; golden dataset; report split per DJ-008). Scaling Strategy (cite DJ-011: parallelize, batch, cache, then vertical). Cite source files inline.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
