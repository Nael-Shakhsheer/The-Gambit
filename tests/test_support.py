"""Shared setup for older combat tests entering a fully visited inn."""
import progression
import time


def finish_dialogue(world, room, player):
    while player.get("dialogue"):
        d = player["dialogue"]
        world.action(room["code"], player["id"], {"action": "dialogueNext", "id": d["id"], "page": d["page"]})


def rest_at_bed(world, room):
    if room.get("townWelcome") and not room["townWelcome"].get("done"):
        room["townWelcome"]["y"] = 405
        progression.tick(world, room, time.monotonic())
        for p in world._active_players(room):
            if not p.get("bot"):
                finish_dialogue(world, room, p)
        progression.tick(world, room, time.monotonic())
    inn = next(h for h in room["townLayout"] if h["service"] == "innkeeper")
    for p in world._active_players(room):
        if not p.get("bot"):
            p.update(townInterior=inn["id"], innFloor=1, x=480, y=220)
            world.action(room["code"], p["id"], {"action": "interact"})
            finish_dialogue(world, room, p)
            p["townInteraction"] = None
    player = next(p for p in world._active_players(room) if not p.get("bot"))
    bed = next(r for r in room["innRooms"] if not r["locked"])
    player.update(townInterior=inn["id"], innFloor=2, x=bed["x"], y=bed["y"])
    world.action(room["code"], player["id"], {"action": "interact"})
    for p in room["players"].values():
        p.update(townInterior=None, innFloor=1, x=480, y=460, townInteraction=None, dialogue=None)
