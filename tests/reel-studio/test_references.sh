#!/bin/bash
# frames.py on a fixture video + 2 screenshots; scrape.py refuses cleanly without a token.
set -euo pipefail
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")" && pwd); S="$HERE/../../reel-studio/scripts"
R=$(mktemp -d)/reel; mkdir -p "$R/references/reels" "$R/references/own"
ffmpeg -v error -f lavfi -i "testsrc2=size=720x1280:rate=30:duration=12" -c:v libx264 -pix_fmt yuv420p "$R/references/reels/someone_2026-01-01_ABC.mp4"
ffmpeg -v error -f lavfi -i "color=c=red:size=720x1280" -frames:v 1 "$R/references/own/shot1.png"
ffmpeg -v error -f lavfi -i "color=c=blue:size=720x1280" -frames:v 1 "$R/references/own/shot2.jpg"
"$PY" "$S/frames.py" "$R" --every 2 --max 5 > /dev/null
"$PY" - "$R" <<'PYEOF'
import json, os, sys
r = sys.argv[1]; d = json.load(open(f"{r}/answers/references.data.json"))
assert d["mode"] == "yesno" and 3 <= len(d["items"]) <= 5, len(d["items"])
assert all(os.path.exists(os.path.join(r, it["img"])) for it in d["items"])
assert len({it["id"] for it in d["items"]}) == len(d["items"])
assert any(it["caption"].startswith("your screenshot") for it in d["items"]), "screenshots must always be included"
print("frames ok")
PYEOF
set +e; env -u APIFY_TOKEN "$PY" "$S/scrape.py" "$R" --handles natgeo --dry-run > "$R/out.txt" 2>&1; code=$?; set -e
[[ $code == 2 ]] || { echo "FAIL: expected exit 2, got $code"; cat "$R/out.txt"; exit 1; }
grep -qi "screenshot" "$R/out.txt" || { echo "FAIL: no screenshot fallback hint"; exit 1; }
APIFY_TOKEN=x "$PY" "$S/scrape.py" "$R" --handles a,b,c --per 10 --cap-usd 0.01 --dry-run > "$R/out.txt" 2>&1 && { echo "FAIL: should refuse over cap"; exit 1; }
grep -q "over your limit" "$R/out.txt" || { echo "FAIL: over-cap message"; cat "$R/out.txt"; exit 1; }
APIFY_TOKEN=x "$PY" "$S/scrape.py" "$R" --handles a,b,c --per 10 --cap-usd 2 --dry-run | grep -q "estimate" || { echo "FAIL: dry run estimate"; exit 1; }
echo "ALL PASS"
