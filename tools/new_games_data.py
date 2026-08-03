"""
Data source for generate-static-games.py — the manual, Strapi-free workflow for
adding new All Yono game pages. Add one dict per new game below, run the
generator, review `git diff`, then commit/push as usual.

Each dict:
    name          Display name, e.g. "Win Rummy"
    slug          URL slug, e.g. "win-rummy" -> /all-yono-games/win-rummy/
    category      One of: slots, rummy, arcade, casual, card-games, sports
    description   One or two sentences shown on the game page
    statuses      List of (pill_class, label) tuples shown as status pills.
                  Common combinations already used on the site:
                    [("new", "NEW"), ("active", "DL: Available")]
                    [("active", "Active"), ("active", "DL: Available")]
                  Pill classes in use: new, active, checking, waiting
    promo_status  Text shown next to "Promo Code:", e.g. "Checking" or "Active"
    updated       ISO date the listing was last checked, e.g. "2026-08-02"
    img           Path to the game's icon, e.g. "/assets/images/games/win-rummy.webp"
    download_url  Outbound APK/download link

This does NOT touch all-yono-games/index.html (the listing grid) or the
rummy/arcade category pages — add the new game's card to those by hand, the
same way blog posts get added to blog/index.html one card at a time.
"""

NEW_GAMES = [
    # {
    #     "name": "Example Game",
    #     "slug": "example-game",
    #     "category": "rummy",
    #     "description": "Example Game download link, access status, and promo code — checked and updated on the All Yono India directory.",
    #     "statuses": [("new", "NEW"), ("active", "DL: Available")],
    #     "promo_status": "Checking",
    #     "updated": "2026-08-02",
    #     "img": "/assets/images/games/example-game.webp",
    #     "download_url": "https://example.com/download",
    # },
]
