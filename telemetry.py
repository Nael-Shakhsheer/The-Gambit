"""Combat contribution measurements; damage counts actual HP lost, not overkill."""
import copy
import time

OVERALL_FIELDS = ("damageDealt", "damageTaken", "revives", "deaths", "kills")


def _overall_player(room, pid):
    totals = room.setdefault("runStats", {})
    player = room["players"].get(pid)
    if pid not in totals:
        totals[pid] = {"name": player["name"] if player else "Adventurer",
                       "class": player["class"] if player else None,
                       **dict.fromkeys(OVERALL_FIELDS, 0)}
    if player:
        totals[pid].update(name=player["name"], **{"class": player["class"]})
    return totals[pid]


def count(room, pid, field, value=1):
    _overall_player(room, pid)[field] += value


def overall(room):
    for pid in room["players"]:
        _overall_player(room, pid)
    totals = room.get("runStats", {})
    order = list(room["players"]) + [pid for pid in totals if pid not in room["players"]]
    return copy.deepcopy([totals[pid] for pid in order])


def start(room, now, ability_sets):
    room["combatStats"] = {
        "stage": room["stage"], "startedAt": now, "lastTick": now,
        'difficulty': room.get('difficulty','medium'), 'totalStages':room.get('totalStages',25),
        'testerMode':room.get('totalStages')==9,
        'balanceStage':min(25,1+3*(room['stage']-1)) if room.get('totalStages')==9 else room['stage'],
        'townsVisited':room.get('townsVisited',0), 'routePressure':room.get('routePressure',0),
        'townPressureStages':list(room.get('townPressureStages',[])),
        "partySize": sum(p.get("connected", True) for p in room["players"].values()),
        "players": {
            pid: {"name": p["name"], "class": p["class"], "heroDamage": 0,
                  "summonDamage": 0, "heroDamageTaken": 0, "summonDamageTaken": 0,
                  "damagePrevented": 0, "summonSeconds": 0, "summonSpawns": 0,
                  "healingGiven": 0, "protectionGiven": 0, "boostDamageGiven": 0,
                  "summonDeaths": 0, "summonLifetimes": [], "ultimateCasts": 0,
                  "openingCooldown": next((a[6] for a in ability_sets.get(p["class"], [])
                                            if a[7] == "ultimate" and a[0] in p["abilities"]), 0)}
            for pid, p in room["players"].items() if p.get("connected", True)
        }, "summons": {},
    }


def add(room, player_id, field, value):
    if field in ("heroDamage", "summonDamage"):
        count(room, player_id, "damageDealt", value)
    elif field == "heroDamageTaken":
        count(room, player_id, "damageTaken", value)
    player = (room.get("combatStats") or {}).get("players", {}).get(player_id)
    if player is not None:
        player[field] = player.get(field, 0) + value


def participant(room, player, now, ability_sets):
    stats = room.get("combatStats")
    if not stats:
        return
    stats.setdefault("startingPartySize", stats["partySize"])
    stats["partySize"] = max(stats["partySize"], sum(p.get("connected", True) for p in room["players"].values()))
    if player["id"] not in stats["players"]:
        # Rejoining a stage already underway must still credit this hero's work.
        scratch = {"stage": room["stage"], "players": {player["id"]: player}}
        start(scratch, now, ability_sets)
        row = scratch["combatStats"]["players"][player["id"]]
        row["joinedAfterSeconds"] = round(now - stats["startedAt"], 2)
        stats["players"][player["id"]] = row


def summon_spawn(room, summon, now):
    stats = room.get("combatStats")
    if stats:
        stats["summons"][summon["id"]] = {"owner": summon["ownerId"], "ability": summon["abilityId"], "born": now}
        add(room, summon["ownerId"], "summonSpawns", 1)


def summon_end(room, summon, now, died):
    stats = room.get("combatStats")
    record = stats["summons"].pop(summon["id"], None) if stats else None
    if record and record["owner"] in stats["players"]:
        player = stats["players"][record["owner"]]
        player["summonLifetimes"].append({"ability": record["ability"], "seconds": round(now - record["born"], 2), "died": died})
        player["summonDeaths"] += int(died)


def tick(room, now):
    stats = room.get("combatStats")
    if not stats:
        return
    dt = max(0, now - stats["lastTick"])
    stats["lastTick"] = now
    for summon in room.get("summons", []):
        add(room, summon["ownerId"], "summonSeconds", dt)


def finish(room, now, outcome):
    stats = room.get("combatStats")
    if not stats:
        return None
    tick(room, now)
    seconds = round(max(0, now - stats["startedAt"]), 2)
    players = copy.deepcopy(stats["players"])
    for record in stats["summons"].values():
        if record["owner"] in players:
            players[record["owner"]]["summonLifetimes"].append({"ability": record["ability"], "seconds": round(now - record["born"], 2), "died": False})
    for player in players.values():
        player["summonSeconds"] = round(player["summonSeconds"], 2)
        player["endedBeforeUltimate"] = seconds < player["openingCooldown"]
        player["totalDamage"] = player["heroDamage"] + player["summonDamage"]
    report = {"version": 2, "run": room.get("runId", room["code"]), "at": time.time(),
              "stage": stats["stage"], "partySize": stats["partySize"], "startingPartySize": stats.get("startingPartySize", stats["partySize"]), "seconds": seconds,
              "outcome": outcome, "players": list(players.values())}
    report.update({key:stats[key] for key in ('difficulty','totalStages','testerMode','balanceStage','townsVisited','routePressure','townPressureStages')})
    room.setdefault("stageReports", []).append(report)
    room["stageReports"] = room["stageReports"][-50:]
    room["combatStats"] = None
    return report
