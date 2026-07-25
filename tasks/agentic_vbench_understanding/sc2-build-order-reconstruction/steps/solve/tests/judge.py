#!/usr/bin/env python3
"""Grade a StarCraft II bird's-eye build-order reconstruction.

Pure Python stdlib, deterministic. No VLM/LLM judge.

Both players' build events are pooled into ONE chronological timeline and
scored together (not per-player). Each event is keyed by (race, structure_name);
a predicted event is a true positive only when it matches a GT event on that
key AND |Dt| <= 3 s (game-time). Greedy 1:1 match (closest time). reward = F1
over matched events. A wrong name, wrong race, or a mis-timed event does not
match, so guessing scores ~= 0.

Tolerance is tight (build order is order/timing-sensitive); the ~5 fps game-time
sampling (~0.18 s) makes +/-3 s physically achievable. Diagnose difficulty by
relaxing tolerance OFFLINE (see calibration/score_sc2_unified.py), not here.

Ground truth lives verifier-side in gt.json next to this script (mounted for the
verify step only; the agent never sees it). The answer is accepted in either of
two shapes (name/time reformatted only; content unchanged):
  A) {"players":[{"race":"terran","buildings":[{"t_seconds":20,"name":"SupplyDepot"}]}, ...]}
  B) {"player_1":[{"name":"Supply Depot","time":"00:40"}], "player_2":[...]}  (P1=terran, P2=zerg)
Name matching is case/space-insensitive; times may be seconds or "MM:SS".
"""
import argparse
import json
from pathlib import Path

TOL = 3.0  # seconds of game-time tolerance


def load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def n(s):
    return str(s if s is not None else "").strip().lower().replace(" ", "")


def to_sec(v):
    s = str(v).strip()
    if ":" in s:
        sec = 0
        for x in s.split(":"):
            sec = sec * 60 + int(x)
        return float(sec)
    return float(s)


def pool_gt(gt):
    ev = [(n(e["race"]), n(e["name"]), float(e["t"])) for e in gt["events"]]
    return sorted(ev, key=lambda x: x[2])


def pool_ans(ans):
    out = []
    if not isinstance(ans, dict):
        return out
    if "players" in ans:  # shape A
        for p in ans.get("players", []):
            race = n(p.get("race"))
            for b in p.get("buildings", []):
                try:
                    out.append((race, n(b.get("name")),
                                to_sec(b.get("t_seconds", b.get("t", b.get("time"))))))
                except Exception:
                    pass
    else:  # shape B: player_1 -> terran, player_2 -> zerg
        for key, race in (("player_1", "terran"), ("player_2", "zerg")):
            for b in ans.get(key, []):
                try:
                    out.append((race, n(b.get("name")),
                                to_sec(b.get("time", b.get("t_seconds", b.get("t"))))))
                except Exception:
                    pass
    return sorted(out, key=lambda x: x[2])


def score(gt, ans):
    G = pool_gt(gt)
    P = pool_ans(ans)
    used = [False] * len(G)
    tp = 0
    for pr, pn, pt in P:
        best, bd = -1, TOL + 1
        for i, (gr, gn, gt_) in enumerate(G):
            if used[i] or gr != pr or gn != pn:
                continue
            dt = abs(gt_ - pt)
            if dt <= TOL and dt < bd:
                best, bd = i, dt
        if best >= 0:
            used[best] = True
            tp += 1
    fp = max(0, len(P) - tp)
    fn = len(G) - tp
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return f1, {"matched": tp, "fp": fp, "fn": fn, "pred": len(P), "gt": len(G),
                "precision": round(prec, 4), "recall": round(rec, 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True, type=Path)
    ap.add_argument("--reward-json", required=True, type=Path)
    ap.add_argument("--reward-txt", required=True, type=Path)
    ap.add_argument("--gt", type=Path, default=None,
                    help="ground-truth JSON; defaults to gt.json next to this script")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    gt_path = args.gt if args.gt is not None else here / "gt.json"
    gt = load(gt_path, {"events": []})

    reason = "ok"
    ans = {}
    try:
        ans = json.loads(args.solution.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # malformed/missing output scores 0
        reason = f"unreadable solution.json: {exc}"

    reward, detail = score(gt, ans)
    detail["reason"] = reason
    detail["tolerance_s"] = TOL
    out = {"reward": round(reward, 4), "details": detail}
    args.reward_json.parent.mkdir(parents=True, exist_ok=True)
    args.reward_json.write_text(json.dumps(out, indent=2))
    args.reward_txt.write_text(f"{round(reward, 4)}\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
