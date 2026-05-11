---
state: VERIFIED
timestamp: 2026-05-11T22:30:19.004054+00:00
brief: scripts/doc_pipeline/briefs/integration_surface.brief.md
mode: encoded
plugin_command: 
framework: 
word_count_floor: 600
---

# INTEGRATION SURFACE

BrandGuard AI operates at the entry point of marketing technology stacks, accepting audience definitions from existing platforms and returning brand-aligned copy with full compliance tracking. Each integration point enforces the same governance model: BrandGuard consumes structured audience data, generates copy with approval gates, and produces audit-traceable outputs that require human review before publication. No integration bypasses human-in-the-loop approval.

## Salesforce Marketing Cloud

BrandGuard AI ingests audience definitions directly from Salesforce Marketing Cloud Data Extensions. A data extension specifies subscriber attributes (name, location, purchase history, engagement tier) in tabular format, and BrandGuard reads this input to understand segment composition and behavioral context. The platform generates personalized email copy, subject lines, and dynamic content blocks tailored to the audience profile. Output includes the generated copy, inline citations linking each message section to brand guidelines or campaign objectives, and a WORM (Write Once, Read Many) trace ID that logs timestamp, source data extension, model version, and approval chain. Integration boundary: BrandGuard does not publish directly to Salesforce journeys. Marketing operations teams export BrandGuard output, review copy against brand voice and campaign intent, and manually push approved messages into Journey Builder or Email Studio. This manual handoff preserves accountability and prevents accidental publication of off-brand content.

## Marketo

BrandGuard AI consumes Marketo Smart Lists as audience inputs, reading list membership criteria (engagement score above 50, industry equals "telecommunications," clicked email in last 30 days) and list size metadata. The platform generates email program copy, nurture sequence variations, and call-to-action language optimized for the Smart List segment. Copy is returned with embedded citations (referencing specific Marketo lead scoring logic or campaign assumptions), WORM trace ID, and brand-compliance flags. Integration boundary: BrandGuard output is staged in a shared workspace or via API callback, never auto-synced to Marketo Email Programs. Marketers review generated copy, validate tone consistency with Strand Wireless voice guidelines, and choose to accept, reject, or request revision before importing into the program template. Marketo workflows remain user-controlled; BrandGuard accelerates copy creation but does not trigger sends.

## Adobe Campaign

BrandGuard AI accepts segment definitions from Adobe Campaign, including audience rule logic (age 25-45, geography = US Southeast, subscriber for >6 months), segment size, and campaign context (promotional, educational, retention). The platform outputs personalized message copy, subject lines, preview text, and dynamic content rules for segment variation. Each output includes citations to campaign briefs, segment assumptions, or brand guidelines; a WORM trace ID; and a compliance summary indicating whether copy adheres to Strand Wireless tone, factual accuracy standards, and regulatory requirements [file:data/brand_voice.md]. Integration boundary: Adobe Campaign segments are not auto-populated with BrandGuard copy. Instead, copy is reviewed by the campaign manager or brand team in a dedicated approval interface, cross-checked against segment intent, and manually inserted into Adobe Campaign drafts before submission to stakeholder sign-off or send.

## Iterable

BrandGuard AI integrates with Iterable by accepting user list metadata and campaign template requirements as inputs. Iterable provides audience size, channel (email, push, SMS), customer attribute schema, and template variable names (e.g., {{first_name}}, {{product_recommendation}}). BrandGuard generates copy that respects Iterable's template syntax, populates dynamic blocks, and respects personalization tokens. Output is returned with WORM trace ID, citations to relevant Iterable campaign brief or audience definition, and brand-compliance checkmarks. Integration boundary: BrandGuard does not write directly to Iterable templates or trigger broadcasts. Generated copy is staged in a review dashboard, approved by the Iterable campaign owner, and manually pasted or API-merged into Iterable template drafts. Sends remain under Iterable user control; no automatic scheduling or publishing occurs without explicit campaign approval.

## Governance Across All Entry Points

Every integration enforces the same principle: BrandGuard AI is a generative tool that accelerates copy creation and ensures compliance at the point of generation, but human judgment decides what reaches customers. WORM trace IDs create an immutable record of what BrandGuard generated, when, for which audience, and with which brand guardrails applied. Approval workflows stay manual, preserving team accountability and allowing rapid rejection of content that misaligns with campaign goals or brand values, even if copy passes automated compliance checks.
