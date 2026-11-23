"""Join every raw file into one clean source video, ready for cutting.

usage: python3 prep.py REEL_DIR [--size 1620x2880] [--fps 30]
  reads  REEL_DIR/raw/*   (video files, joined in name order)
  writes REEL_DIR/work/source.mp4      one 9:16 file, constant frame rate, mono voice on both ears
         REEL_DIR/work/camera_16k.wav  16 kHz mono voice for transcription
         REEL_DIR/work/source.json     {fps, w, h, duration, files:[{name, start, duration, voice_channel}]}

Frames that aren't 9:16 are centre-cropped (never stretched). The default size is larger than 1080x1920
so later zooms stay sharp. If a file has the voice on one channel only (a lav mic on the left, silence on
the right), that channel is used instead of averaging it down to half volume.
"""
import json, os, subprocess, sys
import numpy as np

VIDEO = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".mts", ".webm"}


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode:
        raise SystemExit(" ".join(map(str, cmd[:12])) + "\n" + r.stderr[-1500:].decode(errors="replace"))
    return r.stdout


def probe(path):
    out = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,channels,duration:format=duration",
                          "-of", "json", path]))
    v = [s for s in out["streams"] if s["codec_type"] == "video"]
    a = [s for s in out["streams"] if s["codec_type"] == "audio"]
    if not v:
        raise SystemExit(f"{path} has no picture")
    return float(out["format"]["duration"]), (a[0].get("channels", 1) if a else 0)


def voice_channel(path, channels):
    """'L' or 'R' when one channel is nearly silent, else 'mix'."""
    if channels < 2:
        return "mix"
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-ac", "2", "-ar", "8000", "-f", "f32le", "-"])
    x = np.frombuffer(raw, np.float32).reshape(-1, 2)
    rms = np.sqrt((x ** 2).mean(0)) + 1e-9
    if rms[1] < 0.1 * rms[0]:
        return "L"
    if rms[0] < 0.1 * rms[1]:
        return "R"
    return "mix"


def main():
    reel = sys.argv[1]
    size = sys.argv[sys.argv.index("--size") + 1] if "--size" in sys.argv else "1620x2880"
    fps = int(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 30
    W, H = (int(v) for v in size.split("x"))
    raw_dir, work = os.path.join(reel, "raw"), os.path.join(reel, "work")
    files = sorted(f for f in os.listdir(raw_dir) if os.path.splitext(f)[1].lower() in VIDEO and not f.startswith("."))
    if not files:
        raise SystemExit(f"No video files in {raw_dir}")
    os.makedirs(os.path.join(work, "_prep"), exist_ok=True)

    info, parts, start = [], [], 0.0
    for k, name in enumerate(files):
        src = os.path.join(raw_dir, name)
        dur, ch = probe(src)
        vw, vh = (int(x) for x in run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                        "-of", "csv=p=0", src]).decode().strip().split(",")[:2])
        if abs(vw / vh - W / H) > 0.1:
            print(f"note: {name} is {vw}x{vh}, not 9:16; the sides are cropped to fit. Check the person is still fully in frame.", flush=True)
        vc = voice_channel(src, ch)
        pan = {"L": "pan=mono|c0=c0", "R": "pan=mono|c0=c1", "mix": "pan=mono|c0=0.5*c0+0.5*c1" if ch >= 2 else "pan=mono|c0=c0"}[vc]
        part = os.path.join(work, "_prep", f"p{k:02d}.mov")
        # cover-crop to 9:16, constant frame rate; audio padded/trimmed to exactly the picture length
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps={fps},format=yuv420p"
        if ch:
            ins, amap, af = ["-i", src], "0:a:0", ["-af", f"{pan},aresample=48000,apad"]
        else:  # no sound at all: silent track so the join still works
            ins, amap, af = ["-i", src, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"], "1:a:0", []
        run(["ffmpeg", "-v", "error", "-y"] + ins + ["-vf", vf] + af + ["-t", f"{dur:.3f}", "-map", "0:v:0", "-map", amap,
             "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1", part])
        pd = float(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", part]).decode().strip()) / fps
        parts.append(part)
        info.append({"name": name, "start": round(start, 3), "duration": round(pd, 3), "voice_channel": vc})
        print(f"{name}: {pd:.2f}s, voice {vc}", flush=True)
        start += pd

    lst = os.path.join(work, "_prep", "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    src_mp4 = os.path.join(work, "source.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy",
         "-af", "pan=stereo|c0=c0|c1=c0", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", src_mp4])
    run(["ffmpeg", "-v", "error", "-y", "-i", src_mp4, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
         os.path.join(work, "camera_16k.wav")])
    for p in parts:
        os.remove(p)
    json.dump({"fps": fps, "w": W, "h": H, "duration": round(start, 3), "files": info},
              open(os.path.join(work, "source.json"), "w"), indent=1)
    print(f"source.mp4 {start:.1f}s from {len(files)} file(s)")


if __name__ == "__main__":
    main()
