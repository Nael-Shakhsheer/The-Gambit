from test_support import rest_at_bed
import copy
import unittest
from collections import Counter
from unittest.mock import patch

from game import ABILITY_SETS, CLASSES, TOWNS, GameWorld


class GuildTests(unittest.TestCase):
    def setUp(self):
        self.world = GameWorld()
        self.code, self.host = self.world.create_room("Host")
        _, self.friend = self.world.join_room(self.code, "Friend")
        for player_id, hero in ((self.host, "Knight"), (self.friend, "Wizard")):
            self.world.action(self.code, player_id, {"action": "class", "class": hero})
            selected = [a[0] for a in ABILITY_SETS[hero][::2]]
            self.world.action(self.code, player_id, {"action": "loadout", "abilities": selected})
        self.act("start")
        self.room = self.world.rooms[self.code]
        self.player = self.room["players"][self.host]
        self.world._enter_town(self.room, TOWNS[0])
        rest_at_bed(self.world, self.room)

    def act(self, action, **payload):
        self.world.action(self.code, self.host, {"action": action, **payload})

    def talk(self, player_id=None):
        player_id = player_id or self.host
        player = self.room["players"][player_id]
        guild = next(h for h in self.room["townLayout"] if h["id"] == "guild")
        player.update(townInterior=None, x=guild["x"], y=guild["y"] + 47)
        self.world.action(self.code, player_id, {"action": "interact"})
        self.assertEqual(player["townInterior"], "guild")
        player.update(x=480, y=220)
        self.world.action(self.code, player_id, {"action": "interact"})
        self.assertEqual(player["townInteraction"], "guildmaster")

    def test_every_town_has_accessible_guild_and_spawn(self):
        guild_locations = set()
        for town in TOWNS:
            for _ in range(20):
                self.world._enter_town(self.room, town)
                rest_at_bed(self.world, self.room)
                self.assertEqual(len(self.room["townLayout"]), 6)
                self.assertEqual(sum(h["service"] == "guildmaster" for h in self.room["townLayout"]), 1)
                guild = next(h for h in self.room["townLayout"] if h["id"] == "guild")
                guild_locations.add((round(guild["x"] / 100), round(guild["y"] / 100)))
                for h in self.room["townLayout"]:
                    self.assertTrue(self.world._town_walkable(self.room, h["x"], h["y"] + 47))
                for p in self.room["players"].values():
                    self.assertTrue(self.world._town_walkable(self.room, p["x"], p["y"]))
                for path in self.room["townPaths"]:
                    for (ax, ay), (bx, by) in zip(path, path[1:]):
                        for step in range(21):
                            self.assertTrue(self.world._town_walkable(self.room, ax + (bx-ax)*step/20, ay + (by-ay)*step/20))
        self.assertGreater(len(guild_locations), 1)

    def test_cancel_both_screens_does_not_change_class_or_spend_allowance(self):
        before = copy.deepcopy(self.player["abilities"])
        self.talk()
        self.act("closeShop")
        self.talk()
        self.act("guildPreview", **{"class": "Rogue"})
        self.act("guildBack")
        self.assertIsNone(self.player["guildPreview"])
        self.act("guildPreview", **{"class": "Rogue"})
        self.act("closeShop")
        self.assertIsNone(self.player["guildPreview"])
        self.assertFalse(self.player["classChangeUsed"])
        self.assertEqual(self.player["class"], "Knight")
        self.assertEqual(self.player["abilities"], before)

    def test_shuffled_six_skills_are_class_specific_and_stable_during_polling(self):
        self.talk()
        for hero in CLASSES:
            if hero in ("Knight", "Wizard"):
                continue
            with patch("game.random.shuffle", side_effect=lambda values: values.reverse()):
                self.act("guildPreview", **{"class": hero})
            preview = copy.deepcopy(self.player["guildPreview"])
            self.assertEqual(len(preview["options"]), 6)
            self.assertEqual(Counter(a["attackType"] for a in preview["options"]), {"light": 2, "special": 2, "ultimate": 2})
            self.assertEqual({a["id"] for a in preview["options"]}, {a[0] for a in ABILITY_SETS[hero]})
            self.assertEqual(preview["selected"], [a[0] for a in ABILITY_SETS[hero][1::2]])
            self.act("guildPreview", **{"class": hero})
            for _ in range(3):
                self.assertEqual(self.world.state(self.code, self.host)["guildPreview"], preview)
            self.assertFalse(self.player["classChangeUsed"])

    def test_server_rejects_remote_current_taken_and_invalid_selections(self):
        with self.assertRaisesRegex(ValueError, "Guildmaster"):
            self.act("guildPreview", **{"class": "Rogue"})
        self.talk()
        for hero, reason in (("Knight", "current"), ("Wizard", "taken"), ("unknown", "Unknown")):
            with self.assertRaisesRegex(ValueError, reason):
                self.act("guildPreview", **{"class": hero})
        self.act("guildPreview", **{"class": "Rogue"})
        for skills in (None, [], ["backstab"] * 3, ["backstab", "fan_of_blades", "vanish"], [{}, 1, None]):
            with self.assertRaisesRegex(ValueError, "Choose one"):
                self.act("guildChange", abilities=skills)
        self.assertFalse(self.player["classChangeUsed"])
        self.player.update(x=480, y=405)
        with self.assertRaisesRegex(ValueError, "Guildmaster"):
            self.act("guildChange", abilities=self.player["guildPreview"]["selected"])

    def test_change_keeps_items_and_is_once_per_player_across_towns_and_wipes(self):
        self.player["inventory"] = [self.world._make_item("mana_draught")]
        self.player["toolSlots"][0] = self.world._make_item("iron_sword")
        gear = copy.deepcopy(self.player["toolSlots"])
        items = copy.deepcopy(self.player["inventory"])
        self.player["curse"] = {"effect": "weakened", "stages": 3}
        self.talk()
        self.player["hp"] = 75
        self.act("guildPreview", **{"class": "Rogue"})
        selected = self.player["guildPreview"]["selected"].copy()
        self.act("guildChange", abilities=selected[::-1])
        self.assertEqual(self.player["class"], "Rogue")
        self.assertEqual((self.player["hp"], self.player["maxHp"]), (40, 80))
        self.assertEqual(self.player["abilities"], selected)
        self.assertEqual(self.player["inventory"], items)
        self.assertEqual(self.player["toolSlots"], gear)
        self.assertEqual(self.player["curse"]["stages"], 3)
        self.assertTrue(self.player["classChangeUsed"])
        self.assertFalse(self.room["players"][self.friend]["classChangeUsed"])
        self.assertTrue(any(s["key"] == "shadow_blades" for s in self.player["shopStock"]))
        self.room["phase"] = "defeat"
        self.act("checkpointResume")
        self.assertEqual(self.player["class"], "Rogue")
        self.assertTrue(self.player["classChangeUsed"])
        self.assertEqual(self.player["innFloor"], 2)
        self.assertEqual(self.player["townInterior"], "inn")
        self.world._enter_town(self.room, TOWNS[1])
        rest_at_bed(self.world, self.room)
        self.talk()
        with self.assertRaisesRegex(ValueError, "once"):
            self.act("guildPreview", **{"class": "Knight"})
        self.room["phase"] = "combat"
        self.world._spawn_regular_wave(self.room)
        self.player["hp"] = 30
        self.player["x"], self.player["y"] = 480, 300
        for enemy in self.room["enemies"]:
            enemy["x"], enemy["y"] = 500, 300
        self.world._cast_ability(self.room, self.player, 0)

    def test_two_players_cannot_confirm_the_same_hero(self):
        self.talk()
        self.talk(self.friend)
        self.act("guildPreview", **{"class": "Healer"})
        self.world.action(self.code, self.friend, {"action": "guildPreview", "class": "Healer"})
        self.act("guildChange", abilities=self.player["guildPreview"]["selected"])
        friend = self.room["players"][self.friend]
        with self.assertRaisesRegex(ValueError, "taken"):
            self.world.action(self.code, self.friend, {"action": "guildChange", "abilities": friend["guildPreview"]["selected"]})
        self.assertEqual(friend["class"], "Wizard")
        self.assertFalse(friend["classChangeUsed"])
        self.world.action(self.code, self.friend, {"action": "guildPreview", "class": "Knight"})
        self.world.action(self.code, self.friend, {"action": "guildChange", "abilities": friend["guildPreview"]["selected"]})
        self.assertEqual(friend["class"], "Knight")
        self.assertTrue(friend["classChangeUsed"])


if __name__ == "__main__":
    unittest.main()
