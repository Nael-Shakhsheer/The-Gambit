"""Objective encounters use the existing combat, damage and reward systems."""
import copy
import math
import random
import secrets
import time


def plan(room):
    reserved=set(room['bossStages']+room['miniBossStages']+room['puzzleStages']+room['townStages'])
    candidates=[s for s in range(4,room['totalStages']) if s not in reserved and s!=room.get('assassinationStage')]
    chosen=[]
    for stage in candidates:
        if (not chosen or stage-chosen[-1]>=3) and random.random()<.35: chosen.append(stage)
    if candidates and not chosen: chosen=[random.choice(candidates)]
    kinds=['rift','ward','charge']; random.shuffle(kinds)
    room['objectiveStages']={str(s):kinds[i%3] for i,s in enumerate(chosen)}


def prepare(world,room):
    kind=room.get('objectiveStages',{}).get(str(room['stage']))
    room['objective']=None
    if not kind or room['encounterType']!='normal': return
    now=time.monotonic(); size=len(world._active_players(room))
    balance_stage=world._effective_stage(room)
    template=next((e for e in room['enemies'] if e['kind']!='draco'),room['enemies'][0])
    room['stageWaves']=1
    room['objective']={'kind':kind,'stage':room['stage'],'spawnAt':now+5,'endsAt':now+32,
                       'template':copy.deepcopy(template),'cap':2+size*2,'spawnIndex':0}
    obj=room['objective']
    if kind=='rift':
        structure=copy.deepcopy(room['enemies'][0])
        hp=round(90*(1+.06*balance_stage)*(1+.65*(size-1)))
        structure.update(id=secrets.token_hex(4),kind='rift',name='Summoning rift',affinity='Arcane',
            x=480,y=180,hp=hp,maxHp=hp,speed=0,damage=0,combatRole='structure',
            structure=True,color='#b9a0da',moving=False)
        structure.pop('roleAttack',None); structure.pop('pendingAttack',None)
        structure['class']='Wizard'
        obj['structureId']=structure['id'];room['enemies'].append(structure)
        message='Destroy the summoning rift to stop reinforcements, then clear the field.'
    elif kind=='ward':
        hp=round(190*(1+.05*balance_stage)*(1+.3*(size-1)))
        obj['ward']={'id':'ward-'+secrets.token_hex(4),'name':'Hunter ward','kind':'ward','objectiveWard':True,
                     'x':480,'y':280,'hp':hp,'maxHp':hp,'status':'alive','damageTaken':0}
        if len(room['enemies'])<2:
            extra=copy.deepcopy(room['enemies'][0]);extra['id']=secrets.token_hex(4);room['enemies'].append(extra)
        for i,e in enumerate(room['enemies']):
            e['x'],e['y']=((170,32),(928,190),(790,508),(32,350))[i%4]
        message='Protect the ward for 32 seconds. Enemies approach from different sides; intercept them.'
    else:
        for i,e in enumerate(room['enemies']):
            if i==0:
                e.update(kind='minotaur',name='Charging sentinel',combatRole='charger',
                         speed=e['speed']*1.1,hp=math.ceil(e['maxHp']*1.3),maxHp=math.ceil(e['maxHp']*1.3))
                e['class']='Knight'
        # These few rocks are tactical: a blocked charge creates a longer opening.
        room['environment']['obstacles']=[{'id':secrets.token_hex(4),'kind':'rock','x':x,'y':y,
            'radius':24,'hp':60,'maxHp':60} for x,y in random.sample([(270,215),(690,215),(270,350),(690,350)],2)]
        room['environment']['zones']=[]
        message='Bait the sentinel into rocks. A blocked charge leaves it exposed.'
    obj['instruction']=message
    world._say(room,'system','The Gauntlet',message)


def ward(room):
    w=(room.get('objective') or {}).get('ward')
    return [w] if w and w['status']=='alive' and room['phase']=='combat' else []


def can_complete(room,now):
    obj=room.get('objective') or {}
    return obj.get('kind')!='ward' or now>=obj['endsAt']


def hurt_ward(world,room,target,amount):
    if target['status']!='alive': return
    target['hp']=max(0,target['hp']-max(1,round(amount)));target['damageTaken']+=1
    if target['hp']: return
    target['status']='fallen'
    world._finish_stage_stats(room,'defeat')
    room.update(phase='defeat',enemies=[],projectiles=[],hazards=[],runes=math.floor(room['runes']*.6))
    world._say(room,'system','The Gauntlet','The ward was destroyed. The party loses 40% of its Runes; return to your inn checkpoint or start a new run.')


def tick(world,room,now):
    obj=room.get('objective')
    if not obj or room['phase']!='combat': return
    kind=obj['kind']
    spawning=kind=='rift' and any(e['id']==obj['structureId'] for e in room['enemies']) or kind=='ward' and now<obj['endsAt']
    if spawning and now>=obj['spawnAt']:
        obj['spawnAt']=now+5
        if len(room['enemies'])<obj['cap']:
            e=copy.deepcopy(obj['template']);e['id']=secrets.token_hex(4)
            e.update(hp=e['maxHp'],damageTaken=0,lastAiTick=now,lastAttack=now,roleReadyAt=now+1,
                     moveDecisionAt=0,stunUntil=0,bleedUntil=0)
            for key in ('roleAttack','pendingAttack','roleChargeUntil','roleRecoverUntil'): e.pop(key,None)
            edge=obj['spawnIndex']%4;obj['spawnIndex']+=1
            e['x'],e['y']=((170,32),(928,190),(790,508),(32,350))[edge]
            room['enemies'].append(e)
            world._add_effect(room,'aura',e['x'],e['y'],'#cab9e1',duration=.5)
    if not room['enemies'] and can_complete(room,now): world._complete_encounter(room)


def view(room,now):
    obj=room.get('objective')
    if not obj or room['phase']!='combat': return None
    return {'kind':obj['kind'],'instruction':obj['instruction'],'remaining':max(0,math.ceil(obj['endsAt']-now)),
            'ward':copy.deepcopy(obj.get('ward')), 'structureId':obj.get('structureId')}
