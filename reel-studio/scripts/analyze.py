"""Transcribe the camera audio with word timings and measure loudness every 10 ms.

usage: python3 analyze.py WORK_DIR [--model small.en]
  needs WORK_DIR/camera_16k.wav (16 kHz mono PCM, made by prep.py)
  writes words.json (every word: i, w, s, e, p), db10ms.npy, phrases.txt (lines split at pauses)
"""
import json, sys, wave
import numpy as np

work = sys.argv[1]
model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "small.en"

wf = wave.open(f"{work}/camera_16k.wav")
assert wf.getframerate() == 16000 and wf.getnchannels() == 1, "expected 16 kHz mono"
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# loudness envelope (dBFS per 10 ms): cut points are snapped to its quiet stretches
hop = 160
n = len(a) // hop
db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
np.save(f"{work}/db10ms.npy", db)

from faster_whisper import WhisperModel   # noqa: E402
m = WhisperModel(model_name, device="cpu", compute_type="int8")
# condition_on_previous_text=False keeps more repeats/false starts instead of smoothing them away.
# Pass the array, not a path: some PyAV builds break faster-whisper's own decoder.
segs, _ = m.transcribe(a, word_timestamps=True, condition_on_previous_text=False,
                       vad_filter=False, beam_size=5, temperature=0)
words = []
for s in segs:
    for w in s.words:
        words.append({"i": len(words), "w": w.word, "s": round(w.start, 3), "e": round(w.end, 3),
                      "p": round(w.probability, 3)})
    print(f"{s.start:7.2f} {s.text.strip()}", flush=True)
json.dump(words, open(f"{work}/words.json", "w"))

with open(f"{work}/phrases.txt", "w") as f:
    line, prev = [], None
    for w in words:
        if line and w["s"] - line[-1]["e"] > 0.3:
            f.write(f"[{line[0]['i']:4d}] {line[0]['s']:7.2f}-{line[-1]['e']:7.2f} {''.join(x['w'] for x in line).strip()}\n")
            line = []
        line.append(w)
    if line:
        f.write(f"[{line[0]['i']:4d}] {line[0]['s']:7.2f}-{line[-1]['e']:7.2f} {''.join(x['w'] for x in line).strip()}\n")
print(f"{len(words)} words, {len(a) / 16000:.1f}s -> {work}/words.json, phrases.txt, db10ms.npy")
