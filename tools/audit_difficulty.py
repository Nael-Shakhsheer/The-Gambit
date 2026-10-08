"""Audit generated campaign curves and anonymize existing server observations.

This is a schedule/stat audit, not human playtesting. Does not write saves or
connect to the live server. Prior stage logs may contain developer test runs.
"""
import copy
import json
from pathlib import Path
import random
import statistics
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game import ABILITY_SETS, GameWorld


def main():
    curves=[]
    for length in (9,20,25,30):
        for mode in ('easy','medium','hard'):
            for size in (1,2,4):
                for route in (-4,0,6):
                    random.seed(410+length+size)
                    world=GameWorld();code,pid=world.create_room('Audit')
                    heroes=['Knight','Archer','Healer','Druid'][:size]
                    ids=[pid]+[world.join_room(code,'Audit')[1] for _ in heroes[1:]]
                    for who,hero in zip(ids,heroes):
                        world.action(code,who,{'action':'class','class':hero})
                        world.action(code,who,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS[hero][::2]]})
                    world.action(code,pid,{'action':'runOptions','difficulty':mode,'stages':length})
                    world.action(code,pid,{'action':'start'});room=world.rooms[code]
                    samples=[]
                    for stage in range(1,length+1):
                        visits=[s for s in room['townStages'] if s<stage]
                        room.update(stage=stage,stageWave=1,stageWaves=1,townsVisited=len(visits),townPressureStages=visits,
                                    routePressure=route,environment=None,phase='combat',assassinationUsed=True)
                        room['terrainSeed']=1000
                        world._spawn_wave(room)
                        samples.append({'stage':stage,'encounter':room['encounterType'],'objective':(room.get('objective') or {}).get('kind'),
                            'towns':len(visits),'townPressure':world._town_pressure(room),'enemies':len(room['enemies']),
                            'dracos':sum(e['kind']=='draco' for e in room['enemies']),
                            'totalHP':sum(e['maxHp'] for e in room['enemies']),
                            'maxHit':max(e['damage'] for e in room['enemies']),
                            'maxSpeed':round(max(e['speed'] for e in room['enemies']),1)})
                    curves.append({'mode':mode,'length':length,'partySize':size,'routePressure':route,'townStages':room['townStages'],'stages':samples})
    root=Path(__file__).resolve().parents[1];historical=[]
    source=root/'data/balance.jsonl'
    if source.exists():
        for line in source.read_text(encoding='utf-8').splitlines():
            try: historical.append(json.loads(line))
            except json.JSONDecodeError: pass
    observed=[]
    for stage in sorted({r['stage'] for r in historical}):
        rows=[r for r in historical if r['stage']==stage]
        observed.append({'stage':stage,'observations':len(rows),'cleared':sum(r['outcome']=='cleared' for r in rows),
            'medianSeconds':round(statistics.median(r['seconds'] for r in rows),2),
            'medianHeroDamageTaken':statistics.median(sum(p.get('heroDamageTaken',0) for p in r['players']) for r in rows)})
    result={'source':'generated campaign schedules/stat curves; existing server logs with unverified player/test provenance',
            'curves':curves,'historicalStageObservations':observed,'historicalRows':len(historical),
            'rowsWithDifficultyContext':sum('difficulty' in r for r in historical)}
    out=root/'reports';out.mkdir(exist_ok=True)
    (out/'difficulty-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    spikes=[]
    for c in curves:
        for a,b in zip(c['stages'],c['stages'][1:]):
            if a['encounter']==b['encounter']=='normal' and not a['objective'] and not b['objective']:
                spikes.append((b['totalHP']/max(1,a['totalHP']),c,b))
    worst=sorted(spikes,key=lambda x:x[0],reverse=True)[:5]
    lines=['# Difficulty audit — 2026-10-07','',
        f'Generated {len(curves)} complete schedule/stat curves: all three challenges, the three normal lengths plus Tester (9 stages), parties of 1/2/4 and route pressure -4/0/6. These sample spawned waves and boss/elite/objective compositions; they are not played campaign clears.', '',
        f'The local server has {len(historical)} recorded stage observations spanning stages '+str(min((r["stage"] for r in historical),default=0))+'–'+str(max((r['stage'] for r in historical),default=0))+'. Their player/test provenance is unverified. '+str(sum('difficulty' in r for r in historical))+' rows record challenge/town/route context, so older logs cannot establish which stacking factor caused a spike. New telemetry captures those fields. No names or room identities are exported.','',
        'Town pressure retains its eventual +25% HP / +20% damage per visit, but arrives in two steps: 50% on the first combat stage after town, 100% on the second. Legacy saves without arrival history retain their existing accumulated pressure. This reduces the immediate first-visit increase to +12.5% HP / +10% damage, before the independent stage/party/mode/elite/route factors.','',
        'Challenge and campaign length are independent. A Hard 20-stage run and an Easy 30-stage run are valid; event schedules fit the selected length. Length affects the normalized stage ramp and boss spacing, so it is not a cosmetic timer.','',
        'Tester maps physical stages 1–9 to combat progression 1/4/7/10/13/16/19/22/25. This accelerates enemy stats, ordinary group size, waves, terrain damage and objective HP. Its bosses are at 3/6/9, miniboss at 2, town at 4, puzzle at 5, objective at 8; ordinary waves guarantee a Draco from Tester stage 7. Normal campaigns still introduce Dracos at stage 17. Tester curves are labelled length 9 and should not be pooled with ordinary runs.','',
        'Largest ordinary adjacent-wave HP ratios in the sampled curves (random foe count/type also changes these):','',
        '| Challenge | Length | Party | Route pressure | Stage | Dracos | Total enemy HP ratio |','| --- | --- | --- | --- | --- | --- | --- |']
    for ratio,c,b in worst:lines.append(f"| {c['mode']} | {c['length']} | {c['partySize']} | {c['routePressure']} | {b['stage']} | {b['dracos']} | {ratio:.2f}× |")
    lines+=['','Interpretation: total wave HP is workload, not a single-enemy strength multiplier. Random group size and enemy composition create larger workload changes than the smoothed town factor. Stage 17 also increases ordinary group size and introduces durable Dracos; their counts are captured above and in the JSON. Boss/elite transitions are intentionally excluded from that table; their raw samples remain in the JSON. Do not tune every spike from aggregate HP alone.','',
        '## Required human checks','',
        '- Play matched solo and two-human runs with the same challenge/length; compare the stages just before and after each town, gear/training purchased, knockdowns, clear time and whether losses felt readable.',
        '- Test on a physical phone: hold movement plus attack, change direction, dash away from warnings, tap a preferred enemy, clear it, revive and release, equip/swap utilities, and use landscape dialogue.',
        '- Use two real devices for shared spending and reconnect: buy simultaneously with limited Runes, disconnect at an exit, rejoin during combat, and check the missing player neither blocks votes nor creates duplicate purchases.',
        '- At an inn bed, verify the checkpoint message. Leave/rejoin with the server running, then deliberately restart after a saved town and confirm only bed progress returns.',
        '', 'Physical-phone comfort and human multiplayer coordination have not been established by this audit. Automated regression and protocol checks are separate from those playtests.']
    (out/'DIFFICULTY_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Audited {len(curves)} campaign curves and anonymized {len(historical)} historical observations.')


if __name__=='__main__':main()
