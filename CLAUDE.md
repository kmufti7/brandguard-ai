# CLAUDE.md: BrandGuard AI

This file is the project router for Claude Code sessions on BrandGuard AI. Read it before any work in this directory.

## Project at a Glance

- **Product:** BrandGuard AI, a governed marketing AI product owned by Kaizen Works, LLC. Sole author: Kamil Mufti.
- **Status:** Pre-MVP, paper architecture phase plus scaffolding (Session 2A complete). No agent code yet.
- **License:** Apache 2.0, copyright 2026 Kaizen Works, LLC.
- **Lineage:** Consumes `intelliflow-core` v2 as the upstream governance kernel via `pip install -e`. Lineage is silent in resume contexts and disclosed in README.

## State Protocol (DNA §0)

Notion is the **single source of truth** for project state. The local repo is the source of truth for code and docs only.

- **Notion database:** [BrandGuard AI Version Control](https://www.notion.so/8bdb8b20297648708105838f05d56049)
- **Data source ID:** `1f2a291f-e82d-4ed1-93a4-c938a767fd02`
- **Doc Types:** Context, Kanban, Session Log
- **Status values:** Active, Superseded, Pending Review, Reviewed

Behavior:

1. At session start: read latest Active Context page and latest Kanban page from Notion. The on-disk `backlog.md` is a convenience mirror, not the master.
2. At session end: write a Session Log to Notion with Status = Pending Review. Do not mark Reviewed yourself; that is Kamil's review action.
3. When state changes (Kanban tickets move, Context shifts, scope drifts), update Notion before or alongside the code change, never after a session log is filed.
4. Conflicting state between Notion and a local file: Notion wins. Update the local file to match.

## Architecture

Four native components, three reused governance primitives. See `docs/PRD_BRANDGUARD.md` and `docs/adr/`.

Native:

1. Audience Discovery Agent (FAISS local, telecom-flavored synthetic CRM corpus, 500 records). ADR-001.
2. RAG Copy Generation Agent (single product line, 3-5 SKUs; brand voice as retrieval source plus system-prompt style guide; deterministic citation check). ADR-002.
3. Legal/Brand Review Gate (HITL, fail-closed, extends Kill-Switch Guard; deterministic routing per DNA §8). ADR-003.
4. Hallucination Evaluation Harness (ragas; deterministic citation check pairing per DNA §8; golden dataset 20-30 scenarios in Session 4). ADR-004.

Reused governance primitives from `intelliflow-core` v2:

- WORM Logger
- Kill-Switch Guard
- Token FinOps Tracker

## Language Rules

NEVER use:

- "side project", "portfolio project", "personal project", "hobby"
- "demo" as a noun
- "proof of concept" without "production-grade"
- "module of", "extension of", "vertical of" (anything that subordinates BrandGuard to IntelliFlow OS)
- em dashes (the long dash character). Use commas, colons, periods, parentheses.

USE:

- "marketing AI product", "agentic marketing platform", "governed marketing AI"
- "built and operate", "shipped", "designed and built"

Resume context is silent on the IntelliFlow lineage. README discloses it. Treat that asymmetry as a hard rule.

## Repository Layout

```
brandguard-ai/
  README.md                    Public-facing product framing + lineage disclosure
  CLAUDE.md                    This file
  LICENSE                      Apache 2.0
  pyproject.toml               Python project metadata
  requirements.txt             Runtime deps
  requirements-dev.txt         Dev deps
  backlog.md                   Local mirror of Notion Kanban backlog
  docs/
    PRD_BRANDGUARD.md          Product requirements
    adr/                       Architectural Decision Records (ADR-001 .. ADR-004)
  src/brandguard/
    __init__.py                __version__
    agents/                    Audience, RAG copy
    governance/                Legal/Brand Review Gate (extends intelliflow-core primitives)
    eval/                      ragas harness + deterministic citation check
  tests/                       pytest
```

## Verification Commands

Run on every code change:

```bash
pytest -q
ruff check .
```

Smoke test must pass before any commit. Lint must pass before any push.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ../intelliflow-core
pip install -e .[dev]
pytest -q
```

The `../intelliflow-core` editable install is required for the package to import. If `intelliflow-core` is not at that path, set the environment variable `INTELLIFLOW_CORE_PATH` and re-run, or update the path before `pip install -e`.

## Auto Review

Auto-run `/cc-review` on writes to:

- `docs/PRD_BRANDGUARD.md`
- `docs/adr/*.md`
- `src/brandguard/governance/*` (when populated in Session 3)

## Backlog

See `backlog.md` for B1-B4 from Kanban v1.2. All marked Future, not for v1.0.
