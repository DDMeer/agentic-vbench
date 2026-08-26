#!/usr/bin/env python
"""Score every archived rollout and ablation against the pooled GT and print the tables
used in calibration/scores.md.

The primary reward is the verifier's (steps/solve/tests/judge.py): unified-timeline F1 at
+/-3 s. The extra columns exist only to answer one question: does having the video help?
An agent with NO footage (`abl_no_media`, `abl_recall`) is the guessing floor; a task that
measures video understanding must score clearly above it.

    python calibration/ablation_table.py
    python calibration/ablation_table.py --audit      # scorer sanity check, see scores.md
    python calibration/ablation_table.py --leakfree   # re-score without the 4 prompt-leaked events
"""
import io
import json
import os

GT = "steps/solve/tests/gt.json"
RUNS = [
    ("opus-4.8 (video)", "calibration/rollouts/opus-4.8_v320.answer.json"),
    ("opus-4.8 leak-free prompt (video)", "calibration/rollouts/opus-4.8_v320_leakfree.answer.json"),
    ("codex gpt-5.6-sol (video)", "calibration/rollouts/codex-gpt5.6sol_v320.answer.json"),
    ("gemini-3.1-pro (video)", "calibration/rollouts/gemini-3.1-pro_v320.answer_norm.json"),
    ("opus-5 (video)", "calibration/rollouts/opus-5_v320.answer.json"),
    ("ABL single_frame (1 frame)", "calibration/rollouts/abl_single_frame.answer.json"),
    ("ABL no_media (no footage)", "calibration/rollouts/abl_no_media.answer.json"),
    ("ABL recall (prior knowledge)", "calibration/rollouts/abl_recall.answer.json"),
    ("ABL2 single_frame leak-free", "calibration/rollouts/abl2_single_frame.answer.json"),
    ("ABL2 no_media leak-free", "calibration/rollouts/abl2_no_media.answer.json"),
    ("ABL2 recall leak-free", "calibration/rollouts/abl2_recall.answer.json"),
]
TOLS = (3, 5, 10, 20, 30, 60)
CUTS = (0, 180, 300)


def norm(name):
    return name.lower().replace(" ", "")


def load_answer(path):
    a = json.load(io.open(path, encoding="utf-8-sig"))
    out = []
    for pl in a.get("players", []):
        r = pl["race"].lower()
        for b in pl.get("buildings", []):
            out.append((r, norm(b["name"]), float(b["t_seconds"])))
    return out


def load_gt(path):
    ev = json.load(io.open(path, encoding="utf-8-sig"))["events"]
    return [(e["race"].lower(), norm(e["name"]), float(e["t"])) for e in ev]


def f1(pred, gt, tol):
    """Greedy 1:1 closest-time match on (race, name); same rule as judge.py."""
    used, m = set(), 0
    for p in sorted(pred, key=lambda x: x[2]):
        best, bd = None, tol + 1e-9
        for i, g in enumerate(gt):
            if i in used or g[0] != p[0] or g[1] != p[1]:
                continue
            d = abs(g[2] - p[2])
            if d < bd:
                best, bd = i, d
        if best is not None:
            used.add(best)
            m += 1
    if not pred or not gt:
        return 0.0, m
    pr, rc = m / len(pred), m / len(gt)
    return (0.0 if pr + rc == 0 else 2 * pr * rc / (pr + rc)), m


def optimal_matches(pred, gt, tol):
    """Exact maximum 1:1 matching (not greedy), per (race, name) group.

    Both sides are points on a time line and each pred may match any gt within tol, so
    earliest-deadline-first over time-sorted preds is provably optimal. Used only to prove
    the greedy matcher in judge.py is not costing anyone a match.
    """
    groups = {}
    for g in gt:
        groups.setdefault(g[:2], []).append(g[2])
    for v in groups.values():
        v.sort()
    used, m = set(), 0
    for p in sorted(pred, key=lambda x: x[2]):
        for i, t in enumerate(groups.get(p[:2], [])):
            if (p[:2], i) in used:
                continue
            if t < p[2] - tol:
                continue
            if t > p[2] + tol:
                break
            used.add((p[:2], i))
            m += 1
            break
    return m


def audit():
    gt = load_gt(GT)
    keys = set(g[:2] for g in gt)
    print("| run | predicted | keys valid | greedy +/-3s | optimal +/-3s | median dt | best shift | F1 at shift |")
    print("|---" * 8 + "|")
    for name, path in [(n, p) for n, p in RUNS if os.path.exists(p)]:
        pred = load_answer(path)
        _, greedy = f1(pred, gt, 3)
        opt = optimal_matches(pred, gt, 3)
        valid = sum(1 for p in pred if p[:2] in keys)
        deltas = []
        for p in pred:
            near = [g[2] - p[2] for g in gt if g[:2] == p[:2]]
            if near:
                deltas.append(min(near, key=abs))
        deltas.sort()
        med = deltas[len(deltas) // 2] if deltas else float("nan")
        best = max(
            ((f1([(r, n, t + sh) for r, n, t in pred], gt, 3)[0], sh) for sh in range(-30, 31)),
            key=lambda x: (x[0], -abs(x[1])),
        )
        print("| %s | %d | %d/%d | %d | %d | %+.0f s | %+d s | %.3f |"
              % (name, len(pred), valid, len(pred), greedy, opt, med, best[1], best[0]))


# The four GT events that the ORIGINAL prompt's output example handed to every agent for free
# (fixed 2026-08-26: steps/solve/instruction.md now uses invented placeholder values). Kept here
# so the archived rollouts, which all saw the leaky prompt, can be re-scored without them.
LEAKED = {
    ("terran", "supplydepot", 20.0),
    ("terran", "barracks", 45.0),
    ("zerg", "spawningpool", 44.0),
    ("zerg", "extractor", 55.0),
}


# this run was given the FIXED prompt, so its predictions were never seeded by the example
NEVER_LEAKED = ("opus-4.8 leak-free prompt (video)",
                "ABL2 single_frame leak-free",
                "ABL2 no_media leak-free",
                "ABL2 recall leak-free")


def leakfree():
    """Re-score every run with the four prompt-leaked GT events removed from both sides."""
    gt = load_gt(GT)
    gt2 = [g for g in gt if g not in LEAKED]
    print("| run | +/-3s F1 (94 GT) | matched | of which leaked | **+/-3s F1 (90 GT, leak-free)** | matched |")
    print("|---" * 6 + "|")
    for name, path in [(n, p) for n, p in RUNS if os.path.exists(p)]:
        pred = load_answer(path)
        s0, m0 = f1(pred, gt, 3)
        lk = sum(1 for l in LEAKED
                 if any(p[:2] == l[:2] and abs(p[2] - l[2]) <= 3 for p in pred))
        pred2 = [p for p in pred
                 if not any(p[:2] == l[:2] and abs(p[2] - l[2]) <= 3 for l in LEAKED)]
        s1, m1 = f1(pred2, gt2, 3)
        tag = " (prompt already fixed)" if name in NEVER_LEAKED else ""
        print("| %s%s | %.3f | %d | %d | **%.3f** | %d |" % (name, tag, s0, m0, lk, s1, m1))


def main():
    gt = load_gt(GT)
    runs = [(n, p) for n, p in RUNS if os.path.exists(p)]

    print("## tolerance sweep (whole game, %d GT events)\n" % len(gt))
    print("| run | " + " | ".join("+/-%ds" % t for t in TOLS) + " | events |")
    print("|---" * (len(TOLS) + 2) + "|")
    for name, path in runs:
        pred = load_answer(path)
        cells = []
        for t in TOLS:
            s, m = f1(pred, gt, t)
            cells.append("%.3f (%d)" % (s, m))
        print("| %s | %s | %d |" % (name, " | ".join(cells), len(pred)))

    print("\n## reward restricted to the late game (+/-3 s)\n")
    print("| run | " + " | ".join("GT t>=%ds" % c for c in CUTS) + " |")
    print("|---" * (len(CUTS) + 1) + "|")
    for name, path in runs:
        pred = load_answer(path)
        cells = []
        for c in CUTS:
            g = [e for e in gt if e[2] >= c]
            p = [e for e in pred if e[2] >= c]
            s, m = f1(p, g, 3)
            cells.append("%.3f (%d/%d)" % (s, m, len(g)))
        print("| %s | %s |" % (name, " | ".join(cells)))


if __name__ == "__main__":
    import sys

    if "--audit" in sys.argv:
        audit()
    elif "--leakfree" in sys.argv:
        leakfree()
    else:
        main()
