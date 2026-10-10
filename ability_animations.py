"""Public, transient cast choreography. Never delays or modifies combat rules."""
import secrets
import time


def record(room, player, ability, origin, target, recipient_ids):
    now = time.monotonic()
    attack_type = ability['attackType']
    duration = {'light': .46, 'special': .85, 'ultimate': 1.25}[attack_type]
    if ability['kind'] == 'summon':
        duration = 1.1 if attack_type == 'special' else 1.5
    cast = dict(id=secrets.token_hex(6), abilityId=ability['id'], name=ability['name'],
                attackType=attack_type, kind=ability['kind'], ownerId=player['id'],
                heroClass=player['class'], stage=room['stage'], duration=duration, startedAt=now,
                facingX=player.get('facingX', 0), facingY=player.get('facingY', 1),
                recipientIds=recipient_ids)
    # Holding Light must not erase the pose of a longer Special/Ultimate.
    previous = player.get('abilityAnimation') or {}
    priority = {'light': 1, 'special': 2, 'ultimate': 3}
    active = (previous.get('stage') == room['stage'] and previous.get('heroClass') == player['class']
              and now < previous.get('startedAt', 0) + previous.get('duration', 0))
    if not active or priority[attack_type] >= priority.get(previous.get('attackType'), 0):
        player['abilityAnimation'] = cast
    room['effects'].append(dict(cast, type='ability_cast', x=origin[0], y=origin[1],
        targetX=target[0], targetY=target[1], color='', until=time.time()+duration,
        text='', **{'class': player['class']}))
    room['effects'] = room['effects'][-80:]


def view(player, now, stage):
    cast = player.get('abilityAnimation')
    if not cast or cast.get('stage') != stage or cast.get('heroClass') != player.get('class') or player.get('status') != 'alive':
        return None
    elapsed = now - cast['startedAt']
    if not 0 <= elapsed < cast['duration']:
        return None
    return dict(cast, elapsed=elapsed, remaining=cast['duration']-elapsed)
