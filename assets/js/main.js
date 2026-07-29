/* All Yono India — minimal vanilla JS. No frameworks, no tracking. */
(function () {
  "use strict";

  /* Mobile menu toggle */
  var toggle = document.querySelector(".hamburger");
  var mobileNav = document.querySelector(".mobile-nav");
  if (toggle && mobileNav) {
    toggle.addEventListener("click", function () {
      var open = mobileNav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    mobileNav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        mobileNav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* Coming-soon countdown timers for upcoming-game cards, e.g. a future
     unreleased-title card that follows the same [data-countdown] markup */
  var countdowns = document.querySelectorAll("[data-countdown]");
  if (countdowns.length) {
    var pad2 = function (n) { return n < 10 ? "0" + n : String(n); };
    var tickCountdowns = function () {
      countdowns.forEach(function (el) {
        var target = new Date(el.getAttribute("data-countdown")).getTime();
        var diff = Math.max(0, target - Date.now());
        var days = Math.floor(diff / 86400000);
        var hours = Math.floor((diff % 86400000) / 3600000);
        var minutes = Math.floor((diff % 3600000) / 60000);
        var seconds = Math.floor((diff % 60000) / 1000);
        var setUnit = function (unit, value) {
          var node = el.querySelector('[data-unit="' + unit + '"]');
          if (node) node.textContent = pad2(value);
        };
        setUnit("days", days);
        setUnit("hours", hours);
        setUnit("minutes", minutes);
        setUnit("seconds", seconds);
      });
    };
    tickCountdowns();
    setInterval(tickCountdowns, 1000);
  }

  /* Copy promo code buttons (event delegation so it also works on rows rendered later from JSON) */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".copy-btn[data-code]");
    if (!btn) return;
    var code = btn.getAttribute("data-code");
    if (!code) return;
    var done = function () {
      var original = btn.textContent;
      btn.textContent = "Copied";
      btn.classList.add("is-copied");
      setTimeout(function () {
        btn.textContent = original;
        btn.classList.remove("is-copied");
      }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).then(done).catch(done);
    } else {
      var temp = document.createElement("textarea");
      temp.value = code;
      document.body.appendChild(temp);
      temp.select();
      try { document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(temp);
      done();
    }
  });

  /* Game directory search + category filter (operates on existing static cards) */
  var searchInput = document.getElementById("gameSearch");
  var chips = document.querySelectorAll(".chip[data-filter]");
  var cards = document.querySelectorAll(".game-card[data-name]");
  var resultsCount = document.getElementById("resultsCount");
  var noResults = document.getElementById("noResults");
  var activeFilter = "all";

  function applyFilters() {
    if (!cards.length) return;
    var query = (searchInput && searchInput.value || "").trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (card) {
      var name = (card.getAttribute("data-name") || "").toLowerCase();
      var category = card.getAttribute("data-category") || "";
      var matchesQuery = !query || name.indexOf(query) !== -1;
      var matchesFilter = activeFilter === "all" || category === activeFilter;
      var show = matchesQuery && matchesFilter;
      card.style.display = show ? "" : "none";
      if (show) visible++;
    });
    if (resultsCount) {
      resultsCount.textContent = visible + (visible === 1 ? " game found" : " games found");
    }
    if (noResults) {
      noResults.classList.toggle("is-visible", visible === 0);
    }
  }

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }
  if (chips.length) {
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");
        activeFilter = chip.getAttribute("data-filter") || "all";
        applyFilters();
      });
    });
    var categoryParam = new URLSearchParams(window.location.search).get("category");
    if (categoryParam) {
      var matchedChip = document.querySelector('.chip[data-filter="' + categoryParam + '"]');
      if (matchedChip) {
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        matchedChip.classList.add("is-active");
        activeFilter = categoryParam;
      }
    }
  }
  if (searchInput || chips.length) {
    applyFilters();
  }

  /* Live search against Strapi (additive — the static-card filter above always
     runs first and keeps working even if this fetch fails or Strapi is down).
     Only adds cards for games that aren't already present as static cards,
     e.g. a brand-new game added in the CMS before the next page regeneration. */
  var STRAPI_API_BASE = "https://api.allyonoindia.com";
  var gameGrid = document.querySelector(".game-grid");
  var liveSearchTimer = null;

  function clearLiveCards() {
    if (!gameGrid) return;
    gameGrid.querySelectorAll('.game-card[data-source="live"]').forEach(function (el) {
      el.parentNode.removeChild(el);
    });
  }

  function catLabel(cat) {
    var labels = { slots: "Slots", rummy: "Rummy", arcade: "Arcade", casual: "Casual", "card-games": "Card Games", sports: "Sports" };
    return labels[cat] || cat;
  }

  function renderLiveCard(game) {
    var el = document.createElement("article");
    el.className = "game-card";
    el.setAttribute("data-name", game.name);
    el.setAttribute("data-category", game.category);
    el.setAttribute("data-source", "live");
    var pills = (game.statuses || [])
      .map(function (s) { return '<span class="status-pill status-' + s[0] + '">' + s[1] + "</span>"; })
      .join("");
    el.innerHTML =
      '<a class="game-card-top" href="/all-yono-games/' + game.slug + '/" style="text-decoration:none">' +
      '<span class="game-icon"><img src="' + game.img + '" alt="' + game.name + ' logo" width="52" height="52" loading="lazy"></span>' +
      "<div><h3 class=\"game-name\">" + game.name + '</h3><span class="game-category">' + catLabel(game.category) + "</span></div></a>" +
      '<div class="status-row">' + pills + "</div>" +
      '<ul class="meta-list"><li>Promo Code: <b>' + game.promo_status + "</b></li></ul>" +
      '<div class="card-actions">' +
      '<a class="btn btn-cyan btn-sm" href="' + game.download_url + '" target="_blank" rel="nofollow noopener noreferrer">Download URL</a>' +
      '<a class="btn btn-ghost btn-sm" href="/promo-code/#' + game.slug + '">Check Code</a>' +
      "</div>" +
      '<p class="access-note">Login inside app only</p>';
    return el;
  }

  function liveSearch(query, category) {
    if (!gameGrid || !query) {
      clearLiveCards();
      return;
    }
    var url = STRAPI_API_BASE + "/api/games?filters[name][$containsi]=" + encodeURIComponent(query);
    if (category && category !== "all") {
      url += "&filters[category][$eq]=" + encodeURIComponent(category);
    }
    fetch(url)
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (body) {
        if (!body) return;
        clearLiveCards();
        var existingNames = Array.prototype.map.call(cards, function (c) {
          return (c.getAttribute("data-name") || "").toLowerCase();
        });
        var added = 0;
        body.data.forEach(function (game) {
          if (existingNames.indexOf(game.name.toLowerCase()) !== -1) return;
          gameGrid.appendChild(renderLiveCard(game));
          added++;
        });
        if (added && resultsCount) {
          var currentVisible = parseInt(resultsCount.textContent, 10) || 0;
          resultsCount.textContent = (currentVisible + added) + " games found";
        }
      })
      .catch(function () {
        /* Strapi unreachable — static-card search above already covers the page, nothing else to do. */
      });
  }

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      clearTimeout(liveSearchTimer);
      liveSearchTimer = setTimeout(function () {
        liveSearch(searchInput.value.trim(), activeFilter);
      }, 300);
    });
  }

  /* Promo Code page: search + Active / Waiting to Release filter (rows are injected from JSON, see loadPromoCodes below) */
  var promoSearch = document.getElementById("promoSearch");
  var promoChips = document.querySelectorAll(".chip[data-status-filter]");
  var promoResultsCount = document.getElementById("promoResultsCount");
  var promoNoResults = document.getElementById("promoNoResults");
  var activeStatusFilter = "all";

  function applyPromoFilters() {
    var promoRows = document.querySelectorAll(".promo-table tr[data-name]");
    if (!promoRows.length) return;
    var query = (promoSearch && promoSearch.value || "").trim().toLowerCase();
    var visible = 0;
    promoRows.forEach(function (row) {
      var name = (row.getAttribute("data-name") || "").toLowerCase();
      var status = row.getAttribute("data-status") || "";
      var matchesQuery = !query || name.indexOf(query) !== -1;
      var matchesFilter = activeStatusFilter === "all" || status === activeStatusFilter;
      var show = matchesQuery && matchesFilter;
      row.style.display = show ? "" : "none";
      if (show) visible++;
    });
    if (promoResultsCount) {
      promoResultsCount.textContent = visible + (visible === 1 ? " code found" : " codes found");
    }
    if (promoNoResults) {
      promoNoResults.classList.toggle("is-visible", visible === 0);
    }
  }

  if (promoSearch) {
    promoSearch.addEventListener("input", applyPromoFilters);
  }
  if (promoChips.length) {
    promoChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        promoChips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");
        activeStatusFilter = chip.getAttribute("data-status-filter") || "all";
        applyPromoFilters();
      });
    });
  }

  /* Render promo code tables from /assets/data/promo-codes.txt so codes can be updated by editing one plain-text file */
  function escapeHtml(str) {
    return String(str == null ? "" : str).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var PROMO_STATUS_WORDS = {
    "checking": { status: "checking", label: "Checking" },
    "waiting to release": { status: "waiting", label: "Waiting to Release" },
    "waiting": { status: "waiting", label: "Waiting to Release" },
    "active": { status: "active", label: "Active" },
    "unavailable": { status: "unavailable", label: "Unavailable" }
  };

  function slugifyGameName(name) {
    return name.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function parsePromoSlot(raw) {
    var key = (raw || "").trim().toLowerCase();
    var known = PROMO_STATUS_WORDS[key];
    if (known) return { type: "status", status: known.status, label: known.label };
    return { type: "code", value: (raw || "").trim() };
  }

  function parsePromoText(text) {
    var lastUpdatedMatch = text.match(/^Last Updated:\s*(.+)$/im);
    var games = [];
    text.split(/\n\s*\n/).forEach(function (block) {
      var nameMatch = block.match(/Platform name:\s*(.+)/i);
      if (!nameMatch) return;
      var morningMatch = block.match(/Morning code:\s*(.+)/i);
      var afternoonMatch = block.match(/Afternoon code:\s*(.+)/i);
      var eveningMatch = block.match(/Evening code:\s*(.+)/i);
      var name = nameMatch[1].trim();
      var morning = parsePromoSlot(morningMatch && morningMatch[1]);
      var afternoon = parsePromoSlot(afternoonMatch && afternoonMatch[1]);
      var evening = parsePromoSlot(eveningMatch && eveningMatch[1]);
      var status = (morning.type === "code" || afternoon.type === "code" || evening.type === "code") ? "active" : "waiting";
      games.push({
        slug: slugifyGameName(name),
        name: name,
        status: status,
        morning: morning,
        afternoon: afternoon,
        evening: evening
      });
    });
    return { lastUpdated: lastUpdatedMatch ? lastUpdatedMatch[1].trim() : "", games: games };
  }

  function buildPromoCell(label, cell) {
    if (cell && cell.type === "code") {
      var code = escapeHtml(cell.value);
      return '<td data-label="' + label + '"><span class="code-cell"><span class="code-value">' + code + '</span><button class="copy-btn" data-code="' + code + '" type="button">Copy</button></span></td>';
    }
    var status = cell && cell.status ? cell.status : "waiting";
    var pillLabel = cell && cell.label ? cell.label : "Waiting to Release";
    return '<td data-label="' + label + '"><span class="status-pill status-' + status + '">' + escapeHtml(pillLabel) + "</span></td>";
  }

  function buildPromoRow(game) {
    var name = escapeHtml(game.name);
    return '<tr id="' + game.slug + '" data-name="' + name + '" data-status="' + game.status + '">' +
      '<td data-label="Game"><span class="promo-game-cell"><img src="/assets/images/games/' + game.slug + '.webp" alt="' + name + ' logo" width="30" height="30" loading="lazy" onerror="this.style.display=\'none\'">' + name + "</span></td>" +
      buildPromoCell("Morning", game.morning) +
      buildPromoCell("Afternoon", game.afternoon) +
      buildPromoCell("Evening", game.evening) +
      '<td data-label="Action"><a class="btn btn-outline btn-sm" href="/all-yono-games/' + game.slug + '/">View Game</a></td>' +
      "</tr>";
  }

  /* Maps Strapi's PromoCode + PromoMeta records into the same {lastUpdated, games}
     shape parsePromoText() already produces, so buildPromoRow()/buildPromoCell()
     below don't need to know which source the data came from. */
  function parsePromoFromStrapi(promoCodesBody, metaBody) {
    var games = (promoCodesBody.data || []).map(function (pc) {
      var g = pc.game || {};
      var morning = parsePromoSlot(pc.morning_code);
      var afternoon = parsePromoSlot(pc.afternoon_code);
      var evening = parsePromoSlot(pc.evening_code);
      return {
        slug: g.slug || slugifyGameName(g.name || ""),
        name: g.name || "",
        status: (morning.type === "code" || afternoon.type === "code" || evening.type === "code") ? "active" : "waiting",
        morning: morning,
        afternoon: afternoon,
        evening: evening
      };
    });
    return { lastUpdated: (metaBody.data && metaBody.data.last_updated_label) || "", games: games };
  }

  function fetchPromoDataFromStrapi() {
    return Promise.all([
      fetch(STRAPI_API_BASE + "/api/promo-codes?populate=game&pagination[pageSize]=100").then(function (res) {
        if (!res.ok) throw new Error("promo-codes fetch failed");
        return res.json();
      }),
      fetch(STRAPI_API_BASE + "/api/promo-meta").then(function (res) {
        if (!res.ok) throw new Error("promo-meta fetch failed");
        return res.json();
      })
    ]).then(function (results) {
      return parsePromoFromStrapi(results[0], results[1]);
    });
  }

  /* Falls back to the plain-text file (still kept up to date in parallel during the
     Strapi transition period) if api.allyonoindia.com is unreachable, so the page
     keeps working either way. */
  function fetchPromoDataFromTextFile() {
    return fetch("/assets/data/promo-codes.txt")
      .then(function (res) { return res.text(); })
      .then(function (text) { return parsePromoText(text); });
  }

  /* Static row for DhanGame, which just launched and isn't in Strapi/promo-codes.txt yet,
     so it still surfaces at the top of the Promo Code page ahead of the next CMS sync. */
  function buildDhanGameRow() {
    var checking = '<span class="status-pill status-checking">Checking</span>';
    return '<tr id="dhan-game" data-name="DhanGame" data-status="waiting">' +
      '<td data-label="Game"><span class="promo-game-cell"><img src="/assets/images/games/dhan-game.webp" alt="DhanGame logo" width="30" height="30" loading="lazy" onerror="this.style.display=\'none\'">DhanGame</span></td>' +
      '<td data-label="Morning">' + checking + '</td>' +
      '<td data-label="Afternoon">' + checking + '</td>' +
      '<td data-label="Evening">' + checking + '</td>' +
      '<td data-label="Action"><a class="btn btn-outline btn-sm" href="/all-yono-games/dhan-game/">View Game</a></td>' +
      '</tr>';
  }

  /* Static row for Win Rummy, which just launched and isn't in Strapi/promo-codes.txt yet,
     so it still surfaces at the top of the Promo Code page ahead of the next CMS sync. */
  function buildWinRummyRow() {
    var checking = '<span class="status-pill status-checking">Checking</span>';
    return '<tr id="win-rummy" data-name="Win Rummy" data-status="waiting">' +
      '<td data-label="Game"><span class="promo-game-cell"><img src="/assets/images/games/win-rummy.webp" alt="Win Rummy logo" width="30" height="30" loading="lazy" onerror="this.style.display=\'none\'">Win Rummy</span></td>' +
      '<td data-label="Morning">' + checking + '</td>' +
      '<td data-label="Afternoon">' + checking + '</td>' +
      '<td data-label="Evening">' + checking + '</td>' +
      '<td data-label="Action"><a class="btn btn-outline btn-sm" href="/all-yono-games/win-rummy/">View Game</a></td>' +
      '</tr>';
  }

  var promoTableBody = document.getElementById("promoTableBody");
  var promoPreviewBody = document.getElementById("promoPreviewBody");

  if (promoTableBody || promoPreviewBody) {
    fetchPromoDataFromStrapi()
      .catch(fetchPromoDataFromTextFile)
      .then(function (data) {
        var games = data.games || [];
        var bySlug = {};
        games.forEach(function (g) { bySlug[g.slug] = g; });

        document.querySelectorAll("#promoLastUpdated").forEach(function (el) {
          el.textContent = data.lastUpdated || "—";
        });

        if (promoTableBody) {
          promoTableBody.innerHTML = buildWinRummyRow() + buildDhanGameRow() + games.map(buildPromoRow).join("");
          applyPromoFilters();
          if (window.location.hash) {
            var target = document.getElementById(window.location.hash.slice(1));
            if (target) target.scrollIntoView({ block: "center" });
          }
        }

        if (promoPreviewBody) {
          var slugs = (promoPreviewBody.getAttribute("data-slugs") || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
          var rows = slugs.map(function (slug) { return bySlug[slug]; }).filter(Boolean);
          promoPreviewBody.innerHTML = rows.map(buildPromoRow).join("");
        }
      })
      .catch(function () {
        document.querySelectorAll(".promo-loading-row td").forEach(function (td) {
          td.textContent = "Could not load promo codes right now. Please refresh the page.";
        });
      });
  }

  /* Highlight active bottom nav + main nav link by current path */
  var path = window.location.pathname.replace(/\/index\.html$/, "/");
  document.querySelectorAll("[data-nav-link]").forEach(function (link) {
    var href = link.getAttribute("href");
    if (!href) return;
    if (href === path || (href !== "/" && path.indexOf(href) === 0)) {
      link.classList.add("is-active");
    }
  });
})();
