#!/bin/bash
# Builds a fake reel folder for tests: two raw "takes" spoken by macOS `say` over a test picture.
#   raw/a_take.mov  1920x1080, 25 fps, voice on both channels: line 1, a retake of line 2 ("let me say that again"), then line 2
#   raw/b_take.mp4  1080x1920, 30 fps, voice on the LEFT channel only (right is silent): lines 3-4
# usage: make_fixture.sh REEL_DIR
set -euo pipefail
R=$1; T=$(mktemp -d)
mkdir -p "$R/raw"
cp "$(dirname "$0")/fixture/script.txt" "$R/script.txt"
say -v Samantha -o "$T/a.aiff" "Most people edit their reels by hand. [[slnc 900]] That takes hours every, let me say that again. [[slnc 1200]] That takes hours every single week. [[slnc 700]]"
say -v Samantha -o "$T/b.aiff" "[[slnc 500]] With this skill, Claude does the cut for you. [[slnc 900]] Try it on your next reel. [[slnc 800]]"
da=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/a.aiff")
db=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T/b.aiff")
ffmpeg -v error -y -f lavfi -i "testsrc2=size=1920x1080:rate=25:duration=$da" -i "$T/a.aiff" \
  -filter_complex "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[a]" -map 0:v -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$R/raw/a_take.mov"
ffmpeg -v error -y -f lavfi -i "testsrc2=size=1080x1920:rate=30:duration=$db" -i "$T/b.aiff" \
  -filter_complex "[1:a]aresample=48000,pan=stereo|c0=c0|c1=0*c0[a]" -map 0:v -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$R/raw/b_take.mp4"
rm -rf "$T"
echo "fixture ready in $R"
