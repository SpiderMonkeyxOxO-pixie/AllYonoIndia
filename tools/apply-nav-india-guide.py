"""
Phase 1 one-time (but safe-to-rerun / idempotent) local script: adds the
"India Guide" link (-> /india-guide/) to main-nav, mobile-nav, and the footer
"Main Pages" list across every already-generated static HTML file site-wide.

Pure addition — does not remove or reorder any existing nav item. Skips a
file entirely if it already links to /india-guide/ in its nav (idempotent).
The 3 generator scripts' HEADER/FOOTER constants were already updated by
hand to match, so future regeneration stays in sync with this.

Usage:
    cd tools
    python apply-nav-india-guide.py
"""
import glob
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

EXCLUDE_DIR_PARTS = {"node_modules", ".git", "tools", "Scheduled", "Scheduledv2", "reconciliation"}

MAIN_NAV_RE = re.compile(
    r'(<nav class="main-nav" aria-label="Primary">\s*\n\s*<a href="/"[^>]*>Home</a>)\n(\s*)(<a href="/all-yono-games/")'
)
MOBILE_NAV_RE = re.compile(
    r'(<nav id="mobileNav" class="mobile-nav" aria-label="Mobile">\s*\n\s*<a href="/">Home</a>)\n(\s*)(<a href="/all-yono-games/")'
)
FOOTER_RE = re.compile(
    r'(<h3>Main Pages</h3>\s*\n\s*<ul>\s*\n\s*<li><a href="/">Home</a></li>)\n(\s*)(<li><a href="/all-yono-games/")'
)


def relevant_files():
    for path in glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True):
        rel = os.path.relpath(path, ROOT)
        parts = rel.split(os.sep)
        if any(p in EXCLUDE_DIR_PARTS for p in parts):
            continue
        yield path
    yield os.path.join(ROOT, "404.html")


def process(path):
    if not os.path.isfile(path):
        return "missing"
    html = open(path, encoding="utf-8").read()

    if '/india-guide/">India Guide' in html:
        return "skipped (already present)"

    original = html
    html = MAIN_NAV_RE.sub(lambda m: f'{m.group(1)}\n{m.group(2)}<a href="/india-guide/">India Guide</a>\n{m.group(2)}{m.group(3)}', html, count=1)
    html = MOBILE_NAV_RE.sub(lambda m: f'{m.group(1)}\n{m.group(2)}<a href="/india-guide/">India Guide</a>\n{m.group(2)}{m.group(3)}', html, count=1)
    html = FOOTER_RE.sub(lambda m: f'{m.group(1)}\n{m.group(2)}<li><a href="/india-guide/">India Guide</a></li>\n{m.group(2)}{m.group(3)}', html, count=1)

    if html == original:
        return "SKIPPED — no nav pattern matched (needs manual review)"

    open(path, "w", encoding="utf-8").write(html)
    return "updated"


def main():
    counts = {"updated": 0, "skipped": 0, "error": 0, "missing": 0}
    for f in relevant_files():
        result = process(f)
        rel = os.path.relpath(f, ROOT)
        print(f"{rel}: {result}")
        if result == "updated":
            counts["updated"] += 1
        elif result.startswith("skipped"):
            counts["skipped"] += 1
        elif result == "missing":
            counts["missing"] += 1
        else:
            counts["error"] += 1
    print(f"\n{counts['updated']} updated, {counts['skipped']} already had the link, "
          f"{counts['error']} unmatched (need manual review), {counts['missing']} missing files.")


if __name__ == "__main__":
    main()
