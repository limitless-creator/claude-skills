"""Cut list: which stretches of work/source.mp4 to keep.

usage: python3 edl.py WORK_DIR        (reads job.json, words.json, db10ms.npy)
writes WORK_DIR/edl.json {fps, total_frames, clips:[{src0, src1, tl0, tl1}], removed}  (frames)
       WORK_DIR/words_tl.json  every word's time on the edited timeline (seconds; null if cut)

job.json (seconds are source seconds; word ranges are inclusive indices from words.json):
  fps           30
  pacing        "tight" (breath-length pauses) | "natural" (only pauses over 0.6 s are shortened)
  end_hold      seconds kept after the last word, default 1.0
  last_word     index of the last word to keep (default: the last word heard)
  remove_words  [[first, last, "why"], ...]   retakes, false starts, ums, "let me say that again"
  remove_time   [[start, end, "why"], ...]    when the transcript merged a repeat into one run of words
  force_start   {"<first word index>": seconds}   removal start where there is no silence
  force_end     {"<last word index>": seconds}    removal end override
"""
import sys
import numpy as np
import util

work = sys.argv[1]
J = util.load(f"{work}/job.json")
FPS = J.get("fps", 30)
W = util.load(f"{work}/words.json")
db = np.load(f"{work}/db10ms.npy")
N = len(db)
SIL = -50.0
PACE = {"tight": (0.45, 0.12, 0.10), "natural": (0.60, 0.20, 0.15)}[J.get("pacing", "natural")]
T = lambda i, end=False: W[i]["e"] if end else W[i]["s"]


def silences(t0, t1, thr=SIL, min_len=0.03):
    a, b = max(0, int(t0 * 100)), min(N, int(t1 * 100))
    return [((a + x) / 100, (a + y) / 100) for x, y in util.runs(db[a:b] < thr) if (y - x) / 100 >= min_len]


def gap_between(i, j):
    if i < 0:
        return (max(0.0, T(j) - 0.3), T(j))
    if j >= len(W):
        return (T(i, True), T(i, True) + 0.3)
    t0, t1 = T(i, True) - 0.25, T(j) + 0.25
    c = silences(t0, t1) or silences(t0, t1, thr=-45)
    if not c:
        m = (T(i, True) + T(j)) / 2
        return (m, m)
    return max(c, key=lambda r: r[1] - r[0])


def local_min(t, win=0.08):
    a, b = max(0, int((t - win) * 100)), min(N, int((t + win) * 100))
    return (a + int(np.argmin(db[a:b]))) / 100


# ---- removals -> time ranges, each edge snapped into a silence
fs = {int(k): v for k, v in J.get("force_start", {}).items()}
fe = {int(k): v for k, v in J.get("force_end", {}).items()}
removed = []
for a, b, why in J.get("remove_words", []):
    if a in fs:
        s = local_min(fs[a])
    else:
        g = gap_between(a - 1, a)
        s = min(g[1], g[0] + 0.12)
    if b in fe:
        e = fe[b]
    else:
        g = gap_between(b, b + 1)
        e = max(g[0], g[1] - 0.08)
    removed.append((s, e, why))
removed += [tuple(r) for r in J.get("remove_time", [])]
removed.sort()

# ---- speech mask
speech = db > SIL
for x, y in util.runs(~speech):
    if y - x < 12:
        speech[x:y] = True          # stop consonants are not pauses
for x, y in util.runs(speech):
    if y - x < 6:
        speech[x:y] = False         # clicks are not speech

LW = W[J.get("last_word", len(W) - 1)]
end_src = LW["e"] + 0.6
keep = np.zeros(N, bool)
keep[max(0, int(np.argmax(speech)) - 8):int(end_src * 100)] = True
for s, e, _ in removed:
    keep[int(round(s * 100)):int(round(e * 100))] = False
min_gap, tail, lead = PACE
for x, y in util.runs(~speech):
    if x == 0 or y >= N:
        continue
    t0, t1 = x / 100, y / 100
    if t1 - t0 >= min_gap:
        keep[int(round((t0 + tail) * 100)):int(round((t1 - lead) * 100))] = False

clips = [(x / 100, y / 100) for x, y in util.runs(keep)]
removal_ends = {round(e, 2) for _, e, _ in removed}


def merge_short(clips, min_len=0.7, max_restore=1.0):
    """Clips shorter than min_len flash by; join them to a neighbour unless that would undo a removal."""
    changed = True
    while changed:
        changed = False
        for k, (a, b) in enumerate(clips):
            if b - a >= min_len:
                continue
            opts = []
            if k > 0 and a - clips[k - 1][1] <= max_restore and round(a, 2) not in removal_ends:
                opts.append((a - clips[k - 1][1], k - 1))
            if k + 1 < len(clips) and clips[k + 1][0] - b <= max_restore and round(clips[k + 1][0], 2) not in removal_ends:
                opts.append((clips[k + 1][0] - b, k))
            if opts:
                _, j = min(opts)
                clips[j:j + 2] = [(clips[j][0], clips[j + 1][1])]
                changed = True
                break
    return clips


clips = merge_short(clips)
has_words = lambda a, b: any(w["s"] < b - 0.05 and w["e"] > a + 0.05 for w in W)
clips = [(a, b) for a, b in clips if has_words(a, b)]
clips_f = [[util.fr(a, FPS), util.fr(b, FPS)] for a, b in clips if util.fr(b, FPS) - util.fr(a, FPS) >= 3]
assert clips_f, "nothing left to keep: check job.json removals"
clips_f[-1][1] = min(max(clips_f[-1][1], util.fr(LW["e"] + J.get("end_hold", 1.0), FPS)), util.fr(N / 100, FPS))

split, tl = [], 0
for a, b in clips_f:
    split.append({"src0": a, "src1": b, "tl0": tl, "tl1": tl + b - a})
    tl += b - a
TOTAL = tl


def to_tl(t):
    f = t * FPS
    for c in split:
        if c["src0"] <= f < c["src1"]:
            return round((c["tl0"] + f - c["src0"]) / FPS, 3)
    return None


def word_tl(w):
    """A word that is kept (its middle survives the cut) always gets times, even if a cut shaves its edge."""
    mid = to_tl((w["s"] + w["e"]) / 2)
    if mid is None:
        return None, None
    s = to_tl(w["s"] + 0.02)
    e = to_tl(max(w["s"] + 0.03, w["e"] - 0.02))
    return (s if s is not None and s <= mid else mid), (e if e is not None and e >= mid else mid)


words_tl = [dict(zip(("s", "e"), word_tl(w)), i=w["i"], w=w["w"].strip()) for w in W]
util.save(f"{work}/words_tl.json", words_tl)
util.save(f"{work}/edl.json", {"fps": FPS, "total_frames": TOTAL, "clips": split,
                               "removed": [{"s": s, "e": e, "why": w} for s, e, w in removed]})
lens = np.array([(c["src1"] - c["src0"]) / FPS for c in split])
print(f"timeline {TOTAL / FPS:.1f}s from {end_src:.1f}s of source; {len(split)} clips; shortest {lens.min():.2f}s")
for s, e, w in removed:
    print(f"removed {s:7.2f}-{e:7.2f} ({e - s:5.2f}s) {w}")
