# Calibration — sc2-build-order-reconstruction

Task: from a **whole-map bird's-eye video** of one full 1v1 StarCraft II match (Terran vs Zerg, ~15 min), tiled 3×3 (9 tiles cropped from a single full-map god-view rendered at camera distance 320 that captures the **entire battlefield with margin — no clipping**; **RAW frames, no color/brightness processing**; **~5 fps** game-time sampling ≈ every 0.18 s), reconstruct **both players' build orders** — every structure with its construction-start game-time.

Family: `agentic_vbench_understanding`. Scorer (`steps/solve/tests/judge.py`): deterministic, pure stdlib. Both players' events pooled into ONE chronological timeline; greedy 1:1 match by (race, structure name) within **±3 s**; `reward = F1`. Oracle GT → 1.0, empty → 0.0.

Ground truth (`steps/solve/tests/gt.json`, 100 events: Terran 67, Zerg 33) machine-parsed from the SAME `gt/match.SC2Replay` (AutomatonLE, base build 75689) via the SC2 engine's tracker events (`UnitInitEvent` = construction start) — no manual annotation. Ordinary ladder game → no lookup shortcut.

## Results — three frontier agents (required format)

Each run was isolated in a directory outside the repo tree (`C:/sc2_v320_{codex,opus,ag}`) with only the 9 tiles + `frames_time.json` + `PROMPT.md` + ffmpeg — no GT, no scorer on disk; trajectories audited for GT access — all clean.

| harness | harness version | model | reasoning | score | tool-call turns | trajectory |
|---|---|---|---|---|---|---|
| Claude Code | 2.1.215 | opus-4.8 | high | 0.080 | 112 (102 frame reads + 10 scripts) | `rollouts/opus-4.8_v320.answer.json` |
| Codex CLI | 0.130.0 | gpt-5.6-sol | none | 0.064 | 297 (atomic; 17 exec / 24 turns — see note) | `rollouts/codex-gpt5.6sol_v320.txt` |
| Antigravity CLI | 1.1.5 | Gemini 3.1 Pro | high | 0.031 | 71 (backend turns; CLI does not expose per-tool counts) | `rollouts/gemini-3.1-pro_v320_antigravity.txt` |

Baselines (task is solvable but not guessable):

| baseline | reward |
|---|---|
| oracle (GT submitted as the answer, `steps/solve/solution/solve.sh`) | 1.0 |
| empty answer | 0.0 |

Best real-agent score = 0.080. All three strong code agents score **< 0.10 at the ±3 s build-order standard** (opus 0.080, codex 0.064, gemini 0.031). Not a sampling artifact — the video is sampled ~every 0.18 s so ±3 s is physically achievable (each agent landed a few ±3 s hits). Difficulty is genuine: reconstructing ~100 building instances with ±3 s timing from a tiled bird's-eye is hard — recall is limited (best 56/100), timing is imprecise, and fine-grained sprite typing is the load-bearing step.

## Reasoning workload & tool use

Per-run compute. The Codex CLI was run with `reasoning effort: none` (see log header), unlike the lol_minimap calibration where it ran at `high`; opus and Gemini ran at their default high reasoning.

| Model @ framework | tool calls | notes |
|---|---|---|
| opus-4.8 @ Claude Code | 112 | 102 frame extractions + 10 helper scripts; 50 events (32 Terran / 18 Zerg) |
| gpt-5.6-sol @ Codex | 297 atomic (17 exec / 24 assistant turns) | each exec is a PowerShell loop batching many ffmpeg calls — see note below; 56 events (36 Terran / 20 Zerg), highest recall |
| Gemini 3.1 Pro @ Antigravity | 71 backend turns (~53 frame/montage images + scripts) | reconstructed only the first ~6 min (all 31 events ≤ 05:46) → low whole-game recall; 19 Terran / 12 Zerg |

## Relaxed accuracy (diagnostic only — not the task score)

`score_sc2_unified.py` re-scores each answer under monotonically-looser time tolerances. Metric is F1 (the shipped metric) at each tolerance, with matched count in parens.

| Model @ framework | ±3 s (strict) | ±5 s | ±10 s | ±30 s | events (T/Z) |
|---|---|---|---|---|---|
| opus-4.8 @ Claude Code | 0.080 | 0.080 | 0.133 | 0.240 | 50 (32/18) |
| gpt-5.6-sol @ Codex | 0.064 | 0.090 | 0.154 | 0.269 | 56 (36/20) |
| Gemini 3.1 Pro @ Antigravity | 0.031 | 0.076 | 0.092 | 0.153 | 31 (19/12) |

Difficulty is layered and real: even at ±30 s all three stay ≤ 0.27, so timing is not the only wall — identity (fine-grained sprite typing) and recall (best 56/100; gemini only reached ~6 min) collapse the score. Loosening to ±10 s helps codex most (0.064 → 0.154), i.e. many of its events are right-type/right-race but mistimed by 3–10 s. (`events (T/Z)` = predicted event counts.)

## Cheat audit (why runs are isolated)

Each agent ran in its own dir OUTSIDE the repo (`C:/sc2_v320_{codex,opus,ag}`) containing only the 9 tile videos + `frames_time.json` + `PROMPT.md` + ffmpeg — **no GT, no scorer on disk**. This mirrors the AgenticVBench environment (Docker ships only tiles + prompt; GT/scorer applied by the harness outside). Answers scored afterward against the pooled GT. An early non-isolated run that read `gt/` up the tree was discarded.

## Note on the Codex run (atomic tool-call count)

The Codex row's `tool-call turns = 297` is the **lowest atomic-level tool-call count**: each of the 17 `exec` shell commands is a PowerShell loop that invokes ffmpeg/ffprobe many times (frame × tile batches), so the harness-level `exec` count (17) and the assistant-turn count (24) badly understate the actual tool use. The 297 atomic invocations (288 ffmpeg + 9 ffprobe) were counted from `rollouts/codex-gpt5.6sol_v320.txt` by summing each exec's loop bounds:

| exec line | command structure | ffmpeg/ffprobe calls |
|---|---|---|
| 77 | ffprobe × 9 tiles | 9 |
| 5149 | 2 tiles × sheet | 2 |
| 5157 | 2 tiles × sheet | 2 |
| 5213 | 13 frames × 2 tiles | 26 |
| 5275 | 10 frames × xstack (9 inputs) | 10 |
| 5393 | 4 tiles × (sheet + final) | 8 |
| 5474 | 4 specs × 4 starts | 16 |
| 5606 | 4 specs × 4 starts | 16 |
| 5690 | 4 tiles × 15 frames | 60 |
| 5908 | 21 frames × (T + Z) | 42 |
| 6008 | 2 tiles × 16 frames | 32 |
| 6127 | 2 pairs × 4 starts | 8 |
| 6647 | 2 pairs × 6 starts | 12 |
| 7072 | 27 frames × (T + Z) | 54 |
| **total** | | **297** |

By the harness `exec`-turn metric Codex is 17 (below the >50-turn bar), but by atomic media-tool invocations it is 297 (well above). The other two agents clear the bar on their harness's native metric (opus 112, Gemini 71). A re-run with one-action-per-call would lift Codex's `exec` count past 50 trivially, but is not needed to demonstrate genuine tool use.

## Reproduce

```bash
# strict score (single-tolerance F1, oracle=1.0/empty=0):
python3 steps/solve/tests/judge.py \
  --solution <answer.json> \
  --reward-json reward.json --reward-txt reward.txt

# offline diagnostic (also prints ±5/10/30 s relaxation):
python calibration/score_sc2_unified.py --answer calibration/rollouts/opus-4.8_v320.answer.json \
    --gt-terran gt/gt_terran.json --gt-zerg gt/gt_zerg.json
```

Render recipe and full findings are kept as dev docs outside this PR; lookalike-structure proof images: `calibration/proof/`. Rollouts (answers + logs): `rollouts/`. Prompt given to every run: `steps/solve/instruction.md`.
