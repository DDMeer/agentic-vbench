# Environment (Docker)

The task environment isolates the agent: it gets the 9 bird's-eye tiles + `frames_time.json`
(`/data/`) and the prompt (`/task/instruction.md`) only. The ground truth (`gt/`) and the scorer
(`steps/solve/tests/`) are **never** in the image — the harness applies them outside the container
after the agent finishes. This prevents the filesystem-snooping cheat: during local calibration
each agent ran in a dir containing only the tiles + prompt + ffmpeg (no GT, no scorer on disk).

Requires Docker (Docker Desktop on Windows). If this machine has no Docker, build/run on a host
that does.

## Build
The 9 tile videos are fetched at build time from a pinned base URL + per-file checksums
(`tiles/SHA256SUMS.txt`), so the build fails if any hosted file changes. Run from the task dir
`sc2/`:
```bash
docker build -f environment/Dockerfile \
  --build-arg TILES_BASE_URL=<your-host>/sc2/tiles \
  -t sc2-buildorder-task .
```

## Run the agent inside, then score outside
```bash
# 1) agent works inside the container; it writes /output/answer.json (mount an output dir)
docker run --rm -it -v "$PWD/out:/out" sc2-buildorder-task \
  bash -lc 'cat /task/instruction.md; ls /data; <your agent runs here, writing /output/answer.json>'

# 2) score OUTSIDE the container (GT + judge stay on the host)
ANSWER_PATH=output/answer.json GT_PATH=steps/solve/tests/gt.json \
  python steps/solve/tests/judge.py
# -> {"reward": ..., "detail": {...}}
```

## Hosting
The 9 tiles (~135 MB total) are committed under `tiles/` for review, but for the built image
they should be hosted (e.g. Hugging Face) and pinned by checksum. Set the base URL at build time:
`--build-arg TILES_BASE_URL=<url-dir-containing-the-9-mp4s>`. Keep `tiles/SHA256SUMS.txt` in sync
if the media is ever re-rendered.

## Media provenance
See `../RECORDING.md` for the exact render recipe (PySC2 + Blizzard Linux research build, EGL RGB
on a headless GPU, full-map god-view at camera distance 320, RAW frames, 3×3 tiling, ~5 fps).
