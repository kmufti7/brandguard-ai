---
state: VERIFIED
timestamp: 2026-05-11T22:27:23.352052+00:00
brief: scripts/doc_pipeline/briefs/use_cases.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 700
---

# USE CASES

## Scope

BrandGuard AI governs marketing claims for compliance with FCC regulations and Strand Wireless policies. This document covers use cases in those domains. BrandGuard does not currently audit GDPR, HIPAA, state consumer protection laws, or industry-specific regulations outside telecommunications.

---

## Use Case 1: Regional Speed Campaign Clearance (Essentials SKU)

**Trigger Event**

A regional marketing manager in Texas prepares a campaign claiming "up to 500 Mbps" for a fiber promotion. The campaign runs in 4 cities and targets 200,000 households over 6 weeks.

**Workflow**

The manager uploads the campaign creative to BrandGuard via the Essentials plan. The Citation Agent queries Strand's network performance database and identifies supporting speed test data from the past 90 days covering all 4 cities. The agent flags that 87% of customers in the target areas achieve the claimed speed tier under standard conditions (no deprioritization, no congestion).

The Gate evaluates the Citation Rule:

```
"RULE_CITATION_REQUIRED": {
  "trigger": "any speed claim in marketing material",
  "requirement": "minimum one credible source (internal network test, third-party audit, or FCC Form 477 filing) published within 180 days",
  "action": "PASS if source exists and claim range matches data; FAIL if no source or claim exceeds measured 95th percentile"
}
```

The source exists. The claim (up to 500 Mbps) does not exceed the measured 95th percentile. The Gate returns PASS.

**Expected Outcome**

The manager receives a compliance report showing the citation trail: the exact test dates, sample sizes (4,847 speed tests across all 4 cities), and a downloadable spreadsheet with device type, location ZIP code, and measured throughput for each test. The campaign is approved for immediate launch. The audit trail is retained for 7 years per FCC record-keeping rules.

**Failure Mode Without BrandGuard**

Without system review, the manager publishes the same campaign but omits the speed test data from marketing materials. An FCC complaint arrives 3 weeks later from a consumer who achieved only 320 Mbps. Strand's legal team must reconstruct whether the claim was truthful, delaying response and forcing emergency campaign pull-down. The lack of contemporaneous evidence creates regulatory exposure and damages consumer trust in the market.

---

## Use Case 2: Family Plan Promotion with Autopay Disclosure (Pro SKU)

**Trigger Event**

A national campaign team designs a Family Plan offer: "$79/month for 4 lines, first 3 months $49/month" with enrollment through autopay. The campaign runs across email, paid social, and SMS over 12 weeks reaching 5 million subscribers.

**Workflow**

The team submits the creative to BrandGuard Pro. The Disclosure Agent scans the offer copy and detects a price claim with a time-limited discount. It checks Strand's Billing Policy (Section 3.1: Autopay Terms) and identifies that autopay enrollment is required for this offer but is not mentioned in the email preview text.

The Gate evaluates the Autopay Disclosure Rule:

```
"RULE_AUTOPAY_DISCLOSURE_REQUIRED": {
  "trigger": "promotional price conditional on autopay enrollment",
  "requirement": "autopay terms disclosed before customer confirms purchase; minimum 12pt font for digital materials; plain language explanation of cancellation process and billing date",
  "action": "PASS if disclosure appears in funnel step 1 (landing page or email body); FAIL if disclosure delayed to step 3+ (checkout) or omitted"
}
```

The agent detects the disclosure appears only in the checkout page (step 3), not in the email body or landing page (step 1). The Gate returns FAIL.

**Expected Outcome**

The campaign is blocked with a remediation checklist. The team adds autopay disclosure to the email body ("Automatic monthly billing. Cancel anytime.") and updates the landing page to include a link to Strand's cancellation policy (https://strand.example.com/billing/autopay-manage). The Gate re-evaluates and returns PASS. The team deploys the campaign. A compliance record is filed showing the disclosure location, font size (14pt), and the exact text version approved. The internal benchmark data (Strand's prior 3-month email performance: 2.8% opt-out rate post-disclosure) indicates expected customer cancellation rates and allows the business team to plan retention resources.

**Failure Mode Without BrandGuard**

The campaign launches without autopay disclosure in step 1. Customers enroll at high rates (6.2 million enrollments vs. projected 4.8 million). Billing complaints spike 340% in week 2. The FCC receives 1,200+ complaints citing "hidden autopay terms." Strand issues a public correction and offers 30-day refunds to all affected customers, costing $3.4 million in direct refunds plus reputational damage. Legal liability opens around unfair or deceptive practices under the Telephone Consumer Protection Act.

---

## Use Case 3: Unlimited Data Claim with Deprioritization Caveat (Business SKU)

**Trigger Event**

A business unit launches a campaign claiming "Unlimited data, no throttling" for the Unlimited+ plan in corporate segments. The claim appears in sales decks, proposal templates, and account manager talking points.

**Workflow**

BrandGuard's Scope Agent identifies that "unlimited data" claims with no caveat violate Strand's Service Agreement deprioritization policy. The agent queries Strand's Service Agreement (Section 4.2: Network Management Practices, publicly available at https://strand.example.com/legal/service-agreement) which states:

```
"During periods of network congestion, customers on Unlimited+ plans may experience 
reduced data speeds if total usage exceeds 100 GB per billing cycle."
```

The Disclosure Rule is evaluated:

```
"RULE_UNLIMITED_DISCLOSURE_REQUIRED": {
  "trigger": "any claim of unlimited data or no throttling",
  "requirement": "deprioritization policy disclosed in same communication channel with equal prominence; deprioritization threshold (100 GB/month) and speed impact (typical reduction 40-60% under congestion) stated in plain language",
  "action": "PASS if deprioritization disclosed before or contemporaneous with unlimited claim; FAIL if claim published without caveat or caveat appears only in footnotes/legal text"
}
```

The Business SKU agent scans the sales decks and identifies the unlimited claim in 47 slides without corresponding deprioritization language. The Gate returns FAIL.

**Expected Outcome**

The business team receives a remediation package with revised slide templates. Each unlimited data claim is paired with language: "Unlimited data on Unlimited+ plans. Note: if usage exceeds 100 GB/month, speeds may reduce during network congestion." A link to https://strand.example.com/legal/service-agreement#section-4-2 is added to all materials for customer verification. The updated decks pass BrandGuard review and are distributed to 230 account managers. An internal training module (8 minutes) is assigned to sales staff covering the deprioritization policy and common customer questions. Compliance tracking shows 94% completion within 2 weeks.

**Failure Mode Without BrandGuard**

Sales teams deploy the original decks claiming "unlimited, no throttling" without caveat. Customers purchase Unlimited+ plans based on this claim. After 6 weeks, a subset of heavy users (average 140 GB/month) experience speed reductions and file complaints. Strand receives 890 customer complaints and 3 state attorney general inquiries citing deceptive advertising. The company is forced to issue refunds ($1.8 million), update all sales materials, retrain sales staff, and file a corrective advertising notice with the FCC. The reputation damage affects customer acquisition in the affected states for 9 months.

---

## Use Case 4: Holiday Promotion with Limited Availability (Pro SKU)

**Trigger Event**

A marketing team plans a holiday campaign offering a free premium device (value $199) with activation on a 24-month contract in select markets. The promotion is real: Strand has 8,400 devices budgeted for 6 markets. The team wants to advertise "Limited time, while supplies last" and estimate campaign reach at 2.1 million customers.

**Workflow**

The team uploads the campaign creative to BrandGuard Pro. The Truthfulness Agent cross-references the claim "Limited time, while supplies last" against Strand's promotional inventory database. The agent identifies:

- Available devices: 8,400 units
- Historical conversion rate for device offers: 3.2%
- Expected activations from 2.1 million reach: 67,200 units
- Supply shortfall: 58,800 units

The Disclosure Rule is evaluated:

```
"RULE_AVAILABILITY_DISCLOSURE_REQUIRED": {
  "trigger": "limited availability or while-supplies-last language",
  "requirement": "if claim is based on actual supply limit, disclose the limit in the same message (e.g., '5,000 devices available') or link to real-time inventory; if expected redemption exceeds supply by >10%, flag as misleading terms",
  "action": "PASS if actual supply matches reasonable consumer demand; FAIL if supply is vastly insufficient or limit is artificial"
}
```

The Gate identifies a 686% mismatch between available units and expected demand. It returns FAIL and flags the claim as "misleading terms."

**Expected Outcome**

The campaign is blocked. The team has three options: (a) reduce the reach estimate to match 8,400 devices divided by 3.2% conversion, yielding a realistic reach of 262,500 customers, (b) increase the device budget to 70,000 units, or (c) change the offer from "free device" to "device discount" (e.g., "$49 instead of $199"). The team chooses option (a), reduces paid media spend by 87%, and reprises the campaign with claim "Free $199 device with activation (limited to 8,400 units in select markets; inventory tracked in real time at strand.example.com/holiday)." The Gate approves. The campaign runs, device claims are realistic, and 7,891 customers redeem the offer. No complaints about availability or misleading marketing.

**Failure Mode Without BrandGuard**

The original campaign launches without limits disclosed. 2.1 million customers see the free device offer. Redemption attempts hit 67,200 within 4 days, exhausting 8,400 devices by hour 87 of the campaign. Strand's customer service receives 58,800 angry support tickets from customers who were promised a free device but told "out of stock." Social media complaints accumulate 12,000 posts with #StrandScam and #FalseAdvertising. The Better Business Bureau receives 340 complaints. State attorneys general in 2 markets open investigations into misleading advertising. Strand issues a settlement ($2.1 million in device credits) and pulls the campaign. The reputational damage suppresses customer acquisition across all segments for 6 months.

---

## Summary

Each use case shows how BrandGuard's agents and gates catch compliance risks before launch:

- **Essentials** focuses on citation verification for factual claims.
- **Pro** adds disclosure automation for conditional offers and time-limited claims.
- **Business** provides organization-wide scope management for sales teams and distributed content.
- **Unlimited+** and **Family** plans are supported through the same rule engines.

Without BrandGuard, marketing teams operate blind to compliance, resulting in regulatory complaints, refund obligations, reputational damage, and lost revenue. With BrandGuard, campaigns are approved in hours with audit trails that satisfy regulators and protect customers.
