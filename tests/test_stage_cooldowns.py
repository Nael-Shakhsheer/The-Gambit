from test_support import rest_at_bed
import unittest
from unittest.mock import patch

from game import ABILITY_SETS, TOWN_GATE, GameWorld
from puzzles import new_puzzle


class StageCooldownTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        timer = patch("game.time.monotonic", side_effect=lambda: self.now)
        timer.start()
        self.addCleanup(timer.stop)

    def start(self, hero, ultimate):
        world = GameWorld()
        code, pid = world.create_room("Cooldown tester")
        world.action(code, pid, {"action": "class", "class": hero})
        abilities = [next(a[0] for a in ABILITY_SETS[hero] if a[7] == category)
                     for category in ("light", "special")] + [ultimate[0]]
        world.action(code, pid, {"action": "loadout", "abilities": abilities})
        world.action(code, pid, {"action": "start"})
        room = world.rooms[code]
        return world, room, room["players"][pid]

    def test_every_ultimate_starts_on_cooldown_and_waves_do_not_restart_it(self):
        for hero, abilities in ABILITY_SETS.items():
            for ultimate in (a for a in abilities if a[7] == "ultimate"):
                with self.subTest(hero=hero, ultimate=ultimate[0]):
                    world, room, player = self.start(hero, ultimate)
                    ready = self.now + ultimate[6]
                    self.assertEqual(player["abilityCooldowns"], {ultimate[0]: ready})
                    self.assertEqual([s["cooldownLeft"] for s in world._ability_slots(player)], [0, 0, ultimate[6]])
                    with self.assertRaisesRegex(ValueError, "ready in"):
                        world.action(room["code"], player["id"], {"action": "ability", "slot": 3})
                    self.assertEqual(player["mana"], 100)
                    self.now += 3
                    room["stageWave"] += 1
                    world._spawn_wave(room, preserve_players=True)
                    self.assertEqual(player["abilityCooldowns"][ultimate[0]], ready)
                    self.now = ready
                    self.assertEqual(world._ability_slots(player)[2]["cooldownLeft"], 0)
                    room["puzzleStages"] = []
                    room["townStages"] = []
                    world._present_routes(room)
                    route = room["routes"][0]
                    route["kind"] = "combat"
                    room["routeVotes"] = {player["id"]: route["id"]}
                    world._resolve_routes(room)
                    self.assertEqual(room["stage"], 2)
                    self.assertEqual(player["abilityCooldowns"], {ultimate[0]: self.now + ultimate[6]})

    def test_combat_after_puzzle_starts_with_full_ultimate_cooldown(self):
        ultimate = next(a for a in ABILITY_SETS["Druid"] if a[0] == "ice_bear")
        world, room, player = self.start("Druid", ultimate)
        self.now += 100
        room["phase"] = "puzzle"
        room["puzzle"] = new_puzzle([player["id"]])
        chamber = room["puzzle"]["rooms"][player["id"]]
        correct = next(r for r in chamber["runes"] if r["rune"] == chamber["target"])
        player.update(x=correct["x"], y=correct["y"])
        world._tick_puzzle(room)
        self.assertEqual(room["phase"], "combat")
        self.assertEqual(player["abilityCooldowns"], {"ice_bear": self.now + 15})

    def test_leaving_town_starts_with_full_ultimate_cooldown(self):
        ultimate = next(a for a in ABILITY_SETS["Knight"] if a[0] == "earthshaker")
        world, room, player = self.start("Knight", ultimate)
        self.now += 100
        world._enter_town(room)
        rest_at_bed(world, room)
        player.update(x=TOWN_GATE[0], y=TOWN_GATE[1])
        world.action(room["code"], player["id"], {"action": "townContinue"})
        self.assertEqual(room["phase"], "combat")
        self.assertEqual(player["abilityCooldowns"], {"earthshaker": self.now + ultimate[6]})
