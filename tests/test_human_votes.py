import unittest
from unittest.mock import patch

import progression
from game import ABILITY_SETS, GameWorld


class HumanVoteTests(unittest.TestCase):
    def party(self, count=1):
        world = GameWorld()
        code, host = world.create_room("Host")
        ids = [host] + [world.join_room(code, "Guest")[1] for _ in range(count-1)]
        for pid, hero in zip(ids, ("Knight", "Wizard", "Healer")):
            world.action(code, pid, {"action": "class", "class": hero})
            world.action(code, pid, {"action": "loadout", "abilities": [a[0] for a in ABILITY_SETS[hero][::2]]})
        world.action(code, host, {"action": "runOptions", "companion": True})
        world.action(code, host, {"action": "start"})
        room = world.rooms[code]
        room.update(townStages=[], puzzleStages=[], story={"encountered": True})
        humans = [room["players"][pid] for pid in ids]
        bot = next(p for p in room["players"].values() if p.get("bot"))
        return world, room, humans, bot

    def town(self, world, room, humans, bot):
        world._enter_town(room)
        room["townWelcome"]["done"] = True
        for p in humans: p.update(trainingKnown=True, x=480, y=490)
        bot.update(townInterior="inn", x=260, y=190, townExitReady=False)

    def test_solo_town_vote_leaves_immediately_with_companion_inside_inn(self):
        world, room, humans, bot = self.party()
        self.town(world, room, humans, bot)
        view = world.state(room["code"], humans[0]["id"])
        self.assertEqual((view["activePartySize"], view["townExitTotal"]), (2, 1))
        world.action(room["code"], humans[0]["id"], {"action": "interact"})
        self.assertEqual(room["phase"], "combat")
        self.assertIsNone(bot["townInterior"])
        self.assertEqual(len(world._active_players(room)), 2)

    def test_town_waits_for_other_humans_but_not_offline_humans_or_companion(self):
        world, room, humans, bot = self.party(3)
        self.town(world, room, humans, bot)
        world.action(room["code"], humans[2]["id"], {"action": "disconnect"})
        world._vote_town_exit(room, humans[0])
        self.assertEqual(room["phase"], "town")
        view = world.state(room["code"], humans[0]["id"])
        self.assertEqual((view["townExitVotes"], view["townExitTotal"]), (1, 2))
        world._vote_town_exit(room, humans[1])
        self.assertEqual(room["phase"], "combat")

    def test_fork_counts_only_humans_and_companion_cannot_break_host_tie(self):
        world, room, humans, bot = self.party(2)
        world._present_routes(room); world._enter_fork(room)
        left, right = room["routes"]
        humans[0].update(x=932, y=170); humans[1].update(x=28, y=170)
        room["routeVotes"] = {humans[0]["id"]: right["id"], humans[1]["id"]: left["id"], bot["id"]: left["id"]}
        view = world.state(room["code"], humans[0]["id"])
        self.assertEqual([r["votes"] for r in view["routes"]], [1, 1])
        self.assertEqual(view["activeVoterCount"], 2)
        with patch.object(world, "_advance_stage") as advance:
            world._tick_travel(room)
            self.assertEqual(advance.call_args.args[1]["id"], right["id"])

    def test_route_action_resolves_without_waiting_for_companion_at_edge(self):
        world, room, humans, bot = self.party()
        world._present_routes(room); world._enter_fork(room)
        p = humans[0]; p.update(x=28, y=170)
        bot.update(x=480, y=400)
        world.action(room["code"], p["id"], {"action": "routeVote", "route": room["routes"][0]["id"]})
        self.assertEqual((room["phase"], room["stage"]), ("combat", 2))

    def test_stage_and_story_exits_do_not_wait_for_companion(self):
        world, room, humans, bot = self.party()
        world._present_routes(room); room["forkPending"] = False
        p = humans[0]; p.update(x=480, y=30); bot.update(x=480, y=400)
        view = world.state(room["code"], p["id"])
        self.assertEqual((view["stageExitReady"], view["activeVoterCount"]), (1, 1))
        world._tick_travel(room); self.assertEqual(room["stage"], 2)
        progression.enter_peace(world, room)
        p.update(questAccepted=True, x=480, y=30); bot.update(x=480, y=440)
        progression.tick(world, room, 1000)
        self.assertEqual(room["phase"], "stage_exit")

    def test_companion_alone_cannot_advance_run_or_vote(self):
        world, room, humans, bot = self.party()
        world._present_routes(room); world._enter_fork(room)
        world.action(room["code"], humans[0]["id"], {"action": "disconnect"})
        bot.update(x=28, y=170)
        world.action(room["code"], bot["id"], {"action": "routeVote", "route": room["routes"][0]["id"]})
        world._tick_travel(room); world._resolve_routes(room)
        self.assertEqual((room["phase"], room["stage"]), ("routes", 1))
        self.assertNotIn(bot["id"], room["routeVotes"])
