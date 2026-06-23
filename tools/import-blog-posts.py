"""
One-time migration: parse the 6 existing static blog posts under blog/<slug>/
and import them into Strapi's `BlogPost` collection (with FAQs as the repeatable
blog.faq component, parsed straight from each page's existing FAQPage JSON-LD
block — no fragile re-typing of Q&A pairs needed). Safe to re-run — upserts by slug.

Usage:
    cd tools
    pip install -r requirements.txt
    cp .env.example .env   # then fill in STRAPI_API_URL / STRAPI_API_TOKEN
    python import-blog-posts.py
"""
import html as html_lib
import json
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")
BLOG_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "blog"))

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}

JSONLD_RE = re.compile(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', re.DOTALL)
TITLE_RE = re.compile(r"<title>(.*?)</title>")
DESC_RE = re.compile(r'<meta name="description" content="(.*?)">')
KEYWORDS_RE = re.compile(r'<meta name="keywords" content="(.*?)">')
EYEBROW_RE = re.compile(r'<span class="eyebrow">(.*?)</span>')
H1_RE = re.compile(r"<h1>(.*?)</h1>")
COVER_IMG_RE = re.compile(
    r'<img src="(/assets/images/blog/[^"]+)" alt="(.*?)" width="1200" height="675"'
)
# Body spans from after the cover image to the closing of .content-page (two </div> then </main>).
# Some posts have extra content *after* the FAQ block too, so capture everything in that range
# and separately strip out the FAQ heading+list (FAQs already come from the JSON-LD block instead).
BODY_RE = re.compile(
    r'style="margin:var\(--space-4\) 0">\s*(.*?)\s*</div>\s*</div>\s*</main>',
    re.DOTALL,
)
FAQ_BLOCK_RE = re.compile(r'<h2>([^<]*)</h2>\s*<div class="faq-list">.*?</div>\s*', re.DOTALL)
FAQS_PLACEHOLDER = "<!--FAQS_LIST-->"

# Original FAQ heading text varies per post ("FAQs", "FAQs About the All Yono Games List", etc.),
# and some posts have more body content *after* the FAQ block. Replace the matched block with the
# original heading plus a placeholder, instead of deleting it outright, so generate-blog-pages.py
# can re-insert the FAQ list in its original position and under its original heading.
def strip_faq_block(body):
    def repl(m):
        return f'<h2>{m.group(1)}</h2>\n      {FAQS_PLACEHOLDER}\n'
    return FAQ_BLOCK_RE.sub(repl, body, count=1)


# The FAQPage JSON-LD block (single source of truth for FAQ text) used curly quotes in some posts,
# while the hand-written visible FAQ HTML used straight quotes for the same content. Normalize to
# straight quotes so the now-shared source stays consistent with the rest of the site's convention.
def normalize_quotes(text):
    return (
        text.replace("“", '"').replace("”", '"')
        .replace("‘", "'").replace("’", "'")
    )


def find_existing(slug):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/blog-posts",
        headers=HEADERS,
        params={"filters[slug][$eq]": slug, "publicationState": "preview"},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def parse_post(slug, html):
    article = None
    breadcrumb_label = None
    faqs = []
    for match in JSONLD_RE.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "Article":
            article = data
        elif data.get("@type") == "BreadcrumbList":
            items = data.get("itemListElement", [])
            if len(items) >= 3:
                breadcrumb_label = items[2]["name"]
        elif data.get("@type") == "FAQPage":
            for q in data.get("mainEntity", []):
                # Escaped here (not at render time) so the stored text is final, safe-to-inject
                # HTML — consistent with how body_html/title etc. are already handled. This also
                # means a deliberate <a> link manually added to a FAQ answer (rare, but happens —
                # see is-online-rummy-legal-in-india) survives untouched if added after import.
                faqs.append({
                    "question": html_lib.escape(normalize_quotes(q["name"]), quote=False),
                    "answer": html_lib.escape(normalize_quotes(q["acceptedAnswer"]["text"]), quote=False),
                })

    title_match = H1_RE.search(html)
    meta_title_match = TITLE_RE.search(html)
    desc_match = DESC_RE.search(html)
    keywords_match = KEYWORDS_RE.search(html)
    eyebrow_match = EYEBROW_RE.search(html)
    cover_match = COVER_IMG_RE.search(html)
    body_match = BODY_RE.search(html)

    if not (title_match and meta_title_match and desc_match and eyebrow_match and cover_match and body_match):
        raise ValueError(f"Could not extract all required fields for {slug}")

    body_html = strip_faq_block(body_match.group(1)).strip()

    title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()

    return {
        "title": title,
        "slug": slug,
        "meta_title": meta_title_match.group(1).strip(),
        "meta_description": desc_match.group(1).strip(),
        "keywords": keywords_match.group(1).strip() if keywords_match else "",
        "eyebrow": eyebrow_match.group(1).strip(),
        "cover_image": cover_match.group(1).strip(),
        "image_alt": cover_match.group(2).strip(),
        "breadcrumb_label": breadcrumb_label or title,
        "body_html": body_html,
        "published_date": article["datePublished"] if article else None,
        "faqs": faqs,
    }


def main():
    slugs = sorted(
        name for name in os.listdir(BLOG_DIR)
        if os.path.isdir(os.path.join(BLOG_DIR, name))
    )

    created, updated = 0, 0
    for slug in slugs:
        path = os.path.join(BLOG_DIR, slug, "index.html")
        if not os.path.exists(path):
            continue
        html = open(path, encoding="utf-8").read()

        try:
            fields = parse_post(slug, html)
        except ValueError as e:
            print(f"SKIPPED {slug}: {e}")
            continue

        payload = {"data": fields}
        # status=published since these are already-live posts, not drafts.
        existing = find_existing(slug)
        if existing:
            resp = requests.put(
                f"{STRAPI_API_URL}/api/blog-posts/{existing['documentId']}?status=published",
                headers=HEADERS,
                json=payload,
            )
            updated += 1
        else:
            resp = requests.post(
                f"{STRAPI_API_URL}/api/blog-posts?status=published", headers=HEADERS, json=payload
            )
            created += 1

        if not resp.ok:
            print(f"FAILED on {slug}: {resp.status_code} {resp.text}")
            resp.raise_for_status()

    print(f"Done. Created {created}, updated {updated}.")


if __name__ == "__main__":
    main()
