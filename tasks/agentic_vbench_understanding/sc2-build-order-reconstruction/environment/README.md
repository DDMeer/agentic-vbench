# Environment (Docker)

The task environment isolates the agent: it gets the 9 bird's-eye tiles + `frames_time.json`
(`/workspace/materials/`) and the prompt (`/workspace/instruction.md`) only. The ground truth
(`steps/solve/tests/gt.json`) and the scorer (`steps/solve/tests/judge.py`) are **never** in the
image — the harness applies them outside the container after the agent finishes. This prevents the
filesystem-snooping cheat: during local calibration each agent ran in a dir containing only the
tiles + prompt + ffmpeg (no GT, no scorer on disk).

Requires Docker (Docker Desktop on Windows). If this machine has no Docker, build/run on a host
that does.

## Build
The 9 tile videos are fetched at build time from a pinned, immutable Hugging Face dataset revision
+ per-file SHA256 checksums (`tiles/SHA256SUMS.txt`), so the build fails if any hosted file changes.
Run from the task dir `sc2/`:
```bash
docker build -f environment/Dockerfile -t sc2-buildorder-task .
```
The default `MATERIALS_URL` points at the immutable revision
`b74a6092c12bcd99a394fcec66cfc01253da13af` of `iTheresaApocalypse/agentvbench`; override it only to
point at a mirror:
```bash
docker build -f environment/Dockerfile \
  --build-arg MATERIALS_URL=<your-host>/sc2/tiles -t sc2-buildorder-task .
```

## Run the agent inside, then score outside
```bash
# 1) agent works inside the container; it writes /workspace/output/solution.json
docker run --rm -it -v "$PWD/out:/out" sc2-buildorder-task \
  bash -lc 'cat /workspace/instruction.md; ls /workspace/materials; \
            <your agent runs here, writing /workspace/output/solution.json>'

# 2) score OUTSIDE the container (GT + judge stay on the host)
python steps/solve/tests/judge.py \
  --solution /workspace/output/solution.json \
  --gt steps/solve/tests/gt.json \
  --reward-json /logs/verifier/reward.json \
  --reward-txt /logs/verifier/reward.txt
# -> reward.json: {"reward": ..., "details": {...}}
```

## Hosting
The 9 tiles (~135 MB total) are committed under `tiles/` for review, but for the built image they
are hosted on Hugging Face (`iTheresaApocalypse/agentvbench`, path `sc2/tiles`) and pinned to an
immutable dataset revision + SHA256 checksums. Keep `tiles/SHA256SUMS.txt` in sync if the media is
ever re-rendered.

## Media provenance
See `../RECORDING.md` for the exact render recipe (PySC2 + Blizzard Linux research build, EGL RGB
on a headless GPU, full-map god-view at camera distance 320, RAW frames, 3×3 tiling, ~5 fps).
