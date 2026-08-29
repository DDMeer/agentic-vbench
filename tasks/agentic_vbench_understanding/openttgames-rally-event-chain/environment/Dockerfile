ARG PYTHON_IMAGE=python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

FROM ${PYTHON_IMAGE} AS media-build

ARG MATERIALS_URL=https://lab.osai.ai/datasets/openttgames/data/game_2.mp4
ARG MATERIALS_SHA256=330ac07730bae6d899dbbbd00ad43500c583e6af6ea6dd261565bc77811eba66

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /baked \
    && curl --fail --silent --show-error --location --retry 5 \
        "${MATERIALS_URL}" \
        -o /baked/game.mp4 \
    && echo "${MATERIALS_SHA256}  /baked/game.mp4" | sha256sum -c -

FROM ${PYTHON_IMAGE}

ARG CODEX_VERSION=0.147.0

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        curl \
        bash \
        nodejs \
        npm \
        ripgrep \
    && npm install -g "@openai/codex@${CODEX_VERSION}" \
    && codex --version \
    && command -v codex \
    && command -v node \
    && command -v npm \
    && command -v rg \
    && rm -rf /var/lib/apt/lists/* \
    && npm cache clean --force

COPY --from=media-build /baked/game.mp4 /baked/game.mp4

RUN echo "330ac07730bae6d899dbbbd00ad43500c583e6af6ea6dd261565bc77811eba66  /baked/game.mp4" \
    | sha256sum -c -

WORKDIR /workspace

RUN mkdir -p \
    /workspace/materials \
    /workspace/output \
    /workspace/work
