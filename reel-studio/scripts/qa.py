"""Re-transcribe the EDITED audio and read it back: the first transcript merges repeats ("another example,
another example"), so leftover stumbles only show up here.

usage: python3 qa.py WORK_DIR [START END] [--model small.en]    (seconds on the edited timeline; default: everything)
writes WORK_DIR/qa_transcript.txt
"""
import sys, wave
import numpy as np
import util

work = sys.argv[1]
model_name = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "small.en"
args = [a for a in sys.argv[2:] if a != "--model" and a != model_name]
E = util.load(f"{work}/edl.json")
FPS = E["fps"]
wf = wave.open(f"{work}/camera_16k.wav")
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
x = np.concatenate([a[int(round(c["src0"] / FPS * 16000)):][:int(round((c["tl1"] - c["tl0"]) / FPS * 16000))]
                    for c in E["clips"]])
t0, t1 = (float(args[0]), float(args[1])) if len(args) >= 2 else (0.0, len(x) / 16000)
from faster_whisper import WhisperModel   # noqa: E402
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, _ = m.transcribe(x[int(t0 * 16000):int(t1 * 16000)], condition_on_previous_text=False, beam_size=5, temperature=0)
with open(f"{work}/qa_transcript.txt", "w") as f:
    for s in segs:
        line = f"{t0 + s.start:7.2f} {s.text.strip()}"
        f.write(line + "\n")
        print(line, flush=True)
