#!/usr/bin/env python3
"""Build the P1 ground truth from a rendered session, install the oracle, and prove the
verifier discriminates.

    build_p1_gt_v11.py PLAY_JSON TASK_DIR

Scoring is order-based (see the task's judge.py), so no video-timestamp recovery is needed —
the bot's own event order *is* the ground truth. This script also runs the judge against
three deliberately wrong submissions and prints the scores, so a regression in the verifier
is visible immediately:

  oracle    exact ledger                      -> must be 1.0
  shuffled  right multiset, wrong order        -> should be low
  mono      the single most common token, xN   -> should be low
  mine_only actions right, all targets 'stone' -> should be low
"""
import json, random, re, subprocess, sys, tempfile
from pathlib import Path

play = json.loads(Path(sys.argv[1]).read_text())
task = Path(sys.argv[2])


def check_vocabulary(events, task_dir):
    """Every ground-truth target must appear in the instruction's closed vocabulary.

    An unlisted target is silently unanswerable: the agent is told the vocabulary is closed, so it
    cannot name a block outside it, yet the scorer still expects that token. `jungle_planks` sat in
    the builder's timber palette for three renders without being drawn -- the unfairness was live
    the whole time and only luck kept it out of the shipped ledger. Fail the build instead.
    """
    instr = (task_dir / "steps/solve/instruction.md").read_text()
    blocks = set(re.findall(r"`([a-z_]+)`", instr.split("Blocks (mine/place):")[1]
                                                 .split("Mobs (kill):")[0]))
    mobs = set(re.findall(r"`([a-z_]+)`", instr.split("Mobs (kill):")[1]
                                               .split("## How it is scored")[0]))
    bad = sorted({e["target"] for e in events
                  if e["target"] not in (mobs if e["action"] == "kill" else blocks)})
    if bad:
        sys.exit(f"VOCAB_FAIL {len(bad)} ground-truth target(s) missing from the instruction "
                 f"vocabulary: {bad}")
    print(f"vocab OK: {len({e['target'] for e in events})} distinct targets, "
          f"all within {len(blocks)} blocks + {len(mobs)} mobs")
tests = task / "steps/solve/tests"
sol_dir = task / "steps/solve/solution"

# Optional third arg: the last GO-relative second the video actually shows. Events after it were
# recorded by the bot but fall outside the captured window (the capture wrap can end a few seconds
# before the bot's final events), so keeping them in the ground truth would ask the agent to report
# actions the video never shows — the same off-camera unfairness, at the tail. Trim them.
raw = play["events"]
if len(sys.argv) > 3:
    cutoff_ms = float(sys.argv[3]) * 1000.0
    kept = [e for e in raw if e.get("t_ms", 0) <= cutoff_ms]
    if len(kept) != len(raw):
        print(f"tail-trim: dropped {len(raw)-len(kept)} event(s) after {sys.argv[3]}s "
              f"(outside the captured video)")
    raw = kept

events = [{k: v for k, v in e.items() if k in ("i", "action", "target", "tool")}
          for e in raw]
for i, e in enumerate(events):
    e["i"] = i

check_vocabulary(events, task)

gt = {"n_events": len(events), "events": events}
(tests / "ground_truth.json").write_text(json.dumps(gt, indent=2))

payload = json.dumps({"events": events}, indent=2)
solve = sol_dir / "solve.sh"
solve.write_text("#!/bin/bash\n"
                 "# Oracle: the machine-recorded gameplay ledger (mineflayer events +\n"
                 "# the bot's own placements), in play order, with the weapon per kill.\n"
                 "set -euo pipefail\n"
                 "mkdir -p \"$(dirname \"${SOLUTION_PATH:-/solution/solution.json}\")\"\n"
                 "cat > \"${SOLUTION_PATH:-/solution/solution.json}\" <<'JSON'\n"
                 + payload + "\nJSON\n")
solve.chmod(0o755)

def score(sub, tag):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "sol.json").write_text(json.dumps(sub))
        subprocess.run(["/usr/bin/python3", str(tests / "judge.py"), "--solution", str(td / "sol.json"),
                        "--reward-json", str(td / "r.json"), "--reward-txt", str(td / "r.txt")], check=True)
        r = json.loads((td / "r.json").read_text())
        d = r["details"]
        ledger = d.get("ledger_fbeta", d.get("ledger_f1", 0.0))     # F-beta (new) or F1 (old)
        print(f"  {tag:10s} reward={r['reward']:.4f}  ledger={ledger:.4f} "
              f"weapon={d['weapon_f1']:.4f}")
        return r["reward"]

rng = random.Random(0)
shuf = [dict(e) for e in events]; rng.shuffle(shuf)
from collections import Counter
top = Counter((e["action"], e["target"]) for e in events).most_common(1)[0][0]
mono = [{"action": top[0], "target": top[1]} for _ in events]
mine_only = [{"action": e["action"], "target": "stone", "tool": e.get("tool")} for e in events]

print(f"ground truth: {len(events)} events "
      f"({sum(e['action']=='mine' for e in events)} mine, "
      f"{sum(e['action']=='place' for e in events)} place, "
      f"{sum(e['action']=='kill' for e in events)} kill), "
      f"{len({e['target'] for e in events})} distinct targets")
r_oracle = score({"events": events}, "oracle")
score({"events": shuf}, "shuffled")
score({"events": mono}, "mono")
score({"events": mine_only}, "mine_only")
if abs(r_oracle - 1.0) > 1e-9:
    sys.exit("ORACLE IS NOT 1.0 — verifier and ground truth disagree")
print("oracle verified at 1.0")
