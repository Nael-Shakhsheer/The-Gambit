import copy
import threading
import unittest
from unittest.mock import patch

import server
from game import ABILITY_SETS, GameWorld


class MultiplayerReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.
        clock = patch('game.time.monotonic', side_effect=lambda: self.now)
        clock.start(); self.addCleanup(clock.stop)
        self.world = GameWorld()

    def party(self):
        code, host = self.world.create_room('Host')
        _, friend = self.world.join_room(code, 'Friend')
        for pid, hero in ((host, 'Rogue'), (friend, 'Knight')):
            self.world.action(code, pid, {'action':'class', 'class':hero})
            self.world.action(code, pid, {'action':'loadout', 'abilities':[a[0] for a in ABILITY_SETS[hero][::2]]})
        self.world.action(code, host, {'action':'start'})
        room = self.world.rooms[code]
        room['environment'] = {'obstacles':[], 'zones':[], 'stage':1, 'region':room['region']}
        room['story']['encountered'] = True
        return room, host, friend

    def test_render_crash_bleeding_squadron_enemy_is_not_targeted_after_death(self):
        room, host, friend = self.party()
        first = room['enemies'][0]
        second = copy.deepcopy(first)
        second.update(id='survivor', hp=500, maxHp=500, x=800, y=50)
        room.update(encounterName='Mini-boss Squadron', enemies=[first, second])
        first.update(hp=1, bleedUntil=self.now+5, bleedDamage=7, bleedOwner=host, lastBleedTick=0)
        self.world.action(room['code'], friend, {'action':'input', 'x':1, 'y':0, 'sequence':1})
        x = room['players'][friend]['x']
        self.now += .05
        with patch.object(self.world, '_tick_enemy', wraps=self.world._tick_enemy) as ai:
            self.world.tick()
        self.assertNotIn(first, room['enemies'])
        self.assertEqual([call.args[1]['id'] for call in ai.call_args_list], ['survivor'])
        self.assertGreater(room['players'][friend]['x'], x)
        self.assertFalse(self.world._tick_errors)
        self.now += .05; self.world.tick()
        self.assertGreater(room['players'][friend]['x'], x+5)

    def test_last_bleeding_enemy_can_start_next_wave_without_a_ghost_attack(self):
        room, host, _ = self.party()
        room.update(encounterName='Mini-boss Squadron', stageWave=1, stageWaves=2)
        first = room['enemies'][0]
        room['enemies'] = [first]
        first.update(hp=1, bleedUntil=self.now+5, bleedDamage=7, bleedOwner=host, lastBleedTick=0)
        with patch.object(self.world, '_tick_enemy') as ai:
            self.world.tick()
        ai.assert_not_called()
        self.assertTrue(room['waveStartsAt'])
        self.assertFalse(self.world._tick_errors)
        self.now = room['waveStartsAt']+.01; self.world.tick()
        self.assertTrue(room['enemies'])

    def test_one_room_fault_does_not_freeze_other_rooms_and_recovers_next_tick(self):
        broken, _, _ = self.party()
        healthy, host, _ = self.party()
        self.world.action(healthy['code'], host, {'action':'input', 'x':1, 'y':0})
        x = healthy['players'][host]['x']
        actual = self.world._tick_room
        def fail_one(room, now):
            if room is broken: raise RuntimeError('Injected room fault')
            actual(room, now)
        self.now += .05
        with patch.object(self.world, '_tick_room', side_effect=fail_one), self.assertLogs(level='ERROR'):
            self.world.tick()
        self.assertGreater(healthy['players'][host]['x'], x)
        self.assertIn(broken['code'], self.world._tick_errors)
        self.now += .05; self.world.tick()
        self.assertFalse(self.world._tick_errors)

    def test_dash_has_five_second_server_cooldown_with_fractional_snapshot(self):
        room, host, _ = self.party()
        p = room['players'][host]
        p.update(x=100, y=250, facingX=1, facingY=0)
        self.world.action(room['code'], host, {'action':'dash'})
        self.assertAlmostEqual(p['x'], 216)
        with self.assertRaisesRegex(ValueError, 'recharges'):
            self.world.action(room['code'], host, {'action':'dash'})
        self.now += 4.95
        view = self.world.state(room['code'], host)
        self.assertEqual(view['dashCooldown'], 1)
        self.assertAlmostEqual(view['dashCooldownRemaining'], .05)
        self.assertEqual(view['dashCooldownDuration'], 5)
        self.now += .05
        self.world.action(room['code'], host, {'action':'dash'})
        self.assertAlmostEqual(p['x'], 332)

    def test_reconnect_snapshot_recovers_input_sequence_for_reloaded_clients(self):
        room, host, _ = self.party()
        self.world.action(room['code'], host, {'action':'input', 'x':1, 'sequence':5000})
        snapshot = self.world.state(room['code'], host)
        self.assertEqual(snapshot['inputSequence'], 5000)
        self.world.action(room['code'], host, {'action':'input', 'x':-1, 'sequence':snapshot['inputSequence']+1})
        self.assertEqual(room['players'][host]['dx'], -1)
        self.world.action(room['code'], host, {'action':'input', 'x':1, 'sequence':5000})
        self.assertEqual(room['players'][host]['dx'], -1)

    def test_outer_simulation_loop_survives_an_unexpected_exception(self):
        stop = threading.Event()
        calls = []
        def tick():
            calls.append(1)
            if len(calls) == 1: raise RuntimeError('Injected global failure')
            stop.set()
        with patch.object(server.WORLD, 'tick', side_effect=tick), \
                patch.object(server, 'SIMULATION_LAST_TICK', None), self.assertLogs(level='ERROR'):
            server._simulation_loop(stop)
            self.assertEqual(len(calls), 2)
            self.assertEqual(server.SIMULATION_LAST_TICK, self.now)

    def test_held_light_attacks_do_not_flood_the_party_chat(self):
        room, host, _ = self.party()
        player = room['players'][host]
        foe = room['enemies'][0]
        foe.update(x=player['x']+20,y=player['y'],hp=10000,maxHp=10000)
        self.world.action(room['code'],host,{'action':'chat','message':'Gather here'})
        messages = len(room['chat'])
        hp = foe['hp']
        for _ in range(15):
            self.now += 1
            self.world.action(room['code'],host,{'action':'attack'})
        self.assertLess(foe['hp'],hp)
        self.assertEqual(len(room['chat']),messages)
        self.assertEqual(room['chat'][-1]['message'],'Gather here')
