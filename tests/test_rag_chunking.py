"""Tests for RAG chunking and retrieval."""

from __future__ import annotations

from brandguard.agents.rag_copy_generation import (
    BRAND_VOICE_PATH,
    FACT_SHEET_PATH,
    build_index,
    chunk_brand_voice,
    chunk_fact_sheet,
    retrieve,
)


def test_brand_voice_chunks_emit_section_anchors():
    text = BRAND_VOICE_PATH.read_text(encoding="utf-8")
    chunks = chunk_brand_voice(text)
    anchors = [c.anchor for c in chunks]
    assert "[brand_voice:§1]" in anchors
    assert "[brand_voice:§4]" in anchors
    assert "[brand_voice:§7]" in anchors
    assert all(c.source == "brand_voice" for c in chunks)


def test_fact_sheet_chunks_emit_field_anchors():
    text = FACT_SHEET_PATH.read_text(encoding="utf-8")
    chunks = chunk_fact_sheet(text)
    anchors = [c.anchor for c in chunks]
    assert "[fact_sheet:essentials:price]" in anchors
    assert "[fact_sheet:pro:data]" in anchors
    assert "[fact_sheet:family:hotspot]" in anchors
    assert "[fact_sheet:unlimited_plus:data]" in anchors
    assert "[fact_sheet:business:eligibility]" in anchors


def test_retrieval_pulls_correct_anchor_for_business_pricing():
    """Real fastembed + FAISS: querying for business pricing surfaces the matching anchor."""
    index = build_index()
    chunks = retrieve(
        index, "Strand Business price per line per month with autopay", top_k=5
    )
    anchors = {c.anchor for c in chunks}
    assert "[fact_sheet:business:price]" in anchors
