FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek and sample the clips. The grader is pure
# stdlib + numpy (it transforms baked mesh points by the reported poses).
RUN pip install --no-cache-dir numpy==2.1.3

# Bake the three egocentric clips + the agent-facing camera / query / object lists at
# build time: pinned URL and SHA256 verified at build. Media hosted on Hugging Face
# (see the task README). The answer key is baked separately and never staged into the
# agent workspace.
ARG MATERIALS_BASE=https://huggingface.co/datasets/yalesunxiatao/agentic_vbench_understanding_objects/resolve/main
ARG CLIP01_SHA256=aefb41b216cc2cbacfca639de8175a29f37006c3be730b118928ce20e27d19ee
ARG CLIP02_SHA256=b187d5cbaba972ca715f0ffd670b99b1c77ee9ad579d40b3acdff1b564c114ae
ARG CLIP03_SHA256=56c42f94baecf5a78e2b6e32ed5af59719b51badfc6405d3f67d9b26bbc77520

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
      "${MATERIALS_BASE}/objects.json" -o /baked/objects.json \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/ground_truth.json" -o /baked/ground_truth.json \
 && test -s /baked/clip_01.mp4 && test -s /baked/clip_02.mp4 && test -s /baked/clip_03.mp4

WORKDIR /workspace
RUN mkdir -p /workspace/materials /workspace/output /workspace/work
