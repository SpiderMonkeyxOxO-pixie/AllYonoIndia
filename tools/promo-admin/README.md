# Promo-code admin — code.allyonoindia.com

A small, dependency-free Node server (`server.js`, Node 18+) that edits
`assets/data/promo-codes.txt` — the file the public pages fetch on every load —
and then re-runs `tools/render-promo-table.py` so the pre-rendered HTML that
crawlers see matches. Single admin, no sign-up. `/tools/` is not web-served on
this site, so the code is not publicly reachable.

## One-time setup (on the VPS)

1. **DNS (Cloudflare):** A record `code` -> same IP as allyonoindia.com.
2. **Update the site folder:** `cd /www/wwwroot/allyonoindia.com && git pull origin main`
3. **Create the settings file OUTSIDE the repo** (so `git add -A` publish jobs can never commit it).
   Replace the password text, keep the single quotes:
   ```
   node -e "const c=require('crypto');const s=c.randomBytes(16);console.log('ADMIN_PASSWORD_HASH=scrypt:'+s.toString('hex')+':'+c.scryptSync(process.argv[1],s,64).toString('hex'));console.log('ADMIN_SESSION_SECRET='+c.randomBytes(32).toString('base64url'))" 'your-long-password' > /tmp/new.env
   (echo "ADMIN_USERNAME=Admin"; echo "PORT=3120"; cat /tmp/new.env) > /www/wwwroot/allyonoindia-admin.env
   rm /tmp/new.env; chmod 600 /www/wwwroot/allyonoindia-admin.env; history -c
   ```
4. **Start it:**
   ```
   pm2 start tools/promo-admin/server.js --name allyonoindia-admin
   pm2 save
   curl -s http://127.0.0.1:3120/healthz   # -> ok
   ```
   (If 3120 is taken, change PORT in the settings file and restart with `--update-env`.)
5. **aaPanel:** add site `code.allyonoindia.com` -> Reverse proxy: dir `/`,
   target `http://127.0.0.1:3120`, Sent Domain `$host`, **cache OFF**. Then SSL
   (Let's Encrypt) + Force HTTPS.
6. **Protect live codes from deploys (once):**
   `git update-index --skip-worktree assets/data/promo-codes.txt`
   From now on update the site with `bash tools/promo-admin/deploy.sh`.

## Daily use

Log in at https://code.allyonoindia.com. Type codes into Morning / Afternoon /
Evening and press **Save changes** — live on /promo-code/ immediately. **Start
new day** clears every code. **Add a platform** puts a new platform at the top.
Empty boxes publish as "Waiting to Release".

## Notes

- Each save backs up the previous file to `/www/wwwroot/allyonoindia-admin-data/backups/` (last 60 kept).
- Newly typed codes that look like a link/domain are rejected; old entries are grandfathered.
- Saving merges duplicate platform blocks (the live site already used the last block).
- 5 failed logins from one IP locks that IP out for 15 minutes; sessions last 8 h.
- Settings: `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `ADMIN_SESSION_SECRET`, `PORT`,
  optional `PROMO_FILE`, `BACKUP_DIR`, `PUBLIC_URL`, `ENV_FILE`.
