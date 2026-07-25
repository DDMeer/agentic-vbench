FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG MATERIALS_URL=https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/main/minecraft-gameplay-ledger-s1/game_v31_long.mp4
ARG MATERIALS_SHA256=24623fc3fd7e4fdf8a78a5322bfa0374b6dd6fff975eb178e74e270e9f3a097c
RUN mkdir -p /baked \
 && curl --fail --silent --show-error --location --retry 5 --retry-delay 3 "$MATERIALS_URL" -o /baked/game.mp4 \
 && echo "${MATERIALS_SHA256}  /baked/game.mp4" | sha256sum -c - && test -s /baked/game.mp4
WORKDIR /workspace
RUN mkdir -p /workspace/materials /workspace/output /workspace/work
