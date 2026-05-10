# Decision Journal: BrandGuard AI

**Owner:** Kamil Mufti  
**Purpose:** Append-only structured log of every architectural, product, and process decision made on this project. Source artifact for ADRs (HOW) and PDRs (WHY). Each entry includes the question, options considered, the decision, the thesis, the honest counter-argument, downstream implications, and a 30-second interview framing.

**Discipline:**

- Append-only. DJ-NNN numbers are permanent once committed.
- Status changes via field update. Text changes only via explicit `### REVISED YYYY-MM-DD` addendum block; never silent edit.
- Bar: architectural / product / process decisions only. Not implementation choices.
- Word count floor: 250 per entry. No ceiling; Critic rubric flags bloat.
- Backfilled entries explicitly note backfill date and source.

**Status legend:**

- `Open`: under consideration, not yet committed
- `Decided`: choice made, in effect
- `Promoted to PDR-NNN`: surfaced to a polished Product Decision Record
- `Promoted to ADR-NNN`: surfaced to a polished Architecture Decision Record
- `Superseded by DJ-NNN`: newer decision overrides this one

**Format spec (per entry):**

```
## DJ-NNN: [Decision Name]
Date: YYYY-MM-DD
Session: X
Status: Open | Decided | Promoted to PDR-NNN | Promoted to ADR-NNN | Superseded by DJ-NNN
Owner: Kamil

### The Question
[One paragraph framing the actual question.]

### Options Considered
- A: [position + what it signals]
- B: [position + what it signals]
- C: [position + what it signals]

### Decision
[The choice + confidence.]

### Why This Choice
[Thesis. 2-4 sentences. What property does this protect?]

### What This Forecloses
[Honest counter-argument. What's worse about this path? What complaint can be fairly raised?]

### Downstream Implications
[What this requires from later work.]

### Interview Framing
[30-second answer if asked "why did you do it this way?" Direct.]

### Related
[Cross-references.]
```

**Table of contents (auto-generated or manually maintained):**

- DJ-001: Synthetic-only data with a fictional brand identity
- DJ-002: Deterministic safety gate at the release boundary
- DJ-003: Brand voice as deterministic principle-encoded check
- DJ-004: `injected_copy` fixtures for BLOCK scenarios in live eval
- DJ-005: Two-knob O1 churn retune
- DJ-006: P22 codified (don't reintroduce LLM judgment)
- DJ-007: Doc QC pipeline (Author / Critic / Verifier)
- DJ-008: Split eval evidence (deterministic committed + LLM regenerable)
- DJ-009: Mini-session pattern (X.1 for tight scope)

---

## DJ-001: Synthetic-only data with a fictional brand identity

Date: 2026-05-09
Session: 1, 2B (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

A marketing-AI portfolio piece needs a customer database, brand documentation, and product collateral to be useful. Where does that data come from? Real CRM data is unavailable to a solo developer; even if it were, committing it to a public repo creates compliance exposure (PII, GDPR, CCPA). Using a real existing brand carries collision and trademark risk. What's the right substrate?

### Options Considered

- A. Anonymize a real public dataset and use a real-world brand name as a placeholder. Signals familiarity with real data; carries de-anonymization and collision risk.
- B. Synthesize the corpus AND invent a fictional brand. Signals discipline about data ethics; gives full control over edge cases; nothing to leak.
- C. Use generic placeholders ("BrandX", "Customer 1"). Simplest; reads as toy.

### Decision

B. Synthetic 500-record corpus generated from seed=42 (deterministic). New fictional telecom brand "Strand Wireless," chosen after web-searching 3 candidates and rejecting 2 for collision risk (Tessera Mobile collision with Tessera Mobile Systems Inc; Northwind Mobile crowded by Northwind Wireless and Northwind Communications). Confidence: High.

### Why This Choice

A public repo demonstrating marketing AI must not contain or evoke real customer data. A fictional brand removes the collision and trademark surfaces. A search-validated fictional name (P19-adjacent: claims should be testable) removes the "did you check?" interview question. Determinism via seed=42 means anyone can regenerate the corpus and verify reproducibility.

### What This Forecloses

The portfolio cannot show how the system handles real-world data quirks (typos in addresses, ambiguous account hierarchies, real timezone edge cases). A reviewer who wants to see "messy real data handling" sees engineered data instead.

### Downstream Implications

The brand voice document and product fact sheet had to be authored from scratch (no public source to lift). Citation IDs (§1-§7, [fact_sheet:<sku>:<field>]) became the system's anchor surface, which later enabled the citation existence rule in the gate (DJ-002).

### Interview Framing

Public repo, can't ship real customer data. So I synthesized 500 records deterministically and invented a telecom brand after checking three candidate names against real US carriers. Trade-off: I don't get to demo on messy real data; I do get a corpus I can regenerate, citation anchors that exist by construction, and zero PII exposure.

### Related

DJ-002 (deterministic gate), DJ-003 (brand voice deterministic), Notion Session 2B Log, Context v1.4. Backfilled 2026-05-09 from Context v1.4 and Session 2B Log.

---

## DJ-002: Deterministic safety gate at the release boundary

Date: 2026-05-09
Session: 1, 3 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

LLM-generated marketing copy can be misleading: hallucinated facts, undisclosed legal terms, off-brand language, missing disclaimers. Some kind of safety check has to gate the output before it reaches a user. Should the gate be an LLM-as-judge that scores generated copy and routes ALLOW or BLOCK based on the score, or a rule-based deterministic check that fails closed on specific violations?

### Options Considered

- A. LLM-as-judge gate. Flexible, handles novel violation types, easy to update via prompt changes.
- B. Deterministic rule engine. Strict, auditable, fast, fails closed on known violation types.
- C. Hybrid: LLM-judge for nuanced violations, deterministic for legal/disclosure rules.

### Decision

B. Three deterministic rules at the release boundary: citation existence, autopay disclosure, unlimited disclosure. No LLM in the routing path. Fail-closed. Confidence: High.

### Why This Choice

The gate is the only thing standing between the LLM and the user. If the gate's logic is itself probabilistic, the safety guarantee is probabilistic. For known violation types (legal disclosure, brand-mandated disclaimers, citation faithfulness), the rules are mechanically encodable. Encoding them as code makes the gate auditable, deterministic, and 0.9 ms fast (Session 4.1 measurement: gate is 0.03% of per-scenario latency vs 99.9% for the LLM nodes). No LLM call, no token cost, no variance run-to-run.

### What This Forecloses

Novel violation types not anticipated in code aren't caught. A hostile prompt that emits a violation pattern outside the rule set passes the gate. Trade-off accepted: known-knowns are strict; novel attacks require eval-harness exposure to surface, then rule additions. The eval harness is the early-warning system for new rule needs.

### Downstream Implications

P22 was codified from this decision (DJ-006). Brand voice alignment was designed deterministic for the same reason (DJ-003). The gate's sub-millisecond performance became a defensible resume bullet (Bullet 2). The eval harness exists partly to find violations the gate doesn't catch yet.

### Interview Framing

The gate is the safety boundary. I refuse to let an LLM be the safety boundary's logic. So the three rules are deterministic Python: citation must exist in the RAG sources, autopay disclosure must accompany autopay pricing, unlimited claims must include the deprioritization caveat. Sub-millisecond latency, zero variance. The eval harness, ragas-style, is what catches what the rules don't.

### Related

ADR-003, DJ-003, DJ-006 (P22), Session 4.1 latency data, src/brandguard/governance/legal_brand_review_gate.py. Backfilled 2026-05-09 from ADR-003 and Session 3 Log.

---

## DJ-003: Brand voice as deterministic principle-encoded check

Date: 2026-05-09
Session: 4 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

The eval harness needs a metric for whether generated copy adheres to the brand voice. Brand voice has 8 principles (em dash ban, no filler intensifiers, numbers in pricing context, autopay/unlimited disclosures, etc.). Should brand voice alignment be scored by an LLM judge against a rubric, or by deterministic Python rules that check each mechanically-encodable principle?

### Options Considered

- A. LLM rubric-scored. Flexible, handles tone-by-context, can score "personality fit." Re-introduces LLM judgment.
- B. Deterministic principle-encoded. Each mechanically-encodable principle is a Python check. Score deducts 0.20 per detected violation. Rigid, auditable, byte-stable.
- C. Hybrid: deterministic for mechanical principles, LLM for tone and personality. Forks the metric into two parts.

### Decision

B. Deterministic, principle-encoded. Five checks: §4.2 unlimited disclosure, §4.3 filler intensifiers, §4.6 numbers in pricing context, §4.8 em dashes, autopay disclosure. Tone-by-context principles (§3 personality traits) explicitly NOT in the metric. Confidence: High.

### Why This Choice

The same fail-closed logic that justified DJ-002 applies here. Mechanically-encodable principles deserve mechanical checks. Putting an LLM in the alignment metric would re-introduce non-determinism into what should be a stable score. Tone judgments that resist mechanical encoding belong in human review, not in an LLM-as-judge automated metric. The trade-off is accepted: the metric covers fewer principles than a rubric would, but the principles it covers are scored deterministically.

### What This Forecloses

The metric won't catch tone drift ("sounds robotic", "too corporate") that a human reviewer or LLM judge would catch. Brand voice in the looser sense (personality, voice fit) is unmeasured by this metric. If a reviewer asks "does the system measure overall brand voice adherence?", the honest answer is "the mechanical principles, yes; the tonal principles, no, those are human-reviewer territory."

### Downstream Implications

P22 was codified directly from this and DJ-002 (DJ-006). The eval report has 6 metrics (5 quality + 1 timing in Session 4.1) with 4 deterministic and 2 LLM-judged. The split is documented in the eval_harness.py module docstring. Future rubric-vs-deterministic decisions in this project default to deterministic.

### Interview Framing

Brand voice has principles. Some are mechanical: no em dashes, no filler intensifiers, autopay disclosure when you quote autopay pricing. Those get deterministic Python checks. Others are tonal ("sounds like Strand Wireless") and those resist code. I draw the line: mechanical principles in the metric, tonal principles to human review. The metric doesn't lie about what it measures.

### Related

DJ-002, DJ-006 (P22), src/brandguard/eval/eval_harness.py, brand_voice.md §4. Backfilled 2026-05-09 from Session 4 Log.

---

## DJ-004: `injected_copy` fixtures for BLOCK scenarios in live eval

Date: 2026-05-09
Session: 4 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

The legal/brand review gate has three BLOCK paths: hallucinated anchor, undisclosed autopay, undisclosed unlimited. The eval harness should exercise these paths in a live run against the real LLM. But the LLM (Haiku 4.5 with the brand-voice system-prompt floor) almost never emits these failure modes. How do we exercise BLOCK paths in live eval without faking results?

### Options Considered

- A. Live LLM only. Wait for the LLM to organically produce failures. Honest but produces few BLOCK observations.
- B. Inject pre-written copy with the failure pattern, route it through the rest of the pipeline normally. Documented as a fixture, not a hallucination.
- C. Adversarial prompts to coax failures. Might fail to produce them; pollutes the brief.

### Decision

B. Three BLOCK scenarios (G016 hallucinated anchor, G017 undisclosed autopay, G018 undisclosed unlimited) carry an `injected_copy` field. The eval runner returns the injected copy from a dispatch instead of calling the LLM for those scenarios. ALLOW scenarios still hit the real LLM. Documented in the runner script and in the golden_dataset.json schema. Confidence: High.

### Why This Choice

The gate's BLOCK paths are real and need exercise. Without injection, the eval reports only ALLOW behavior; the gate appears unused. Injection is honest: the eval distinguishes "what the LLM produced" from "what the gate caught given an input." The runner explicitly logs which scenarios used injection. A reviewer reading the eval report can see the distinction.

### What This Forecloses

The injected copy is hand-crafted, not LLM-emitted. So we don't get the natural variation a real LLM failure would have. The 3 fixtures are 3 specific failure modes, not the full distribution of how the LLM might fail. If the LLM later starts failing in a 4th way, we wouldn't see it in this eval; we'd see it in production or in the real-LLM ALLOW scenarios that fail.

### Downstream Implications

The eval report explicitly notes which scenarios used injection. P19 (resume claims testable) covers this: any bullet about "deterministic safety gates blocking violations" must be defensible against the injection, not just against organic LLM failures. The framing in resume bullet 1 already accounts for this: "deterministic human-in-the-loop safety gates enforcing legal disclosure and brand-safety rules in code."

### Interview Framing

The gate is designed to BLOCK three failure modes. The LLM with the brand-voice floor almost never emits them. So I injected pre-written copy with each failure pattern as a fixture, ran it through the rest of the pipeline, and confirmed the gate BLOCKs as expected. Fixtures are explicit in the dataset, not hidden. The honest framing: ALLOW scenarios test the LLM; BLOCK scenarios test the gate; both matter.

### Related

data/golden_dataset.json, scripts/run_eval_report.py, Session 4 Log scope-drift flag 3. Backfilled 2026-05-09 from Session 4 Log.

---

## DJ-005: Two-knob O1 churn retune (threshold AND autopay weight)

Date: 2026-05-09
Session: 4 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

Session 2B's corpus had 444 low / 54 medium / 2 high churn-risk records out of 500. With only 2 high-risk records, retention-copy eval scenarios couldn't get a meaningful signal. The original Session 4 plan was to drop the high-risk threshold from 4 points to 3 (one knob). Should we leave it at one knob, or also adjust the weight of "autopay not enrolled" because that's a real-world strong churn signal?

### Options Considered

- A. One-knob change. Drop threshold 4 to 3. Minimal change, simplest to explain.
- B. Two-knob change. Drop threshold AND bump autopay-not-enrolled weight from +1 to +2 (autopay non-enrollment is empirically a strong real-world churn signal in telecom).
- C. Re-design the heuristic from scratch.

### Decision

B. Two-knob retune. Threshold 4 to 3 plus autopay weight +1 to +2. New distribution 306 / 164 / 30. 30 high-risk out of 500 is 6%, in the spec's 20-80 target band (4-16%). Deterministic from seed=42 (re-verified by running twice and diffing). Confidence: High.

### Why This Choice

The original heuristic was undertuned in two ways, not one. Just dropping the threshold would have produced a more balanced distribution, but the autopay signal was undervalued for the telecom domain we're modeling. The two-knob retune is more truthful about what drives churn in real telecom data, and the resulting distribution is stronger across both retention scenarios and segmentation edges.

### What This Forecloses

The retuned heuristic is still a hand-crafted approximation. It's not derived from real telecom data, so it doesn't capture interactions (e.g., billing tenure × plan type × international usage). A more sophisticated approach would model these interactions; we don't, because the corpus is for portfolio demonstration, not production prediction.

### Downstream Implications

Retention/churn eval scenarios now have meaningful coverage (3 scenarios in the 20-scenario golden dataset). Future eval expansion can lean into retention without thinking about distribution. The retune is captured as a backfill-eligible decision because it was a judgment call: the spec asked for one knob, and the author identified a second one that mattered.

### Interview Framing

The original churn distribution was too skewed for retention scenarios to be testable. The minimum fix was a one-line threshold change. I made it a two-line change instead, because autopay non-enrollment is a stronger churn signal in real telecom than my original heuristic gave it credit for. New distribution 306/164/30 sits in the 4-16% high-risk band, deterministic from seed 42, and the retention eval scenarios now produce signal.

### Related

scripts/corpus_generator.py, data/synthetic_crm_corpus.json, Session 4 Log O1 evidence section. Backfilled 2026-05-09 from Session 4 Log.

---

## DJ-006: P22 codified, don't reintroduce LLM judgment for code-answerable questions

Date: 2026-05-09
Session: 3, 4 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

After DJ-002 (deterministic gate) and DJ-003 (deterministic brand voice metric), a pattern was visible: every time the architecture faced a "should the LLM judge this" question, the answer was "no, encode it deterministically if mechanically possible." Should this pattern become an explicit process rule, or stay as case-by-case judgment?

### Options Considered

- A. Case-by-case. Each rubric-vs-deterministic question gets evaluated on its own merits.
- B. Explicit process rule (P22): default to deterministic, with LLM acceptable only for offline regression metrics that never gate releases.
- C. Stronger explicit rule: deterministic-only, no LLM-judged metrics anywhere.

### Decision

B. P22: don't reintroduce LLM judgment for code-answerable questions. Eval metrics, gate rules, and constraint checks default to deterministic. LLM judgment is acceptable for offline regression on questions that resist mechanical encoding (e.g., faithfulness across paraphrase) but not for any release-gating decision or any check where mechanical encoding is feasible. Confidence: High.

### Why This Choice

The pattern was strong enough to be a rule. Codifying it prevents future drift: when Session 4 was scoping the eval harness, P22 made the brand voice deterministic-vs-LLM choice automatic instead of debatable. The Session 4.1 timing data vindicated the rule: deterministic checks are 0.03% of latency, LLM nodes are 99.9%. Encoding the rule made the architecture cheaper AND stronger, simultaneously.

### What This Forecloses

Some questions genuinely benefit from LLM judgment (e.g., subjective tone fit, paraphrase-tolerant faithfulness). P22 doesn't ban these, but it forces a explicit "this is the case where LLM judgment is the right tool" justification before they get used. Slight friction. Acceptable: friction in the right place.

### Downstream Implications

Every future eval metric or gate rule starts with the question "is this code-answerable?" If yes, it's deterministic by default. The eval_harness.py module docstring explicitly documents which metrics are LLM-judged and why each one is. PDR-002 (planned for Session 5B) will cite P22 and DJ-002/003/006 as foundation.

### Interview Framing

Pattern recognition. After two architectural decisions in a row chose deterministic over LLM-judged for the same reason ("the safety-relevant logic shouldn't itself be probabilistic"), I codified the pattern as a process rule. P22: don't reintroduce LLM judgment for code-answerable questions. The Session 4.1 timing numbers vindicated it: code is faster than judgment by orders of magnitude, and the deterministic checks have zero variance.

### Related

DJ-002, DJ-003, Context v1.7 process fix log, Session 4.1 latency data. Backfilled 2026-05-09 from Context v1.7 process fix log entry.

---

## DJ-007: Doc QC pipeline (Author / Critic / Verifier) for documentation discipline

Date: 2026-05-09
Session: planning v1.6 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

Session 5B will produce 9 product docs and 4 PDRs. Without a QC mechanism, those docs risk reading like "a PM textbook explained the prompt." How do we keep documentation honest, specific, and not hand-wavy?

### Options Considered

- A. Hand-write every doc with manual review. Slow, depends on the author's discipline alone.
- B. Author / Critic / Verifier pipeline: subagent drafts, second subagent grades against a rubric, deterministic Python verifies (banned phrases, citation existence, em dash, cross-references, word count). Only VERIFIED state commits.
- C. Use commercial tooling (Notion AI, etc.) and manually clean up.

### Decision

B. Pipeline with 4-state lifecycle (DRAFTED → CRITIQUED → REVISED → VERIFIED). Maximum 3 cycles per doc; if still failing, human review. Plugin-augmented Author (uses Anthropic's official PM plugin where applicable). Confidence: High.

### Why This Choice

Documentation about decisions deserves the same fail-closed discipline as the legal/brand gate. The same Author/Critic/Verifier separation that prevents an LLM from grading itself in eval (DJ-006) prevents doc theater here: the writer can't approve its own work, the grader is a fresh subagent, and the verifier is plain Python. Pipeline transitions WORM-logged for audit trail.

### What This Forecloses

The pipeline is itself code that needs to be built and maintained. ~3-5 hours in Session 5A. If the pipeline is buggy, doc quality suffers. Mitigated by Session 5A producing a proof-run on one doc end-to-end before generating the other 12.

### Downstream Implications

P21 (P24 expanded) was codified directly from this decision. The pipeline becomes a second portfolio artifact (see backlog B10: marketplace listing). Decision Journal entries themselves pass through the pipeline once it ships (P24).

### Interview Framing

Most repos have docs. Docs are easy to fake. So I built a small pipeline: one subagent drafts, a second subagent grades against a rubric, plain Python verifies banned phrases and citation links. Only docs that pass all three commit. The pipeline transitions log to a tamper-proof WORM chain. Same fail-closed discipline as the safety gate, applied to documentation.

### Related

P21, P24, Context v1.6 Doc QC Pipeline section, planned in Kanban v1.6 Session 5A. Backfilled 2026-05-09 from Context v1.6.

---

## DJ-008: Split eval evidence: deterministic committed, LLM regenerable on demand

Date: 2026-05-09
Session: 4 (Q1 decided this session)
Status: Decided
Owner: Kamil

### The Question

The Session 4 eval report mixes deterministic metrics (citation existence, brand voice alignment, context precision/recall, throughput) with LLM-judged metrics (faithfulness, answer relevance). LLM-judged metrics drift run-to-run because of model variance. If the report commits as a single artifact, the file diffs every time it regenerates, even when nothing material changed. Two questions: should this matter, and if so, what's the fix?

### Options Considered

- A. Accept LLM drift. Commit current eval_report.md as-is. Note in README that LLM metrics are non-deterministic. Simpler.
- B. Split: deterministic metrics commit-stable, LLM metrics regenerate on demand and aren't committed. Cleaner artifact discipline.
- C. Don't commit any eval evidence; require regeneration to view results.

### Decision

B. Split eval evidence. `docs/eval_report_deterministic.md` (or equivalent) commits with stable metrics. `eval_report_llm.json` (or equivalent) regenerates on demand to a gitignored path. README documents the split in 4 lines. CLI flag controls which side runs. Confidence: High.

### Why This Choice

A committed artifact should mean "this is what the system produced and what you can verify." If you re-run and get different numbers, the file is lying about its stability. Splitting the evidence enforces that committed = reproducible, regenerable = exploratory. This is the same discipline as DJ-002 and DJ-003 applied to the artifacts themselves: the deterministic / LLM boundary isn't just at the metric level, it's at the version-control level. Strengthens the planned PDR-002 (eval design rationale): two reinforcing legs (metric design + artifact discipline) instead of one.

### What This Forecloses

A single-file eval report is gone. Two files / two artifacts means slightly more friction to read the full picture. README mitigates by documenting where each piece lives. Some readers will find the split fussy.

### Downstream Implications

Session 5A scope expanded to include the split runner implementation (~30 minutes). B17 (eval split runner) collapses into Session 5A. The PDR-002 written in Session 5B can cite this entry as one of its supporting arguments. JD coverage strengthened: "MLOps best practices including versioning datasets" is now backed by visible discipline about what does and doesn't go in version control.

### Interview Framing

Eval evidence has two kinds: deterministic and LLM-judged. Mixing them in one committed file makes the file lie about its stability. So I split them: deterministic metrics commit alongside the code, LLM metrics regenerate on demand to a gitignored path. Same boundary discipline as the gate, applied to the artifacts. The committed file means what it says. Reproducibility is a first-class product property here, not an afterthought.

### Related

DJ-002, DJ-003, DJ-006 (P22), Q1 in Context v1.8, scripts/run_eval_report.py (to be split in Session 5A). Decided 2026-05-09.

---

## DJ-009: Mini-session pattern (X.1 for tight scope)

Date: 2026-05-09
Session: 2A.1, 4.1 (backfilled 2026-05-09)
Status: Decided
Owner: Kamil

### The Question

Some work doesn't fit a full session. Session 2A.1 was a cleanup pass that took under an hour. Session 4.1 was a tight D4 throughput fix that took 1-2 hours. Should these be full sessions, folded into a parent session, or have their own pattern?

### Options Considered

- A. Roll into the parent session (4 with 4.1 inside, 2A with 2A.1 inside). Mixes scope; pollutes the parent session log.
- B. Promote to full sessions (Session 5, Session 6 with renumbering). Inflates session count; misleads about effort.
- C. Mini-session pattern: parent.N decimals for tight scope work. Own session log, own commit, own review cycle. Compact protocol.

### Decision

C. Mini-session pattern. X.1, X.2, etc. for tight scope work. Each gets its own Session Log (Pending Review → Reviewed via assessor) and its own commit. Confidence: High.

### Why This Choice

Tight scope work earns its own discipline without inflating the session count or muddling parent sessions. Session 2A.1 (cleanup) and Session 4.1 (D4) both benefited from being separate from their parents. The pattern is now used twice, which is enough to make it a convention.

### What This Forecloses

Session count metrics ("we shipped in 5 sessions") become harder to interpret if mini-sessions are folded in. Mitigated by being explicit: "Sessions 1, 2A, 2A.1, 2B, 3, 4, 4.1, 4.2" tells the truth. The pattern adds a small bookkeeping cost.

### Downstream Implications

Future tight-scope work will follow this pattern. Session 4.2 (Decision Journal Backfill) is itself a mini-session. The Notion Database tracks all sessions including mini-sessions; the Kanban distinguishes parent and mini in the build plan.

### Interview Framing

Tight scope work gets its own session number with a decimal, like 4.1 for the throughput fix. Each mini-session has its own review cycle, its own commit, its own log. Keeps the parent session focused, keeps the review cycle clean, and tells the truth about effort. Used it twice already; it works.

### Related

Session 2A.1 Log, Session 4.1 Log, this Session 4.2 Log. Backfilled 2026-05-09 from Notion session logs.
