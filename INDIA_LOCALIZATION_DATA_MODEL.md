# AllYonoIndia.com — India Localization Data Model

**Status:** Phase 1 governance document. Defines the fields AllYonoIndia.com uses to record India-specific facts about listed platforms, and the rules for populating them.

**Built:** Phase 1 (India-Specific YONO Hub alignment), following the Phase 0 legal-content integrity fixes.

---

## 1. Purpose

The Phase 0 audit and the portfolio master spec both found the same root problem: this site could not express India-specific facts (availability, legal status, payment support, KYC, tax treatment) in a structured, honest way — it either said nothing, or occasionally said something unsourced. This document defines the fields that replace that gap, and the rule that governs every one of them:

> **Missing data is UNKNOWN. It is never a negative claim.**

A blank/unknown value must never be displayed or interpreted as "not available," "not legal," "not supported," "no KYC," or "no UPI." It means the fact has not been reviewed yet.

---

## 2. Fields

Each field below is optional on the underlying game record. None are currently populated for any game. The template renders the documented fallback when a field is absent — this is intentional and correct, not a bug to "fix" by inventing values.

### `india_availability_status`
- **Allowed values:** `confirmed`, `limited`, `not_confirmed`, `unknown`
- **Meaning:** Whether this specific platform's accessibility/availability for users in India has been independently checked.
- **Evidence required:** A first-hand check of the platform's own stated service area, or a specific sourced official statement.
- **Public display:** Yes, label only — never rendered as true/false.
- **Fallback:** `unknown`
- **Legal/financial review required:** No, but must always appear next to the standard non-legal-advice note (this field is an access/operational observation, not a legal conclusion).

### `legal_review_status`
- **Allowed values:** `verified`, `unverified`, `requires_legal_review`, `unknown`
- **Meaning:** Whether this platform's legal status under Indian law has been reviewed against a named, citable source.
- **Evidence required:** Citation to a specific statute/rule/official notice, plus a review date.
- **Public display:** Yes, always paired with a link to the Disclaimer and the site's legal explainer.
- **Fallback:** `unknown`
- **Legal review required:** Yes — this field *is* the legal-review flag.

### `state_restriction_status`
- **Allowed values:** `known_restricted`, `known_unrestricted`, `mixed_unclear`, `unknown`
- **Meaning:** Whether state-level restriction data for this platform has actually been sourced.
- **Evidence required:** A named state + a citable government/regulatory source + a date. A value other than `unknown` must never be published without its source field populated.
- **Public display:** Yes, only alongside the source citation.
- **Fallback:** `unknown`
- **Legal review required:** Yes.

### `upi_support_status`
- **Allowed values:** `confirmed`, `not_confirmed`, `unknown`
- **Meaning:** Whether UPI as a payment method has been directly observed on this specific platform (not inferred from similar apps).
- **Evidence required:** Direct, dated observation of the platform's own payment page.
- **Public display:** Yes.
- **Fallback:** `unknown`
- **Legal review required:** No.

### `kyc_requirement_status`
- **Allowed values:** `platform_states_required`, `platform_states_not_required`, `unknown`
- **Meaning:** Whether the *platform itself* documents a KYC requirement — never a legal inference from "real-money gaming usually requires KYC."
- **Evidence required:** A direct citation/quote from the platform's own terms or privacy policy.
- **Public display:** Yes, always labeled "platform-stated," never "legally required."
- **Fallback:** `unknown`
- **Legal review required:** No, but must not be conflated with a legal KYC obligation.

### `tax_tds_status`
- **Allowed values (Phase 1):** `not_yet_reviewed`, `requires_financial_legal_review`
- **Meaning:** Whether tax/TDS/GST treatment of winnings on this platform has been reviewed.
- **Evidence required:** An authoritative tax-authority source and a qualified review — not yet performed for any platform.
- **Public display:** Phase 1 only displays the "not yet reviewed" state. Do not populate a specific tax claim without completing that review.
- **Fallback:** `not_yet_reviewed`
- **Legal/financial review required:** Yes.

### Evidence fields (optional, free text — render only if present)
`availability_source`, `legal_source`, `state_restriction_source`, `upi_source`, `kyc_source`, and the matching `*_reviewed_at` timestamps. None are auto-generated. A timestamp is only ever set when a human actually performs the review it describes — never defaulted to "today."

---

## 3. Rendering rule

The template must render the field's label as-is (e.g. "Not Yet Reviewed") — it must never map an absent field to "No," "Not Available," or any other negative-sounding synonym. See `tools/india_status.py`'s `INDIA_STATUS_FIELDS` constant for the canonical label mapping.

## 4. Current population (as of Phase 1)

All 54 currently listed platforms: **every field above is `ABSENT`** in the source data. This is expected — no verification pass has been performed yet. The site currently displays this honestly rather than guessing. Populating real values is Phase 2/3 work requiring an actual review process against the evidence standard each field defines above.
