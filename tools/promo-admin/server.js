#!/usr/bin/env node
/**
 * code.allyonoindia.com — promo-code admin for the static AllYonoIndia site.
 *
 * Zero dependencies (Node 18+). Runs as its own process (PM2), listens on
 * 127.0.0.1 only, and is exposed through an nginx/aaPanel reverse proxy for
 * code.allyonoindia.com. It edits assets/data/promo-codes.txt — the file the
 * public pages fetch on every load — then re-runs tools/render-promo-table.py
 * so the pre-rendered HTML (what crawlers see) matches.
 *
 * Config comes from an env file OUTSIDE the git checkout (default
 * /www/wwwroot/allyonoindia-admin.env, i.e. next to the site folder), so the
 * VPS's `git add -A` publish jobs can never commit secrets. See README.md.
 */
"use strict";

const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { execFile } = require("node:child_process");

const SITE_ROOT = path.resolve(process.env.SITE_ROOT || path.join(__dirname, "..", ".."));

// ---------- config ----------
function loadEnvFile(file) {
  let raw;
  try {
    raw = fs.readFileSync(file, "utf8");
  } catch {
    return;
  }
  for (const line of raw.split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2];
  }
}
loadEnvFile(
  process.env.ENV_FILE || path.resolve(SITE_ROOT, "..", "allyonoindia-admin.env"),
);

const PORT = Number(process.env.PORT || 3120);
const PROMO_FILE = path.resolve(
  process.env.PROMO_FILE || path.join(SITE_ROOT, "assets", "data", "promo-codes.txt"),
);
const BACKUP_DIR = path.resolve(
  process.env.BACKUP_DIR || path.join(SITE_ROOT, "..", "allyonoindia-admin-data", "backups"),
);
const PUBLIC_URL = (process.env.PUBLIC_URL || "https://allyonoindia.com").replace(/\/$/, "");
const SECURE_COOKIE = process.env.INSECURE_COOKIES !== "1";
const RENDER_CMD = process.env.RENDER_CMD || (process.platform === "win32" ? "python" : "python3");

const SESSION_MS = 8 * 60 * 60 * 1000;
const COOKIE = "ai_admin";
const MAX_CODE_LENGTH = 40;
const MAX_NAME_LENGTH = 40;
const WAITING = "Waiting to Release";

function authConfigured() {
  return Boolean(
    process.env.ADMIN_USERNAME &&
      process.env.ADMIN_PASSWORD_HASH &&
      (process.env.ADMIN_SESSION_SECRET || "").length >= 32,
  );
}

// ---------- auth ----------
const sign = (payload) =>
  crypto.createHmac("sha256", process.env.ADMIN_SESSION_SECRET || "").update(payload).digest("base64url");

function safeEqual(a, b) {
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  return ab.length === bb.length && crypto.timingSafeEqual(ab, bb);
}

function verifyPassword(password, stored) {
  const [scheme, saltHex, hashHex] = String(stored).split(":");
  if (scheme !== "scrypt" || !saltHex || !hashHex) return false;
  const expected = Buffer.from(hashHex, "hex");
  const actual = crypto.scryptSync(password, Buffer.from(saltHex, "hex"), expected.length);
  return crypto.timingSafeEqual(actual, expected);
}

const MAX_FAILS = 5;
const LOCK_MS = 15 * 60 * 1000;
const fails = new Map();

function clientKey(req) {
  return (
    req.headers["x-real-ip"] ||
    String(req.headers["x-forwarded-for"] || "").split(",")[0].trim() ||
    req.socket.remoteAddress ||
    "unknown"
  );
}
function isLockedOut(req) {
  const key = clientKey(req);
  const rec = fails.get(key);
  if (!rec) return false;
  if (Date.now() - rec.first > LOCK_MS) {
    fails.delete(key);
    return false;
  }
  return rec.count >= MAX_FAILS;
}
function recordFailure(req) {
  const key = clientKey(req);
  const rec = fails.get(key);
  if (!rec || Date.now() - rec.first > LOCK_MS) fails.set(key, { count: 1, first: Date.now() });
  else rec.count += 1;
}

function parseCookies(req) {
  const out = {};
  for (const part of String(req.headers.cookie || "").split(";")) {
    const i = part.indexOf("=");
    if (i > 0) out[part.slice(0, i).trim()] = decodeURIComponent(part.slice(i + 1).trim());
  }
  return out;
}

function isAuthenticated(req) {
  if (!authConfigured()) return false;
  const token = parseCookies(req)[COOKIE];
  if (!token) return false;
  const i = token.lastIndexOf(".");
  if (i < 0) return false;
  const payload = token.slice(0, i);
  if (!safeEqual(token.slice(i + 1), sign(payload))) return false;
  return Number(payload.split(".")[0]) > Date.now();
}

function sessionCookie(value, maxAgeSec) {
  return `${COOKIE}=${value}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAgeSec}${SECURE_COOKIE ? "; Secure" : ""}`;
}

// ---------- promo file ----------
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function istNow() {
  return new Date(Date.now() + 330 * 60_000);
}
function formatIstDate(d = istNow()) {
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}
function parseSiteDate(text) {
  const m = String(text || "").match(/(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})/);
  if (!m) return null;
  const mi = MONTHS.findIndex((x) => x.toLowerCase() === m[2].toLowerCase());
  return mi < 0 ? null : `${m[3]}-${String(mi + 1).padStart(2, "0")}-${m[1].padStart(2, "0")}`;
}
const todayIso = () => istNow().toISOString().slice(0, 10);

const slugify = (name) =>
  name.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

const slotValue = (raw) => {
  const v = (raw || "").trim();
  return v.toLowerCase() === WAITING.toLowerCase() || v.toLowerCase() === "waiting" ? "" : v;
};

/** Same block grammar as assets/js/main.js; duplicate names merge, last block wins, first position kept. */
function readSheet() {
  const text = fs.readFileSync(PROMO_FILE, "utf8");
  const lu = text.match(/^Last Updated:\s*(.+)$/im);
  const bySlug = new Map();
  let duplicates = 0;
  for (const block of text.split(/\n\s*\n/)) {
    const nm = block.match(/Platform name:\s*(.+)/i);
    if (!nm) continue;
    const name = nm[1].trim();
    const get = (label) => {
      const m = block.match(new RegExp(label + "\\s*code:\\s*(.+)", "i"));
      return slotValue(m && m[1]);
    };
    const slug = slugify(name);
    if (bySlug.has(slug)) duplicates += 1;
    bySlug.set(slug, {
      name,
      morning: get("Morning"),
      afternoon: get("Afternoon"),
      evening: get("Evening"),
    });
  }
  const stat = fs.statSync(PROMO_FILE);
  return {
    lastUpdated: lu ? lu[1].trim() : "",
    platforms: [...bySlug.values()],
    duplicates,
    savedAt: stat.mtime.toISOString(),
    today: formatIstDate(),
    stale: parseSiteDate(lu && lu[1]) !== todayIso(),
  };
}

function codeProblem(value, unchanged = false) {
  if (!value) return null;
  if (value.length > MAX_CODE_LENGTH) return `longer than ${MAX_CODE_LENGTH} characters`;
  if (/[\u0000-\u001f\u007f]/.test(value)) return "contains a control character";
  return null;
}

function validatePlatforms(list, existing = new Map()) {
  const errors = [];
  const rows = [];
  const seen = new Set();
  if (!Array.isArray(list) || list.length === 0 || list.length > 300) {
    return { rows, errors: ["Platform list is missing or too long."] };
  }
  for (const p of list) {
    const name = String((p && p.name) || "").trim();
    if (!name || name.length > MAX_NAME_LENGTH || /[\u0000-\u001f\u007f]/.test(name)) {
      errors.push(`Invalid platform name: "${name.slice(0, 50)}"`);
      continue;
    }
    const slug = slugify(name);
    if (!slug) {
      errors.push(`Platform name needs letters or numbers: "${name}"`);
      continue;
    }
    if (seen.has(slug)) {
      errors.push(`Duplicate platform: ${name}`);
      continue;
    }
    seen.add(slug);
    const row = { name };
    for (const slot of ["morning", "afternoon", "evening"]) {
      const v = String((p && p[slot]) || "").trim();
      const prev = existing.get(slug);
      const problem = codeProblem(v, Boolean(prev) && prev[slot] === v);
      if (problem) errors.push(`${name} — ${slot}: ${problem}`);
      row[slot] = v;
    }
    rows.push(row);
  }
  return { rows, errors };
}

function serialize(rows) {
  const blocks = rows.map(
    (r) =>
      `Platform name: ${r.name}\nMorning code: ${r.morning || WAITING}\nAfternoon code: ${r.afternoon || WAITING}\nEvening code: ${r.evening || WAITING}`,
  );
  return `Last Updated: ${formatIstDate()}\n\n${blocks.join("\n\n")}\n`;
}

function backupCurrent() {
  try {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    fs.copyFileSync(PROMO_FILE, path.join(BACKUP_DIR, `promo-codes-${stamp}.txt`));
    const files = fs.readdirSync(BACKUP_DIR).filter((f) => f.startsWith("promo-codes-")).sort();
    for (const f of files.slice(0, Math.max(0, files.length - 60))) {
      fs.unlinkSync(path.join(BACKUP_DIR, f));
    }
  } catch (err) {
    console.warn("backup failed:", err.message);
  }
}

/** Keep files owned by whoever owned them before (the admin may run as root, other jobs as www). */
function ownerOf(file) {
  try {
    const st = fs.statSync(file);
    return { uid: st.uid, gid: st.gid };
  } catch {
    return null;
  }
}
function restoreOwner(file, owner) {
  if (!owner || typeof process.getuid !== "function" || process.getuid() !== 0) return;
  try {
    fs.chownSync(file, owner.uid, owner.gid);
  } catch (err) {
    console.warn("chown failed:", file, err.message);
  }
}

function writeSheet(rows) {
  const owner = ownerOf(PROMO_FILE);
  backupCurrent();
  const tmp = `${PROMO_FILE}.tmp`;
  const mode = (() => {
    try {
      return fs.statSync(PROMO_FILE).mode & 0o777;
    } catch {
      return 0o644;
    }
  })();
  fs.writeFileSync(tmp, serialize(rows), { encoding: "utf8", mode });
  restoreOwner(tmp, owner);
  fs.renameSync(tmp, PROMO_FILE);
}

function rerender() {
  return new Promise((resolve) => {
    const script = path.join(SITE_ROOT, "tools", "render-promo-table.py");
    if (!fs.existsSync(script)) return resolve({ ok: false, message: "render script not found" });
    const pages = ["promo-code/index.html", "index.html"].map((f) => path.join(SITE_ROOT, f));
    const owners = pages.map(ownerOf);
    execFile(RENDER_CMD, [script], { cwd: SITE_ROOT, timeout: 30_000 }, (err, stdout, stderr) => {
      pages.forEach((f, i) => restoreOwner(f, owners[i]));
      if (err) {
        console.warn("render failed:", err.message, stderr);
        return resolve({ ok: false, message: "Saved, but the static pages could not be refreshed." });
      }
      resolve({ ok: true, message: String(stdout).trim() });
    });
  });
}

// ---------- http helpers ----------
const SECURITY_HEADERS = {
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "same-origin",
  "Content-Security-Policy":
    "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
};

function send(res, status, body, type = "text/html; charset=utf-8", extra = {}) {
  res.writeHead(status, { ...SECURITY_HEADERS, "Content-Type": type, ...extra });
  res.end(body);
}
const sendJson = (res, status, obj) => send(res, status, JSON.stringify(obj), "application/json; charset=utf-8");
const redirect = (res, to, extra = {}) => {
  res.writeHead(303, { ...SECURITY_HEADERS, Location: to, ...extra });
  res.end();
};

function readBody(req, limit = 200_000) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (c) => {
      size += c.length;
      if (size > limit) {
        reject(new Error("Body too large"));
        req.destroy();
      } else chunks.push(c);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

/** State-changing requests must come from this host (SameSite=Strict is the first line of defence). */
function sameOrigin(req) {
  const origin = req.headers.origin;
  if (!origin) return true;
  try {
    return new URL(origin).host === req.headers.host;
  } catch {
    return false;
  }
}

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// ---------- pages ----------
const PAGE_STYLE = `
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;background:#f1f5f9;color:#0f172a}
header{background:#0f172a;color:#fff}.bar{max-width:1150px;margin:0 auto;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.bar b span{color:#67e8f9}button,input{font:inherit}main{max-width:1150px;margin:0 auto;padding:20px 16px 90px}
.btn{min-height:40px;border-radius:8px;border:1px solid #cbd5e1;background:#fff;color:#334155;padding:0 14px;cursor:pointer;font-weight:600}
.btn:disabled{opacity:.5;cursor:default}.btn-primary{background:#4f46e5;border-color:#4f46e5;color:#fff}.btn-dark{background:transparent;border-color:#ffffff55;color:#fff;min-height:36px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px}.toolbar{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}
.toolbar label{font-size:14px;font-weight:600;color:#334155;flex:1;min-width:180px}.toolbar input{display:block;width:100%;min-height:40px;margin-top:4px;border:1px solid #cbd5e1;border-radius:8px;padding:0 10px}
.muted{font-size:12px;color:#64748b}.grid{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.grid li.changed{border-color:#f59e0b;box-shadow:0 0 0 1px #fcd34d}.grid h2{font-size:14px;margin:0 0 8px}.slot{display:flex;align-items:center;gap:8px;margin-top:6px}
.slot span{width:76px;font-size:12px;font-weight:600;color:#64748b;flex:none}.slot input{flex:1;min-width:0;min-height:40px;border:1px solid #cbd5e1;border-radius:6px;padding:0 8px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px}
.warn{background:#fffbeb;border:1px solid #fcd34d;color:#78350f;border-radius:10px;padding:12px;margin-bottom:14px;font-size:14px}
.err{color:#b91c1c;font-size:14px}.ok{color:#047857;font-weight:600;font-size:14px}
.save{position:fixed;left:0;right:0;bottom:0;background:#fffffff2;border-top:1px solid #e2e8f0;padding:12px 16px}.save>div{max-width:1150px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.login{max-width:360px;margin:60px auto;padding:0 16px}.login label{display:block;font-size:14px;font-weight:600;margin-top:14px}
.login input{display:block;width:100%;min-height:44px;margin-top:4px;border:1px solid #cbd5e1;border-radius:8px;padding:0 10px}
`;

const shell = (title, inner, authed) => `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>${esc(title)}</title><style>${PAGE_STYLE}</style></head><body>
<header><div class="bar"><b>AllYonoIndia <span>Admin</span></b>${
  authed ? '<form method="post" action="/logout"><button class="btn btn-dark" type="submit">Log out</button></form>' : ""
}</div></header>${inner}</body></html>`;

function loginPage(error, username = "") {
  const body = authConfigured()
    ? `<form method="post" action="/login" autocomplete="on">
<label>Username<input name="username" autocomplete="username" required value="${esc(username)}"></label>
<label>Password<input name="password" type="password" autocomplete="current-password" required></label>
${error ? `<p class="err" role="alert">${esc(error)}</p>` : ""}
<button class="btn btn-primary" style="width:100%;margin-top:18px;min-height:44px" type="submit">Log in</button></form>`
    : `<p class="warn">Admin login is not configured on this server. Set ADMIN_USERNAME, ADMIN_PASSWORD_HASH and ADMIN_SESSION_SECRET (see tools/promo-admin/README.md), then restart.</p>`;
  return shell(
    "Admin log in — AllYonoIndia",
    `<div class="login"><h1 style="margin:0 0 4px;font-size:24px">Admin log in</h1><p class="muted">Restricted area. Authorised administrators only.</p>${body}</div>`,
    false,
  );
}

const editorPage = () =>
  shell(
    "Promo codes — AllYonoIndia Admin",
    `<main><h1 style="margin:0;font-size:24px">Daily promo codes</h1>
<p class="muted" style="font-size:14px">Enter each platform's Morning / Afternoon / Evening code, then press Save. Changes appear on
<a href="${esc(PUBLIC_URL)}/promo-code/" target="_blank" rel="noopener noreferrer">${esc(PUBLIC_URL.replace("https://", ""))}/promo-code/</a> straight away. Empty boxes show "Waiting to Release".</p>
<div id="app" class="muted">Loading…</div></main><script src="/app.js"></script>`,
    true,
  );

// ---------- browser app (served at /app.js, so CSP can forbid inline scripts) ----------
const APP_JS = `(function () {
  var SLOTS = [["morning", "Morning"], ["afternoon", "Afternoon"], ["evening", "Evening"]];
  var app = document.getElementById("app");
  var data, saved, pending = false, result = null, query = "";
  var el = function (tag, props, kids) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (props[k] == null) return;
      if (k === "class") n.className = props[k];
      else if (k === "text") n.textContent = props[k];
      else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), props[k]);
      else n.setAttribute(k, props[k]);
    });
    (kids || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  };
  var clone = function (p) { return p.map(function (x) { return { name: x.name, morning: x.morning, afternoon: x.afternoon, evening: x.evening }; }); };
  var rowDirty = function (a, b) { return !b || a.morning !== b.morning || a.afternoon !== b.afternoon || a.evening !== b.evening; };
  function dirtyCount() {
    var by = {}; saved.forEach(function (s) { by[s.name] = s; });
    return data.platforms.filter(function (p) { return rowDirty(p, by[p.name]); }).length;
  }
  function api(path, body) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Requested-With": "promo-admin" }, body: JSON.stringify(body || {}) })
      .then(function (r) { if (r.status === 401) { location.href = "/login"; throw new Error("auth"); } return r.json(); });
  }
  function finish(r) {
    pending = false; result = r;
    if (r.ok) { data.lastUpdated = r.lastUpdated; data.savedAt = r.savedAt; data.stale = false; saved = clone(data.platforms); }
    render();
  }
  function save() { pending = true; render(); api("/api/save", { platforms: data.platforms }).then(finish).catch(function () { pending = false; render(); }); }
  function newDay() {
    if (!confirm("Start a new day? This clears ALL codes for every platform.")) return;
    pending = true; render();
    api("/api/new-day").then(function (r) { if (r.ok) data.platforms.forEach(function (p) { p.morning = p.afternoon = p.evening = ""; }); finish(r); });
  }
  function addPlatform() {
    var input = document.getElementById("newName"); var name = input.value.trim();
    if (!name) return;
    if (data.platforms.some(function (p) { return p.name.toLowerCase() === name.toLowerCase(); })) { alert("That platform is already in the list."); return; }
    data.platforms.unshift({ name: name, morning: "", afternoon: "", evening: "" });
    query = ""; render();
  }
  function render() {
    var dirty = dirtyCount();
    var filled = data.platforms.filter(function (p) { return p.morning || p.afternoon || p.evening; }).length;
    var by = {}; saved.forEach(function (s) { by[s.name] = s; });
    var children = [];
    var items = [];
    if (data.stale) children.push(el("div", { class: "warn", role: "status" }, [
      "The sheet says ", el("b", { text: "Last Updated: " + (data.lastUpdated || "unknown") }), " but today is ", el("b", { text: data.today }),
      " (IST). Visitors may be seeing old codes — press ", el("b", { text: "Start new day" }), " to clear them."]));
    if (data.duplicates) children.push(el("div", { class: "warn" }, [data.duplicates + " duplicate platform entr" + (data.duplicates === 1 ? "y was" : "ies were") + " merged (the last one wins, matching the live site). Saving cleans the file up."]));
    children.push(el("div", { class: "card toolbar" }, [
      el("label", {}, ["Find a platform", el("input", { type: "search", value: query, "data-search": "1", placeholder: "e.g. spin gold", oninput: function (e) { query = e.target.value.toLowerCase(); filterList(); } })]),
      el("label", {}, ["Add a platform", el("input", { id: "newName", maxlength: "40", placeholder: "Exact name, e.g. Jeet Spin" })]),
      el("button", { class: "btn", type: "button", onclick: addPlatform, text: "Add" }),
      el("button", { class: "btn", type: "button", disabled: pending ? "disabled" : null, onclick: newDay, text: "Start new day" }),
      el("p", { class: "muted", style: "width:100%;margin:0", text: filled + " of " + data.platforms.length + " platforms have a code · Last Updated on site: " + (data.lastUpdated || "—") }),
    ]));
    var list = el("ul", { class: "grid" });
    data.platforms.forEach(function (p) {
      var li = el("li", { class: "card" + (rowDirty(p, by[p.name]) ? " changed" : "") }, [el("h2", { text: p.name })]);
      SLOTS.forEach(function (s) {
        li.appendChild(el("label", { class: "slot" }, [el("span", { text: s[1] }), el("input", {
          type: "text", value: p[s[0]], maxlength: "40", autocomplete: "off", autocapitalize: "off", spellcheck: "false", placeholder: "Waiting to Release",
          oninput: function (e) { p[s[0]] = e.target.value; li.className = "card" + (rowDirty(p, by[p.name]) ? " changed" : ""); status(); }
        })]));
      });
      items.push({ li: li, name: p.name.toLowerCase() });
      list.appendChild(li);
    });
    function filterList() { items.forEach(function (it) { it.li.hidden = Boolean(query) && it.name.indexOf(query) < 0; }); }
    filterList();
    children.push(list);
    var statusEl = el("span", { class: "muted", style: "font-size:14px", "aria-live": "polite" });
    function status() { var d = dirtyCount(); statusEl.textContent = d ? d + " platform" + (d === 1 ? "" : "s") + " changed — not saved yet" : "All changes saved"; saveBtn.disabled = pending || !d; }
    var saveBtn = el("button", { class: "btn btn-primary", type: "button", onclick: save, text: pending ? "Saving…" : "Save changes" });
    var bar = el("div", {}, [saveBtn, statusEl]);
    if (result && result.ok && !dirty) bar.appendChild(el("span", { class: "ok", role: "status", text: "✓ Saved — " + result.live + " platform" + (result.live === 1 ? "" : "s") + " with codes live" + (result.render && !result.render.ok ? " (" + result.render.message + ")" : "") }));
    var save2 = el("div", { class: "save" }, [bar]);
    if (result && !result.ok) {
      var ul = el("ul", { class: "err", role: "alert", style: "margin:8px auto 0;max-width:1150px" });
      (result.errors || ["Save failed."]).forEach(function (e) { ul.appendChild(el("li", { text: e })); });
      save2.appendChild(ul);
    }
    children.push(save2);
    app.textContent = ""; children.forEach(function (c) { app.appendChild(c); });
    status();
  }
  window.addEventListener("beforeunload", function (e) { if (data && dirtyCount()) e.preventDefault(); });
  fetch("/api/sheet", { headers: { "X-Requested-With": "promo-admin" } })
    .then(function (r) { if (r.status === 401) { location.href = "/login"; throw new Error("auth"); } return r.json(); })
    .then(function (d) { data = d; saved = clone(d.platforms); render(); })
    .catch(function (e) { if (e.message !== "auth") app.textContent = "Could not load the promo sheet."; });
})();`;

// ---------- routing ----------
async function handle(req, res) {
  const url = new URL(req.url, "http://localhost");
  const route = `${req.method} ${url.pathname}`;

  if (route === "GET /robots.txt") return send(res, 200, "User-agent: *\nDisallow: /\n", "text/plain");
  if (route === "GET /healthz") return send(res, 200, "ok", "text/plain");

  if (route === "GET /login") {
    return isAuthenticated(req) ? redirect(res, "/") : send(res, 200, loginPage());
  }
  if (route === "POST /login") {
    if (!sameOrigin(req)) return send(res, 403, "Forbidden", "text/plain");
    if (isLockedOut(req)) return send(res, 429, loginPage("Too many failed attempts. Try again in 15 minutes."));
    const form = new URLSearchParams(await readBody(req, 10_000));
    const username = form.get("username") || "";
    const password = form.get("password") || "";
    if (!authConfigured()) return send(res, 200, loginPage());
    // Always run scrypt so response timing doesn't reveal whether the username exists.
    const passOk = verifyPassword(password, process.env.ADMIN_PASSWORD_HASH);
    const userOk = safeEqual(username, process.env.ADMIN_USERNAME);
    if (!(passOk && userOk)) {
      recordFailure(req);
      return send(res, 401, loginPage("Incorrect username or password.", username));
    }
    fails.delete(clientKey(req));
    const payload = `${Date.now() + SESSION_MS}.${crypto.randomBytes(12).toString("base64url")}`;
    return redirect(res, "/", { "Set-Cookie": sessionCookie(`${payload}.${sign(payload)}`, SESSION_MS / 1000) });
  }
  if (route === "POST /logout") {
    if (!sameOrigin(req)) return send(res, 403, "Forbidden", "text/plain");
    return redirect(res, "/login", { "Set-Cookie": sessionCookie("", 0) });
  }

  // everything below needs a session
  if (!isAuthenticated(req)) {
    if (url.pathname.startsWith("/api/")) return sendJson(res, 401, { ok: false, errors: ["Not logged in."] });
    return redirect(res, "/login");
  }

  if (route === "GET /" || route === "GET /promo-codes") return send(res, 200, editorPage());
  if (route === "GET /app.js") return send(res, 200, APP_JS, "application/javascript; charset=utf-8");

  if (url.pathname.startsWith("/api/")) {
    if (req.headers["x-requested-with"] !== "promo-admin" || !sameOrigin(req)) {
      return sendJson(res, 403, { ok: false, errors: ["Forbidden."] });
    }
    if (route === "GET /api/sheet") return sendJson(res, 200, readSheet());

    if (route === "POST /api/save" || route === "POST /api/new-day") {
      let rows;
      if (route === "POST /api/new-day") {
        rows = readSheet().platforms.map((p) => ({ name: p.name, morning: "", afternoon: "", evening: "" }));
      } else {
        let body;
        try {
          body = JSON.parse(await readBody(req));
        } catch {
          return sendJson(res, 400, { ok: false, errors: ["Invalid request."] });
        }
        const current = new Map(readSheet().platforms.map((p) => [slugify(p.name), p]));
        const v = validatePlatforms(body.platforms, current);
        if (v.errors.length) return sendJson(res, 200, { ok: false, errors: v.errors });
        rows = v.rows;
      }
      writeSheet(rows);
      const render = await rerender();
      return sendJson(res, 200, {
        ok: true,
        savedAt: new Date().toISOString(),
        lastUpdated: formatIstDate(),
        live: rows.filter((r) => r.morning || r.afternoon || r.evening).length,
        render,
      });
    }
  }
  return send(res, 404, "Not found", "text/plain");
}

// Always start: under PM2, require.main is PM2's own wrapper, so a `require.main === module`
// guard would leave the process "online" but never listening.
if (!process.env.PROMO_ADMIN_NO_LISTEN) {
  if (!authConfigured()) console.warn("[promo-admin] ADMIN_* settings missing — login is disabled.");
  http
    .createServer((req, res) => {
      handle(req, res).catch((err) => {
        console.error(err);
        if (!res.headersSent) send(res, 500, "Server error", "text/plain");
      });
    })
    .listen(PORT, "127.0.0.1", () =>
      console.log(`[promo-admin] http://127.0.0.1:${PORT}  file=${PROMO_FILE}`),
    );
}

module.exports = { readSheet, validatePlatforms, serialize, slugify, formatIstDate, parseSiteDate };
