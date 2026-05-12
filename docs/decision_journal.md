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

---

## DJ-010: Pre-pass discipline for Claude Chat drafts going to CC

Date: 2026-05-09
Session: 4.2
Status: Decided
Owner: Kamil

### The Question

Session 4.2 surfaced a hard contradiction in the CC command Claude Chat drafted. "Commit verbatim" combined with "no em dashes anywhere" and a 0-hit em dash grep verification step. The drafted DJ entries contained 12 em dashes. CC absorbed the cost of resolving it under pressure. Flag, choose reality (em dash ban), substitute, document. CC handled it well. Should the contradiction have reached CC at all?

### Options Considered

- A. Accept that Claude Chat drafts will sometimes contradict project rules. Rely on CC's P20 discipline to catch them at commit time.
- B. Codify a pre-pass discipline. Every Claude Chat-drafted text destined for CC commit must pre-pass the project's Doc QC verifier rules (banned phrases, em dashes, citation format) before being issued in the CC command.
- C. Build a verifier-in-chat tool that Claude Chat runs on its own drafts before sending.

### Decision

B. P25 codified. Claude Chat pre-passes drafts through the same rules CC will verify. CC remains the second-pass guard. Confidence: High.

### Why This Choice

The Doc QC pipeline (DJ-007) exists to keep documentation honest. Claude Chat is one of the authors. Authors that do not self-audit before submission burn CC's review budget on noise. The 12 em dashes in Session 4.2 cost CC time and forced an under-pressure P20 call. Pre-passing in chat catches them in the draft, where revision is cheap.

### What This Forecloses

Slight friction. Claude Chat has to grep its own outputs before issuing CC commands. Mitigated. It is a constant-time check, not a creative bottleneck.

### Downstream Implications

P25 explicit in Context v1.10. Future CC commands from Claude Chat that include verbatim text include a pre-pass step in the chat reasoning. When Session 5A pipeline is built, the same banned phrase list serves as the pre-pass check for chat drafts.

### Interview Framing

Mistake caught. Drafted DJ entries in chat using em dashes while the project bans them. CC flagged it via P20 (always flag, never silent fix), substituted 12 em dashes with equivalent punctuation, documented every swap in the session log. Codified the lesson. Claude Chat now self-audits text drafts against the project's banned-phrase and punctuation rules before sending them to CC for commit. Better hygiene. Same discipline as the Doc QC pipeline.

### Related

DJ-007 (Doc QC pipeline), P20, P21, Session 4.2 Log.

---

## DJ-011: Scaling priorities for the agentic workflow

Date: 2026-05-09
Session: 5A (decided post-Session 4.1 timing data)
Status: Decided
Owner: Kamil

### The Question

The Session 4.1 timing data shows 9.5 scenarios/minute throughput in single-user serial mode. RAG copy generation takes 75% of per-scenario latency, audience discovery 25%, the deterministic gate 0.03%. If this needed to scale to production, in what order should the bottlenecks be addressed, and what does each step trade?

### Options Considered

- A. Vertical scaling. Faster model (Sonnet over Haiku) plus larger embedding model.
- B. Parallelization across scenarios. Run N scenarios concurrently against the LLM and the FAISS index.
- C. LLM-call batching. Batch the prompts of multiple scenarios into single API calls.
- D. Embedding and retrieval caching. Cache FAISS results for repeated audience queries.

### Decision

B then C then D. Vertical (A) is rejected as the first move because it trades cost for latency without addressing the architectural bottleneck. Confidence: High.

### Why This Choice

The data tells the order. RAG copy generation is one async LLM call per scenario. Scenarios are independent. Parallelization is the cleanest unlock. Batching gives the next compression but adds complexity in error handling per scenario. Caching helps only when queries repeat, which is a usage-pattern question that comes after architectural scale. Vertical scaling (bigger model) trades latency for cost and only matters once parallelization is saturated.

### What This Forecloses

Parallelization assumes scenarios are independent. If future work introduces cross-scenario state (e.g., personalization based on prior outputs in the same session), serial is forced again. Batching also assumes the LLM API supports prompt batching efficiently. Current Anthropic API does, but rate limits become the new bottleneck.

### Downstream Implications

B6 (Token FinOps Tracker integration) becomes more relevant because parallelization changes the cost-per-scenario calculation. The eval harness will need a parallel runner mode in Session 5A or 5B. The gate's sub-millisecond performance does not change at scale. It remains negligible.

### Interview Framing

The data says where to spend time. RAG copy generation is 75% of per-scenario latency. Scenarios are independent. So parallelization comes first. Batching second, when the API supports it cleanly. Caching third, because it only matters if queries repeat. Vertical scaling (bigger model) is not the first move because it trades cost for latency without fixing the architecture. Gate is sub-millisecond. Stays sub-millisecond.

### Related

DJ-002 (deterministic gate validated at scale by sub-ms timing), Session 4.1 latency data, backlog B6 (Token FinOps). Decided 2026-05-09 based on Session 4.1 numbers.

---

## DJ-012: WORM logger reuse with session-id prefix for doc pipeline

Date: 2026-05-10
Session: 5A
Status: Decided
Owner: Kamil

### The Question

The doc QC pipeline needs an audit trail of state transitions (DRAFTED, CRITIQUED, REVISED, VERIFIED, FAILED). Three architectural options were on the table for where this trail lives. Each one carries different operational and auditability properties. The pipeline log should be tamper-evident and verifiable, but the doc pipeline is a separate concern from the runtime workflow.

### Options Considered

- A. Separate WORM database file per pipeline. One SQLite file for the runtime workflow, another for the doc pipeline. Clean separation; two chains to verify.
- B. Reuse the runtime WORM logger; segment chains by trace_id prefix. One SQLite file, one chain, every trace_id starts with a prefix that identifies which subsystem produced it (runtime workflow vs doc pipeline).
- C. Build a new audit log abstraction shared by both pipelines. Cleanest architecturally; most work.

### Decision

B. Single WORM database. trace_id prefix segments the chain: runtime workflow uses bare UUIDs; doc pipeline uses `doc_pipeline:<doc_slug>:<run_uuid>`. Verifier of either subsystem reads its slice by prefix filter. Confidence: High.

### Why This Choice

The HMAC-SHA256 hash chain in the WORM logger is the audit defense; splitting the database into two files would create two chains that have to be verified independently, doubling the operational surface. A single chain with trace_id prefix segmentation preserves end-to-end verifiability across the project. The DJ-007 architectural note already anticipated this design; this entry codifies it. Reusing the existing WORMLogRepository class avoids inventing a parallel abstraction whose maintenance would compete with the one already in production use.

### What This Forecloses

A bad doc pipeline write could in theory bloat the runtime workflow's chain or compete on the SQLite write lock. The risk is low because doc pipeline writes are infrequent (one per state transition, not per token), but the failure mode exists and is documented here so future ops work knows the dependency. Hard-separated chains would have isolated this surface; we accepted the trade-off for simpler verification.

### Downstream Implications

Session 5A orchestrator writes to the same WORM DB as run_workflow. The verify_chain() call in run_e2e_sample.py validates the entire chain including any doc pipeline transitions present. If the doc pipeline scales to dozens of docs per run, we may need to revisit option A.

### Interview Framing

The doc pipeline state transitions write to the same WORM logger as the runtime workflow. Same HMAC-SHA256 chain, append-only SQLite triggers, one file. Trace IDs are prefixed to segment the chain by subsystem: `doc_pipeline:product_overview:UUID` versus a bare UUID for runtime runs. One chain to verify end-to-end. Future scaling may force a split, but that day is not today.

### Related

DJ-007 (Doc QC pipeline), src/brandguard/workflow.py, scripts/doc_pipeline/orchestrator.py, intelliflow_core WORMLogRepository.

---

## DJ-013: Critic rubric structure (base + doc-specific extensions)

Date: 2026-05-10
Session: 5A
Status: Decided
Owner: Kamil

### The Question

The doc QC pipeline scores each doc on multiple dimensions. PRODUCT_OVERVIEW has different concerns than a PDR or a Decision Journal entry. Should every doc share one rubric with optional dimensions, should each doc have its own bespoke rubric, or should rubrics inherit from a base?

### Options Considered

- A. Single shared rubric with all possible dimensions; some dimensions ignored per doc type. Simple file structure; rubric file becomes a kitchen sink.
- B. Bespoke per-doc rubric, no inheritance. Each rubric is self-contained. Rubric drift across doc types becomes likely.
- C. Base rubric (Specificity, Evidence Trail, Honest Scope, Voice) plus doc-specific extensions (Business Framing for PRODUCT_OVERVIEW, Counter-Thesis Honesty for PDR, etc.). Inheritance discipline; small files.

### Decision

C. base.rubric.md plus extensions per doc type (product_overview, user_personas, pdr, dj, readme). Pass floor 7 on every dimension. Confidence: High.

### Why This Choice

The four base dimensions (Specificity, Evidence Trail, Honest Scope, Voice) apply to every documentation artifact in the project. Adding them to every rubric by inheritance is cheaper than copying them and keeps the grading bar consistent across doc types. Doc-specific dimensions live alongside the base in a small extension file. The Critic loads the merged rubric at call time. Total surface area stays small; six rubric files cover thirteen briefs.

### What This Forecloses

A rubric that needs to override a base dimension (e.g., relax Voice for a contributor-facing CONTRIBUTING.md) requires explicit prose in the extension. The current setup does not support inheritance overrides cleanly. If override becomes common, the Critic prompt assembly may need a more formal merge step. For Session 5A the simple concatenation is sufficient.

### Downstream Implications

The five doc-specific rubrics created in Session 5A (product_overview, user_personas, pdr, dj, readme) cover the docs that warrant grading distinctions. Remaining doc types (use_cases, success_metrics, roadmap, integration_surface, mlops_playbook, architecture, usage, contributing, data_changelog) use the base rubric only. Session 5B may add extensions as it generates docs and notices weakness in the base scoring.

### Interview Framing

Rubrics inherit. Four base dimensions every doc gets graded on: specificity, evidence trail, honest scope, voice. Each doc type adds two or three dimensions of its own: a product overview gets business framing and competitive positioning specificity, a PDR gets counter-thesis honesty and foreclosed-paths visibility, a Decision Journal entry gets falsifiable thesis and buzzword-free interview framing. Pass floor seven out of ten on every dimension. Below seven anywhere triggers a revision cycle.

### Related

docs/_qc/rubrics/, scripts/doc_pipeline/critic_agent.py, DJ-007 (pipeline), P22 (LLM judgment is rubric-bounded here).

---

## DJ-014: Plugin-vs-encoded Author modes (pmprompt fallback)

Date: 2026-05-10
Session: 5A
Status: Decided
Owner: Kamil

### The Question

Two PM plugins were planned for Session 5A's Author Agent: the Anthropic product-management plugin (write-spec, roadmap-update, etc.) and the pmprompt plugin (prd-writer, jobs-to-be-done, working-backwards, etc.). The pmprompt plugin is blocked on an upstream manifest conflict surfaced during plugin setup. Should we wait for the upstream fix, encode pmprompt's frameworks inline, or run with the Anthropic plugin only?

### Options Considered

- A. Wait. Open issue or PR upstream on pmprompt/claude-plugin-product-management. Session 5A blocked until fixed.
- B. Encode the affected frameworks (jobs-to-be-done, working-backwards) inline in the Author Agent's brief schema. Author Agent supports two modes: plugin (load the Anthropic skill behavior into the system prompt) and encoded (load a named framework definition inline).
- C. Skip the pmprompt frameworks entirely. user_personas.md becomes "audience description" without JTBD discipline. README opens without Working Backwards framing.

### Decision

B. Dual-mode Author Agent. Brief frontmatter `mode: plugin` invokes a named Anthropic plugin skill (system prompt mirrors the documented skill behavior). Brief frontmatter `mode: encoded` loads a named framework text inline (JTBD, Working Backwards, Shape Up). Confidence: High.

### Why This Choice

The pmprompt manifest conflict is an upstream issue with no committed timeline. Blocking on it would delay Session 5A indefinitely. Encoding the frameworks inline costs no LLM quality (Claude knows JTBD and Working Backwards from training; the framework text is a focusing prompt, not novel content). Dual-mode also gives the pipeline portability: if a third plugin becomes relevant later, the Author Agent already supports plugin mode; if a new framework needs encoding, it slots into the encoded-framework dictionary.

### What This Forecloses

The encoded frameworks are not authoritative reproductions of the pmprompt skills. The Author's behavior is approximate, not exact. A reviewer comparing the output to pmprompt's actual skill output may notice deviation. We accept this because the alternative (no JTBD personas, no Working Backwards README) is worse. Session 5B may revisit if pmprompt's manifest conflict gets resolved.

### Downstream Implications

Session 5A pipeline ships with plugin mode (product_overview, success_metrics, roadmap use Anthropic plugin) and encoded mode (user_personas via JTBD, README via Working Backwards, others via project-specific prompts). Backlog item B22 tracks the pmprompt retry. The Author Agent's `_ENCODED_FRAMEWORKS` dictionary is a living artifact; adding a framework is one entry.

### Interview Framing

Two plugins on the table for Session 5A. The Anthropic product-management plugin installed clean. The pmprompt plugin loaded with an upstream manifest conflict. Rather than block, I built dual-mode support in the Author Agent. Plugin mode invokes the Anthropic skill. Encoded mode loads the framework definition inline (JTBD, Working Backwards). Pipeline runs either way. When pmprompt fixes the manifest, encoded mode becomes optional, not required.

### Related

Plugin setup status report, scripts/doc_pipeline/author_agent.py, backlog B22, DJ-007 (pipeline).

---

## DJ-015: Banned phrase list governance (living artifact)

Date: 2026-05-10
Session: 5A
Status: Decided
Owner: Kamil

### The Question

The doc QC verifier blocks any doc containing any phrase from `scripts/doc_pipeline/banned_phrases.txt`. The list shipped Session 5A with 15 phrases (see the file for the full list). New generic noise will surface as docs get generated. How does the list evolve, who is empowered to add phrases, and what is the change-control trail?

### Options Considered

- A. Frozen list. Session 5A's 15 phrases are the final set. New noise survives.
- B. Anyone can add or remove. Edit the file, commit. Fast; loose change control.
- C. Add phrases via DJ entry referencing the new phrase and why it should be banned. Removal also via DJ entry. The list itself is governed by the same Decision Journal that governs every other architectural call.

### Decision

C. Banned phrase list is a living artifact governed by DJ entries (backlog B13). Each addition requires a DJ entry naming the phrase, an example of the doc-text it appeared in, and the reason it counts as generic noise. Removal follows the same path. Confidence: High.

### Why This Choice

The banned phrase list is upstream of every doc that ships. Loose change control (option B) means a maintainer's pet peeve becomes a project-wide block without scrutiny. A frozen list (option A) means the bar erodes over time as the LLM finds new ways to be generic. Governing the list through DJ entries makes additions visible, justified, and reversible. It also creates an audit trail: every banned phrase has a paper trail explaining why it counts as failure.

### What This Forecloses

Adding a phrase costs more than editing a text file. A Decision Journal entry is the bar. Quick experimental additions are harder. We accept this because the list is a shared semantic bar across the project, not a personal style preference. A reviewer should be able to read the DJ entry and agree the phrase belongs in the list.

### Downstream Implications

B13 (Banned phrase list extensions) is the standing backlog ticket for this work. The first time a doc pipeline run reveals a generic noise phrase not in the list, a DJ entry is drafted, reviewed, committed, and the phrase added. The doc pipeline retroactively re-verifies any pending docs against the new list.

### Interview Framing

The banned phrase list is the verifier's grep dictionary. Fifteen phrases shipped Session 5A. Adding or removing a phrase requires a Decision Journal entry that names the phrase, gives an example of where it appeared, and explains why it counts as generic noise. Same change-control discipline as any other architectural call. The list is a living artifact, not a one-time configuration.

### Related

scripts/doc_pipeline/banned_phrases.txt, scripts/doc_pipeline/verifier.py, backlog B13, DJ-007 (pipeline).

---

## DJ-016: Author and Critic Agents via Anthropic API, not nested Claude Code subagent processes
Date: 2026-05-10
Session: 5A (decided), 5B Task 0c (committed)
Status: Decided
Owner: Kamil

### The Question
Session 5A's spec said "spawn a fresh Claude Code subagent (NOT recursive into the same context)" for both the Author and Critic Agents in the Doc QC pipeline. The intent was independent LLM context, role isolation, no orchestrator memory leakage. Reality: spawning a Claude Code subagent process from inside Python is not a callable interface. Anthropic's Python SDK exposes Anthropic API calls, not nested CC processes. How should the orchestrator achieve "fresh subagent" semantics when the literal mechanism is unavailable?

### Options Considered
- A. Wait until nested CC subagent spawning is available; defer the pipeline build.
- B. Implement Author and Critic as fresh Anthropic API calls with role-isolated system prompts. Each call has no shared state with the orchestrator's runtime memory; the LLM instance is a fresh API request.
- C. Use a shared session with role-prompt injection in a single context window.

### Decision
B. Author and Critic are independent anthropic.Anthropic().messages.create() calls with role-specific system prompts. Confidence: High.

### Why This Choice
The semantic intent of "fresh subagent" is independent LLM context, role isolation, no memory leakage from orchestrator state into the agent's reasoning. An Anthropic API call with a role-specific system prompt achieves all three. The LLM has only the system prompt and user message. No chat history from the orchestrator. No shared variables. Each call is stateless on the LLM side. The fact that the Python orchestrator wrapper is the same process is immaterial to the LLM. The orchestrator could be implemented as separate processes; the result would be identical because the LLM only sees its prompt context.

### What This Forecloses
The pipeline cannot use Claude Code-specific subagent affordances (tools, MCP access, file-system permissions) that nested CC processes might offer. For documentation generation, those affordances are not needed. The Author Agent just produces text from a brief; the Critic Agent just scores text against a rubric. If future pipeline stages need file-system access or tool use, they would need either explicit Python implementation or genuine nested CC subagent spawning if and when Anthropic makes it available.

### Downstream Implications
The pipeline architecture is portable. It does not require Claude Code to run. Any environment with the Anthropic SDK can execute the pipeline. This is a portfolio strength: the system is not locked to Claude Code. Documented explicitly in the README and ARCHITECTURE.md when 5B writes those. The Verifier remains plain Python, no LLM. The Author and Critic Agents are bounded by their system prompts; rubric-bounded judgment continues to apply.

### Interview Framing
The spec said "subagent." The closest reality from inside Python is a fresh Anthropic API call with a role-isolated system prompt. Same semantic intent: no memory leakage, fresh LLM context per call. I documented this as an architectural deviation in the Session 5A log and codified it here. The pipeline runs the same on or off Claude Code as a result; portability is a bonus.

### Related
DJ-007 (Doc QC pipeline architecture), Session 5A architectural-delta log entry, P22 (Critic is LLM-judged but bounded by rubric; Verifier is deterministic Python; together they remain fail-closed).

---

## DJ-017: Orchestrator patches frontmatter state on VERIFIED transition
Date: 2026-05-10
Session: 5B Task 0d
Status: Decided
Owner: Kamil

### The Question
The Doc QC pipeline's orchestrator transitions a doc to VERIFIED state by writing a `.qc.json` sidecar. The doc's own frontmatter `state:` field, written earlier by the Author Agent during DRAFTED/REVISED, is not updated. PRODUCT_OVERVIEW.md was committed in Session 5A with `state: REVISED` even though its sidecar correctly shows VERIFIED. Should the orchestrator update the frontmatter, or is the sidecar the canonical truth?

### Options Considered
- A. Orchestrator patches the doc's frontmatter state field on VERIFIED. Single source of truth in the doc.
- B. Sidecar is canonical; frontmatter state is informational. README documents the sidecar as the truth source.
- C. Remove the state field from frontmatter entirely.

### Decision
A. Orchestrator patches frontmatter on VERIFIED. Confidence: High.

### Why This Choice
Most readers will look at the doc, not the sidecar. The frontmatter is the doc's metadata; if it says REVISED while the sidecar says VERIFIED, the doc is lying about its own state. Same artifact-discipline argument as DJ-008 (committed artifacts should mean what they say). The fix is mechanical: one regex rewrite of one line on successful transition.

### What This Forecloses
The frontmatter is now mutable by the orchestrator after the Author writes it. If a future change wants strict author-only writes, it would need to refactor. Acceptable; the orchestrator is the legitimate transition authority.

### Downstream Implications
12 remaining doc runs in Session 5B will have correct frontmatter from the start. The patch backfills PRODUCT_OVERVIEW.md as part of Task 0d.

### Interview Framing
Caught a small bug. Doc frontmatter said REVISED while the sidecar said VERIFIED. Pipeline orchestrator now patches frontmatter on VERIFIED transition. Committed artifacts mean what they say; same discipline as the eval evidence split.

### Related
DJ-007, DJ-008, Session 5A scope-drift flag 4.

---

## DJ-018: File citation anchors forbidden in Author prompts
Date: 2026-05-11
Session: 5B
Status: Decided
Owner: Kamil

### The Question
Session 5B's first pipeline runs failed twice on the same root cause. The Author Agent's LLM kept emitting [file:path] citation anchors to paths that did not exist in the repo (backend/, monitoring/, evaluation_datasets/, src/brandguard/eval/faithfulness_classifier.py, etc.). The Verifier's deterministic citation_file check blocked them on every cycle. The 3-cycle budget exhausted before the LLM stopped inventing files. What is the right architectural response?

### Options Considered
- A. Provide the LLM with a manifest of real file paths at prompt time, asking it to cite only from the manifest. Adds prompt size and an indirect failure mode (LLM still hallucinates from the list).
- B. Forbid [file:path] anchors entirely in the Author prompts. The doc can name files in prose without the anchor syntax. The Verifier never sees a file citation, so never blocks on one.
- C. Add file-existence checks to the Author Agent (post-LLM, pre-write) and strip hallucinated citations before passing to the Verifier. Adds Author complexity.

### Decision
B. The Author's system prompts (encoded and plugin modes) now explicitly forbid [file:path] anchors and instruct the LLM to reference files in prose by name. The Verifier still resolves any [file:...] that appears, but the Author will not produce them. Confidence: High.

### Why This Choice
File anchors are an LLM hallucination magnet. The model has no introspection into the actual repo state; it pattern-matches plausible-sounding paths from training. Forbidding the anchor syntax in the Author prompt eliminates the failure mode at the source rather than fighting it cycle by cycle. The Verifier remains the gate; it just never sees the violation because the Author doesn't emit it. Prose references to file paths ("the legal/brand review gate at src/brandguard/governance/legal_brand_review_gate.py") read just as well to a human reader, with zero hallucination risk.

### What This Forecloses
Docs cannot machine-link to specific files through a verified citation system. If a future reader wanted to click a [file:...] anchor that resolves to a hovercard or IDE jump, that capability is now gone for Author-generated docs. Acceptable trade-off: the docs are primarily for human readers and the prose reference is sufficient. DJ entries, ADRs, and brand voice anchors still use anchor syntax because their resolution is deterministic and verifiable.

### Downstream Implications
The Author prompt change recovered success_metrics, roadmap, architecture, and other docs that had been failing on citation_file blocks. All 16 Session 5B pipeline runs reached VERIFIED. Future briefs do not need to enumerate file paths; the Author Agent simply does not emit them.

### Interview Framing
File citation anchors are an LLM hallucination magnet. The model pattern-matches plausible file paths from training and the verifier blocks them. Rather than fight the LLM cycle by cycle, I removed the temptation: the Author prompt forbids [file:path] anchors and the LLM references files in prose. Same readability, zero hallucination risk. Recovered four pipeline failures with one prompt change.

### Related
DJ-007 (Doc QC pipeline), Session 5B failure-recovery flag, scripts/doc_pipeline/author_agent.py.

---

## DJ-019: README rewrite philosophy (Working Backwards, lineage preserved)
Date: 2026-05-11
Session: 5B Task 7
Status: Decided
Owner: Kamil

### The Question
The Session 2A README was a setup-first document that read like a getting-started guide with product framing tucked at the bottom. Session 5B's Task 7 was to rewrite it. Three things needed to be decided: lead with product framing or setup, where to put the intelliflow-core lineage disclosure, and what level of repo introspection the README should reach.

### Options Considered
- A. Setup-first (current pattern). Reads as a getting-started guide.
- B. Working Backwards / PR-FAQ framing first (per the encoded framework in author_agent.py). Product framing before setup. Lineage disclosure preserved as a top-level section, not buried.
- C. Hybrid: short Working Backwards intro, then setup, then architecture.

### Decision
B. Working Backwards framing leads. The opening paragraph describes what the customer can now do because the product exists. Setup is demoted below the architecture overview. Lineage disclosure is preserved as a top-level section ("Lineage matters. BrandGuard AI consumes intelliflow-core ..."). Confidence: High.

### Why This Choice
A README is the first read of the project for a hiring manager or evaluator. Setup-first signals "this is a tool for engineers to install." Working Backwards-first signals "this is a product that does something specific for a specific user." The latter framing is correct for a portfolio piece. The lineage disclosure preserves the contract from DJ-001 and earlier sessions: intelliflow-core is the upstream governance kernel, and BrandGuard does not subordinate that contribution.

### What This Forecloses
A reader who came to the README looking for "how do I install this" must scroll past product framing to find setup. Mitigated by the Quick Start section being clearly named and reachable; not buried.

### Downstream Implications
Future README revisions follow the same pattern. Other product docs (ARCHITECTURE.md, USE_CASES.md) inherit the lineage disclosure convention.

### Interview Framing
README leads with what the customer can do, not how to install it. Working Backwards framing first. Lineage disclosure to the upstream governance kernel is preserved as a top-level section, not buried. Setup is reachable but demoted. Same product-first discipline as Amazon's PR-FAQ pattern.

### Related
DJ-001 (synthetic data + fictional brand), DJ-007 (doc pipeline), README.md.

---

## DJ-020: Verifier coverage gaps from DJ-018 fallback and missing PDR resolver
Date: 2026-05-10
Session: 5B (discovered), 6 Task 0 (fixed)
Status: Decided
Owner: Kamil

### The Question
DJ-018 banned [file:path] citation anchors from Author prompts because the LLM kept hallucinating them; the fallback was prose backtick-paths like `docs/foo.md`. This works for hallucination prevention but bypasses the Verifier's citation_file check, which only matches the structured form. Separately, the Verifier defines a PDR citation pattern in _CITATION_PATTERNS["pdr"] but has no resolver loop in _check_citations. Together these are two coverage gaps. Should we fix them both, fix one, or accept them?

### Options Considered
- A. Fix both. Add a prose-path resolver to _check_citations (parse backtick paths, check existence). Add the missing PDR resolver loop.
- B. Fix only the PDR resolver (clear bug); document the prose-path gap as accepted trade-off in DJ-018.
- C. Re-allow [file:path] anchors in Author prompts; rely on the Critic to catch hallucinations.

### Decision
A. Fix both. Confidence: High.

### Why This Choice
The Verifier's purpose is to catch what the Critic and Author miss. A coverage gap defeats the purpose. The PDR resolver is a literal bug (pattern defined, no enforcement); the prose-path gap is structural but small to close (regex for paths in backticks, check repo-root existence). Cheap; full coverage restored.

### What This Forecloses
The prose-path resolver may produce false positives if a path-shaped string appears in prose without being an actual reference. Mitigation: only match paths that look like real repo paths (start with known top-level dirs: docs/, src/, scripts/, tests/, data/).

### Downstream Implications
README's dangling docs/README_PRODUCT.md and docs/README_ENGINEERING.md would have been caught at commit time. README either needs those files created or the references rewritten to point at the docs that do exist (ARCHITECTURE.md, USAGE.md). Decided in Session 6 Task 0.

### Interview Framing
Caught a coverage gap in our own Verifier. DJ-018 banned structured file citations to stop the LLM hallucinating paths; the fallback (prose backticks) was not being verified. Plus the PDR resolver was missing entirely. Both fixed in one pass. The pipeline now catches what it was designed to catch.

### Related
DJ-007, DJ-018, Session 5B README rewrite, Session 6 Task 0.

---

## DJ-021: Max-cycles raised from 3 to 5 for long-form docs in Session 5B
Date: 2026-05-10
Session: 5B (decided), 6 Task 0 (backfilled commit)
Status: Decided
Owner: Kamil

### The Question
Session 5A established a 3-cycle ceiling per doc through the Doc QC pipeline (DRAFTED -> CRITIQUED -> REVISED -> CRITIQUED -> ... -> VERIFIED or FAILED after 3). Session 5B encountered ARCHITECTURE.md (1200-word floor) and data/CHANGELOG.md (300-word floor) failing at 3 cycles when the Critic kept finding new asks per revision. CC raised the cycle limit to 5 mid-session to land them. Was that the right call, and should the new limit stand?

### Options Considered
- A. Keep 3-cycle limit; force the rubrics to be looser if a doc cannot pass in 3.
- B. Raise to 5 cycles permanently for all docs; longer docs need more revision room.
- C. Raise to 5 cycles only for docs with word floors >= 1000; keep 3 for shorter docs.

### Decision
B. 5-cycle ceiling permanently for all docs. Confidence: Medium-High.

### Why This Choice
The original 3-cycle limit was a guess, not a measurement. After running 16 docs through the pipeline, evidence shows: 11 of 16 reached VERIFIED in 1-2 cycles, 4 needed 2-3 cycles, 1 (data/CHANGELOG.md) needed 4. None of the 16 took 5 cycles. A 5-cycle ceiling gives long-form docs the revision room they need without inviting endless revision spirals. The rubrics did not need loosening; the pipeline just needed slightly more headroom.

### What This Forecloses
A 5-cycle limit means a maximally bad first draft can burn 5 API calls per agent (Author + Critic) before failing. Slightly higher cost per FAILED doc. Acceptable given the 1-in-16 utilization rate observed in 5B; if a future session sees most docs taking 4-5 cycles, that is a signal to investigate the rubrics or briefs, not raise the limit further.

### Downstream Implications
orchestrator.py max_cycles default updated from 3 to 5. The "max 3 cycles" mention in DJ-007 is now historically true but operationally superseded. README and ARCHITECTURE.md docs that describe the pipeline should reflect the 5-cycle ceiling. P23 backfill: should have flagged this as a decision the same session it was made; folded into Session 6 Task 0.

### Interview Framing
Original spec was 3 cycles max. Ran 16 docs through the pipeline; the longest-form ones needed 4 cycles. Raised to 5 with the data backing the call: nothing took 5, but 1200-word docs need more headroom than I originally guessed.

### Related
DJ-007, Session 5B Log architectural deltas, P23.
