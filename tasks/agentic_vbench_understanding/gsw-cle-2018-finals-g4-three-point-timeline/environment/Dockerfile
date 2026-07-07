FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek and sample frames. The grader is pure
# stdlib (it only compares integers), so it needs nothing extra.

# Bake the full-game broadcast at build time, the same way the v1.0 families do,
# with a pinned URL and a SHA256 verified at build (see the repo's sequencing
# Dockerfile for the pattern).
#
# TODO before this is a real task:
#   1. Re-host the archive.org file on Hugging Face (or pin the direct archive.org
#      file URL) so the bytes are stable, and put the exact URL here.
#   2. (DONE) The exact archive.org file URL is set below. SHA256 is filled in once
#      the file finishes downloading and is hashed.
ARG MATERIALS_URL=https://archive.org/download/2018-nba-finals-game-4-cleveland-cavaliers-vs-golden-state-warriors-jun-8-2018/2018%20NBA%20Finals%20Game%204%20Cleveland%20Cavaliers%20vs%20Golden%20State%20Warriors%20Jun%208%20%202018.mp4
ARG MATERIALS_SHA256=6df565f0708a9a6b0f80c2b02bcb7d5211e48abd234d752cf607525adcb30757
RUN mkdir -p /baked \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "$MATERIALS_URL" -o /baked/game.mp4 \
 && echo "${MATERIALS_SHA256}  /baked/game.mp4" | sha256sum -c - \
 && test -s /baked/game.mp4

WORKDIR /workspace
RUN mkdir -p /workspace/materials /workspace/output /workspace/work
