"""
Pre-renders the promo code table (from assets/data/promo-codes.txt) into the
static HTML of promo-code/index.html and the homepage preview in index.html,
so both pages have real, crawlable content on first paint instead of a
"Loading promo codes..." placeholder. This is a Python port of the same
parsing/rendering logic in assets/js/main.js (parsePromoText, buildPromoRow,
etc.) — the client-side JS is untouched and still re-fetches and re-renders
on page load, so codes stay live between runs of this script; this just
gives crawlers and no-JS/first-paint visitors real content to see.

Also dedupes platform blocks that share the same name in promo-codes.txt
(keeping the last block's codes) — the JS table has no such dedup, so
duplicate blocks currently render as duplicate <tr id="..."> elements,
which is invalid HTML and breaks #slug anchor links to that game's row.

Usage:
    cd tools
    python render-promo-table.py
"""
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(ROOT, "assets", "data", "promo-codes.txt")

PROMO_STATUS_WORDS = {
    "checking": ("checking", "Checking"),
    "waiting to release": ("waiting", "Waiting to Release"),
    "waiting": ("waiting", "Waiting to Release"),
    "active": ("active", "Active"),
    "unavailable": ("unavailable", "Unavailable"),
}

PREVIEW_SLUGS = ["yono-777", "101z", "saga-slots", "abc-rummy"]


def escape_html(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    return s.strip("-")


def parse_slot(raw):
    key = (raw or "").strip().lower()
    known = PROMO_STATUS_WORDS.get(key)
    if known:
        return {"type": "status", "status": known[0], "label": known[1]}
    return {"type": "code", "value": (raw or "").strip()}


def field(block, label):
    m = re.search(rf"{label}:\s*(.+)", block, re.I)
    return m.group(1) if m else None


def parse_promo_text(text):
    m = re.search(r"^Last Updated:\s*(.+)$", text, re.I | re.M)
    last_updated = m.group(1).strip() if m else ""

    games = {}
    for block in re.split(r"\n\s*\n", text):
        name_raw = field(block, "Platform name")
        if not name_raw:
            continue
        name = name_raw.strip()
        morning = parse_slot(field(block, "Morning code"))
        afternoon = parse_slot(field(block, "Afternoon code"))
        evening = parse_slot(field(block, "Evening code"))
        status = "active" if any(c["type"] == "code" for c in (morning, afternoon, evening)) else "waiting"
        # dict assignment: duplicate platform-name blocks overwrite in place,
        # so the row keeps its first position but shows the LAST block's codes
        games[slugify(name)] = {
            "slug": slugify(name), "name": name, "status": status,
            "morning": morning, "afternoon": afternoon, "evening": evening,
        }
    return last_updated, list(games.values())


def build_promo_cell(label, cell):
    if cell["type"] == "code":
        code = escape_html(cell["value"])
        return (f'<td data-label="{label}"><span class="code-cell"><span class="code-value">{code}</span>'
                f'<button class="copy-btn" data-code="{code}" type="button">Copy</button></span></td>')
    status = cell.get("status", "waiting")
    label_text = escape_html(cell.get("label", "Waiting to Release"))
    return f'<td data-label="{label}"><span class="status-pill status-{status}">{label_text}</span></td>'


def build_promo_row(game):
    name = escape_html(game["name"])
    return (
        f'<tr id="{game["slug"]}" data-name="{name}" data-status="{game["status"]}">'
        f'<td data-label="Game"><span class="promo-game-cell"><img src="/assets/images/games/{game["slug"]}.webp" '
        f'alt="{name} logo" width="30" height="30" loading="lazy" onerror="this.style.display=\'none\'">{name}</span></td>'
        + build_promo_cell("Morning", game["morning"])
        + build_promo_cell("Afternoon", game["afternoon"])
        + build_promo_cell("Evening", game["evening"])
        + f'<td data-label="Action"><a class="btn btn-outline btn-sm" href="/all-yono-games/{game["slug"]}/">View Game</a></td>'
        + "</tr>"
    )


def static_checking_row(slug, name):
    checking = '<span class="status-pill status-checking">Checking</span>'
    return (
        f'<tr id="{slug}" data-name="{name}" data-status="waiting">'
        f'<td data-label="Game"><span class="promo-game-cell"><img src="/assets/images/games/{slug}.webp" '
        f'alt="{name} logo" width="30" height="30" loading="lazy" onerror="this.style.display=\'none\'">{name}</span></td>'
        f'<td data-label="Morning">{checking}</td>'
        f'<td data-label="Afternoon">{checking}</td>'
        f'<td data-label="Evening">{checking}</td>'
        f'<td data-label="Action"><a class="btn btn-outline btn-sm" href="/all-yono-games/{slug}/">View Game</a></td>'
        "</tr>"
    )


def replace_tbody(html, element_id, new_inner):
    pattern = re.compile(
        r'(<tbody id="' + re.escape(element_id) + r'"[^>]*>)(.*?)(</tbody>)', re.S
    )
    if not pattern.search(html):
        raise SystemExit(f'Could not find <tbody id="{element_id}"> — aborting.')
    return pattern.sub(lambda m: m.group(1) + new_inner + m.group(3), html, count=1)


def replace_last_updated(html, text):
    pattern = re.compile(r'(<span id="promoLastUpdated">)(.*?)(</span>)', re.S)
    if not pattern.search(html):
        return html
    display = escape_html(text) if text else "—"
    return pattern.sub(lambda m: m.group(1) + display + m.group(3), html, count=1)


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        text = f.read()
    last_updated, games = parse_promo_text(text)

    main_rows = "\n            " + "\n            ".join(
        [static_checking_row("dhan-game", "DhanGame")]
        + [build_promo_row(g) for g in games]
    ) + "\n          "
    by_slug = {g["slug"]: g for g in games}
    preview_rows = "\n            " + "\n            ".join(
        build_promo_row(by_slug[s]) for s in PREVIEW_SLUGS if s in by_slug
    ) + "\n          "

    promo_page_path = os.path.join(ROOT, "promo-code", "index.html")
    with open(promo_page_path, encoding="utf-8") as f:
        html = f.read()
    html = replace_tbody(html, "promoTableBody", main_rows)
    html = replace_last_updated(html, last_updated)
    with open(promo_page_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {len(games)} rows in promo-code/index.html")

    home_path = os.path.join(ROOT, "index.html")
    with open(home_path, encoding="utf-8") as f:
        html = f.read()
    html = replace_tbody(html, "promoPreviewBody", preview_rows)
    html = replace_last_updated(html, last_updated)
    with open(home_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated {len(PREVIEW_SLUGS)}-slot preview in index.html")

    dupe_check = re.findall(r"Platform name:\s*(.+)", text)
    from collections import Counter
    dupes = {k.strip(): v for k, v in Counter(n.strip() for n in dupe_check).items() if v > 1}
    if dupes:
        print(f"\nNote: promo-codes.txt has duplicate blocks for: {dupes} — kept the last block's codes for each.")


if __name__ == "__main__":
    main()
