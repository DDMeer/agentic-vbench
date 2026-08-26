# Reconstruct BOTH players' build orders from a tiled bird's-eye StarCraft II video

You are given NINE videos: a 3×3 tiling of ONE bird's-eye view of the WHOLE map of a 1v1
StarCraft II match (Terran vs Zerg), the full ~15-minute game. Tiles `tile_r{row}c{col}.mp4`
(row 0=top..2=bottom, col 0=left..2=right) together cover the entire battlefield with no gaps
and no clipping. BOTH bases are in the grid: the Terran main (grey/red metal) sits in the
right-hand column and the Zerg main (buildings on purple creep) in the left-hand column;
each main straddles a tile seam, and both players expand to further bases during the game, so
locate the bases yourself instead of assuming one tile per player.

- The frames are the **RAW render — no brightness/contrast processing** (so they are dim; you
  may brighten/adjust them yourself with ffmpeg if it helps you read structures).
- Each video is 5000 frames sampled ~every 0.18 game-seconds. `frames_time.json` maps frame
  index → game-seconds, so you can time each event precisely (to ~1 s).
- The tiles are encoded at 15 fps, so frame `i` is at `i/15` seconds of *video* time; convert
  to game-seconds through `frames_time.json`, never by reading the video clock directly.
- Time each structure by the moment its construction STARTS — the first frame at which its
  foundation/pit is visible on the ground, not when it finishes.
- Buildings do NOT simply persist: they can be destroyed and rebuilt (a rebuild on the same
  spot is a new event), and a structure's sprite changes without a new building being made
  (SupplyDepots raise and lower repeatedly, a CommandCenter grows an Orbital dish, a Hatchery
  becomes a Lair, tanks siege). Judge from the ground footprint, not from any single sprite.
- There is no HUD, production panel, resource/supply counter, minimap, or player name anywhere
  in the video — only the rendered game world.

## What to produce

Reconstruct, per player, the chronological list of every structure and tech building made,
with the game-time (in seconds) each was started. Report EVERY instance — a rebuilt or
duplicate building at a new time is a SEPARATE event (do not de-duplicate to a type set).

- Structure tech morphs ARE separate events, timed at the morph: CommandCenter→OrbitalCommand
  (or →PlanetaryFortress), Hatchery→Lair→Hive, Spire→GreaterSpire.
- Add-ons (BarracksTechLab/Reactor, FactoryTechLab/Reactor, StarportTechLab/Reactor) are
  separate events, timed when the add-on starts.
- A placement that is CANCELLED before it finishes is NOT an event.
- Excluded, even though you will see them: units, creep tumors, mineral fields, vespene
  geysers, destructible rocks, and the two summonables that are not build-order structures
  (Raven AutoTurret, Reaper KD8Charge).

Scoring: both players are pooled into one timeline; a reported event counts only if the race,
the structure name and the time all match a ground-truth event, with **|Δt| ≤ 3 seconds**.
Wrong name, wrong race or a mis-timed event scores nothing, so guessing does not pay.

Structure names — Terran: CommandCenter, OrbitalCommand, PlanetaryFortress, SupplyDepot,
Barracks, Refinery, Factory, Starport, EngineeringBay, Bunker, MissileTurret, SensorTower,
GhostAcademy, Armory, FusionCore, BarracksTechLab, BarracksReactor, FactoryTechLab,
FactoryReactor, StarportTechLab, StarportReactor.
Zerg: Hatchery, Lair, Hive, SpawningPool, Extractor, RoachWarren, BanelingNest,
EvolutionChamber, HydraliskDen, InfestationPit, Spire, GreaterSpire, NydusNetwork,
UltraliskCavern, SpineCrawler, SporeCrawler. (Name matching is case/space-insensitive.)

## Output → write `./answer.json`

The JSON below shows the required **format only** — its names and times are invented
placeholders, not events from this match.

```json
{"players":[
  {"race":"terran","buildings":[{"t_seconds":137,"name":"Factory"},{"t_seconds":642,"name":"Armory"}]},
  {"race":"zerg","buildings":[{"t_seconds":262,"name":"RoachWarren"},{"t_seconds":708,"name":"SpineCrawler"}]}
]}
```

Watch the entire game across all 9 tiles, using every tool available to you over many rounds of
tool calls (50+ preferred). Find each base among the tiles, track construction starts, and time
each via `frames_time.json`. Write `answer.json` early and refine it; do not fabricate. The nine
tiles + `frames_time.json` are the only inputs provided.
