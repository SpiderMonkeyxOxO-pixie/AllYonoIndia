"""
Bulk-imports newly drafted blog posts (SEO keyword-accumulation batch, 2026-07)
into Strapi's `BlogPost` collection as DRAFTS ONLY (no ?status=published),
so nothing becomes visible on the live site until explicitly promoted later
via promote-post.py.

Data lives in new-posts-data.py (NEW_POSTS list) — one dict per post,
matching the same fields as import-blog-posts.py's parsed output.

Usage:
    cd tools
    python import-new-posts.py            # imports every post in NEW_POSTS
    python import-new-posts.py joy-rummy-apk-download   # import a single slug
"""
import os
import sys

import requests
from dotenv import load_dotenv

from new_posts_data import NEW_POSTS

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}


def find_existing(slug):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/blog-posts",
        headers=HEADERS,
        params={"filters[slug][$eq]": slug, "status": "draft"},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def main():
    only_slug = sys.argv[1] if len(sys.argv) > 1 else None
    posts = [p for p in NEW_POSTS if only_slug is None or p["slug"] == only_slug]
    if not posts:
        sys.exit(f"No matching post found for slug '{only_slug}'." if only_slug else "NEW_POSTS is empty.")

    created, updated, failed = 0, 0, 0
    for post in posts:
        slug = post["slug"]
        payload = {"data": post}

        existing = find_existing(slug)
        # No ?status=published here — leaves the entry as an unpublished draft.
        if existing:
            resp = requests.put(
                f"{STRAPI_API_URL}/api/blog-posts/{existing['documentId']}",
                headers=HEADERS,
                json=payload,
            )
            action = "updated (draft)"
        else:
            resp = requests.post(
                f"{STRAPI_API_URL}/api/blog-posts",
                headers=HEADERS,
                json=payload,
            )
            action = "created (draft)"

        if resp.ok:
            print(f"OK  {slug}: {action}")
            if existing:
                updated += 1
            else:
                created += 1
        else:
            print(f"FAIL {slug}: {resp.status_code} {resp.text[:500]}")
            failed += 1

    print(f"\nDone. Created {created}, updated {updated}, failed {failed}.")


if __name__ == "__main__":
    main()
