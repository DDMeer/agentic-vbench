# ABLATION (recall): reconstruct a StarCraft II build order from prior knowledge

A 1v1 StarCraft II ladder game was played on **Automaton LE**, Terran vs Zerg, lasting about
15 minutes (game version base build 75689). No footage of this game is provided.

Write, from your own knowledge of the game and of typical/known build orders, the full list of
structures each player built with the game-second each was STARTED. Report every instance
(rebuilds and duplicates are separate events). Structure tech morphs (OrbitalCommand,
PlanetaryFortress, Lair, Hive, GreaterSpire) and add-ons (TechLab/Reactor) are separate events.

Scoring pools both players into one timeline; an event counts only if race, structure name and
time all match the real game within +/-3 seconds.

## Output -> write `./answer.json`

The JSON below shows the required **format only** — its names and times are invented
placeholders, not events from this match.

```json
{"players":[
  {"race":"terran","buildings":[{"t_seconds":137,"name":"Factory"}]},
  {"race":"zerg","buildings":[{"t_seconds":262,"name":"RoachWarren"}]}
]}
```

Output your best estimate rather than nothing.
