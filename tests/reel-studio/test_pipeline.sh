#!/bin/bash
# End-to-end test of the footage scripts on the fixture. usage: PY=/path/to/python tests/test_pipeline.sh
set -euo pipefail
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")" && pwd); S="$HERE/../../reel-studio/scripts"
R=$(mktemp -d)/reel; "$HERE/make_fixture.sh" "$R" >/dev/null
fail() { echo "FAIL: $*"; exit 1; }

"$PY" "$S/prep.py" "$R" > "$R/prep.log"
W="$R/work"
"$PY" - "$W" <<'PYEOF' || exit 1
import json, subprocess, sys
w = sys.argv[1]; s = json.load(open(f"{w}/source.json"))
assert s["fps"] == 30, f"RF1 fps {s['fps']}"
assert [f["voice_channel"] for f in s["files"]] == ["mix", "L"], f"RF2 channels {s['files']}"
d = lambda st: float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", st, "-show_entries", "stream=duration", "-of", "csv=p=0", f"{w}/source.mp4"], capture_output=True, text=True).stdout)
assert abs(d("v:0") - d("a:0")) < 0.05, f"RF1 drift v={d('v:0')} a={d('a:0')}"
print("prep ok")
PYEOF

"$PY" "$S/analyze.py" "$W" > "$R/analyze.log"
# remove the retake: the phrase where the speaker says "let me say that again"
"$PY" - "$W" <<'PYEOF'
import json, re, sys
w = sys.argv[1]
idx = [int(re.match(r"\[\s*(\d+)\]", l).group(1)) for l in open(f"{w}/phrases.txt")]
txt = [l for l in open(f"{w}/phrases.txt")]
k = next(n for n, l in enumerate(txt) if "say that again" in l.lower())
rm = [[idx[k], idx[k + 1] - 1, "retake"]]
json.dump({"fps": 30, "pacing": "natural", "end_hold": 0.8, "remove_words": rm}, open(f"{w}/job.json", "w"))
PYEOF
"$PY" "$S/edl.py" "$W" > "$R/edl.log"
"$PY" "$S/qa.py" "$W" > /dev/null
"$PY" - "$W" "$R/script.txt" <<'PYEOF'
import re, sys
qa = re.sub(r"[^a-z ]", " ", open(f"{sys.argv[1]}/qa_transcript.txt").read().lower())
qa = " ".join(qa.split())
assert "again" not in qa and qa.count("that takes") == 1, f"retake still in: {qa}"
for line in open(sys.argv[2]):
    words = " ".join(re.sub(r"[^a-z ]", " ", line.lower()).split()[:3])
    assert words in qa, f"missing line start '{words}' in: {qa}"
import json
wt = json.load(open(f"{sys.argv[1]}/words_tl.json")); job = json.load(open(f"{sys.argv[1]}/job.json"))
gone = {i for a, b, _ in job["remove_words"] for i in range(a, b + 1)}
missing = [w["w"] for w in wt if w["i"] not in gone and (w["s"] is None or w["e"] is None)]
assert not missing, f"kept words without times (captions would skip them): {missing}"
print("cut ok")
PYEOF
"$PY" "$S/render_cut.py" "$W" "$R/cut.mp4" 1.0 > /dev/null
[[ $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$R/cut.mp4") == "1080,1920" ]] || fail "RF3 size"
"$S/finish.sh" "$R/cut.mp4" "$R/final.mp4" 1.15 > /dev/null
[[ -z $("$PY" "$S/find_glitches.py" "$R/final.mp4") ]] || fail "glitch frames"
"$PY" "$S/find_glitches.py" --selftest
echo "ALL PASS ($R)"
