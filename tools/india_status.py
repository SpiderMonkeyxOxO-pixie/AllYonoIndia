"""
Shared India-localization field model and renderer. Used by both
generate-static-games.py (for any future new game page) and
apply-india-status-module.py (which applied the identical HTML to the
already-generated static entity pages) — see INDIA_LOCALIZATION_DATA_MODEL.md
at the repo root for full governance: allowed values, evidence required,
legal-review requirement per field.

None of these fields have been populated for any game yet, so every game
currently falls back to its documented "not reviewed" label below.
That is correct, honest behavior — never map an absent field to a
negative claim like "Not Available."
"""

INDIA_STATUS_FIELDS = [
    ("india_availability_status", "Availability in India", {
        "confirmed": "Confirmed", "limited": "Limited", "not_confirmed": "Not Confirmed",
    }),
    ("legal_review_status", "Legal Status", {
        "verified": "Verified", "unverified": "Unverified", "requires_legal_review": "Requires Legal Review",
    }),
    ("state_restriction_status", "State Restrictions", {
        "known_restricted": "Known Restricted (see source)",
        "known_unrestricted": "Known Unrestricted (see source)",
        "mixed_unclear": "Mixed / Unclear",
    }),
    ("upi_support_status", "UPI / Payment Support", {
        "confirmed": "Confirmed", "not_confirmed": "Not Confirmed",
    }),
    ("kyc_requirement_status", "KYC Requirement (platform-stated)", {
        "platform_states_required": "Platform States Required",
        "platform_states_not_required": "Platform States Not Required",
    }),
]
INDIA_STATUS_UNKNOWN_LABEL = "Not Yet Reviewed"
INDIA_STATUS_TAX_LABEL = "Requires Financial/Legal Review"


def india_status_html(g, name):
    """g: dict-like game record (may be empty/missing all India fields — that's expected)."""
    rows = []
    for field, label, value_labels in INDIA_STATUS_FIELDS:
        raw = g.get(field) if hasattr(g, "get") else None
        shown = value_labels.get(raw, INDIA_STATUS_UNKNOWN_LABEL)
        rows.append(f"<li>{label}: <b>{shown}</b></li>")
    rows.append(f"<li>Tax / TDS Treatment: <b>{INDIA_STATUS_TAX_LABEL}</b></li>")
    return f'''
      <div class="callout" style="margin-top:24px">
        <strong style="display:block;margin-bottom:8px;color:var(--white)">India-Specific Status for {name}</strong>
        <ul class="meta-list" style="margin:0 0 8px">
          {"".join(rows)}
        </ul>
        <p style="margin:0;font-size:0.85rem">These fields are not yet independently verified for {name}. Read <a href="/india-guide/" style="color:var(--cyan);font-weight:700">how All Yono India verifies India-specific information</a>.</p>
      </div>
'''
