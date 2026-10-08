import copy
import unittest
from unittest.mock import patch

import enemy_roles
import combat_encounters
from game import ABILITY_SETS, ENEMIES, GameWorld


class DracoTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.
        clock = patch('game.time.monotonic', side_effect=lambda: self.now)
        clock.start(); self.addCleanup(clock.stop)
        self.world = GameWorld()
        self.code, self.pid = self.world.create_room('Hunter')
        self.world.action(self.code, self.pid, {'action':'class','class':'Knight'})
        self.world.action(self.code, self.pid, {'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        self.world.action(self.code, self.pid, {'action':'start'})
        self.room = self.world.rooms[self.code]
        self.room.update(stage=17, objectiveStages={}, environment={'obstacles':[],'zones':[]}, projectiles=[])
        self.player = self.room['players'][self.pid]
        self.player.update(x=340, y=200)

    def spawn(self, stage=17, include=True):
        self.room['stage'] = stage
        with patch('game.random.random', return_value=0), patch('game.random.randint', side_effect=lambda low, high: low), patch('game.random.choice', side_effect=lambda options: ENEMIES[-1] if options is ENEMIES else options[0]):
            self.world._spawn_regular_wave(self.room, include_dracos=include)
        enemy_roles.assign(self.room)
        return self.room['enemies']

    def draco(self):
        e = next(e for e in self.spawn() if e['kind'] == 'draco')
        e.update(x=300, y=200, moveDecisionAt=0)
        return e

    def tick(self, e, delta=0, target=None):
        self.now += delta
        self.world._tick_enemy(self.room, e, target or self.player, self.now)

    def test_stage_threshold_and_bounded_mixed_groups(self):
        self.assertFalse(any(e['kind']=='draco' for e in self.spawn(16)))
        foes = self.spawn(17)
        self.assertEqual(sum(e['kind']=='draco' for e in foes), 1)
        self.assertGreater(len(foes), 1)
        self.assertFalse(any(e['kind']=='draco' for e in self.spawn(20, include=False)))
        for index in range(3):
            p = copy.deepcopy(self.player); p['id'] = 'ally'+str(index)
            self.room['players'][p['id']] = p
        self.assertEqual(sum(e['kind']=='draco' for e in self.spawn()), 3)

    def test_draco_keeps_its_role_and_has_fast_durable_low_hit_stats(self):
        foes = self.spawn(); e = foes[0]; troll = next(a for a in foes if a['kind']=='troll')
        self.assertEqual(e['combatRole'], 'draco')
        self.assertGreater(e['maxHp'], troll['maxHp'])
        self.assertGreater(e['speed'], troll['speed']*1.7)
        self.assertLess(e['damage'], troll['damage'])
        self.assertGreater(e['damage']/1.25, troll['damage']/2.5)
        self.assertTrue(any(a['combatRole']=='support' and a['kind']!='draco' for a in foes))

    def test_projectile_bite_projectile_cycle_and_windups(self):
        e = self.draco(); self.tick(e)
        self.assertEqual(e['roleAttack']['kind'], 'draco_projectile')
        self.assertFalse(self.room['projectiles'])
        self.tick(e, .36)
        self.assertEqual(len(self.room['projectiles']), 1)
        shot = self.room['projectiles'][0]
        self.assertEqual(shot['damage'], e['damage'])
        self.assertEqual(shot['turnRate'], .3)
        self.assertEqual(shot['radius'], 8)
        self.tick(e, .9)
        self.assertEqual(e['roleAttack']['kind'], 'draco_melee')
        hp = self.player['hp']; self.tick(e, .41)
        self.assertLess(self.player['hp'], hp)
        self.assertEqual(len(self.room['projectiles']), 1)
        self.tick(e, .85)
        self.assertEqual(e['roleAttack']['kind'], 'draco_projectile')

    def test_dodging_bite_avoids_damage_and_still_advances_cycle(self):
        e = self.draco(); e['dracoNext'] = 'draco_melee'; self.tick(e)
        hp = self.player['hp']; self.player['x'] = 420
        self.tick(e, .41)
        self.assertEqual(self.player['hp'], hp)
        self.assertEqual(e['dracoNext'], 'draco_projectile')

    def test_cover_blocks_attack_and_downing_cancels_old_target(self):
        e = self.draco()
        self.room['environment']['obstacles'] = [{'id':'rock','x':320,'y':200,'radius':24,'hp':60,'maxHp':60}]
        self.tick(e)
        self.assertNotIn('roleAttack', e)
        self.room['environment']['obstacles'] = []; e.update(x=300, y=200, moveDecisionAt=0)
        self.tick(e, .1)
        self.assertIn('roleAttack', e)
        ally = copy.deepcopy(self.player); ally.update(id='ally', x=500)
        self.room['players']['ally'] = ally; self.player['status'] = 'downed'
        self.tick(e, .4, ally)
        self.assertNotIn('roleAttack', e)
        self.assertFalse(self.room['projectiles'])
        self.assertEqual(e['targetId'], 'ally')

    def test_objective_reinforcements_do_not_multiply_dracos(self):
        self.spawn(); self.room['objectiveStages']={'17':'rift'}
        combat_encounters.prepare(self.world,self.room)
        self.now+=5; combat_encounters.tick(self.world,self.room,self.now)
        self.assertEqual(sum(e['kind']=='draco' for e in self.room['enemies']),1)
        self.assertNotEqual(self.room['enemies'][-1]['kind'],'draco')


if __name__ == '__main__':
    unittest.main()
