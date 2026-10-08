"""Repeatable bot observations, separate from human play telemetry.

Run: python -B tools/balance_probe.py
No server connection, player save writes or god mode. Bots approach inside
Light range, use defensive companion movement and cast available abilities.
They do not revive, use items or select gear. --before-tuning substitutes the
previous summon/stun constants in this simulation process only.
"""
import json
import math
from pathlib import Path
import random
import statistics
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game import ABILITY_SETS, GameWorld
import companion_ai


def probe(classes, stage, seed, druid_special="lightning_bird", druid_ultimate="ice_bear"):
    now = [1000.0]
    random.seed(seed)
    ids_rng = random.Random(seed*7919+stage)
    with patch("game.time.monotonic", side_effect=lambda: now[0]), \
         patch("game.secrets.randbelow", side_effect=lambda n: ids_rng.randrange(n)), \
         patch("game.secrets.token_hex", side_effect=lambda n: format(ids_rng.getrandbits(n*8),'0'+str(n*2)+'x')):
        world = GameWorld()
        code, host = world.create_room(classes[0])
        ids = [host] + [world.join_room(code, hero)[1] for hero in classes[1:]]
        for pid, hero in zip(ids, classes):
            world.action(code, pid, {"action": "class", "class": hero})
            abilities = [next(a[0] for a in ABILITY_SETS[hero] if a[7] == kind) for kind in ("light", "special", "ultimate")]
            if hero == "Druid":
                abilities = ["thornshot", druid_special, druid_ultimate]
            world.action(code, pid, {"action": "loadout", "abilities": abilities})
        world.action(code, host, {"action": "start"})
        room = world.rooms[code]
        room.update(stage=stage, stageWave=1, assassinationStage=None, projectiles=[], effects=[])
        random.seed(seed + stage * 100)
        world._reset_cooldowns(room)
        world._spawn_wave(room)
        for _ in range(4800):  # Four simulated minutes per combat stage.
            for p in room["players"].values():
                if room["phase"] != "combat" or p["status"] != "alive" or room["waveStartsAt"]:
                    continue
                target = min(room["enemies"], key=lambda e: math.hypot(e["x"] - p["x"], e["y"] - p["y"]), default=None)
                if target:
                    dx, dy = target["x"] - p["x"], target["y"] - p["y"]
                    distance = max(.001, math.hypot(dx, dy))
                    light = next(a for a in ABILITY_SETS[p["class"]] if a[0] == p["abilities"][0])
                    p["dx"], p["dy"] = (dx / distance, dy / distance) if distance > light[5] * .75 else (0, 0)
                    p["attacking"] = True
                    companion_ai.defensive_move(room,p,target,light[5],now[0])
                for slot in (1, 2):
                    try:
                        world._cast_ability(room, p, slot)
                    except ValueError:
                        pass
            now[0] += .05
            world.tick()
            if room["phase"] != "combat":
                break
        if room.get("combatStats"):
            world._finish_stage_stats(room, "timeout")
        report = room["stageReports"][-1]
        report.update(source="bot simulation", seed=seed, lineup=classes,
                      druidLoadout=[druid_special, druid_ultimate] if "Druid" in classes else [])
        report.pop("run", None)
        report.pop("at", None)
        return report


def main():
    before_tuning = "--before-tuning" in sys.argv
    if before_tuning:
        from game import SUMMON_TYPES
        for aid,hp,interval in (("lightning_bird",55,.85),("fire_wolf",90,.75),("ice_bear",180,1.1),("nature_golem",240,1.4)):
            SUMMON_TYPES[aid].update(hp=hp,attackInterval=interval)
        def previous_stun(enemy, now):
            enemy["stunUntil"] = now+(.25 if enemy.get("boss") else .55 if enemy.get("miniBoss") else 1.5)
        GameWorld._stun = staticmethod(previous_stun)
    cases = [(hero,)+tuple(a for a in ("Knight","Archer","Healer","Wizard") if a != hero)[:size-1]
             for hero in ABILITY_SETS for size in (1,2,3,4)]
    reports = [probe(list(team), stage, seed) for stage in (1,8,16) for team in cases for seed in (1,2)]
    reports += [probe(["Druid"],stage,seed,"fire_wolf","nature_golem") for stage in (1,8,16) for seed in (1,2)]
    output = Path(__file__).resolve().parents[1] / "reports"
    output.mkdir(exist_ok=True)
    if before_tuning:
        (output / "balance-before-tuning.json").write_text(json.dumps(reports,indent=2),encoding="utf-8")
        print("Saved 198 matched simulations with previous summon/stun tuning.",flush=True)
        return
    (output / "balance-probe.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    lines = ["# Balance probe — 2026-10-07", "", "198 simulations: all eight heroes in solo and 2–4-player lineups, stages 1, 8 and 16, two seeds each. Additional solo cases test Wolf/Golem. Controlled observations, not human playtests or a final class ranking.", "",
             "Bots approach inside Light range, use the companion's defensive movement and cast equipped skills. They do not revive, use items or choose gear. Default first skills except Druid uses Thornshot. Stage 8 includes its boss wave. Four-minute timeouts count as failures. Higher stages start with fresh base gear and no town training, so their failures do not represent normal geared progression. Deterministic terrain, identifiers and seeds allow before/after tuning comparisons.", "",
             "| Stage / lineup | Clears | Median clear s | Hero damage | Healing | Wards | Boost assistance | Hero HP lost | Summon damage | Summon HP absorbed | Summon deaths/spawns | Ends before Ult |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    groups = {}
    for r in reports:
        key = (r["stage"], tuple(r["lineup"]), tuple(r["druidLoadout"]))
        groups.setdefault(key, []).append(r)
    for (stage, lineup, loadout), group in groups.items():
        clears = [r for r in group if r["outcome"] == "cleared"]
        rows = [p for r in group for p in r["players"]]
        total = lambda field: sum(p[field] for p in rows)
        seconds = f"{statistics.median(r['seconds'] for r in clears):.1f}" if clears else "—"
        label = " + ".join(lineup) + (" (" + "/".join(loadout) + ")" if loadout else "")
        lines.append(f"| {stage}: {label} | {len(clears)}/{len(group)} | {seconds} | {total('heroDamage')} | {total('healingGiven')} | {total('protectionGiven')} | {total('boostDamageGiven')} | {total('heroDamageTaken')} | {total('summonDamage')} | {total('summonDamageTaken')} | {total('summonDeaths')}/{total('summonSpawns')} | {total('endedBeforeUltimate')}/{len(rows)} |")
    lines += ["", "Columns total both seeds, including failures. Raw JSON separates every participant, includes summon survival durations and combined uptime. Healing counts actual HP restored, including revives; wards credit their caster for actual HP saved after armor. Boost assistance is the extra HP removed by a supported hero, already included in that hero's damage; do not sum those columns. Summon HP absorbed is actual HP lost, not an estimate of damage a hero would have taken. The visible Run stats remain the five requested overall totals.", "",
              "Live reports append to `data/balance.jsonl`. Validate tuning with matched human runs (stage, party size, gear and loadout); these bots cannot establish that every hero is balanced. See COMBAT_BALANCE_NOTES.md for tuning evidence and remaining limits."]
    (output / "BALANCE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {len(reports)} simulations to reports/BALANCE_REPORT.md and balance-probe.json")


if __name__ == "__main__":
    main()
