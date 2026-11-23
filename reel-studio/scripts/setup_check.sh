#!/bin/bash
# What's installed and what's missing. Prints one line per tool; never installs anything.
# usage: setup_check.sh [PYTHON]   (default: ~/ReelStudio/.venv/bin/python, then python3)
PY=${1:-$HOME/ReelStudio/.venv/bin/python}; [[ -x "$PY" ]] || PY=$(command -v python3 || true)
v() { "$@" 2>/dev/null | head -1; }
[[ -n $(command -v ffmpeg) ]] && echo "ok ffmpeg $(v ffmpeg -version | awk '{print $3}')" || echo "missing ffmpeg"
[[ -n $(command -v ffprobe) ]] && echo "ok ffprobe" || echo "missing ffprobe"
if [[ -n $(command -v node) ]]; then
  major=$(node -v | sed 's/v\([0-9]*\).*/\1/'); (( major >= 20 )) && echo "ok node $(node -v)" || echo "old node $(node -v) (need 20 or newer)"
else echo "missing node"; fi
if [[ -n "$PY" ]]; then
  echo "ok python $("$PY" -c 'import sys;print(sys.version.split()[0])') ($PY)"
  "$PY" -c "import numpy" 2>/dev/null && echo "ok numpy" || echo "missing numpy"
  "$PY" -c "import faster_whisper" 2>/dev/null && echo "ok faster-whisper" || echo "missing faster-whisper"
else echo "missing python3"; fi
[[ -d "$HOME/ReelStudio/.remotion/node_modules/remotion" ]] && echo "ok remotion" || echo "missing remotion (~/ReelStudio/.remotion)"
[[ -n "${APIFY_TOKEN:-}" ]] && echo "ok APIFY_TOKEN is set" || echo "missing APIFY_TOKEN (only needed to download reference reels)"
df -g "$HOME" 2>/dev/null | awk 'NR==2 {print ($4 >= 5 ? "ok" : "low"), "disk", $4 " GB free"}'
exit 0
