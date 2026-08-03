HOW TO UPDATE PROMO CODES (3x a day: morning / afternoon / evening)
====================================================================

Edit ONLY this file: assets/data/promo-codes.txt
Then save and upload it. Nothing else needs to change.

It's a plain text list, one block per game:

    Platform name: Yono 777
    Morning code: AYIYONO77
    Afternoon code: Checking
    Evening code: Waiting to Release

RULES
-----
1. Update the "Last Updated:" line at the very top of the file each time you edit, e.g.:
     Last Updated: 20 Jun 2026, Afternoon IST

2. For each game block, just type whatever is true for that time slot:
   - If a real code exists, type the code itself, e.g.:  Morning code: AYIYONO77
     -> the website shows it with a Copy button automatically.
   - If no code exists yet, type one of these exact words instead:
       Checking
       Waiting to Release
     -> the website shows it as a colored status badge instead of a code (no Copy button).

3. Do NOT rename the "Platform name" — it must match the game name exactly as it
   already appears on the site (the website uses this name to find the right game
   logo and page link). Don't add new games or delete game blocks here; that still
   needs a request to Claude.

4. Keep one blank line between each game block, like in the example above. That blank
   line is how the website knows where one game ends and the next one starts.

5. Plain text only — no quotes, no commas, no special formatting needed. Any text
   editor works (Notepad is fine).

That's it. Both the homepage preview and the full Promo Code page read from this one
file automatically — you never need to touch any .html file for daily code updates.

Codes still show up live the instant you save this file — the page fetches it directly
in the visitor's browser, same as always. Separately, run `python3 tools/render-promo-table.py`
(or `bash tools/publish.sh`, which does this plus the game/blog regeneration) whenever
convenient — once a day is plenty — to bake the current codes into the page's raw HTML
too, so search engines see real content instead of a "Loading..." placeholder. Skipping
it for a few updates doesn't break anything for visitors, it just means Google sees a
slightly older snapshot of the table until you next run it.
