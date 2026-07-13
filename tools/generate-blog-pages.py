"""
Regenerates blog/<slug>/index.html for every published BlogPost in Strapi.
Mirrors generate-game-pages.py's pattern: Strapi is the source of truth,
this script just re-renders the same static HTML structure your blog posts
already use (so SEO/schema/canonical tags are unaffected).

Usage:
    cd tools
    pip install -r requirements.txt
    cp .env.example .env   # then fill in STRAPI_API_URL / STRAPI_API_TOKEN
    python generate-blog-pages.py
"""
import html
import json
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")
ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
LISTING_PAGE = os.path.join(ROOT, "blog", "index.html")

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {"Authorization": f"Bearer {STRAPI_API_TOKEN}"}

HEADER = '''<header class="site-header">
  <div class="container">
    <a href="/" class="logo"><img src="/assets/icons/logo.webp" alt="All Yono India logo" width="34" height="34" class="logo-mark-img" loading="eager">All Yono <span class="logo-india">India</span></a>
    <nav class="main-nav" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/all-yono-games/">All Yono Games</a>
      <a href="/promo-code/">Promo Code</a>
      <a href="/blog/" class="is-active">Blog</a>
    </nav>
    <div class="header-actions">
      <a href="/all-yono-games/" class="btn btn-primary btn-sm">View Games</a>
      <button class="hamburger" aria-expanded="false" aria-controls="mobileNav" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
  <nav id="mobileNav" class="mobile-nav" aria-label="Mobile">
    <a href="/">Home</a>
    <a href="/all-yono-games/">All Yono Games</a>
    <a href="/promo-code/">Promo Code</a>
    <a href="/blog/">Blog</a>
  </nav>
</header>'''

FOOTER = '''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="/" class="logo"><img src="/assets/icons/logo.webp" alt="All Yono India logo" width="34" height="34" class="logo-mark-img" loading="eager">All Yono <span class="logo-india">India</span></a>
        <p>A mobile-first directory for All Yono game downloads, APK access, and promo code status, made for Indian users.</p>
        <a href="https://t.me/AllYonogameIndia" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" style="margin-top:14px;display:inline-flex;align-items:center;gap:8px;width:auto">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 3 3 10.5l7 2.5 2 7L21 3Z" stroke-linecap="round" stroke-linejoin="round"/><path d="M10.5 13 21 3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Join Telegram Channel
        </a>
      </div>
      <div class="footer-col">
        <h3>Main Pages</h3>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/all-yono-games/">All Yono Games</a></li>
          <li><a href="/promo-code/">Promo Code</a></li>
          <li><a href="/blog/">Blog</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Game Access</h3>
        <ul>
          <li><a href="/all-yono-games/">Download URLs</a></li>
          <li><a href="/all-yono-games/rummy/">All Yono Rummy Games</a></li>
          <li><a href="/all-yono-games/arcade/">All Yono Arcade Games</a></li>
          <li><a href="/blog/all-yono-games-list/">All Yono Games List 2026</a></li>
          <li><a href="/blog/">Access Notes</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>Important Notes</h3>
        <ul>
          <li><a href="/contact/">Contact</a></li>
          <li><a href="/disclaimer/">Disclaimer</a></li>
          <li><a href="/privacy-policy/">Privacy Policy</a></li>
          <li><a href="/terms/">Terms</a></li>
        </ul>
      </div>
    </div>
    <p class="footer-note">All Yono India does not collect OTPs, passwords, payment details, IDs, screenshots, or private account information through this website.</p>
    <div class="footer-bottom">
      <span>&copy; 2026 All Yono India. All rights reserved.</span>
      <span>Made for Indian mobile game users.</span>
    </div>
  </div>
</footer>

<nav class="bottom-nav" aria-label="Mobile quick navigation">
  <a href="/all-yono-games/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 7h10l2 4-1 7-3-2H9l-3 2-1-7 2-4Z"/></svg>Games</a>
  <a href="/promo-code/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 4h14v16l-7-4-7 4V4Z"/></svg>Codes</a>
  <a href="/blog/" class="is-active"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5h16M4 12h16M4 19h10"/></svg>Blog</a>
  <a href="#top"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 19V5M5 12l7-7 7 7"/></svg>Top</a>
</nav>

<script src="/assets/js/main.min.js"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VGXGPH0EFT"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag("js", new Date());

  gtag("config", "G-VGXGPH0EFT");
</script>
<script src="https://analytics.ahrefs.com/analytics.js" data-key="F2Upk514gOfWdTFQ86ltnw" async></script>
</body>
</html>
'''

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def date_human(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def fetch_posts():
    posts = []
    page = 1
    while True:
        resp = requests.get(
            f"{STRAPI_API_URL}/api/blog-posts",
            headers=HEADERS,
            params={
                "pagination[page]": page,
                "pagination[pageSize]": 100,
                "populate": "faqs",
                "status": "published",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        posts.extend(body["data"])
        if page >= body["meta"]["pagination"]["pageCount"]:
            break
        page += 1
    return posts


def build_post(post):
    slug = post["slug"]
    title = post["title"]
    meta_title = post["meta_title"]
    meta_desc = post["meta_description"]
    keywords = post.get("keywords") or ""
    eyebrow = post["eyebrow"]
    date = post["published_date"]
    canonical = f"https://allyonoindia.com/blog/{slug}/"
    img = f"https://allyonoindia.com{post['cover_image']}"
    image_alt = post.get("image_alt") or title
    breadcrumb_label = post.get("breadcrumb_label") or title
    faqs = [(f["question"], f["answer"]) for f in post.get("faqs", [])]

    # q/a are stored HTML-escaped and may contain a deliberate inline <a> link (see
    # import-blog-posts.py). schema.org's FAQPage expects plain text, not escaped entities
    # or markup, so strip tags and unescape entities for the JSON-LD copy specifically.
    def plain_text(s):
        return html.unescape(re.sub(r"<[^>]+>", "", s))

    faq_json = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": plain_text(q),
                "acceptedAnswer": {"@type": "Answer", "text": plain_text(a)},
            }
            for q, a in faqs
        ],
    }
    breadcrumb_json = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://allyonoindia.com/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://allyonoindia.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": breadcrumb_label, "item": canonical},
        ],
    }
    article_json = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": meta_desc,
        "image": img,
        "datePublished": date,
        "dateModified": date,
        "author": {"@type": "Organization", "name": "All Yono India", "url": "https://allyonoindia.com/"},
        "publisher": {
            "@type": "Organization",
            "name": "All Yono India",
            "logo": {"@type": "ImageObject", "url": "https://allyonoindia.com/assets/icons/logo.webp"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }

    # q/a are already escaped (and safe to inject raw) at import time, not here — see
    # import-blog-posts.py. That lets a deliberate <a> link inside a FAQ answer survive.
    faq_html_blocks = []
    for q, a in faqs:
        faq_html_blocks.append(f'''        <details class="faq-item">
          <summary>{q}<svg class="faq-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>
          <p class="faq-answer">{a}</p>
        </details>''')
    faq_html = "\n".join(faq_html_blocks)
    faq_list_html = f'<div class="faq-list">\n{faq_html}\n      </div>'

    # import-blog-posts.py leaves a placeholder where the original FAQ block was (preserving the
    # original heading text and position, since some posts have content after their FAQ section).
    # Posts authored directly in Strapi without ever going through that import won't have the
    # placeholder, so fall back to appending under a generic heading at the end.
    if "<!--FAQS_LIST-->" in post["body_html"]:
        body_with_faqs = post["body_html"].replace("<!--FAQS_LIST-->", faq_list_html)
    else:
        body_with_faqs = f'{post["body_html"]}\n\n      <h2>FAQs</h2>\n      {faq_list_html}'

    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>{meta_title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="article">
<meta property="og:title" content="{meta_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="All Yono India">
<meta property="og:image" content="{img}">
<meta property="article:published_time" content="{date}">
<meta property="article:modified_time" content="{date}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{meta_title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="{img}">

<link rel="icon" href="/assets/icons/favicon.webp" type="image/webp">
<link rel="apple-touch-icon" href="/assets/icons/logo.webp">
<link rel="preconnect" href="https://api.allyonoindia.com">
<link rel="preload" href="/assets/fonts/goldman-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.min.css">

<script type="application/ld+json">
{json.dumps(breadcrumb_json, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(article_json, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(faq_json, indent=2)}
</script>
</head>
<body>

{HEADER}

<main>
  <div class="container" style="max-width:760px">
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a> / <a href="/blog/">Blog</a> / <span aria-current="page">{breadcrumb_label}</span>
    </nav>
    <div class="content-page">
      <span class="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p class="footer-note" style="margin-top:-4px">Last Reviewed: {date_human(date)}</p>

      <img src="{post['cover_image']}" alt="{image_alt}" width="1200" height="675" loading="eager" style="margin:var(--space-4) 0">

{body_with_faqs}
    </div>
  </div>
</main>

{FOOTER}'''


def build_listing_card(post):
    slug = post["slug"]
    title = post["title"]
    eyebrow = post["eyebrow"]
    image_alt = post.get("image_alt") or title
    # excerpt is the hand-written card teaser (distinct from meta_description, which is
    # written for search-result snippets) — falls back to meta_description for any post
    # that hasn't had excerpt filled in yet, so a freshly published post never shows blank.
    teaser = post.get("excerpt") or post["meta_description"]
    # The hidden screen-reader-only suffix on "Read the full post" was hand-written per
    # post before this generator existed (e.g. "about spotting fake All Yono apps"), with
    # no dedicated field for it. Auto-generating it from the title is an intentional, low-
    # stakes simplification — it's supplementary accessibility text, not visible content.
    about_text = f"about {title}"
    return f'''<a href="/blog/{slug}/" class="blog-card" style="text-decoration:none;grid-column:span 2">
          <img src="{post['cover_image']}" alt="{image_alt}" width="1200" height="675" loading="lazy">
          <span class="tag">{eyebrow}</span>
          <h3>{title}</h3>
          <p>{teaser}</p>
          <span class="read-more">Read the full post <span class="visually-hidden">{about_text}</span></span>
        </a>'''


def regenerate_listing_page(posts):
    html_text = open(LISTING_PAGE, encoding="utf-8").read()
    newest_first = sorted(posts, key=lambda p: p["published_date"], reverse=True)
    cards = "\n        ".join(build_listing_card(p) for p in newest_first)
    new_block = (
        "<!-- BLOG_GRID_START: auto-generated by tools/generate-blog-pages.py, do not hand-edit individual cards below -->\n        "
        + cards
        + "\n        <!-- BLOG_GRID_END -->"
    )
    pattern = re.compile(r"<!-- BLOG_GRID_START.*?BLOG_GRID_END -->", re.DOTALL)
    if not pattern.search(html_text):
        sys.exit("Could not find BLOG_GRID_START/END markers in blog/index.html — aborting.")
    html_text = pattern.sub(new_block, html_text)
    open(LISTING_PAGE, "w", encoding="utf-8").write(html_text)


def main():
    posts = fetch_posts()
    for post in posts:
        out_dir = os.path.join(ROOT, "blog", post["slug"])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_post(post))
    regenerate_listing_page(posts)
    print(f"Generated {len(posts)} blog pages and regenerated the listing page grid.")


if __name__ == "__main__":
    main()
