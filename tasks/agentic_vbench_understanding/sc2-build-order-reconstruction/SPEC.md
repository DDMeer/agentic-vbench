---
title: Task Spec Card
summary: The structured header every video-understanding task must fill in and prove.
read_when: Reviewing this task. Every field is a verifiable claim.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/sc2-build-order-reconstruction

# 1. What kind of thinking does this task need?
#    understanding = compare/order/relate; reasoning = cause/cross-event inference.
#    Build-order reconstruction is perception + ordering/timing of ~100 structures,
#    not causal inference; the load-bearing step is fine-grained sprite reading.
cognitive_level: understanding

# 2. Which modalities are REQUIRED (not just present)?
modalities_required:
  video: "Every structure is observable only in the 3×3 bird's-eye tiles; identity comes from building sprites and add-on shapes (Reactor vs Tech Lab), race from tile location/creep. No HUD/panels/counters/minimap/names are shown."
  audio: "not used — the raw render has no audio (stripped by construction)"

# 3. The exact question and output schema.
question: "From a 3×3 bird's-eye tiling of one full ~15-min StarCraft II match (Terran vs Zerg), reconstruct both players' build orders — every structure with its construction-start game-time."
output_schema: "JSON {\"players\":[{race:terran|zerg, buildings:[{t_seconds:int, name:str}]}]}; name from a fixed vocabulary per race; full (race, name) match within 3 s, scored by F1. Rebuilds and tech morphs are separate events; cancelled buildings / creep tumors / minerals / geysers / rocks excluded."

# 4. Evidence chain: the specific moments the answer depends on (>=2 far-apart).
evidence:
  - "t=29s, video (tile r0c2, Terran main), first SupplyDepot — earliest Terran production, sets the opening"
  - "t=38s, video (tile r2c0, Zerg main), SpawningPool — earliest Zerg tech; read off purple-creep sprites"
  - "t=~110s, video, OrbitalCommand morph + Lair morph — tech morphs are separate timed events, not new buildings"
  - "t=~443s (07:23), video, Zerg Spire — late-game tech switch; only reachable by working the whole 15-min game across tiles"

# 5. Ground truth: value, source, tier, verification.
ground_truth:
  source: "SC2 engine tracker events (UnitInitEvent = construction start) machine-parsed from the SAME match.SC2Replay the video was rendered from; no manual annotation"
  tier: "machine-truth (engine-internal structured tracker records)"
  verification: "100 events (Terran 67, Zerg 33) pooled into steps/solve/tests/gt.json; event time = construction-start game-loop in game-seconds (not completion); replay base build 75689"

# 6. Scorer: deterministic code only.
scorer:
  metric: "F1 over events; a TP requires (race, structure_name) equal AND |Dt| <= 3 s; greedy 1:1 closest-time match. A wrong name, wrong race, or mis-timed event does not match."
  oracle_reward: 1.0
  null_reward: 0.0  # measured: empty submission -> 0.0

# 7. Difficulty: measured with a real strong-agent run.
difficulty:
  strong_agent_reward: 0.080  # opus-4.8 @ Claude Code, best of three
  tool_call_turns: 112  # opus-4.8 (102 frame reads + 10 scripts); codex ran 297 atomic ffmpeg/ffprobe calls (see scores.md)
  agent_model: "opus-4.8 (Claude Code 2.1.215) = 0.080 / 112 calls; gpt-5.6-sol (Codex CLI 0.130.0, reasoning=none) = 0.064 / 297 atomic calls; Gemini 3.1 Pro (Antigravity CLI 1.1.5) = 0.031 / 71 turns"

# 8. Anti-shortcut ablations: run a strong model under each degraded input.
#    Every one must score <= 0.15. TODO: run these measured ablations before the PR.
anti_shortcut:
  single_frame: "not on any frame — construction-start timing needs the frame a structure FIRST appears across the 15-min sequence, not a snapshot"
  video_only: "n/a — the raw render has no audio by construction; the full task is video-only"
  audio_only: "0.0 — no audio exists (stripped by construction)"
  no_media: "not recallable — ordinary ladder game with no public build-order record; ~100 specific instances with ±3 s timing are not guessable from the prompt alone"
  frame_dump_no_tools: "agency required — locating first-appearances needs seeking across 15 min × 9 tiles and brightening RAW frames, not pasted frames"
  on_screen_text: "~0 — no HUD, panels, counters, minimap, or names are rendered; only the game world"
  recall: "~0 — ordinary ladder game, not a broadcast/famous match"

# 9. Input media.
input:
  url: "https://huggingface.co/datasets/iTheresaApocalypse/agentvbench/resolve/main/sc2/tiles/ (9 files tile_r{0..2}c{0..2}.mp4)"
  sha256: "see tiles/SHA256SUMS.txt (9 per-file digests, verified at Docker build)"
  length_min: 15
  resolution: "3×3 tiling of one 3072² full-map god-view at camera distance 320 (whole battlefield, no clipping); RAW (no image processing); ~5 fps game-time (~0.18 s spacing, 5000 frames/tile)"
```

## Prompt-writing rules (the agent-facing instruction)

- One task per task: reconstruct both players' build orders (structure + game-time). No compound asks.
- Every scored term is defined: event time = construction start; tech morphs and rebuilds are separate events; cancelled buildings / creep tumors / minerals / geysers / rocks excluded.
- Closed vocabularies given in full per race (Terran 18 names, Zerg 12 names).
- Exact output schema and deliverable path (`/workspace/output/solution.json`) stated.
- The scoring method, tolerance, and ground-truth source are NOT described to the agent.
- No trick wording: everything scored is stated in `instruction.md`.
