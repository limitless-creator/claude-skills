#!/bin/bash
# Final file: optional speed-up, Rec.709, voice + effects at -16 LUFS, optional music ~18 dB under the voice.
# usage: finish.sh IN.mp4 OUT.mp4 [SPEED=1.0] [MUSIC.mp3]
set -euo pipefail
IN=$1; OUT=$2; SPEED=${3:-1.0}; MUS=${4:-}
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
LEN=$(python3 -c "print(round($DUR/$SPEED,3))")
V="[0:v]setpts=PTS/$SPEED,fps=30,format=yuv420p[v]"
ENC=(-c:v libx264 -crf 18 -preset slow -profile:v high -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv
     -c:a aac -b:a 256k -ar 48000 -movflags +faststart)
if [[ -z "$MUS" ]]; then
  FC="$V;[0:a]atempo=$SPEED,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
  ffmpeg -v error -y -i "$IN" -filter_complex "$FC" -map "[v]" -map "[a]" "${ENC[@]}" "$OUT"
else
  FO=$(python3 -c "print(max(0, round($LEN-1.8,3)))")
  FC="$V;[0:a]atempo=$SPEED,loudnorm=I=-16:TP=-1.5:LRA=11[vo];[1:a]atrim=0:$LEN,asetpts=PTS-STARTPTS,loudnorm=I=-34:TP=-9:LRA=11,afade=t=in:d=0.6,afade=t=out:st=$FO:d=1.8[m];[vo][m]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]"
  ffmpeg -v error -y -i "$IN" -stream_loop -1 -i "$MUS" -filter_complex "$FC" -map "[v]" -map "[a]" "${ENC[@]}" "$OUT"
fi
echo "done $OUT ($LEN s)"
