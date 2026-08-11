---
title: Task Spec Card
summary: minecraft-gameplay-ledger-s1 — reconstruct a player's action ledger, with the weapon used per kill, from a first-person Minecraft session.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/minecraft-gameplay-ledger-s1

cognitive_level: understanding
# Follow a moving first-person session across seven biomes and reconstruct the ordered
# sequence of deliberate actions — 1005 actions over ~95 minutes — including which weapon
# was used for each kill. Every recorded action is guaranteed on-camera by construction.

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
    shuffled_ledger: 0.239  # right multiset, wrong order — order sensitivity, not a shortcut
    single_token_xN: 0.085  # most common (action,target) repeated
    targets_wrong: 0.025    # actions right, every target replaced by "stone"

difficulty:
  strong_agent_reward: 0.177   # Codex gpt-5.6-sol (xhigh) on the shipped v34; rollout calibration/rollouts/codex_v34_*
  agent_model: "codex gpt-5.6-sol, model_reasoning_effort=xhigh"
  note: "RECALL-LIMITED and run-dependent (recall = agent's ~fixed ~200-300 reconstructed events /
         total). Measured on prior renders of THIS generator: v32 (628 events, 53 min) = 0.355;
         v33 (1046 events, 93 min) = 0.236. v34 is the all-events-visible 1005-event / 95-min build,
         v34 (1005 events, 95 min, all-visible) = 0.177 (reported 233/1005 events, recall 0.16,
         precision 0.70, 1308 tool calls). An honest MEDIUM; the difficulty lever is event
         count/density, not a metric change. Recall is run-dependent, so ~0.16-0.36 across runs. n=1."

anti_shortcut:
  single_frame: 0.0             # Codex given one mid-video frame: correctly wrote an empty ledger
  most_common_token_xN: 0.081   # the single commonest (action, target), repeated
  actions_right_targets_stone: 0.026
  correct_multiset_shuffled: 0.245   # order sensitivity, not a shortcut — see Known limitations
  empty: 0.0
  frame_dump_no_tools: 0.0      # a 53-min video at 1 fps is >3000 frames, far past any context window

input:
  url: https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/main/minecraft-gameplay-ledger-s1/game_v34.mp4
  sha256: 6b3052b3fcb48155caeb7e9675d0b1f6f6e8b2319aeaff57f4481e2beaf8e94d
  length_min: 94.9
  resolution: 720
  contents: 1005 events (282 mine, 645 place, 78 kill); 48 distinct block/mob types; biomes forest,
            beach, desert, snowy tundra, jungle, plains, savanna, badlands (x5 laps, re-rolled
            palettes); structures built on camera (cabin, well, watchtower); a staircase mine. Every
            recorded event is guaranteed on-camera (see fairness constraints). The SAME generator
            scales to any length (628-event 53-min and 248-event 19-min instances also exist).
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
3. **Every scored placement was witnessed.** Before each block the player backs off and, if the
   block is not in frame, walks around to that block's own side of the structure — which is also how
   a person builds. A block that STILL cannot be framed with clear line-of-sight from any vantage is
   **skipped entirely — neither placed nor recorded** — so the ledger and the world stay identical
   and every recorded placement is provably on-camera. In the shipped v34 session 54 placements
   were skipped this way.
4. **No blind-guessable runs.** Build palettes alternate within each layer and the mine is cut
   through layered strata, so long runs of one repeated block no longer dominate the ledger —
   closing the earlier weakness where a plausible-house guess partly matched.

## Known limitations

- **The task is a MEDIUM, not sub-0.10.** On prior renders of this generator Codex scored 0.355 (v32,
  628 events) and 0.236 (v33, 1046 events); the shipped v34 (1005 events, all-visible) = 0.177
  (reported 233/1005 events; recall-limited). Recall-limited: the agent reconstructs a roughly fixed absolute
  number of events, so recall = that / total falls as the ledger grows — event count/density is the
  difficulty lever, not the (already strict, order-aware, recall-weighted) metric. See calibration/scores.md.
- Order-aware scoring leaves part of the reward recoverable from the target multiset alone; the
  shuffled ablation at **0.245** quantifies that ceiling — a property (reproducing the exact
  1005-event multiset means watching the whole video), not a shortcut. The genuine shortcuts,
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
  build and checks the first block hit belongs to it (`ORBIT_SHOWN n/m`). Placements the camera
  cannot frame with clear line-of-sight from any vantage are **skipped — not placed, not recorded**
  (54 in the shipped v34 session), so nothing exists in the finished build that is absent from the
  ledger and no recorded placement is off-camera. Each element is built as one screen-left-to-right
  run from a fixed vantage so the fill direction matches the camera, and the space above every placed
  block is cleared so none is tucked under an overhang.
- **Spurious air-mines are dropped.** A shaft cut that resolves to `air`/`cave_air` (an existing cave
  pocket) is not a nameable block; both `rec()` in the generator and the GT builder drop it (3 in v34).
