"""Deterministic scorer for sc2-build-order-reconstruction. No LLM/VLM judge.

Both players' build events are pooled into ONE chronological timeline and scored
together (not per-player). Each event is keyed by (race, structure_name); a predicted
event scores iff it matches a GT event on that key AND |Dt| <= 3s (game-time). Greedy
1:1 match (closest time). reward = F1 over matched events. A wrong name, wrong race, or
a mis-timed event does not match, so guessing ~= 0.

Tolerance is tight (build order is order/timing-sensitive); the ~5 fps game-time
sampling (~0.18s) makes +/-3s physically achievable. Diagnose difficulty by relaxing
TOL OFFLINE (see calibration/score_sc2_unified.py), not in this scorer.

GT (gt.json, sibling of this script): {"events":[{"race","name","t"}...]} pooled terran+zerg.
Answer (--solution): accepted in either of two shapes (name/time reformatted only;
content unchanged):
  A) {"players":[{"race":"terran","buildings":[{"t_seconds":20,"name":"SupplyDepot"}]}, ...]}
  B) {"player_1":[{"name":"Supply Depot","time":"00:40"}], "player_2":[...]}  (P1=terran, P2=zerg)
Name matching is case/space-insensitive; times may be seconds or "MM:SS".
"""
import argparse
import json
from pathlib import Path

TOL = 3.0


def load(p, default=None):
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return default


def norm(s):
    return str(s if s is not None else "").strip().lower().replace(" ", "")


def to_sec(v):
    s = str(v).strip()
    if ":" in s:
        parts = [int(x) for x in s.split(":")]
        sec = 0
        for x in parts:
            sec = sec * 60 + x
        return float(sec)
    return float(s)


def pool_gt(gt):
    ev = [(norm(e["race"]), norm(e["name"]), float(e["t"])) for e in gt["events"]]
    return sorted(ev, key=lambda x: x[2])


def pool_ans(ans):
    out = []
    if not isinstance(ans, dict):
        return out
    if "players" in ans:  # shape A
        for p in ans.get("players", []):
            race = norm(p.get("race"))
            for b in p.get("buildings", []):
                try:
                    out.append((race, norm(b.get("name")), to_sec(b.get("t_seconds", b.get("t", b.get("time"))))))
                except Exception:
                    pass
    else:  # shape B: player_1 -> terran, player_2 -> zerg
        for key, race in (("player_1", "terran"), ("player_2", "zerg")):
            for b in ans.get(key, []):
                try:
                    out.append((race, norm(b.get("name")), to_sec(b.get("time", b.get("t_seconds", b.get("t"))))))
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
    return f1, {"matched": tp, "pred": len(P), "gt": len(G),
                "precision": round(prec, 4), "recall": round(rec, 4), "tol_s": TOL}


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True, type=Path)
    ap.add_argument("--reward-json", required=True, type=Path)
    ap.add_argument("--reward-txt", required=True, type=Path)
    ap.add_argument("--gt", type=Path, default=here / "gt.json")
    args = ap.parse_args()

    gt = load(args.gt)
    ans = load(args.solution, {})
    reward, details = score(gt, ans)
    out = {"reward": round(reward, 4), "details": details}
    args.reward_json.parent.mkdir(parents=True, exist_ok=True)
    args.reward_json.write_text(json.dumps(out, indent=2))
    args.reward_txt.write_text(f"{round(reward, 4)}\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
