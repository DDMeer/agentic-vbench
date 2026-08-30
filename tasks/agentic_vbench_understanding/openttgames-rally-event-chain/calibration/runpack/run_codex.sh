#!/bin/bash
# Official Codex calibration run (GPT-5.6 Sol, high reasoning).
#
# Two independent layers block lookup:
#   1. harness level - `--sandbox workspace-write` denies the agent's own shell
#      commands any network, and `tools.web_search=false` removes the search tool;
#   2. container level - the shared netgate namespace drops GitHub, the raw
#      content CDN and the dataset host outright (see net_guard.sh).
# The CLI's model calls still leave the namespace: that is inference, not lookup.
#
# The CLI is installed into the *run* container, never into the shipped image.
# Usage: ./run_codex.sh [codex-version]
set -euo pipefail

CNAME=avb-run-codex
VER="${1:-0.147.0}"
MODEL="${2:-gpt-5.6-sol}"
TASK="$(cd "$(dirname "$0")/../.." && pwd)"
R="$(cd "$(dirname "$0")/.." && pwd)/rollouts"
mkdir -p "$R"

docker inspect "$CNAME" >/dev/null 2>&1 || { echo "run ./stage_workspace.sh codex first"; exit 1; }
"$(dirname "$0")/net_guard.sh" codex-pre "$R/codex.netguard.log"

echo "installing codex@$VER into the run container (calibration-only, not in the shipped image)"
docker exec "$CNAME" sh -c "
  apt-get update -qq && apt-get install -y -qq --no-install-recommends nodejs npm >/dev/null
  npm install -g @openai/codex@$VER >/dev/null 2>&1
  codex --version
" | sed 's/^/  /'

# Tighten the gate before scoring: the package hosts needed for the install
# above must not stay reachable during the run itself.
"$(dirname "$0")/netgate.sh" lock

# Record exactly what is being run; scores.md cites this file.
{
  echo "harness:        Codex CLI"
  echo "harness version: $(docker exec "$CNAME" codex --version 2>/dev/null)"
  echo "model:          $MODEL"
  echo "reasoning:      high"
  echo "task commit:    $(git -C "$TASK" rev-parse HEAD)"
  echo "image:          ${TASK_IMAGE:-agentic-vbench-openttgames}"
  echo "started:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$R/codex_run_metadata.txt"

echo "launching codex; this is a long-horizon run"
docker exec -e CODEX_HOME=/opt/codex-home \
  ${OPENAI_API_KEY:+-e OPENAI_API_KEY="$OPENAI_API_KEY"} \
  "$CNAME" sh -c '
    cd /workspace
    codex exec --json --skip-git-repo-check \
      --sandbox workspace-write \
      --config model='"$MODEL"' \
      --config model_reasoning_effort=high \
      --config tools.web_search=false \
      "$(cat instruction.md)" < /dev/null
  ' > "$R/codex_gpt-5.6-sol.jsonl" 2> "$R/codex_gpt-5.6-sol.err" || true

"$(dirname "$0")/net_guard.sh" codex-post "$R/codex.netguard.log"
docker cp "$CNAME:/workspace/output/solution.json" "$R/codex_solution.json" 2>/dev/null \
  || echo "  no solution.json produced - record as an incomplete run scoring 0.0"

echo "rollout: $R/codex_gpt-5.6-sol.jsonl"
echo "next:    ./audit_and_grade.sh codex $R/codex_gpt-5.6-sol.jsonl"
echo "NOTE: record codex --version and the resolved model id in scores.md."
