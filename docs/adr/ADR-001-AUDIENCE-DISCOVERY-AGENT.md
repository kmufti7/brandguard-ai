# ADR-001: Audience Discovery Agent

**Status:** Accepted (paper)
**Date:** 2026-05-09
**Deciders:** Kamil Mufti
**Component:** Audience Discovery Agent

---

## Context

Marketing teams need to translate natural-language audience descriptions ("customers in the Northeast who upgraded their plan in the last 90 days and have an open support ticket") into structured segments that can be (a) reviewed by a human, (b) attached to a copy generation request, and (c) audited later. The MVP must work over a synthetic CRM corpus of 500 records, telecom-flavored. No real customer data, no live CRM connection.

The agent has three responsibilities:

1. Parse a natural-language audience query into a structured segmentation specification.
2. Retrieve and segment over the CRM corpus using that specification.
3. Return a structured audience definition plus a human-readable summary, both written to the WORM audit log.

---

## Decision

Build an Audience Discovery Agent that consumes a natural-language query and returns a segmented audience over a 500-record synthetic CRM corpus, telecom-flavored. Use FAISS as the local vector store. Use a structured intermediate representation (segmentation spec) between NL parsing and corpus retrieval so both halves are independently testable.

### Vector store: FAISS (local)

FAISS runs in-process, requires no external service, and has no per-query cost. Marketing data sensitivity (even synthetic data that mirrors real customer attributes) is the deciding factor: a local vector store keeps the corpus, the embeddings, and the queries on the machine running BrandGuard. Cloud vector stores (Pinecone, Weaviate Cloud, etc.) introduce a third-party data plane that the legal review surface would need to account for. FAISS avoids that without sacrificing recall quality at this corpus size.

500 records is well within FAISS's flat-index sweet spot. No need for IVF or HNSW partitioning at this scale; the flat index gives exact nearest neighbors in milliseconds.

### NL parsing approach

Two-stage:

1. **Schema extraction.** The NL query is sent to a foundation model (Claude or GPT-class) with a structured-output schema that defines the segmentation spec fields (geography, plan tier, recency window, support status, custom predicates). The model returns a JSON object conforming to the schema. Strict schema validation rejects anything malformed; on rejection the agent returns a structured error rather than a guessed segment.
2. **Lexical fallback for known fields.** A small set of high-frequency fields (geography names, plan tier names, time windows) are also matched lexically against the query as a sanity check on the LLM's extraction. Disagreement between the lexical pass and the LLM extraction surfaces a warning in the WORM log and routes the request to a clarification step before retrieval runs.

The lexical fallback is not the primary parser. It exists to catch the failure mode where the LLM misreads a numeric or named field, which is the highest-frequency parsing error in this domain.

### Segmentation logic

The segmentation spec is evaluated against the corpus in two passes:

1. **Deterministic predicate filter.** All structured predicates (plan tier, geography, recency window, support status) are applied as Python filters over the corpus. This pass returns a candidate set.
2. **Semantic re-rank (optional).** If the original NL query has a semantic component that does not map to any structured predicate (e.g., "customers who seem frustrated"), the candidate set is embedded and re-ranked against the query embedding using FAISS. The re-rank is an opt-in branch the agent invokes only when the parsed spec marks a semantic field as present.

The deterministic-first ordering means that for queries that fully decompose into structured predicates, the result is exact and explainable. The semantic re-rank is bounded to operate on an already-filtered subset, keeping behavior predictable.

### Output schema

```
AudienceDefinition {
  audience_id: UUID,
  query_natural: str,
  segmentation_spec: {
    structured_predicates: list[Predicate],
    semantic_field: Optional[str],
    raw_llm_extraction: dict
  },
  matched_record_ids: list[str],
  match_count: int,
  human_summary: str,
  parser_warnings: list[str],
  created_at: ISO8601 UTC,
  worm_log_ref: str
}
```

The `human_summary` field is a one- or two-sentence English description of the segment, generated alongside the structured output for use in the legal review surface and reviewer notifications.

---

## Consequences

### Positive

- Fully local data plane for audience queries (FAISS in-process)
- Structured segmentation spec is independently testable from the NL parser
- Deterministic-first segmentation yields explainable results for the common case
- Output schema is stable enough to be the input to the RAG Copy Generation Agent without further mediation

### Negative / accepted trade-offs

- The two-stage parser (LLM + lexical fallback) doubles the parsing path. Acceptable because the lexical fallback catches the highest-impact LLM errors.
- FAISS local indexes do not support online updates without rebuilding. For MVP this is fine (the corpus is static synthetic data); production deployment with a live CRM would need either incremental index update or a different store. Out of MVP scope.
- The optional semantic re-rank is non-deterministic. The WORM log records both the deterministic candidate set and the re-ranked subset so reviewers can see the diff.

---

## Alternatives Considered

- **Cloud vector store (Pinecone, Weaviate, Qdrant Cloud).** Rejected: introduces a third-party data plane and per-query cost without recall benefit at this corpus size.
- **SQL-only segmentation (no vector store).** Rejected: cannot serve the semantic re-rank branch and removes a meaningful capability for queries with subjective language.
- **End-to-end LLM segmentation (no structured spec).** Rejected: not auditable, not reviewable, and not testable in isolation.
