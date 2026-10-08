import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import boss_ai
import progression
from game import GameWorld, ABILITY_SETS, CLASSES
from test_support import finish_dialogue, rest_at_bed


class HunterStoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        clock = patch("game.time.monotonic", side_effect=lambda: self.now)
        clock.start(); self.addCleanup(clock.stop)

    def party(self, heroes=("Knight", "Healer"), **kwargs):
        world = GameWorld(**kwargs); code, host = world.create_room("Hunter")
        ids = [host]+[world.join_room(code, "Friend")[1] for _ in heroes[1:]]
        for pid, hero in zip(ids, heroes):
            world.action(code, pid, {"action": "class", "class": hero})
            world.action(code, pid, {"action": "loadout", "abilities": [a[0] for a in ABILITY_SETS[hero][::2]]})
        world.action(code, host, {"action": "start"})
        return world, world.rooms[code], [world.rooms[code]["players"][pid] for pid in ids]

    def tick(self, world, n=1):
        for _ in range(n):
            self.now += .05; world.tick()

    def welcome(self, world, room, players):
        room["townWelcome"]["y"] = 405
        self.tick(world)
        for p in players: finish_dialogue(world, room, p)
        self.tick(world)

    def test_early_story_happens_once_after_either_stage_without_consuming_a_stage(self):
        for stage in (1, 2):
            world, room, players = self.party(("Knight",))
            p = players[0]; room["story"]["afterStage"] = stage
            room.update(stage=stage, townStages=[], puzzleStages=[])
            world._present_routes(room); p.update(x=480, y=30)
            world._tick_travel(room)
            self.assertEqual(room["phase"], "peace"); self.assertEqual(room["stage"], stage)
            p.update(x=480,y=250)
            world.action(room["code"],p["id"],{"action":"interact"})
            self.assertIn("dragon", progression.dialogue(p)["text"])
            with self.assertRaises(ValueError):
                world.action(room["code"],p["id"],{"action":"dialogueNext","id":"stale","page":0})
            finish_dialogue(world,room,p)
            self.assertEqual(room["story"]["quest"],"active")
            p.update(x=480,y=30); self.tick(world)
            self.assertNotEqual(room["phase"],"peace")
            self.assertTrue(room["story"]["encountered"])

    def test_peace_requires_every_present_human_to_accept_but_offline_players_do_not_block(self):
        world, room, players = self.party()
        progression.enter_peace(world,room)
        players[0].update(questAccepted=True,x=480,y=30)
        self.tick(world); self.assertEqual(room["phase"],"peace")
        world.action(room["code"],players[1]["id"],{"action":"disconnect"})
        self.tick(world); self.assertNotEqual(room["phase"],"peace")

    def test_village_runner_freezes_all_movement_until_every_present_player_acknowledges(self):
        world, room, players = self.party(); world._enter_town(room)
        before=[(p["x"],p["y"]) for p in players]
        for p in players:
            world.action(room["code"],p["id"],{"action":"input","x":1,"y":-1})
        self.tick(world,15)
        self.assertEqual(before,[(p["x"],p["y"]) for p in players])
        self.assertEqual(room["townWelcome"]["y"],405)
        finish_dialogue(world,room,players[0]); self.tick(world)
        self.assertFalse(room["townWelcome"]["done"])
        finish_dialogue(world,room,players[1]); self.tick(world)
        self.assertTrue(room["townWelcome"]["done"])
        world.action(room["code"],players[0]["id"],{"action":"input","x":1,"y":0});self.tick(world)
        self.assertGreater(players[0]["x"],before[0][0])

    def test_first_village_requires_tutorial_and_occupied_rooms_block_movement(self):
        world,room,players=self.party();world._enter_town(room);self.welcome(world,room,players)
        for p in players: p.update(x=480,y=490)
        with self.assertRaisesRegex(ValueError,"Every present"):
            world._vote_town_exit(room,players[0])
        p=players[0]; p.update(townInterior="inn",x=480,y=220)
        world.action(room["code"],p["id"],{"action":"interact"});finish_dialogue(world,room,p)
        self.assertTrue(p["trainingKnown"]);self.assertEqual(p["skillPoints"],1)
        p.update(townInterior=None,x=480,y=490)
        with self.assertRaises(ValueError):world._vote_town_exit(room,p)
        occupied=next(r for r in room["innRooms"] if r["locked"])
        p.update(townInterior="inn",innFloor=2,x=occupied["x"],y=335)
        self.assertFalse(progression.interior_walkable(room,p,p["x"],320))
        world.action(room["code"],p["id"],{"action":"interact"})
        self.assertIn("locked",room["privateNotices"][p["id"]])

    def test_only_upstairs_beds_create_checkpoints_and_disk_restore_returns_to_same_room(self):
        with tempfile.TemporaryDirectory() as directory:
            world,room,players=self.party(storage_dir=directory);world._enter_town(room)
            file=Path(directory)/"checkpoints"/(room["code"]+".json")
            self.assertFalse(file.exists());self.assertIsNone(room["checkpoint"])
            self.welcome(world,room,players)
            p=players[0];p.update(townInterior="inn",x=480,y=220)
            world.action(room["code"],p["id"],{"action":"interact"});finish_dialogue(world,room,p)
            self.assertFalse(file.exists())
            p.update(x=710,y=350,townInteraction=None)
            world.action(room["code"],p["id"],{"action":"interact"})
            self.assertEqual(p["innFloor"],2)
            bed=next(r for r in room["innRooms"] if not r["locked"])
            p.update(x=bed["x"],y=bed["y"],hp=1,mana=0)
            world.action(room["code"],p["id"],{"action":"interact"})
            self.assertTrue(file.exists()); self.assertEqual(p["hp"],p["maxHp"])
            restored=GameWorld(storage_dir=directory);q=restored.rooms[room["code"]]["players"][p["id"]]
            self.assertEqual((q["townInterior"],q["innFloor"],q["x"]),("inn",2,bed["x"]))
            view=restored.state(room["code"],p["id"])
            self.assertEqual((view["townInterior"],view["innFloor"]),("inn",2))
            self.assertEqual(q["x"],bed["x"])
            self.assertEqual(q["skillPoints"],1);self.assertEqual(restored.rooms[room["code"]]["innRooms"],room["innRooms"])
            p.update(x=710,y=430)
            world.action(room["code"],p["id"],{"action":"interact"});self.assertEqual(p["innFloor"],1)

    def test_visiting_another_town_cannot_overwrite_the_previous_bed_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            world,room,players=self.party(storage_dir=directory);world._enter_town(room);rest_at_bed(world,room)
            file=Path(directory)/"checkpoints"/(room["code"]+".json");before=file.read_bytes()
            previous=copy.deepcopy(room["checkpoint"]);room["stage"]+=3;world._enter_town(room)
            world._save_checkpoint(room)
            self.assertEqual(before,file.read_bytes());self.assertEqual(room["checkpoint"],previous)
            room["phase"]="defeat"
            world.action(room["code"],players[0]["id"],{"action":"checkpointResume"})
            self.assertEqual(room["townInstance"],previous["townInstance"])
            self.assertEqual(players[0]["innFloor"],2)

    def test_skill_ranks_cost_points_have_caps_and_use_new_hero_base_after_guild(self):
        world,room,players=self.party();world._enter_town(room);rest_at_bed(world,room)
        p=players[0];p.update(townInterior="inn",innFloor=1,x=480,y=220,skillPoints=9)
        for branch in progression.SKILLS:
            for _ in range(3):world.action(room["code"],p["id"],{"action":"trainSkill","branch":branch})
            with self.assertRaises(ValueError):world.action(room["code"],p["id"],{"action":"trainSkill","branch":branch})
        self.assertEqual(p["skillPoints"],0);self.assertEqual(p["maxHp"],168)
        p.update(townInterior="guild",x=480,y=220,townInteraction="guildmaster")
        world.action(room["code"],p["id"],{"action":"guildPreview","class":"Wizard"})
        world.action(room["code"],p["id"],{"action":"guildChange","abilities":p["guildPreview"]["selected"]})
        self.assertEqual(p["maxHp"],progression.max_hp(p,CLASSES));self.assertEqual(p["skillRanks"]["power"],3)

    def test_legacy_checkpoint_is_bound_to_its_original_village(self):
        with tempfile.TemporaryDirectory() as directory:
            world,room,players=self.party(storage_dir=directory);world._enter_town(room);rest_at_bed(world,room)
            room["checkpoint"].pop("townInstance");room.pop("townInstance")
            room["checkpoint"].pop("bed")
            world.storage.save(room)
            restored=GameWorld(storage_dir=directory);saved=restored.rooms[room["code"]]
            restored.state(room["code"],players[0]["id"])
            self.assertEqual(saved["checkpoint"]["townInstance"],saved["townInstance"])
            file=Path(directory)/"checkpoints"/(room["code"]+".json");before=file.read_bytes()
            saved["stage"]+=3;restored._enter_town(saved);restored._save_checkpoint(saved)
            self.assertEqual(file.read_bytes(),before)

    def test_rewards_are_once_per_run_even_after_repeat_tutorial_or_boss_retry(self):
        world,room,players=self.party();world._enter_town(room);rest_at_bed(world,room)
        p=players[0]; progression.reward(p,"first_inn");self.assertEqual(p["skillPoints"],1)
        room["bossesDefeated"]=1;progression.boss_reward(room);progression.boss_reward(room)
        self.assertEqual(p["skillPoints"],2)
        room["bossesDefeated"]=2;progression.boss_reward(room);self.assertEqual(p["skillPoints"],3)
        room["bossesDefeated"]=3;progression.boss_reward(room);self.assertEqual(room["story"]["quest"],"complete")

    def test_enemy_retargets_living_hero_and_downing_does_not_shorten_rescue_timer(self):
        world,room,players=self.party();p,q=players;p.update(status="downed",hp=0,downedUntil=self.now+8,x=200,y=200)
        q.update(x=700,y=200,hp=1000,maxHp=1000)
        e=room["enemies"][0];room["enemies"]=[e];e.update(x=180,y=200,targetId=p["id"],moveDecisionAt=self.now+99,moveGoal=[200,200])
        self.tick(world);self.assertEqual(e["targetId"],q["id"]);self.assertGreater(e["moveGoal"][0],300)
        until=p["downedUntil"];world._damage_player(room,e,p,100);self.assertEqual(p["downedUntil"],until)
        boss_ai.area(room,e,p["x"],p["y"],self.now,delay=0)
        boss_ai.tick_areas(world,room,self.now+.05);self.assertEqual(p["downedUntil"],until)

    def test_projectiles_and_splash_ignore_downed_heroes(self):
        world,room,players=self.party();p,q=players
        p.update(status="downed",hp=0,x=250,y=200,downedUntil=self.now+8);q.update(x=500,y=450)
        world._launch_projectile(room,side="enemy",owner_id="foe",target_id=p["id"],x=200,y=200,damage=50,color="#fff",attack_class="Wizard",speed=200,splash=100)
        self.now+=.3;world._tick_projectiles(room,self.now)
        self.assertEqual(p["downedUntil"],1008);self.assertEqual(len(room["projectiles"]),1)

    def test_mana_regeneration_is_halved_and_focus_changes_it(self):
        world,room,players=self.party();p=players[0];room["enemies"]=[];p.update(mana=0,lastManaTick=self.now)
        self.tick(world,10);self.assertAlmostEqual(p["mana"],1)
        p["skillRanks"]["focus"]=3;self.tick(world,10);self.assertAlmostEqual(p["mana"],2.15)
        room["phase"]="routes";room["routes"]=[];p.update(mana=0,lastManaTick=self.now)
        self.tick(world,10);self.assertAlmostEqual(p["mana"],3.45)
