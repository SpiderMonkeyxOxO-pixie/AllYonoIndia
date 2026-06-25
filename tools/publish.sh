#!/bin/bash
# One-command publish: pulls latest Strapi content into static pages and
# pushes the result. Meant to be run directly on the live VPS, inside
# /www/wwwroot/allyonoindia.com — there is no separate deploy step because
# this directory IS the live site.
#
# Usage (on the VPS):
#   cd /www/wwwroot/allyonoindia.com
#   bash tools/publish.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Regenerating game pages..."
python3 tools/generate-game-pages.py

echo "Regenerating blog pages..."
python3 tools/generate-blog-pages.py

chown -R www:www . || true

if git diff --quiet && git diff --cached --quiet; then
  echo "No content changes since last publish. Nothing to do."
  exit 0
fi

git add -A
git commit -m "Publish: regenerate game/blog pages from Strapi"
git push

echo "Published."
