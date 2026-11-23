"""Find broken (tiled) frames Remotion sometimes leaves: a frame that jumps away from the one before and comes
back within 1-3 frames. A real cut jumps and stays; a broken frame jumps and returns.
usage: find_glitches.py VIDEO.mp4     -> prints bad frame numbers, one per line (nothing = clean)
       find_glitches.py --selftest"""
import subprocess, sys
import numpy as np

W, H, T = 108, 192, 12.0


def bad_frames(f):
    d = lambda a, b: float(np.abs(f[a] - f[b]).mean())
    bad = set()
    for n in range(1, len(f) - 1):
        jump = d(n - 1, n)
        if jump <= T:
            continue
        for k in range(1, 4):
            if n + k < len(f) and d(n - 1, n + k) < 0.35 * jump:
                bad.update(range(n, n + k))
                break
    return sorted(bad)


if sys.argv[1] == "--selftest":
    cut = np.zeros((6, H, W), np.float32); cut[3:] = 200
    flash = np.zeros((6, H, W), np.float32); flash[2] = 200
    assert bad_frames(cut) == [] and bad_frames(flash) == [2]
    print("selftest ok", file=sys.stderr)
    sys.exit()
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
for n in bad_frames(np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)):
    print(n)
