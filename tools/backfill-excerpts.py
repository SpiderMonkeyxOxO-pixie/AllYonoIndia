"""
One-time backfill: sets the new `excerpt` field on the 6 original blog posts to their
existing hand-written listing-card teaser text (captured from blog/index.html before the
listing page became auto-generated). New posts published after this should have excerpt
filled in directly in the Strapi admin UI — if left blank, the generator falls back to
meta_description, so nothing breaks either way.

Usage:
    cd tools
    python backfill-excerpts.py
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}

EXCERPTS = {
    "all-yono-app-permissions-explained": (
        "Which All Yono app permissions are typical, which are warning signs, and the "
        "settings to review before granting access on your Android device."
    ),
    "all-yono-games-list": (
        "An organised overview of rummy, slots, arcade, casual, and card game categories "
        "— plus how to use the live directory safely."
    ),
    "all-yono-login-explained": (
        "This website has no login form. Here's where account access actually happens "
        "and why we never ask for your password or OTP."
    ),
    "how-all-yono-promo-codes-work": (
        'Promo codes are checked and updated three times a day. Here\'s what "Checking" '
        'and "Waiting to Release" actually mean.'
    ),
    "spot-fake-all-yono-app-scam": (
        "Fake clones and phishing links can look convincing. Learn the warning signs, how "
        "to check the current listed link, and what to do after a suspicious download."
    ),
    "is-online-rummy-legal-in-india": (
        "India's national framework now focuses on money and stakes, not just the "
        "skill-vs-chance label. Here's what changed and what it means for online rummy."
    ),
}


def find_existing(slug):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/blog-posts",
        headers=HEADERS,
        params={"filters[slug][$eq]": slug, "publicationState": "preview"},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def main():
    updated = 0
    for slug, excerpt in EXCERPTS.items():
        post = find_existing(slug)
        if not post:
            print(f"SKIPPED {slug}: not found")
            continue
        resp = requests.put(
            f"{STRAPI_API_URL}/api/blog-posts/{post['documentId']}?status=published",
            headers=HEADERS,
            json={"data": {"excerpt": excerpt}},
        )
        if not resp.ok:
            print(f"FAILED on {slug}: {resp.status_code} {resp.text}")
            resp.raise_for_status()
        updated += 1
    print(f"Done. Updated {updated} of {len(EXCERPTS)} posts.")


if __name__ == "__main__":
    main()
