#!/usr/bin/env python3
"""Build review artifacts for a rendered P1 session, so the footage can be judged quickly.

    make_preview.py GAME_MP4 PLAY_JSON OUTDIR

Produces:
  contact.png     a 5x4 contact sheet sampled evenly across the video
  highlights.mp4  short clips around a few build / combat / mining moments
  report.txt      duration, event mix, distinct targets, kills with weapons
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

FP = "/pkg/ffmpeg/4.2.2/bin/ffprobe"        # module build has ffprobe but NO libx264
FF = "/pkg/ffmpeg/4.2.2/bin/ffmpeg"         # fine for decoding / PNG extraction
FFX = subprocess.run(["/usr/bin/python3", "-c",
                      "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                     capture_output=True, text=True, check=True).stdout.strip()  # has x264

game, play, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
d = json.loads(play.read_text())
evs = d["events"]

dur = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(game)], capture_output=True, text=True).stdout.strip())

# contact sheet
n, cols = 20, 5
frames = out / "frames"; frames.mkdir(exist_ok=True)
times = [dur * (i + 0.5) / n for i in range(n)]
for i, t in enumerate(times):
    subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(game), "-frames:v", "1",
                    str(frames / f"f{i:02d}.png"), "-y"], check=True)
W, H = 320, 180
rows = (n + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, (H + 14) * rows), "white")
dr = ImageDraw.Draw(sheet)
for i, t in enumerate(times):
    p = frames / f"f{i:02d}.png"
    if not p.exists(): continue
    sheet.paste(Image.open(p).resize((W, H)), ((i % cols) * W, (i // cols) * (H + 14)))
    dr.text(((i % cols) * W + 4, (i // cols) * (H + 14) + H + 1), f"{t:.0f}s", fill="black")
sheet.save(out / "contact.png")

# highlight reel: evenly spaced 6s windows
clips = []
for k, frac in enumerate([0.06, 0.22, 0.40, 0.58, 0.74, 0.90]):
    t = max(0.0, dur * frac)
    c = out / f"clip{k}.mp4"
    subprocess.run([FFX, "-v", "error", "-ss", f"{t:.2f}", "-t", "6", "-i", str(game),
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p", str(c), "-y"], check=True)
    clips.append(c)
lst = out / "clips.txt"
lst.write_text("".join(f"file '{c.name}'\n" for c in clips))
subprocess.run([FFX, "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c", "copy", str(out / "highlights.mp4"), "-y"], check=True)

kills = [(e["target"], e.get("tool")) for e in evs if e["action"] == "kill"]
mix = {a: sum(e["action"] == a for e in evs) for a in ("mine", "place", "kill")}
report = "\n".join([
    f"video      {game.name}  {dur/60:.1f} min ({dur:.0f}s)",
    f"events     {len(evs)}  mine={mix['mine']} place={mix['place']} kill={mix['kill']}",
    f"targets    {len({e['target'] for e in evs})} distinct: "
    + ", ".join(sorted({e['target'] for e in evs})),
    f"kills      " + ", ".join(f"{m}({w})" for m, w in kills),
    f"held items " + ", ".join(f"{h['item']}@{h['t_ms']/1000:.0f}s" for h in d.get("held", [])),
])
(out / "report.txt").write_text(report + "\n")
print(report)
print("\nwrote", out / "contact.png", "and", out / "highlights.mp4")
