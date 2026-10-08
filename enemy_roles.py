"""Recognizable family roles with committed windups and recovery."""
import math
import time
import combat_environment as terrain

ROLES = {"minotaur":"charger","serpent":"ranged","wolf":"ambusher","spider":"ambusher","troll":"bruiser","draco":"draco"}
KITS = {"charger":"Knight","ranged":"Archer","ambusher":"Rogue","support":"Healer","bruiser":"Knight","draco":"Wizard"}


def assign(room):
    eligible = [e for e in room["enemies"] if not any(e.get(k) for k in ("boss","miniBoss","assassin","structure")) and e["kind"] != "draco"]
    support_id = eligible[-1]["id"] if len(room["enemies"]) >= 3 and eligible else None
    for index,e in enumerate(room["enemies"]):
        if e.get("boss") or e.get("miniBoss"): continue
        role = "ambusher" if e.get("assassin") else ROLES.get(e["kind"],"bruiser")
        if e["id"] == support_id:
            role = "support"
        e.update(combatRole=role, **{"class":KITS[role]}, roleReadyAt=0)


def approach(room,e,target,now,dt,stop):
    if now >= e.get("moveDecisionAt",0):
        dx,dy = target["x"]-e["x"],target["y"]-e["y"]
        distance = max(.001,math.hypot(dx,dy))
        gx,gy = target["x"]-dx/distance*stop,target["y"]-dy/distance*stop
        if stop < 0: gx,gy = e["x"]-dx/distance*70,e["y"]-dy/distance*70
        if e["combatRole"]=="ambusher" and distance > 130:
            side = 1 if sum(map(ord,e["id"]))%2 else -1
            gx,gy = target["x"]-dy/distance*90*side,target["y"]+dx/distance*90*side
        e.update(moveDecisionAt=now+.8,moveGoal=[max(28,min(932,gx)),max(30,min(510,gy))])
    gx,gy = e.get("moveGoal",[e["x"],e["y"]])
    dx,dy = gx-e["x"],gy-e["y"]
    distance = max(.001,math.hypot(dx,dy))
    step = min(distance,e["speed"]*dt)
    terrain.move(room,e,e["x"]+dx/distance*step,e["y"]+dy/distance*step,avoid=True)


def tick(world,room,e,target,now,dt):
    role = e.setdefault("combatRole",ROLES.get(e["kind"],"bruiser"))
    if role == "draco":
        tick_draco(world,room,e,target,now,dt)
        return
    old_x,old_y = e["x"],e["y"]
    e["facingX"],e["facingY"] = target["x"]-e["x"],target["y"]-e["y"]
    if e.get("roleChargeUntil",0)>now:
        terrain.move(room,e,e["x"]+e["roleVx"]*dt,e["y"]+e["roleVy"]*dt)
        expected=math.hypot(e['roleVx'],e['roleVy'])*dt
        if expected>1 and math.hypot(e['x']-old_x,e['y']-old_y)<expected*.3:
            e.update(roleChargeUntil=now,roleRecoverUntil=now+2.0,moving=False)
            world._add_effect(room,'impact',e['x'],e['y'],'#f3d69a',duration=.4)
            return
        for actor in world._combat_targets(room):
            hit = terrain.circle_hit(old_x,old_y,e["x"],e["y"],actor["x"],actor["y"],28)
            if actor["status"]=="alive" and hit is not None and actor["id"] not in e["roleHits"]:
                e["roleHits"].append(actor["id"]);world._damage_player(room,e,actor,round(e["damage"]*1.15))
        e["moving"] = True
        return
    if e.get("roleRecoverUntil",0)>now:
        e["moving"] = False;return
    pending = e.get("roleAttack")
    if pending:
        e["moving"] = False
        if now<pending["releaseAt"]: return
        e.pop("roleAttack")
        e["animationUntil"] = time.time()+.4
        if role in ("charger","ambusher"):
            dx,dy = pending["x"]-e["x"],pending["y"]-e["y"]
            distance = max(.001,math.hypot(dx,dy))
            speed = 270 if role=="charger" else 220
            duration = .55 if role=="charger" else .35
            e.update(roleVx=dx/distance*speed,roleVy=dy/distance*speed,roleChargeUntil=now+duration,roleHits=[],roleRecoverUntil=now+duration+.9)
        elif role=="support" and pending.get("ally"):
            ally = next((a for a in room["enemies"] if a["id"]==pending["ally"]),None)
            if ally and math.hypot(ally["x"]-e["x"],ally["y"]-e["y"])<250:
                ally["hp"] = min(ally["maxHp"],ally["hp"]+max(4,round(ally["maxHp"]*.08)))
                world._add_effect(room,"heal",ally["x"],ally["y"],"#94e5aa",duration=.6)
            e["roleRecoverUntil"] = now+.8
        elif role in ("ranged","support"):
            world._launch_projectile(room,side="enemy",owner_id=e["id"],target_id=pending["targetId"],x=e["x"],y=e["y"],damage=e["damage"],color=e["color"],attack_class=KITS[role],speed=225,turn_rate=.4)
            shot = room["projectiles"][-1]
            angle = math.atan2(pending["y"]-e["y"],pending["x"]-e["x"])
            shot.update(vx=math.cos(angle)*225,vy=math.sin(angle)*225)
            e["roleRecoverUntil"] = now+.6
        else:
            for actor in world._combat_targets(room):
                if actor["status"]=="alive" and math.hypot(actor["x"]-e["x"],actor["y"]-e["y"])<=70 and terrain.line_clear(room,e,actor):
                    world._damage_player(room,e,actor,e["damage"])
            e["roleRecoverUntil"] = now+1.0
        return
    distance = math.hypot(target["x"]-e["x"],target["y"]-e["y"])
    clear = terrain.line_clear(room,e,target)
    reach = {"ranged":260,"support":220,"charger":290,"ambusher":175,"bruiser":65}[role]
    stop = 180 if role in ("ranged","support") else 40
    if role in ("ranged","support") and distance<105: stop = -1
    elif not clear: stop = 25
    elif distance<=reach: stop = distance
    approach(room,e,target,now,dt,stop)
    e["moving"] = math.hypot(e["x"]-old_x,e["y"]-old_y)>.1
    if now < e.get("roleReadyAt",0): return
    wounded = [a for a in room["enemies"] if a is not e and a["hp"]<a["maxHp"]*.9 and math.hypot(a["x"]-e["x"],a["y"]-e["y"])<230]
    if (distance<=reach and clear) or (role=="support" and wounded):
        delay = .8 if role in ("charger","support") else .6
        e["roleAttack"] = {"kind":role,"x":target["x"],"y":target["y"],"targetId":target["id"],"startedAt":now,"releaseAt":now+delay}
        if role=="support" and wounded: e["roleAttack"]["ally"] = min(wounded,key=lambda a:a["hp"]/a["maxHp"])["id"]
        rate = min(1.5,e.get("attackRate",1))
        e["roleReadyAt"] = now+({"charger":4.5,"ambusher":4,"support":6,"ranged":2.4,"bruiser":2.5}[role])/rate
        e["moving"] = False


def tick_draco(world, room, e, target, now, dt):
    """A quick shot, then a committed close-range bite; misses still advance the cycle."""
    e["facingX"], e["facingY"] = target["x"]-e["x"], target["y"]-e["y"]
    if e.get("roleRecoverUntil", 0) > now:
        e["moving"] = False
        return
    pending = e.get("roleAttack")
    if pending:
        e["moving"] = False
        if now < pending["releaseAt"]:
            return
        e.pop("roleAttack")
        e["animationUntil"] = time.time()+.3
        if pending["kind"] == "draco_projectile":
            world._launch_projectile(room, side="enemy", owner_id=e["id"], target_id=pending["targetId"],
                x=e["x"], y=e["y"], damage=e["damage"], color=e["color"], attack_class="Wizard",
                speed=300, radius=8, turn_rate=.3)
            # Commit to the announced direction, with only gentle initial tracking.
            angle = math.atan2(pending["y"]-e["y"], pending["x"]-e["x"])
            room["projectiles"][-1].update(vx=math.cos(angle)*300, vy=math.sin(angle)*300)
            e["dracoNext"] = "draco_melee"
        else:
            actor = next((p for p in world._combat_targets(room) if p["id"] == pending["targetId"] and p["status"] == "alive"), None)
            if actor and math.hypot(actor["x"]-e["x"], actor["y"]-e["y"]) <= 55 and terrain.line_clear(room,e,actor):
                world._damage_player(room,e,actor,e["damage"])
                world._add_effect(room,"enemy_attack",e["x"],e["y"],e["color"],actor["x"],actor["y"],.2,attack_class="Knight")
            e["dracoNext"] = "draco_projectile"
        e.update(roleRecoverUntil=now+.25, moveDecisionAt=0)
        return
    kind = e.get("dracoNext", "draco_projectile")
    reach = 245 if kind == "draco_projectile" else 55
    distance = math.hypot(target["x"]-e["x"],target["y"]-e["y"])
    clear = terrain.line_clear(room,e,target)
    old_x, old_y = e["x"], e["y"]
    stop = distance if distance <= reach and clear else 135 if kind == "draco_projectile" and clear else 30
    approach(room,e,target,now,dt,stop)
    e["moving"] = math.hypot(e["x"]-old_x,e["y"]-old_y)>.1
    if now >= e.get("roleReadyAt",0) and distance <= reach and clear:
        delay = .35 if kind == "draco_projectile" else .4
        e["roleAttack"] = {"kind":kind,"x":target["x"],"y":target["y"],"targetId":target["id"],"startedAt":now,"releaseAt":now+delay}
        e["roleReadyAt"] = now+1.25/min(1.5,e.get("attackRate",1))
        e["moving"] = False


def attack_view(pending, now):
    if not pending: return None
    duration = max(.01, pending["releaseAt"]-pending.get("startedAt",pending["releaseAt"]-.9))
    return dict(pending, remaining=max(0,pending["releaseAt"]-now),
                progress=max(0,min(1,1-(pending["releaseAt"]-now)/duration)))
