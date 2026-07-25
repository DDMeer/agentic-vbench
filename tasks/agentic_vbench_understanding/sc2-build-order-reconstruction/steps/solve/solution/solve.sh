#!/bin/bash
# Oracle: write the verified build-order timeline as solution.json.
#
# The reference answer is the 100-event ground truth machine-parsed from the
# SAME .SC2Replay the video was rendered from (SC2 engine tracker events ->
# construction-start times); no manual annotation. The agent never sees this
# file.
#
# gt.json lives verifier-side next to judge.py; the oracle runs with the task
# source tree available, so it reads it from there and emits it in the agent
# output schema.
set -euo pipefail

mkdir -p /workspace/output
GT="$(dirname "$0")/../tests/gt.json"

python3 - "$GT" <<'PY'
import json, sys
from pathlib import Path
gt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
players = {}
for e in sorted(gt["events"], key=lambda x: x["t"]):
    players.setdefault(e["race"], []).append({"t_seconds": e["t"], "name": e["name"]})
ans = {"players": [{"race": r, "buildings": b} for r, b in players.items()]}
Path("/workspace/output/solution.json").write_text(
    json.dumps(ans, ensure_ascii=False, indent=2)
)
n = sum(len(b) for b in players.values())
print(f"oracle: wrote /workspace/output/solution.json ({n} events)")
PY
