#!/usr/bin/env python3
"""Prove the kill events are answerable from the video: extract frames around every recorded
kill so each mob can be eyeballed.

    verify_kills.py GAME_MP4 PLAY_JSON OFFSET_S OUTDIR

For each kill event, grabs frames at t-4, t-2 and t-0.5 seconds (video time = offset +
event time, verified to be exact for this pipeline) and lays them out one row per kill with
the mob name and weapon labelled. If a mob cannot be found in its own row, that ledger entry
is unanswerable and must be removed from the ground truth — this is the check that caught a
panda kill happening entirely off-camera.
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

FF = "/pkg/ffmpeg/4.2.2/bin/ffmpeg"
game, play, offset, out = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]), Path(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)

kills = [e for e in json.loads(play.read_text())["events"] if e["action"] == "kill"]
OFFSETS = [-4.0, -2.0, -0.5]
W, H = 400, 225

sheet = Image.new("RGB", (W * len(OFFSETS), (H + 16) * len(kills)), "white")
dr = ImageDraw.Draw(sheet)
for r, k in enumerate(kills):
    t0 = offset + k["t_ms"] / 1000.0
    for c, dt in enumerate(OFFSETS):
        t = max(0.0, t0 + dt)
        f = out / f"k{r:02d}_{c}.png"
        subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(game), "-frames:v", "1",
                        str(f), "-y"], check=True)
        if f.exists():
            sheet.paste(Image.open(f).resize((W, H)), (c * W, r * (H + 16)))
        dr.text((c * W + 4, r * (H + 16) + H + 2),
                f"{k['target']} ({k.get('tool')})  t{dt:+.1f}s @ {t:.0f}s", fill="black")
sheet.save(out / "kills.png")
print(f"{len(kills)} kills -> {out/'kills.png'}")
for r, k in enumerate(kills):
    print(f"  row {r}: {k['target']:11s} {k.get('tool'):5s} at {offset + k['t_ms']/1000:.0f}s")
