"""
Generates standalone all-yono-games/<slug>/index.html files directly from
new_games_data.py, with NO Strapi involvement at all — matches the exact
template/structure the site already uses (same HEADER/FOOTER/schema layout
as generate-game-pages.py), but reads local data instead of the CMS. This is
the manual-posting workflow for new games: edit new_games_data.py or the
generated HTML directly, then git push when ready.

Does NOT touch all-yono-games/index.html (the listing grid) or the rummy/
arcade category pages — add the new game's card to those by hand, to avoid
clobbering any existing entries.

Usage:
    cd tools
    python generate-static-games.py                  # generates every game in new_games_data.py
    python generate-static-games.py win-rummy         # just specific slugs
"""
import hashlib
import json
import os
import re
import sys
from urllib.parse import urlsplit

from new_games_data import NEW_GAMES

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
GDIR = os.path.join(ROOT, "all-yono-games")
BLOG_DIR = os.path.join(ROOT, "blog")

CAT_LABEL = {
    "slots": "Slots", "rummy": "Rummy", "arcade": "Arcade",
    "casual": "Casual", "card-games": "Card Games", "sports": "Sports",
}

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def date_human(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y} IST"


def pill_html(status_list):
    out = []
    for cls, label in status_list or []:
        out.append(f'<span class="status-pill status-{cls}">{label}</span>')
    return "\n            ".join(out)


def possessive(name):
    return name + ("'" if name.endswith(("s", "S")) else "'s")


def pick(pool, slug, salt):
    i = int(hashlib.md5((slug + salt).encode()).hexdigest(), 16) % len(pool)
    return pool[i]


DOWNLOAD_VARIANTS = [
    "Tap the Download URL button above. It links to the current official {name} download link verified on All Yono India — always use this directory's link rather than one shared in a chat or screenshot, since unofficial copies can go stale.",
    "Use the Download URL button on this page to get {poss} current APK. The destination link is checked and updated here, so treat any copy shared elsewhere as unverified until you compare it against this page.",
    "The Download URL button above points to {poss} current access link as tracked on All Yono India. Download links in this category change periodically, so this page — not an old bookmark or forwarded message — is the one to trust.",
    "Grab {name} using the Download URL button above. This directory checks that link on an ongoing basis; if a link you found somewhere else doesn't match what's shown here, assume it's outdated.",
    "The current {name} download link sits behind the Download URL button on this page. Since links in this app category rotate periodically, this listing is the one to check against before using a link from anywhere else.",
]

LOGIN_VARIANTS = [
    "{name} login happens entirely inside the app after installation — enter your phone number and confirm the SMS OTP. This website never provides a login form and will not ask for your password, OTP, or account details.",
    "Login for {name} is completed inside the app itself: install it, enter your phone number, and verify the OTP sent by SMS. This directory doesn't collect login details and never will.",
    "You log in to {name} from inside the installed app using your phone number plus an SMS OTP. All Yono India has no login form of its own and never requests passwords, OTPs, or account information.",
    "{poss} login step lives inside the app: enter your phone number, confirm the SMS code, and you're in. This site never asks for that information itself.",
    "Signing in to {name} is handled entirely within the app using your phone number and an SMS OTP. No login form exists on this website, and none of your credentials are ever requested here.",
]

QUICK_ANSWER_VARIANTS = [
    "{name} is one of the {cat_lower} apps listed in the All Yono directory. This page tracks its current download link, live promo code status, and login steps — always confirm details here before using a link from elsewhere.",
    "{name} is a {cat_lower} app in the All Yono lineup, independently developed and unaffiliated with this directory. Get its current download link, check today's promo code status, and see how login works below.",
    "Looking for {name}? It's a {cat_lower}-category app tracked on All Yono India, with its own developer and account system separate from every other listing here. The current download link, promo code status, and login details are below.",
    "{name} sits in the {cat_lower} category of the All Yono directory. This page keeps its download link, promo code status, and login steps up to date — check below before installing.",
    "{name} is one of several {cat_lower} apps in the All Yono directory, each run independently. Find its current download link, promo code status, and login process on this page.",
]


def load_existing_games():
    """Lightweight scan of already-published game pages, used only for
    cross-linking context (siblings/related-games) when generating a new one."""
    existing = []
    for slug in sorted(os.listdir(GDIR)):
        p = os.path.join(GDIR, slug, "index.html")
        if slug in ("rummy", "arcade") or not os.path.isfile(p):
            continue
        c = open(p, encoding="utf-8").read()
        name_m = re.search(r'<h1[^>]*>([^<]+)</h1>', c)
        cat_m = re.search(r'game-category">([^<]+)</span>', c)
        img_m = re.search(r'game-icon" style="width:64px;height:64px"><img src="([^"]+)"', c)
        if name_m and cat_m and img_m:
            existing.append({"slug": slug, "name": name_m.group(1).strip(),
                              "category": cat_m.group(1).strip(), "img": img_m.group(1)})
    return existing


def matching_blog_slug(slug):
    if not os.path.isdir(BLOG_DIR):
        return None
    blogs = set(os.listdir(BLOG_DIR))
    for cand in (slug + "-apk-download", slug + "-promo-code", slug + "-welcome-bonus"):
        if cand in blogs:
            return cand
    return None


def blog_post_title(blog_slug):
    p = os.path.join(BLOG_DIR, blog_slug, "index.html")
    c = open(p, encoding="utf-8").read()
    m = re.search(r'<h1>(.*?)</h1>', c, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else blog_slug


def build_quick_answer(g):
    text = pick(QUICK_ANSWER_VARIANTS, g["slug"], "qa").format(name=g["name"], cat_lower=CAT_LABEL[g["category"]].lower())
    return f'      <p style="font-weight:600;color:var(--white)">{text}</p>'


def build_key_takeaways(g, siblings):
    domain = urlsplit(g["download_url"]).netloc.replace("www.", "")
    rows = [
        ("Category", CAT_LABEL[g["category"]]),
        ("Current download domain", domain),
        ("Login method", "Phone number + SMS OTP, inside the app only"),
        ("Promo code schedule", "Morning, afternoon, evening &mdash; updated as codes release"),
        ("Status", g["promo_status"]),
    ]
    if siblings:
        rows.append(("Often confused with", ", ".join(siblings)))
    trs = "\n".join(f'          <tr><td>{k}</td><td>{v}</td></tr>' for k, v in rows)
    return f'''      <div class="callout" style="margin:20px 0 24px">
        <table style="width:100%;border-collapse:collapse">
          <thead><tr><th style="text-align:left;padding-bottom:6px">What</th><th style="text-align:left;padding-bottom:6px">Details</th></tr></thead>
          <tbody>
{trs}
          </tbody>
        </table>
      </div>'''


def build_faq(g, siblings):
    name, slug = g["name"], g["slug"]
    poss = possessive(name)
    download_a = pick(DOWNLOAD_VARIANTS, slug, "dl").format(name=name, poss=poss)
    login_a = pick(LOGIN_VARIANTS, slug, "lg").format(name=name, poss=poss)

    if siblings:
        sib = siblings[0]
        disambig_q = f"Is {name} the same app as {sib}?"
        disambig_a = (f"No. {name} shares the {CAT_LABEL[g['category']]} category with {sib} and others in the All Yono "
                       f"lineup, but it is a separate app with its own developer, download link, account system, and "
                       f"promo codes. Installing {name} has no effect on any other All Yono app.")
    else:
        disambig_q = f"Is {name} part of the All Yono directory?"
        disambig_a = (f"Yes. {name} is listed in the {CAT_LABEL[g['category']]} category on All Yono India. The download "
                       f"link and promo code on this page are updated regularly. See the "
                       f"<a href='/all-yono-games/' style='color:var(--cyan);font-weight:700'>full All Yono Games directory</a> "
                       f"for other listed apps.")

    promo_q = f"Is there a {name} promo code yet?"
    promo_a = (f"Check the <a href='/promo-code/#{slug}' style='color:var(--cyan);font-weight:700'>Promo Code page</a> "
               f"for {name}'s current morning, afternoon, and evening status before assuming a code is active.")

    faqs = [
        (disambig_q, disambig_a),
        (f"How do I download the {name} APK?", download_a),
        (f"How does {name} login work?", login_a),
        (promo_q, promo_a),
    ]

    blocks = []
    for i, (q, a) in enumerate(faqs):
        margin = "margin-bottom:32px" if i == len(faqs) - 1 else "margin-bottom:10px"
        blocks.append(
            f'      <div style="{margin};padding:16px 20px;background:var(--panel);'
            f'border:1px solid rgba(255,255,255,0.07);border-radius:4px">\n'
            f'        <h3 style="font-size:0.95rem;margin-bottom:8px">{q}</h3>\n'
            f'        <p style="margin:0;color:var(--muted);font-size:0.88rem">{a}</p>\n'
            f'      </div>'
        )
    faq_html = "\n".join(blocks)
    faq_json = [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in faqs
    ]
    return faq_html, faq_json


def build_related(g, siblings_full):
    if not siblings_full:
        return None
    cards = []
    for o in siblings_full[:4]:
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


def build_game_page(g, existing_games):
    name, slug = g["name"], g["slug"]
    cat_label = CAT_LABEL[g["category"]]
    desc = g.get("description") or ""
    updated = date_human(g["updated"])
    title = f"{name} APK Download & Promo Code | All Yono India"
    meta_desc = f"{name} download link, access status, and promo code — checked and updated on the All Yono India directory."
    og_desc = f"Live download link, access status, and promo code for {name} on All Yono India."
    canonical = f"https://allyonoindia.com/all-yono-games/{slug}/"
    keywords = f"{name.lower()}, {name.lower()} apk download, {name.lower()} login, {name.lower()} promo code"

    same_cat = [o for o in existing_games if o["category"].lower() == g["category"].lower() and o["slug"] != slug]
    siblings = [o["name"] for o in same_cat[:2]]

    quick_answer = build_quick_answer(g)
    key_takeaways = build_key_takeaways(g, siblings)
    faq_html, faq_json_list = build_faq(g, siblings)
    related = build_related(g, same_cat)
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

    blog_slug = matching_blog_slug(slug)
    blog_link_html = ""
    if blog_slug:
        blog_title = blog_post_title(blog_slug)
        blog_link_html = (
            f'\n      <p>For setup steps, login safety checks, and more detail, see the '
            f'<a href="/blog/{blog_slug}/" style="color:var(--cyan);font-weight:700">{blog_title}</a> on the blog.</p>'
        )

    breadcrumb_json = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://allyonoindia.com/"},
            {"@type": "ListItem", "position": 2, "name": "All Yono Games", "item": "https://allyonoindia.com/all-yono-games/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }
    faq_json = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_json_list,
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
<link rel="preload" href="/assets/fonts/goldman-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/goldman-700.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.min.css">

<script type="application/ld+json">
{json.dumps(breadcrumb_json, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(faq_json, indent=2)}
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

{quick_answer}
{key_takeaways}
      <p>{desc}</p>
      <ul class="meta-list" style="margin:16px 0">
        <li>Promo Code: <b>{g['promo_status']}</b></li>
        <li>Last Updated: <b>{updated}</b></li>
      </ul>
      <div class="card-actions" style="max-width:420px">
        <a class="btn btn-cyan" href="{g['download_url']}" target="_blank" rel="nofollow noopener noreferrer">Download URL</a>
        <a class="btn btn-ghost" href="/promo-code/#{slug}">Check Promo Code</a>
      </div>
      <p class="access-note" style="margin-top:12px">Login inside app only</p>{blog_link_html}

      <h2 style="margin-top:40px">Frequently Asked Questions</h2>
{faq_html}
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
    updated = date_human(g["updated"])
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


def main():
    only_slugs = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    existing_games = load_existing_games()
    written = 0
    for g in NEW_GAMES:
        slug = g["slug"]
        if only_slugs and slug not in only_slugs:
            continue
        out_dir = os.path.join(ROOT, "all-yono-games", slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(build_game_page(g, existing_games))
        print(f"Wrote all-yono-games/{slug}/index.html")
        print(f"  -> Add this card to all-yono-games/index.html (and the {g['category']} category page, if it has one):")
        print(f"  {build_listing_card(g)}")
        written += 1

    print(f"\nDone. {written} game page(s) written. Remember to add each one to sitemap.xml.")


if __name__ == "__main__":
    main()
