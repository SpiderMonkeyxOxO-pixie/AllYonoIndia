"""
Promotes one or more draft BlogPost entries (created by import-new-posts.py)
to published, so they'll be picked up the next time generate-blog-pages.py
runs. This is the "flip the switch" step for the staggered publish schedule.

Usage:
    cd tools
    python promote-post.py yono-rummy-apk-download ind-rummy-apk-download inr-rummy-apk-download
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}


def find_draft(slug):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/blog-posts",
        headers=HEADERS,
        params={"filters[slug][$eq]": slug, "status": "draft"},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def main():
    slugs = sys.argv[1:]
    if not slugs:
        sys.exit("Usage: python promote-post.py <slug> [<slug> ...]")

    for slug in slugs:
        existing = find_draft(slug)
        if not existing:
            print(f"SKIP {slug}: no draft found")
            continue
        resp = requests.put(
            f"{STRAPI_API_URL}/api/blog-posts/{existing['documentId']}?status=published",
            headers=HEADERS,
            json={"data": {}},
        )
        if resp.ok:
            print(f"OK  {slug}: published")
        else:
            print(f"FAIL {slug}: {resp.status_code} {resp.text[:500]}")

    print("\nRemember to run generate-blog-pages.py (or publish.sh) afterward to regenerate static pages.")


if __name__ == "__main__":
    main()
