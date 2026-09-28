"""Staged posts published one per day by publish-scheduled-posts.py.

Each post's full page lives in tools/scheduled/<slug>/index.html (not web-served) with
{{DATE_ISO}} / {{DATE_HUMAN}} placeholders. On its published_date the publisher renders it
into blog/<slug>/, unlinks references to staged posts that are not live yet, and lists it.
Add a post: put its page in tools/scheduled/<slug>/ and append an entry below."""

SCHEDULED_POSTS = [
    {
        "slug": "yono-games-available-in-india-meaning",
        "published_date": "2026-09-29",
        "title": "What Does \"Available in India\" Actually Mean for a Yono Game App?",
        "eyebrow": "India Status",
        "excerpt": "\"Available in India\" is not the same as \"the link opens\". The four checks behind an India availability status, and what it does not tell you.",
        "image_alt": "Checklist graphic explaining what available in India means for a Yono game app",
        "cover_image": "/assets/images/blog/yono-games-available-in-india-meaning.webp"
    },
    {
        "slug": "india-availability-vs-legal-status",
        "published_date": "2026-09-30",
        "title": "India Availability vs Legal Status: Why They Are Not the Same",
        "eyebrow": "Legal Information",
        "excerpt": "A Yono game app can be reachable in India and still be prohibited. How availability differs from legal status under the Online Gaming Act, 2025.",
        "image_alt": "Two separate status boxes for India availability and legal status",
        "cover_image": "/assets/images/blog/india-availability-vs-legal-status.webp"
    },
    {
        "slug": "confirmed-vs-unverified-vs-not-yet-reviewed",
        "published_date": "2026-10-01",
        "title": "Confirmed vs Unverified vs Not Yet Reviewed: What Each Status Means",
        "eyebrow": "India Status",
        "excerpt": "How to read the India-Specific Status panel on a game page: what each label means, what moves it, and worked examples.",
        "image_alt": "Status label chart showing Confirmed, Unverified and Not Yet Reviewed",
        "cover_image": "/assets/images/blog/confirmed-vs-unverified-vs-not-yet-reviewed.webp"
    },
    {
        "slug": "download-link-not-proof-of-india-availability",
        "published_date": "2026-10-02",
        "title": "Why a Working Download Link Does Not Prove a Yono App Is Available in India",
        "eyebrow": "India Status",
        "excerpt": "A download link that opens proves only that a file is online today. Why links rotate, what they cannot tell you, and what to check instead.",
        "image_alt": "Graphic showing a download link next to a question mark about India availability",
        "cover_image": "/assets/images/blog/download-link-not-proof-of-india-availability.webp"
    },
    {
        "slug": "yono-games-kyc-requirement-proof",
        "published_date": "2026-10-03",
        "title": "What Counts as Proof That a Yono Game Requires KYC?",
        "eyebrow": "Account Safety",
        "excerpt": "The evidence that shows an app really requires KYC, the difference between 'KYC required' and 'KYC mentioned', and fake-KYC scams to avoid.",
        "image_alt": "Graphic about KYC evidence for Yono game apps with a document and shield icon",
        "cover_image": "/assets/images/blog/yono-games-kyc-requirement-proof.webp"
    },
    {
        "slug": "yono-games-upi-support-proof",
        "published_date": "2026-10-04",
        "title": "What Counts as Proof That a Yono Game Supports UPI?",
        "eyebrow": "Payments",
        "excerpt": "Most 'UPI supported' claims are marketing. The evidence ladder we use, why a screenshot is weak proof, and what the 2025 Act says about payments.",
        "image_alt": "Evidence ladder graphic for UPI support claims on Yono game apps",
        "cover_image": "/assets/images/blog/yono-games-upi-support-proof.webp"
    }
]
