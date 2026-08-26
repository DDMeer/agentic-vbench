#!/usr/bin/env bash
# Verifier entrypoint: score the agent's /output/answer.json against the pinned GT with the
# deterministic unified-timeline F1 scorer, writing reward.json. Pure code, no VLM/LLM.
set -euo pipefail
cd "$(dirname "$0")"
export GT_PATH="${GT_PATH:-$(pwd)/gt.json}"
export ANSWER_PATH="${ANSWER_PATH:-/output/answer.json}"
export REWARD_PATH="${REWARD_PATH:-/output/reward.json}"
python judge.py
cat "$REWARD_PATH"
