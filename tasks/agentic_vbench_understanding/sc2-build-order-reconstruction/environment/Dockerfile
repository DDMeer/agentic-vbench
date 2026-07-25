FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
 ffmpeg curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek, sample, and brighten frames across the
# 3×3 tile grid. The grader is pure Python stdlib (it only matches event tuples),
# so it needs nothing extra.

# Bake the 9 bird's-eye tiles + frames_time.json at build time, fetched from a
# pinned Hugging Face URL and verified by SHA256 (see ARG MATERIALS_URL and
# tiles/SHA256SUMS.txt), so no local media is needed and the build works on any
# host. The tiles + frames_time.json are the only inputs the agent gets; ground
# truth and scorer are verifier-side, never in this image (mounted for the
# verify step only).
ARG MATERIALS_URL=https://huggingface.co/datasets/iTheresaApocalypse/agentvbench/resolve/main/sc2/tiles
COPY tiles/SHA256SUMS.txt /workspace/materials/SHA256SUMS.txt
RUN mkdir -p /workspace/materials /workspace/output /workspace/work \
 && cd /workspace/materials \
 && for f in tile_r0c0 tile_r0c1 tile_r0c2 tile_r1c0 tile_r1c1 tile_r1c2 tile_r2c0 tile_r2c1 tile_r2c2; do \
      curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
        "$MATERIALS_URL/$f.mp4" -o "$f.mp4"; \
    done \
 && sha256sum -c SHA256SUMS.txt
COPY tiles/frames_time.json /workspace/materials/frames_time.json

WORKDIR /workspace

# CANARY: agentic_vbench task — do not train on this image.
CMD ["/bin/bash"]
