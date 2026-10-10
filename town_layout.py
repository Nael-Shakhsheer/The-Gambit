"""Seeded village scenery with roads routed around the buildings."""
from collections import deque
import math
import random

BUILDINGS = [("inn", "Inn", "innkeeper"), ("store", "Store", "merchant"),
             ("lab", "Alchemy Lab", "alchemist"), ("guild", "Guild", "guildmaster"),
             ("cottage", "Cottage", None), ("lodge", "Lodge", None)]
ROOFS = ["#a94f3d", "#426f78", "#c56643", "#906451", "#b6773f", "#66518c"]

# Different silhouettes, rather than merely swapping services on a two-row grid.
LAYOUTS = {
    "market_ring": [(170, 120), (480, 110), (790, 120), (170, 345), (370, 290), (790, 350)],
    "two_hamlets": [(140, 125), (340, 115), (190, 335), (640, 120), (840, 130), (780, 350)],
    "winding_street": [(140, 120), (380, 150), (650, 110), (820, 285), (200, 350), (620, 305)],
    "staggered_lanes": [(180, 105), (740, 105), (310, 275), (650, 275), (100, 425), (860, 425)],
    "western_common": [(160, 120), (400, 110), (700, 120), (150, 325), (630, 300), (840, 425)],
    "crescent": [(130, 240), (310, 110), (550, 120), (810, 110), (830, 305), (230, 425)],
    "scattered_courts": [(130, 115), (350, 270), (600, 105), (850, 140), (150, 420), (760, 375)],
}


def clear(houses, x, y, margin=0):
    return not any(abs(x - h["x"]) < 69 + margin and
                   h["y"] - 78 - margin < y < h["y"] + 35 + margin for h in houses)


def _route(houses, start, goal, rng):
    """Route a walkable, full-width trail, keeping roofs and door approaches clear."""
    steps = [(10, 0), (-10, 0), (0, 10), (0, -10)]
    rng.shuffle(steps)
    queue, parent = deque([start]), {start: None}
    while queue and goal not in parent:
        x, y = queue.popleft()
        for dx, dy in steps:
            point = (x + dx, y + dy)
            if (point not in parent and 30 <= point[0] <= 930 and 30 <= point[1] <= 510
                    and clear(houses, *point, 23)):
                parent[point] = (x, y)
                queue.append(point)
    if goal not in parent:
        raise ValueError("Village road cannot reach a door")
    route, point = [], goal
    while point is not None:
        route.append(list(point))
        point = parent[point]
    route.reverse()
    bends = [route[0]]
    for i in range(1, len(route) - 1):
        if ((route[i][0] - route[i-1][0], route[i][1] - route[i-1][1]) !=
                (route[i+1][0] - route[i][0], route[i+1][1] - route[i][1])):
            bends.append(route[i])
    if len(route) > 1:
        bends.append(route[-1])
    return bends, {tuple(point) for point in route}


def _network(houses, rng):
    root = (480, 500)
    paths = [[[480, 540], [480, 500]]]
    style = rng.choice(["branching", "loop", "lanes"])
    candidates = [(x, y) for x in range(140, 821, 10) for y in range(170, 391, 10)
                  if clear(houses, x, y, 23)]
    if not candidates:
        raise ValueError("Village has no clear crossroads")
    hubs = [rng.choice(candidates)]
    for _ in range(2 if style == "loop" else 1):
        distant = [point for point in candidates if all(math.dist(point, h) > 170 for h in hubs)]
        if len(hubs) == 2:
            a, b = hubs
            distant = [p for p in distant if abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])) > 14000]
        if not distant:
            raise ValueError("Village has no separated commons")
        hubs.append(rng.choice(distant))
    connected = {root}
    for start, goal in zip([root] + hubs, hubs):
        bends, cells = _route(houses, start, goal, rng)
        paths.append(bends)
        connected.update(cells)
    if style == "loop":
        bends, cells = _route(houses, hubs[-1], hubs[0], rng)
        paths.append(bends)
        connected.update(cells)
    order = houses.copy()
    rng.shuffle(order)
    for house in order:
        goal = (round(house["x"] / 10) * 10, math.ceil((house["y"] + 65) / 10) * 10)
        # Branching villages grow organically; lanes/loops connect to their commons.
        choices = sorted(connected) if style == "branching" else hubs
        start = min(choices, key=lambda point: math.dist(point, goal))
        bends, cells = _route(houses, start, goal, rng)
        bends.extend([[house["x"], goal[1]], [house["x"], house["y"] + 47]])
        paths.append(bends)
        connected.update(cells)
    return paths, hubs, style


def roads(houses, rng):
    """Legacy helper: return the connected road polylines."""
    return _network(houses, rng)[0]


def scenery(houses, seed):
    rng = random.Random(seed)
    paths, plazas, style = _network(houses, rng)
    villagers = []
    for _ in range(2000):
        if len(villagers) >= 12:
            break
        if rng.random() < .5:
            px, py = rng.choice(plazas)
            x, y = px + rng.randint(-85, 85), py + rng.randint(-65, 65)
        else:
            x, y = rng.randint(65, 895), rng.randint(100, 475)
        if not (65 <= x <= 895 and 100 <= y <= 475):
            continue
        if (clear(houses, x, y, 28) and math.hypot(x - 480, y - 480) > 80
                and all(math.hypot(x-h["x"], y-h["y"]-47) > 48 for h in houses)
                and all(math.hypot(x-v["x"], y-v["y"]) > 38 for v in villagers)):
            villagers.append({"x": x, "y": y, "shirt": rng.choice(["#ba7777", "#8fb583", "#759fbf", "#d0b475", "#b59bcd"]),
                              "skin": rng.choice(["#f1cda1", "#cc9871", "#94664e"]),
                              "hair": rng.choice(["#49352e", "#b88d58", "#ddd0b7"]), "hat": rng.choice([True, False])})
    trees = []
    tree_count = rng.randint(6, 11)
    for _ in range(220):
        x, y = rng.randint(35, 925), rng.randint(75, 480)
        # Leave roads, spawn, doors and villagers visually clear.
        near_road = any(min(a[0], b[0])-42 <= x <= max(a[0], b[0])+42 and
                        min(a[1], b[1])-42 <= y <= max(a[1], b[1])+42
                        for path in paths for a, b in zip(path, path[1:]))
        if (not near_road and clear(houses, x, y, 36)
                and all(math.hypot(x-v["x"], y-v["y"]) > 45 for v in villagers)
                and all(math.hypot(x-t[0], y-t[1]) > 60 for t in trees)):
            trees.append([x, y])
            if len(trees) == tree_count:
                break
    return {"townPaths": paths, "townVillagers": villagers,
            "townDecor": {"trees": trees, "plazas": [list(p) for p in plazas], "roadStyle": style}}


def _valid_positions(positions):
    houses = [{"x": x, "y": y} for x, y in positions]
    # All four party spawns, the exit and the welcoming runner's approach.
    if not all(clear(houses, x, y, 23) for x, y in [(417, 460), (459, 460), (501, 460), (543, 460), (480, 500), (480, 345)]):
        return False
    return all(abs(x-a) >= 180 or abs(y-b) >= 158
               for i, (x, y) in enumerate(positions) for a, b in positions[:i])


def generate(seed, previous_layout=None):
    rng = random.Random(seed)
    kind = rng.choice([name for name in LAYOUTS if name != previous_layout])
    mirrored = rng.choice([True, False])
    for attempt in range(160):
        spread = 1 if attempt < 120 else .4
        positions = [(max(95, min(865, (960-x if mirrored else x) + round(rng.randint(-38, 38)*spread))),
                      max(100, min(425, y + round(rng.randint(-25, 25)*spread)))) for x, y in LAYOUTS[kind]]
        if not _valid_positions(positions):
            continue
        # Occasionally move a whole building into a different free part of the village.
        if rng.random() < .45:
            index = rng.randrange(6)
            for _ in range(50):
                candidate = positions.copy()
                candidate[index] = (rng.randint(100, 860), rng.randint(100, 425))
                if _valid_positions(candidate):
                    positions = candidate
                    break
        rng.shuffle(positions)
        roofs = ROOFS.copy()
        rng.shuffle(roofs)
        houses = [{"id": key, "name": name, "service": service, "x": x, "y": y, "roof": roofs[i]}
                  for i, ((key, name, service), (x, y)) in enumerate(zip(BUILDINGS, positions))]
        try:
            village = {"townLayout": houses, "townSeed": seed, **scenery(houses, seed)}
            village["townDecor"]["layout"] = kind
            return village
        except ValueError:
            continue
    raise RuntimeError("Could not generate a connected village")
