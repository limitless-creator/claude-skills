"""Turn reference reels and screenshots into the picker page's data.

usage: python3 frames.py REEL_DIR [--every 2.5] [--max 60]
  reads  REEL_DIR/references/reels/*.mp4 and REEL_DIR/references/own/*.{jpg,jpeg,png,webp}
  writes REEL_DIR/references/frames/*.jpg and REEL_DIR/answers/references.data.json (picker, yes/no)
Screenshots are always included. Video frames: one every --every seconds, near-duplicates dropped,
then spread evenly across reels until --max items in total.
"""
import json, os, subprocess, sys
import numpy as np

reel = sys.argv[1]
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
every, cap = float(arg("--every", "2.5")), int(arg("--max", "60"))
ref = os.path.join(reel, "references")
out = os.path.join(ref, "frames")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
items = []

own_dir = os.path.join(ref, "own")
own = sorted(f for f in os.listdir(own_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))) if os.path.isdir(own_dir) else []
for k, f in enumerate(own):
    dst = f"own_{k:02d}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(own_dir, f), "-vf", "scale=720:-2", os.path.join(out, dst)], check=True)
    items.append({"id": f"own{k}", "img": f"references/frames/{dst}", "caption": f"your screenshot: {f}"})


def thumbs(video):
    """[(seconds, small grey picture)] one per `every` seconds."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=1/{every},scale=32:56,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, 56, 32).astype(np.float32)
    return [((k + 0.5) * every, a[k]) for k in range(len(a))]


rdir = os.path.join(ref, "reels")
videos = sorted(f for f in os.listdir(rdir) if f.endswith(".mp4")) if os.path.isdir(rdir) else []
per_video = []
for v in videos:
    keep, last = [], None
    for t, img in thumbs(os.path.join(rdir, v)):
        if last is None or np.abs(img - last).mean() > 6:   # skip near-duplicates
            keep.append(t)
            last = img
    per_video.append((v, keep))

room = max(0, cap - len(items))
picked = []
for i, (v, ts) in enumerate(per_video):
    share = room // len(per_video) + (1 if i < room % len(per_video) else 0)   # even share per reel
    idx = np.unique(np.linspace(0, len(ts) - 1, min(share, len(ts))).round().astype(int)) if ts and share else []
    picked.append([ts[j] for j in idx])
for (v, _), ts in zip(per_video, picked):
    owner = v.split("_")[0]
    for t in ts:
        dst = f"{os.path.splitext(v)[0]}_{int(t * 10):05d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", os.path.join(rdir, v), "-frames:v", "1",
                        "-vf", "scale=720:-2", os.path.join(out, dst)], check=True)
        items.append({"id": f"v{len(items)}", "img": f"references/frames/{dst}", "caption": f"@{owner} · {t:.0f}s"})

os.makedirs(os.path.join(reel, "answers"), exist_ok=True)
json.dump({"title": "Which of these looks do you like?", "mode": "yesno", "items": items},
          open(os.path.join(reel, "answers", "references.data.json"), "w"), indent=1)
print(f"{len(items)} pictures ({len(own)} screenshots, {len(items) - len(own)} from {len(videos)} reels)")
