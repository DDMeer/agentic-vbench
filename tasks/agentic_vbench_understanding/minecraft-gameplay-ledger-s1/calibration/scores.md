# Calibration — minecraft-gameplay-ledger-s1

## Shipped: v38 (game_v38.mp4), timestamp-windowed metric

`game_v38.mp4`, sha256 `110f1232…356d715d`, 238.5 min, **1995 events** (355 mine / 1501 place /
139 kill), 41 distinct block/mob types, 8 biomes ×9 laps, 27 structures (cabin with a full gable
roof whose timber rotates per lap, well, watchtower) + a staircase mine, 1280×720 @ 25 fps, no audio.

**Scorer:** `reward = 0.85 · F2(action,target) + 0.15 · weapon-F1 over aligned kills`. Alignment is
an **order-preserving LCS on `(action,target)` within a ±10 s time window** — a predicted event
aligns only if its `t` is within 10 s of the true video time. Recall-weighted (β=2). This is the
maintainer-requested "order-preserving LCS **plus a time tolerance**": the window makes the order
real, so a right-multiset / wrong-timing ledger cannot score.

| submission | reward | ledger F2 | notes |
|---|---|---|---|
| oracle | **1.0000** | 1.0000 | harness path (`solve.sh` → `judge.py`); verified |
| correct multiset, order shuffled | 0.0431 | 0.0456 | LCS order + time window defeat it |
| correct multiset, random times | 0.0079 | 0.0080 | time window defeats it |
| most-common token ×N (times spread) | 0.0469 | 0.0551 | genuine shortcut, well under 0.15 |
| actions+times right, targets "stone" | 0.0192 | 0.0226 | genuine shortcut, well under 0.15 |
| **Codex `gpt-5.6-sol` (xhigh)** | **0.0196** | 0.0043 | timestamp task: reported 103/1995 events, 22 aligned within ±10 s (2 runs: 0.0196 / 0.0105, run-dependent); rollout `codex_v38ts_*` |

**Why the timestamp window.** Under the earlier order-only LCS, a shuffled full multiset scored
0.216 — an artifact of repeated-token leniency (41 distinct types over 1995 events; identical tokens
match in any order). The ±10 s window pins each event to its place in the video, collapsing that to
0.043 while the oracle stays 1.0. The map from event time to video time was spot-checked at both ends
of the 238-min video (events appear within the window of their predicted times).

**Generation fairness (v38 session):** 33 placements skipped as unframable (not placed, not recorded),
86 kills rejected off-camera (139 recorded), all 27 structures verified visible (`ORBIT_SHOWN`),
0 air-mines. Every recorded action is on-camera and framed dead-centre.

## Difficulty is recall-limited (event count is the lever)

The strong agent reconstructs a roughly fixed absolute number of events (~200) and covers a smaller
fraction as the ledger grows, so reward falls with event count. Measured on renders of THIS generator
under the shipped scorer family (order-only unless noted); the timestamp window is strictly no easier:

| render | events | length | strong-agent reward | recall |
|---|---|---|---|---|
| v34 | 1005 | 95 min | 0.177 | 0.16 |
| v36 | 1135 | 120 min | 0.174 | 0.13 |
| v37 | 1431 | 150 min | 0.120 | 0.07 |
| v38 (order-only) | 1995 | 238 min | 0.070 | 0.05 |
| **v38 (timestamp, shipped)** | 1995 | 238 min | **0.020** | 0.003 |

n=1 per render; run-dependent. Rollouts in `calibration/rollouts/`.
