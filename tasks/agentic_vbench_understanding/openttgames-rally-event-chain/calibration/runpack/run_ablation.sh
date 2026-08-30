#!/bin/bash
# Degraded-input ablations. Each must score at or below 0.15; a pass here is what
# proves the task has no shortcut, so every number must come from a real run --
# never a constructed submission.
#
#   single-frame    one representative frame instead of the video
#   no-media        prompt and schema only, no media at all
#   frame-dump      every frame available, agent inspection tools removed
#
# video-only / audio-only are not run: this task declares audio as not required,
# so that pair does not apply.
#
# Usage: ./run_ablation.sh single-frame|no-media|frame-dump [codex-version]
set -euo pipefail

MODE="${1:?usage: ./run_ablation.sh single-frame|no-media|frame-dump}"
VER="${2:-0.147.0}"
TASK="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE=${TASK_IMAGE:-agentic-vbench-openttgames}
GATE=avb-netgate
CNAME="avb-abl-$MODE"
A="$(cd "$(dirname "$0")/.." && pwd)/ablations"
mkdir -p "$A"

docker inspect "$GATE" >/dev/null 2>&1 || { echo "FATAL: netgate not up"; exit 1; }
docker rm -f "$CNAME" >/dev/null 2>&1 || true
docker run -d --name "$CNAME" --network "container:$GATE" -w /workspace "$IMAGE" \
  sh -c 'sleep infinity' >/dev/null
docker cp "$TASK/steps/solve/instruction.md" "$CNAME:/workspace/instruction.md"
docker exec "$CNAME" mkdir -p /workspace/materials /workspace/output

case "$MODE" in
  single-frame)
    docker exec "$CNAME" sh -c '
      ffmpeg -nostdin -v error -ss 700 -i /baked/game.mp4 -frames:v 1 \
        /workspace/materials/frame.png'
    ;;
  no-media)
    : # materials stays empty on purpose
    ;;
  frame-dump)
    # one frame per second, and no tools: the point is to show agency matters,
    # so the agent gets the pixels but cannot drive ffmpeg itself.
    docker exec "$CNAME" sh -c '
      ffmpeg -nostdin -v error -i /baked/game.mp4 -vf fps=1 \
        /workspace/materials/f_%05d.png'
    ;;
  *) echo "unknown mode $MODE" >&2; exit 1 ;;
esac

"$(dirname "$0")/net_guard.sh" "ablation-$MODE-pre" "$A/$MODE.netguard.log"

docker exec "$CNAME" sh -c "
  apt-get update -qq && apt-get install -y -qq --no-install-recommends nodejs npm >/dev/null
  npm install -g @openai/codex@$VER >/dev/null 2>&1
"

SANDBOX="--sandbox workspace-write"
[ "$MODE" = "frame-dump" ] && SANDBOX="--sandbox read-only"

docker exec -e OPENAI_API_KEY="${OPENAI_API_KEY:?export OPENAI_API_KEY first}" \
  "$CNAME" sh -c "
    cd /workspace
    codex exec --json --skip-git-repo-check $SANDBOX \
      --config model_reasoning_effort=high \
      --config tools.web_search=false \
      \"\$(cat instruction.md)\" < /dev/null
  " > "$A/ablation_$MODE.jsonl" 2> "$A/ablation_$MODE.err" || true

docker cp "$CNAME:/workspace/output/solution.json" "$A/ablation_${MODE}_solution.json" 2>/dev/null \
  || echo '{"rallies": []}' > "$A/ablation_${MODE}_solution.json"

python3 "$TASK/steps/solve/tests/judge.py" \
  --solution "$A/ablation_${MODE}_solution.json" \
  --reference "$TASK/steps/solve/tests/reference.json" \
  --output "$A/ablation_${MODE}_reward.json" | tail -1

echo "ablation $MODE reward:"
python3 -c "import json;print('  ', json.load(open('$A/ablation_${MODE}_reward.json'))['reward'])"
echo "  (gate: must be <= 0.15)"
