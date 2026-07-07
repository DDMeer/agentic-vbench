#!/bin/bash
# Oracle: write the verified three-point timeline as solution.json.
#
# The reference answer is the official play-by-play (from ESPN's structured feed for
# this game): every made three-pointer with quarter, game clock, shooter, assister.
# Like the Assembly oracle, this is the verified answer key, not an echo of the input.
# The agent never sees this file.
set -euo pipefail

mkdir -p /workspace/output

python3 - <<'PY'
import json
from pathlib import Path

THREES = [
  {"quarter": 1, "clock": "11:02", "shooter": "JR Smith",       "assister": "LeBron James"},
  {"quarter": 1, "clock": "8:47",  "shooter": "Stephen Curry",  "assister": "unassisted"},
  {"quarter": 1, "clock": "6:38",  "shooter": "Kevin Love",     "assister": "LeBron James"},
  {"quarter": 1, "clock": "6:25",  "shooter": "Andre Iguodala", "assister": "Draymond Green"},
  {"quarter": 1, "clock": "6:03",  "shooter": "Stephen Curry",  "assister": "unassisted"},
  {"quarter": 1, "clock": "5:42",  "shooter": "Draymond Green", "assister": "Kevin Durant"},
  {"quarter": 1, "clock": "3:59",  "shooter": "Kevin Love",     "assister": "Jeff Green"},
  {"quarter": 1, "clock": "2:39",  "shooter": "Nick Young",     "assister": "Kevin Durant"},
  {"quarter": 1, "clock": "1:35",  "shooter": "Andre Iguodala", "assister": "Jordan Bell"},
  {"quarter": 2, "clock": "11:36", "shooter": "Jeff Green",     "assister": "Larry Nance Jr."},
  {"quarter": 2, "clock": "4:36",  "shooter": "Andre Iguodala", "assister": "Draymond Green"},
  {"quarter": 2, "clock": "3:54",  "shooter": "JR Smith",       "assister": "LeBron James"},
  {"quarter": 2, "clock": "3:12",  "shooter": "Stephen Curry",  "assister": "unassisted"},
  {"quarter": 2, "clock": "1:20",  "shooter": "JR Smith",       "assister": "LeBron James"},
  {"quarter": 2, "clock": "5.0",   "shooter": "Stephen Curry",  "assister": "Kevin Durant"},
  {"quarter": 3, "clock": "5:52",  "shooter": "Klay Thompson",  "assister": "Kevin Durant"},
  {"quarter": 3, "clock": "4:58",  "shooter": "Rodney Hood",    "assister": "LeBron James"},
  {"quarter": 3, "clock": "2:12",  "shooter": "Klay Thompson",  "assister": "Kevin Durant"},
  {"quarter": 4, "clock": "11:11", "shooter": "Stephen Curry",  "assister": "Draymond Green"},
  {"quarter": 4, "clock": "10:01", "shooter": "George Hill",    "assister": "Larry Nance Jr."},
  {"quarter": 4, "clock": "9:45",  "shooter": "Stephen Curry",  "assister": "unassisted"},
  {"quarter": 4, "clock": "6:19",  "shooter": "Stephen Curry",  "assister": "Draymond Green"},
]

Path("/workspace/output/solution.json").write_text(json.dumps({"three_pointers": THREES}, indent=2))
PY

echo "oracle: wrote /workspace/output/solution.json (22 threes)"
