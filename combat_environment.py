"""Stage-local destructible cover and terrain, simulated by the server."""
import math
import random
import secrets
import time


def prepare(room):
    previous = room.get("environment")
    if previous and previous["stage"] == room["stage"] and previous["region"] == room.get("region"):
        return
    room.setdefault("terrainSeed", secrets.randbelow(2**31))
    rng = random.Random(room["terrainSeed"] + room["stage"]*7919)
    region = room.get("region", "woodland")
    # Sparse, well separated features leave the middle and entry lanes open.
    points = [(x+rng.randint(-24,24), y+rng.randint(-20,20))
              for x in (140,310,650,820) for y in (170,280,375)]
    rng.shuffle(points)
    obstacles = []
    count = rng.choice((1,2))
    for x,y in points:
        if any(math.hypot(x-o['x'],y-o['y']) < 240 for o in obstacles): continue
        i = len(obstacles)
        kind = "rock" if region in ("cavern","frost") and i != 1 else "crate"
        hp = 42 if kind == "rock" else 24
        obstacles.append({"id":secrets.token_hex(4),"kind":kind,"x":x,
            "y":y,"radius":24,"hp":hp,"maxHp":hp})
        if len(obstacles) == count: break
    kind = rng.choice(("trap","poison","ice") if region == "frost" else ("trap","poison"))
    radius = {"trap":34,"poison":48,"ice":90}[kind]
    x,y = next((p for p in points if all(math.hypot(p[0]-o['x'],p[1]-o['y']) >= radius+o['radius']+70
                                       for o in obstacles)), (480,220))
    zones = [{"id":kind,"kind":kind,"x":x,"y":y,"radius":radius,"warnAt":0,"readyAt":0}]
    room["environment"] = {"stage":room["stage"],"region":region,"obstacles":obstacles,"zones":zones}


def obstacles(room):
    return [o for o in (room.get("environment") or {}).get("obstacles",[]) if o["hp"] > 0]


def circle_hit(ax,ay,bx,by,x,y,radius):
    dx,dy = bx-ax,by-ay
    ox,oy = ax-x,ay-y
    length = dx*dx+dy*dy
    if ox*ox+oy*oy <= radius*radius: return 0.0
    if length < .000001: return None
    dot = ox*dx+oy*dy
    discriminant = dot*dot-length*(ox*ox+oy*oy-radius*radius)
    if discriminant < 0: return None
    t = (-dot-math.sqrt(discriminant))/length
    return t if 0 <= t <= 1 else None


def shot_block(room,ax,ay,bx,by,radius=0):
    hits = [(t,o) for o in obstacles(room)
            if (t:=circle_hit(ax,ay,bx,by,o["x"],o["y"],o["radius"]+radius)) is not None]
    return min(hits,key=lambda hit:hit[0],default=None)


def line_clear(room,a,b):
    return shot_block(room,a["x"],a["y"],b["x"],b["y"]) is None


def walkable(room,x,y,radius=12):
    return all(math.hypot(x-o["x"],y-o["y"]) >= radius+o["radius"] for o in obstacles(room))


def move(room,actor,x,y,*,avoid=False):
    if actor.get('rootUntil', 0) > time.monotonic():
        actor['moving'] = False
        return
    # A summon can arrive beside its owner at a cover edge; let it escape safely.
    for obstacle in obstacles(room):
        dx,dy = actor["x"]-obstacle["x"],actor["y"]-obstacle["y"]
        distance = math.hypot(dx,dy)
        if distance < obstacle["radius"]+12:
            dx,dy = (dx/max(.001,distance),dy/max(.001,distance)) if distance else (1,0)
            actor["x"],actor["y"] = obstacle["x"]+dx*(obstacle["radius"]+13),obstacle["y"]+dy*(obstacle["radius"]+13)
    start_x,start_y = actor["x"],actor["y"]
    dx,dy = x-start_x,y-start_y
    steps = max(1,math.ceil(math.hypot(dx,dy)/8))
    for _ in range(steps):
        nx,ny = max(28,min(932,actor["x"]+dx/steps)),max(30,min(510,actor["y"]+dy/steps))
        if walkable(room,nx,actor["y"]): actor["x"] = nx
        if walkable(room,actor["x"],ny): actor["y"] = ny
    if avoid and math.hypot(actor["x"]-start_x,actor["y"]-start_y) < math.hypot(dx,dy)*.3:
        # Deterministic detour; does not mirror the player's movement input.
        side = 1 if sum(ord(c) for c in actor["id"])%2 else -1
        for sign in (side,-side):
            nx,ny = start_x-dy*sign,start_y+dx*sign
            if 28<=nx<=932 and 30<=ny<=510 and walkable(room,nx,ny):
                actor["x"],actor["y"] = nx,ny
                break


def player_move(room,actor,dx,dy,speed,dt):
    icy = any(z["kind"]=="ice" and math.hypot(actor["x"]-z["x"],actor["y"]-z["y"])<z["radius"]
              for z in (room.get("environment") or {}).get("zones",[]))
    vx,vy = dx*speed,dy*speed
    if icy:
        blend = min(1,dt*3.5)
        vx = actor.get("slideVx",0)+(vx-actor.get("slideVx",0))*blend
        vy = actor.get("slideVy",0)+(vy-actor.get("slideVy",0))*blend
    actor["slideVx"],actor["slideVy"] = vx,vy
    move(room,actor,actor["x"]+vx*dt,actor["y"]+vy*dt)


def damage_cover(world,room,obstacle,amount):
    if obstacle["hp"] <= 0: return
    obstacle["hp"] = max(0,obstacle["hp"]-max(1,amount))
    world._add_effect(room,"impact",obstacle["x"],obstacle["y"],"#d6af7b",duration=.25)
    if not obstacle["hp"]:
        world._add_effect(room,"burst",obstacle["x"],obstacle["y"],"#d6af7b",duration=.4)


def tick(world,room,now):
    if room["phase"] != "combat" or room.get("waveStartsAt"): return
    env = room.get("environment") or {}
    actors = world._active_players(room)+room.get("summons",[])+list(room["enemies"])
    for zone in env.get("zones",[]):
        inside = [a for a in actors if a.get("status","alive")=="alive" and
                  math.hypot(a["x"]-zone["x"],a["y"]-zone["y"]) <= zone["radius"]]
        if zone["kind"]=="trap":
            if zone.get("warnAt") and now >= zone["warnAt"]:
                zone.update(warnAt=0,readyAt=now+4)
                for actor in inside: hurt(world,room,zone,actor,8+world._effective_stage(room)//4)
                world._add_effect(room,"burst",zone["x"],zone["y"],"#ffb277",duration=.3)
            elif inside and not zone.get("warnAt") and now >= zone.get("readyAt",0):
                zone["warnAt"] = now+.75
        elif zone["kind"]=="poison":
            for actor in inside:
                if now >= actor.get("terrainHitAt",0):
                    actor["terrainHitAt"] = now+1
                    hurt(world,room,zone,actor,3+world._effective_stage(room)//6)


def hurt(world,room,zone,actor,damage):
    if actor in room["enemies"]:
        actor["hp"] = max(1,actor["hp"]-damage)  # Terrain weakens foes; players still earn the final kill.
        actor["damageTaken"] = actor.get("damageTaken",0)+1
    else:
        world._damage_player(room,zone,actor,damage)


def view(room,now):
    env = room.get("environment")
    if not env or room["phase"] not in ("combat","chest","stage_exit"): return None
    return {"obstacles":[dict(o) for o in env["obstacles"]],
        "zones":[dict(z,warning=bool(z.get("warnAt")),warningLeft=max(0,z.get("warnAt",0)-now)) for z in env["zones"]]}
