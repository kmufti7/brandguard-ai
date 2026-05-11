---
state: VERIFIED
timestamp: 2026-05-11T22:48:52.608464+00:00
brief: scripts/doc_pipeline/briefs/contributing.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 400
---

# Contributing to BrandGuard AI

Thank you for helping improve BrandGuard AI. This guide explains how to prepare and submit contributions that meet our governance and quality standards.

## Testing Requirements

All pull requests must pass the pytest suite before review. Run the full test battery locally:

```bash
pytest
```

Tests validate both functionality and compliance with brand voice rules. If a test fails, review the output carefully, fix the issue, and run again. Do not submit a PR with failing tests.

## Documentation Quality Control

Every new document or documentation change enters the QC pipeline automatically, as documented in DJ-007. This pipeline enforces:

- Brand voice consistency (checked against data/brand_voice.md)
- Markdown syntax validity
- Citation format and accuracy
- Banned phrase filtering
- Punctuation discipline

Do not bypass or work around this pipeline. If QC blocks your doc, address the flagged issues and resubmit. The pipeline is designed to catch problems early, before they reach production.

## Architectural Decisions

When your contribution introduces or modifies significant architectural choices, create a Decision Journal entry. The DJ process is tracked as P23 internally. Add your entry to docs/decision_journal.md following the existing format:

- Entry ID (next available number, e.g., DJ-018)
- Date
- Decision title
- Context and rationale
- Consequences (what changes as a result)
- Related entries (if any)

This creates a permanent record of why the system works the way it does, helping future maintainers understand design intent.

## Style Discipline

Our style standards are non-negotiable. Two key resources govern your writing:

**Banned phrases and filler language:** scripts/doc_pipeline/banned_phrases.txt contains the definitive list of prohibited terms. These are filtered automatically by QC, so violations will be caught. Review the list before submitting prose-heavy contributions.

**Punctuation and grammar:** data/brand_voice.md section 4 specifies our punctuation rules. Key points: no em dashes (use commas, colons, periods, or parentheses), and prefer concrete numbers over vague modifiers. Read section 4 in full.

## Pre-Pass Discipline (P25)

Before opening a PR, run the pre-pass checks locally:

```bash
scripts/doc_pipeline/verify.sh
```

This catches citation errors, banned phrases, and formatting issues before submission. A green pre-pass does not guarantee QC approval, but a red pre-pass means your PR will be blocked. Fix all pre-pass failures first.

## PR Submission Checklist

- [ ] pytest passes locally
- [ ] Pre-pass checks (scripts/doc_pipeline/verify.sh) pass
- [ ] New docs or doc changes added to the QC pipeline scope
- [ ] Architectural decisions documented in DJ if applicable
- [ ] Brand voice checked against data/brand_voice.md
- [ ] Banned phrases removed (scripts/doc_pipeline/banned_phrases.txt)
- [ ] Punctuation follows section 4 of brand_voice.md

Questions about governance or compliance? Refer to the decision journal (docs/decision_journal.md) or ask the maintainers.
