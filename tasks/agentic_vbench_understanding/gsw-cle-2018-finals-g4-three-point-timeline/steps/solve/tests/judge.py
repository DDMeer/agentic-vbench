#!/usr/bin/env python3
"""Grade a three-point-timeline reconstruction. Pure Python stdlib, deterministic.

The agent must list every made three-pointer with quarter, game clock, shooter, and
assister. A predicted three is a true positive only when it FULLY reconstructs the
play: same quarter, same shooter, same assister, and a game clock within TOL seconds.
We then score by F1 (so misses and false positives both hurt). reward = F1.

Why this task and metric: a full game has ~20 made threes scattered across 2.5 hours.
No broadcast graphic lists them, no one memorizes their timestamps, and identifying
the passer on each one requires watching the play, so only genuinely reconstructing
the game off the video scores. The oracle (exact list) -> 1.0; an empty or guessed
list -> ~0; a strong agent that mostly mis-attributes shooters/assisters -> well
below 0.1.
"""
import argparse
import json
import re
from pathlib import Path

TOL = 5  # seconds of game-clock tolerance (the broadcast clock is exact; reads should be close)

GROUND_TRUTH = [
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


def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())


def clock_secs(cv):
    cv = str(cv).strip()
    try:
        if ":" in cv:
            m, s = cv.split(":")
            return int(m) * 60 + int(float(s))
        return int(float(cv))
    except (ValueError, AttributeError):
        return None


# Lastnames that are unique among GT shooters can be matched on lastname alone;
# ambiguous ones (e.g. two "Green"s) require the full name to match.
def _lastname(name):
    return norm(name.split()[-1]) if str(name).split() else norm(name)


_GT_LASTS = [_lastname(g["shooter"]) for g in GROUND_TRUTH]
_UNIQUE_LASTS = {ln for ln in _GT_LASTS if _GT_LASTS.count(ln) == 1}


def shooter_match(pred, gt_full):
    p, g = norm(pred), norm(gt_full)
    if not p:
        return False
    if p == g:
        return True
    gl = _lastname(gt_full)
    return gl in _UNIQUE_LASTS and p == gl  # lastname only if unambiguous


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True, type=Path)
    ap.add_argument("--reward-json", required=True, type=Path)
    ap.add_argument("--reward-txt", required=True, type=Path)
    args = ap.parse_args()

    reason = "ok"
    preds = []
    try:
        sol = json.loads(args.solution.read_text())
        preds = sol.get("three_pointers", [])
        if not isinstance(preds, list):
            raise ValueError("three_pointers is not a list")
    except Exception as exc:  # noqa: BLE001 - malformed output scores 0
        reason, preds = f"unreadable solution.json: {exc}", []

    used = [False] * len(GROUND_TRUTH)      # for strict (full-play) TPs
    used_loose = [False] * len(GROUND_TRUTH)  # shooter+time only, for diagnostics
    tp = 0
    shooter_time_only = 0
    for pr in preds:
        if not isinstance(pr, dict):
            continue
        pq = pr.get("quarter")
        ps = clock_secs(pr.get("clock"))
        if ps is None:
            continue
        # diagnostic: did it at least get quarter+shooter+clock right?
        for i, gt in enumerate(GROUND_TRUTH):
            if not used_loose[i] and pq == gt["quarter"] \
                    and shooter_match(pr.get("shooter", ""), gt["shooter"]) \
                    and abs(ps - clock_secs(gt["clock"])) <= TOL:
                used_loose[i] = True
                shooter_time_only += 1
                break
        # scored: full-play reconstruction (also requires the assister)
        for i, gt in enumerate(GROUND_TRUTH):
            if not used[i] and pq == gt["quarter"] \
                    and shooter_match(pr.get("shooter", ""), gt["shooter"]) \
                    and norm(pr.get("assister", "")) == norm(gt["assister"]) \
                    and abs(ps - clock_secs(gt["clock"])) <= TOL:
                used[i] = True
                tp += 1
                break

    n_pred, n_gt = len(preds), len(GROUND_TRUTH)
    precision = tp / n_pred if n_pred else 0.0
    recall = tp / n_gt if n_gt else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    details = {
        "reason": reason,
        "n_ground_truth": n_gt,
        "n_predicted": n_pred,
        "true_positives_full_play": tp,
        "shooter_time_only_matches": shooter_time_only,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "clock_tolerance_s": TOL,
    }
    args.reward_json.parent.mkdir(parents=True, exist_ok=True)
    args.reward_json.write_text(json.dumps({"reward": round(f1, 4), "details": details}, indent=2))
    args.reward_txt.write_text(f"{round(f1, 4)}\n")


if __name__ == "__main__":
    main()
