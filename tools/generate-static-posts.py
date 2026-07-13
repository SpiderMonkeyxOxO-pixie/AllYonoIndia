"""
Generates standalone blog/<slug>/index.html files directly from new_posts_data.py,
with NO Strapi involvement at all — matches the exact template/structure the site
already uses (same HEADER/FOOTER/schema layout as generate-blog-pages.py), but reads
local data instead of the CMS. This is the new manual-posting workflow: edit
new_posts_data.py or the generated HTML directly, then git push when ready.

Does NOT touch blog/index.html (the listing grid) — that's handled separately,
one card at a time, to avoid clobbering any existing entries.

Usage:
    cd tools
    python generate-static-posts.py                    # generates every post except joy-rummy (already live)
    python generate-static-posts.py jaiho-arcade-apk-download ind-club-apk-download   # just specific slugs
"""
import html
import json
import os
import re
import sys

from new_posts_data import NEW_POSTS

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ALREADY_LIVE = {"joy-rummy-apk-download"}  # generated via Strapi earlier, don't touch

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def date_human(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


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


def build_post(post):
    slug = post["slug"]
    title_raw = post["title"]
    meta_title_raw = post["meta_title"]
    meta_desc_raw = post["meta_description"]
    keywords_raw = post.get("keywords") or ""
    eyebrow_raw = post["eyebrow"]
    breadcrumb_label_raw = post.get("breadcrumb_label") or post["title"]
    date = post["published_date"]
    canonical = f"https://allyonoindia.com/blog/{slug}/"
    img = f"https://allyonoindia.com{post['cover_image']}"
    image_alt_raw = post.get("image_alt") or post["title"]
    faqs = [(f["question"], f["answer"]) for f in post.get("faqs", [])]

    # HTML-escaped versions for interpolation into attributes/text content —
    # JSON-LD blocks below use the *_raw versions instead, since json.dumps
    # handles its own escaping and HTML entities would corrupt the JSON.
    title = html.escape(title_raw)
    meta_title = html.escape(meta_title_raw)
    meta_desc = html.escape(meta_desc_raw)
    keywords = html.escape(keywords_raw)
    eyebrow = html.escape(eyebrow_raw)
    breadcrumb_label = html.escape(breadcrumb_label_raw)
    image_alt = html.escape(image_alt_raw)

    def plain_text(s):
        return html.unescape(re.sub(r"<[^>]+>", "", s))

    faq_json = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": plain_text(q), "acceptedAnswer": {"@type": "Answer", "text": plain_text(a)}}
            for q, a in faqs
        ],
    }
    breadcrumb_json = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://allyonoindia.com/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://allyonoindia.com/blog/"},
            {"@type": "ListItem", "position": 3, "name": breadcrumb_label_raw, "item": canonical},
        ],
    }
    article_json = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title_raw,
        "description": meta_desc_raw,
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

    faq_html_blocks = []
    for q, a in faqs:
        faq_html_blocks.append(f'''        <details class="faq-item">
          <summary>{q}<svg class="faq-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg></summary>
          <p class="faq-answer">{a}</p>
        </details>''')
    faq_html = "\n".join(faq_html_blocks)
    faq_list_html = f'<div class="faq-list">\n{faq_html}\n      </div>'

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


def main():
    only_slugs = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    written, skipped = 0, 0
    for post in NEW_POSTS:
        slug = post["slug"]
        if slug in ALREADY_LIVE:
            continue
        if only_slugs and slug not in only_slugs:
            continue
        out_dir = os.path.join(ROOT, "blog", slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(build_post(post))
        print(f"Wrote blog/{slug}/index.html")
        written += 1

    print(f"\nDone. {written} files written.")


if __name__ == "__main__":
    main()
