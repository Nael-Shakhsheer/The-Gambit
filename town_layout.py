"""Seeded village scenery with roads routed around the buildings."""
from collections import deque
import math
import random

BUILDINGS = [("inn", "Inn", "innkeeper"), ("store", "Store", "merchant"),
             ("lab", "Alchemy Lab", "alchemist"), ("guild", "Guild", "guildmaster"),
             ("cottage", "Cottage", None), ("lodge", "Lodge", None)]
ROOFS = ["#a94f3d", "#426f78", "#c56643", "#906451", "#b6773f", "#66518c"]


def clear(houses, x, y, margin=0):
    return not any(abs(x - h["x"]) < 69 + margin and
                   h["y"] - 78 - margin < y < h["y"] + 35 + margin for h in houses)


def roads(houses, rng):
    """Connect every door to the gate; compress grid bends for the client."""
    root = (480, 500)
    paths = [[[480, 540], [480, 500]]]
    steps = [(10, 0), (-10, 0), (0, 10), (0, -10)]
    rng.shuffle(steps)
    # A different crossroads changes both the trunk and branch geometry.
    candidates = [(x, y) for x in range(250, 711, 10) for y in range(210, 421, 10)
                  if clear(houses, x, y, 23)]
    plaza = rng.choice(candidates)
    goals = [(plaza, None)] + [((round(h["x"] / 10) * 10,
                               math.ceil((h["y"] + 65) / 10) * 10), h) for h in houses]
    for goal, house in goals:
        start = root if house is None else plaza
        queue, parent = deque([start]), {start: None}
        while queue and goal not in parent:
            x, y = queue.popleft()
            for dx, dy in steps:
                point = (x + dx, y + dy)
                if (point not in parent and 20 <= point[0] <= 940 and 20 <= point[1] <= 530
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
        bends.append(route[-1])
        if house:
            bends.extend([[house["x"], goal[1]], [house["x"], house["y"] + 47]])
        paths.append(bends)
    return paths


def scenery(houses, seed):
    rng = random.Random(seed)
    paths = roads(houses, rng)
    villagers = []
    for _ in range(2000):
        if len(villagers) >= 12:
            break
        x, y = rng.randint(65, 895), rng.randint(100, 475)
        if (clear(houses, x, y, 28) and math.hypot(x - 480, y - 480) > 80
                and all(math.hypot(x-h["x"], y-h["y"]-47) > 48 for h in houses)
                and all(math.hypot(x-v["x"], y-v["y"]) > 38 for v in villagers)):
            villagers.append({"x": x, "y": y, "shirt": rng.choice(["#ba7777", "#8fb583", "#759fbf", "#d0b475", "#b59bcd"]),
                              "skin": rng.choice(["#f1cda1", "#cc9871", "#94664e"]),
                              "hair": rng.choice(["#49352e", "#b88d58", "#ddd0b7"]), "hat": rng.choice([True, False])})
    trees = []
    for _ in range(160):
        x, y = rng.randint(35, 925), rng.randint(75, 480)
        # Leave roads, spawn, doors and villagers visually clear.
        near_road = any(min(a[0], b[0])-42 <= x <= max(a[0], b[0])+42 and
                        min(a[1], b[1])-42 <= y <= max(a[1], b[1])+42
                        for path in paths for a, b in zip(path, path[1:]))
        if (not near_road and clear(houses, x, y, 36)
                and all(math.hypot(x-v["x"], y-v["y"]) > 45 for v in villagers)
                and all(math.hypot(x-t[0], y-t[1]) > 60 for t in trees)):
            trees.append([x, y])
            if len(trees) == 10:
                break
    return {"townPaths": paths, "townVillagers": villagers, "townDecor": {"trees": trees}}


def generate(seed):
    rng = random.Random(seed)
    templates = [
        [(180, 125), (480, 120), (780, 130), (180, 330), (480, 325), (780, 335)],
        [(250, 100), (700, 100), (250, 270), (700, 270), (250, 440), (700, 440)],
        [(140, 125), (400, 130), (675, 125), (265, 330), (550, 325), (820, 330)],
    ]
    for attempt in range(80):
        if rng.random() < .5:
            positions = []
            for _ in range(800):
                x, y = rng.randint(130, 830), rng.randint(100, 425)
                if (y > 375 and abs(x-480) < 150) or any(abs(x-a) < 180 and abs(y-b) < 175 for a, b in positions):
                    continue
                positions.append((x, y))
                if len(positions) == 6:
                    break
            if len(positions) != 6:
                continue
        else:
            template = rng.choice(templates)
            positions = [(x+rng.randint(-25, 25), y+rng.randint(-3, 3)) for x, y in template]
        rng.shuffle(positions)
        roofs = ROOFS.copy()
        rng.shuffle(roofs)
        houses = [{"id": key, "name": name, "service": service, "x": x, "y": y, "roof": roofs[i]}
                  for i, ((key, name, service), (x, y)) in enumerate(zip(BUILDINGS, positions))]
        try:
            return {"townLayout": houses, "townSeed": seed, **scenery(houses, seed)}
        except ValueError:
            continue
    raise RuntimeError("Could not generate a connected village")
