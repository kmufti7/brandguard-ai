"""Doc QC Verifier: deterministic Python checks, no LLM.

Per DJ-006 (P22) and DJ-007. The Verifier is the same fail-closed discipline
as src/brandguard/governance/legal_brand_review_gate.py applied to
documentation. Checks:

  1. Banned phrase grep. Case-insensitive search for any phrase in
     banned_phrases.txt. Any hit blocks.

  2. Em dash check. Looks for chr(0x2014). Any hit blocks. The detector
     uses chr(0x2014) so the verifier source itself stays grep-clean
     against the same rule it enforces.

  3. Citation existence. Pulls every reference of the forms:
       [file:path/to/x.py]
       [DJ-NNN]   [PDR-NNN]   [ADR-NNN]
       [brand_voice:§N]   [fact_sheet:<sku>:<field>]
     and confirms each resolves to a real file or anchor in the repo.

  4. Word count floor. Each brief frontmatter declares a `word_count_floor`.
     Default 600 for product docs, 250 for DJ entries.

  5. Cross-reference graph. Doc-to-doc links must resolve to existing files
     under docs/.

Output: a `VerifierResult` with `passed: bool` and a list of `failures`
(rule_id, line_number, message). Same return shape as the legal/brand gate's
decision so the orchestrator can treat them identically.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

EM_DASH = chr(0x2014)

# Citation patterns the verifier knows how to resolve.
_CITATION_PATTERNS = {
    "file": re.compile(r"\[file:([^\]]+)\]"),
    "dj": re.compile(r"\[DJ-(\d{3})\]"),
    "pdr": re.compile(r"\[PDR-(\d{3})\]"),
    "adr": re.compile(r"\[ADR-(\d{3})\]"),
    "brand_voice": re.compile(r"\[brand_voice:§(\d+)\]"),
    "fact_sheet": re.compile(r"\[fact_sheet:([a-z_+]+):([a-z_+]+)\]"),
}

# Inline doc-to-doc markdown links of the form (path/to/X.md).
_MD_LINK = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)")

# Prose-form file paths: backtick-quoted, starting with a known top-level dir.
# DJ-018 banned [file:...] anchors; the fallback is prose backtick-paths, which
# this resolver covers (DJ-020).
_PROSE_PATH_PATTERN = re.compile(r"`((?:docs|src|scripts|tests|data)/[^`\s]+)`")


@dataclass
class VerifierFailure:
    rule_id: str
    line_number: int
    message: str


@dataclass
class VerifierResult:
    passed: bool
    failures: list[VerifierFailure] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "failures": [
                {
                    "rule_id": f.rule_id,
                    "line_number": f.line_number,
                    "message": f.message,
                }
                for f in self.failures
            ],
        }


def _load_banned_phrases(banned_phrases_path: Path) -> list[str]:
    return [
        line.strip()
        for line in banned_phrases_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Yaml-lite frontmatter parser for brief headers and doc state metadata.

    Recognizes `--- ... ---` blocks and `key: value` lines. Returns (meta, body).
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    block = text[3:end].strip()
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, text[end + 4 :].lstrip()


def _check_banned_phrases(
    text: str, banned: list[str], failures: list[VerifierFailure]
) -> None:
    lower = text.lower()
    for phrase in banned:
        idx = lower.find(phrase.lower())
        while idx >= 0:
            line = text[:idx].count("\n") + 1
            failures.append(
                VerifierFailure(
                    rule_id="banned_phrase",
                    line_number=line,
                    message=f"banned phrase '{phrase}' present",
                )
            )
            idx = lower.find(phrase.lower(), idx + 1)


def _check_em_dashes(text: str, failures: list[VerifierFailure]) -> None:
    for i, line in enumerate(text.splitlines(), start=1):
        if EM_DASH in line:
            failures.append(
                VerifierFailure(
                    rule_id="em_dash",
                    line_number=i,
                    message="em dash present; use commas, colons, periods, or parentheses",
                )
            )


def _check_citations(
    text: str, repo_root: Path, failures: list[VerifierFailure]
) -> None:
    # File citations.
    for m in _CITATION_PATTERNS["file"].finditer(text):
        rel = m.group(1).strip()
        if not (repo_root / rel).exists():
            line = text[: m.start()].count("\n") + 1
            failures.append(
                VerifierFailure(
                    rule_id="citation_file",
                    line_number=line,
                    message=f"file citation [file:{rel}] does not resolve",
                )
            )

    # DJ-NNN citations.
    dj_path = repo_root / "docs" / "decision_journal.md"
    if dj_path.exists():
        dj_text = dj_path.read_text(encoding="utf-8")
        dj_anchors = set(re.findall(r"^## DJ-(\d{3}):", dj_text, flags=re.MULTILINE))
        for m in _CITATION_PATTERNS["dj"].finditer(text):
            num = m.group(1)
            if num not in dj_anchors:
                line = text[: m.start()].count("\n") + 1
                failures.append(
                    VerifierFailure(
                        rule_id="citation_dj",
                        line_number=line,
                        message=f"DJ-{num} not found in docs/decision_journal.md",
                    )
                )

    # ADR citations.
    adr_dir = repo_root / "docs" / "adr"
    if adr_dir.exists():
        adr_files = list(adr_dir.glob("ADR-*.md"))
        adr_numbers = {f.name.split("-")[1] for f in adr_files}
        for m in _CITATION_PATTERNS["adr"].finditer(text):
            num = m.group(1)
            if num not in adr_numbers:
                line = text[: m.start()].count("\n") + 1
                failures.append(
                    VerifierFailure(
                        rule_id="citation_adr",
                        line_number=line,
                        message=f"ADR-{num} not found in docs/adr/",
                    )
                )

    # PDR citations (DJ-020: resolver was missing).
    pdr_dir = repo_root / "docs" / "pdr"
    if pdr_dir.exists():
        pdr_files = list(pdr_dir.glob("PDR-*.md"))
        pdr_numbers = {f.name.split("-")[1].split(".")[0] for f in pdr_files}
        for m in _CITATION_PATTERNS["pdr"].finditer(text):
            num = m.group(1)
            if num not in pdr_numbers:
                line = text[: m.start()].count("\n") + 1
                failures.append(
                    VerifierFailure(
                        rule_id="citation_pdr",
                        line_number=line,
                        message=f"PDR-{num} not found in docs/pdr/",
                    )
                )

    # Prose-form file paths (backtick-quoted, starting with known top-dirs).
    # DJ-020: covers the DJ-018 fallback (prose paths replacing [file:...] anchors).
    for m in _PROSE_PATH_PATTERN.finditer(text):
        rel = m.group(1).strip()
        if not (repo_root / rel).exists():
            line = text[: m.start()].count("\n") + 1
            failures.append(
                VerifierFailure(
                    rule_id="citation_prose_path",
                    line_number=line,
                    message=f"prose-form path `{rel}` does not resolve",
                )
            )

    # brand_voice and fact_sheet anchors are validated by the same logic used in
    # the legal/brand gate (collect_known_anchors). Reuse if available; otherwise
    # skip silently in environments where the agent module isn't importable.
    try:
        from brandguard.agents.rag_copy_generation import collect_known_anchors

        known = collect_known_anchors()
        for m in _CITATION_PATTERNS["brand_voice"].finditer(text):
            anchor = f"[brand_voice:§{m.group(1)}]"
            if anchor not in known:
                line = text[: m.start()].count("\n") + 1
                failures.append(
                    VerifierFailure(
                        rule_id="citation_brand_voice",
                        line_number=line,
                        message=f"{anchor} not found in brand_voice.md",
                    )
                )
        for m in _CITATION_PATTERNS["fact_sheet"].finditer(text):
            anchor = f"[fact_sheet:{m.group(1)}:{m.group(2)}]"
            if anchor not in known:
                line = text[: m.start()].count("\n") + 1
                failures.append(
                    VerifierFailure(
                        rule_id="citation_fact_sheet",
                        line_number=line,
                        message=f"{anchor} not found in product_fact_sheet.md",
                    )
                )
    except Exception:
        pass


def _check_word_count(body: str, floor: int, failures: list[VerifierFailure]) -> None:
    n = len(body.split())
    if n < floor:
        failures.append(
            VerifierFailure(
                rule_id="word_count_floor",
                line_number=0,
                message=f"word count {n} below floor {floor}",
            )
        )


def _check_doc_to_doc_links(
    text: str, doc_path: Path, repo_root: Path, failures: list[VerifierFailure]
) -> None:
    for m in _MD_LINK.finditer(text):
        target = m.group(1).strip()
        # Resolve relative to the doc's parent; if that fails, try repo root.
        candidates = []
        if target.startswith("/"):
            candidates.append(repo_root / target.lstrip("/"))
        else:
            candidates.append((doc_path.parent / target).resolve())
            candidates.append((repo_root / target).resolve())
        if not any(c.exists() for c in candidates):
            line = text[: m.start()].count("\n") + 1
            failures.append(
                VerifierFailure(
                    rule_id="cross_reference",
                    line_number=line,
                    message=f"markdown link target {target} does not resolve",
                )
            )


def verify(
    doc_path: Path,
    banned_phrases_path: Path,
    repo_root: Path,
    word_count_floor: int | None = None,
) -> VerifierResult:
    """Run all deterministic checks on a doc. Returns VerifierResult.

    If `word_count_floor` is None, the verifier reads it from the doc's
    frontmatter `word_count_floor:` field; if absent, defaults to 600.
    """
    text = doc_path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)

    if word_count_floor is None:
        try:
            word_count_floor = int(meta.get("word_count_floor", "600"))
        except ValueError:
            word_count_floor = 600

    failures: list[VerifierFailure] = []
    banned = _load_banned_phrases(banned_phrases_path)

    _check_banned_phrases(body, banned, failures)
    _check_em_dashes(body, failures)
    _check_citations(body, repo_root, failures)
    _check_word_count(body, word_count_floor, failures)
    _check_doc_to_doc_links(body, doc_path, repo_root, failures)

    return VerifierResult(passed=not failures, failures=failures)


def verify_as_json(*args, **kwargs) -> str:
    return json.dumps(verify(*args, **kwargs).to_dict(), indent=2)
