"""
Regenerates the 52 individual game pages (all-yono-games/<slug>/index.html)
and the hardcoded card block inside all-yono-games/index.html, sourcing
data from Strapi instead of the old c:/tmp/game-pages-data.json scratch file.

This is a manual, explicitly-run step (matches the existing git-pull-with-
approval workflow) — it is never auto-triggered by Strapi or CI. Run it,
review `git diff`, then commit/push as usual.

Usage:
    cd tools
    pip install -r requirements.txt
    cp .env.example .env   # then fill in STRAPI_API_URL / STRAPI_API_TOKEN
    python generate-game-pages.py
"""
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
LISTING_PAGE = os.path.join(ROOT, "all-yono-games", "index.html")

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {"Authorization": f"Bearer {STRAPI_API_TOKEN}"}

CAT_LABEL = {
    "slots": "Slots", "rummy": "Rummy", "arcade": "Arcade",
    "casual": "Casual", "card-games": "Card Games", "sports": "Sports",
}

# Dedicated SEO landing pages for categories with real standalone search demand
# (low-competition keyword research, 2026-06-25) — every other category is still
# reachable via the client-side filter chips on the main listing page only.
CATEGORY_PAGES = {
    "rummy": {
        "title": "All Yono Rummy Games | APK Download & Promo Codes",
        "meta_desc": "Browse every All Yono rummy game and app with APK download links, live access status, and promo code checks in one directory.",
        "keywords": "all yono rummy, yono rummy apk download all, all yono rummy apk, yono rummy games",
        "h1": "All Yono Rummy Games",
        "intro": "Every All Yono rummy game and app in one place — APK download links, live access status, and promo code checks for each title below.",
    },
    "arcade": {
        "title": "All Yono Arcade Games | Download & Promo Codes",
        "meta_desc": "Browse every All Yono arcade game and app with download links, live access status, and promo code checks in one directory.",
        "keywords": "all yono arcade, yono arcade all download, yono arcade all games, all yono arcade apk",
        "h1": "All Yono Arcade Games",
        "intro": "Every All Yono arcade game and app in one place — download links, live access status, and promo code checks for each title below.",
    },
}


def fetch_games():
    games = []
    page = 1
    while True:
        resp = requests.get(
            f"{STRAPI_API_URL}/api/games",
            headers=HEADERS,
            params={"pagination[page]": page, "pagination[pageSize]": 100, "sort": "name:asc"},
        )
        resp.raise_for_status()
        body = resp.json()
        games.extend(body["data"])
        if page >= body["meta"]["pagination"]["pageCount"]:
            break
        page += 1
    return games


def format_updated(iso_timestamp):
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return dt.strftime("%-d %b %Y IST") if os.name != "nt" else f"{dt.day} {dt.strftime('%b %Y')} IST"


def pill_html(status_list):
    out = []
    for cls, label in status_list or []:
        out.append(f'<span class="status-pill status-{cls}">{label}</span>')
    return "\n            ".join(out)


def related_html(game, by_cat):
    cat = game["category"]
    others = [g for g in by_cat.get(cat, []) if g["slug"] != game["slug"]][:4]
    if not others:
        return None
    cards = []
    for o in others:
        cards.append(
            f'<a href="/all-yono-games/{o["slug"]}/" class="quick-card" style="text-decoration:none;flex-direction:row;align-items:center;gap:12px">'
            f'<span class="game-icon" style="width:36px;height:36px;flex-shrink:0"><img src="{o["img"]}" width="36" height="36" alt="{o["name"]} logo" loading="lazy"></span>'
            f'<h3 style="font-size:0.92rem;margin:0">{o["name"]}</h3>'
            f'</a>'
        )
    return "\n        ".join(cards)


HEADER = '''<header class="site-header">
  <div class="container">
    <a href="/" class="logo"><img src="/assets/icons/logo.webp" alt="All Yono India logo" width="34" height="34" class="logo-mark-img" loading="eager">All Yono <span class="logo-india">India</span></a>
    <nav class="main-nav" aria-label="Primary">
      <a href="/">Home</a>
      <a href="/all-yono-games/" class="is-active">All Yono Games</a>
      <a href="/promo-code/">Promo Code</a>
      <a href="/blog/">Blog</a>
    </nav>
    <div class="header-actions">
      <a href="/promo-code/" class="btn btn-primary btn-sm">Promo Code</a>
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
  <a href="/all-yono-games/" class="is-active"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 7h10l2 4-1 7-3-2H9l-3 2-1-7 2-4Z"/></svg>Games</a>
  <a href="/promo-code/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 4h14v16l-7-4-7 4V4Z"/></svg>Codes</a>
  <a href="/blog/"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5h16M4 12h16M4 19h10"/></svg>Blog</a>
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


def build_game_page(g, by_cat):
    name, slug = g["name"], g["slug"]
    cat_label = CAT_LABEL[g["category"]]
    desc = g.get("description") or ""
    updated = format_updated(g["updatedAt"])
    title = f"{name} APK Download & Promo Code | All Yono India"
    meta_desc = f"{name} download link, access status, and promo code — checked and updated on the All Yono India directory."
    og_desc = f"Live download link, access status, and promo code for {name} on All Yono India."
    canonical = f"https://allyonoindia.com/all-yono-games/{slug}/"
    keywords = f"{name.lower()}, {name.lower()} apk download, {name.lower()} login, {name.lower()} promo code"

    related = related_html(g, by_cat)
    if related:
        related_block = f'''
      <h2 style="margin-top:40px">More {cat_label} Games</h2>
      <div class="quick-grid" style="grid-template-columns:repeat(2,1fr)">
        {related}
      </div>
'''
    else:
        related_block = '''
      <p style="margin-top:32px"><a href="/all-yono-games/" style="color:var(--cyan);font-weight:700">Browse the full All Yono Games directory</a></p>
'''

    import json as _json
    breadcrumb_json = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://allyonoindia.com/"},
            {"@type": "ListItem", "position": 2, "name": "All Yono Games", "item": "https://allyonoindia.com/all-yono-games/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }

    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>{title}</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{keywords}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="All Yono India">
<meta property="og:image" content="https://allyonoindia.com/assets/images/og-cover.jpg">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="https://allyonoindia.com/assets/images/og-cover.jpg">

<link rel="icon" href="/assets/icons/favicon.webp" type="image/webp">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.webp">
<link rel="preconnect" href="https://api.allyonoindia.com" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.min.css">

<script type="application/ld+json">
{_json.dumps(breadcrumb_json, indent=2)}
</script>
</head>
<body>

{HEADER}

<main>
  <div class="container">
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a> / <a href="/all-yono-games/">All Yono Games</a> / <span aria-current="page">{name}</span>
    </nav>
  </div>

  <section class="section" style="padding-top:24px">
    <div class="container" style="max-width:760px">
    <div class="content-page">
      <div class="game-card-top" style="margin-bottom:16px">
        <span class="game-icon" style="width:64px;height:64px"><img src="{g['img']}" alt="{name} logo" width="64" height="64" loading="eager"></span>
        <div>
          <h1 style="margin-bottom:4px">{name}</h1>
          <span class="game-category">{cat_label}</span>
        </div>
      </div>
      <div class="status-row" style="margin-bottom:16px">
            {pill_html(g['statuses'])}
      </div>
      <p>{desc}</p>
      <ul class="meta-list" style="margin:16px 0">
        <li>Promo Code: <b>{g['promo_status']}</b></li>
        <li>Last Updated: <b>{updated}</b></li>
      </ul>
      <div class="card-actions" style="max-width:420px">
        <a class="btn btn-cyan" href="{g['download_url']}" target="_blank" rel="nofollow noopener noreferrer">Download URL</a>
        <a class="btn btn-ghost" href="/promo-code/#{slug}">Check Promo Code</a>
      </div>
      <p class="access-note" style="margin-top:12px">Login inside app only</p>
{related_block}
      <div class="callout" style="margin-top:32px">
        All Yono India is an independent directory and is not the developer, publisher, or operator of {name}. <a href="/disclaimer/" style="color:var(--cyan);font-weight:700">Read our full disclaimer</a>.
      </div>
    </div>
    </div>
  </section>
</main>

{FOOTER}'''


def build_listing_card(g):
    name, slug = g["name"], g["slug"]
    cat_label = CAT_LABEL[g["category"]]
    updated = format_updated(g["updatedAt"])
    pills = "\n            ".join(
        f'<span class="status-pill status-{cls}">{label}</span>' for cls, label in (g["statuses"] or [])
    )
    return f'''<article class="game-card" data-name="{name}" data-category="{g['category']}">
          <a class="game-card-top" href="/all-yono-games/{slug}/" style="text-decoration:none">
            <span class="game-icon"><img src="{g['img']}" alt="{name} logo" width="52" height="52" loading="lazy"></span>
            <div>
              <h3 class="game-name">{name}</h3>
              <span class="game-category">{cat_label}</span>
            </div>
          </a>
          <div class="status-row">
            {pills}
          </div>
          <ul class="meta-list">
            <li>Promo Code: <b>{g['promo_status']}</b></li>
            <li>Last Updated: <b>{updated}</b></li>
          </ul>
          <div class="card-actions">
            <a class="btn btn-cyan btn-sm" href="{g['download_url']}" target="_blank" rel="nofollow noopener noreferrer">Download URL</a>
            <a class="btn btn-ghost btn-sm" href="/promo-code/#{slug}">Check Code</a>
          </div>
          <p class="access-note">Login inside app only</p>
        </article>'''


def build_category_page(category, games_in_cat):
    seo = CATEGORY_PAGES[category]
    canonical = f"https://allyonoindia.com/all-yono-games/{category}/"
    cards = "\n        ".join(build_listing_card(g) for g in games_in_cat)
    other_links = "\n        ".join(
        f'<a href="/all-yono-games/{slug}/" style="color:var(--cyan);font-weight:700">{CATEGORY_PAGES[slug]["h1"]}</a>'
        for slug in CATEGORY_PAGES if slug != category
    )

    import json as _json
    breadcrumb_json = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://allyonoindia.com/"},
            {"@type": "ListItem", "position": 2, "name": "All Yono Games", "item": "https://allyonoindia.com/all-yono-games/"},
            {"@type": "ListItem", "position": 3, "name": seo["h1"], "item": canonical},
        ],
    }

    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>{seo["title"]}</title>
<meta name="description" content="{seo["meta_desc"]}">
<meta name="keywords" content="{seo["keywords"]}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow">

<meta property="og:type" content="website">
<meta property="og:title" content="{seo["title"]}">
<meta property="og:description" content="{seo["meta_desc"]}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="All Yono India">
<meta property="og:image" content="https://allyonoindia.com/assets/images/og-cover.jpg">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{seo["title"]}">
<meta name="twitter:description" content="{seo["meta_desc"]}">
<meta name="twitter:image" content="https://allyonoindia.com/assets/images/og-cover.jpg">

<link rel="icon" href="/assets/icons/favicon.webp" type="image/webp">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.webp">
<link rel="preconnect" href="https://api.allyonoindia.com" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.min.css">

<script type="application/ld+json">
{_json.dumps(breadcrumb_json, indent=2)}
</script>
</head>
<body>

{HEADER}

<main>
  <div class="container">
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="/">Home</a> / <a href="/all-yono-games/">All Yono Games</a> / <span aria-current="page">{seo["h1"]}</span>
    </nav>
  </div>

  <section class="section" style="padding-top:24px">
    <div class="container">
      <div class="section-head">
        <span class="eyebrow">Game Directory · {CAT_LABEL[category]}</span>
        <h1>{seo["h1"]}</h1>
        <p>{seo["intro"]}</p>
      </div>

      <p style="margin:-4px 0 20px;font-size:0.92rem">Other categories: {other_links} &middot; <a href="/all-yono-games/" style="color:var(--cyan);font-weight:700">Full Directory</a></p>

      <div class="game-grid">
        {cards}
      </div>
    </div>
  </section>
</main>

{FOOTER}'''


def regenerate_listing_page(games):
    html = open(LISTING_PAGE, encoding="utf-8").read()
    cards = "\n        ".join(build_listing_card(g) for g in games)
    new_block = (
        "<!-- GAMES_GRID_START: auto-generated by tools/generate-game-pages.py, do not hand-edit individual cards below -->\n        "
        + cards
        + "\n        <!-- GAMES_GRID_END -->"
    )
    pattern = re.compile(
        r"<!-- GAMES_GRID_START.*?GAMES_GRID_END -->",
        re.DOTALL,
    )
    if not pattern.search(html):
        sys.exit("Could not find GAMES_GRID_START/END markers in all-yono-games/index.html — aborting.")
    html = pattern.sub(new_block, html)
    open(LISTING_PAGE, "w", encoding="utf-8").write(html)


def main():
    games = fetch_games()
    by_cat = {}
    for g in games:
        by_cat.setdefault(g["category"], []).append(g)

    for g in games:
        out_dir = os.path.join(ROOT, "all-yono-games", g["slug"])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_game_page(g, by_cat))

    regenerate_listing_page(games)

    for category in CATEGORY_PAGES:
        out_dir = os.path.join(ROOT, "all-yono-games", category)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_category_page(category, by_cat.get(category, [])))

    print(
        f"Generated {len(games)} individual game pages, regenerated the listing page grid, "
        f"and built {len(CATEGORY_PAGES)} category landing pages."
    )


if __name__ == "__main__":
    main()
