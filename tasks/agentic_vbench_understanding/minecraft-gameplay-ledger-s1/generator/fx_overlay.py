#!/usr/bin/env python3
"""Composite gameplay FX the headless renderer does not draw — block-break cracks and a
hit-flash — onto an already-HUD'd Minecraft video.

    fx_overlay.py IN.mp4 PLAY_JSON OFFSET_S OUT.mp4

Why this is needed and why it is honest: prismarine-viewer ships the vanilla `destroy_stage`
crack textures but never renders them, and has no entity damage-tint — so a break looks
instantaneous and a hit shows no reaction. Both effects are things the real client draws.
This restores them from the bot's OWN event log (exact mine and kill times), anchored to
screen-centre because the camera is aimed AT the block/mob when the action happens (the bot
does `smoothLookAt(target)` first). It is an approximation of placement, but the *timing* is
exact and the effect is the real vanilla texture.

  crack: for each `mine`, the real destroy_stage_0..9 sprite grows over the ~0.6 s before the
         block disappears, then clears at the break instant.
  flash: for each `kill`, a brief red tint over the centre where the mob is, at the moment it
         takes the fatal hit.

Built as one transparent low-fps overlay track (fast to generate, most frames empty), then
overlaid onto the input in a single ffmpeg pass. The track content is self-tested numerically
(non-empty near event times, empty far from them) since it cannot be eyeballed here.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

FF = subprocess.run(["/usr/bin/python3", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True, check=True).stdout.strip()
FP = "/pkg/ffmpeg/4.2.2/bin/ffprobe"
TEX = Path(__file__).resolve().parent / "node_modules/prismarine-viewer/public/textures/1.16.4/blocks"

inp, play, offset, out = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3]), Path(sys.argv[4])
W, H, FPS = 1280, 720, 12

d = json.loads(play.read_text())
ev = d["events"]
# head trim matches composite_hud.py: video starts ~offset s before the first event.
head = max(0.0, offset + (ev[0]["t_ms"] / 1000.0 - 8.0)) if ev else max(0.0, offset - 1.0)
def vt(e):
    return offset - head + e["t_ms"] / 1000.0
mines = [vt(e) for e in ev if e["action"] == "mine"]
kills = [vt(e) for e in ev if e["action"] == "kill"]

dur = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(inp)], capture_output=True, text=True).stdout.strip() or 0)
n_frames = int(dur * FPS)

# pre-scaled crack sprites (screen-block ~ 150 px), and a red flash tile
CRACK = [Image.open(TEX / f"destroy_stage_{i}.png").convert("RGBA").resize((150, 150), Image.NEAREST)
         for i in range(10)]
CRACK_XY = (W // 2 - 75, int(H * 0.52) - 75)     # slightly below centre, where a mined block sits
CRACK_WIN = 0.6
FLASH_WIN = 0.30

def frame_rgba(t):
    """The overlay content at video-time t. Returns HxWx4 uint8 (mostly zero)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for mt in mines:
        if mt - CRACK_WIN <= t < mt:
            stage = min(9, int((t - (mt - CRACK_WIN)) / CRACK_WIN * 10))
            img.alpha_composite(CRACK[stage], CRACK_XY)
    for kt in kills:
        if abs(t - kt) <= FLASH_WIN:
            a = int(120 * (1 - abs(t - kt) / FLASH_WIN))     # fade in/out
            red = Image.new("RGBA", (int(W * 0.5), int(H * 0.5)), (220, 30, 30, a))
            img.alpha_composite(red, (W // 4, H // 5))
    return np.asarray(img)


def selftest():
    ok = True
    for label, ts, present in [("at first crack", mines[0] - 0.05 if mines else None, True),
                               ("between events", None, False),
                               ("at first kill", kills[0] if kills else None, True)]:
        if label == "between events":
            # a time far from any event
            allt = sorted(mines + kills)
            gap = 5.0
            t = None
            for i in range(len(allt) - 1):
                if allt[i + 1] - allt[i] > 2 * gap:
                    t = allt[i] + gap
                    break
            if t is None:
                continue
        else:
            t = ts
        if t is None:
            continue
        cov = float((frame_rgba(t)[:, :, 3] > 0).mean())
        hit = cov > 0.001
        status = "ok " if hit == present else "FAIL"
        if hit != present:
            ok = False
        print(f"  {status} overlay {'present' if present else 'empty'} {label} (t={t:.1f}s, cov={cov:.4f})")
    return ok


if not selftest():
    sys.exit("fx self-test failed — overlay not gated to event times correctly")

# stream raw RGBA frames to ffmpeg -> lossless-alpha track
track = out.with_suffix(".fxtrack.mov")
p = subprocess.Popen(
    [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
     "-c:v", "qtrle", str(track)], stdin=subprocess.PIPE)
for i in range(n_frames):
    p.stdin.write(frame_rgba(i / FPS).tobytes())
p.stdin.close()
if p.wait() != 0:
    sys.exit("failed to encode fx track")

subprocess.run(
    [FF, "-v", "error", "-i", str(inp), "-i", str(track),
     "-filter_complex", "[1:v]fps=25[fx];[0:v][fx]overlay=0:0[v]", "-map", "[v]",
     "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", str(out), "-y"], check=True)
track.unlink(missing_ok=True)
print(f"wrote {out}  ({len(mines)} cracks, {len(kills)} flashes)")
