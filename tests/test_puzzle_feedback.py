import unittest

from game import GameWorld
from puzzles import new_puzzle, player_puzzle_view


class PuzzleFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.world = GameWorld()
        self.code, self.pid = self.world.create_room("Rune tester")
        self.room = self.world.rooms[self.code]
        self.room["phase"] = "puzzle"
        self.room["puzzle"] = new_puzzle([self.pid])
        self.player = self.room["players"][self.pid]
        self.chamber = self.room["puzzle"]["rooms"][self.pid]
        self.wrong = next(r for r in self.chamber["runes"] if r["rune"] != self.chamber["target"])
        self.player.update(x=self.wrong["x"], y=self.wrong["y"])

    def test_standing_on_wrong_rune_keeps_penalty_without_popup(self):
        self.world._tick_puzzle(self.room)
        self.assertEqual(self.chamber["standing"], self.wrong["rune"])
        self.assertEqual(self.room["strainMistakes"], 1)
        self.assertEqual(self.world.state(self.code, self.pid)["privateNotice"], "")

    def test_interacting_on_wrong_rune_does_not_create_popup(self):
        self.world.action(self.code, self.pid, {"action": "interact"})
        self.assertEqual(self.room["strainMistakes"], 1)
        self.assertEqual(self.world.state(self.code, self.pid)["privateNotice"], "")

    def test_reading_totem_does_not_mark_runes_as_totem_locations(self):
        totem = self.chamber["totem"]
        self.player.update(x=totem["x"], y=totem["y"])
        self.world.action(self.code, self.pid, {"action": "interact"})
        self.assertTrue(self.world.state(self.code, self.pid)["puzzle"]["atTotem"])
        self.player.update(x=self.wrong["x"], y=self.wrong["y"])
        view = self.world.state(self.code, self.pid)["puzzle"]
        self.assertFalse(view["atTotem"])
        self.assertEqual(view["clue"], self.chamber["clue"])
        self.assertEqual(view["targetSigil"], self.chamber["target"])
        self.assertEqual(view["standingRune"], self.wrong["rune"])

    def test_totem_view_uses_the_same_interaction_radius_as_server(self):
        totem = self.chamber["totem"]
        view = player_puzzle_view(self.room["puzzle"], self.pid, (totem["x"] + 55, totem["y"]))
        self.assertTrue(view["atTotem"])
