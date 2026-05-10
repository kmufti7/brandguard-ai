# PRODUCT_OVERVIEW rubric (base + extensions)

Inherits the four base dimensions (Specificity, Evidence Trail, Honest Scope, Voice) from base.rubric.md. Score each 0..10. Pass floor 7.

Additional dimensions specific to PRODUCT_OVERVIEW:

## Dimension 5: Business Framing

- 9-10: The doc opens with a problem statement that is provably the buyer's problem, not a feature description. Solution framing follows from the problem, not the other way around. Business impact is quantified or scoped.
- 7-8: Problem statement is real; solution framing is mostly buyer-driven; impact is described.
- 4-6: Reads as feature catalog with a thin problem framing on top.
- 0-3: No business framing; this is a tech-spec-as-product-overview.

## Dimension 6: Competitive Positioning Specificity

- 9-10: Names Persado, Phrasee, Jasper, Writer specifically. Positions BrandGuard against each by NAMED differentiator (governance, deterministic gate, audit trail, etc.), not generic "we are better at X."
- 7-8: Names at least three of the four competitors and positions concretely.
- 4-6: Mentions competitors generically or only one or two named.
- 0-3: No named competitors; positioning is "we exist in a market."

## Required structural sections (Verifier will check via grep)

- Problem Statement
- Target User
- Solution
- Competitive Positioning
- Business Impact

If any required section is missing, the Critic should score Business Framing 5 or below and add an explicit "ask" naming the missing section.
