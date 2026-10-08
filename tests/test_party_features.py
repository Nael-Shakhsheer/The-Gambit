from test_support import rest_at_bed
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import ABILITY_SETS, GameWorld, TOWN_GATE
from puzzles import player_puzzle_view
from run_storage import RunStorage


class PartyFeatureTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        timer = patch("game.time.monotonic", side_effect=lambda: self.now)
        timer.start()
        self.addCleanup(timer.stop)

    def party(self, classes=("Druid", "Knight"), **kwargs):
        world = GameWorld(**kwargs)
        code, host = world.create_room("Player 1")
        ids = [host]
        for i in range(1, len(classes)):
            ids.append(world.join_room(code, f"Player {i + 1}")[1])
        for pid, hero in zip(ids, classes):
            world.action(code, pid, {"action": "class", "class": hero})
            selected = [next(a[0] for a in ABILITY_SETS[hero] if a[7] == kind) for kind in ("light", "special", "ultimate")]
            world.action(code, pid, {"action": "loadout", "abilities": selected})
        world.action(code, host, {"action": "start"})
        world.rooms[code]["story"]["encountered"] = True
        return world, world.rooms[code], ids

    def test_atomic_checkpoint_restores_identity_inventory_guild_and_schedule(self):
        with tempfile.TemporaryDirectory() as directory:
            world, room, ids = self.party(storage_dir=directory)
            world._enter_town(room)
            rest_at_bed(world, room)
            p = room["players"][ids[0]]
            p["inventory"] = [world._make_item("healing_draught")]
            p["classChangeUsed"] = True
            room["runes"] = 123
            world._save_checkpoint(room)
            checkpoint = Path(directory) / "checkpoints" / (room["code"] + ".json")
            before = checkpoint.read_bytes()
            with patch("run_storage.os.replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    world.storage.save({**room, "runes": 999})
            self.assertEqual(checkpoint.read_bytes(), before)
            room["runes"] = 999
            room["stage"] += 2  # Combat after the inn must not leak into recovery.
            restored = GameWorld(storage_dir=directory, disconnect_timeout=15)
            view = restored.state(room["code"], ids[0])
            self.assertEqual(view["phase"], "town")
            self.assertEqual(view["runes"], 123)
            self.assertEqual(view["inventory"], p["inventory"])
            self.assertTrue(view["classChangeUsed"])
            self.assertEqual(view["townHouses"], room["townLayout"])
            self.assertEqual(view["stage"], room["checkpoint"]["stage"])
            self.assertEqual(view["activePartySize"], 1)
            self.assertFalse(view["summons"])
            self.assertGreater(view["checkpointSavedAt"], 0)
            restored.state(room["code"], ids[1])
            self.assertEqual(len(restored._active_players(restored.rooms[room["code"]])), 2)

    def test_corrupt_checkpoint_is_preserved_without_preventing_other_restores(self):
        with tempfile.TemporaryDirectory() as directory:
            world, room, _ = self.party(storage_dir=directory)
            world._enter_town(room)
            rest_at_bed(world, room)
            broken = Path(directory) / "checkpoints" / "BAD.json"
            broken.write_text("{invalid")
            with self.assertLogs(level="ERROR"):
                restored = GameWorld(storage_dir=directory)
            self.assertIn(room["code"], restored.rooms)
            self.assertEqual(broken.read_text(), "{invalid")

    def test_disconnect_does_not_block_exit_chest_or_town_vote(self):
        for phase in ("stage_exit", "chest", "town"):
            with self.subTest(phase=phase):
                world, room, ids = self.party(disconnect_timeout=15)
                first, second = [room["players"][pid] for pid in ids]
                if phase == "town":
                    world._enter_town(room)
                    rest_at_bed(world, room)
                    first.update(x=TOWN_GATE[0], y=TOWN_GATE[1], townExitReady=True)
                elif phase == "chest":
                    room.update(phase="chest", chest={"decisions": {ids[0]: "opened"}})
                else:
                    world._present_routes(room)
                    first.update(x=480, y=30)
                second["lastSeen"] = self.now - 16
                world.tick()
                self.assertFalse(second["connected"])
                self.assertNotEqual(room["phase"], phase)

    def test_pause_freezes_timers_and_reconnect_keeps_player_identity(self):
        world, room, ids = self.party(("Druid",), disconnect_timeout=15)
        p = room["players"][ids[0]]
        ready = p["abilityCooldowns"]["ice_bear"]
        world.action(room["code"], ids[0], {"action": "disconnect"})
        positions = [(e["x"], e["y"]) for e in room["enemies"]]
        self.now += 120
        world.tick()
        self.assertEqual(positions, [(e["x"], e["y"]) for e in room["enemies"]])
        view = world.state(room["code"], ids[0])
        self.assertEqual(view["you"], ids[0])
        self.assertEqual(p["abilityCooldowns"]["ice_bear"], ready + 120)
        self.assertEqual(room["combatStats"]["startedAt"], 1120)

    def test_offline_host_transfers_and_stale_input_stops(self):
        world, room, ids = self.party(disconnect_timeout=15)
        first, second = [room["players"][pid] for pid in ids]
        first.update(lastSeen=self.now - 16)
        second.update(dx=1, attacking=True, lastInputAt=self.now - 3)
        world.tick()
        self.assertEqual(room["host"], ids[1])
        self.assertEqual(second["dx"], 0)
        self.assertFalse(second["attacking"])

    def test_coop_clues_are_crossed_and_individual_answers_are_private(self):
        world, room, ids = self.party()
        room.update(phase="puzzle", puzzle=world._new_puzzle(room))
        a, b = [room["puzzle"]["rooms"][pid] for pid in ids]
        view = player_puzzle_view(room["puzzle"], ids[0], (a["totem"]["x"], a["totem"]["y"]))
        self.assertEqual(view["targetSigil"], b["target"])
        self.assertEqual(view["clueForName"], "Player 2")
        self.assertIsNone(view["isCorrect"])
        room["players"][ids[1]].update(x=480, y=468)  # Not already standing on a randomly placed rune.
        wrong = next(r for r in a["runes"] if r["rune"] != a["target"])
        room["players"][ids[0]].update(x=wrong["x"], y=wrong["y"])
        world.action(room["code"], ids[0], {"action": "interact"})
        world._tick_puzzle(room)
        self.assertEqual(room["strainMistakes"], 0)
        correct_b = next(r for r in b["runes"] if r["rune"] == b["target"])
        room["players"][ids[1]].update(x=correct_b["x"], y=correct_b["y"])
        world._tick_puzzle(room)
        self.assertEqual(room["strainMistakes"], 1)
        self.assertIn("group answer", room["chat"][-1]["message"])
        self.now += 10
        world._tick_puzzle(room)
        self.assertEqual(room["strainMistakes"], 1)  # No repeating penalty for waiting.
        for pid in ids:
            chamber = room["puzzle"]["rooms"][pid]
            rune = next(r for r in chamber["runes"] if r["rune"] == chamber["target"])
            room["players"][pid].update(x=rune["x"], y=rune["y"])
        world._tick_puzzle(room)
        self.assertEqual(room["phase"], "combat")

    def test_coop_clues_reassign_to_solo_and_back_on_reconnect(self):
        world, room, ids = self.party()
        room.update(phase="puzzle", puzzle=world._new_puzzle(room))
        world.action(room["code"], ids[1], {"action": "disconnect"})
        chamber = room["puzzle"]["rooms"][ids[0]]
        self.assertEqual(chamber["clueFor"], ids[0])
        world.state(room["code"], ids[1])
        self.assertEqual(chamber["clueFor"], ids[1])

    def test_contribution_counts_actual_damage_and_survival_across_waves(self):
        with tempfile.TemporaryDirectory() as directory:
            world, room, ids = self.party(("Druid",), storage_dir=directory)
            p = room["players"][ids[0]]
            world._summon_companion(room, p, "fire_wolf", 10, self.now)
            summon = room["summons"][0]
            enemy = room["enemies"][0]
            enemy["hp"] = 500
            world._damage_enemy(room, p, enemy, 15)
            world._damage_enemy(room, p, enemy, 10, summon["id"])
            world._damage_player(room, enemy, p, 8)
            self.now += 3
            world._damage_summon(room, summon, 1000)
            self.assertEqual(room["combatStats"]["players"][ids[0]]["summonDamageTaken"], summon["maxHp"])
            world._spawn_wave(room, preserve_players=True)
            self.now += 2
            room["stageWave"] = room["stageWaves"]
            room["enemies"] = [copy.deepcopy(enemy)]
            room["enemies"][0]["hp"] = 7
            world._damage_enemy(room, p, room["enemies"][0], 1000)
            report = room["stageReports"][-1]
            row = report["players"][0]
            self.assertEqual(row["heroDamage"], 22)
            self.assertEqual(row["summonDamage"], 10)
            self.assertEqual(row["heroDamageTaken"], 8)
            self.assertEqual(row["summonSeconds"], 3)
            self.assertEqual(row["summonDeaths"], 1)
            self.assertTrue(row["endedBeforeUltimate"])
            self.assertEqual(report["seconds"], 5)
            self.assertEqual(json.loads((Path(directory) / "balance.jsonl").read_text()), report)

    def test_projectile_keeps_summon_credit_after_bird_death(self):
        world, room, ids = self.party(("Druid",))
        p = room["players"][ids[0]]
        world._summon_companion(room, p, "lightning_bird", 10, self.now)
        bird = room["summons"][0]
        target = room["enemies"][0]
        target.update(x=bird["x"] + 60, y=bird["y"] - 8, hp=500)
        room["enemies"] = [target]
        self.now += bird["attackInterval"]+.01
        world._tick_summons(room, self.now)
        world._damage_summon(room, bird, 1000)
        for _ in range(8):
            self.now += .05
            world._tick_projectiles(room, self.now)
        row = room["combatStats"]["players"][ids[0]]
        self.assertEqual(row["summonDamage"], 10)
        self.assertEqual(row["heroDamage"], 0)

    def test_ping_validation_throttle_and_expiry(self):
        world, room, ids = self.party()
        act = lambda **payload: world.action(room["code"], ids[0], {"action": "ping", **payload})
        with self.assertRaises(ValueError):
            act(kind="enemy", targetId="missing")
        act(kind="help")
        act(kind="gather")
        self.assertEqual(len(world.state(room["code"], ids[1])["pings"]), 1)
        self.now += 2
        act(kind="enemy", targetId=room["enemies"][0]["id"])
        self.assertEqual(len(room["pings"]), 2)
        self.now += 6
        self.assertFalse(world.state(room["code"], ids[1])["pings"])

    def test_hold_attack_repeats_equipped_light_at_its_cooldown_then_stops(self):
        world, room, ids = self.party(("Knight",))
        player = room["players"][ids[0]]
        enemy = room["enemies"][0]
        enemy.update(x=player["x"], y=player["y"] - 80, hp=1000, maxHp=1000, speed=0)
        room["enemies"] = [enemy]
        world.action(room["code"], ids[0], {"action": "input", "attack": True})
        first_hp = enemy["hp"]
        self.assertEqual(first_hp, 981)  # Equipped Shield Bash: round(18 * 1.05).
        self.assertGreater(enemy["stunUntil"], self.now)
        self.now += .2
        world.tick()
        self.assertEqual(enemy["hp"], first_hp)
        self.now += .26
        world.tick()
        self.assertEqual(enemy["hp"], first_hp - 19)
        world.action(room["code"], ids[0], {"action": "input", "attack": False})
        self.now += .6
        world.tick()
        self.assertEqual(enemy["hp"], first_hp - 19)

    def test_rapid_tap_still_attacks_and_hold_waits_for_targets(self):
        world, room, ids = self.party(("Knight",))
        player = room["players"][ids[0]]
        enemy = room["enemies"][0]
        room["enemies"] = [enemy]
        enemy.update(x=player["x"], y=player["y"] - 80, hp=1000, speed=0)
        for attack in (True, False):
            world.action(room["code"], ids[0], {"action": "input", "attack": attack})
        self.assertEqual(enemy["hp"], 981)
        self.now += .5
        enemy["y"] = 30
        world.action(room["code"], ids[0], {"action": "input", "attack": True})
        self.assertEqual(enemy["hp"], 981)
        enemy["y"] = player["y"] - 80
        world.tick()
        self.assertEqual(enemy["hp"], 962)


if __name__ == "__main__":
    unittest.main()
