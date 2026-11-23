"""Render the cut (camera only, no graphics) from work/source.mp4 and work/edl.json.

usage: python3 render_cut.py WORK_DIR OUT.mp4 SPEED [--size 1080x1920] [--crf 20] [--lut FILE.cube] [--sharpen 0.5]
  SPEED 1.0 for the base Remotion uses; e.g. 1.1 for a quick preview the person watches.
  --lut      the camera maker's LUT, only for log footage (it turns flat grey log video into normal colour)
  --sharpen  light sharpening on the camera picture (0 = off)
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

R, out, speed = sys.argv[1], sys.argv[2], float(sys.argv[3])
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
W, H = (int(v) for v in arg("--size", "1080x1920").split("x"))
crf, lut, sharpen = arg("--crf", "20"), arg("--lut", None), float(arg("--sharpen", "0"))
SRC = os.path.join(R, "source.mp4")
E = json.load(open(os.path.join(R, "edl.json")))
FPS = E["fps"]
tmp = os.path.join(R, "_pieces")
os.makedirs(tmp, exist_ok=True)
vf = [f"scale={W}:{H}:flags=lanczos"]
if lut:
    if not os.path.exists(lut):
        raise SystemExit(f"LUT not found: {lut}")
    vf.append("lut3d='%s'" % lut.replace("'", r"\'"))
if sharpen > 0:
    vf.append(f"cas={sharpen}")
# the output is normal Rec.709 video: say so, or players and Remotion may show it darker
vf += ["setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709", "format=yuv420p"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(" ".join(cmd[:10]) + "\n" + r.stderr[-1500:])


def piece(k_c):
    k, c = k_c
    n = c["tl1"] - c["tl0"]
    o = f"{tmp}/p{k:03d}.mov"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c['src0'] / FPS:.4f}", "-i", SRC, "-frames:v", str(n), "-vf", ",".join(vf),
         "-af", f"pan=mono|c0=c0,atrim=0:{n / FPS:.5f},apad", "-t", f"{n / FPS:.5f}", "-c:v", "libx264", "-preset", "fast",
         "-crf", "12", "-r", str(FPS), "-c:a", "pcm_s16le", "-ar", "48000", o])
    return o


with ThreadPoolExecutor(3) as ex:
    parts = list(ex.map(piece, enumerate(E["clips"])))
ins, cat = [], ""
for k, f in enumerate(parts):
    ins += ["-i", f]
    cat += f"[{k}:v][{k}:a]"
fc = (f"{cat}concat=n={len(parts)}:v=1:a=1[cv][ca];[cv]setpts=PTS/{speed},fps={FPS}[v];"
      f"[ca]atempo={speed},loudnorm=I=-16:TP=-1.5:LRA=11,pan=stereo|c0=c0|c1=c0[a]")
run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
     "-preset", "medium", "-crf", crf, "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
     "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out])
for p in parts:
    os.remove(p)
print("done", out)
