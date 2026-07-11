FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek and sample the clips. The grader is pure
# stdlib + numpy (it only compares 3D coordinates), installed here for the verifier.
RUN pip install --no-cache-dir numpy==2.1.3

# Bake the three egocentric clips + the agent-facing camera models and query list at
# build time, the same way the v1.0 families bake their media: a pinned URL and a
# SHA256 verified at build. The clips and their ground truth are hosted on Hugging Face
# (see the task README); the answer key itself is baked separately and never staged
# into the agent workspace.
ARG MATERIALS_BASE=https://huggingface.co/datasets/yalesunxiatao/agentic_vbench_understanding_hands/resolve/main
ARG CLIP01_SHA256=22d4f7e060ee79eb77eadd58b92c0f3a3e840640aba2f3afc6322aee47c8b729
ARG CLIP02_SHA256=5323761ef008f7f0e3d317a9b477c4f9ffd80da6da3504b3280324af93a47544
ARG CLIP03_SHA256=6fc266fd070b00e547642ef3e0613ef82ca13a58b8042a86c4259f7bf8269874

RUN mkdir -p /baked \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/clip_01.mp4" -o /baked/clip_01.mp4 \
 && echo "${CLIP01_SHA256}  /baked/clip_01.mp4" | sha256sum -c - \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/clip_02.mp4" -o /baked/clip_02.mp4 \
 && echo "${CLIP02_SHA256}  /baked/clip_02.mp4" | sha256sum -c - \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/clip_03.mp4" -o /baked/clip_03.mp4 \
 && echo "${CLIP03_SHA256}  /baked/clip_03.mp4" | sha256sum -c - \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/cameras.json" -o /baked/cameras.json \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/queries.json" -o /baked/queries.json \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/ground_truth.json" -o /baked/ground_truth.json \
 && test -s /baked/clip_01.mp4 && test -s /baked/clip_02.mp4 && test -s /baked/clip_03.mp4

WORKDIR /workspace
RUN mkdir -p /workspace/materials /workspace/output /workspace/work
