"""Verifier tests (Doc QC pipeline).

Three tests asserting the deterministic Verifier behaves like a strict gate:
banned phrases block, hallucinated citations block, a clean doc passes.
"""

from __future__ import annotations

from pathlib import Path

from scripts.doc_pipeline.verifier import verify

REPO_ROOT = Path(__file__).resolve().parents[1]
BANNED = REPO_ROOT / "scripts" / "doc_pipeline" / "banned_phrases.txt"

CLEAN_DOC_BODY = (
    "# Sample\n\n"
    + ("Strand Wireless writes plain copy with numbers. " * 50)
    + " The autopay disclosure runs through every quote."
)


def _write(tmp_path: Path, body: str, floor: int = 100) -> Path:
    p = tmp_path / "sample.md"
    p.write_text(
        f"---\nstate: REVISED\nword_count_floor: {floor}\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return p


def test_verifier_blocks_banned_phrase(tmp_path: Path):
    body = (
        "# Sample\n\nStrand Wireless plans to synergize across the marketing stack. "
        + ("Filler text. " * 100)
    )
    doc = _write(tmp_path, body)
    result = verify(doc, BANNED, REPO_ROOT)
    assert result.passed is False
    rule_ids = [f.rule_id for f in result.failures]
    assert "banned_phrase" in rule_ids


def test_verifier_blocks_missing_citation(tmp_path: Path):
    body = (
        "# Sample\n\n"
        + ("Body text describing the system. " * 60)
        + " See [DJ-999] for the original decision."
    )
    doc = _write(tmp_path, body)
    result = verify(doc, BANNED, REPO_ROOT)
    assert result.passed is False
    rule_ids = [f.rule_id for f in result.failures]
    assert "citation_dj" in rule_ids


def test_verifier_passes_clean_doc(tmp_path: Path):
    doc = _write(tmp_path, CLEAN_DOC_BODY, floor=100)
    result = verify(doc, BANNED, REPO_ROOT)
    assert result.passed is True, result.failures
    assert result.failures == []


def test_orchestrator_patches_frontmatter_state_on_verified(tmp_path: Path):
    """DJ-017: after orchestrator transitions to VERIFIED, the doc's frontmatter
    state field is rewritten from DRAFTED/REVISED to VERIFIED.

    We exercise the helper directly (no LLM calls) since it is the unit of work
    that DJ-017 codifies. End-to-end orchestrator flow already covered by the
    proof run in Session 5A.
    """
    from scripts.doc_pipeline.orchestrator import _patch_frontmatter_state

    doc = tmp_path / "sample.md"
    doc.write_text(
        "---\nstate: REVISED\nword_count_floor: 100\nbrief: x.brief.md\n---\n\nbody text",
        encoding="utf-8",
    )
    _patch_frontmatter_state(doc, "VERIFIED")
    text = doc.read_text(encoding="utf-8")
    state_line = next(line for line in text.splitlines() if line.startswith("state:"))
    assert state_line == "state: VERIFIED"
    # Idempotent: second call leaves it unchanged.
    _patch_frontmatter_state(doc, "VERIFIED")
    state_line2 = next(
        line for line in doc.read_text().splitlines() if line.startswith("state:")
    )
    assert state_line2 == "state: VERIFIED"


def test_verifier_blocks_missing_pdr_citation(tmp_path: Path):
    """DJ-020: the PDR resolver was missing. A [PDR-NNN] reference to a
    non-existent PDR must now block.
    """
    pdr_dir = tmp_path / "docs" / "pdr"
    pdr_dir.mkdir(parents=True)
    (pdr_dir / "PDR-001.md").write_text("# PDR-001\n", encoding="utf-8")

    doc = tmp_path / "test_doc.md"
    doc.write_text(
        "---\nword_count_floor: 5\n---\n\n"
        "# Test\nThis cites [PDR-001] (exists) and [PDR-999] (does not).\n",
        encoding="utf-8",
    )
    result = verify(doc, BANNED, tmp_path)
    assert result.passed is False
    assert any(f.rule_id == "citation_pdr" for f in result.failures)
    # The real PDR-001 reference should not be flagged.
    assert not any("PDR-001" in f.message for f in result.failures)


def test_verifier_blocks_dangling_prose_path(tmp_path: Path):
    """DJ-020: prose-form backtick paths starting with a known top-dir are now
    resolved. A path to a non-existent file must block.
    """
    doc = tmp_path / "test_doc.md"
    doc.write_text(
        "---\nword_count_floor: 5\n---\n\n"
        "# Test\nSee `docs/nonexistent.md` for details.\n",
        encoding="utf-8",
    )
    result = verify(doc, BANNED, tmp_path)
    assert result.passed is False
    assert any(f.rule_id == "citation_prose_path" for f in result.failures)
