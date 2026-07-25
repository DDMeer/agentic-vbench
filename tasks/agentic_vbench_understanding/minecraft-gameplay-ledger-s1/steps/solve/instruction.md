# Minecraft First-Person Gameplay Ledger Reconstruction

You are given one video at `/workspace/materials/game.mp4`: a first-person recording of a
Minecraft session. The player travels across several biomes (forest, desert, snowy tundra,
jungle, badlands), gathers many kinds of block, **builds a house block-by-block on camera**,
hunts animals with a **diamond sword** and with a **bow and arrow**, and finally digs a
staircase mine and extracts every ore it exposes.

Reconstruct the player's deliberate action ledger **in the order the actions happen**:

- **mine** — the player breaks a block; report the block type.
- **place** — the player places a block (while building); report the block type.
- **kill** — the player kills a mob; report the mob type **and the weapon used**.

Identify blocks and mobs from their rendered textures. The weapon is visible two ways: the
selected slot in the on-screen hotbar, and how the animal dies — a **sword** kill happens
with the player right next to the animal and swinging, while a **bow** kill happens at a
distance with arrows in flight. Use any tools in the image (for example `ffmpeg` and
`ffprobe`) to seek through and sample the video.

## What to submit

Write `/workspace/output/solution.json`, actions in chronological order:

```json
{
  "events": [
    {"action": "mine",  "target": "oak_log"},
    {"action": "kill",  "target": "cow",   "tool": "sword"},
    {"action": "place", "target": "stone_bricks"},
    {"action": "kill",  "target": "chicken", "tool": "bow"},
    {"action": "mine",  "target": "iron_ore"}
  ]
}
```

- `action`: `mine`, `place`, or `kill`.
- `target`: a block type (mine/place) or a mob type (kill), from the vocabulary below.
- `tool`: `sword` or `bow` — required on `kill` events, ignored elsewhere.

## Vocabulary (closed)

Blocks (mine/place): `oak_log`, `birch_log`, `spruce_log`, `jungle_log`, `acacia_log`,
`dark_oak_log`, `oak_leaves`, `birch_leaves`, `spruce_leaves`, `grass_block`, `dirt`,
`gravel`, `stone`, `cobblestone`, `stone_bricks`, `andesite`, `granite`, `diorite`, `sand`, `sandstone`, `cactus`,
`snow`, `snow_block`, `ice`, `packed_ice`, `red_sand`, `terracotta`, `orange_terracotta`,
`white_terracotta`, `red_terracotta`, `yellow_terracotta`, `brown_terracotta`,
`light_gray_terracotta`, `red_sandstone`, `coarse_dirt`, `podzol`, `clay`, `coal_ore`, `iron_ore`,
`gold_ore`, `redstone_ore`, `diamond_ore`, `lapis_ore`, `emerald_ore`, `oak_planks`,
`spruce_planks`, `birch_planks`, `jungle_planks`, `oak_stairs`, `oak_fence`, `glass`, `oak_door`, `torch`.

Mobs (kill): `cow`, `pig`, `sheep`, `chicken`, `wolf`, `mooshroom`, `polar_bear`, `turtle`,
`panda`.

## How it is scored

Order-aware and recall-weighted: the reward is `0.85 *` an order-aware **F2** over the ordered
`(action, target)` sequence (a longest-common-subsequence match, with recall weighted twice as
heavily as precision) plus `0.15 *` a weapon score over the kills you place correctly. Missed
actions, invented actions, wrong block/mob types, and wrong ordering all lower the score.

**Recall matters more than a confident subset.** Because recall is weighted double, reporting a
small number of events you are sure about scores poorly — the task is to reconstruct *most* of the
ledger, in order, not to list a safe fraction of it. Watch the whole video.

## Rules
- Stay inside this working directory. Do not read, write, or search outside it.
- Do not look anything up online. Reconstruct the actions from the video, in order.
- Report only `mine`, `place`, and `kill` actions (not walking, looking, or pickups).
