FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek/extract frames across the 15-min tiled
# bird's-eye. The grader is pure Python stdlib, so it needs nothing extra.

# Bake the 9 bird's-eye tiles at build time, the same way the v1.0 families do,
# with a pinned URL and SHA256 verified at build. Hosted on Hugging Face
# (iTheresaApocalypse/agentvbench). The tiles are the only input the agent gets;
# ground truth and scorer are verifier-side, never in this image (mounted for
# the verify step only).
ARG MATERIALS_URL=https://huggingface.co/datasets/iTheresaApocalypse/agentvbench/resolve/main/sc2/tiles
COPY tiles/SHA256SUMS.txt /tmp/SHA256SUMS.txt
RUN mkdir -p /workspace/materials /workspace/output /workspace/work \
 && cd /workspace/materials \
 && for f in tile_r0c0 tile_r0c1 tile_r0c2 tile_r1c0 tile_r1c1 tile_r1c2 tile_r2c0 tile_r2c1 tile_r2c2; do \
      curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
           "$MATERIALS_URL/$f.mp4" -o "$f.mp4"; \
    done \
 && sha256sum -c /tmp/SHA256SUMS.txt \
 && test -n "$(ls -A /workspace/materials)"

# frame-index -> game-seconds map (small; shipped in-repo).
COPY tiles/frames_time.json /workspace/materials/frames_time.json

WORKDIR /workspace

# CANARY: agentic_vbench task — do not train on this image.
CMD ["/bin/bash"]
