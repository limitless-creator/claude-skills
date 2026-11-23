# Checks before sending anything

Run these yourself. Never ask the person to check something you can check.

## The clean cut (before showing it)

- Read the whole `qa_transcript.txt` against `script.txt`. Every script line is there once, in order, with no retakes, "um", "let me say that again", or false starts.
- **Merged repeats:** Whisper (the transcription model) often writes a repeated phrase only once ("That takes… That takes hours" becomes one line), so the read-back can look clean while a repeat is still in. For each kept clip, list the speech bursts from `db10ms.npy` (runs above −50 dB separated by > 0.35 s silence). Re-transcribe any short burst that is followed by a pause and check it isn't a false start.
- No cut lands mid-word: listen-check by reading words around each cut in `words_tl.json` (no word with `s` or `e` null next to a kept neighbour).

## The clean-cut preview (after rendering it)

- It is 1080×1920 and the person is fully in frame (grab 3–4 frames with ffmpeg and look at them).

## Stills of each beat (before the elements page)

- The face is fully in frame in every zoom.
- Graphics respect `preferences.face` and `preferences.fullscreen`.
- With `framing: zoom-to-side`: sides change on a new point, graphics sit on the free side.
- Nothing important sits in the bottom ~250 px or top ~150 px (app buttons cover those).
- Real things (apps, logos, people, websites) look like the real thing.

## The full render

- `find_glitches.py out/reel.mp4` prints nothing. If it prints frame numbers, re-render those frames with `stills.mjs` and overlay them back (`ffmpeg … overlay=enable='eq(n,N)'`), then run it again.
- A contact sheet: one frame every 2 s (`ffmpeg -vf "fps=1/2,scale=216:-1,tile=6x5"`). Look at it: no empty stretch longer than `preferences.change_every` allows, no text cut off at the edges.
- Brightness: on 2–3 **wide** beats (zooms move the picture, so only wide beats line up), the reel isn't darker than `camera_1x.mp4`. Compare the same moment (remember the final speed-up when picking times in the final file):
  `ffmpeg -ss T -i FILE -frames:v 1 -vf "scale=1080:1920,crop=400:400:340:500,signalstats,metadata=print" -f null - 2>&1 | grep YAVG` (within ±3).
- Size 1080×1920, 30 fps, H.264, AAC.
- Loudness: `ffmpeg -i final.mp4 -af ebur128 -f null -` → integrated about −16 LUFS (±1.5).
- Length matches the cut at the chosen speed.
