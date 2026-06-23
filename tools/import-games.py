"""
One-time migration: import the 52 games from the old scratch JSON files
(c:/tmp/game-pages-data.json + c:/tmp/game-descriptions.json) into Strapi's
`Game` collection type. Safe to re-run — it upserts by slug.

Usage:
    cd tools
    pip install -r requirements.txt
    cp .env.example .env   # then fill in STRAPI_API_URL / STRAPI_API_TOKEN
    python import-games.py
"""
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")

GAME_DATA_PATH = "c:/tmp/game-pages-data.json"
DESCRIPTIONS_PATH = "c:/tmp/game-descriptions.json"

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}


def find_existing(slug):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/games",
        headers=HEADERS,
        params={"filters[slug][$eq]": slug},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def main():
    games = json.load(open(GAME_DATA_PATH, encoding="utf-8"))
    descriptions = {d["slug"]: d["description"] for d in json.load(open(DESCRIPTIONS_PATH, encoding="utf-8"))}

    created, updated = 0, 0
    for game in games:
        payload = {
            "data": {
                "name": game["name"],
                "slug": game["slug"],
                "category": game["category"],
                "img": game["img"],
                "download_url": game["url"],
                "statuses": game["statuses"],
                "promo_status": game["promo"],
                "description": descriptions.get(game["slug"], ""),
            }
        }

        existing = find_existing(game["slug"])
        if existing:
            resp = requests.put(
                f"{STRAPI_API_URL}/api/games/{existing['documentId']}",
                headers=HEADERS,
                json=payload,
            )
            updated += 1
        else:
            resp = requests.post(f"{STRAPI_API_URL}/api/games", headers=HEADERS, json=payload)
            created += 1

        if not resp.ok:
            print(f"FAILED on {game['slug']}: {resp.status_code} {resp.text}")
            resp.raise_for_status()

    print(f"Done. Created {created}, updated {updated}, total {len(games)} games.")


if __name__ == "__main__":
    main()
