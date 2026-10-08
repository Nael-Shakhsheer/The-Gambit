import copy
import math
import unittest
from unittest.mock import patch

import boss_ai
import combat_environment as terrain
import tactical_rules as tactical
from game import ABILITY_SETS, GameWorld


class TacticalUpdateTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.
        timer=patch('game.time.monotonic',side_effect=lambda:self.now)
        timer.start(); self.addCleanup(timer.stop)
        self.world=GameWorld(); self.code,self.pid=self.world.create_room('Hunter')
        self.world.action(self.code,self.pid,{'action':'class','class':'Knight'})
        self.world.action(self.code,self.pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        self.world.action(self.code,self.pid,{'action':'start'})
        self.room=self.world.rooms[self.code]; self.p=self.room['players'][self.pid]
        self.p.update(x=100,y=200,mana=1000,hp=1000,maxHp=1000)
        self.template=copy.deepcopy(self.room['enemies'][0])
        self.room['environment']={'stage':1,'region':'woodland','obstacles':[],'zones':[]}
        self.foes()

    def hero(self, hero):
        self.p.update(**{'class':hero},abilities=[a[0] for a in ABILITY_SETS[hero][::2]],abilityCooldowns={})

    def foes(self, positions=((300,200),(335,220),(345,180))):
        self.room.update(phase='combat',projectiles=[],hazards=[])
        self.room['enemies']=[]
        for index,(x,y) in enumerate(positions):
            enemy=copy.deepcopy(self.template)
            enemy.update(id='enemy'+str(index),x=x,y=y,hp=10000,maxHp=10000,stunUntil=0,
                         stunResistUntil=0,lastAttack=self.now,bleedUntil=0,boss=False)
            self.room['enemies'].append(enemy)
        return self.room['enemies']

    def cast(self, ability_id):
        entry=next(a for a in ABILITY_SETS[self.p['class']] if a[0]==ability_id)
        index={'light':0,'special':1,'ultimate':2}[entry[7]]
        self.p['abilities'][index]=ability_id
        self.p['abilityCooldowns'].pop(ability_id,None)
        self.world._cast_ability(self.room,self.p,index)

    def impact(self):
        for _ in range(80):
            if not self.room['projectiles']: break
            self.now+=.05; self.world._tick_projectiles(self.room,self.now)

    def gear(self, key):
        item=self.world._make_item(key);self.p['toolSlots']=[item,None];return item

    def boss(self, kind, affinity='Nature', phase=1):
        enemy=self.foes(((480,250),))[0]
        enemy.update(kind=kind,boss=True,bossPhase=phase,affinity=affinity,damage=10,speed=80,
                     nextBossAttack=self.now,attackIndex=0,recoverUntil=0)
        return enemy

    def ally(self):
        phase=self.room['phase'];self.room['phase']='lobby'
        _,pid=self.world.join_room(self.code,'Ally')
        self.room['phase']=phase
        ally=self.room['players'][pid];ally.update(x=120,y=200,hp=1000,maxHp=1000)
        return ally

    def test_briar_controls_a_cluster_while_thornshot_hits_one_harder(self):
        self.hero('Druid'); targets=self.foes();self.cast('briar_burst');self.impact()
        spread=[10000-e['hp'] for e in targets]
        self.assertTrue(all(d>0 for d in spread));self.assertTrue(all(e['rootUntil']>self.now for e in targets))
        targets=self.foes();self.cast('thornshot');self.impact()
        self.assertGreater(10000-targets[0]['hp'],spread[0]);self.assertEqual(targets[1]['hp'],10000)
        self.assertGreater(sum(spread),10000-targets[0]['hp'])

    def test_roots_stop_movement_without_stunning_or_repeated_locking(self):
        enemy=self.room['enemies'][0]; tactical.root(enemy,self.now,.8)
        before=enemy['x'],enemy['y']; terrain.move(self.room,enemy,enemy['x']+30,enemy['y'])
        self.assertEqual((enemy['x'],enemy['y']),before);self.assertEqual(enemy['stunUntil'],0)
        first=enemy['rootUntil'];tactical.root(enemy,self.now+.5,.8);self.assertEqual(enemy['rootUntil'],first)
        enemy['boss']=True;tactical.root(enemy,self.now+2,.8);self.assertEqual(enemy['rootUntil'],self.now+2.25)

    def test_arc_chains_to_two_unique_enemies_and_frost_controls_only_one(self):
        self.hero('Wizard');targets=self.foes(((300,200),(345,200),(390,200),(430,200)))
        self.cast('arc_burst');self.impact();losses=[10000-e['hp'] for e in targets]
        self.assertGreater(losses[0],losses[1]);self.assertGreater(losses[1],losses[2]);self.assertEqual(losses[3],0)
        targets=self.foes();self.cast('frost_lance');self.impact()
        self.assertGreater(targets[0]['stunUntil'],self.now);self.assertEqual(targets[1]['hp'],10000)
        self.assertLess(10000-targets[0]['hp'],losses[0])

    def test_chain_does_not_cross_cover(self):
        self.hero('Wizard');targets=self.foes(((300,200),(380,200)))
        self.room['environment']['obstacles']=[dict(id='rock',x=340,y=200,radius=20,hp=90,maxHp=90)]
        self.cast('arc_burst');self.impact()
        self.assertLess(targets[0]['hp'],10000);self.assertEqual(targets[1]['hp'],10000)

    def test_flask_splashes_while_sanctified_throw_has_better_single_damage(self):
        self.hero('Cleric');targets=self.foes();self.cast('radiant_flask');self.impact()
        losses=[10000-e['hp'] for e in targets];self.assertTrue(all(d>0 for d in losses))
        targets=self.foes();self.cast('sanctified_throw');self.assertEqual(self.room['projectiles'][0]['speed'],340)
        self.impact();self.assertGreater(10000-targets[0]['hp'],losses[0]);self.assertEqual(targets[1]['hp'],10000)
        self.assertGreater(sum(losses),10000-targets[0]['hp'])

    def test_rain_targets_selected_cluster_locks_position_and_has_no_friendly_fire(self):
        self.hero('Archer');targets=self.foes(((150,200),(400,200),(440,200)))
        self.p['preferredTarget']=targets[1]['id'];self.cast('rain_of_arrows')
        zone=self.room['hazards'][0];self.assertEqual((zone['x'],zone['radius']),(400,110))
        hp=self.p['hp'];boss_ai.tick_areas(self.world,self.room,self.now+.64)
        self.assertEqual(targets[1]['hp'],10000)
        targets[1]['x']=700;self.now+=.66;boss_ai.tick_areas(self.world,self.room,self.now)
        self.assertEqual(targets[1]['hp'],10000);self.assertLess(targets[2]['hp'],10000)
        self.assertEqual(targets[0]['hp'],10000);self.assertEqual(self.p['hp'],hp)

    def test_rain_out_of_range_does_not_spend_mana_or_cooldown(self):
        self.hero('Archer');self.foes(((700,200),));before=self.p['mana']
        with self.assertRaisesRegex(ValueError,'range'):self.cast('rain_of_arrows')
        self.assertEqual(self.p['mana'],before);self.assertNotIn('rain_of_arrows',self.p['abilityCooldowns'])

    def test_death_bloom_applies_real_bleed_to_each_hit_with_owner_credit(self):
        self.hero('Rogue');targets=self.foes();self.cast('death_bloom')
        hp=[e['hp'] for e in targets]
        self.assertTrue(all(e['bleedOwner']==self.pid and e['bleedUntil']==self.now+5 for e in targets))
        self.now+=1.05;self.world.tick()
        self.assertTrue(all(e['hp']<before for e,before in zip(targets,hp)))
        self.assertGreater(self.room['runStats'][self.pid]['damageDealt'],sum(10000-before for before in hp))

    def test_conductor_reduces_primary_hit_and_adds_one_damage_only_jump(self):
        self.hero('Wizard');targets=self.foes();self.gear('arcane_conductor');self.cast('frost_lance')
        damage=self.room['projectiles'][0]['damage'];self.impact()
        self.assertEqual(10000-targets[1]['hp'],round(damage*.5));self.assertEqual(targets[2]['hp'],10000)
        self.assertEqual(targets[1]['stunUntil'],0)

    def test_conductor_extends_arc_once_without_rehitting_or_recursive_chains(self):
        self.hero('Wizard');targets=self.foes(((300,200),(345,200),(390,200),(430,200),(470,200)))
        self.gear('arcane_conductor');self.cast('arc_burst');self.impact()
        self.assertTrue(all(e['hp']<10000 for e in targets[:4]));self.assertEqual(targets[4]['hp'],10000)

    def test_summon_projectiles_ignore_conductor_penalty_and_chains(self):
        self.hero('Druid');self.gear('arcane_conductor');enemy=self.room['enemies'][0]
        self.world._launch_projectile(self.room,side='hero',owner_id=self.pid,target_id=enemy['id'],
            x=100,y=200,damage=20,color='#fff',attack_class='Druid',summon_id='bird')
        shot=self.room['projectiles'][0];self.assertEqual(shot['damage'],20);self.assertFalse(shot.get('conductorJump'))

    def test_summoner_staff_durability_and_direct_damage_cost(self):
        self.hero('Druid');self.p['abilities'][0]='thornshot';item=self.gear('summoners_staff');self.cast('fire_wolf')
        wolf=self.room['summons'][0];self.assertEqual(wolf['maxHp'],98)
        self.cast('thornshot');penalized=self.room['projectiles'][-1]['damage']
        self.p['toolSlots']=[dict(key='plain',damage=2),None];self.cast('thornshot')
        self.assertGreater(self.room['projectiles'][-1]['damage'],penalized)
        self.assertGreater(wolf['damage'],penalized*.9)  # Direct penalty never reduces pet damage.

    def test_staff_swapping_preserves_health_without_rounding_heal_exploit(self):
        self.hero('Druid');item=self.gear('summoners_staff');self.cast('fire_wolf');wolf=self.room['summons'][0]
        wolf['hp']=1
        for _ in range(30):
            self.p['toolSlots']=[None,None];tactical.refresh_summon_health(self.p,wolf,dict(hp=65))
            self.p['toolSlots']=[item,None];tactical.refresh_summon_health(self.p,wolf,dict(hp=65))
        self.assertEqual(wolf['hp'],1);self.assertEqual(wolf['maxHp'],98)

    def test_rescue_guard_is_channel_bound_and_cannot_be_refreshed_by_tapping(self):
        ally=self.ally();ally.update(status='downed',hp=0);self.gear('rescuers_cuirass')
        self.world._revive(self.room,self.p);end=self.p['rescueGuardUntil'];self.now+=.5
        self.world._revive(self.room,self.p);self.assertEqual(self.p['rescueGuardUntil'],end)
        before=self.p['hp'];self.world._damage_player(self.room,self.room['enemies'][0],self.p,10)
        self.assertEqual(before-self.p['hp'],4)
        self.world.action(self.code,self.pid,{'action':'stopRevive'})
        self.world._revive(self.room,self.p);self.assertEqual(tactical.rescue_factor(self.room,self.p,self.now),1)

    def test_pursuit_has_idle_cost_one_follow_up_and_requires_an_actual_dash(self):
        self.gear('pursuit_blade');self.assertEqual(tactical.direct_factor(self.p,self.now),.85)
        tactical.dashed(self.p,self.now,0);self.assertEqual(tactical.direct_factor(self.p,self.now),.85)
        self.world.action(self.code,self.pid,{'action':'dash'})
        self.assertAlmostEqual(tactical.direct_factor(self.p,self.now),1.36)
        self.cast('shield_bash');self.assertEqual(tactical.direct_factor(self.p,self.now),.85)

    def test_build_items_enter_loot_and_shop_with_tradeoffs(self):
        for key in tactical.BUILD_ITEMS:
            item=self.world._make_item(key);self.assertTrue(item['effect']);self.assertTrue(item['effectLabel'])
        self.hero('Druid');self.world._stock_shop(self.room,self.p)
        stock=[s['key'] for s in self.p['shopStock']]
        self.assertIn('summoners_staff',stock);self.assertEqual(sum(k in tactical.BUILD_ITEMS for k in stock),2)

    def test_minotaur_cover_collision_creates_damage_opening(self):
        enemy=self.boss('minotaur');enemy.update(x=155,y=200,chargeUntil=self.now+1,chargeVx=270,chargeVy=0,chargeHits=[])
        self.room['environment']['obstacles']=[dict(id='rock',x=200,y=200,radius=24,hp=90,maxHp=90)]
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.1)
        self.assertEqual(enemy['chargeUntil'],self.now);self.assertEqual(enemy['vulnerableUntil'],self.now+3)
        hp=enemy['hp'];self.world._damage_enemy(self.room,self.p,enemy,20);self.assertEqual(hp-enemy['hp'],27)

    def test_behemoth_creates_then_destroys_telegraphed_cover(self):
        enemy=self.boss('troll');self.p.update(x=650,y=300)
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertEqual(enemy['pendingAttack']['kind'],'raise_cover');self.assertFalse(terrain.obstacles(self.room))
        self.now+=1.41;boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertEqual(len(terrain.obstacles(self.room)),2)
        enemy.update(attackIndex=2,nextBossAttack=self.now,recoverUntil=0)
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertEqual(enemy['pendingAttack']['kind'],'shatter')
        self.now+=1.41;boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertFalse(terrain.obstacles(self.room))

    def test_matriarch_weave_is_fixed_connected_with_escape_gap_and_interruptible(self):
        enemy=self.boss('serpent','Poison');self.p.update(x=700,y=250)
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertEqual(len(self.room['hazards']),4)
        before=[(h['x'],h['y']) for h in self.room['hazards']]
        self.p.update(x=900,y=480);boss_ai.tick(self.world,self.room,enemy,self.p,self.now+.1,.05)
        self.assertEqual(before,[(h['x'],h['y']) for h in self.room['hazards']])
        distances=sorted(math.hypot(a[0]-b[0],a[1]-b[1]) for a,b in zip(before,before[1:]))
        self.assertEqual(distances,[66,66,132])
        self.world._stun(enemy,self.now);boss_ai.interrupt(self.world,self.room,enemy,self.now)
        self.assertFalse(self.room['hazards']);self.assertNotIn('pendingAttack',enemy)

    def test_each_dragon_element_has_distinct_spatial_signature(self):
        signatures=set()
        for affinity in ('Fire','Ice','Storm','Dark','Arcane'):
            enemy=self.boss('dragon',affinity)
            boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
            signatures.add(enemy['pendingAttack']['kind']);self.assertTrue(self.room['hazards'])
        self.assertEqual(len(signatures),5)

    def test_storm_phase_two_rewards_spacing_instead_of_overlapping_partners(self):
        ally=self.ally();enemy=self.boss('dragon','Storm',2)
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertTrue(any(h.get('label')=='RESONANCE' for h in self.room['hazards']))
        ally['x']=600;enemy=self.boss('dragon','Storm',2)
        boss_ai.tick(self.world,self.room,enemy,self.p,self.now,.05)
        self.assertFalse(any(h.get('label')=='RESONANCE' for h in self.room['hazards']))

    def test_armor_is_foreshadowed_and_true_form_changes_strategy(self):
        enemy=self.boss('dragon','Fire');original=boss_ai.pattern(enemy)
        self.assertIn('ARMOR',boss_ai.view(self.room)['phaseLabel'])
        self.world._damage_enemy(self.room,self.p,enemy,7000)
        self.assertTrue(enemy['armorWarned']);self.assertTrue(any('cracking' in m['message'] for m in self.room['chat']))
        self.world._damage_enemy(self.room,self.p,enemy,10000)
        self.assertEqual(enemy['bossPhase'],2);self.assertNotEqual(boss_ai.pattern(enemy),original)
        self.assertEqual(enemy['recoverUntil'],self.now+2);self.assertIn('TRUE FORM',boss_ai.view(self.room)['phaseLabel'])

    def test_pause_preserves_new_status_and_build_clocks(self):
        self.p.update(pursuitUntil=self.now+2,rescueGuardReadyAt=self.now+8)
        enemy=self.room['enemies'][0];enemy.update(rootUntil=self.now+.8,vulnerableUntil=self.now+3)
        self.world._shift_clocks(self.room,20)
        self.assertEqual(self.p['pursuitUntil'],self.now+22);self.assertEqual(enemy['rootUntil'],self.now+20.8)
