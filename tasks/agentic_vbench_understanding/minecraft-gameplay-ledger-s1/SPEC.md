---
title: Task Spec Card
summary: minecraft-gameplay-ledger-s1 — reconstruct a player's action ledger, with the weapon used per kill, from a first-person Minecraft session.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/minecraft-gameplay-ledger-s1

cognitive_level: understanding
# Follow a moving first-person session across seven biomes and reconstruct the ordered
# sequence of deliberate actions — 211 actions over 10.9 minutes — including which weapon
# was used for each kill.

modalities_required:
  video: the action sequence exists only across frames of the first-person view.
  audio: not used.

question: Reconstruct the player's ordered action ledger (mine/place block-type, kill mob-type + weapon).
output_schema: '{"events": [{"action": "mine"|"place"|"kill", "target": <block/mob>, "tool": "sword"|"bow"}]}'

ground_truth:
  source: the mineflayer bot's own events (dig completion, entity death) plus its own
          /setblock placements; Paper 1.16.5 generated world.
  tier: machine-truth
  verification: oracle solution.json = the bot's action order; judge.py scores it 1.0.

scorer:
  metric: "0.85 * order-aware F2 (recall-weighted, beta=2) over ordered (action,target)
           + 0.15 * weapon score over LCS-aligned kills."
  oracle_reward: 1.0
  null_reward: 0.0
  measured_ablations:       # same GT, deliberately wrong submissions, under the shipped F2 scorer
    shuffled_ledger: 0.245  # right multiset, wrong order — order sensitivity, not a shortcut
    single_token_xN: 0.081  # most common (action,target) repeated
    targets_wrong: 0.026    # actions right, every target replaced by "stone"

difficulty:
  strong_agent_reward: 0.355   # Codex gpt-5.6-sol (xhigh) on the SHIPPED v32 video; rollout in
                               # calibration/rollouts/codex_v32_*
  tool_call_turns: 808
  agent_model: "codex gpt-5.6-sol, model_reasoning_effort=xhigh"
  note: "RECALL-LIMITED and run-dependent. On the shipped v32 (628 events) Codex scored 0.355
         (precision 0.60, recall 0.32, 808 tool calls, 337 events reported); an earlier run on the
         equivalent v31 (633 events) scored 0.164 (precision 0.79, recall 0.13, 241 tool calls).
         The score is bounded by how much of the 53-min video the agent chooses to watch, so it
         varies ~0.16-0.36 across runs — an honest MEDIUM either way, not <0.10. n=1 per render;
         see calibration/scores.md."

anti_shortcut:
  single_frame: 0.0             # Codex given one mid-video frame: correctly wrote an empty ledger
  most_common_token_xN: 0.081   # the single commonest (action, target), repeated
  actions_right_targets_stone: 0.026
  correct_multiset_shuffled: 0.245   # order sensitivity, not a shortcut — see Known limitations
  empty: 0.0
  frame_dump_no_tools: 0.0      # a 53-min video at 1 fps is >3000 frames, far past any context window

input:
  url: https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/main/minecraft-gameplay-ledger-s1/game_v31_long.mp4
  sha256: 24623fc3fd7e4fdf8a78a5322bfa0374b6dd6fff975eb178e74e270e9f3a097c
  length_min: 53.1
  resolution: 720
  contents: 633 events (166 mine, 422 place, 45 kill); 43 distinct block/mob types;
            biomes forest, beach, desert, snowy tundra, jungle, plains, savanna, badlands (x3 laps,
            re-rolled palettes); 3 structures built on camera (cabin, well, watchtower); a staircase
            mine. The SAME generator also emits a 19-min / 248-event instance (game_v30.mp4) and can
            scale to any length — see the scaling note below.
```

## Notes

- **Real first-person gameplay** — a moving player, real mining with the camera turning to
  each block, sword and bow combat, and structures assembled block by block. Real-life
  analog: gameplay/instructional-video analysis and embodied-agent behaviour verification.
  Distinct from VPT/MineRL frame-level inverse dynamics: this is long-horizon and
  event-level, not per-frame action regression.
- **Order-based scoring** handles the moving camera and the variable-FPS software render.
  Video time was verified to be an exact offset of event time (checked against two landmarks
  64 s apart), but order remains the scored quantity.
- **The HUD is the real game HUD, and it is evidence.** It is composited from the actual
  Minecraft GUI sprites shipped with prismarine-viewer (`gui/widgets.png` hotbar and
  selector, `gui/icons.png` hearts / hunger / XP bar, the real 16x16 item textures) at
  vanilla geometry — GUI scale 3, hotbar at x=centre-91 and y=height-22, hearts at y=-39,
  XP at y=-32. The highlighted slot tracks the item the player actually held at that moment,
  from the bot's own held-item timeline, so the weapon component is answerable rather than
  guessable. The held item is also drawn first-person in the lower right, and two effects the
  renderer omits are composited back from the event log: the vanilla block-break crack grows
  over each dig, and a red hit-flash marks each kill (timing exact; placement centre-anchored
  because the camera is aimed at the target when it acts).

## Fairness constraints enforced during generation

Each was found by inspecting frames, and each would otherwise have put unanswerable rows
into the ground truth.

1. **Only mobs this renderer actually draws are in the vocabulary.** An audit of 27 mobs
   found 11 render (`generator/MOB_RENDER_AUDIT.md`): zombies, skeletons, creepers,
   spiders, villagers, foxes, rabbits, horses and llamas are invisible even though the entity
   exists and the camera tracks it. Earlier drafts scored kills on invisible mobs.
2. **Every scored kill was witnessed.** A kill is recorded only if the mob was present and in
   range for several consecutive attack ticks with the camera on it. An earlier session
   contained a panda kill that happened entirely off camera. In the shipped session, 0 of 25
   kills were rejected by this gate.
3. **Every scored placement was witnessed.** Before each block the player backs off and, if
   the block is not in frame, walks around to that block's own side of the structure — which
   is also how a person builds. A block that still cannot be framed is placed (so the
   building completes) but excluded from the ledger. In the shipped session 5 placements were
   excluded this way.
4. **No blind-guessable runs.** Build palettes alternate within each layer and the mine is cut
   through layered strata, so long runs of one repeated block no longer dominate the ledger —
   closing the earlier weakness where a plausible-house guess partly matched.

## Known limitations

- **The task is a MEDIUM, not sub-0.10.** Codex scores **0.355 on the shipped v32** (precision 0.60,
  recall 0.32, 808 tool calls) — an earlier v31 run scored 0.164 (recall 0.13). The difficulty is
  recall-limited and run-dependent: the reward tracks how much of the 53-min video the agent watches
  (recall 0.13 -> 0.32 moved the score 0.16 -> 0.36), so it lands ~0.16-0.36. Order-aware LCS-F2 is
  deliberately generous to a confident partial answer. Recall weighting (F2, beta=2) punishes
  confident-partial answers; it lowered the number only
  slightly because the agent reports more events when recall is weighted. See calibration/scores.md.
- Order-aware scoring leaves part of the reward recoverable from the target multiset alone; the
  shuffled ablation at **0.245** quantifies that ceiling — a property (reproducing the exact
  633-event multiset means watching the whole video), not a shortcut. The genuine shortcuts,
  most-common-token (0.081) and actions-right-targets-wrong (0.026), are both under 0.15.
- **Weapon credit is gated on ledger alignment.** Scored independently it was nearly free (two weapon
  classes): an all-"stone" answer scored ledger 0.03 and weapon 1.0. Credit is now granted only on
  kills inside the ledger's LCS alignment; the oracle stays at exactly 1.0.
- **The closed vocabulary is asserted against the ledger at build time.** The staircase mine records
  the real blocks it digs, so the vocabulary must cover the terrain of every biome on the route, not
  just the gather categories. `build_p1_gt_v11.py` refuses to emit a task whose ground truth contains
  an unlisted target — it caught `brown_terracotta` in badlands on a real session.
- 2.4% of frames are dominated by a single colour (distant vistas and sky), measured with
  `generator/frame_audit.py`; mean dominant-colour share is 0.242. Run-to-run variation on
  that metric is ±1–2 points and is driven by spawn terrain, so it is reported rather than optimised
  against.
- **Every structure is verified visible from the camera.** The generator raycasts to each finished
  build and checks the first block hit belongs to it, logging `ORBIT_SHOWN n/m` (cabin 6/6,
  watchtower 5/5, well 5/5). Placements the camera missed are not silently written into the world —
  they are deferred and placed for real on camera in a second pass (residual 0), so nothing exists in
  the finished build that is absent from the ledger. Each element is built as one screen-left-to-right
  run from a fixed vantage, so the fill direction matches the camera, and the space above every
  placed block is cleared so none is tucked under an overhang.
