"""Download recent reels from the creators someone likes, with a hard spending limit.

usage: python3 scrape.py REEL_DIR --handles name1,name2 [--per 8] [--cap-usd 2] [--dry-run]
  needs APIFY_TOKEN in the environment (from console.apify.com > Settings > API & Integrations)
  writes REEL_DIR/references/reels/<owner>_<date>_<code>.mp4 and references/reels/index.json

Uses apify/instagram-reel-scraper (pay per result). The scraper's own video-download add-on is
expensive, so the video is fetched from the link it returns instead (free).
exit codes: 0 ok · 2 no token · 3 nothing found · 4 estimate over the limit
"""
import json, os, re, sys, urllib.parse, urllib.request

ACTOR = "apify~instagram-reel-scraper"
PRICE_PER_REEL, PRICE_START = 0.0026, 0.001   # highest (free-plan) prices, Nov 2026; check reference/apify.md


def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


reel = sys.argv[1]
handles = [h.strip().lstrip("@").split("/")[-1] or h for h in arg("--handles", "").split(",") if h.strip()]
per, cap = int(arg("--per", "8")), float(arg("--cap-usd", "2"))
token = os.environ.get("APIFY_TOKEN")
if not token:
    print("No Apify token found (APIFY_TOKEN).\n"
          "Either: make a free account at apify.com, copy your API token from Settings > API & Integrations,\n"
          "and set it with:  export APIFY_TOKEN=your_token\n"
          f"Or skip Apify: put screenshots of reels you like in {reel}/references/own/ and continue.")
    sys.exit(2)
if not handles:
    raise SystemExit("Give at least one Instagram handle with --handles")

estimate = PRICE_START + PRICE_PER_REEL * per * len(handles)
print(f"estimate: up to {per * len(handles)} reels from {len(handles)} creator(s), about ${estimate:.2f} (limit ${cap:.2f})")
if estimate > cap:
    print(f"That is over your limit of ${cap:.2f}. Lower --per or raise the limit.")
    sys.exit(4)
if "--dry-run" in sys.argv:
    sys.exit(0)

q = urllib.parse.urlencode({"maxTotalChargeUsd": f"{cap:.2f}", "timeout": 600})
req = urllib.request.Request(f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items?{q}",
                             data=json.dumps({"username": handles, "resultsLimit": per, "skipPinnedPosts": True}).encode(),
                             headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=700) as r:
    items = json.load(r)

out = os.path.join(reel, "references", "reels")
os.makedirs(out, exist_ok=True)
index, missing = [], set(h.lower() for h in handles)
for it in items:
    url, owner, code = it.get("videoUrl"), it.get("ownerUsername", "unknown"), it.get("shortCode", "x")
    if not url:
        continue
    missing.discard(owner.lower())
    name = f"{re.sub(r'[^A-Za-z0-9_.]', '', owner)}_{(it.get('timestamp') or '')[:10]}_{re.sub(r'[^A-Za-z0-9_-]', '', code)}.mp4"
    try:
        urllib.request.urlretrieve(url, os.path.join(out, name))
    except Exception as e:  # Instagram links expire; skip the odd one
        print(f"skipped {code}: {e}")
        continue
    index.append({"owner": owner, "shortCode": code, "duration": it.get("videoDuration"),
                  "plays": it.get("videoPlayCount"), "file": name})
json.dump(index, open(os.path.join(out, "index.json"), "w"), indent=1)
for h in sorted(missing):
    print(f"nothing found for @{h} (private, misspelled, or no reels)")
if not index:
    print(f"No reels downloaded. Check the handles, or put screenshots in {reel}/references/own/ instead.")
    sys.exit(3)
print(f"downloaded {len(index)} reels to {out}")
