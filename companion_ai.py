"""A hero companion shares the party's normal combat and progression rules."""
import math
import progression
import combat_environment as terrain


def defensive_move(room, bot, enemy, light_range, now):
    """Commit briefly to an escape, then resume positioning. Never gain extra speed."""
    if bot.get("aiDodgeUntil",0) > now:
        bot["aiMoveAt"] = 0
        move(bot, bot["aiDodgeGoal"], now)
        return True
    zones = list(room.get("hazards", [])) + [z for z in (room.get("environment") or {}).get("zones", [])
              if z["kind"] == "poison" or z["kind"] == "trap" and z.get("warnAt")]
    danger = any(math.hypot(bot["x"]-z["x"],bot["y"]-z["y"]) < z["radius"]+25 for z in zones)
    shots = [s for s in room["projectiles"] if s["side"] == "enemy"]
    danger |= any(terrain.circle_hit(s["x"],s["y"],s["x"]+s["vx"]*.65,s["y"]+s["vy"]*.65,
                                    bot["x"],bot["y"],s.get("radius",7)+24) is not None for s in shots)
    for foe in room["enemies"]:
        pending = foe.get("pendingAttack") or foe.get("roleAttack")
        if pending and pending["kind"] in ("charge","charger","ambusher"):
            dx,dy = pending["x"]-foe["x"],pending["y"]-foe["y"]
            length = max(.001,math.hypot(dx,dy))
            reach = math.hypot(pending.get("endX",pending["x"])-foe["x"],pending.get("endY",pending["y"])-foe["y"])
            danger |= terrain.circle_hit(foe["x"],foe["y"],foe["x"]+dx/length*reach,foe["y"]+dy/length*reach,bot["x"],bot["y"],55) is not None
        if pending and pending["kind"] == "bruiser":
            danger |= math.hypot(bot["x"]-foe["x"],bot["y"]-foe["y"]) < 95
    distance = math.hypot(enemy["x"]-bot["x"],enemy["y"]-bot["y"]) if enemy else 999
    kite = enemy and light_range > 120 and distance < 105 and enemy.get("stunUntil",0) <= now
    strafe = enemy and not bot.get("reviving") and distance < light_range and now >= bot.get("aiStrafeAt",0)
    if not (danger or kite or strafe): return False
    if bot.get("reviving") and not danger: return False
    side = -bot.get("aiDodgeSide",1)
    candidates = []
    for i in range(8):
        angle = i*math.pi/4
        x,y = bot["x"]+math.cos(angle)*110, bot["y"]+math.sin(angle)*110
        if not (35<x<925 and 35<y<505) or not terrain.walkable(room,x,y): continue
        if not terrain.line_clear(room,bot,{"x":x,"y":y}): continue
        score = min(80,min([math.hypot(x-z["x"],y-z["y"])-z["radius"] for z in zones],default=80))
        for shot in shots:
            if terrain.circle_hit(shot["x"],shot["y"],shot["x"]+shot["vx"]*.9,shot["y"]+shot["vy"]*.9,x,y,shot.get("radius",7)+25) is not None:
                score -= 200
        if enemy:
            new_distance = math.hypot(x-enemy["x"],y-enemy["y"])
            score -= abs(new_distance-min(light_range*.75,180))*.35
            cross = (enemy["x"]-bot["x"])*(y-bot["y"])-(enemy["y"]-bot["y"])*(x-bot["x"])
            score += 25 if cross*side > 0 else 0
            if kite and new_distance<distance: score -= 120
        candidates.append((score,[x,y]))
    if not candidates: return False
    bot.update(aiDodgeGoal=max(candidates,key=lambda pair:pair[0])[1], aiDodgeUntil=now+.65,
               aiDodgeSide=side,aiStrafeAt=now+1.8,aiMoveAt=0,reviving=None)
    move(bot,bot["aiDodgeGoal"],now)
    return True


def move(bot, goal, now):
    if now >= bot.get("aiMoveAt", 0):
        bot["aiMoveAt"] = now+.4
        bot["aiGoal"] = list(goal)
    dx, dy = bot["aiGoal"][0]-bot["x"], bot["aiGoal"][1]-bot["y"]
    length = math.hypot(dx, dy)
    bot["dx"], bot["dy"] = (dx/length, dy/length) if length > 12 else (0, 0)


def equip_loot(world, room, bot):
    for item in list(bot["inventory"]):
        slot = 0 if item["kind"] == "weapon" else 1
        if item["slot"] != "tool":
            continue
        old = bot["toolSlots"][slot]
        field = "damage" if slot == 0 else "armor"
        if old is None or item.get(field, 0) > old.get(field, 0):
            world._action(room["code"], bot["id"], {"action": "equipItem", "slot": slot, "item": item["id"]})


def tick(world, room, now, ability_sets):
    humans = [p for p in world._active_players(room) if not p.get("bot")]
    if not humans:
        return
    for bot in [p for p in room["players"].values() if p.get("bot")]:
        bot["attacking"] = False
        if progression.locked(room, bot) or bot["status"] != "alive" or room["phase"] in ("lobby", "defeat", "cleared"):
            bot["dx"], bot["dy"] = 0, 0
            continue
        leader = next((p for p in humans if p["id"] == room["host"]), humans[0])
        phase = room["phase"]
        if phase == "combat":
            downed = [p for p in world._active_players(room) if p["status"] == "downed"]
            enemy = min(room["enemies"], key=lambda e: math.hypot(e["x"]-bot["x"], e["y"]-bot["y"]), default=None)
            if downed:
                rescue = min(downed, key=lambda p: math.hypot(p["x"]-bot["x"], p["y"]-bot["y"]))
                if math.hypot(rescue["x"]-bot["x"], rescue["y"]-bot["y"]) <= 55:
                    bot["dx"], bot["dy"] = 0, 0
                    if not bot.get("reviving"):
                        world._revive(room, bot)
                else:
                    move(bot, (rescue["x"], rescue["y"]), now)
            elif enemy:
                bot["reviving"] = None
                light = next(a for a in ability_sets[bot["class"]] if a[0] == bot["abilities"][0])
                distance = math.hypot(enemy["x"]-bot["x"], enemy["y"]-bot["y"])
                if distance > light[5]*.8:
                    move(bot, (enemy["x"], enemy["y"]), now)
                else:
                    bot["dx"], bot["dy"] = 0, 0
                bot["attacking"] = True
            else:
                move(bot, (leader["x"]+35, leader["y"]), now)
            light = next(a for a in ability_sets[bot["class"]] if a[0] == bot["abilities"][0])
            defensive_move(room, bot, enemy, light[5], now)
            # A short waypoint around cover prevents endlessly walking into its edge.
            goal = bot.get("aiGoal")
            if goal and (bot["dx"] or bot["dy"]) and not terrain.line_clear(room,bot,{"x":goal[0],"y":goal[1]}):
                dx,dy = goal[0]-bot["x"],goal[1]-bot["y"]
                length = max(1,math.hypot(dx,dy))
                for side in (bot.get("aiDodgeSide",1),-bot.get("aiDodgeSide",1)):
                    point = (bot["x"]-dy/length*80*side,bot["y"]+dx/length*80*side)
                    if terrain.walkable(room,*point) and 28<point[0]<932 and 30<point[1]<510:
                        bot["aiMoveAt"] = 0; move(bot,point,now); break
            if not room.get("waveStartsAt") and now >= bot.get("aiCastAt", 0):
                bot["aiCastAt"] = now+.2
                for index, aid in enumerate(bot["abilities"]):
                    if room["phase"] != "combat":
                        break
                    ability = next(a for a in ability_sets[bot["class"]] if a[0] == aid)
                    if ability[3] == "team_heal" and all(p["hp"] >= p["maxHp"]*.8 for p in world._active_players(room) if p["status"] == "alive"):
                        continue
                    if index == 0 and downed:
                        continue
                    try:
                        world._cast_ability(room, bot, index)
                    except ValueError:
                        pass  # Normal cooldown, mana and valid-target rules still apply.
                for item in list(bot["inventory"]):
                    if (item["kind"] == "heal" and bot["hp"] < bot["maxHp"]*.5) or (item["kind"] == "mana" and bot["mana"] < 25):
                        world._action(room["code"], bot["id"], {"action": "useItem", "item": item["id"]})
                        break
        elif phase == "peace":
            move(bot, (480, 30) if all(p.get("questAccepted") for p in humans) else (leader["x"]+35, leader["y"]), now)
        elif phase == "stage_exit":
            move(bot, (480, 30) if any(p["y"] < 200 for p in humans) else (leader["x"]+30, leader["y"]), now)
        elif phase == "routes":
            votes = room["routeVotes"]
            route_id = votes.get(leader["id"]) or next(iter(votes.values()), None)
            if route_id:
                index = next(i for i, r in enumerate(room["routes"]) if r["id"] == route_id)
                path = [(480, 320), (260 if index == 0 else 700, 170), (28 if index == 0 else 932, 170)]
                if bot.get("aiRoute") != route_id:
                    bot.update(aiRoute=route_id, aiPathIndex=0, aiMoveAt=0)
                point = path[bot["aiPathIndex"]]
                if math.hypot(bot["x"]-point[0], bot["y"]-point[1]) < 25 and bot["aiPathIndex"] < 2:
                    bot["aiPathIndex"] += 1
                    bot["aiMoveAt"] = 0
                move(bot, path[bot["aiPathIndex"]], now)
            else:
                move(bot, (leader["x"], leader["y"]), now)
        elif phase == "town":
            ready = all(p.get("townExitReady") for p in humans)
            bot["townExitReady"] = False
            move(bot, (480, 490) if ready else (480, 460), now)
        elif phase == "chest":
            chest = room["chest"]
            if bot["id"] not in chest["decisions"]:
                move(bot, (chest["x"], chest["y"]), now)
                if math.hypot(bot["x"]-chest["x"], bot["y"]-chest["y"]) <= 60:
                    if bot["chestReward"]:
                        old = min(bot["inventory"], key=lambda item: item["sell"])
                        world._action(room["code"], bot["id"], {"action": "chestClaim", "replace": old["id"]})
                    else:
                        world._action(room["code"], bot["id"], {"action": "openChest"})
                    equip_loot(world, room, bot)
            else:
                bot["dx"], bot["dy"] = 0, 0
        elif phase == "puzzle":
            puzzle = room["puzzle"]
            own = puzzle["rooms"][bot["id"]]
            if not own["totemSeen"]:
                totem = own["totem"]
                move(bot, (totem["x"], totem["y"]), now)
                if math.hypot(bot["x"]-totem["x"], bot["y"]-totem["y"]) <= 58:
                    own["totemSeen"] = True
                    world._say(room, bot["id"], bot["name"], f"Clue for {own['clueForName']}: {own['clue']}")
            elif bot.get("aiRunePuzzle") == puzzle["id"]:
                rune = next(r for r in own["runes"] if r["rune"] == own["target"])
                move(bot, (rune["x"], rune["y"]), now)
            else:
                bot["dx"], bot["dy"] = 0, 0
