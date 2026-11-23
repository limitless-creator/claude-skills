# Reference reels with Apify

Apify is a paid web-scraping service with a free monthly credit. Reel Studio uses it to download a few recent reels from creators the person likes, so they can say yes or no to the frames.

## Before anything runs

1. Ask for the spending limit in plain words: "Downloading reels costs a few cents on Apify. What's the most you want to spend on this? I suggest $2." Never run without a number.
2. Run the dry run first and show the estimate:
   `python3 scripts/scrape.py REEL_DIR --handles a,b,c --per 8 --cap-usd 2 --dry-run`
3. Only then run without `--dry-run`. The limit is also sent to Apify (`maxTotalChargeUsd`), so Apify itself stops the run at the limit.

## The actor

- `apify/instagram-reel-scraper`, pay per result.
- Prices (checked 23 Nov 2026, highest tier = free plan): $0.0026 per reel + $0.001 per run. 3 creators × 8 reels ≈ $0.06.
- Input used: `{"username": [handles], "resultsLimit": per, "skipPinnedPosts": true}`.
- Do **not** turn on `includeDownloadedVideo` (charged per MB, easily $0.10+ per reel) or `includeTranscript`. `scrape.py` downloads the video from the returned `videoUrl` for free.
- If prices change, update `PRICE_PER_REEL` / `PRICE_START` in `scrape.py`. Check with the Apify MCP `fetch-actor-details` (pricing) when it's connected.

## Getting a token

1. Free account at https://apify.com.
2. Console → Settings → API & Integrations → copy the personal API token.
3. In the terminal Claude Code runs in: `export APIFY_TOKEN=...` (or add it to `~/.zshrc`). Never write the token into any file in the reel folder, and never repeat it in chat.

If the Apify MCP connector is connected instead, the same actor and input work through it: call it with the same input and the same `maxTotalChargeUsd`, then download each `videoUrl` into `references/reels/` and write `index.json` like `scrape.py` does.

## Fallbacks (the picker works the same)

- No account or no wish to pay: the person drops screenshots of reels they like into `references/own/`. Ten to twenty screenshots is plenty.
- A handle returns nothing (private, misspelled, no reels): `scrape.py` says which. Ask for another creator or use screenshots.
- `frames.py` always includes screenshots, so mixing both is fine.

## Respect

Reference reels are only used on the person's own computer to learn their taste. Never repost them, never copy their graphics, names or catchphrases. Learn patterns only.
