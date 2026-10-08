from test_support import rest_at_bed
import copy
import math
import random
import tempfile
import unittest
from unittest.mock import patch

import boss_ai
import companion_ai
from game import ABILITY_SETS, CLASSES, DIFFICULTIES, DRAGON_TYPES, LARGE_BOSSES, GameWorld


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        timer = patch("game.time.monotonic", side_effect=lambda: self.now)
        timer.start()
        self.addCleanup(timer.stop)

    def party(self, mode="medium", companion=False, **kwargs):
        world = GameWorld(**kwargs)
        code, pid = world.create_room("Hero")
        world.action(code, pid, {"action": "class", "class": "Knight"})
        world.action(code, pid, {"action": "loadout", "abilities": [a[0] for a in ABILITY_SETS["Knight"][::2]]})
        world.action(code, pid, {"action": "runOptions", "difficulty": mode, "companion": companion})
        world.action(code, pid, {"action": "start"})
        room = world.rooms[code]
        return world, room, room["players"][pid]

    def steps(self, world, count):
        for _ in range(count):
            self.now += .05
            world.tick()

    def test_modes_have_valid_event_schedules_and_exact_final_stage(self):
        for mode, settings in DIFFICULTIES.items():
            for _ in range(12):
                world, room, _ = self.party(mode)
                total = settings["stages"]
                self.assertEqual(room["totalStages"], total)
                self.assertEqual(room["bossStages"][-1], total)
                for key in ("puzzleStages", "miniBossStages", "townStages"):
                    self.assertTrue(all(1 < stage < total for stage in room[key]))
                    self.assertEqual(len(room[key]), len(set(room[key])))
                self.assertFalse(set(room["townStages"]) & set(room["puzzleStages"]+room["miniBossStages"]+room["bossStages"]))
                self.assertTrue(room["townStages"])

    def test_balance_modes_baseline_and_per_stage_strength_compose(self):
        world, room, _ = self.party()
        template = {"hp": 100, "maxHp": 100, "damage": 100, "speed": 100, "kind": "spider"}
        room.update(encounterType="normal", townsVisited=0)
        for mode, settings in DIFFICULTIES.items():
            for stage in (1, 13, 20):
                room.update(difficulty=mode, stage=stage, enemies=[copy.deepcopy(template)])
                world._tune_enemy_group(room)
                factor = 1.15*settings["multiplier"]*(1+.05*(stage-1))
                self.assertEqual(room["enemies"][0]["maxHp"], math.ceil(100*factor))
                self.assertEqual(room["enemies"][0]["damage"], math.ceil(100*factor))

    def test_late_solo_counts_and_three_wave_frequency(self):
        world, room, _ = self.party()
        room.update(routeEffect="enemy_health", routePressure=0)
        for stage, low, high in ((1, 1, 2), (13, 2, 3), (17, 3, 4), (20, 5, 5), (29, 5, 5)):
            room["stage"] = stage
            for _ in range(8):
                world._spawn_regular_wave(room)
                self.assertTrue(low <= len(room["enemies"]) <= high)
        with patch("game.random.random", return_value=.74):
            self.assertEqual(world._stage_wave_count(1, 13), 3)
        with patch("game.random.random", return_value=.75):
            self.assertEqual(world._stage_wave_count(1, 13), 2)
        self.assertEqual(world._stage_wave_count(1, 17), 3)
        self.assertEqual(world._stage_wave_count(4, 7), 3)

    def test_early_three_wave_stages_have_ten_percent_chance_for_every_party_size(self):
        for stage in range(1, 7):
            for size in range(1, 5):
                with patch("game.random.random", return_value=.099):
                    self.assertEqual(GameWorld._stage_wave_count(size, stage), 3)
                with patch("game.random.random", return_value=.10):
                    self.assertEqual(GameWorld._stage_wave_count(size, stage), 2)

    def test_all_ultimates_recharge_in_fifteen_seconds_after_start_and_cast(self):
        self.assertTrue(all(a[6] == 15 for abilities in ABILITY_SETS.values() for a in abilities if a[7] == "ultimate"))
        world, room, p = self.party()
        self.assertEqual(world._ability_slots(p)[2]["cooldownLeft"], 15)
        self.now += 15
        world._cast_ability(room, p, 2)
        self.assertEqual(p["abilityCooldowns"][p["abilities"][2]], self.now+15)
        p["mana"] = 100
        self.now += 14.9
        with self.assertRaisesRegex(ValueError, "ready in"):
            world._cast_ability(room, p, 2)
        self.now += .11
        world._cast_ability(room, p, 2)

    def test_companion_is_unique_hero_real_slot_and_scales_waves(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        self.assertEqual(len(world._active_players(room)), 2)
        self.assertIn(bot["class"], CLASSES)
        self.assertNotEqual(bot["class"], p["class"])
        self.assertEqual(len(bot["abilities"]), 3)
        self.assertTrue(3 <= len(room["enemies"]) <= 5)
        with self.assertRaisesRegex(ValueError, "before"):
            world.action(room["code"], p["id"], {"action": "runOptions", "companion": False})

    def test_companion_option_reserves_slot_and_cannot_be_set_by_guest(self):
        world = GameWorld()
        code, host = world.create_room("Host")
        _, guest = world.join_room(code, "Guest")
        with self.assertRaisesRegex(ValueError, "host"):
            world.action(code, guest, {"action": "runOptions", "difficulty": "hard"})
        world.action(code, host, {"action": "runOptions", "companion": True})
        world.join_room(code, "Third human")
        with self.assertRaisesRegex(ValueError, "full"):
            world.join_room(code, "Fifth member")
        world.action(code, host, {"action": "runOptions", "companion": False})
        world.join_room(code, "Fourth human")
        with self.assertRaisesRegex(ValueError, "slot"):
            world.action(code, host, {"action": "runOptions", "companion": True})

    def test_companion_fights_summons_and_records_contribution(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        bot.update(**{"class": "Druid"}, abilities=["thornshot", "fire_wolf", "ice_bear"], abilityCooldowns={"ice_bear": self.now+15})
        e = room["enemies"][0]
        e.update(x=bot["x"], y=bot["y"]-60, hp=10000, maxHp=10000, stunUntil=self.now+100)
        room["enemies"] = [e]
        self.steps(world, 40)
        self.assertTrue(room["summons"])
        self.assertLess(e["hp"], 10000)
        self.assertGreater(room["runStats"][bot["id"]]["damageDealt"], 0)

    def test_companion_revives_human_and_pauses_when_humans_disconnect(self):
        world, room, p = self.party(companion=True, disconnect_timeout=15)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        bot.update(**{"class": "Knight"}, abilities=[a[0] for a in ABILITY_SETS["Knight"][::2]], x=p["x"], y=p["y"])
        p.update(status="downed", hp=0, downedUntil=self.now+8)
        for e in room["enemies"]:
            e["stunUntil"] = self.now+100
        self.steps(world, 42)
        self.assertEqual(p["status"], "alive")
        self.assertEqual(room["runStats"][bot["id"]]["revives"], 1)
        world.action(room["code"], p["id"], {"action": "disconnect"})
        before = (bot["x"], bot["y"], bot["hp"], room["stage"])
        self.steps(world, 400)
        self.assertEqual(before, (bot["x"], bot["y"], bot["hp"], room["stage"]))
        self.assertFalse(world._active_players(room))

    def test_companion_does_not_block_town_exit_or_checkpoint_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            world, room, p = self.party("hard", companion=True, storage_dir=directory)
            bot = next(member for member in room["players"].values() if member.get("bot"))
            world._enter_town(room)
            rest_at_bed(world, room)
            p.update(x=480, y=490)
            world._vote_town_exit(room, p)
            self.steps(world, 4)
            self.assertEqual(room["phase"], "combat")
            restored = GameWorld(storage_dir=directory)
            view = restored.state(room["code"], p["id"])
            self.assertTrue(view["npcCompanion"])
            self.assertEqual(view["difficulty"], "hard")
            self.assertEqual(view["totalStages"], 30)
            self.assertEqual(len(restored._active_players(restored.rooms[room["code"]])), 2)
            self.assertTrue(restored.rooms[room["code"]]["players"][bot["id"]]["bot"])

    def test_companion_completes_fork_and_chest_without_waiting_for_input(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        room.update(townStages=[], puzzleStages=[])
        world._present_routes(room)
        world._enter_fork(room)
        p.update(x=28, y=170)
        self.steps(world, 300)
        self.assertEqual(room["stage"], 2)
        self.assertEqual(room["phase"], "combat")
        room.update(phase="chest", chest={"x": bot["x"], "y": bot["y"], "decisions": {p["id"]: "opened"}, "runesAwarded": True})
        bot.update(chestReward=None, status="alive", hp=bot["maxHp"])
        with patch.object(world, "_roll_chest_outcome", return_value="runes"), patch("game.random.random", return_value=1):
            companion_ai.tick(world, room, self.now, ABILITY_SETS)
        self.assertEqual(room["phase"], "stage_exit")

    def test_companion_resets_navigation_at_each_fork(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        room.update(townStages=[], puzzleStages=[], miniBossStages=[])
        for expected in (2, 3):
            for member in room["players"].values(): member.update(status="alive", hp=member["maxHp"])
            world._present_routes(room)
            world._enter_fork(room)
            self.assertIsNone(bot["aiRoute"])
            self.assertEqual(bot["aiPathIndex"], 0)
            p.update(x=28, y=170)
            self.steps(world, 280)
            self.assertEqual(room["stage"], expected)
            self.assertEqual(room["phase"], "combat")

    def test_companion_never_inherits_host_and_last_human_can_leave(self):
        world = GameWorld()
        code, host = world.create_room("Host")
        world.action(code, host, {"action": "runOptions", "companion": True})
        _, guest = world.join_room(code, "Guest")
        world.action(code, host, {"action": "leaveRoom"})
        self.assertEqual(world.rooms[code]["host"], guest)
        world.action(code, guest, {"action": "leaveRoom"})
        self.assertNotIn(code, world.rooms)

    def test_pause_shifts_tracking_window_and_malformed_mode_is_rejected(self):
        world, room, p = self.party()
        shot = {"trackUntil": self.now+1.1, "expiresAt": self.now+3}
        world._shift_clocks(shot, 50)
        self.assertEqual(shot["trackUntil"], self.now+51.1)
        room["phase"] = "lobby"
        with self.assertRaises(ValueError):
            world.action(room["code"], p["id"], {"action": "runOptions", "difficulty": []})

    def test_companion_puzzle_requires_shared_clue_then_can_finish(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        room.update(phase="puzzle", puzzle=world._new_puzzle(room))
        own = room["puzzle"]["rooms"][p["id"]]
        buddy = room["puzzle"]["rooms"][bot["id"]]
        p.update(x=own["totem"]["x"], y=own["totem"]["y"])
        self.steps(world, 120)
        self.assertNotEqual(bot.get("aiRunePuzzle"), room["puzzle"]["id"])
        world.action(room["code"], p["id"], {"action": "shareClue"})
        self.steps(world, 180)
        self.assertTrue(buddy["totemSeen"])
        self.assertIsNotNone(world.state(room["code"], p["id"])["companionClue"])
        answer = next(r for r in own["runes"] if r["rune"] == own["target"])
        p.update(x=answer["x"], y=answer["y"])
        self.steps(world, 200)
        self.assertEqual(room["phase"], "combat")

    def test_enemy_does_not_strafe_or_follow_input_between_decisions(self):
        world, room, p = self.party()
        e = room["enemies"][0]
        e.update(x=100, y=100, **{"class": "Knight"}, combatRole="bruiser", speed=100)
        p.update(x=500, y=100)
        world._tick_enemy(room, e, p, self.now)
        goal = e["moveGoal"].copy()
        p.update(x=300, y=400, dx=-1, dy=1)
        self.now += .05
        world._tick_enemy(room, e, p, self.now)
        self.assertEqual(e["moveGoal"], goal)
        self.assertEqual(e["y"], 100)
        e.update(x=100, y=100, moveDecisionAt=0, combatRole="ranged", **{"class": "Archer"})
        p.update(x=150, y=100)
        self.now += .05
        world._tick_enemy(room, e, p, self.now)
        self.assertLess(e["x"], 100)  # Ranged roles retreat when crowded.
        self.assertEqual(e["y"], 100)

    def test_enemy_projectiles_turn_gently_then_stop_tracking(self):
        world, room, p = self.party()
        p.update(x=600, y=250)
        world._launch_projectile(room, side="enemy", owner_id="enemy", target_id=p["id"], x=100, y=250,
                                 damage=10, color="#fff", attack_class="Wizard", speed=200)
        shot = room["projectiles"][0]
        p["y"] = 450
        self.now += .05
        world._tick_projectiles(room, self.now)
        angle = math.atan2(shot["vy"], shot["vx"])
        self.assertTrue(0 < angle <= .65*.05+1e-8)
        self.assertAlmostEqual(math.hypot(shot["vx"], shot["vy"]), 200)
        self.now += 1.2
        shot["lastTick"] = self.now-.05
        p.update(x=100, y=100)
        world._tick_projectiles(room, self.now)
        self.assertAlmostEqual(math.atan2(shot["vy"], shot["vx"]), angle)

    def test_ten_item_pouch_and_non_item_chests_work_when_full(self):
        for outcome in ("runes", "heal", "item"):
            world, room, p = self.party()
            p["inventory"] = [world._make_item("mana_draught") for _ in range(10)]
            p.update(x=480, y=270, hp=40)
            room.update(phase="chest", chest={"x": 480, "y": 270, "decisions": {}, "runesAwarded": False})
            with patch.object(world, "_roll_chest_outcome", return_value=outcome), patch("game.random.random", return_value=1):
                world.action(room["code"], p["id"], {"action": "openChest"})
            self.assertEqual(len(p["inventory"]), 10)
            if outcome == "item":
                self.assertIsNotNone(p["chestReward"])
                world.action(room["code"], p["id"], {"action": "chestClaim", "replace": p["inventory"][0]["id"]})
            elif outcome == "heal":
                self.assertEqual(p["hp"], 115)
            else:
                self.assertGreaterEqual(room["runes"], 20)
            self.assertEqual(room["phase"], "stage_exit")

    def boss(self, kind="minotaur"):
        world, room, p = self.party()
        room.update(stage=room["bossStages"][0], stageWave=1, stageWaves=1,
                    bossSequence=[next(b for b in LARGE_BOSSES if b["kind"] == kind), LARGE_BOSSES[0], DRAGON_TYPES[0]])
        world._spawn_large_boss(room)
        base_speed = room["enemies"][0]["speed"]
        world._tune_enemy_group(room)
        return world, room, p, room["enemies"][0], base_speed

    def test_stone_and_labyrinth_bosses_speed_and_telegraphed_patterns(self):
        for kind in ("minotaur", "troll"):
            world, room, p, boss, base_speed = self.boss(kind)
            self.assertEqual(boss["speed"], base_speed*2.5)
            p.update(x=600, y=250)
            boss.update(x=400, y=250, nextBossAttack=self.now, attackIndex=1)
            boss_ai.tick(world, room, boss, p, self.now, .05)
            self.assertEqual(boss["pendingAttack"]["kind"], "rocks")
            self.assertFalse(room["projectiles"])
            self.now = boss["pendingAttack"]["releaseAt"]+.01
            boss_ai.tick(world, room, boss, p, self.now, .05)
            self.assertEqual(len(room["projectiles"]), 3)
            self.assertTrue(all(shot["radius"] == 18 and shot["splash"] == 65 for shot in room["projectiles"]))

    def test_charge_is_locked_and_hits_each_hero_only_once(self):
        world, room, p, boss, _ = self.boss()
        boss.update(x=400, y=250, nextBossAttack=self.now, attackIndex=2, damage=10)
        p.update(x=600, y=250)
        boss_ai.tick(world, room, boss, p, self.now, .05)
        p.update(x=430, y=250)
        self.now = boss["pendingAttack"]["releaseAt"]+.01
        boss_ai.tick(world, room, boss, p, self.now, .05)
        self.assertEqual(boss["chargeVy"], 0)
        hp = p["hp"]
        for _ in range(6):
            self.now += .05
            boss_ai.tick(world, room, boss, p, self.now, .05)
        self.assertEqual(p["hp"], hp-14)

    def test_aoe_warns_then_damages_multiple_heroes_and_summons(self):
        world, room, p = self.party(companion=True)
        bot = next(member for member in room["players"].values() if member.get("bot"))
        p.update(x=480, y=270)
        bot.update(x=510, y=270, hp=100, maxHp=100)
        enemy = room["enemies"][0]
        enemy.update(damage=10)
        world._summon_companion(room, p, "fire_wolf", 10, self.now)
        summon = room["summons"][0]
        summon.update(x=480, y=270)
        boss_ai.area(room, enemy, 480, 270, self.now, radius=85)
        before = (p["hp"], bot["hp"], summon["hp"])
        boss_ai.tick_areas(world, room, self.now)
        self.assertEqual((p["hp"], bot["hp"], summon["hp"]), before)
        self.now += .91
        boss_ai.tick_areas(world, room, self.now)
        self.assertEqual((p["hp"], bot["hp"], summon["hp"]), tuple(hp-10 for hp in before))

    def test_dragon_phase_two_gates_victory_and_kill_credit(self):
        for mode in DIFFICULTIES:
            world, room, p = self.party(mode)
            room.update(stage=room["totalStages"], bossesDefeated=2, stageWave=3, stageWaves=3)
            world._spawn_wave(room)
            boss = room["enemies"][0]
            first_hp, first_damage = boss["maxHp"], boss["damage"]
            world._damage_enemy(room, p, boss, 1000000)
            self.assertEqual(room["phase"], "combat")
            self.assertEqual(boss["bossPhase"], 2)
            self.assertGreater(boss["maxHp"], first_hp)
            self.assertGreater(boss["damage"], first_damage)
            self.assertEqual(room["bossesDefeated"], 2)
            self.assertEqual(room["runStats"][p["id"]]["kills"], 0)
            second_hp = boss["maxHp"]
            world._damage_enemy(room, p, boss, 1000000)
            self.assertEqual(room["phase"], "cleared")
            self.assertEqual(room["runStats"][p["id"]]["kills"], 1)
            self.assertEqual(room["runStats"][p["id"]]["damageDealt"], first_hp+second_hp)


if __name__ == "__main__":
    unittest.main()
