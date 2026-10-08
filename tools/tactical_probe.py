"""Stationary 12s light-attack probe; measures damage and control, not human balance."""
import copy
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game import ABILITY_SETS, GameWorld


def probe(hero, ability, count):
    now=[1000.]
    with patch('game.time.monotonic',side_effect=lambda:now[0]):
        world=GameWorld();code,pid=world.create_room('Probe')
        world.action(code,pid,{'action':'class','class':hero})
        choices=[ability]+[next(a[0] for a in ABILITY_SETS[hero] if a[7]==category) for category in ('special','ultimate')]
        world.action(code,pid,{'action':'loadout','abilities':choices});world.action(code,pid,{'action':'start'})
        room=world.rooms[code];player=room['players'][pid];player.update(x=100,y=200)
        room['environment']=None
        original=copy.deepcopy(room['enemies'][0]);room['enemies']=[]
        for index,(x,y) in enumerate(((300,200),(335,220),(345,180))[:count]):
            enemy=copy.deepcopy(original);enemy.update(id=str(index),x=x,y=y,hp=100000,maxHp=100000)
            room['enemies'].append(enemy)
        control=0
        for _ in range(240):
            world._attack(room,player);now[0]+=.05;world._tick_projectiles(room,now[0])
            control+=.05*sum(max(e.get('rootUntil',0),e.get('stunUntil',0))>now[0] for e in room['enemies'])
        damage=sum(100000-e['hp'] for e in room['enemies'])
        return dict(hero=hero,ability=ability,targets=count,damage=damage,dps=round(damage/12,2),controlEnemySeconds=round(control,2))


if __name__=='__main__':
    results=[probe(hero,a[0],count) for hero in ('Druid','Wizard','Cleric') for a in ABILITY_SETS[hero] if a[7]=='light' for count in (1,3)]
    root=Path(__file__).resolve().parents[1]/'reports';root.mkdir(exist_ok=True)
    (root/'tactical-light-probe.json').write_text(json.dumps({'method':'12s stationary targets, no equipment, no enemy attacks; remaining in-flight damage excluded. Control counts enemy-seconds. Not human balance evidence.','results':results},indent=2),encoding='utf-8')
    rows=['# Tactical light-attack probe','', 'Stationary 12-second scenarios with one target or a tight three-enemy cluster. No equipment or enemy AI. This checks tactical identities, not human encounter balance. Control is summed across affected enemies.','', '| Hero | Ability | Targets | DPS | Control enemy-seconds |','|---|---|---:|---:|---:|']
    for r in results:rows.append(f"| {r['hero']} | {r['ability']} | {r['targets']} | {r['dps']} | {r['controlEnemySeconds']} |")
    (root/'TACTICAL_LIGHT_PROBE.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(json.dumps(results))
