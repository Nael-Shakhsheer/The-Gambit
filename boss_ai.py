"""Boss attacks use visible windups, fixed attack decisions and dodgeable areas."""
import math
import secrets
import combat_environment as terrain

WINDUPS = {"slam":1.0,"rocks":1.1,"charge":1.15,"volley":1.1,"breath":1.25,"pool":1.2,"meteor":1.5}
RECOVERY = {"slam":1.25,"rocks":1.1,"charge":1.3,"volley":1.0,"breath":1.4,"pool":1.0,"meteor":1.5}
SIGNATURES = {'raise_cover', 'shatter', 'venom_weave', 'fire_trail', 'ice_wall', 'storm_marks', 'dark_ring', 'arcane_cross'}
WINDUPS.update({kind: 1.4 for kind in SIGNATURES})
WINDUPS['venom_weave'] = 1.6
RECOVERY.update({kind: 1.6 for kind in SIGNATURES})


def view(room):
    boss = next((e for e in room.get('enemies', []) if e.get('boss')), None)
    if not boss or room.get('phase') != 'combat': return None
    tips = {'minotaur': 'Bait a charge into cover: it creates a 3s opening with +35% damage.',
            'troll': 'The Behemoth raises rocks, then shatters cover. Move when it marks your shelter.',
            'serpent': 'Bait the poison weave away from your path, or stun her during its wind-up.'}
    elements = {'Fire': 'Leave the marked breath lane; the ground keeps burning.',
                'Ice': 'Ice walls divide movement lanes. Use the gaps or break the shards.',
                'Storm': 'Spread out: nearby allies overlap lightning strikes.',
                'Dark': 'Dark rings leave a safe center; true form adds a delayed central strike.',
                'Arcane': 'Dodge the cross, then leave its center before the delayed detonation.'}
    phase = boss.get('bossPhase', 1)
    dragon = boss['kind'] == 'dragon'
    tip = elements.get(boss.get('affinity'), 'Avoid the marked areas.') if dragon else tips.get(boss['kind'], 'Dodge the wind-up and punish recovery.')
    if dragon and phase == 2:
        tip += {'Fire': ' A second fire lane now spreads beside it.', 'Ice': ' More shards now restrict the lanes.',
                'Storm': ' Close partners also trigger resonance strikes.'}.get(boss.get('affinity'), '')
    return {'tactic': tip, 'phaseLabel': ('ARMOR · TRUE FORM FOLLOWS' if phase==1 else 'TRUE FORM · PHASE 2') if dragon else 'BOSS',
            'phaseTwoHint': 'Breaking the armor awakens a larger, stronger form.' if dragon and phase==1 else ''}


def cover_at(room, enemy, x, y, *, ice=False):
    env = room.get('environment')
    if not env: terrain.prepare(room); env = room['environment']
    x, y = max(65, min(895, x)), max(70, min(470, y))
    actors = list(room.get('players', {}).values())+room.get('summons', [])+room.get('enemies', [])
    if len(terrain.obstacles(room)) >= 6 or any(math.hypot(a['x']-x, a['y']-y)<55 for a in actors if a.get('status','alive')=='alive'):
        return None
    if any(math.hypot(o['x']-x, o['y']-y)<65 for o in terrain.obstacles(room)): return None
    hp = 52 if ice else 90
    rock = dict(id=secrets.token_hex(4), kind='rock', x=x, y=y, radius=24, hp=hp, maxHp=hp,
                signatureOwner=enemy['id'], iceWall=ice)
    env['obstacles'].append(rock)
    return rock


def prepare(room, enemy):
    if enemy.get('signaturePrepared'): return
    enemy['signaturePrepared'] = True
    if enemy['kind'] == 'minotaur':
        for x,y in ((310,170),(650,370)):
            if len(terrain.obstacles(room)) < 3: cover_at(room, enemy, x, y)


def pattern(enemy):
    if enemy.get('boss'):
        if enemy['kind']=='minotaur': return ('charge','rocks','charge','slam')
        if enemy['kind']=='troll': return ('raise_cover','rocks','shatter','slam')
        if enemy['kind']=='serpent': return ('venom_weave','volley','venom_weave','slam')
        if enemy['kind']=='dragon':
            signature = {'Fire':'fire_trail','Ice':'ice_wall','Storm':'storm_marks','Dark':'dark_ring','Arcane':'arcane_cross'}[enemy['affinity']]
            return (signature,'meteor',signature,'breath') if enemy.get('bossPhase')==2 else (signature,'breath','volley','charge')
    return {'minotaur':('slam','rocks','charge'), 'troll':('slam','rocks','charge'),
            'serpent':('pool','volley','slam'), 'wolf':('charge','pool','volley'),
            'monster':('volley','slam','pool'), 'dragon':('breath','pool','volley','charge')}.get(enemy['kind'], ('volley','slam','pool'))


def prepare_signature(world, room, enemy, pending, now):
    kind, x, y = pending['kind'], pending['x'], pending['y']
    delay, phase = WINDUPS[kind], enemy.get('bossPhase', 1)
    token = pending['signatureToken'] = secrets.token_hex(4)
    def mark(px, py, radius=45, duration=.3, power=1, extra=0, label=None):
        h = area(room, enemy, max(40,min(920,px)), max(45,min(495,py)), now,
                 radius=radius, delay=delay+extra, duration=duration, power=power, kind=kind)
        h.update(signatureToken=token, label=label or kind.replace('_',' ').upper())
    if kind in ('raise_cover','ice_wall'):
        offsets = (-85,85) if kind=='raise_cover' or phase==1 else (-180,-60,60,180)
        pending['placements'] = [(max(65,min(895,x+offset)), max(80,min(455,y+45))) for offset in offsets]
        for px,py in pending['placements']: mark(px,py,36,power=.8,label='ICE WALL' if kind=='ice_wall' else 'ROCK RISE')
    elif kind=='shatter':
        covers = sorted(terrain.obstacles(room), key=lambda o:math.hypot(o['x']-x,o['y']-y))[:2]
        pending['coverIds'] = [o['id'] for o in covers]
        for cover in covers: mark(cover['x'],cover['y'],78,power=1.2,label='COVER SHATTER')
        if not covers: mark(x,y,90,power=1.1)
    elif kind=='venom_weave':
        angle = math.atan2(y-enemy['y'],x-enemy['x'])+math.pi/2
        gap = -1 if enemy['attackIndex']%2 else 1
        for i in range(-2,3):
            if i!=gap: mark(x+math.cos(angle)*i*66,y+math.sin(angle)*i*66,42,6,.55,label='POISON WEAVE')
    elif kind=='fire_trail':
        angle=math.atan2(y-enemy['y'],x-enemy['x'])
        for lane in (0,95) if phase==2 else (0,):
            for step in range(1,6):
                mark(enemy['x']+math.cos(angle)*step*65-math.sin(angle)*lane,
                     enemy['y']+math.sin(angle)*step*65+math.cos(angle)*lane,43,6,.6,label='BURNING LANE')
    elif kind=='storm_marks':
        humans=[p for p in world._active_players(room) if p['status']=='alive']
        for actor in humans: mark(actor['x'],actor['y'],65 if phase==1 else 78,power=1.1,label='LIGHTNING · SPREAD')
        if phase==2:
            for index,a in enumerate(humans):
                for b in humans[index+1:]:
                    if math.hypot(a['x']-b['x'],a['y']-b['y'])<180:
                        mark((a['x']+b['x'])/2,(a['y']+b['y'])/2,50,power=.9,extra=.65,label='RESONANCE')
            if len(humans)==1: mark(x,y,55,power=.9,extra=.65,label='AFTERSHOCK')
    elif kind in ('dark_ring','arcane_cross'):
        count=6 if kind=='dark_ring' else 4
        radius=95 if kind=='dark_ring' else 115
        for index in range(count):
            angle=index*math.tau/count
            mark(x+math.cos(angle)*radius,y+math.sin(angle)*radius,38,power=.85)
        if phase==2 or kind=='arcane_cross': mark(x,y,65,power=1.1,extra=.7,label='CENTER DETONATION')


def release_signature(world, room, enemy, pending):
    kind=pending['kind']
    if kind in ('raise_cover','ice_wall'):
        if kind=='ice_wall':
            for cover in terrain.obstacles(room):
                if cover.get('iceWall') and cover.get('signatureOwner')==enemy['id']:
                    terrain.damage_cover(world,room,cover,cover['hp'])
        for x,y in pending['placements']: cover_at(room,enemy,x,y,ice=kind=='ice_wall')
    elif kind=='shatter':
        for cover in terrain.obstacles(room):
            if cover['id'] in pending.get('coverIds',[]): terrain.damage_cover(world,room,cover,cover['hp'])


def interrupt(world, room, enemy, now):
    pending=enemy.get('pendingAttack')
    if not pending or pending['kind']!='venom_weave' or enemy.get('stunUntil',0)<=now: return
    enemy.pop('pendingAttack')
    room['hazards']=[h for h in room.get('hazards',[]) if h.get('signatureToken')!=pending.get('signatureToken') or h['activatesAt']<=now]
    enemy.update(recoverUntil=now+2, nextBossAttack=now+3)
    world._add_effect(room,'burst',enemy['x'],enemy['y'],enemy['color'],duration=.6,text='VENOM INTERRUPTED')


def area(room, enemy, x, y, now, *, radius=85, delay=.9, duration=.2, power=1, kind="slam"):
    room.setdefault("hazards", []).append({"id": secrets.token_hex(5), "ownerId": enemy["id"],
        "x": x, "y": y, "radius": radius, "damage": max(1, round(enemy["damage"]*power)),
        "color": enemy["color"], "kind": kind, "activatesAt": now+delay,
        "expiresAt": now+delay+duration, "nextHitAt": now+delay})
    return room['hazards'][-1]


def tick_areas(world, room, now):
    if room["phase"] != "combat":
        room["hazards"] = []
        return
    remaining = []
    for hazard in room.get("hazards", []):
        if hazard not in room.get('hazards', []): continue
        if now >= hazard["expiresAt"]:
            continue
        if now >= hazard["nextHitAt"]:
            hazard["nextHitAt"] = now+.8
            if hazard.get('side')=='hero':
                owner=room['players'].get(hazard['ownerId'])
                if owner:
                    for enemy in list(room['enemies']):
                        if math.hypot(enemy['x']-hazard['x'],enemy['y']-hazard['y']) <= hazard['radius']:
                            world._damage_enemy(room,owner,enemy,hazard['damage'],boost_source=hazard.get('boostSource'),boost_factor=hazard.get('boostFactor',1))
                    for cover in terrain.obstacles(room):
                        if math.hypot(cover['x']-hazard['x'],cover['y']-hazard['y']) <= hazard['radius']:
                            terrain.damage_cover(world,room,cover,hazard['damage'])
                continue
            for target in world._combat_targets(room):
                if target["status"] == "alive" and math.hypot(target["x"]-hazard["x"], target["y"]-hazard["y"]) <= hazard["radius"]+10:
                    world._damage_player(room, hazard, target, hazard["damage"])
            if world._check_party_wipe(room):
                break
        if hazard in room.get('hazards', []): remaining.append(hazard)
    room["hazards"] = remaining if room["phase"] == "combat" else []


def second_phase(world, room, enemy, now):
    enemy.update(bossPhase=2, name="Enraged "+enemy["name"],
                 maxHp=math.ceil(enemy["maxHp"]*1.6), damage=math.ceil(enemy["damage"]*1.35),
                 speed=enemy["speed"]*1.2, attackRate=enemy.get("attackRate", 1)*1.25,
                 nextBossAttack=now+2.5, stunUntil=0, bleedUntil=0, rootUntil=0, attackIndex=0)
    enemy["hp"] = enemy["maxHp"]
    enemy.pop("pendingAttack", None)
    enemy.pop("chargeUntil", None)
    enemy['recoverUntil'] = now+2
    room["hazards"] = []
    for shot in room["projectiles"]:
        if shot["side"] == "enemy":
            shot["expiresAt"] = now
    room["projectiles"] = [p for p in room["projectiles"] if p["side"] == "hero"]
    room["encounterName"] = enemy["name"]
    world._add_effect(room, "burst", enemy["x"], enemy["y"], enemy["color"], duration=1.8, text="ARMOR BROKEN · TRUE FORM")
    world._say(room, "system", "The Gauntlet", "The dragon armor breaks, awakening its larger true form! Its elemental attacks now change the arena — phase two begins.")


def tick(world, room, enemy, target, now, dt):
    old_x, old_y = enemy["x"], enemy["y"]
    if enemy.get("chargeUntil", 0) > now:
        destination=(old_x+enemy['chargeVx']*dt,old_y+enemy['chargeVy']*dt)
        block=terrain.shot_block(room,old_x,old_y,*destination,20)
        if block and enemy.get('rootUntil',0)<=now:
            t=max(0,block[0]-.02)
            terrain.move(room,enemy,old_x+(destination[0]-old_x)*t,old_y+(destination[1]-old_y)*t)
            baited=enemy.get('boss') and enemy['kind']=='minotaur'
            enemy.update(chargeUntil=now,recoverUntil=now+(3 if baited else 1.5),nextBossAttack=now+(4 if baited else 2.5),moving=False)
            if baited: enemy['vulnerableUntil']=now+3
            terrain.damage_cover(world,room,block[1],22)
            world._add_effect(room,'impact',enemy['x'],enemy['y'],enemy['color'],duration=.5,text='OPENING!' if baited else '')
            return
        terrain.move(room, enemy, old_x+enemy["chargeVx"]*dt, old_y+enemy["chargeVy"]*dt)
        dx, dy = enemy["x"]-old_x, enemy["y"]-old_y
        length = max(.001, dx*dx+dy*dy)
        for ally in world._combat_targets(room):
            t = max(0, min(1, ((ally["x"]-old_x)*dx+(ally["y"]-old_y)*dy)/length))
            distance = math.hypot(ally["x"]-old_x-t*dx, ally["y"]-old_y-t*dy)
            if ally["status"] == "alive" and ally["id"] not in enemy["chargeHits"] and distance <= 42:
                enemy["chargeHits"].append(ally["id"])
                world._damage_player(room, enemy, ally, math.ceil(enemy["damage"]*1.4))
        enemy["moving"] = True
        return
    if enemy.get("recoverUntil", 0) > now:
        enemy["moving"] = False
        return
    pending = enemy.get("pendingAttack")
    if pending:
        enemy["moving"] = False
        if now < pending["releaseAt"]:
            return
        enemy.pop("pendingAttack")
        kind, x, y = pending["kind"], pending["x"], pending["y"]
        if kind == "charge":
            dx, dy = x-enemy["x"], y-enemy["y"]
            distance = max(.001, math.hypot(dx, dy))
            speed = min(420, max(240, enemy["speed"]*3.2))
            enemy.update(chargeUntil=now+.7, chargeVx=dx/distance*speed,
                         chargeVy=dy/distance*speed, chargeHits=[])
        elif kind in ("rocks", "volley", "breath"):
            angle = math.atan2(y-enemy["y"], x-enemy["x"])
            count = 5 if kind == "breath" else 3
            for i in range(count):
                world._launch_projectile(room, side="enemy", owner_id=enemy["id"], target_id=pending["targetId"],
                    x=enemy["x"], y=enemy["y"], damage=math.ceil(enemy["damage"]*1.15),
                    color=enemy["color"], attack_class="Boss", speed=225 if kind == "rocks" else 245,
                    splash=65, radius=18 if kind == "rocks" else 15,
                    effect_kind="rock" if kind == "rocks" else "boss_orb", turn_rate=.35)
                shot = room["projectiles"][-1]
                direction = angle+(i-(count-1)/2)*.23
                shot.update(vx=math.cos(direction)*shot["speed"], vy=math.sin(direction)*shot["speed"])
        elif kind in SIGNATURES:
            release_signature(world,room,enemy,pending)
        enemy["recoverUntil"] = now+RECOVERY[kind]+(.7 if kind == "charge" else 0)
        enemy["nextBossAttack"] = enemy["recoverUntil"]+2.3/enemy.get("attackRate", 1)
        return
    if now >= enemy.get("nextBossAttack", 0):
        attacks = pattern(enemy)
        index = enemy.get("attackIndex", 0)
        kind = attacks[index % len(attacks)]
        enemy["attackIndex"] = index+1
        x, y = target["x"], target["y"]
        enemy["pendingAttack"] = {"kind": kind, "x": x, "y": y, "startedAt":now,
                                  "releaseAt": now+WINDUPS[kind], "targetId": target["id"]}
        if kind == "charge":
            distance = max(.001, math.hypot(x-enemy["x"],y-enemy["y"]))
            reach = min(420,max(240,enemy["speed"]*3.2))*.7
            enemy["pendingAttack"].update(endX=max(28,min(932,enemy["x"]+(x-enemy["x"])/distance*reach)),
                                          endY=max(30,min(510,enemy["y"]+(y-enemy["y"])/distance*reach)))
        enemy["facingX"], enemy["facingY"] = x-enemy["x"], y-enemy["y"]
        if kind in SIGNATURES:
            prepare_signature(world,room,enemy,enemy['pendingAttack'],now)
        if kind == "slam":
            area(room, enemy, enemy["x"], enemy["y"], now, radius=115, delay=WINDUPS[kind], power=1.4)
        elif kind in ("pool", "meteor"):
            targets = [p for p in world._active_players(room) if p["status"] == "alive"] if kind == "meteor" else [target]
            for ally in targets:
                area(room, enemy, ally["x"], ally["y"], now, radius=95 if kind == "meteor" else 80,
                     delay=WINDUPS[kind], duration=.25 if kind == "meteor" else 4,
                     power=1.6 if kind == "meteor" else .7, kind=kind)
        enemy["moving"] = False
        return
    # Pursuit decisions are made periodically, never mirrored from player input.
    if now >= enemy.get("bossMoveAt", 0):
        enemy.update(bossMoveAt=now+.75, bossGoal=[target["x"], target["y"]])
    goal = enemy.get("bossGoal", [target["x"], target["y"]])
    dx, dy = goal[0]-old_x, goal[1]-old_y
    distance = math.hypot(dx, dy)
    if distance > 65:
        step = min(distance-65, enemy["speed"]*dt)
        terrain.move(room, enemy, old_x+dx/distance*step, old_y+dy/distance*step, avoid=True)
    enemy["moving"] = math.hypot(enemy["x"]-old_x, enemy["y"]-old_y) > .1
