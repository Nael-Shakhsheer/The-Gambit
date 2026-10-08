"""Ability identities and equipment tradeoffs shared by combat entry points."""
import math

ABILITY_DETAILS = {
    'briar_burst': {'splashRadius': 65, 'rootDuration': .8},
    'arc_burst': {'chainTargets': 2, 'chainRange': 110, 'chainDecay': .65},
    'radiant_flask': {'splashRadius': 75},
    'sanctified_throw': {'projectileSpeed': 340},
    'rain_of_arrows': {'castRange': 380, 'blastRadius': 110, 'impactDelay': .65},
}

BUILD_ITEMS = {
    'arcane_conductor': dict(name='Arcane Conductor', rarity='Rare', price=34, sell=17,
        kind='weapon', slot='tool', damage=3, color='#b9a4ff', effect='conductor',
        effectLabel='Projectile chain / -20% projectile damage',
        description='+3 damage. Direct projectiles deal 20% less damage, then jump to one extra enemy within 110px for 50% damage. Jumps do damage only. Summons are unaffected. Effect does not stack.'),
    'rescuers_cuirass': dict(name="Rescuer's Cuirass", rarity='Uncommon', price=26, sell=13,
        kind='armor', slot='tool', armor=1, color='#92d9d1', effect='rescuer',
        effectLabel='Rescue protection / only 1 armor',
        description='+1 armor. Take 60% less damage during the first 2s of a manual rescue. Protection recharges in 8s and ends when the rescue stops. Less ordinary defense than other armor. Effect does not stack.'),
    'summoners_staff': dict(name="Summoner's Staff", rarity='Rare', price=36, sell=18,
        kind='weapon', slot='tool', damage=2, color='#77bf82', effect='summoner',
        effectLabel='Druid summon HP +50% / direct damage -25%',
        description='+2 damage. Druid summons have 50% more HP, but the Druid deals 25% less direct attack damage. Changes to summon HP preserve their health percentage when swapping gear. Effect does not stack.'),
    'pursuit_blade': dict(name='Pursuit Blade', rarity='Rare', price=32, sell=16,
        kind='weapon', slot='tool', damage=2, color='#df9b65', effect='pursuit',
        effectLabel='Follow-up after dash +60% / direct damage -15%',
        description='+2 damage. Direct attacks deal 15% less damage. Your next damaging ability within 2s after Dash, Blink or Shadowstep deals 60% more damage. One follow-up per dash; summons are unaffected. Effect does not stack.'),
}

def effects(player):
    return {item.get('effect', BUILD_ITEMS.get(item.get('key'), {}).get('effect'))
            for item in player.get('toolSlots', []) if item} - {None}

def direct_factor(player, now, *, consume=False):
    active = effects(player)
    factor = .75 if 'summoner' in active and player.get('class') == 'Druid' else 1
    if 'pursuit' in active:
        factor *= .85
        if player.get('pursuitUntil', 0) > now and not player.get('pursuitSpent'):
            factor *= 1.6
            if consume: player['pursuitSpent'] = True
    return factor

def dashed(player, now, distance):
    if distance >= 12 and 'pursuit' in effects(player):
        player.update(pursuitUntil=now+2, pursuitSpent=False)

def summon_health(player, template):
    factor = 1.5 if player.get('class') == 'Druid' and 'summoner' in effects(player) else 1
    return math.ceil(template['hp']*factor)

def refresh_summon_health(player, summon, template):
    hp = summon_health(player, template)
    if summon['maxHp'] != hp:
        fraction = summon.setdefault('gearHealthFraction', summon['hp']/summon['maxHp'])
        summon['hp'] = max(1, round(fraction*hp))
        summon['maxHp'] = hp

def decorate_projectile(player, shot):
    if shot.get('summonId'): return
    detail = ABILITY_DETAILS.get(shot.get('abilityId'), {})
    shot.update(chainTargets=detail.get('chainTargets', 0),
                chainRange=detail.get('chainRange', 110), chainDecay=detail.get('chainDecay', .5),
                rootDuration=detail.get('rootDuration', 0))
    if 'conductor' in effects(player):
        shot['damage'] = max(1, round(shot['damage']*.8))
        shot['conductorJump'] = True

def root(enemy, now, duration):
    if enemy.get('structure') or enemy.get('rootResistUntil', 0) > now: return
    duration = min(duration, .25 if enemy.get('boss') else .5 if enemy.get('miniBoss') else duration)
    enemy.update(rootUntil=now+duration, rootResistUntil=now+1.8, moving=False)

def bleed(player, enemy, now, damage):
    enemy.update(bleedOwner=player['id'], bleedUntil=now+5,
                 bleedDamage=max(1, round(damage)), lastBleedTick=now,
                 bleedBoostSource=player.get('damageBoostSource'),
                 bleedBoostFactor=player['damageBoost'] if player.get('damageBoostUntil', 0)>now else 1)

def rescue_factor(room, rescuer, now):
    target = room['players'].get(rescuer.get('reviving'))
    if ('rescuer' in effects(rescuer) and rescuer.get('rescueGuardUntil', 0)>now and
            rescuer.get('connected', True) and target and target['status']=='downed' and
            math.hypot(target['x']-rescuer['x'], target['y']-rescuer['y']) <= 62):
        return .4
    return 1
