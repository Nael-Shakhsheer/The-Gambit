from test_support import rest_at_bed
import copy
import math
import random
import tempfile
import unittest
from unittest.mock import patch

from game import ABILITY_SETS, GameWorld, TOWN_GATE
import telemetry
import town_layout


class ProgressionUpdateTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        timer = patch("game.time.monotonic", side_effect=lambda: self.now)
        timer.start()
        self.addCleanup(timer.stop)

    def party(self, heroes=("Knight", "Healer"), **kwargs):
        world = GameWorld(**kwargs)
        code, host = world.create_room("Player 1")
        ids = [host] + [world.join_room(code, f"Player {i+2}")[1] for i in range(len(heroes)-1)]
        for pid, hero in zip(ids, heroes):
            world.action(code, pid, {"action": "class", "class": hero})
            world.action(code, pid, {"action": "loadout", "abilities": [a[0] for a in ABILITY_SETS[hero][::2]]})
        world.action(code, host, {"action": "start"})
        world.rooms[code]["story"]["encountered"] = True
        return world, world.rooms[code], ids

    def test_overall_totals_include_current_stage_summons_and_actual_hp(self):
        world, room, ids = self.party()
        p = room["players"][ids[0]]
        enemy = room["enemies"][0]
        enemy["hp"] = 9
        world._damage_enemy(room, p, enemy, 100, summon_id="dead-bird")
        world._damage_enemy(room, p, enemy, 100)  # Stale target cannot be counted twice.
        p["hp"] = 6
        world._damage_player(room, {}, p, 100)
        first = world.run_stats(room["code"], ids[0])[0]
        self.assertEqual(first, {"name": "Player 1", "class": "Knight", "damageDealt": 9,
                                "damageTaken": 6, "revives": 0, "deaths": 0, "kills": 1})
        world._finish_stage_stats(room, "cleared")
        room["stage"] += 1
        world._spawn_wave(room)
        world._damage_enemy(room, p, room["enemies"][0], 3)
        self.assertEqual(world.run_stats(room["code"], ids[0])[0]["damageDealt"], 12)

    def test_rescues_and_actual_deaths_count_once_per_life(self):
        world, room, ids = self.party()
        p, healer = [room["players"][pid] for pid in ids]
        for enemy in room["enemies"]:
            enemy["stunUntil"] = self.now + 100
        p.update(status="downed", hp=0, downedUntil=self.now+8)
        healer.update(x=p["x"], y=p["y"])
        world.action(room["code"], healer["id"], {"action": "revive"})
        self.now += 1
        world.tick()
        self.assertEqual(world.run_stats(room["code"], ids[0])[1]["revives"], 1)
        self.assertEqual(world.run_stats(room["code"], ids[0])[0]["deaths"], 0)
        p.update(status="fallen", hp=0)  # Legacy fallen heroes remain recoverable.
        world._record_death(room, p)
        healer["abilities"][1] = "quick_revival"
        world._cast_ability(room, healer, 1)  # Quick Revival rescues a fallen hero too.
        self.assertEqual(world.run_stats(room["code"], ids[0])[1]["revives"], 2)
        p.update(status="downed", hp=0)
        healer.update(status="downed", hp=0)
        world._check_party_wipe(room)
        world._check_party_wipe(room)
        totals = world.run_stats(room["code"], ids[0])
        self.assertEqual([row["deaths"] for row in totals], [2, 1])

    def test_downed_allies_have_no_expiry_and_can_be_revived_after_a_long_wait(self):
        world, room, ids = self.party()
        p, healer = [room["players"][pid] for pid in ids]
        for enemy in room["enemies"]: enemy["stunUntil"] = self.now+100
        world._damage_player(room, {}, p, 10000)
        self.assertEqual(p["downedUntil"], 0)
        p["downedUntil"] = self.now-1  # Old timer values must also be ignored.
        self.now += 60; world.tick()
        self.assertEqual(p["status"], "downed")
        self.assertEqual(world.run_stats(room["code"], ids[0])[0]["deaths"], 0)
        self.assertNotIn("reviveSeconds", world.state(room["code"], ids[0])["players"][0])
        healer.update(x=p["x"], y=p["y"])
        world.action(room["code"], healer["id"], {"action": "revive"})
        self.now += 1; world.tick()
        self.assertEqual(p["status"], "alive")

    def test_chest_animation_is_private_for_pending_loot_and_finished_shares(self):
        world, room, ids = self.party()
        room.update(phase="chest", chest={"x":480,"y":270,"decisions":{},"runesAwarded":False})
        p, q = [room["players"][pid] for pid in ids]
        for member in (p,q): member.update(x=480,y=270)
        p["inventory"] = [world._make_item("healing_draught") for _ in range(10)]
        with patch("game.random.random", return_value=1), patch.object(world,"_roll_chest_outcome",return_value="item"):
            world.action(room["code"],p["id"],{"action":"openChest"})
        self.assertTrue(p["chestReward"])
        self.assertTrue(room["chest"]["runesAwarded"])
        self.assertTrue(world.state(room["code"],p["id"])["chest"]["opened"])
        self.assertFalse(world.state(room["code"],q["id"])["chest"]["opened"])
        world.action(room["code"],p["id"],{"action":"chestClaim","replace":p["inventory"][0]["id"]})
        self.assertTrue(world.state(room["code"],p["id"])["chest"]["opened"])
        self.assertFalse(world.state(room["code"],q["id"])["chest"]["opened"])
        self.assertNotIn("opened",room["chest"])

    def test_team_revive_counts_all_rescued_allies(self):
        world, room, ids = self.party(("Healer", "Knight", "Druid"))
        healer = room["players"][ids[0]]
        # Locate the actual team-revive ability instead of depending on its label.
        healer["abilities"][2] = next(a[0] for a in ABILITY_SETS["Healer"] if a[3] == "team_revive")
        healer["abilityCooldowns"] = {}
        for pid in ids[1:]:
            room["players"][pid].update(status="downed", hp=0)
        world._cast_ability(room, healer, 2)
        self.assertEqual(world.run_stats(room["code"], ids[0])[0]["revives"], 2)

    def test_overall_stats_and_town_scenery_survive_disk_restore_and_wipe(self):
        with tempfile.TemporaryDirectory() as directory:
            world, room, ids = self.party(storage_dir=directory)
            telemetry.count(room, ids[0], "kills", 4)
            world._enter_town(room)
            rest_at_bed(world, room)
            restored = GameWorld(storage_dir=directory)
            self.assertEqual(restored.run_stats(room["code"], ids[0])[0]["kills"], 4)
            view = restored.state(room["code"], ids[0])
            self.assertEqual(view["townPaths"], room["townPaths"])
            self.assertEqual(view["townVillagers"], room["townVillagers"])
            room.update(phase="defeat")
            telemetry.count(room, ids[0], "kills", 2)
            world.action(room["code"], ids[0], {"action": "checkpointResume"})
            self.assertEqual(world.run_stats(room["code"], ids[0])[0]["kills"], 6)
            self.assertEqual(room["townsVisited"], 1)

    def test_fork_coin_flip_is_once_per_transition_and_towns_are_direct(self):
        for coin, phase in ((.499, "routes"), (.5, "combat")):
            world, room, ids = self.party(("Knight",))
            room.update(townStages=[], puzzleStages=[])
            with patch("game.random.random", return_value=coin) as roll:
                world._present_routes(room)
                roll.assert_called_once()
            for _ in range(3):
                world.state(room["code"], ids[0])
            room["players"][ids[0]].update(x=480, y=30)
            world._tick_travel(room)
            self.assertEqual(room["phase"], phase)
        world, room, ids = self.party(("Knight",))
        room.update(townStages=[room["stage"]+1], puzzleStages=[])
        with patch("game.random.random") as roll:
            world._present_routes(room)
            roll.assert_not_called()
        self.assertFalse(room["forkPending"])
        self.assertTrue(all(r["kind"] != "town" for r in room["routes"]))
        room["players"][ids[0]].update(x=480, y=30)
        world._tick_travel(room)
        self.assertEqual(room["phase"], "town")
        self.assertEqual(room["townsVisited"], 1)

    def test_full_pouch_can_swap_any_tool_kind_and_all_utility_slots(self):
        world, room, ids = self.party(("Knight",))
        p = room["players"][ids[0]]
        for slot in range(2):
            p["toolSlots"][slot] = world._make_item("iron_sword")
            incoming = world._make_item("oakguard_vest")
            p["inventory"] = [incoming] + [world._make_item("mana_draught") for _ in range(9)]
            old = p["toolSlots"][slot]
            before = {item["id"] for item in p["inventory"]+[old]}
            world.action(room["code"], ids[0], {"action": "equipItem", "slot": slot, "item": incoming["id"]})
            self.assertEqual(p["toolSlots"][slot], incoming)
            self.assertEqual(len(p["inventory"]), 10)
            self.assertEqual({item["id"] for item in p["inventory"]+[incoming]}, before)
        for slot in range(3):
            p["utilitySlots"][slot] = world._make_item("mana_draught")
            incoming = world._make_item("healing_draught")
            p["inventory"] = [incoming] + [world._make_item("mana_draught") for _ in range(9)]
            old = p["utilitySlots"][slot]
            world.action(room["code"], ids[0], {"action": "equipItem", "slot": slot, "item": incoming["id"]})
            self.assertEqual(p["utilitySlots"][slot], incoming)
            self.assertIn(old, p["inventory"])
            self.assertEqual(len(p["inventory"]), 10)

    def test_towns_have_varied_connected_roads_and_noninteractive_villagers(self):
        signatures = set()
        for seed in range(40):
            village = town_layout.generate(seed)
            houses = village["townLayout"]
            signatures.add(tuple(sorted((h["x"], h["y"]) for h in houses)))
            ends = {tuple(path[-1]) for path in village["townPaths"]}
            for h in houses:
                self.assertIn((h["x"], h["y"]+47), ends)
            self.assertEqual(len(village["townVillagers"]), 12)
            for v in village["townVillagers"]:
                self.assertTrue(town_layout.clear(houses, v["x"], v["y"], 28))
                self.assertNotIn("service", v)
        self.assertEqual(len(signatures), 40)
        world, room, ids = self.party(("Knight",))
        world._enter_town(room)
        rest_at_bed(world, room)
        p = room["players"][ids[0]]
        v = room["townVillagers"][0]
        p.update(x=v["x"], y=v["y"])
        self.assertIsNone(world._nearby_npc(room, p))

    def test_town_visits_increase_every_wave_without_compounding_each_spawn(self):
        world, room, ids = self.party(("Knight",))
        room.update(stage=4, stageWave=1, miniBossStages=[], bossStages=[], assassinationStage=None)
        variants = []
        for visits in (0, 1, 2, 1):
            room["townsVisited"] = visits
            random.seed(920)
            world._spawn_wave(room, preserve_players=True)
            variants.append(copy.deepcopy(room["enemies"]))
        for base, one, two, repeat in zip(*variants):
            self.assertAlmostEqual(one["maxHp"], base["maxHp"]*1.25, delta=1.25)
            self.assertAlmostEqual(two["maxHp"], base["maxHp"]*1.5, delta=1.5)
            self.assertAlmostEqual(one["damage"], base["damage"]*1.2, delta=1.2)
            self.assertAlmostEqual(one["speed"], base["speed"]*1.1)
            self.assertAlmostEqual(one["attackRate"], base["attackRate"]*1.12)
            self.assertEqual(one["maxHp"], repeat["maxHp"])

    def test_empowered_and_squadron_enemies_receive_elite_boost(self):
        for encounter in ("empowered", "squadron"):
            world, room, _ = self.party(("Knight",))
            room.update(stage=4, stageWave=2, stageWaves=2, miniBossStages=[4], bossStages=[], assassinationStage=None)
            choose = lambda values: encounter if "empowered" in values else values[0]
            with patch("game.random.choice", side_effect=choose):
                world._spawn_wave(room)
            self.assertEqual(room["encounterType"], "mini_boss")
            for enemy in room["enemies"]:
                self.assertTrue(enemy["elite"])
                self.assertAlmostEqual(enemy["attackRate"], math.sqrt(1.25)*1.25)

    def test_elite_attack_rate_causes_earlier_attack_in_actual_ai(self):
        intervals = []
        for rate in (1, 1.25):
            world, room, ids = self.party(("Knight",))
            p = room["players"][ids[0]]
            e = room["enemies"][0]
            room["enemies"] = [e]
            e.update(x=p["x"]+10, y=p["y"], **{"class": "Knight"}, lastAttack=self.now-1.7,
                     attackRate=rate, elite=rate>1, stunUntil=0, combatRole="bruiser", roleReadyAt=0)
            world.tick()
            self.assertIsNotNone(e.get("roleAttack"))
            intervals.append(e["roleReadyAt"]-self.now)
        self.assertAlmostEqual(intervals[1], intervals[0]/1.25)


if __name__ == "__main__":
    unittest.main()
