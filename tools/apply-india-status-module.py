"""
Phase 1 one-time (but safe-to-rerun / idempotent) local script: inserts the
India-Specific Status module (see india_status.py + INDIA_LOCALIZATION_DATA_MODEL.md)
into the already-generated all-yono-games/<slug>/index.html files.

None of the India-status fields have been populated for any game yet — the
module always renders the honest "not yet reviewed" fallback regardless.

ADAPTED during the Phase 3 controlled port (2026-08-13): the category-page
exclusion list was widened from ("rummy", "arcade") to also cover
("slots", "card-games", "casual"), added upstream after this script was
originally written — see ALLYONOINDIA_CONTROLLED_PORT_REPORT.md.

Usage:
    cd tools
    python apply-india-status-module.py
"""
import glob
import os
import re

from india_status import india_status_html

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

CALLOUT_RE = re.compile(
    r'(<div class="callout" style="margin-top:32px">\s*\n\s*'
    r'All Yono India is an independent directory and is not the developer, '
    r'publisher, or operator of )([^.]+)(\. <a href="/disclaimer/")'
)

# Category landing pages — not individual entity pages, no per-entity
# disclaimer callout to anchor on.
CATEGORY_PAGES = ("rummy", "arcade", "slots", "card-games", "casual")


def process(path):
    html = open(path, encoding="utf-8").read()

    if "India-Specific Status for" in html:
        return "skipped (already present)"

    match = CALLOUT_RE.search(html)
    if not match:
        return "SKIPPED — could not find the expected disclaimer callout to anchor on"

    name = match.group(2)
    module = india_status_html({}, name)
    insertion = module + "      " + match.group(0).replace('margin-top:32px', 'margin-top:16px')
    new_html = CALLOUT_RE.sub(lambda m: insertion, html, count=1)

    open(path, "w", encoding="utf-8").write(new_html)
    return f"updated ({name})"


def main():
    pattern = os.path.join(ROOT, "all-yono-games", "*", "index.html")
    files = [f for f in sorted(glob.glob(pattern))
             if os.path.basename(os.path.dirname(f)) not in CATEGORY_PAGES]

    counts = {"updated": 0, "skipped": 0, "error": 0}
    for f in files:
        result = process(f)
        rel = os.path.relpath(f, ROOT)
        print(f"{rel}: {result}")
        if result.startswith("updated"):
            counts["updated"] += 1
        elif result.startswith("skipped"):
            counts["skipped"] += 1
        else:
            counts["error"] += 1

    print(f"\n{counts['updated']} updated, {counts['skipped']} already had the module, "
          f"{counts['error']} could not be matched (need manual review).")


if __name__ == "__main__":
    main()
