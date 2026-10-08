import copy
import random
import tempfile
import unittest
from unittest.mock import patch

from game import ABILITY_SETS, GameWorld, TOWN_GATE
from test_support import rest_at_bed


class TesterModeTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.
        clock = patch('game.time.monotonic', side_effect=lambda: self.now)
        clock.start(); self.addCleanup(clock.stop)

    def party(self, mode='medium', **kwargs):
        world=GameWorld(**kwargs); code,pid=world.create_room('Tester')
        world.action(code,pid,{'action':'class','class':'Knight'})
        world.action(code,pid,{'action':'loadout','abilities':[a[0] for a in ABILITY_SETS['Knight'][::2]]})
        world.action(code,pid,{'action':'runOptions','difficulty':mode,'stages':9})
        world.action(code,pid,{'action':'start'})
        return world,world.rooms[code],world.rooms[code]['players'][pid]

    def test_nine_stage_schedules_are_complete_and_non_overlapping(self):
        for mode in ('easy','medium','hard'):
            for seed in range(12):
                random.seed(seed);world,room,p=self.party(mode)
                self.assertEqual(room['bossStages'],[3,6,9])
                self.assertEqual(room['miniBossStages'],[2])
                self.assertEqual(room['townStages'],[4])
                self.assertEqual(room['puzzleStages'],[5])
                self.assertEqual(set(room['objectiveStages']),{'8'})
                self.assertIn(room['objectiveStages']['8'],('rift','ward','charge'))
                self.assertIsNone(room['assassinationStage'])
                view=world.state(room['code'],p['id'])
                self.assertTrue(view['testerMode']);self.assertEqual(view['totalStages'],9)

    def test_compressed_stat_ramp_matches_standard_progression(self):
        world,room,p=self.party('hard')
        template={'hp':100,'maxHp':100,'damage':100,'speed':100,'kind':'spider'}
        for actual in range(1,10):
            room.update(stage=actual,encounterType='normal',townsVisited=0,enemies=[copy.deepcopy(template)])
            expected=1+3*(actual-1)
            self.assertEqual(world._effective_stage(room),expected)
            ramp=world._stage_ramp(room);world._tune_enemy_group(room);foe=copy.deepcopy(room['enemies'][0])
            reference=dict(room,totalStages=25,stage=expected,enemies=[copy.deepcopy(template)])
            self.assertEqual(world._stage_ramp(reference),ramp)
            world._tune_enemy_group(reference)
            self.assertEqual(foe,reference['enemies'][0])

    def test_late_mobs_waves_and_dracos_arrive_before_the_dragon(self):
        world,room,p=self.party()
        for stage,lo,hi in ((1,1,2),(5,2,3),(7,3,4),(8,5,5),(9,5,5)):
            room['stage']=stage
            with patch('game.random.random',return_value=1):world._spawn_regular_wave(room)
            self.assertTrue(lo<=len(room['enemies'])<=hi)
            self.assertEqual(any(e['kind']=='draco' for e in room['enemies']),stage>=7)
        room.update(stage=6,phase='stage_exit')
        world._advance_stage(room,{'kind':'combat','region':'woodland'})
        self.assertEqual(room['stage'],7);self.assertEqual(room['stageWaves'],3)

    def test_mode_survives_a_disk_bed_checkpoint_and_challenge_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            world,room,p=self.party('hard',storage_dir=directory)
            room['stage']=4;world._enter_town(room);rest_at_bed(world,room)
            restored=GameWorld(storage_dir=directory)
            view=restored.state(room['code'],p['id'])
            self.assertEqual(view['totalStages'],9);self.assertTrue(view['testerMode'])
            self.assertEqual(view['balanceStage'],10)
            saved=restored.rooms[room['code']]
            self.assertEqual(saved['bossStages'],[3,6,9]);self.assertEqual(set(saved['objectiveStages']),{'8'})
        world=GameWorld();code,pid=world.create_room('Next')
        world.action(code,pid,{'action':'runOptions','stages':9})
        world.action(code,pid,{'action':'runOptions','difficulty':'hard'})
        self.assertEqual(world.rooms[code]['totalStages'],9)
        world.action(code,pid,{'action':'runOptions','stages':25})
        self.assertFalse(world.state(code,pid)['testerMode'])

    def test_campaign_transitions_reach_both_dragon_phases_and_finish_at_nine(self):
        # Fast-forward damage/time in the test only; use actual wave, puzzle,
        # inn/tutorial and boss transitions. This is not a balance playtest.
        world,room,p=self.party();room['story']['encountered']=True
        bosses=[];saw_phase_two=False
        for stage in range(1,10):
            self.assertEqual(room['stage'],stage)
            if room['phase']=='town':
                rest_at_bed(world,room);p.update(x=TOWN_GATE[0],y=TOWN_GATE[1])
                world.action(room['code'],p['id'],{'action':'townContinue'})
            if room['phase']=='puzzle':
                chamber=room['puzzle']['rooms'][p['id']]
                rune=next(r for r in chamber['runes'] if r['rune']==chamber['target'])
                p.update(x=rune['x'],y=rune['y']);world._tick_puzzle(room)
            rounds=0
            while room['phase']=='combat':
                rounds+=1;self.assertLess(rounds,8)
                if room.get('objective',{}):
                    self.now=max(self.now,room['objective']['endsAt'])
                if not room['enemies']:
                    self.now+=3.1;room['waveStartsAt']=0
                    world._spawn_wave(room,preserve_players=True)
                for e in list(room['enemies']):
                    if e.get('boss'):
                        if stage not in bosses:bosses.append(stage)
                        saw_phase_two |= e.get('bossPhase')==2
                    world._damage_enemy(room,p,e,e['hp'])
            if stage<9:
                next_stage=stage+1
                world._advance_stage(room,{'kind':'town' if next_stage==4 else 'combat','destination':'Tester village','region':'woodland'})
        self.assertEqual(room['phase'],'cleared');self.assertEqual(room['stage'],9)
        self.assertEqual(bosses,[3,6,9]);self.assertTrue(saw_phase_two)
        self.assertEqual(room['bossesDefeated'],3);self.assertEqual(room['puzzlesCompleted'],1)
        self.assertEqual(room['townsVisited'],1)
        self.assertTrue(all(r['testerMode'] for r in room['stageReports']))


if __name__=='__main__':unittest.main()
