#!/bin/bash
# Degraded-input ablations. Each must score at or below 0.15; a pass here is what
# proves the task has no shortcut, so every number must come from a real run --
# never a constructed submission.
#
#   single-frame    one representative frame instead of the video
#   no-media        prompt and schema only, no media at all
#   frame-dump      frames pre-extracted at 1 fps (1435 PNGs), ffmpeg/ffprobe/ffplay
#                   removed afterwards. This is a documented substitute for the
#                   family's literal frame_dump_no_tools, not that condition: the
#                   agent keeps a shell, because Codex's only tool is the shell and
#                   `--sandbox read-only` would leave it unable to write
#                   output/solution.json at all.
#
# video-only / audio-only are not run: this task declares audio as not required,
# so that pair does not apply.
#
# Usage: ./run_ablation.sh single-frame|no-media|frame-dump [codex-version]
set -euo pipefail

MODE="${1:?usage: ./run_ablation.sh single-frame|no-media|no-media-forced|frame-dump}"
VER="${2:-0.147.0}"
TASK="$(cd "$(dirname "$0")/../.." && pwd)"
IMAGE=${TASK_IMAGE:-agentic-vbench-openttgames}
GATE=${AVB_GATE:-avb-netgate}
CNAME="avb-abl-$MODE"
A="$(cd "$(dirname "$0")/.." && pwd)/ablations"
mkdir -p "$A"

docker inspect "$GATE" >/dev/null 2>&1 || { echo "FATAL: netgate not up"; exit 1; }
docker rm -f "$CNAME" >/dev/null 2>&1 || true
MEM_MB=$(awk -F'[= ]+' '/^memory_mb/{print $2}' "$TASK/task.toml" | head -1)
CPUS=$(awk -F'[= ]+' '/^cpus/{print $2}' "$TASK/task.toml" | head -1)
docker run -d --name "$CNAME" --network "container:$GATE" -w /workspace \
  --memory="${MEM_MB:-8192}m" --memory-swap="${MEM_MB:-8192}m" --cpus="${CPUS:-4}" \
  "$IMAGE" sh -c 'sleep infinity' >/dev/null
echo "  budget: ${MEM_MB:-8192}MB / ${CPUS:-4} cpus   gate: $GATE"
docker cp "$TASK/steps/solve/instruction.md" "$CNAME:/workspace/instruction.md"
# Same harness rules as the canonical run. Without this the ablation would differ
# from canonical in two ways at once and would not isolate the input degradation.
for f in AGENTS.md GEMINI.md CLAUDE.md; do
  docker cp "$(dirname "$0")/AGENTS.md" "$CNAME:/workspace/$f" >/dev/null 2>&1
done
docker exec "$CNAME" mkdir -p /workspace/materials /workspace/output /opt/codex-home
if [ -f "$HOME/.codex/auth.json" ]; then
  docker cp "$HOME/.codex/auth.json" "$CNAME:/opt/codex-home/auth.json"
  docker exec "$CNAME" chmod 600 /opt/codex-home/auth.json
elif [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "FATAL: no ~/.codex/auth.json and no OPENAI_API_KEY" >&2; exit 1
fi

case "$MODE" in
  single-frame)
    docker exec "$CNAME" sh -c '
      ffmpeg -nostdin -v error -ss 700 -i /baked/game.mp4 -frames:v 1 \
        /workspace/materials/frame.png'
    ;;
  no-media|no-media-forced)
    : # materials stays empty on purpose
    ;;
  frame-dump)
    # one frame per second, then the extraction tooling is removed: the point is
    # to show agency matters, so the agent gets the pixels but cannot drive
    # ffmpeg itself.
    #
    # The tools are removed from the container rather than by running the agent
    # under `--sandbox read-only`. read-only makes /workspace unwritable, so the
    # agent cannot write output/solution.json at all -- that scores 0.0 by
    # construction, which proves nothing about whether frames alone suffice.
    # Verified directly: `codex sandbox -c sandbox_mode="read-only"` fails a
    # write to /workspace/output with "Read-only file system".
    docker exec "$CNAME" sh -c '
      ffmpeg -nostdin -v error -i /baked/game.mp4 -vf fps=1 \
        /workspace/materials/f_%05d.png
      FF=$(command -v ffmpeg || true); FP=$(command -v ffprobe || true); FL=$(command -v ffplay || true)
      rm -f "$FF" "$FP" "$FL" 2>/dev/null
      for b in "$FF" "$FP" "$FL"; do
        [ -n "$b" ] && [ -e "$b" ] && { echo "FATAL: $b still present" >&2; exit 1; }
      done
      echo "  extracted $(ls /workspace/materials | wc -l) frames; ffmpeg/ffprobe removed"'
    ;;
  *) echo "unknown mode $MODE" >&2; exit 1 ;;
esac

if [ "$MODE" = no-media-forced ]; then
  docker exec "$CNAME" sh -c 'cat >> /workspace/instruction.md <<'"'"'EOF'"'"'

## Ablation condition

No media is provided for this run. Produce your best-effort `output/solution.json`
in the required schema regardless. Do not stop to ask for the media and do not
finish without writing the file.
EOF'
fi

"$(dirname "$0")/net_guard.sh" "ablation-$MODE-pre" "$A/$MODE.netguard.log"

# Package mirrors are CDN-backed and rotate; re-pin them right before apt runs.
"$(dirname "$0")/netgate.sh" install
docker exec "$CNAME" sh -c "
  apt-get update -qq && apt-get install -y -qq --no-install-recommends nodejs npm >/dev/null
  npm install -g @openai/codex@$VER >/dev/null 2>&1
" || true
docker exec "$CNAME" codex --version >/dev/null 2>&1 || {
  echo "FATAL: codex did not install - not starting a scored phase" >&2; exit 1; }

# Package hosts must not stay reachable during the scored phase.
"$(dirname "$0")/netgate.sh" lock

{
  echo "ablation:        $MODE"
  echo "harness:         Codex CLI"
  echo "harness version: $(docker exec "$CNAME" codex --version 2>/dev/null)"
  echo "model:           gpt-5.6-sol"
  echo "reasoning:       high"
  echo "web_search:      false"
  echo "gate:            $GATE"
  echo "task commit:     $(git -C "$TASK" rev-parse HEAD)"
  echo "rules sha256:    $(shasum -a 256 "$(dirname "$0")/AGENTS.md" | awk '{print $1}')"
  echo "started:         $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$A/ablation_${MODE}_metadata.txt"

SANDBOX="--sandbox workspace-write"

docker exec -e CODEX_HOME=/opt/codex-home \
  ${OPENAI_API_KEY:+-e OPENAI_API_KEY="$OPENAI_API_KEY"} \
  "$CNAME" sh -c "
    cd /workspace
    codex exec --json --skip-git-repo-check $SANDBOX \
      --config model_reasoning_effort=high \
      --config model=gpt-5.6-sol \
      --config tools.web_search=false \
      \"\$(cat instruction.md)\" < /dev/null
  " > "$A/ablation_$MODE.jsonl" 2> "$A/ablation_$MODE.err" || true

"$(dirname "$0")/net_guard.sh" "ablation-$MODE-post" "$A/$MODE.netguard.log"

docker cp "$CNAME:/workspace/output/solution.json" "$A/ablation_${MODE}_solution.json" 2>/dev/null \
  || echo '{"rallies": []}' > "$A/ablation_${MODE}_solution.json"

python3 "$TASK/steps/solve/tests/judge.py" \
  --solution "$A/ablation_${MODE}_solution.json" \
  --reference "$TASK/steps/solve/tests/reference.json" \
  --output "$A/ablation_${MODE}_reward.json" | tail -1

echo "ablation $MODE reward:"
python3 -c "import json;print('  ', json.load(open('$A/ablation_${MODE}_reward.json'))['reward'])"
echo "  (gate: must be <= 0.15)"
