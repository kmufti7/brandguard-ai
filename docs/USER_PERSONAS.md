---
state: VERIFIED
timestamp: 2026-05-11T22:25:55.973513+00:00
brief: scripts/doc_pipeline/briefs/user_personas.brief.md
mode: encoded
plugin_command: 
framework: jtbd
word_count_floor: 800
---

# USER PERSONAS

## Persona 1: Marketing Operations Manager

**Name:** Sarah Chen

**Role:** Director of Marketing Operations

**Company Context:** Series B SaaS (65 employees), $8M ARR, B2B marketing automation platform

**Job Statement:** When I launch a multi-channel campaign across email, SMS, and push notifications using Marketo and Salesforce Marketing Cloud, I want to ensure every message aligns with our brand guidelines and complies with regulations, so I can ship campaigns 40% faster without legal review delays or brand inconsistency.

**Day in the Life:**

Sarah starts work at 8:30 AM reviewing overnight Slack notifications from her campaign team. By 9:00 AM, she opens Marketo to audit three new email sequences (15 minutes). She pastes campaign copy into a shared Google Doc where five team members have already flagged tone concerns. At 10:00 AM, she switches to Salesforce Marketing Cloud to check SMS templates bound for 50,000 subscribers. A junior marketer had written two messages using casual language inconsistent with Strand Wireless voice guidelines.

By 10:45 AM, Sarah manually rewrites both SMS messages using her brand style guide (stored as a PDF in Box). She spends 20 minutes cross-referencing compliance requirements with Legal (Slack DM thread). At 12:00 PM, she exports the revised campaign to Iterable for push notification sequencing and manually spot-checks tone and offer clarity for 10 minutes.

At 2:00 PM, Sarah attends a planning meeting where the campaign manager requests approval to launch by 4:00 PM. Sarah asks for copy edits. At 3:15 PM, she receives revised copy and conducts a final 25-minute audit across all three channels. She flags one more brand voice violation in the subject line. At 4:00 PM, the campaign ships 30 minutes late.

By end of day, Sarah has spent 90 minutes on brand and compliance review across three tools, with three back-and-forth cycles. She documents decisions in Asana for historical record (10 minutes).

**Hiring Criteria (What Sarah Looks For in Solutions):**

1. Instant feedback on brand alignment without manual copy-pasting between systems
2. Integration with Marketo, Salesforce Marketing Cloud, and Iterable (not a standalone tool requiring exports)
3. Compliance flagging tied to specific regulations (TCPA for SMS, CAN-SPAM for email)
4. Approval workflow that reduces Legal handoff time from 20 minutes to under 5 minutes
5. Audit trail that documents why copy was flagged and what was changed
6. Speed of feedback: under 60 seconds per campaign asset
7. Confidence that AI recommendations won't override brand voice, only reinforce it

**Fear: Loss of Control and Brand Drift**

Sarah fears that an AI tool will either (a) approve messages that subtly violate Strand Wireless voice guidelines because the AI learned from outdated brand references, or (b) reject legitimate creative variations that actually strengthen brand connection with specific audience segments. She worries that outsourcing brand judgment to AI will create organizational muscle memory where no one remembers why certain tone choices matter. She also fears that tool recommendations will become "black box" decisions her team blindly follows, eroding internal expertise.

BrandGuard addresses this through explicit brand voice configuration [file:data/brand_voice.md] that Sarah controls directly. Feedback includes a human-readable explanation of which voice attribute triggered a flag (e.g., "Tone: Detected overly formal language; Strand Wireless voice uses accessible, conversational phrasing"). Sarah can override any flag with a single click and that decision trains future audits for her account. The tool tracks what Strand Wireless copy was approved vs. rejected, surfacing patterns Sarah can review monthly in a voice consistency dashboard.

BrandGuard fails to address if: The tool makes recommendations without showing source evidence (which brand guideline was cited), or if flagging becomes so aggressive that Sarah disables the tool to ship faster.

---

## Persona 2: Brand Manager

**Name:** Marcus Thompson

**Role:** Senior Brand Manager

**Company Context:** Mid-market B2C (180 employees), Series C telecom company, $40M ARR

**Job Statement:** When our 12 regional marketing teams and agency partners create local campaign variations in HubSpot, Adobe Campaign, and social media platforms, I want to ensure every variation preserves core brand identity while respecting regional preferences, so I can maintain brand consistency across 15 different markets without reviewing 300 individual assets per quarter.

**Day in the Life:**

Marcus begins his day at 9:00 AM in a weekly brand sync meeting with agency leads. Two regional managers request approval for localized email campaigns targeting different customer segments. One campaign uses colloquial regional language; Marcus must decide if it aligns with Strand Wireless or deviates too far.

At 10:30 AM, Marcus opens HubSpot and reviews 18 email templates queued for launch. He downloads four PDFs of campaign visuals and opens them in Figma to check logo sizing, color palette accuracy, and typography (40 minutes). He takes notes on three templates that use off-brand colors.

By 11:45 AM, Marcus creates a feedback document in Google Docs, typing corrections for each team. At 1:00 PM, he attends a call with the West Coast team to discuss why their messaging tone doesn't match the Strand Wireless voice profile he distributed last month. The call runs 35 minutes.

At 2:30 PM, Marcus opens Adobe Campaign to spot-check dynamic content in three email flows targeting different customer segments. One flow uses language Marcus considers too casual; one is too formal. He flags both for revision.

By 4:00 PM, Marcus has reviewed 12 assets and sent revision requests to four different owners. He estimates 6 days before all teams resubmit revised copy. He updates a tracking spreadsheet (15 minutes).

By end of day, Marcus has spent 3.5 hours reviewing and communicating about 18 assets, with actual review time around 2 hours and 20 minutes communication overhead.

**Hiring Criteria (What Marcus Looks For in Solutions):**

1. Multi-team access with role-based permissions so regional teams can self-service review without waiting for Marcus
2. Integration with HubSpot and Adobe Campaign (where templates actually live)
3. Visual asset checking, not just copy (logo placement, color accuracy, typography)
4. Bulk review capability for 25+ assets per week
5. Clear pass/fail feedback with correctable flags, not vague suggestions
6. Feedback delivered in under 90 seconds per asset
7. Regional variation support: ability to set different rules for different markets while maintaining global baseline
8. Reporting on consistency metrics (what percentage of West Coast campaigns met brand standards this month?)

**Fear: Brand Dilution and Market Confusion**

Marcus fears that empowering teams to self-serve brand review with AI will result in "brand creep," where each region stretches guidelines incrementally until 12 different brand identities exist under one corporate name. He worries customers will encounter Strand Wireless as a disjointed experience rather than a coherent brand. He also fears that an AI tool will either be so permissive it approves off-brand work, or so restrictive it becomes an obstacle that teams work around (ignoring the tool entirely and shipping unapproved work).

BrandGuard addresses this by establishing a configurable brand baseline that Marcus defines once [file:data/brand_voice.md], then allowing regional rule sets that dial permitted variation up or down per region. The tool flags deviations with specific explanations tied to the baseline rule. Marcus receives weekly reporting on how many campaigns passed/failed per region and what types of violations are most common. This creates accountability without micromanagement.

BrandGuard fails to address if: The tool cannot accommodate legitimate regional variations and becomes so rigid that teams disable it or work around it. Or if reporting is vague (e.g., "12 assets failed") without breakdown of what failed and why.

---

## Persona 3: Email Copywriter

**Name:** Jasmine Patel

**Role:** Senior Email Copywriter

**Company Context:** Enterprise B2B SaaS (420 employees), publicly traded, $250M revenue

**Job Statement:** When I write promotional and transactional email copy for Strand Wireless campaigns reaching 2 million subscribers across 8 customer segments, I want real-time feedback on whether my copy matches brand voice, complies with regulations, and achieves performance targets, so I can reduce revision cycles from 4 days to 1 day and increase email open rates by 15%.

**Day in the Life:**

Jasmine arrives at 8:30 AM and opens her shared draft folder in Google Docs where three new email campaigns await her attention. She has written two welcome series emails and is waiting for feedback on tone before proceeding to a third email.

By 9:00 AM, she opens Iterable (where emails are deployed) and reviews performance data on last week's promotional campaign. Open rate was 22%, click rate was 3.8%. Jasmine notes that the subject line was formal. She hypothesizes that a more conversational subject line could lift opens by 2 percentage points.

At 10:00 AM, Jasmine writes a new subject line variant in her Google Doc and reads it aloud to catch rhythm and cadence issues (5 minutes). She checks the Strand Wireless brand voice guide PDF for examples of conversational subject lines used in past campaigns (10 minutes). By 10:20 AM, she has finalized copy for three new emails and is ready for brand review.

Normally, review takes 24 to 48 hours. A brand manager or marketing operations person reads the copy and returns notes via email. Jasmine revises, resubmits, and waits 24 more hours for sign-off. This cycle repeats 2 to 3 times per campaign.

At 11:00 AM, Jasmine attends a performance review meeting where the team discusses why a recent transactional email (password reset) underperformed in click-through rate. The team suspects the copy was too technical and not conversational enough. Jasmine makes a note to adjust tone.

At 2:00 PM, Jasmine writes a new password reset email using simpler, more conversational language. She finalizes copy by 2:45 PM and submits to the brand manager via Slack, knowing she will wait until tomorrow for feedback. She uses this time to outline next week's campaign calendar (30 minutes).

At 4:00 PM, Jasmine receives Slack feedback from the brand manager: the password reset email is too casual and needs to sound more trustworthy. Jasmine spends 20 minutes revising to add more formal language while keeping it conversational. She resubmits at 4:30 PM. By end of day, the campaign still awaits final approval.

By end of week, Jasmine has spent 8 hours writing copy and 6 hours waiting for or responding to review feedback.

**Hiring Criteria (What Jasmine Looks For in Solutions):**

1. Instant feedback on brand voice alignment as she types (inline suggestions, not batch reviews)
2. Performance benchmarking against past campaigns (is this subject line length similar to our best performers?)
3. Regulatory compliance check (GDPR, CAN-SPAM, CASL) integrated into the writing flow
4. Tone adjustment suggestions tied to campaign goals (e.g., "goal is transactional trust, detected overly casual tone")
5. Segment-specific feedback (subject line tone that works for SMB segment may not work for enterprise segment)
6. Integration with Google Docs so feedback appears where she writes
7. Confidence that AI suggestions improve performance, not just enforce rules
8. No forced revisions, only coaching and explanations

**Fear: Loss of Creative Authority and Over-Optimization**

Jasmine fears that a brand compliance tool will prioritize rule-following over genuine creative expression and audience connection. She worries that real-time AI feedback will make her second-guess every word choice and slow her thinking, turning email writing into a compliance task rather than a creative craft. She also fears being blamed if an AI suggestion (that she incorporated) leads to lower performance. She doesn't want a tool that tells her "this violates brand voice" without explaining why or offering creative alternatives that achieve the same brand goal.

BrandGuard addresses this by framing feedback as coaching, not rules. When Jasmine's copy triggers a brand concern, BrandGuard explains the specific voice attribute at issue (e.g., "Strand Wireless uses active voice; your sentence uses passive voice") and offers 2 to 3 alternative phrasings that maintain her intended tone and meaning while aligning with brand voice [file:data/brand_voice.md]. Jasmine always has the final say and can override any flag. The tool learns from her choices and personalizes future feedback to her writing style.

BrandGuard fails to address if: Feedback is vague or prescriptive ("this doesn't sound like Strand Wireless, rewrite it") without concrete alternatives. Or if the tool's suggestions are so generic they strip personality from copy or don't improve performance metrics. Or if Jasmine is held accountable for AI-recommended changes that underperform.
