#!/usr/bin/env python
"""Regenerate the build-order ground truth for sc2-build-order-reconstruction.

Source of truth: the SAME .SC2Replay the video was rendered from. No manual annotation.

Rules (these are the rules SPEC.md documents; keep the two in sync):
  * Event time = construction START, in game-seconds: t = round(game_loop / 22.4).
  * Structures only, from an explicit per-race whitelist (STRUCTURES below). Anything not
    on the whitelist is excluded: units, larvae/eggs/cocoons, creep tumors, neutral map
    objects, beacons, and the two summonables that are not build-order structures
    (AutoTurret, KD8Charge).
  * A structure placed via `UnitInitEvent` counts only if it also has a `UnitDoneEvent`
    (i.e. it finished). Cancelled placements are excluded.
  * The two starting structures (Terran CommandCenter, Zerg Hatchery) come from
    `UnitBornEvent` at loop 0.
  * Structure tech morphs are separate events at the morph moment, from
    `UnitTypeChangeEvent`: CommandCenter->OrbitalCommand/PlanetaryFortress,
    Hatchery->Lair->Hive, Spire->GreaterSpire. Non-structure type changes
    (SupplyDepotLowered, Siege mode, burrow, cocoons, ...) are excluded.
  * Every instance counts: a rebuilt or duplicated structure at a new time is a separate
    event; there is no de-duplication to a type set.

Usage:
    python calibration/gen_sc2_gt.py --replay gt/match.SC2Replay \
        --out-terran gt/gt_terran.json --out-zerg gt/gt_zerg.json \
        --out-pooled steps/solve/tests/gt.json
"""
import argparse
import collections
import json
import io

import sc2reader
from sc2reader.resources import Replay

LOOPS_PER_SECOND = 22.4  # SC2 "Faster" game speed: 22.4 loops == 1 game-second

TERRAN_STRUCTURES = {
    "CommandCenter", "OrbitalCommand", "PlanetaryFortress", "SupplyDepot", "Barracks",
    "Refinery", "Factory", "Starport", "EngineeringBay", "Bunker", "MissileTurret",
    "SensorTower", "GhostAcademy", "Armory", "FusionCore", "BarracksTechLab",
    "BarracksReactor", "FactoryTechLab", "FactoryReactor", "StarportTechLab",
    "StarportReactor",
}
ZERG_STRUCTURES = {
    "Hatchery", "Lair", "Hive", "SpawningPool", "Extractor", "RoachWarren", "BanelingNest",
    "EvolutionChamber", "HydraliskDen", "InfestationPit", "Spire", "GreaterSpire",
    "NydusNetwork", "UltraliskCavern", "SpineCrawler", "SporeCrawler",
}
STRUCTURES = {"terran": TERRAN_STRUCTURES, "zerg": ZERG_STRUCTURES}
# Morph targets that ARE build-order structures (UnitTypeChangeEvent).
MORPH_TARGETS = {"OrbitalCommand", "PlanetaryFortress", "Lair", "Hive", "GreaterSpire"}
# Summonable / consumable "structures" the engine reports but a build order does not contain.
EXCLUDED_SUMMONS = {"AutoTurret", "KD8Charge", "CreepTumor", "CreepTumorBurrowed",
                    "CreepTumorQueen", "PointDefenseDrone"}
START_STRUCTURES = {"CommandCenter", "Hatchery", "Nexus"}


def _load(path):
    """sc2reader chokes on replays with no cache handles (locally rendered games)."""
    original = Replay.load_details

    def patched(self):
        try:
            original(self)
        except IndexError:
            self.region = "us"

    Replay.load_details = patched
    try:
        return sc2reader.load_replay(path, load_level=4)
    finally:
        Replay.load_details = original


def race_of(replay, unit_names_by_pid):
    """pid -> lowercase race, plus structure-name -> race for owner-less morph events.

    Replays rendered locally have no cache handles, so sc2reader cannot parse the details
    header and `replay.players` comes back empty. In that case the race of each player is
    inferred from the race-exclusive structures that player actually built.
    """
    by_pid = {}
    for p in replay.players:
        by_pid[p.pid] = str(p.play_race).lower()
    if not by_pid:
        for pid, names in unit_names_by_pid.items():
            votes = {race: sum(1 for n in names if n in structs)
                     for race, structs in STRUCTURES.items()}
            race, n = max(votes.items(), key=lambda kv: kv[1])
            if n:
                by_pid[pid] = race
    by_name = {}
    for race in set(by_pid.values()):
        for name in STRUCTURES.get(race, ()):
            by_name[name] = race
    return by_pid, by_name


def collect(replay):
    init, born, morph = [], [], []
    done = set()
    names_by_pid = collections.defaultdict(list)
    for e in replay.tracker_events:
        kind = type(e).__name__
        name = getattr(e, "unit_type_name", None)
        if kind == "UnitDoneEvent":
            done.add(e.unit_id)
        elif kind == "UnitInitEvent":
            init.append((e.control_pid, name, e.frame, e.unit_id))
            names_by_pid[e.control_pid].append(name)
        elif kind == "UnitBornEvent":
            born.append((e.control_pid, name, e.frame, e.unit_id))
            names_by_pid[e.control_pid].append(name)
        elif kind == "UnitTypeChangeEvent":
            owner = getattr(getattr(e, "unit", None), "owner", None)
            morph.append((getattr(owner, "pid", None), name, e.frame))

    pid_race, name_race = race_of(replay, names_by_pid)
    events = collections.defaultdict(list)   # race -> [(t, name)]
    skipped = collections.Counter()

    def keep(race, name, frame):
        events[race].append((round(frame / LOOPS_PER_SECOND), name))

    for pid, name, frame, uid in init:
        race = pid_race.get(pid)
        if name in EXCLUDED_SUMMONS or race is None or name not in STRUCTURES.get(race, ()):
            skipped[("not_a_structure", name)] += 1
            continue
        if uid not in done:
            skipped[("cancelled", name)] += 1
            continue
        keep(race, name, frame)

    for pid, name, frame, uid in born:
        race = pid_race.get(pid)
        if race is None or name not in START_STRUCTURES or frame != 0:
            continue
        keep(race, name, frame)

    for pid, name, frame in morph:
        if name not in MORPH_TARGETS:
            skipped[("morph_not_structure", name)] += 1
            continue
        race = pid_race.get(pid) or name_race.get(name)
        if race is None:
            skipped[("morph_no_owner", name)] += 1
            continue
        keep(race, name, frame)

    return events, skipped, pid_race


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", default="gt/match.SC2Replay")
    ap.add_argument("--out-terran", default="gt/gt_terran.json")
    ap.add_argument("--out-zerg", default="gt/gt_zerg.json")
    ap.add_argument("--out-pooled", default="steps/solve/tests/gt.json")
    args = ap.parse_args()

    replay = _load(args.replay)
    events, skipped, pid_race = collect(replay)

    pooled = []
    for race, out_path in (("terran", args.out_terran), ("zerg", args.out_zerg)):
        rows = sorted(events[race], key=lambda x: (x[0], x[1]))
        pid = next((p for p, r in pid_race.items() if r == race), None)
        with io.open(out_path, "w", encoding="utf-8") as f:
            json.dump({"pid": pid, "n_events": len(rows),
                       "events": [{"t": t, "name": n} for t, n in rows]},
                      f, indent=1, ensure_ascii=False)
        pooled += [{"race": race, "name": n, "t": t} for t, n in rows]
        print(f"{race}: {len(rows)} events -> {out_path}")

    pooled.sort(key=lambda e: (e["t"], e["race"], e["name"]))
    with io.open(args.out_pooled, "w", encoding="utf-8") as f:
        json.dump({"n_events": len(pooled), "events": pooled}, f, indent=1, ensure_ascii=False)
    print(f"pooled: {len(pooled)} events -> {args.out_pooled}")
    if skipped:
        print("excluded:")
        for (why, name), n in sorted(skipped.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if why != "not_a_structure" or name in EXCLUDED_SUMMONS:
                print(f"  {why:20s} {name:24s} x{n}")


if __name__ == "__main__":
    main()
