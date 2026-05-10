# Strand Wireless: Brand Voice Document

**Version:** 1.0 (paper architecture phase)
**Owner:** Strand Wireless Brand Lead (fictional persona)
**Last reviewed:** 2026-05-09
**Note:** Strand Wireless is a fictional brand created for BrandGuard AI's synthetic corpus and RAG retrieval. Any resemblance to a real telecom carrier is unintentional.

---

## §1. Brand Name

**Strand Wireless.** Always rendered with both words. Never abbreviate to "SW" or "Strand" alone in marketing copy. Internal tooling may use "Strand" as a short form; external copy does not.

## §2. Tagline

**"The wireless that respects your attention."**

The tagline is a posture more than a slogan. It signals two commitments at once: a network that performs reliably, and a brand that communicates without filler, hype, or asterisks.

## §3. Personality

Five traits, in priority order:

1. **Direct.** We say what we mean in the smallest number of words that still carry the meaning.
2. **Plain-spoken.** We translate technology into how it shows up in a customer's day. We do not lean on industry jargon to sound credible.
3. **Calmly confident.** We do not oversell. We describe what the network does and let the work speak.
4. **Optimistic about technology.** We treat 5G, eSIM, and modern device management as enabling tools, not as buzzwords. We are excited but not breathless.
5. **Customer-respectful.** We write for an adult who has other things to do. We do not waste the reader's time with throat-clearing or repetition.

## §4. Voice Principles

Eight rules. These are the operational instructions the RAG copy generator should treat as defaults.

1. **Plain English first.** Explain technology in terms of what it does for the reader. Reserve technical terms for technical audiences (engineering blog, API docs).
2. **No "unlimited" without disclosure.** If a plan throttles past a soft cap, the cap and the post-cap speed must appear in the same sentence as the word "unlimited", every time.
3. **No filler intensifiers.** Avoid "amazing," "incredible," "best-in-class," "world-class," "next-generation," "cutting-edge," "revolutionary." If a feature is good, describe what it does.
4. **One idea per sentence.** Long sentences with multiple clauses make pricing and policy easy to misread. Break them up.
5. **Active voice for actions, passive only for policy framing.** "We bill you on the 5th of each month" beats "Billing is performed on the 5th." Passive is acceptable when describing a regulatory requirement applied to us, not by us.
6. **Numbers belong in copy.** Specific GB allowances, specific dollar amounts, specific speeds. Vague language ("plenty of data," "fast speeds") fails the citation check at the legal/brand review gate.
7. **No fear-based framing.** We do not sell against competitor failure modes. We describe what we do and let comparisons happen on the customer's terms.
8. **No em dashes.** Use commas, colons, periods, or parentheses. Never the long dash character. Em dashes read as marketing-cliche and are banned across all Strand Wireless copy.

## §5. Vocabulary

Ten do/don't pairs.

| Do say | Don't say | Reason |
|--------|-----------|--------|
| data plan | data package | "Package" is wireline-cable language. We are wireless. |
| monthly bill | invoice cycle | Customers pay bills, not invoice cycles. |
| network | infrastructure | "Infrastructure" is internal/B2B language. |
| coverage area | service footprint | "Footprint" is operations jargon. |
| customer | subscriber | "Subscriber" is a 1990s telecom artifact. |
| sign up | enroll | "Enroll" reads bureaucratic. Reserve for autopay-specific copy where regulators expect it. |
| roaming abroad | international roaming | Drop "international" when "abroad" is already in the sentence. |
| 5G | 5G technology | "5G technology" is a tautology. |
| your account | the account | Possessive "your" makes the relationship personal. |
| switch your number to Strand | port-in your line | Customers do not say "port-in." |

## §6. Tone in Different Contexts

- **Customer support.** Calm, specific, end with a clear next step. Acknowledge the situation in one sentence, give the answer in one sentence, give the action in one sentence.
- **Marketing copy.** Confident but quiet. Lead with what the product does for the reader, then the price, then the caveats. Do not bury caveats.
- **Technical docs.** More precise, less casual. Engineers want unambiguous facts. The voice rules still apply (plain English first, numbers belong in copy), but personality dials down.

## §7. Compliance Baseline

Every claim about Strand Wireless products, pricing, network performance, or coverage must be substantiated by an entry in the product fact sheet, a published rate card, a coverage map dated within 30 days, or an internal benchmark report. The legal/brand review gate (ADR-003) treats unsubstantiated claims as auto-block conditions; the RAG copy generator (ADR-002) treats unsubstantiated claims as citation-check failures and rejects the generation.

This is a generation-time constraint, not a review-time one. Copy that does not cite a substantiating source does not reach the reviewer. The voice doc itself is also a citable source for tone, vocabulary, and framing rules; section IDs (`§1` through `§7`) are stable and may be cited inline as `[brand_voice:§5]`.
