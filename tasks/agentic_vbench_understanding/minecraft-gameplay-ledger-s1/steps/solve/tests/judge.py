#!/usr/bin/env python3
"""Grade a Minecraft first-person gameplay-ledger reconstruction. Pure stdlib, deterministic.

The video is a ~10-minute FIRST-PERSON recording of a player exploring a generated
Minecraft world: walking, looking around, mining blocks (the camera turns to each block
as it breaks), and fighting a mob. The agent reconstructs the ORDERED ledger of the
player's deliberate actions: the chronological sequence of (action, target), where
action is `mine` (a block is broken; target = block type) or `kill` (a mob is defeated;
target = mob type).

Scoring is order-aware (LCS) so the moving first-person camera and the render frame-rate
are irrelevant: F1 = 2*LCS / (len_pred + len_gt) over the (action, target) token
sequence. Misses, invented actions, wrong block/mob types, and reorderings all lower it.
reward = LCS-F1.

Why order (not timestamps): a first-person session has a moving camera and the software
render is variable-FPS, so the reliable machine-exact ground truth is the ORDER of the
player's actions (mineflayer events). The task stays hard and shortcut free: ~90 actions
over ~10 minutes in first person, block/mob identity read from the rendered textures, no
HUD — a single frame or a still cannot recover the ordered action sequence.

A second, weighted component scores COMBAT STYLE: for the kill events only, the ordered
sequence of the weapon used (`sword` for a melee kill — the player is adjacent and swings
— vs `bow` for a ranged kill, where arrows fly and the mob dies at a distance). This is
read from the video the same way a human would: engagement distance, flying arrows, and
the highlighted hotbar slot.

    reward = 0.85 * LCS-F1(action, target)  +  0.15 * LCS-F1(kill weapons)

Ground truth (ordered tokens) is baked verifier-side at /tests/ground_truth.json.
"""
import argparse, json, re
from pathlib import Path
GT_PATH = Path(__file__).with_name("ground_truth.json")

def norm(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())

def act_norm(a):
    a = norm(a)
    if a in ("mine","mined","break","broke","dig","dug"): return "mine"
    if a in ("kill","killed","mobkill","defeat","defeated","slay","slew"): return "kill"
    return a

def token(ev): return (act_norm(ev.get("action") or ev.get("event")), norm(ev.get("target") or ev.get("block")))

def weapon_norm(w):
    w = norm(w)
    if "bow" in w or "arrow" in w or "ranged" in w: return "bow"
    if "sword" in w or "melee" in w or "blade" in w: return "sword"
    return w

def weapon_seq(evs):
    """Ordered weapon tokens for the kill events (combat-style component)."""
    out = []
    for e in evs:
        if not isinstance(e, dict): continue
        if act_norm(e.get("action") or e.get("event")) != "kill": continue
        out.append(weapon_norm(e.get("tool") or e.get("weapon") or ""))
    return out

def lcs_len(a, b):
    n, m = len(a), len(b)
    if n == 0 or m == 0: return 0
    prev = [0]*(m+1)
    for i in range(1, n+1):
        cur = [0]*(m+1); ai = a[i-1]
        for j in range(1, m+1):
            cur[j] = prev[j-1]+1 if ai == b[j-1] else (prev[j] if prev[j] >= cur[j-1] else cur[j-1])
        prev = cur
    return prev[m]

def lcs_pairs(a, b):
    """Matched (i, j) index pairs of one longest common subsequence of a and b."""
    n, m = len(a), len(b)
    if n == 0 or m == 0: return []
    tbl = [[0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1):
        ai = a[i-1]
        row, prev = tbl[i], tbl[i-1]
        for j in range(1, m+1):
            row[j] = prev[j-1]+1 if ai == b[j-1] else (prev[j] if prev[j] >= row[j-1] else row[j-1])
    out, i, j = [], n, m
    while i > 0 and j > 0:
        if a[i-1] == b[j-1] and tbl[i][j] == tbl[i-1][j-1]+1:
            out.append((i-1, j-1)); i -= 1; j -= 1
        elif tbl[i-1][j] >= tbl[i][j-1]:
            i -= 1
        else:
            j -= 1
    return out[::-1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solution", required=True, type=Path)
    ap.add_argument("--reward-json", required=True, type=Path)
    ap.add_argument("--reward-txt", required=True, type=Path)
    a = ap.parse_args()
    gt_raw = json.loads(GT_PATH.read_text())["events"]
    gt = [token(e) for e in gt_raw]; gt_w = weapon_seq(gt_raw)
    reason = "ok"; preds = []; pred_raw = []; pred_w = []
    try:
        raw = json.loads(a.solution.read_text()).get("events", [])
        if not isinstance(raw, list): raise ValueError("events not a list")
        pred_raw = [e for e in raw if isinstance(e, dict)]
        preds = [token(e) for e in pred_raw]
        pred_w = weapon_seq(raw)
    except Exception as exc:  # noqa: BLE001
        reason = f"unreadable solution.json: {exc}"
    # Ledger score is an ORDER-AWARE, RECALL-WEIGHTED F-beta over the (action, target) sequence.
    # beta=2 weights recall 2x precision: the task is to reconstruct the WHOLE ledger, and a
    # confident partial answer (high precision, low recall) is most of the task left undone. Under
    # plain F1 an agent that correctly named 11% of events in order scored 0.20; F2 scores that 0.14,
    # matching the intuition that finding one event in nine is not "20% solved". Oracle (perfect
    # recall and precision) is still exactly 1.0, and an empty or all-wrong answer is still 0.
    BETA = 2.0
    lcs = lcs_len(preds, gt); np_, ng = len(preds), len(gt)
    prec = (lcs / np_) if np_ else 0.0
    rec = (lcs / ng) if ng else 0.0
    b2 = BETA * BETA
    f1 = ((1 + b2) * prec * rec / (b2 * prec + rec)) if (b2 * prec + rec) > 0 else 0.0

    # Weapon credit is earned only on kills the submission actually IDENTIFIED — i.e. kill events
    # that fall inside the ledger's LCS alignment. Scoring the weapon sequence independently made it
    # nearly free: there are only two weapon classes, so an LCS-F1 over that sequence stays high even
    # when the ledger is wrong. Measured on v30, a submission that named every block "stone" scored
    # ledger 0.028 yet collected weapon 1.000, lifting a useless answer to reward 0.174; shuffling
    # the ledger still collected weapon 0.722. Neither can now claim credit it did not earn.
    pairs = lcs_pairs(preds, gt)
    nw_p, nw_g = len(pred_w), len(gt_w)
    aligned = [(i, j) for (i, j) in pairs if gt[j][0] == "kill"]
    wl = sum(1 for i, j in aligned
             if weapon_norm(pred_raw[i].get("tool") or pred_raw[i].get("weapon") or "")
             == weapon_norm(gt_raw[j].get("tool") or gt_raw[j].get("weapon") or ""))
    f1w = (2*wl/(nw_p+nw_g)) if (nw_p+nw_g) else 0.0
    reward = 0.85*f1 + 0.15*f1w
    det = {"reason": reason, "n_ground_truth": ng, "n_predicted": np_, "lcs": lcs,
           "ledger_precision": round(prec,4), "ledger_recall": round(rec,4), "beta": BETA,
           "ledger_fbeta": round(f1,4), "n_gt_kills": nw_g, "n_pred_kills": nw_p,
           "aligned_kills": len(aligned), "weapon_correct": wl, "weapon_f1": round(f1w,4),
           "note": "reward = 0.85*LCS-Fbeta(action,target; beta=2, recall-weighted) "
                   "+ 0.15*weapon-F1 over LCS-aligned kills"}
    a.reward_json.parent.mkdir(parents=True, exist_ok=True)
    a.reward_json.write_text(json.dumps({"reward": round(reward,4), "details": det}, indent=2))
    a.reward_txt.write_text(f"{round(reward,4)}\n")

if __name__ == "__main__": main()
