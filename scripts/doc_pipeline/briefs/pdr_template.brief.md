---
audience: Future authors of PDR-001..004
depth: synthesizing
mode: encoded
plugin_command: 
framework: 
word_count_floor: 500
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/, docs/decision_journal.md
---

# Brief: PDR_TEMPLATE.md

Produce a Product Decision Record template that Session 5B will use to author PDR-001 (corpus design), PDR-002 (eval design rationale), PDR-003 (governance gate philosophy), PDR-004 (doc QC pipeline rationale). Required template sections: Context (what was true when the decision was made), Decision (the chosen path), Trade-Offs Considered (options + signals), Foreclosed Paths (what this rules out), Consequences (downstream implications). For PDR-002 only, an additional required section: 'On The LLM-Judged Score Defense' stating that the deterministic safety floor is the strong story; the LLM-judged scores describe LLM behavior, not gate efficacy.

## Voice + constraints

Follow Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers preferred over vague language. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path] where claims point to code.
