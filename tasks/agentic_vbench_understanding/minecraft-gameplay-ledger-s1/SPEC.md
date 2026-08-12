---
title: Task Spec Card
summary: minecraft-gameplay-ledger-s1 — reconstruct a player's action ledger, with the weapon used per kill, from a first-person Minecraft session.
---

# Task Spec Card

```yaml
task: agentic_vbench_understanding/minecraft-gameplay-ledger-s1

cognitive_level: understanding
# Follow a moving first-person session across eight biomes and reconstruct the ordered
# sequence of deliberate actions — 1135 actions over ~120 minutes — including which weapon
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
    shuffled_ledger: 0.221  # right multiset, wrong order — order sensitivity, not a shortcut
    single_token_xN: 0.056  # most common (action,target) repeated
    targets_wrong: 0.019    # actions right, every target replaced by "stone"

difficulty:
  strong_agent_reward: 0.174   # Codex gpt-5.6-sol (xhigh) on the shipped v36; recall 0.134, precision
                               # 0.528, 288/1135 events, weapon 0.268; rollout calibration/rollouts/codex_v36_*
  agent_model: "codex gpt-5.6-sol, model_reasoning_effort=xhigh"
  note: "RECALL-LIMITED and run-dependent (recall = agent's ~fixed ~200-300 reconstructed events /
         total). Measured on renders of THIS generator: v32 (628 events, 53 min) = 0.355; v33 (1046
         events, 93 min) = 0.236; v34 (1005 events, 95 min) = 0.177; the shipped v36 (1135 events,
         120 min, every action re-verified on-camera — see fairness constraints) = 0.174, essentially
         matching v34. An honest MEDIUM; the difficulty lever is event count/density, not a metric
         change. Recall is run-dependent, so it varies ~0.16-0.36 across runs. n=1 per render."

anti_shortcut:
  single_frame: 0.0             # Codex given one mid-video frame: correctly wrote an empty ledger
  most_common_token_xN: 0.056   # the single commonest (action, target), repeated
  actions_right_targets_stone: 0.019
  correct_multiset_shuffled: 0.221   # order sensitivity, not a shortcut — see Known limitations
  empty: 0.0
  frame_dump_no_tools: 0.0      # a 120-min video at 1 fps is >7000 frames, far past any context window

input:
  url: https://huggingface.co/datasets/explcre/agenticvbench-understanding-materials/resolve/main/minecraft-gameplay-ledger-s1/game_v36.mp4
  sha256: 8393f938b9bc2d0606d1d19552b05661616954b460766c65ee3be8a2531528ad
  length_min: 120.5
  resolution: 720
  contents: 1135 events (206 mine, 839 place, 90 kill); 42 distinct block/mob types; biomes forest,
            beach, desert, snowy tundra, jungle, plains, savanna, badlands (x5 laps, re-rolled
            palettes); structures built on camera (cabin with a full gable roof, well, watchtower);
            a staircase mine. Every recorded event is guaranteed on-camera (see fairness constraints).
            The SAME generator scales to any length (628-event 53-min and 248-event 19-min instances
            also exist).
```

## Notes

- **Real first-person gameplay** — a moving player, real mining with the camera turning to
  each block, sword and bow combat, and structures assembled block by block. Real-life
  analog: gameplay/instructional-video analysis and embodied-agent behaviour verification.
  Distinct from VPT/MineRL frame-level inverse dynamics: this is long-horizon and
  event-level, not per-frame action regression.
- **Order-based scoring** handles the moving camera and the variable-FPS software render.
  Video time is an offset of event time, but order remains the scored quantity.
- **The HUD is the real game HUD, and it is evidence.** It is composited from the actual
  Minecraft GUI sprites shipped with prismarine-viewer (`gui/widgets.png` hotbar and
  selector, `gui/icons.png` hearts / hunger / XP bar, the real 16x16 item textures) at
  vanilla geometry — GUI scale 3, hotbar at x=centre-91 and y=height-22, hearts at y=-39,
  XP at y=-32. The highlighted slot tracks the item the player actually held at that moment,
  from the bot's own held-item timeline, so the weapon component is answerable rather than
  guessable. The held item is also drawn first-person in the lower right, and two effects the
  renderer omits are composited back from the event log: a red hit-flash marks each kill, and
  the vanilla block-break crack grows over each dig. The crack is **projected onto the mined
  block's exact screen position** from the camera pose recorded at the swing (pinhole model,
  the viewer's real 75-deg FOV), and scaled by the block's distance, so it sits ON the block —
  not at a fixed screen point. Timing and placement are both exact; the sprite is the real
  vanilla `destroy_stage` texture.

## Fairness constraints enforced during generation

Each was found by inspecting frames, and each would otherwise have put unanswerable rows
into the ground truth.

1. **Only mobs this renderer actually draws are in the vocabulary.** An audit of 27 mobs
   found 11 render (`generator/MOB_RENDER_AUDIT.md`): zombies, skeletons, creepers,
   spiders, villagers, foxes, rabbits, horses and llamas are invisible even though the entity
   exists and the camera tracks it. Earlier drafts scored kills on invisible mobs.
2. **Every scored kill was witnessed.** A kill is recorded only if the mob was present and in
   range for several consecutive attack ticks with the camera on it. In the shipped v36 session
   35 attempted kills were rejected by this gate (off-camera / not witnessed) and 90 recorded.
3. **Every scored action is framed dead-centre, not merely on screen.** The viewer's vertical
   FOV is 75 deg, so a block more than ~24 deg off the view axis is at the frame edge. Before
   each placement the bot moves to a vantage at the block's OWN height — using creative flight
   for high courses like the roof — backed off along the block's outward normal, and aims the
   camera dead-centre with clear line-of-sight; a block that cannot be framed that way from any
   vantage is **skipped entirely — neither placed nor recorded** (15 in the shipped v36 session),
   so the world and the ledger stay identical and every recorded placement is provably on-camera.
   Mines are framed the same way and settled on-camera through the full crack window before the dig.
4. **No blind-guessable runs.** Build palettes alternate within each layer, the roof timber
   **rotates per lap** (oak / spruce / birch / jungle / acacia), and the mine is cut through
   layered strata, so no single (action, block) token dominates the ledger — the most-common-token
   shortcut is 0.056 (see anti-shortcut).

## Known limitations

- **The task is a MEDIUM, not sub-0.10.** On prior renders of this generator Codex scored 0.355 (v32,
  628 events), 0.236 (v33, 1046 events) and 0.177 (v34, 1005 events). The shipped v36 (1135 events,
  120 min) is denser and re-verified all-visible; its strong-agent number is being re-measured
  (see difficulty). Recall-limited: the agent reconstructs a roughly fixed absolute number of events,
  so recall = that / total falls as the ledger grows — event count/density is the difficulty lever,
  not the (already strict, order-aware, recall-weighted) metric. See calibration/scores.md.
- Order-aware scoring leaves part of the reward recoverable from the target multiset alone; the
  shuffled ablation at **0.221** quantifies that ceiling — a property (reproducing the exact
  1135-event multiset means watching the whole video), not a shortcut. The genuine shortcuts,
  most-common-token (0.056) and actions-right-targets-wrong (0.019), are both well under 0.15.
- **Weapon credit is gated on ledger alignment.** Scored independently it was nearly free (two weapon
  classes): an all-"stone" answer scored ledger 0.02 and weapon 1.0. Credit is now granted only on
  kills inside the ledger's LCS alignment; the oracle stays at exactly 1.0.
- **The closed vocabulary is asserted against the ledger at build time.** The staircase mine records
  the real blocks it digs, so the vocabulary must cover the terrain of every biome on the route, not
  just the gather categories. `build_p1_gt_v11.py` refuses to emit a task whose ground truth contains
  an unlisted target.
- **Every structure is verified visible from the camera.** The generator raycasts to each finished
  build and checks the first block hit belongs to it (`ORBIT_SHOWN n/m`; all 15 structures shown in
  the shipped session). Placements the camera cannot frame with clear line-of-sight from any vantage
  are **skipped — not placed, not recorded** (15 in the shipped v36 session), so nothing exists in the
  finished build that is absent from the ledger and no recorded placement is off-camera.
- **Spurious air-mines are dropped.** A shaft cut that resolves to `air`/`cave_air` (an existing cave
  pocket) is not a nameable block; both `rec()` in the generator and the GT builder drop it (0 in v36).
