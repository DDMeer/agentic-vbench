#!/usr/bin/env bash
# Oracle: the answer is the authoritative build-order GT, machine-parsed from the SAME
# .SC2Replay the video was rendered from (engine tracker events -> construction-start times).
# The agent only sees the 9 bird's-eye tiles; the oracle reproduces the exact answer from
# the replay, so it scores reward = 1.0. Both players are emitted in the answer schema.
set -euo pipefail
GT="${GT_PATH:-/data/gt.json}"          # pooled {"events":[{race,name,t}...]}
OUT="${OUTPUT_PATH:-/output/answer.json}"
python - "$GT" "$OUT" <<'PY'
import json, io, sys
gt = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))["events"]
players = {"terran": [], "zerg": []}
for e in sorted(gt, key=lambda x: x["t"]):
    players.setdefault(e["race"], []).append({"t_seconds": e["t"], "name": e["name"]})
ans = {"players": [{"race": r, "buildings": b} for r, b in players.items()]}
json.dump(ans, io.open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
print("wrote", sys.argv[2], "->", sum(len(b) for b in players.values()), "events")
PY
