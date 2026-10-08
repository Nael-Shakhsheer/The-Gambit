from test_support import rest_at_bed
import copy
import unittest
from unittest.mock import patch

from game import ABILITY_SETS, SUMMON_TYPES, GameWorld


class DruidTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        timer = patch("game.time.monotonic", side_effect=lambda: self.now)
        timer.start()
        self.addCleanup(timer.stop)
        self.world = GameWorld()
        self.code, self.pid = self.world.create_room("Druid")
        self.act("class", **{"class": "Druid"})
        self.act("loadout", abilities=["thornshot", "lightning_bird", "ice_bear"])
        self.act("start")
        self.now += 15  # Let the opening Ultimate cooldown finish for combat tests.
        self.room = self.world.rooms[self.code]
        self.room["environment"] = None  # Isolate summon mechanics from cover; terrain has its own tests.
        self.player = self.room["players"][self.pid]
        self.player.update(x=300, y=350)
        template = copy.deepcopy(self.room["enemies"][0])
        self.room["enemies"] = [template]
        template.update(x=500, y=350, hp=500, maxHp=500, speed=0, lastAttack=self.now)
        template["class"] = "Knight"
        self.enemy = template

    def act(self, action, **payload):
        self.world.action(self.code, self.pid, {"action": action, **payload})

    def cast(self, ability_id):
        category = next(a[7] for a in ABILITY_SETS["Druid"] if a[0] == ability_id)
        slot = {"light": 0, "special": 1, "ultimate": 2}[category]
        self.player["abilities"][slot] = ability_id
        self.act("ability", slot=slot + 1)
        return next((s for s in self.room["summons"] if s["abilityId"] == ability_id), None)

    def test_both_lights_launch_projectiles_and_damage_only_on_impact(self):
        for ability_id in ("briar_burst", "thornshot"):
            with self.subTest(ability=ability_id):
                hp = self.enemy["hp"]
                self.cast(ability_id)
                self.assertEqual(self.enemy["hp"], hp)
                self.assertEqual(len(self.room["projectiles"]), 1)
                for _ in range(25):
                    self.now += 0.05
                    self.world._tick_projectiles(self.room, self.now)
                self.assertLess(self.enemy["hp"], hp)
                self.assertFalse(self.room["projectiles"])

    def test_each_summon_locks_until_death_then_recharges_for_exact_duration(self):
        for ability_id, template in SUMMON_TYPES.items():
            with self.subTest(ability=ability_id):
                self.player["mana"] = 100
                summon = self.cast(ability_id)
                self.assertEqual(summon["hp"], template["hp"])
                self.assertIn(ability_id, self.player["activeSummons"])
                self.assertNotIn(ability_id, self.player["abilityCooldowns"])
                mana = self.player["mana"]
                self.now += 100
                self.world._tick_summons(self.room, self.now)
                with self.assertRaisesRegex(ValueError, "still alive"):
                    self.cast(ability_id)
                self.assertEqual(self.player["mana"], mana)
                self.world._damage_player(self.room, self.enemy, summon, summon["maxHp"])
                self.assertNotIn(summon, self.room["summons"])
                self.assertEqual(self.player["abilityCooldowns"][ability_id], self.now + template["recharge"])
                self.now += template["recharge"] - 0.01
                with self.assertRaisesRegex(ValueError, "ready in"):
                    self.cast(ability_id)
                self.now += 0.01
                self.player["mana"] = 100
                self.assertIsNotNone(self.cast(ability_id))
                self.world._dismiss_summons(self.room)
                self.now += 16

    def test_special_and_ultimate_locks_are_independent(self):
        bird = self.cast("lightning_bird")
        bear = self.cast("ice_bear")
        self.assertEqual(len(self.room["summons"]), 2)
        slots = self.world.state(self.code, self.pid)["abilitySlots"]
        self.assertTrue(slots[1]["summonAlive"])
        self.assertTrue(slots[2]["summonAlive"])
        self.world._damage_summon(self.room, bird, 1000)
        self.assertIn(bear, self.room["summons"])
        slots = self.world.state(self.code, self.pid)["abilitySlots"]
        self.assertEqual(slots[1]["cooldownLeft"], 8)
        self.assertFalse(slots[1]["summonAlive"])
        self.assertTrue(slots[2]["summonAlive"])

    def test_summons_chase_and_attack_nearest_enemy(self):
        for ability_id in SUMMON_TYPES:
            with self.subTest(ability=ability_id):
                self.player["mana"] = 100
                summon = self.cast(ability_id)
                near = copy.deepcopy(self.enemy)
                far = copy.deepcopy(self.enemy)
                near.update(id="near", x=summon["x"] + (100 if ability_id != "lightning_bird" else 80), y=summon["y"], hp=500)
                far.update(id="far", x=summon["x"] + 200, y=summon["y"], hp=500)
                self.room["enemies"] = [far, near]
                original_x = summon["x"]
                for _ in range(20):
                    self.now += 0.1
                    self.world._tick_summons(self.room, self.now)
                if ability_id == "lightning_bird":
                    self.assertTrue(self.room["projectiles"])
                    self.assertTrue(all(p["targetId"] == "near" for p in self.room["projectiles"]))
                    self.assertTrue(all(p["effectKind"] == "lightning" for p in self.room["projectiles"]))
                else:
                    self.assertGreater(summon["x"], original_x)
                    self.assertLess(near["hp"], 500)
                self.assertEqual(far["hp"], 500)
                self.world._dismiss_summons(self.room)
                self.room["projectiles"] = []
                self.now += 16

    def test_enemy_melee_and_projectiles_can_kill_summons(self):
        wolf = self.cast("fire_wolf")
        self.player.update(x=100,y=350)  # Keep the owner outside the new bruiser's area swing.
        self.enemy.update(x=wolf["x"], y=wolf["y"], damage=1000, lastAttack=0, combatRole="bruiser")
        self.world.tick()
        self.now += .61  # Bruisers now announce their swing before hitting.
        self.world.tick()
        self.assertFalse(self.room["summons"])
        self.assertEqual(self.player["hp"], self.player["maxHp"])
        self.now += 8
        self.player["mana"] = 100
        wolf = self.cast("fire_wolf")
        self.enemy["class"] = "Wizard"
        self.enemy["x"], self.enemy["y"] = wolf["x"] - 30, wolf["y"]
        self.world._enemy_class_attack(self.room, self.enemy, wolf, self.now)
        self.now += 0.12
        self.world._tick_projectiles(self.room, self.now)
        self.assertFalse(self.room["summons"])
        self.assertEqual(self.player["hp"], self.player["maxHp"])

    def test_waves_preserve_surviving_summons_and_death_recharge(self):
        bird = self.cast("lightning_bird")
        bear = self.cast("ice_bear")
        self.world._damage_summon(self.room, bird, 1000)
        self.world._damage_summon(self.room, bear, 30)
        ready = self.player["abilityCooldowns"]["lightning_bird"]
        self.world._damage_enemy(self.room, self.player, self.enemy, 1000)
        self.assertEqual(self.room["stageWave"], 2)
        x = bear["x"]
        self.now += 1
        self.world._tick_summons(self.room, self.now)
        self.assertEqual(bear["x"], x)
        with self.assertRaisesRegex(ValueError, "still alive"):
            self.cast("ice_bear")
        self.now = self.room["waveStartsAt"]
        self.room["waveStartsAt"] = 0
        self.world._spawn_wave(self.room, preserve_players=True)
        self.assertIn(bear, self.room["summons"])
        self.assertEqual(bear["hp"], bear["maxHp"] - 30)
        self.assertEqual(self.player["activeSummons"]["ice_bear"], bear["id"])
        self.assertEqual(self.player["abilityCooldowns"]["lightning_bird"], ready)
        with self.assertRaisesRegex(ValueError, "ready in"):
            self.cast("lightning_bird")

    def test_new_stage_removes_summons_and_starts_ultimate_cooldown(self):
        bird = self.cast("lightning_bird")
        self.cast("ice_bear")
        self.world._damage_summon(self.room, bird, 1000)
        self.assertGreater(self.player["abilityCooldowns"]["lightning_bird"], self.now)
        self.room["puzzleStages"] = []
        self.room["townStages"] = []
        self.world._present_routes(self.room)
        route = self.room["routes"][0]
        route["kind"] = "combat"
        self.room["routeVotes"] = {self.pid: route["id"]}
        self.world._resolve_routes(self.room)
        self.assertEqual(self.room["stage"], 2)
        self.assertFalse(self.room["summons"])
        self.assertFalse(self.player["activeSummons"])
        self.assertEqual(self.player["abilityCooldowns"], {"ice_bear": self.now + 15})
        slots = self.world.state(self.code, self.pid)["abilitySlots"]
        self.assertTrue(all(not slot["summonAlive"] for slot in slots))
        self.assertEqual([slot["cooldownLeft"] for slot in slots], [0, 0, 15])
        self.player["mana"] = 100
        self.assertIsNotNone(self.cast("lightning_bird"))
        with self.assertRaisesRegex(ValueError, "ready in"):
            self.cast("ice_bear")
        self.now += 15
        self.assertIsNotNone(self.cast("ice_bear"))

    def test_summon_damage_tracks_equipped_light_with_equipment_buffs_and_curses(self):
        for empowered in (False, True):
            self.player["toolSlots"] = [{"damage": 9} if empowered else None, None]
            self.player["damageBoost"] = 1.5 if empowered else 1
            self.player["damageBoostUntil"] = self.now + 1000
            self.player["curse"] = {"effect": "weakened"} if empowered else None
            for light_id in ("briar_burst", "thornshot"):
                self.cast(light_id)
                light_damage = self.room["projectiles"][-1]["damage"]
                self.room["projectiles"] = []
                for ability_id in SUMMON_TYPES:
                    with self.subTest(light=light_id, summon=ability_id, empowered=empowered):
                        self.player["mana"] = 100
                        summon = self.cast(ability_id)
                        if ability_id in ("lightning_bird", "fire_wolf"):
                            self.assertEqual(summon["damage"], round(light_damage * 0.9))
                            self.assertLess(summon["damage"], light_damage)
                        else:
                            self.assertEqual(summon["damage"], light_damage * 2)
                        self.world._dismiss_summons(self.room)
                        self.now += 16

    def test_summon_kill_gets_normal_rewards_and_wave_progression(self):
        wolf = self.cast("fire_wolf")
        self.enemy.update(x=wolf["x"] + 10, y=wolf["y"], hp=1)
        self.now += wolf["attackInterval"]+.01
        self.world._tick_summons(self.room, self.now)
        self.assertFalse(self.room["enemies"])
        self.assertGreater(self.room["runes"], 0)
        self.assertEqual(self.room["stageWave"], 2)
        self.assertGreater(self.room["waveStartsAt"], self.now)
        self.assertIn(wolf, self.room["summons"])

    def test_summons_do_not_bypass_party_wipe_and_leave_cleanup(self):
        wolf = self.cast("fire_wolf")
        self.enemy.update(x=wolf["x"] + 10, y=wolf["y"], hp=1)
        self.room["stageWave"] = self.room["stageWaves"]
        self.now += 1
        self.player["status"] = "downed"
        self.player["downedUntil"] = self.now + 8
        self.world.tick()
        self.assertEqual(self.room["phase"], "defeat")
        self.assertFalse(self.room["summons"])
        self.assertFalse(self.player["activeSummons"])
        self.room["phase"] = "combat"
        self.player["status"] = "alive"
        self.player["mana"] = 100
        self.cast("ice_bear")
        self.act("leaveRoom")
        self.assertFalse(self.room["summons"])

    def test_guild_change_dismisses_the_previous_druids_summons(self):
        self.cast("lightning_bird")
        self.world._enter_town(self.room)
        rest_at_bed(self.world, self.room)
        self.player.update(townInterior="guild", x=480, y=220)
        self.act("interact")
        self.act("guildPreview", **{"class": "Knight"})
        self.act("guildChange", abilities=self.player["guildPreview"]["selected"])
        self.assertFalse(self.room["summons"])
        self.assertFalse(self.player["activeSummons"])
        self.assertEqual(self.player["class"], "Knight")


if __name__ == "__main__":
    unittest.main()
