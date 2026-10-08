import unittest

from game import ABILITY_SETS, GameWorld


class DamageFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.world = GameWorld()
        self.code, self.player_id = self.world.create_room("Knight")
        self.world.action(self.code, self.player_id, {"action": "class", "class": "Knight"})
        self.world.action(self.code, self.player_id, {
            "action": "loadout", "abilities": [a[0] for a in ABILITY_SETS["Knight"][::2]],
        })
        self.world.action(self.code, self.player_id, {"action": "start"})
        self.room = self.world.rooms[self.code]
        self.player = self.room["players"][self.player_id]
        self.enemy = self.room["enemies"][0]

    def test_damage_events_are_visible_even_if_hp_is_restored_before_polling(self):
        self.world._damage_enemy(self.room, self.player, self.enemy, 1)
        self.enemy["hp"] = self.enemy["maxHp"]
        self.world._damage_player(self.room, self.enemy, self.player, 5)
        self.player["hp"] = self.player["maxHp"]
        state = self.world.state(self.code, self.player_id)
        self.assertEqual(state["players"][0]["damageTaken"], 1)
        self.assertEqual(state["enemies"][0]["damageTaken"], 1)
        # Reading state never consumes or repeats damage events.
        self.assertEqual(self.world.state(self.code, self.player_id)["players"][0]["damageTaken"], 1)

    def test_repeated_hits_and_downing_are_counted_but_downed_timer_hits_are_not(self):
        self.world._damage_player(self.room, self.enemy, self.player, 1)
        self.world._damage_player(self.room, self.enemy, self.player, 1000)
        self.assertEqual(self.player["damageTaken"], 2)
        self.assertEqual(self.player["status"], "downed")
        self.world._damage_player(self.room, self.enemy, self.player, 1)
        self.assertEqual(self.player["damageTaken"], 2)
        self.assertEqual(self.player["hp"], 0)

    def test_spawn_and_healing_do_not_report_damage(self):
        state = self.world.state(self.code, self.player_id)
        self.assertEqual(state["players"][0]["damageTaken"], 0)
        self.assertTrue(all(e["damageTaken"] == 0 for e in state["enemies"]))
        self.player["hp"] -= 20
        potion = self.world._make_item("healing_draught")
        self.player["inventory"].append(potion)
        self.world.action(self.code, self.player_id, {"action": "useItem", "item": potion["id"]})
        self.assertEqual(self.player["hp"], self.player["maxHp"])
        self.assertEqual(self.world.state(self.code, self.player_id)["players"][0]["damageTaken"], 0)


if __name__ == "__main__":
    unittest.main()
