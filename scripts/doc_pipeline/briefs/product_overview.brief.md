---
audience: PM hiring managers, AI product leads, governance-curious buyers
depth: synthesizing
mode: plugin
plugin_command: /write-spec
word_count_floor: 600
evidence_sources: docs/PRD_BRANDGUARD.md, docs/adr/, src/brandguard/, data/brand_voice.md, data/product_fact_sheet.md
required_sections: Problem Statement, Target User, Solution, Competitive Positioning, Business Impact
---

# Brief: PRODUCT_OVERVIEW.md

Produce a product overview for BrandGuard AI. The doc should answer the question "what is this and why does it exist" for a reader who is a PM hiring manager or an AI product lead evaluating a governed marketing AI product.

## Context the Author should incorporate

- BrandGuard AI is a marketing AI product owned by Kaizen Works, LLC. Sole author: Kamil Mufti. License Apache 2.0.
- Native components: Audience Discovery Agent (LLM extracts filter, deterministic Python applies it over 500-record synthetic CRM corpus). RAG Copy Generation Agent (FAISS over brand voice + product fact sheet; citation-required). Legal/Brand Review Gate (three deterministic rules, fail-closed: citation existence, autopay disclosure, unlimited disclosure). Eval harness (ragas-style faithfulness + answer relevance LLM-judged, three deterministic metrics).
- Reused governance primitives from upstream `intelliflow-core` kernel: WORM Logger (HMAC-SHA256 hash chain, append-only SQLite triggers), Kill-Switch Guard, Token FinOps Tracker.
- Fictional brand for the synthetic corpus: Strand Wireless (US telecom). Five SKUs (Essentials / Pro / Family / Unlimited+ / Business).
- Measured: gate latency 0.9 ms p50, 1.9 ms p95. RAG generation 2.6 s avg, 4.7 s p95. Throughput 9.5 scenarios/minute single-user serial.

## Required sections

1. Problem Statement: marketers using LLM copy generation lose visibility into brand-voice drift, citation provenance, and legal exposure. State why this matters in revenue or risk terms.
2. Target User: marketing managers, brand leads, legal reviewers, AI PMs evaluating governed marketing AI for procurement.
3. Solution: the four-component architecture + three reused governance primitives, framed as how each component addresses a specific user need.
4. Competitive Positioning: name Persado, Phrasee, Jasper, Writer specifically. Position BrandGuard against each by named differentiator: deterministic gate, audit trail (WORM), citation-required output, kill-switch. Be honest about where competitors are stronger (incumbent scale, native CMP integrations).
5. Business Impact: scope what this protects (brand reputation, legal exposure, audit defensibility) and what it does not measure (campaign performance, conversion lift).

## Voice + constraints

Strand Wireless brand voice (data/brand_voice.md). Plain English. Numbers in pricing/data context. No em dashes. No filler intensifiers from the banned phrase list. Cite source files with [file:path/to/x.py] where claims point to code.
