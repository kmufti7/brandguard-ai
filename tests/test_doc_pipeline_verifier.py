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
