"""
One-time migration: import assets/data/promo-codes.txt into Strapi's
`PromoCode` collection (linked to each Game by name) and the `PromoMeta`
single type (the global "Last Updated" label). Safe to re-run.

Usage:
    cd tools
    pip install -r requirements.txt
    cp .env.example .env   # then fill in STRAPI_API_URL / STRAPI_API_TOKEN
    python import-promo-codes.py
"""
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

STRAPI_API_URL = os.environ.get("STRAPI_API_URL", "http://localhost:1337")
STRAPI_API_TOKEN = os.environ.get("STRAPI_API_TOKEN")
PROMO_TXT_PATH = "../assets/data/promo-codes.txt"

if not STRAPI_API_TOKEN:
    sys.exit("STRAPI_API_TOKEN is not set. Copy .env.example to .env and fill it in.")

HEADERS = {
    "Authorization": f"Bearer {STRAPI_API_TOKEN}",
    "Content-Type": "application/json",
}

LAST_UPDATED_RE = re.compile(r"Last Updated:\s*(.+)")
BLOCK_RE = re.compile(
    r"Platform name:\s*(.+?)\s*\n"
    r"Morning code:\s*(.*?)\s*\n"
    r"Afternoon code:\s*(.*?)\s*\n"
    r"Evening code:\s*(.*?)\s*(?:\n|$)"
)


def find_game_by_name(name):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/games",
        headers=HEADERS,
        params={"filters[name][$eq]": name},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def find_existing_promo(game_document_id):
    resp = requests.get(
        f"{STRAPI_API_URL}/api/promo-codes",
        headers=HEADERS,
        params={"filters[game][documentId][$eq]": game_document_id},
    )
    resp.raise_for_status()
    items = resp.json()["data"]
    return items[0] if items else None


def upsert_promo_meta(label):
    payload = {"data": {"last_updated_label": label}}
    resp = requests.put(f"{STRAPI_API_URL}/api/promo-meta", headers=HEADERS, json=payload)
    resp.raise_for_status()


def main():
    text = open(PROMO_TXT_PATH, encoding="utf-8").read()

    last_updated_match = LAST_UPDATED_RE.search(text)
    if last_updated_match:
        upsert_promo_meta(last_updated_match.group(1).strip())
        print(f"PromoMeta last_updated_label set to: {last_updated_match.group(1).strip()}")

    created, updated, missing = 0, 0, []
    for match in BLOCK_RE.finditer(text):
        name, morning, afternoon, evening = (g.strip() for g in match.groups())
        game = find_game_by_name(name)
        if not game:
            missing.append(name)
            continue

        payload = {
            "data": {
                "game": game["documentId"],
                "morning_code": morning,
                "afternoon_code": afternoon,
                "evening_code": evening,
            }
        }

        existing = find_existing_promo(game["documentId"])
        if existing:
            resp = requests.put(
                f"{STRAPI_API_URL}/api/promo-codes/{existing['documentId']}",
                headers=HEADERS,
                json=payload,
            )
            updated += 1
        else:
            resp = requests.post(f"{STRAPI_API_URL}/api/promo-codes", headers=HEADERS, json=payload)
            created += 1

        if not resp.ok:
            print(f"FAILED on {name}: {resp.status_code} {resp.text}")
            resp.raise_for_status()

    print(f"Done. Created {created}, updated {updated}.")
    if missing:
        print(f"WARNING: no matching Game found for: {missing}")


if __name__ == "__main__":
    main()
