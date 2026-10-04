#!/bin/bash
# Safe site update on the VPS. The admin panel rewrites three tracked files
# (assets/data/promo-codes.txt, promo-code/index.html, index.html), so a plain
# `git pull` can refuse or clobber them. Run this instead:
#
#   cd /www/wwwroot/allyonoindia.com && bash tools/promo-admin/deploy.sh
#
# - promo-codes.txt is never touched by deploys (skip-worktree), so live codes survive.
# - the two pre-rendered pages are reset, pulled, then re-rendered from the live codes.
set -euo pipefail
cd "$(dirname "$0")/../.."

git update-index --skip-worktree assets/data/promo-codes.txt
git checkout -- index.html promo-code/index.html
git pull --ff-only origin main
python3 tools/render-promo-table.py
pm2 restart allyonoindia-admin --update-env >/dev/null 2>&1 || true
echo "Deployed. Live promo codes preserved."
