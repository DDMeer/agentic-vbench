# AgenticVBench environment for sc2-build-order-reconstruction.
# Build context = the task dir (sc2/):  docker build -f environment/Dockerfile -t sc2-buildorder-task .
#
# The agent runs INSIDE this image with the 9 tile videos + frames_time.json at /data and the
# prompt at /task. The ground truth (gt/) and scorer (steps/solve/tests/) are NEVER copied in —
# they are applied by the harness OUTSIDE the container, so the agent cannot read them (this is
# what stops the filesystem-snooping cheat: local calibration ran agents in dirs with no GT/scorer).
FROM python:3.12-slim

# Agent tools: ffmpeg to extract/inspect frames, curl to fetch the videos. Scorer needs only stdlib.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- media: the 9 bird's-eye tiles, fetched at build time from a pinned base URL + checksums ---
# The checksums (tiles/SHA256SUMS.txt) make the build fail if any hosted file ever changes.
# Host the 9 tile_r{r}c{c}.mp4 under $TILES_BASE_URL/ and override the ARG when building.
ARG TILES_BASE_URL=https://huggingface.co/datasets/PLACEHOLDER/agentvbench/resolve/main/sc2/tiles
RUN mkdir -p /data /task
COPY tiles/SHA256SUMS.txt /data/SHA256SUMS.txt
RUN cd /data \
 && for f in tile_r0c0 tile_r0c1 tile_r0c2 tile_r1c0 tile_r1c1 tile_r1c2 tile_r2c0 tile_r2c1 tile_r2c2; do \
      curl -fsSL "$TILES_BASE_URL/$f.mp4" -o "$f.mp4"; \
    done \
 && sha256sum -c SHA256SUMS.txt

# frame-index -> game-seconds map (small; shipped in-repo) and the task prompt
COPY tiles/frames_time.json /data/frames_time.json
COPY steps/solve/instruction.md /task/instruction.md
WORKDIR /task

# CANARY: agentic_vbench task — do not train on this image.
CMD ["/bin/bash"]
