#!/bin/bash
# Renders the Remotion starter on the fixture cut: 3 stills (wide, left, right) + a full render without broken frames.
# usage: PY=... [NODE_MODULES=/path/to/node_modules] tests/test_remotion.sh   (without NODE_MODULES it runs npm install)
set -euo pipefail
PY=${PY:-python3}
HERE=$(cd "$(dirname "$0")" && pwd); SK="$HERE/../../reel-studio"
R=$(mktemp -d)/reel; "$HERE/make_fixture.sh" "$R" >/dev/null
"$PY" "$SK/scripts/prep.py" "$R" >/dev/null
echo '{"fps":30,"pacing":"natural","end_hold":0.8}' > "$R/work/job.json"
"$PY" "$SK/scripts/analyze.py" "$R/work" >/dev/null 2>&1
"$PY" "$SK/scripts/edl.py" "$R/work" >/dev/null
cp -R "$SK/remotion" "$R/remotion"; mkdir -p "$R/remotion/public"
"$PY" "$SK/scripts/render_cut.py" "$R/work" "$R/remotion/public/camera_1x.mp4" 1.0 --size 1620x2880 --crf 14 >/dev/null
cd "$R/remotion"
if [[ -n "${NODE_MODULES:-}" ]]; then ln -s "$NODE_MODULES" node_modules; else npm install --silent >/dev/null; fi
DUR=$("$PY" -c "import json;e=json.load(open('$R/work/edl.json'));print(round(e['total_frames']/e['fps'],3))")
cat > src/beats.json <<JSON
{"duration": $DUR, "beats": [
 {"id":"b1","t0":0,"framing":"wide","elements":[{"type":"text","at":0.2,"lead":"most people","key":"edit by hand","pos":"top"}]},
 {"id":"b2","t0":4,"framing":"left","cut":"hard","elements":[{"type":"number","at":4.2,"value":5,"suffix":" hrs","label":"every week"}]},
 {"id":"b3","t0":7,"framing":"right","cut":"ease","elements":[{"type":"card","at":7.2,"title":"Reel Studio","body":"Claude does the cut"},{"type":"list","at":7.6,"items":["cut","graphics","music"]}]}
]}
JSON
node stills.mjs Reel 2 5 8 > "$R/stills.log" 2>&1 || { tail -30 "$R/stills.log"; exit 1; }
for s in 2 5 8; do [[ $(ffprobe -v error -show_entries stream=width,height -of csv=p=0 out/still_$s.png) == "1080,1920" ]] || { echo "FAIL size $s"; exit 1; }; done
"$PY" - out <<'PYEOF'
import subprocess, sys
import numpy as np
g = lambda s: np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f"{sys.argv[1]}/still_{s}.png", "-vf", "scale=54:96,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout, np.uint8).astype(float)
assert np.abs(g(2) - g(5)).mean() > 5 and np.abs(g(5) - g(8)).mean() > 5, "framing did not change between beats"
print("stills ok")
PYEOF
node render.mjs Reel out/reel.mp4 > "$R/render.log" 2>&1 || { tail -30 "$R/render.log"; exit 1; }
[[ -z $("$PY" "$SK/scripts/find_glitches.py" out/reel.mp4) ]] || { echo "FAIL glitches"; exit 1; }
echo "ALL PASS ($R)"
