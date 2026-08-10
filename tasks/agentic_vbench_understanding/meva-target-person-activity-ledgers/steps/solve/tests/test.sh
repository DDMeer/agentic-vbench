#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier /logs/artifacts

if [ -f /workspace/output/solution.json ]; then
    cp /workspace/output/solution.json /logs/artifacts/submitted_solution.json
fi

python3 /tests/judge.py \
    --solution /workspace/output/solution.json \
    --ground-truth /tests/ground_truth.json \
    --reward-json /logs/verifier/reward.json \
    --reward-txt /logs/verifier/reward.txt
