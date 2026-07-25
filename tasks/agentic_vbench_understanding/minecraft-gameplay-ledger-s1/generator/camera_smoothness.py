#!/usr/bin/env python3
"""Objectively measure how abrupt a video's camera motion is, so "smoother" is a number, not a vibe.

    camera_smoothness.py VIDEO [FPS]

Global optical flow proxy: sample frames, take the mean absolute pixel difference between
consecutive frames, and report the distribution of that per-frame motion. A hard camera snap shows
up as a small number of very large spikes, so the tail (p95 / max) and the count of "jump" frames
(motion > 4x the median) separate an eased pan from a teleporting one, even though both can have a
similar mean. It is a proxy for pan velocity, not ground truth motion, which is why the comparison
is between two renders of the same content rather than an absolute threshold.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

FF = subprocess.run(["/usr/bin/python3", "-c",
                     "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip() or "ffmpeg"


def frame_diffs(video, fps):
    """Mean absolute inter-frame difference for frames sampled at `fps`, on a downscaled grey copy."""
    tmp = Path(video).with_suffix(".smooth_frames")
    tmp.mkdir(exist_ok=True)
    for f in tmp.glob("*.png"):
        f.unlink()
    subprocess.run([FF, "-v", "error", "-i", str(video), "-vf",
                    f"fps={fps},scale=160:90", str(tmp / "f%05d.png")], check=True)
    frames = sorted(tmp.glob("*.png"))
    arrs = [np.asarray(Image.open(f).convert("L"), dtype=np.float32) for f in frames]
    diffs = [float(np.abs(arrs[i] - arrs[i - 1]).mean()) for i in range(1, len(arrs))]
    for f in frames:
        f.unlink()
    tmp.rmdir()
    return np.array(diffs)


def main():
    video = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    d = frame_diffs(video, fps)
    if len(d) == 0:
        print("no frames"); return
    med = float(np.median(d))
    jumps = int((d > 4 * max(med, 1e-6)).sum())
    print(f"{Path(video).name}: {len(d)+1} frames @ {fps}fps")
    print(f"  motion/frame  mean={d.mean():.2f} median={med:.2f} "
          f"p95={np.percentile(d,95):.2f} max={d.max():.2f}")
    print(f"  jump frames (motion > 4x median): {jumps}  ({100*jumps/len(d):.1f}%)")


if __name__ == "__main__":
    main()
