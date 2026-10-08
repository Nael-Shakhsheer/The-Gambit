import copy
import math
import unittest
from unittest.mock import patch

import combat_encounters as objectives
import combat_environment as terrain
import enemy_roles
import telemetry
from game import GameWorld, ABILITY_SETS


class DeliberateCombatTests(unittest.TestCase):
    def setUp(self):
        self.now=1000.
        timer=patch('game.time.monotonic',side_effect=lambda:self.now);timer.start();self.addCleanup(timer.stop)
        self.world=GameWorld();self.code,self.pid=self.world.create_room('Hunter')
        self.world.action(self.code,self.pid,{'action':'class','class':'Knight'})
        self.world.action(self.code,self.pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        self.world.action(self.code,self.pid,{'action':'start'})
        self.room=self.world.rooms[self.code];self.p=self.room['players'][self.pid]
        self.room.update(stage=4,objectiveStages={},bossStages=[8,16,25],miniBossStages=[],enemies=[])
        self.world._spawn_regular_wave(self.room);self.world._tune_enemy_group(self.room);enemy_roles.assign(self.room)
        self.room['environment']={'stage':4,'region':'woodland','obstacles':[],'zones':[]}

    def encounter(self,kind):
        self.room['objectiveStages']={'4':kind};objectives.prepare(self.world,self.room)
        return self.room['objective']

    def test_rift_spawns_until_destroyed_then_finishes_only_when_field_is_clear(self):
        obj=self.encounter('rift');structure=next(e for e in self.room['enemies'] if e.get('structure'))
        before=len(self.room['enemies']);self.now+=5;objectives.tick(self.world,self.room,self.now)
        self.assertEqual(len(self.room['enemies']),before+1)
        self.world._damage_enemy(self.room,self.p,structure,structure['hp'])
        remaining=list(self.room['enemies']);self.now+=10;objectives.tick(self.world,self.room,self.now)
        self.assertEqual(self.room['enemies'],remaining);self.assertEqual(self.room['phase'],'combat')
        for e in remaining:self.world._damage_enemy(self.room,self.p,e,e['hp'])
        self.assertNotEqual(self.room['phase'],'combat');self.assertEqual(self.room['stageWaves'],1)

    def test_structure_stays_stationary(self):
        self.encounter('rift');e=next(e for e in self.room['enemies'] if e.get('structure'))
        before=(e['x'],e['y']);self.world._tick_enemy(self.room,e,self.p,self.now)
        self.assertEqual((e['x'],e['y']),before)

    def test_ward_cannot_be_cleared_early_and_requires_surviving(self):
        obj=self.encounter('ward')
        for e in list(self.room['enemies']):self.world._damage_enemy(self.room,self.p,e,e['hp'])
        self.assertEqual(self.room['phase'],'combat')
        self.now+=5;objectives.tick(self.world,self.room,self.now)
        self.assertTrue(self.room['enemies'])
        self.now=obj['endsAt']
        for e in list(self.room['enemies']):self.world._damage_enemy(self.room,self.p,e,e['hp'])
        self.assertNotEqual(self.room['phase'],'combat')

    def test_ward_damage_uses_objective_hp_and_failure_not_hero_deaths(self):
        obj=self.encounter('ward');ward=obj['ward'];hp=self.p['hp']
        self.world._damage_player(self.room,self.room['enemies'][0],ward,20)
        self.assertEqual(self.p['hp'],hp);self.assertEqual(ward['maxHp']-ward['hp'],20)
        self.assertEqual(telemetry.overall(self.room)[0]['damageTaken'],0)
        self.world._damage_player(self.room,self.room['enemies'][0],ward,10000)
        self.assertEqual(self.room['phase'],'defeat');self.assertEqual(telemetry.overall(self.room)[0]['deaths'],0)

    def test_ward_is_a_valid_projectile_and_melee_target(self):
        obj=self.encounter('ward');w=obj['ward'];self.p.update(x=900,y=480)
        e=self.room['enemies'][0];e.update(x=w['x']-60,y=w['y'])
        self.world._launch_projectile(self.room,side='enemy',owner_id=e['id'],target_id=w['id'],x=e['x'],y=e['y'],damage=10,color='#fff',attack_class='Archer',speed=1000,turn_rate=0)
        self.now+=.08;self.world._tick_projectiles(self.room,self.now)
        self.assertEqual(w['maxHp']-w['hp'],10)
        self.assertIn(w,self.world._combat_targets(self.room))

    def test_charger_colliding_with_cover_creates_two_second_opening(self):
        self.encounter('charge');e=self.room['enemies'][0]
        self.room['environment']['obstacles']=[{'id':'rock','x':200,'y':200,'radius':24,'hp':60,'maxHp':60}]
        e.update(x=164,y=200,roleChargeUntil=self.now+1,roleVx=270,roleVy=0,roleHits=[])
        enemy_roles.tick(self.world,self.room,e,self.p,self.now,.05)
        self.assertEqual(e['roleChargeUntil'],self.now);self.assertEqual(e['roleRecoverUntil'],self.now+2)
        before=(e['x'],e['y']);enemy_roles.tick(self.world,self.room,e,self.p,self.now+1,.05)
        self.assertEqual((e['x'],e['y']),before)

    def test_target_preference_chooses_farther_valid_enemy_and_falls_back_when_blocked(self):
        self.p.update(x=100,y=200);a=self.room['enemies'][0];b=copy.deepcopy(a);b['id']='preferred'
        a.update(x=130,y=200,hp=1000,maxHp=1000);b.update(x=190,y=200,hp=1000,maxHp=1000)
        self.room['enemies']=[a,b]
        self.world.action(self.code,self.pid,{'action':'target','targetId':b['id']})
        self.world._cast_ability(self.room,self.p,0)
        self.assertEqual(a['hp'],1000);self.assertLess(b['hp'],1000)
        self.now+=1;b.update(x=400,y=200);self.world._cast_ability(self.room,self.p,0)
        self.assertLess(a['hp'],1000)

    def test_stale_input_cannot_overwrite_release_and_revive_can_be_cancelled(self):
        self.world.action(self.code,self.pid,{'action':'input','x':0,'y':0,'sequence':11})
        self.world.action(self.code,self.pid,{'action':'input','x':1,'y':0,'sequence':10})
        self.assertEqual(self.p['dx'],0);self.assertEqual(self.world.state(self.code,self.pid)['movement']['sequence'],11)
        self.p['reviving']='ally';self.world.action(self.code,self.pid,{'action':'stopRevive'})
        self.assertIsNone(self.p['reviving'])

    def test_run_length_and_challenge_are_independent_and_persist_across_edits(self):
        code,pid=self.world.create_room('Next')
        self.world.action(code,pid,{'action':'runOptions','difficulty':'hard','stages':20})
        self.assertEqual(self.world.rooms[code]['totalStages'],20)
        self.world.action(code,pid,{'action':'runOptions','difficulty':'easy'})
        self.assertEqual(self.world.rooms[code]['totalStages'],20)
        self.world.action(code,pid,{'action':'class','class':'Knight'})
        self.world.action(code,pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        self.world.action(code,pid,{'action':'start'})
        self.assertEqual(self.world.rooms[code]['bossStages'][-1],20)

    def test_town_pressure_arrives_in_two_steps_and_legacy_visits_stay_valid(self):
        self.room.update(townsVisited=2,townPressureStages=[5,12])
        for stage,value in ((5,0),(6,.5),(7,1),(12,1),(13,1.5),(14,2)):
            self.room['stage']=stage;self.assertEqual(self.world._town_pressure(self.room),value)
        self.room['townPressureStages']=[];self.assertEqual(self.world._town_pressure(self.room),2)

    def test_sparse_features_scatter_without_blocking_entry_or_exit(self):
        layouts=set()
        for region in ('woodland','ruins','cavern','frost'):
            for stage in range(1,25):
                room={'stage':stage,'region':region,'terrainSeed':18};terrain.prepare(room)
                env=room['environment'];self.assertIn(len(env['obstacles']),(1,2));self.assertEqual(len(env['zones']),1)
                layouts.add(tuple((o['x'],o['y']) for o in env['obstacles']))
                for o in env['obstacles']:
                    self.assertGreater(abs(o['x']-480),100)
                    for z in env['zones']:self.assertGreaterEqual(math.hypot(o['x']-z['x'],o['y']-z['y']),o['radius']+z['radius']+70)
                if len(env['obstacles'])==2:self.assertGreaterEqual(math.hypot(env['obstacles'][0]['x']-env['obstacles'][1]['x'],env['obstacles'][0]['y']-env['obstacles'][1]['y']),240)
        self.assertGreater(len(layouts),20)

    def test_pause_shifts_objective_clocks(self):
        obj=self.encounter('ward');before=(obj['spawnAt'],obj['endsAt'])
        self.world._shift_clocks(self.room,20)
        self.assertEqual((obj['spawnAt'],obj['endsAt']),(before[0]+20,before[1]+20))
