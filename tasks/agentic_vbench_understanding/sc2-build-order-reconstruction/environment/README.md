# Environment (Docker)

The task environment isolates the agent: it gets the 9 bird's-eye tile videos
(`/workspace/materials/tile_r{0..2}c{0..2}.mp4`) plus the frame→game-time map
(`/workspace/materials/frames_time.json`) and the prompt (`/workspace` working
dir + `steps/solve/instruction.md`) only. The ground truth
(`steps/solve/tests/gt.json`) and the scorer (`steps/solve/tests/judge.py`) are
**never** in the agent image — the harness mounts them for the verify step
only, after the agent finishes. This prevents the filesystem-snooping cheat
caught during local calibration (an agent reading `gt/` up the tree).

## Build

The tiles are fetched at build time from a pinned Hugging Face URL and verified
by SHA256 (see `ARG MATERIALS_URL` and `tiles/SHA256SUMS.txt` in the Dockerfile),
so no local media file is needed and the build works on any host. Run from the
task dir:

```bash
docker build -f environment/Dockerfile -t sc2-buildorder-task .
```

## Hosting

The ~140 MB of tiles are not committed; they are hosted on Hugging Face and
pinned by checksum:

- Base URL: `https://huggingface.co/datasets/iTheresaApocalypse/agentvbench/resolve/main/sc2/tiles/`
- Per-file SHA256: `tiles/SHA256SUMS.txt` (9 tiles)
- `frames_time.json` and `SHA256SUMS.txt` are small and shipped in-repo (COPYed
  into the image); only the 9 `.mp4` tiles are downloaded at build time.

To re-host elsewhere, override at build time:
`docker build --build-arg MATERIALS_URL=<new-base-url> ...`.
