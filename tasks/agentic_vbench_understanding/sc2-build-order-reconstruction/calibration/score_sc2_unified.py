#!/usr/bin/env python3
"""
Unified-timeline F1 for SC2 build order: BOTH players' build events are pooled into
ONE chronological sequence and scored together (not per-player). Each event keyed by
(race, building_name); greedy 1:1 time-matched within tolerance. Primary tolerance
±3s (build order needs strict timing); relaxation shown for diagnosis only.

Usage: python score_sc2_unified.py --answer a.json --gt-terran gt_p1.json --gt-zerg gt_p2.json
"""
import argparse, json


def norm(s):
    return str(s or "").strip().lower().replace(" ", "")


def pool_gt(gt_terran, gt_zerg):
    ev = [("terran", norm(e["name"]), float(e["t"])) for e in gt_terran] + \
         [("zerg", norm(e["name"]), float(e["t"])) for e in gt_zerg]
    return sorted(ev, key=lambda x: x[2])


def pool_ans(ans):
    out = []
    for p in ans.get("players", []):
        race = norm(p.get("race"))
        for b in p.get("buildings", []):
            try:
                out.append((race, norm(b.get("name")), float(b.get("t_seconds", b.get("t")))))
            except Exception:
                pass
    return sorted(out, key=lambda x: x[2])


def f1(gt, pred, tol):
    used = [False] * len(gt)
    tp = 0
    for pr, pn, pt in pred:
        best, bd = -1, tol + 1
        for i, (gr, gn, gt_) in enumerate(gt):
            if used[i] or gr != pr or gn != pn:
                continue
            dt = abs(gt_ - pt)
            if dt <= tol and dt < bd:
                best, bd = i, dt
        if best >= 0:
            used[best] = True; tp += 1
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gt) if gt else 0.0
    return (2 * p * r / (p + r) if (p + r) else 0.0), tp, len(pred), len(gt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answer", required=True)
    ap.add_argument("--gt-terran", required=True)
    ap.add_argument("--gt-zerg", required=True)
    args = ap.parse_args()
    gt = pool_gt(json.load(open(args.gt_terran, encoding="utf-8"))["events"],
                 json.load(open(args.gt_zerg, encoding="utf-8"))["events"])
    try:
        pred = pool_ans(json.load(open(args.answer, encoding="utf-8")))
    except Exception as e:
        print(f"answer unreadable: {e}"); pred = []
    print(f"unified timeline: pred={len(pred)} events | gt={len(gt)} events")
    for tol in (3, 5, 10, 30):
        fs, tp, npred, ng = f1(gt, pred, tol)
        tag = "  <-- PRIMARY (build-order standard)" if tol == 3 else ""
        print(f"[±{tol:>2}s] unified F1 = {fs:.4f}  (tp={tp}/{ng}, pred={npred}){tag}")


if __name__ == "__main__":
    main()
