from __future__ import annotations

import random
import secrets

RUNES = ["SUN", "MOON", "LEAF", "FLAME", "WAVE", "STAR"]
HINTS = {
    "SUN": "Seek the golden rune that heralds the dawn.",
    "MOON": "Seek the silver rune that watches through the night.",
    "LEAF": "Seek the green rune of growing things.",
    "FLAME": "Seek the red rune that carries a living fire.",
    "WAVE": "Seek the blue rune that moves like water.",
    "STAR": "Seek the pale rune that shines far above the world.",
}


def new_puzzle(player_ids: list[str], names: dict | None = None) -> dict:
    rooms = {}
    for player_id in player_ids:
        positions = [(x, y) for y in (112, 226, 340, 426) for x in (125, 267, 409, 551, 693, 835)]
        random.shuffle(positions)
        options = [
            {"rune": rune, "x": positions[index][0], "y": positions[index][1]}
            for index, rune in enumerate(RUNES)
        ]
        target = random.choice(RUNES)
        free_spots = [(x, y) for y in (112, 226, 340, 426) for x in (125, 267, 409, 551, 693, 835)
                      if all((x - rune["x"]) ** 2 + (y - rune["y"]) ** 2 > 95 ** 2 for rune in options)]
        totem_x, totem_y = random.choice(free_spots)
        rooms[player_id] = {
            "runes": options,
            "target": target,
            "clue": HINTS[target],
            "totem": {"x": totem_x, "y": totem_y},
            "totemSeen": False,
            "wrongAt": 0,
            "standing": None,
        }
    puzzle = {"id": secrets.token_hex(4), "rooms": rooms}
    assign_clues(puzzle, player_ids, names or {})
    return puzzle


def assign_clues(puzzle: dict, player_ids: list[str], names: dict) -> None:
    """A cycle means every active player holds exactly one teammate's clue."""
    active = [pid for pid in player_ids if pid in puzzle["rooms"]]
    if puzzle.get("activePlayers") == active:
        return
    puzzle["activePlayers"] = active
    puzzle["lastAttempt"] = None
    for index, pid in enumerate(active):
        recipient = active[(index + 1) % len(active)]
        room = puzzle["rooms"][pid]
        room["clueFor"] = recipient
        room["clueForName"] = names.get(recipient, "Your teammate") if recipient != pid else "You"
        room["clue"] = HINTS[puzzle["rooms"][recipient]["target"]]
        room["totemSeen"] = False


def player_puzzle_view(puzzle: dict | None, player_id: str, position: tuple[float, float]) -> dict | None:
    if not puzzle or player_id not in puzzle["rooms"]:
        return None
    room = puzzle["rooms"][player_id]
    active = puzzle.get("activePlayers", list(puzzle["rooms"]))
    cooperative = len(active) > 1
    recipient = room.get("clueFor", player_id)
    x, y = position
    at_totem = (x - room["totem"]["x"]) ** 2 + (y - room["totem"]["y"]) ** 2 <= 58 ** 2
    clue_known = room["totemSeen"] or at_totem
    standing = next((rune["rune"] for rune in room["runes"]
                     if (x - rune["x"]) ** 2 + (y - rune["y"]) ** 2 <= 34 ** 2), None)
    return {
        "id": puzzle["id"],
        "runes": room["runes"],
        "totem": room["totem"],
        "clue": room["clue"] if clue_known else None,
        "targetSigil": puzzle["rooms"][recipient]["target"] if clue_known else None,
        "clueForName": room.get("clueForName", "You"),
        "cooperative": cooperative,
        "atTotem": at_totem,
        "standingRune": standing,
        "isCorrect": None if cooperative else standing == room["target"],
        "readyCount": sum(bool(puzzle["rooms"][pid].get("standing")) for pid in active),
        "partySize": len(active),
    }
