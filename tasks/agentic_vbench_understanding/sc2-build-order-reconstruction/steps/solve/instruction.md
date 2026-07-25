# Reconstruct BOTH players' build orders from a tiled bird's-eye StarCraft II video

You are given NINE videos: a 3×3 tiling of ONE bird's-eye view of the WHOLE map of a 1v1
StarCraft II match (Terran vs Zerg), the full ~15-minute game. Tiles `tile_r{row}c{col}.mp4`
(row 0=top..2=bottom, col 0=left..2=right) together cover the entire battlefield with no gaps
and no clipping. BOTH bases are in the grid: Terran (grey/red metal) around the top-right
(tile r0c2), Zerg (buildings on purple creep) around the lower-left (tile r2c0).

- The frames are the **RAW render — no brightness/contrast processing** (so they are dim; you
  may brighten/adjust them yourself with ffmpeg if it helps you read structures).
- Each video is 5000 frames sampled ~every 0.18 game-seconds. `frames_time.json` maps frame
  index → game-seconds, so you can time each event precisely (to ~1 s).
- Buildings persist once built; time each by the frame it FIRST appears.
- There is no HUD, production panel, resource/supply counter, minimap, or player name anywhere
  in the video — only the rendered game world.

## What to produce

Reconstruct, per player, the chronological list of every structure and tech building made,
with the game-time (in seconds) each was started. Report EVERY instance — a rebuilt or
duplicate building at a new time is a SEPARATE event (do not de-duplicate to a type set).
Tech morphs are separate events (CommandCenter→OrbitalCommand→PlanetaryFortress,
Hatchery→Lair→Hive, add-ons Reactor/TechLab). Exclude creep tumors, mineral fields, vespene
geysers, and destructible rocks.

Structure names — Terran: CommandCenter, OrbitalCommand, PlanetaryFortress, SupplyDepot,
Barracks, Refinery, Factory, Starport, EngineeringBay, Bunker, BarracksTechLab, BarracksReactor,
FactoryTechLab, FactoryReactor, StarportTechLab, StarportReactor, Armory, MissileTurret.
Zerg: Hatchery, Lair, Hive, SpawningPool, Extractor, RoachWarren, BanelingNest, EvolutionChamber,
HydraliskDen, SpineCrawler, SporeCrawler, Spire. (Name matching is case/space-insensitive.)

## Output → write `/workspace/output/solution.json`

```json
{"players":[
  {"race":"terran","buildings":[{"t_seconds":20,"name":"SupplyDepot"},{"t_seconds":45,"name":"Barracks"}]},
  {"race":"zerg","buildings":[{"t_seconds":18,"name":"SpawningPool"},{"t_seconds":55,"name":"Extractor"}]}
]}
```

Watch the entire game across all 9 tiles, using every tool available to you over many rounds of
tool calls (50+ preferred). Find each base among the tiles, track first-appearances, and time
each via `frames_time.json`. Write `/workspace/output/solution.json` early and refine it; do not
fabricate. The nine tiles + `frames_time.json` are the only inputs provided.
