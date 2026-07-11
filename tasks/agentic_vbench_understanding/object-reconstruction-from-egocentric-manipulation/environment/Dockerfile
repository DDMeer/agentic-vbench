FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The agent uses ffmpeg/ffprobe to seek and sample the clips. The grader samples and
# aligns point clouds, so it needs numpy + scipy + trimesh.
RUN pip install --no-cache-dir numpy==2.1.3 scipy==1.14.1 trimesh==4.5.3

# Bake the three egocentric clips + the agent-facing camera / object lists AND the
# reference meshes (used only by the oracle + verifier, never staged to the agent) at
# build time: pinned URL and SHA256 verified at build. Media hosted on Hugging Face
# (see the task README).
ARG MATERIALS_BASE=https://huggingface.co/datasets/yalesunxiatao/agentic_vbench_understanding_recon/resolve/main
ARG CLIP01_SHA256=2f153d49b5c6b61e58d6b648af1002718dddd2fe2b32c6ba28d4e9d80d388a1c
ARG CLIP02_SHA256=bbfabad6a5e5736de3ec5de7d31cee679c8c8267fdb0bc88ca52bcc8c82f47e6
ARG CLIP03_SHA256=9d2cd0f8127622bc5805f4cbaf83efcbf17a9ad8d1f46748a26a9ccb7c5ab546

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
      "${MATERIALS_BASE}/objects.json" -o /baked/objects.json \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/ref_clip_01.glb" -o /baked/ref_clip_01.glb \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/ref_clip_02.glb" -o /baked/ref_clip_02.glb \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 \
      "${MATERIALS_BASE}/ref_clip_03.glb" -o /baked/ref_clip_03.glb \
 && test -s /baked/clip_01.mp4 && test -s /baked/clip_02.mp4 && test -s /baked/clip_03.mp4

WORKDIR /workspace
RUN mkdir -p /workspace/materials /workspace/output /workspace/work
