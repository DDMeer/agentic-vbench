# Calibration — sc2-build-order-reconstruction

Task: from a **whole-map bird's-eye video** of one full 1v1 StarCraft II match (Terran vs Zerg, ~15 min), tiled 3×3 (9 tiles cropped from a single full-map god-view rendered at camera distance 320 that captures the **entire battlefield with margin — no clipping**; **RAW frames, no color/brightness processing**; ~5.6 fps game-time sampling ≈ every 0.18 s), reconstruct **both players' build orders** — every structure with its construction-start game-time.

Family: `agentic_vbench_understanding`. Scorer (`steps/solve/tests/judge.py`): deterministic, pure stdlib. Both players' events pooled into ONE chronological timeline; greedy 1:1 match by (race, structure name) within **±3 s**; `reward = F1`. Oracle GT → 1.0, empty → 0.0.

Ground truth: regenerated from the replay by `calibration/gen_sc2_gt.py` (reproducible, in-repo) — `gt/gt_terran.json` (61) + `gt/gt_zerg.json` (33) = **94 events** (Terran 61, Zerg 33), pooled for the verifier as `steps/solve/tests/gt.json`. Source replay: `gt/match.SC2Replay` (AutomatonLE, base build 75689). Ordinary ladder game → no lookup shortcut. The regeneration fixes the four defects of the original 100-event GT (see "Ground truth regeneration").

## Results — three frontier agents (required format)

Each run was isolated in a directory outside the repo tree (`C:/sc2_v320_{codex,opus,ag}`) with only the 9 tiles + `frames_time.json` + `PROMPT.md` + ffmpeg — no GT, no scorer on disk; trajectories audited for GT access — all clean.

| harness | harness version | model | score | tool-call turns | trajectory |
|---|---|---|---|---|---|
| Claude Code | 2.1.215 | opus-4.8 | 0.083 | 112 (102 frame reads + 10 scripts) | `rollouts/opus-4.8_v320.answer.json` |
| Codex CLI | 0.130.0 | gpt-5.6-sol | 0.080 | 297 (atomic; 17 exec / 24 turns — see note) | `rollouts/codex-gpt5.6sol_v320.txt` |
| Antigravity CLI | 1.1.5 | Gemini 3.1 Pro | 0.080 | 71 (backend turns; CLI does not expose per-tool counts) | `rollouts/gemini-3.1-pro_v320_antigravity.txt` |

Scores are against the regenerated 94-event GT; the numbers in the original PR description were against the older 100-event GT and differ slightly (opus 0.080 → 0.083, codex 0.064 → 0.080, gemini 0.031 → 0.080).

### Raw transcript for the opus-4.8 (112-turn) run

The 112-turn opus-4.8 run above was completed before transcripts were being retained, so its raw step-level transcript was not saved. It was re-run on 2026-08-26 on the current prompt (43 min, 100 tool calls — 50 bash, 47 image reads; cheat audit clean) and that transcript is shipped as `rollouts/opus-4.8_v320_rerun.transcript.jsonl` (372 records, native Claude Code session format). The re-run scored **0.097** (5 matched, 9 reported events — it went precision-first, precision 0.556 the highest in the bundle; answer at `rollouts/opus-4.8_v320_rerun.answer.json`). Its one genuine mid-game find is the Zerg expansion `Hatchery` at 348 s, exact to the second.

Baselines (task is solvable but not guessable):

| baseline | reward |
|---|---|
| oracle (GT submitted as the answer, `steps/solve/solution/solve.sh`) | 1.0 |
| empty answer | 0.0 |

Best real-agent score = 0.097 (opus-4.8 re-run). All three strong code agents score **< 0.10 at the ±3 s build-order standard**. Not a sampling artifact — the video is sampled ~every 0.18 s so ±3 s is physically achievable (each agent landed a few ±3 s hits). Difficulty is genuine: reconstructing ~94 building instances with ±3 s timing from a tiled bird's-eye is hard — recall is limited (best 56/94), timing is imprecise, and fine-grained sprite typing is the load-bearing step.

## Reasoning workload & tool use

| Model @ framework | tool calls | notes |
|---|---|---|
| opus-4.8 @ Claude Code | 112 | 102 frame extractions + 10 helper scripts; 50 events (32 T / 18 Z) |
| opus-4.8 re-run @ Claude Code | 100 | 50 bash + 47 image reads; precision-first, 9 events (6 T / 3 Z); transcript retained |
| gpt-5.6-sol @ Codex | 297 atomic (17 exec / 24 turns) | each exec is a PowerShell loop batching many ffmpeg calls — see note; 56 events (36 T / 20 Z), highest recall |
| Gemini 3.1 Pro @ Antigravity | 71 backend turns (~53 frame/montage images + scripts) | reconstructed only the first ~6 min (all 31 events ≤ 05:46); 19 T / 12 Z |

## Relaxed accuracy (diagnostic only — not the task score)

`score_sc2_unified.py` re-scores each answer under monotonically-looser time tolerances. Metric is F1 (the shipped metric) at each tolerance, matched count in parens.

| Model @ framework | ±3 s (strict) | ±5 s | ±10 s | ±30 s | events (T/Z) |
|---|---|---|---|---|---|
| opus-4.8 @ Claude Code | 0.083 | 0.083 | 0.139 | 0.264 | 50 (32/18) |
| opus-4.8 re-run @ Claude Code | 0.097 | 0.097 | 0.097 | 0.117 | 9 (6/3) |
| gpt-5.6-sol @ Codex | 0.080 | 0.093 | 0.160 | 0.280 | 56 (36/20) |
| Gemini 3.1 Pro @ Antigravity | 0.080 | 0.096 | 0.112 | 0.176 | 31 (19/12) |

Difficulty is layered and real: even at ±30 s all four stay ≤ 0.28, so timing is not the only wall — identity (fine-grained sprite typing) and recall (best 56/94; gemini only reached ~6 min) collapse the score. Loosening to ±10 s helps codex most (0.080 → 0.160), i.e. many of its events are right-type/right-race but mistimed by 3–10 s.

## Anti-shortcut — MEASURED

Three ablations were run to measure the no-footage floor. Each ran `codex exec -m gpt-5.6-sol` in its own directory outside the repo (`C:/sc2_abl2_{single_frame,no_media,recall}`), media only — no GT, no scorer, no repo access; logs cheat-audited (no network, no replay/GT/judge access). Each `prompt.md` is the exact prompt that ablation was given.

| ablation | footage provided | ±3 s F1 | matched / 94 | predicted |
|---|---|---|---|---|
| `single_frame` | ONE frame (t=450 s, 9 still PNGs) | **0.076** | 5 | 37 |
| `no_media` | none (videos unavailable) | **0.047** | 3 | 33 |
| `recall` | none ("answer from prior knowledge") | **0.022** | 2 | 88 |

The uncontaminated floor is **0.022–0.076**. Every video run is above it (opus-4.8 re-run 0.097, opus-4.8 0.083, codex 0.080, gemini 0.080), though three of the four clear it only narrowly — the opening of a TvZ game is stereotyped and the GT holds 17 Terran SupplyDepots, so a periodic depot guess scores a few by construction. The separation is decisive late, where priors cannot reach:

| run | GT t>=0 s | GT t>=180 s | GT t>=300 s |
|---|---|---|---|
| opus-4.8 (video) | 0.083 (6/94) | 0.000 (0/76) | 0.000 (0/64) |
| opus-4.8 re-run (video) | 0.097 (5/94) | 0.026 (1/76) | 0.031 (1/64) |
| codex gpt-5.6-sol (video) | 0.080 (6/94) | 0.037 (2/76) | 0.049 (2/64) |
| gemini-3.1-pro (video) | 0.080 (5/94) | 0.065 (3/76) | 0.058 (2/64) |
| ABL2 `single_frame` | 0.076 (5/94) | 0.021 (1/76) | 0.000 (0/64) |
| ABL2 `no_media` | 0.047 (3/94) | 0.000 (0/76) | 0.000 (0/64) |
| ABL2 `recall` | 0.022 (2/94) | 0.014 (1/76) | 0.017 (1/64) |

Restricted to GT events at `t>=300 s`, all three ablations collapse to ≤ 0.017 while the video runs land 1–2 late events — a prior can open a game; it cannot time an expansion Hatchery at 348 s. So the anti-shortcut claim holds for an agent that mines the footage, and is honestly narrow for one that does not. `on_screen_text` was not run: impossible by construction (no HUD/panel/counter/clock/minimap/name is rendered — verified by inspecting frames). Reproduce with `python calibration/ablation_table.py`.

## Alignment (measured, with screenshots)

GT↔video time alignment is measured, not assumed: `calibration/verify_events.py` writes `proof/alignment.md` plus before/at/after PNG strips for six landmark structures spread over the game and across both players.

| landmark | GT t (s) | measured onset (s) | delta |
|---|---|---|---|
| terran SupplyDepot | 20 | 19 | −1 |
| zerg SpawningPool | 44 | 44 | 0 |
| terran Barracks | 45 | 45 | 0 |
| zerg Extractor | 55 | 54 | −1 |
| terran EngineeringBay | 332 | 332 | 0 |
| terran SupplyDepot | 800 | 801 | +1 |

All six land within ±1 s of the GT (median 0 s, mean −0.2 s), well inside the scorer's ±3 s window, with the same small spread early (t=20) and late (t=800) — so there is no clock drift across the 15 minutes. The onset is timed to the **formal construction start** (the replay's `UnitInitEvent`), not the placement animation: a building appears in two stages on this render — a 1–2 s edge-energy spike when the builder places the foundation (which leads the tracker event), then a dip, then a sustained ramp as it grows — so the detector skips the placement spike and fires at the dip just before the ramp. The Extractor is the two-sided case (it covers a geyser and smooths the ground rather than adding edges), so for it the onset is the first second the edge energy stays below the pre-event baseline.

Method: each landmark's montage pixel was read off base-region renders before/after the event; the **onset is then measured from the pixels alone** as a step in *normalised edge energy* `mean(|dI/dx|+|dI/dy|) / (mean(I)+8)` inside a 60×60 px box (two-sided, so an Extractor covering a geyser counts too). Plain brightness does not work (moving cloud shadows fire more often than buildings); an unsupervised whole-region shift scan also fails (army movement and creep spread dominate) — neither is shipped. Not claimed: only these six in-base landmarks are checked; morphs are excluded (gradual animation, no well-defined onset).

## Ground truth regeneration

The GT shipped in the original PR had four defects; all are fixed by `gen_sc2_gt.py`, which is now in the repo so the GT is reproducible rather than a checked-in artifact:

```bash
python calibration/gen_sc2_gt.py --replay gt/match.SC2Replay
```

| change | effect |
|---|---|
| dropped 6 `AutoTurret` (Raven summon) and 1 `KD8Charge` (Reaper ability) | −7 |
| dropped 2 cancelled `SpineCrawler` placements (no `UnitDoneEvent`) | −2 |
| added 3 structure morphs that were missing: `OrbitalCommand` t=119, `Lair` t=413, `Hive` t=875 | +3 |
| times now `t = round(game_loop / 22.4)` (documented, reproducible) | shifts old times by 0–2 s |
| **100 → 94 events** (Terran 61, Zerg 33) | |

Verifier integrity under the new GT: oracle (`steps/solve/solution/solve.sh`) → **1.0** (94/94), empty answer → **0.0**. Every GT structure name appears in `steps/solve/instruction.md`, so recall is not capped by vocabulary.

## Instruction changes (per review)

`steps/solve/instruction.md` was rewritten to state the GT rules explicitly:
- the old "buildings persist once built; time each by the frame it FIRST appears" line is gone — buildings can be destroyed and rebuilt (a rebuild is a new event), and a structure's sprite changes without a new building being made (SupplyDepot raise/lower, Orbital dish, Hatchery→Lair, siege mode) → judge from the ground footprint;
- construction **START** is stated explicitly (foundation/pit visible, not completion);
- **morphs** (CC→Orbital/Planetary, Hatchery→Lair→Hive, Spire→GreaterSpire) and **add-ons** are listed as separate events; **cancelled placements are NOT events**; AutoTurret/KD8Charge excluded by name;
- the **±3 s tolerance** is stated in the prompt ("|Δt| ≤ 3 seconds … guessing does not pay");
- the 15 fps → `frames_time.json` conversion rule is spelled out (never read the video clock directly);
- the structure-name lists are completed (SensorTower, GhostAcademy, FusionCore, InfestationPit, GreaterSpire, NydusNetwork, UltraliskCavern);
- base-location wording corrected: each main straddles a tile seam and both players expand, so the agent must locate the bases itself;
- the output JSON example was adjusted to use invented placeholder values instead of real events, with an explicit "format only, not events from this match" line.

## Cheat audit (why runs are isolated)

Each agent ran in its own dir OUTSIDE the repo (`C:/sc2_v320_*`, `C:/sc2_abl2_*`, `C:/sc2_opus48`) containing only the 9 tile videos + `frames_time.json` + `PROMPT.md` + ffmpeg — **no GT, no scorer on disk**. This mirrors the AgenticVBench environment (Docker ships only tiles + prompt; GT/scorer applied by the harness outside). Answers scored afterward against the pooled GT. An early non-isolated run that read `gt/` up the tree was discarded.

## Note on the Codex run (atomic tool-call count)

The Codex row's `tool-call turns = 297` is the **atomic** count: the 17 `exec` commands are PowerShell loops batching many ffmpeg/ffprobe calls (frame×tile batches), so the harness `exec` count (17) and assistant-turn count (24) understate the actual tool use. 297 = 288 ffmpeg + 9 ffprobe, summed from each exec's loop bounds (breakdown in `rollouts/codex-gpt5.6sol_v320.txt`). By the harness `exec`-turn metric Codex is 17 (below the >50 bar); by atomic media-tool invocations it is 297 (well above). The other two agents clear the bar on their harness's native metric (opus 112, Gemini 71). A re-run with one-action-per-call would lift Codex's `exec` count past 50 trivially, but is not needed to demonstrate genuine tool use.

## Reproduce (run from the `sc2/` dir)

```bash
# strict score (single-tolerance F1, oracle=1.0/empty=0):
python3 steps/solve/tests/judge.py \
  --solution calibration/rollouts/opus-4.8_v320.answer.json \
  --reward-json reward.json --reward-txt reward.txt

# all runs + ablations, tolerance sweep and late-game windows:
python calibration/ablation_table.py

# regenerate the ground truth from the replay:
python calibration/gen_sc2_gt.py --replay gt/match.SC2Replay

# measure GT <-> video alignment (writes proof/alignment.md + the PNG strips):
python calibration/verify_events.py --grid
```

Render recipe: `RECORDING.md`; full findings: `NOTES.md`. Rollouts (answers + logs + the ablation prompts): `rollouts/`. Prompt given to every run: `steps/solve/instruction.md`.
