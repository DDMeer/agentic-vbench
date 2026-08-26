# SPEC — sc2-build-order-reconstruction

## Input
Nine videos (`tiles/tile_r{0..2}c{0..2}.mp4`) = a 3×3 tiling of ONE full-map bird's-eye god-view
of a 1v1 StarCraft II match (Terran vs Zerg, ~15 min), plus `tiles/frames_time.json` (frame index
→ game-seconds). Full observer vision (no fog); RAW frames (no image processing); whole battlefield
in frame (no clipping); ~5 fps game-time sampling (~0.18 s, 5000 frames/tile). No HUD, panels,
counters, minimap, or names — only the rendered world.

## Output (`answer.json`)
Per player, a chronological list of production events `(game_time_s, structure)`:
```json
{"players":[
  {"race":"terran","buildings":[{"t_seconds":137,"name":"Factory"}]},
  {"race":"zerg","buildings":[{"t_seconds":262,"name":"RoachWarren"}]}
]}
```

## Event definition (what counts, precisely)
These are exactly the rules `calibration/gen_sc2_gt.py` implements, and exactly what
`steps/solve/instruction.md` tells the agent.
- **Time = construction START** — the game-loop the structure is first placed (`UnitInitEvent`),
  converted with `t = round(game_loop / 22.4)` (SC2 "Faster" speed), not completion time.
- **Structures only**, from a per-race whitelist. Units, larvae/eggs/cocoons, creep tumors,
  mineral fields, vespene geysers and destructible rocks are excluded, and so are the two
  summonables the engine reports as structures but a build order does not contain
  (Raven **AutoTurret**, Reaper **KD8Charge**).
- **Structure tech morphs are separate events**, timed at the morph (`UnitTypeChangeEvent`):
  CommandCenter→OrbitalCommand/PlanetaryFortress, Hatchery→Lair→Hive, Spire→GreaterSpire.
  Non-structure type changes are excluded (SupplyDepot lower/raise, siege mode, burrow,
  cocoons, Overseer/Queen morphs, …) — in this replay that removes 17 SupplyDepotLowered and
  92 siege-mode changes that a naive parser would emit as build events.
- **Add-ons** (Barracks/Factory/Starport TechLab and Reactor) are separate events.
- **Rebuilds after destruction count as separate events** — full instance count required, no
  de-duplication to a type set.
- **Cancelled buildings** are NOT counted: a placement counts only if it also has a
  `UnitDoneEvent`. In this replay that excludes 1 Extractor and 2 SpineCrawlers.
- The two starting structures (Terran CommandCenter, Zerg Hatchery) are events at t=0.

## Scoring (deterministic, pure code — `steps/solve/tests/judge.py`)
Both players' events are pooled into ONE chronological timeline. A predicted event matches a GT
event iff it agrees on **(race, structure_name)** (case/space-insensitive) AND game-time within
**±3 s**; greedy 1:1 (closest time). **reward = F1** over matched events. A wrong name, wrong race,
or mis-timed event does not match → guessing scores ≈ 0.

Tolerance is tight because build order is order/timing-sensitive; the ~5 fps sampling makes ±3 s
physically achievable. Relaxation (±5/10/30 s, per-race, name-only) is for OFFLINE diagnosis only
(`calibration/score_sc2_unified.py`), not the reward.

## Ground truth
Machine-parsed from the SAME `.SC2Replay` the video was rendered from (SC2 engine tracker events →
construction-start times); no manual annotation. Regenerate with:

```bash
python calibration/gen_sc2_gt.py --replay gt/match.SC2Replay
```

`gt/gt_terran.json` (61) + `gt/gt_zerg.json` (33) = **94 events**, pooled into
`steps/solve/tests/gt.json` for the verifier. GT names use the engine's unit-type names, and every
name that occurs is listed in the agent's instruction, so recall is not capped by vocabulary.

**Alignment with the video** is measured, not assumed: `calibration/verify_events.py` measures,
for six landmark structures spread over the game and across both players, the second at which the
structure appears in the render, and compares it with the GT second. The onset is measured from the
pixels alone as a step in *normalised edge energy* (`mean(|dI/dx|+|dI/dy|)/(mean(I)+8)`) in a 60×60
px box — shadow-invariant, because this map has large moving cloud shadows that a brightness test
cannot tell apart from a new building. The onset is timed to the **formal construction start**
(the replay's `UnitInitEvent`), not the placement animation: a building appears in two stages —
a 1–2 s edge-energy spike when the foundation is placed (which leads the tracker event), then a
dip, then a sustained ramp as it grows — so the detector skips the placement spike and fires at
the dip just before the ramp (the Extractor, which covers a geyser and smooths the ground, is the
two-sided case and fires at the first second the edge energy stays below the baseline). Result:
**all six within ±1 s of the GT** (deltas −1 / 0 / 0 / −1 / 0 / +1 s; median 0 s), well inside the
±3 s match window, with the same spread at t=20 s and at t=800 s, i.e. no clock drift. The
report `calibration/proof/alignment.md` ships the before/at/after screenshot strips and the
per-landmark series; it also records what does *not* work (whole-region shift scans are dominated
by army movement and creep spread) and what is not claimed (only in-base landmarks; morphs
excluded).

## Validation
- Oracle (`steps/solve/solution/solve.sh`, reproduces GT) → reward **1.0**.
- Empty / absent answer → **0.0**.
- Calibration (strong code agents, isolated, no GT/scorer in the workdir): all four runs are
  **< 0.10** at ±3 s (opus-4.8 re-run 0.097, opus-4.8 0.083, codex gpt-5.6-sol 0.080,
  gemini-3.1-pro 0.080). Recall is the wall: best 56/94 events. See `calibration/scores.md`.

## Anti-shortcut — MEASURED
`on_screen_text` is impossible by construction (no HUD, panel, counter, clock, minimap or name is
rendered — verified by inspecting frames). The other three shortcuts were run as ablations against
this GT and this verifier (codex `gpt-5.6-sol`, three isolated dirs, media only; `calibration/rollouts/abl2_*`):

| run | footage | reward (±3 s F1) | `t>=300 s` only |
|---|---|---|---|
| best full-video agent (opus-4.8 re-run) | 9 tiles, 15 min | **0.097** | 0.031 |
| opus-4.8 / codex / gemini (video) | 9 tiles, 15 min | 0.080–0.083 | 0.000–0.058 |
| `single_frame` | ONE frame at t=450 s | 0.076 | 0.000 |
| `no_media` | none | 0.047 | 0.000 |
| `recall` | none, prior knowledge only | 0.022 | 0.017 |

The uncontaminated floor is **0.022–0.076**. Every video run is above it, though three of the four
clear it only narrowly — the opening of a TvZ game is stereotyped and the GT holds 17 Terran
SupplyDepots, so a periodic depot guess scores a few by construction. The separation is decisive
late, where priors cannot reach: restricted to GT events at `t>=300 s`, all three ablations collapse
to ≤ 0.017 while the video runs land 1–2 late events — a prior can open a game; it cannot time an
expansion Hatchery at 348 s.

**State the claim honestly: it is not `≈ 0`, and it is model-dependent.** An agent that does not
mine the footage is nearly indistinguishable from one guessing a standard TvZ opening. If a stronger
prior-proofing is wanted, requiring each event's map coordinates (or scoring only rebuilds,
destructions and expansion locations) would remove the guessable component entirely. Regenerate
with `python calibration/ablation_table.py`.
