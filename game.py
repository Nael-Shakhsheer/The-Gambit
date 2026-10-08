from __future__ import annotations

import math
import random
import secrets
import threading
import time
import copy
from pathlib import Path
import logging
from puzzles import new_puzzle, player_puzzle_view, assign_clues
from run_storage import RunStorage
import telemetry
import town_layout
import boss_ai
import tactical_rules as tactical
import companion_ai
import progression
import combat_environment as terrain
import enemy_roles
import combat_encounters

WIDTH = 960
HEIGHT = 540
MAX_PLAYERS = 4
POUCH_CAPACITY = 10
DIFFICULTIES = {
    "easy": {"label": "Easy", "stages": 20, "multiplier": .9},
    "medium": {"label": "Medium", "stages": 25, "multiplier": 1.25},
    "hard": {"label": "Hard", "stages": 30, "multiplier": 1.6},
}
CLASSES = {
    "Knight": {"role": "Melee tank", "hp": 150, "damage": 18, "speed": 145, "range": 120, "color": "#d9b76e"},
    "Wizard": {"role": "Ranged arcane damage", "hp": 100, "damage": 15, "speed": 145, "range": 250, "color": "#a68bff"},
    "Archer": {"role": "Fast piercing shots", "hp": 105, "damage": 13, "speed": 185, "range": 300, "color": "#8bd47b"},
    "Cleric": {"role": "Splash-potion support", "hp": 85, "damage": 9, "speed": 145, "range": 190, "color": "#ffe28a"},
    "Rogue": {"role": "Fast bleed damage", "hp": 80, "damage": 16, "speed": 205, "range": 125, "color": "#c68bd8"},
    "Druid": {"role": "Elemental summoner", "hp": 80, "damage": 12, "speed": 145, "range": 280, "color": "#6bc49b"},
    "Bard": {"role": "Team stat support", "hp": 75, "damage": 8, "speed": 145, "range": 185, "color": "#f095bf"},
    "Healer": {"role": "Strong healing and quick revives", "hp": 110, "damage": 6, "speed": 140, "range": 175, "color": "#85d9db"},
}
ABILITY_SETS = {
    "Knight": [
        ("shield_bash", "Shield Bash", "Strike and briefly stun the nearest foe.", "stun", 1.05, 155, 0.45, "light"),
        ("cleaving_arc", "Cleave", "A quick arc that hits nearby foes.", "area", 0.9, 125, 0.55, "light"),
        ("iron_wall", "Iron Wall", "Take half damage for 8 seconds.", "self_ward", 0.5, 0, 8, "special"),
        ("challenge", "Challenge", "Draw enemy attention for 7 seconds.", "taunt", 1, 0, 7, "special"),
        ("guardian_cry", "Last Stand", "Give the whole party a powerful ward.", "team_ward", 0.45, 0, 30, "ultimate"),
        ("earthshaker", "Earthshaker", "Smash the ground and hit foes within 260px of you.", "area", 2.6, 260, 28, "ultimate"),
    ],
    "Wizard": [
        ("arc_burst", "Arc Bolt", "A bolt chains to two more foes within 110px of each hit, dealing 65% damage per jump. Best against clusters.", "damage", 0.85, 285, 0.55, "light"),
        ("frost_lance", "Frost Lance", "Freeze one foe briefly, with lower sustained damage. Bosses resist repeated control.", "stun", 0.65, 300, 0.75, "light"),
        ("spell_surge", "Spell Surge", "Increase your damage for 8 seconds.", "self_damage", 1.5, 0, 8, "special"),
        ("blink", "Blink", "Dash away from nearby danger.", "blink", 1, 180, 7, "special"),
        ("team_aegis", "Astral Aegis", "Protect the whole party with a strong ward.", "team_ward", 0.4, 0, 30, "ultimate"),
        ("arcane_cataclysm", "Arcane Cataclysm", "Unleash a blast that hits foes within 320px of you.", "area", 3.0, 320, 28, "ultimate"),
    ],
    "Archer": [
        ("piercing_volley", "Quick Shot", "A fast arrow that pierces nearby foes.", "pierce", 0.8, 320, 0.4, "light"),
        ("snare_shot", "Snare Shot", "A quick arrow that briefly stuns.", "stun", 0.95, 300, 0.5, "light"),
        ("eagle_eye", "Eagle Eye", "Increase your damage for 8 seconds.", "self_damage", 1.55, 0, 8, "special"),
        ("quickstep", "Quickstep", "Move faster for 6 seconds.", "speed", 1.8, 0, 7, "special"),
        ("rain_of_arrows", "Rain of Arrows", "Aim at your selected foe within 380px (nearest if unavailable). After 0.65s, arrows strike a fixed 110px-radius cluster there.", "target_area", 2.4, 380, 29, "ultimate"),
        ("deadeye", "Deadeye", "A devastating shot at the nearest foe.", "damage", 4.0, 400, 28, "ultimate"),
    ],
    "Cleric": [
        ("radiant_flask", "Radiant Flask", "A holy flask bursts on impact, hitting enemies within 75px. Lower single-target damage; strong against clusters.", "damage", 0.65, 250, 0.6, "light"),
        ("sanctified_throw", "Sanctified Throw", "A fast holy bolt hits one foe within 300px. Higher sustained damage against an isolated target.", "damage", 1.05, 300, 0.45, "light"),
        ("splash_mend", "Splash Mend", "Heal nearby allies.", "team_heal", 32, 240, 8, "special"),
        ("blessed_vial", "Blessed Vial", "Ward allies within 220px for 8 seconds.", "team_ward", 0.6, 220, 8, "special"),
        ("sanctuary_rain", "Sanctuary Rain", "Restore health to the whole party.", "team_heal", 65, 0, 30, "ultimate"),
        ("cleansing_splash", "Cleansing Splash", "Revive a nearby fallen ally instantly.", "revive", 1, 240, 28, "ultimate"),
    ],
    "Rogue": [
        ("backstab", "Quick Cut", "A fast, bleeding strike against one foe.", "bleed", 1.0, 155, 0.38, "light"),
        ("fan_of_blades", "Fan of Blades", "A quick slash around you.", "area", 0.9, 140, 0.52, "light"),
        ("vanish", "Vanish", "Become untargetable for 5 seconds.", "invisible", 1, 0, 7, "special"),
        ("shadowstep", "Shadowstep", "Dash toward a foe and strike it.", "dash_strike", 1.8, 300, 8, "special"),
        ("death_bloom", "Death Bloom", "Blades strike every foe within 280px of you and apply a 5-second bleed.", "area", 2.3, 280, 30, "ultimate"),
        ("execution", "Shadow Execution", "A devastating strike against the nearest foe.", "bleed", 4.0, 300, 27, "ultimate"),
    ],
    "Druid": [
        ("briar_burst", "Briar Bolt", "Briars spread within 65px of impact and root the cluster for 0.8s. Lower damage; bosses resist repeated roots.", "damage", 0.7, 280, 0.65, "light"),
        ("thornshot", "Thornshot", "A focused thorn hits one foe within 300px. Faster attacks and higher sustained single-target damage.", "damage", 1.05, 300, 0.45, "light"),
        ("lightning_bird", "Lightning Bird", "Summon a bird that fires lightning at the nearest foe for 90% of your Light damage per hit. Locked while alive; 8s recharge after it dies.", "summon", 0.9, 0, 8, "special"),
        ("fire_wolf", "Fire Wolf", "Summon a fire wolf that hunts the nearest foe for 90% of your Light damage per hit. Locked while alive; 8s recharge after it dies.", "summon", 0.9, 0, 8, "special"),
        ("ice_bear", "Ice Bear", "Summon an ice bear that mauls the nearest foe for twice your Light damage per hit. Locked while alive; 15s recharge after it dies.", "summon", 2.0, 0, 15, "ultimate"),
        ("nature_golem", "Nature Rock Golem", "Summon a nature rock golem that smashes the nearest foe for twice your Light damage per hit. Locked while alive; 15s recharge after it dies.", "summon", 2.0, 0, 15, "ultimate"),
    ],
    "Bard": [
        ("discord_note", "Discord Note", "A quick sound burst hits foes within 200px of you.", "area", 0.85, 200, 0.55, "light"),
        ("quickstring", "Quickstring", "Fire a quick piercing note at one foe.", "damage", 1.0, 250, 0.45, "light"),
        ("battle_anthem", "Battle Anthem", "Raise the party's damage for 8 seconds.", "team_damage", 1.3, 0, 8, "special"),
        ("fleet_rhythm", "Fleet Rhythm", "Give the party a short speed boost.", "team_speed", 1.5, 0, 8, "special"),
        ("grand_crescendo", "Grand Crescendo", "Raise every ally's damage dramatically.", "team_damage", 1.75, 0, 30, "ultimate"),
        ("rallying_chord", "Finale of Heroes", "Restore health to the whole party.", "team_heal", 65, 0, 28, "ultimate"),
    ],
    "Healer": [
        ("life_spark", "Life Spark", "A quick spark of light harms the nearest foe.", "damage", 0.9, 240, 0.5, "light"),
        ("healing_ray", "Gentle Mend", "Restore a little health to the most injured ally.", "team_heal", 12, 320, 0.8, "light"),
        ("major_mend", "Major Mend", "Heal the most injured nearby ally.", "team_heal", 55, 0, 8, "special"),
        ("quick_revival", "Quick Revival", "Instantly revive the nearest downed ally.", "revive", 1, 300, 7, "special"),
        ("miracle", "Miracle", "Restore a great amount of health to the party.", "team_heal", 90, 0, 30, "ultimate"),
        ("mass_revival", "Mass Revival", "Revive every fallen ally in the party.", "team_revive", 1, 0, 32, "ultimate"),
    ],
}

# Keep mana costs stable while all Ultimates recharge in 15 seconds.
ULTIMATE_MANA_COSTS = {a[0]: 10+round(a[6]*1.5) for abilities in ABILITY_SETS.values() for a in abilities if a[7] == "ultimate"}
ABILITY_SETS = {hero: [a[:6]+(15,)+a[7:] if a[7] == "ultimate" else a for a in abilities]
                for hero, abilities in ABILITY_SETS.items()}

SUMMON_TYPES = {
    "lightning_bird": {"name": "Lightning Bird", "kind": "bird", "affinity": "Storm", "hp": 40, "speed": 185, "range": 210, "attackInterval": 1.15, "recharge": 8},
    "fire_wolf": {"name": "Fire Wolf", "kind": "wolf", "affinity": "Fire", "hp": 65, "speed": 160, "range": 35, "attackInterval": 1.15, "recharge": 8},
    "ice_bear": {"name": "Ice Bear", "kind": "bear", "affinity": "Ice", "hp": 125, "speed": 100, "range": 45, "attackInterval": 1.4, "recharge": 15},
    "nature_golem": {"name": "Nature Rock Golem", "kind": "golem", "affinity": "Nature", "hp": 170, "speed": 75, "range": 50, "attackInterval": 1.8, "recharge": 15},
}
def ability_record(ability: tuple) -> dict:
    ability_id, name, description, kind, power, reach, cooldown, attack_type = ability
    return {"id": ability_id, "name": name, "description": description, "kind": kind,
            "power": power, "range": reach, "cooldown": cooldown, **tactical.ABILITY_DETAILS.get(ability_id, {}),
            "attackType": attack_type,
            "manaCost": 0 if attack_type == "light" else ULTIMATE_MANA_COSTS.get(ability_id, 10 + round(cooldown * 1.5))}


ENEMIES = [
    ("Serpent Guard", "serpent", 46, 7, "#a9c65c"),
    ("Minotaur", "minotaur", 76, 11, "#b87b52"),
    ("Wolf", "wolf", 38, 8, "#aba8b6"),
    ("Cave Spider", "spider", 32, 6, "#9b83b1"),
    ("Cave Troll", "troll", 90, 12, "#7da48a"),
]
DRACO = ("Draco", "draco", 124, 7, "#ba7650")
LARGE_BOSSES = [
    {"name": "Serpent Matriarch", "kind": "serpent", "affinity": "Poison", "hp": 620, "damage": 16},
    {"name": "Labyrinth Minotaur King", "kind": "minotaur", "affinity": "Storm", "hp": 820, "damage": 19},
    {"name": "Ancient Stone Behemoth", "kind": "troll", "affinity": "Nature", "hp": 980, "damage": 21},
    {"name": "Chimera", "kind": "monster", "affinity": "Arcane", "hp": 760, "damage": 18},
    {"name": "Great Wolf Guardian", "kind": "wolf", "affinity": "Ice", "hp": 680, "damage": 17},
]
DRAGON_TYPES = [
    {"name": "Fire Dragon", "affinity": "Fire", "hp": 1040, "damage": 22},
    {"name": "Ice Dragon", "affinity": "Ice", "hp": 1080, "damage": 20},
    {"name": "Dark Magic Dragon", "affinity": "Dark", "hp": 1120, "damage": 21},
    {"name": "Arcane Dragon", "affinity": "Arcane", "hp": 980, "damage": 23},
    {"name": "Storm Dragon", "affinity": "Storm", "hp": 1020, "damage": 22},
]
AFFINITIES = {
    "Fire": "#f47745",
    "Ice": "#85dcf2",
    "Dark": "#79618e",
    "Arcane": "#bb83ff",
    "Poison": "#92d64f",
    "Storm": "#e9dd72",
    "Nature": "#64c78d",
}
TOWNS = ["Mossgate", "Bellweather", "Hearthrest", "Silverbrook", "Rookhaven"]
TOWN_GATE = (480, 490)
TOWN_SERVICE_POSITION = (480, 220)
ROUTE_GATES = ((28, 170), (WIDTH - 28, 170))
FORK_PATHS = (((480, 540), (480, 320), (260, 170), (0, 170)),
              ((480, 540), (480, 320), (700, 170), (960, 170)))
PUZZLE_RUNS = (("one", 65), ("two", 30), ("three", 5))
ITEMS = {
    "healing_draught": {"name": "Healing Draught", "rarity": "Common", "price": 8, "sell": 4, "kind": "heal", "slot": "utility", "description": "Restore 40 HP."},
    "warding_tonic": {"name": "Warding Tonic", "rarity": "Uncommon", "price": 12, "sell": 6, "kind": "ward", "slot": "utility", "description": "Take 40% less damage for 30 seconds."},
    "mana_draught": {"name": "Mana Draught", "rarity": "Uncommon", "price": 14, "sell": 7, "kind": "mana", "slot": "utility", "mana": 50, "description": "Restore 50 mana."},
    "quickstep_elixir": {"name": "Quickstep Elixir", "rarity": "Uncommon", "price": 14, "sell": 7, "kind": "speed", "slot": "utility", "factor": 1.45, "duration": 10, "description": "Move 45% faster for 10 seconds."},
    "route_lens": {"name": "Pathfinder's Lens", "rarity": "Rare", "price": 18, "sell": 9, "kind": "hint", "slot": "utility", "description": "Reveal the easier path at the next fork. One use."},
    "ember_oil": {"name": "Ember Oil", "rarity": "Rare", "price": 25, "sell": 12, "kind": "buff", "slot": "utility", "factor": 1.4, "duration": 12, "description": "Deal 40% more damage for 12 seconds."},
    "piercing_arrows": {"name": "Piercing Arrows", "rarity": "Rare", "price": 24, "sell": 12, "kind": "arrows", "slot": "utility", "attacks": 5, "factor": 1.5, "description": "Empower your next 5 basic attacks."},
    "phoenix_flask": {"name": "Phoenix Flask", "rarity": "Epic", "price": 40, "sell": 20, "kind": "heal", "slot": "utility", "heal": 75, "description": "Restore 75 HP."},
    "stormguard_charm": {"name": "Stormguard Charm", "rarity": "Epic", "price": 42, "sell": 21, "kind": "ward", "slot": "utility", "factor": 0.35, "duration": 22, "description": "Take 65% less damage for 22 seconds."},
    "iron_sword": {"name": "Iron Sword", "rarity": "Common", "price": 22, "sell": 11, "kind": "weapon", "slot": "tool", "damage": 6, "color": "#d8d4c9", "description": "A sturdy blade adds 6 damage to attacks."},
    "oakguard_vest": {"name": "Oakguard Vest", "rarity": "Uncommon", "price": 20, "sell": 10, "kind": "armor", "slot": "tool", "armor": 3, "color": "#8a9d61", "description": "Woven bark armor blocks 3 damage per hit."},
    "moonsteel_sword": {"name": "Moonsteel Sword", "rarity": "Rare", "price": 34, "sell": 17, "kind": "weapon", "slot": "tool", "damage": 10, "color": "#b9d7e8", "description": "A moon-forged blade adds 10 damage to attacks."},
    "dragonbone_armor": {"name": "Dragonbone Armor", "rarity": "Epic", "price": 48, "sell": 24, "kind": "armor", "slot": "tool", "armor": 6, "color": "#df9b65", "description": "Dragonbone plates block 6 damage per hit."},
    "starfall_blade": {"name": "Starfall Blade", "rarity": "Legendary", "price": 80, "sell": 40, "kind": "weapon", "slot": "tool", "damage": 18, "color": "#f4d98c", "description": "A legendary blade adds 18 damage to attacks."},
    "aegis_of_dawn": {"name": "Aegis of Dawn", "rarity": "Legendary", "price": 76, "sell": 38, "kind": "armor", "slot": "tool", "armor": 10, "color": "#92d9d1", "description": "A radiant cuirass blocks 10 damage per hit."},
    "sage_wand": {"name": "Sage's Wand", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 6, "color": "#9d83ef", "description": "A crystal focus adds 6 damage to spells."},
    "wind_bow": {"name": "Wind Bow", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 6, "color": "#90cb77", "description": "A springy bow adds 6 damage to arrows."},
    "sun_censer": {"name": "Sun Censer", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 5, "color": "#e8ca74", "description": "A radiant censer adds 5 damage to holy flasks."},
    "shadow_blades": {"name": "Shadow Blades", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 7, "color": "#b898d5", "description": "Twin knives add 7 damage to quick strikes."},
    "thorn_staff": {"name": "Thorn Staff", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 6, "color": "#77bf82", "description": "A living branch adds 6 damage to nature magic."},
    "travel_lute": {"name": "Travel Lute", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 5, "color": "#df9dbd", "description": "A finely tuned lute adds 5 damage to sonic attacks."},
    "mercy_rod": {"name": "Mercy Rod", "rarity": "Common", "price": 25, "sell": 12, "kind": "weapon", "slot": "tool", "damage": 4, "color": "#8ce0db", "description": "A healing rod adds 4 damage to light attacks."},
}
ITEMS.update(tactical.BUILD_ITEMS)
CLASS_WEAPONS = {"Knight": "iron_sword", "Wizard": "sage_wand", "Archer": "wind_bow", "Cleric": "sun_censer",
                 "Rogue": "shadow_blades", "Druid": "thorn_staff", "Bard": "travel_lute", "Healer": "mercy_rod"}
LOOT_RARITIES = (("Common", 48), ("Uncommon", 27), ("Rare", 16), ("Epic", 7), ("Legendary", 2))
CURSES = [
    {"name": "Ashen Shackles", "description": "Movement speed is reduced by 25%.", "effect": "sluggish"},
    {"name": "Hollow Edge", "description": "You deal 25% less attack damage.", "effect": "weakened"},
    {"name": "Brittle Oath", "description": "You take 25% more damage from enemies.", "effect": "frail"},
]


class GameWorld:
    def __init__(self, storage_dir=None, disconnect_timeout=None) -> None:
        self.rooms: dict[str, dict] = {}
        self.lock = threading.RLock()
        self.storage = RunStorage(storage_dir) if storage_dir is not None else None
        self.disconnect_timeout = disconnect_timeout
        if self.storage:
            for room in self.storage.load():
                try:
                    self._prepare_restored_room(room)
                    self.rooms[room["code"]] = room
                except (KeyError, TypeError, ValueError):
                    logging.exception("Invalid checkpoint preserved: %s", room.get("code"))

    @staticmethod
    def _active_players(room):
        humans = [p for p in room["players"].values() if not p.get("bot") and p.get("connected", True)]
        return [p for p in room["players"].values() if p.get("bot") or p.get("connected", True)] if humans else []

    @staticmethod
    def _voting_players(room):
        return [p for p in room["players"].values() if not p.get("bot") and p.get("connected", True)]

    def _combat_targets(self, room):
        return self._active_players(room)+room.get('summons',[])+combat_encounters.ward(room)

    @staticmethod
    def _town_pressure(room):
        arrivals=room.get('townPressureStages',[])
        return max(0,room.get('townsVisited',0)-len(arrivals))+sum(max(0,min(1,(room['stage']-stage)/2)) for stage in arrivals)

    def _routes_ready(self, room):
        voters = self._voting_players(room)
        return bool(voters) and all(p["id"] in room["routeVotes"] for p in voters)

    def _prepare_restored_room(self, room):
        room.update(phase="town", enemies=[], summons=[], projectiles=[], effects=[],
                    puzzle=None, routes=[], routeVotes={}, chest=None, waveStartsAt=0,
                    pings=[], combatStats=None, hazards=[], pausedAt=time.monotonic())
        if not room.get("townPaths"):
            room.update(town_layout.scenery(room["townLayout"], room.get("townSeed", 1)))
        room.update(nextTown=None, forkPending=False)
        room.setdefault("difficulty", "medium")
        room.setdefault("totalStages", DIFFICULTIES[room["difficulty"]]["stages"])
        room.setdefault('objectiveStages',{})
        room.setdefault('townPressureStages',[])
        room['objective']=None
        for pid, saved in list(room["players"].items()):
            player = self._player(pid, saved["name"])
            for key in ("class", "maxHp", "maxMana", "abilities", "inventory", "utilitySlots",
                        "toolSlots", "weapon", "armor", "curse", "shopStock", "classChangeUsed", "bot", "skillRanks", "skillPoints", "skillRewards", "trainingKnown", "questAccepted"):
                if key in saved:
                    player[key] = saved[key]
            player.update(hp=player["maxHp"], mana=player["maxMana"], x=480, y=460, connected=False)
            player["connected"] = bool(player.get("bot"))
            room["players"][pid] = player
        progression.defaults(room, legacy=True)
        room["checkpoint"].setdefault("townInstance", room["townInstance"])
        room["townWelcome"] = None
        for p in room["players"].values():
            progression.place_at_checkpoint(room, p)
        room.setdefault("privateNotices", {})
        for pid in room["players"]:
            room["privateNotices"][pid] = "Run restored at your saved inn checkpoint."

    def _save_checkpoint(self, room):
        if not self.storage or room["phase"] != "town" or not room.get("checkpoint"):
            return
        if room["checkpoint"].get("townInstance", room.get("townInstance")) != room.get("townInstance"):
            return
        snapshot = copy.deepcopy(room)
        snapshot["checkpointSavedAt"] = time.time()
        try:
            self.storage.save(snapshot)
            room["checkpointSavedAt"] = snapshot["checkpointSavedAt"]
        except OSError:
            logging.exception("Could not save checkpoint")
            for pid in room["players"]:
                room.setdefault("privateNotices", {})[pid] = "Checkpoint could not be saved to disk. Please check available storage."

    @staticmethod
    def _shift_clocks(value, seconds):
        clock_keys = {"lastAttack", "lastMove", "lastManaTick", "lastTick", "startedAt", "born",
                      "downedUntil", "reviveStarted", "dashCooldownUntil", "wardUntil", "damageBoostUntil",
                      "speedBoostUntil", "invisibleUntil", "tauntUntil", "waveStartsAt", "expiresAt",
                      "stunUntil", "bleedUntil", "lastBleedTick", "wrongAt", "lastAiTick", "moveDecisionAt",
                      "aiMoveAt", "aiCastAt", "bossMoveAt", "nextBossAttack", "releaseAt",
                      "chargeUntil", "activatesAt", "nextHitAt", "trackUntil", "recoverUntil",
                      "roleReadyAt", "roleRecoverUntil", "roleChargeUntil", "warnAt", "readyAt",
                      "terrainHitAt", "stunResistUntil", "aiDodgeUntil", "aiStrafeAt", "spawnAt", "endsAt",
                      "rootUntil", "rootResistUntil", "pursuitUntil", "rescueGuardUntil", "rescueGuardReadyAt", "vulnerableUntil"}
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "abilityCooldowns":
                    for ability in item:
                        item[ability] += seconds
                elif key in clock_keys and isinstance(item, (int, float)) and item:
                    value[key] += seconds
                elif isinstance(item, (dict, list)):
                    GameWorld._shift_clocks(item, seconds)
        elif isinstance(value, list):
            for item in value:
                GameWorld._shift_clocks(item, seconds)

    def _touch_player(self, room, player):
        now = time.monotonic()
        if room.get("pausedAt") is not None:
            self._shift_clocks(room, max(0, now - room.pop("pausedAt")))
        if not player.get("connected", True):
            companions = [p for p in self._active_players(room) if p["id"] != player["id"] and p["status"] == "alive" and not p.get("townInterior")]
            if companions and room["phase"] in ("combat", "routes", "stage_exit", "chest"):
                player["x"], player["y"] = companions[0]["x"], companions[0]["y"]
            if room["phase"] == "town" and not player.get("townInterior"):
                player.update(x=480, y=460, townInterior=None, townInteraction=None)
            player.update(lastMove=now, lastManaTick=now, dx=0, dy=0, attacking=False)
            if room["phase"] == "puzzle" and player["id"] not in room["puzzle"]["rooms"]:
                room["puzzle"]["rooms"].update(new_puzzle([player["id"]])["rooms"])
        player["connected"], player["lastSeen"] = True, now
        telemetry.participant(room, player, now, ABILITY_SETS)

    def _disconnect_player(self, room, player):
        player.update(connected=False, dx=0, dy=0, attacking=False, reviving=None, townExitReady=False)
        room.get("routeVotes", {}).pop(player["id"], None)
        self._dismiss_summons(room, player["id"])

    def _update_presence(self, room, now):
        if self.disconnect_timeout:
            for player in room["players"].values():
                if player.get("bot"):
                    continue
                if player.get("connected", True) and now - player.get("lastSeen", now) > self.disconnect_timeout:
                    self._disconnect_player(room, player)
                if now - player.get("lastInputAt", now) > 2:
                    player["dx"], player["dy"], player["attacking"] = 0, 0, False
        active = self._active_players(room)
        humans = [p for p in active if not p.get("bot")]
        if humans and not room["players"].get(room["host"], {}).get("connected", False):
            room["host"] = humans[0]["id"]
        if room.get("puzzle") and active:
            assign_clues(room["puzzle"], [p["id"] for p in active], {p["id"]: p["name"] for p in active})
        if not active:
            room.setdefault("pausedAt", now)
        return bool(active)

    def _finish_stage_stats(self, room, outcome):
        report = telemetry.finish(room, time.monotonic(), outcome)
        if report and self.storage:
            try:
                self.storage.record(report)
            except OSError:
                logging.exception("Could not write balance observation")

    def _new_puzzle(self, room):
        active = self._active_players(room)
        return new_puzzle([p["id"] for p in active], {p["id"]: p["name"] for p in active})

    def _ping(self, room, player, payload):
        now = time.monotonic()
        kind = payload.get("kind")
        if kind not in ("help", "gather", "enemy"):
            raise ValueError("Choose Help, Gather, or Enemy.")
        if now - player.get("lastPing", -10) < 1.5:
            return
        target = next((e for e in room["enemies"] if e["id"] == payload.get("targetId")), None)
        if kind == "enemy" and target is None:
            raise ValueError("Select an enemy to mark.")
        player["lastPing"] = now
        room.setdefault("pings", []).append({"id": secrets.token_hex(4), "kind": kind,
            "name": player["name"], "playerId": player["id"], "targetId": target["id"] if target else None,
            "phase": room["phase"], "interior": player.get("townInterior"),
            "x": target["x"] if target else player["x"], "y": target["y"] if target else player["y"],
            "expiresAt": now + 5})
        room["pings"] = [p for p in room["pings"] if p["expiresAt"] > now][-12:]

    def _new_code(self) -> str:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(5))
            if code not in self.rooms:
                return code

    @staticmethod
    def _player(player_id: str, name: str) -> dict:
        return {
            "id": player_id, "name": name, "class": None, "hp": 100, "maxHp": 100,
            "mana": 100, "maxMana": 100, "lastManaTick": time.monotonic(),
            "x": 480, "y": 300, "dx": 0, "dy": 0, "status": "alive",
            "facingX": 1, "facingY": 0, "dashCooldownUntil": 0,
            "downedUntil": 0, "lastAttack": 0, "lastMove": time.monotonic(), "attacking": False, "reviving": None, "reviveStarted": 0,
            "inventory": [], "wardUntil": 0, "wardFactor": 1.0,
            "abilities": [], "abilityCooldowns": {}, "utilitySlots": [None, None, None], "toolSlots": [None, None],
            "weapon": None, "armor": None,
            "damageBoostUntil": 0, "damageBoost": 1, "speedBoostUntil": 0, "speedBoost": 1,
            "invisibleUntil": 0, "tauntUntil": 0,
            "specialAttacks": 0, "specialAttackFactor": 1,
            "curse": None, "chestReward": None, "shopStock": [], "townInteraction": None,
            "townInterior": None, "townReturn": None, "townExitReady": False,
            "classChangeUsed": False,
            "guildPreview": None,
            "deathRecorded": False,
            "activeSummons": {}, "skillPoints": 0, "skillRanks": {key: 0 for key in progression.SKILLS},
            "skillRewards": [], "trainingKnown": False, "questAccepted": False, "dialogue": None, "innFloor": 1,
            "connected": True, "lastSeen": time.monotonic(), "lastInputAt": time.monotonic(), "lastPing": -10,
        }

    def create_room(self, name: str) -> tuple[str, str]:
        with self.lock:
            code = self._new_code()
            player_id = secrets.token_urlsafe(9)
            room = {
                "code": code, "host": player_id, "phase": "lobby", "stage": 0, "region": "woodland",
                "players": {}, "enemies": [], "summons": [], "chat": [], "runes": 0,
                "wave": 0, "created": time.time(), "messageId": 0, "puzzle": None, "strainMistakes": 0,
                "routes": [], "routeVotes": {}, "routePressure": 0, "routeEffect": None,
                "revealedRoute": None, "town": None, "shopStock": {}, "checkpoint": None,
                "bossSequence": [], "bossesDefeated": 0, "miniBossesSinceBoss": 0,
                "miniBossesRequired": 0, "regularWavesSinceMiniBoss": 0,
                "regularWavesRequired": 0, "encounterType": "normal", "encounterName": "",
                "chest": None, "effects": [], "projectiles": [], "stageWave": 1, "stageWaves": 3,
                "waveStartsAt": 0,
                "miniBossStages": [], "bossStages": [8, 16, 25], "puzzlesRequired": 1,
                "puzzlesCompleted": 0, "puzzleStages": [], "townsTarget": 0, "townsVisited": 0, "townStages": [],
                "pings": [], "hazards": [], "stageReports": [], "runStats": {}, "runId": secrets.token_hex(8),
                "difficulty": "medium", "totalStages": 25,
            }
            room["players"][player_id] = self._player(player_id, name or "Player")
            progression.defaults(room)
            self.rooms[code] = room
            return code, player_id

    def join_room(self, code: str, name: str) -> tuple[str, str | None]:
        with self.lock:
            room = self.rooms.get(code.upper())
            if not room:
                raise ValueError("That room code was not found.")
            if room["phase"] != "lobby":
                raise ValueError("This run has already started.")
            if len(room["players"]) >= MAX_PLAYERS:
                raise ValueError("This room is full.")
            player_id = secrets.token_urlsafe(9)
            room["players"][player_id] = self._player(player_id, name or "Player")
            return code.upper(), player_id

    def state(self, code: str, player_id: str) -> dict:
        with self.lock:
            room = self.rooms.get(code.upper())
            if not room or player_id not in room["players"]:
                raise ValueError("Room or player not found.")
            self._touch_player(room, room["players"][player_id])
            self._update_presence(room, time.monotonic())
            own = room['players'][player_id]
            now = time.monotonic()
            speed = CLASSES.get(own['class'], {}).get('speed', 140)
            if room['phase'] == 'combat' and not room.get('waveStartsAt'):
                speed *= own['speedBoost'] if own['speedBoostUntil'] > now else 1
                speed *= .75 if (own.get('curse') or {}).get('effect') == 'sluggish' else 1
            players = []
            for player in room["players"].values():
                class_data = CLASSES.get(player["class"], {})
                players.append({
                    "id": player["id"], "name": player["name"], "class": player["class"], "bot": player.get("bot", False),
                    "hp": player["hp"], "maxHp": player["maxHp"], "x": round(player["x"], 1),
                    "damageTaken": player.get("damageTaken", 0),
                    "y": round(player["y"], 1), "status": player["status"], "reviving": bool(player.get("reviving")),
                    "color": class_data.get("color", "#e7e2d8"),
                    "role": class_data.get("role", "Choose a class"),
                    "weaponColor": (player.get("weapon") or {}).get("color"),
                    "armorColor": (player.get("armor") or {}).get("color"),
                    "facingX": player.get("facingX", 0), "facingY": player.get("facingY", 1),
                    "moving": bool(player.get("dx", 0) or player.get("dy", 0)),
                    "animation": player.get("animation", "idle"),
                    "animationUntil": player.get("animationUntil", 0),
                "abilityCount": len(player["abilities"]),
                    "invisible": player["invisibleUntil"] > time.monotonic(),
                    "indoors": bool(player.get("townInterior")),
                    "townExitReady": bool(player.get("townExitReady")),
                    "connected": player.get("connected", True),
                })
            return {
                "code": room["code"], "host": room["host"], "you": player_id,
                "activePartySize": len(self._active_players(room)),
                "activeVoterCount": len(self._voting_players(room)),
                "difficulty": room.get("difficulty", "medium"), "difficulties": DIFFICULTIES,
                "totalStages": room.get("totalStages", 25), "pouchCapacity": POUCH_CAPACITY,
                "testerMode": room.get("totalStages") == 9, "balanceStage": self._effective_stage(room),
                "npcCompanion": any(p.get("bot") for p in room["players"].values()),
                "pings": [dict(p) for p in room.get("pings", []) if p["expiresAt"] > time.monotonic()],
                "checkpointSavedAt": room.get("checkpointSavedAt"),
                "checkpointStage": (room.get('checkpoint') or {}).get('stage'),
                "dialogue": progression.dialogue(room["players"][player_id]),
                "movementLocked": progression.locked(room, room["players"][player_id]),
                "movement": {"x":own['x'], "y":own['y'], "age":max(0,now-own['lastMove']),
                    "speed":speed, "slideVx":own.get('slideVx',0), "slideVy":own.get('slideVy',0),
                    "sequence":own.get('inputSequence',0)},
                "story": copy.deepcopy(room.get("story", {})),
                "questAccepted": room["players"][player_id].get("questAccepted", False),
                "townWelcome": copy.deepcopy(room.get("townWelcome")),
                "innFloor": room["players"][player_id].get("innFloor", 1),
                "innRooms": copy.deepcopy(room.get("innRooms", [])),
                "trainingKnown": room["players"][player_id].get("trainingKnown", False),
                "skillPoints": room["players"][player_id].get("skillPoints", 0),
                "skillRanks": copy.deepcopy(room["players"][player_id].get("skillRanks", {})),
                "skills": progression.SKILLS,
                "firstTownTrainingRequired": room.get("townsVisited") == 1 and any(not p.get("trainingKnown") for p in self._active_players(room) if not p.get("bot")),
                "phase": room["phase"], "stage": room["stage"], "wave": room["wave"], "region": room.get("region", "woodland"),
                "bossesDefeated": room["bossesDefeated"], "bossesTotal": 3,
                "attackRange": CLASSES.get(room["players"][player_id]["class"], {}).get("range", 0),
                "miniBossesDefeated": room["miniBossesSinceBoss"],
                "miniBossesRequired": room["miniBossesRequired"], "encounterType": room["encounterType"],
                "encounterName": room["encounterName"],
                "chestStatus": ("pending" if room["phase"] == "chest" and room["players"][player_id]["chestReward"] else
                                "done" if room["phase"] == "chest" and player_id in room["chest"]["decisions"] else
                                "nearby" if room["phase"] == "chest" and room["chest"] and math.hypot(room["players"][player_id]["x"] - room["chest"]["x"], room["players"][player_id]["y"] - room["chest"]["y"]) <= 62 else
                                "unopened" if room["phase"] == "chest" else None),
                "chestDecision": room["chest"]["decisions"].get(player_id) if room["phase"] == "chest" and room["chest"] else None,
                "chestOpenedCount": sum(p["id"] in room["chest"]["decisions"] for p in self._active_players(room)) if room["chest"] else 0,
                "chestTotal": len(self._active_players(room)) if room["phase"] == "chest" else 0,
                "chestReward": dict(room["players"][player_id]["chestReward"]) if room["players"][player_id]["chestReward"] else None,
                "curse": dict(room["players"][player_id]["curse"]) if room["players"][player_id]["curse"] else None,
                "privateNotice": room.get("privateNotices", {}).pop(player_id, ""),
                "runes": room["runes"], "players": players, "classes": CLASSES,
                "mana": round(room["players"][player_id]["mana"], 1),
                "maxMana": room["players"][player_id]["maxMana"],
                "dashCooldown": max(0, math.ceil(room["players"][player_id].get("dashCooldownUntil", 0) - time.monotonic())),
                "enemies": [
                    {k: enemy[k] for k in ("id", "name", "kind", "affinity", "color", "x", "y", "hp", "maxHp")}
                    | {"boss": enemy.get("boss", False), "bossPhase": enemy.get("bossPhase", 1),
                       "bossAttack": enemy_roles.attack_view(enemy.get("pendingAttack"), time.monotonic()),
                       "roleAttack": enemy_roles.attack_view(enemy.get("roleAttack"), time.monotonic()),
                       "combatRole": enemy.get("combatRole"),
                       "rooted": enemy.get("rootUntil", 0) > time.monotonic(),
                       "bleeding": enemy.get("bleedUntil", 0) > time.monotonic(),
                       "vulnerable": enemy.get("vulnerableUntil", 0) > time.monotonic(),
                       "recovering": max(enemy.get("recoverUntil", 0), enemy.get("roleRecoverUntil", 0)) > time.monotonic(),
                       "charging": max(enemy.get("chargeUntil", 0), enemy.get("roleChargeUntil", 0)) > time.monotonic(),
                       "miniBoss": enemy.get("miniBoss", False), "class": enemy.get("class", "Knight"),
                       "damageTaken": enemy.get("damageTaken", 0),
                       "baseColor": enemy.get("baseColor", "#85977a"), "facingX": enemy.get("facingX", 0),
                       "facingY": enemy.get("facingY", 1), "moving": enemy.get("moving", False),
                       "animation": "light", "animationUntil": enemy.get("animationUntil", 0)}
                    for enemy in room["enemies"]
                ],
                "chat": room["chat"][-40:], "puzzle": player_puzzle_view(room["puzzle"], player_id,
                    (room["players"][player_id]["x"], room["players"][player_id]["y"])),
                "effects": [dict(effect) for effect in room["effects"]],
                "environment": terrain.view(room, time.monotonic()),
                "objective": combat_encounters.view(room, time.monotonic()),
                "bossIntel": boss_ai.view(room),
                "preferredTarget": own.get('preferredTarget'),
                "hazards": [dict(h, windupLeft=max(0, h["activatesAt"]-time.monotonic()),
                                 active=time.monotonic() >= h["activatesAt"]) for h in room.get("hazards", [])],
                "companionClue": next((pr["clue"] for pr in (room.get("puzzle") or {}).get("rooms", {}).values()
                                      if pr.get("clueFor") == player_id and pr.get("totemSeen") and
                                      any(p.get("bot") and (room.get("puzzle") or {}).get("rooms", {}).get(p["id"]) is pr
                                          for p in room["players"].values())), None),
                "summons": [{key: summon[key] for key in (
                    "id", "ownerId", "abilityId", "name", "kind", "affinity", "color", "x", "y", "hp", "maxHp",
                    "damageTaken", "facingX", "facingY", "moving", "animationUntil")}
                    for summon in room.get("summons", [])],
                "projectiles": [dict(projectile) for projectile in room["projectiles"]],
                "stageWave": room["stageWave"], "stageWaves": room["stageWaves"],
                "waveCountdown": max(0, math.ceil(room.get("waveStartsAt", 0) - time.monotonic())) if room.get("waveStartsAt") else 0,
                "puzzlesCompleted": room["puzzlesCompleted"], "puzzlesRequired": room["puzzlesRequired"],
                "routes": [
                    {"id": route["id"], "name": route["name"],
                     "x": route["x"], "y": route["y"],
                     "votes": sum(room["routeVotes"].get(p["id"]) == route["id"] for p in self._voting_players(room)),
                     "easier": room["revealedRoute"] == route["id"]}
                    for route in room["routes"]
                ],
                "yourRouteVote": room["routeVotes"].get(player_id),
                "stageExitReady": sum(self._at_stage_exit(member) for member in self._voting_players(room)) if room["phase"] == "stage_exit" else 0,
                "assassinationActive": room["phase"] == "combat" and room["encounterType"] == "assassination",
                "inventory": [dict(item) for item in room["players"][player_id]["inventory"]],
                "town": room["town"],
                "shopStock": [dict(item) for item in room["players"][player_id]["shopStock"]] if room["phase"] == "town" else [],
                "townInteraction": room["players"][player_id].get("townInteraction"),
                "classChangeUsed": room["players"][player_id].get("classChangeUsed", False),
                "guildPreview": copy.deepcopy(room["players"][player_id].get("guildPreview")),
                "townInterior": room["players"][player_id].get("townInterior"),
                "nearbyNpc": self._nearby_npc(room, room["players"][player_id]) if room["phase"] in ("town", "peace") else None,
                "townNpcs": self._town_npcs(room, room["players"][player_id]) if room["phase"] == "town" else {},
                "townHouses": copy.deepcopy(room.get("townLayout", [])) if room["phase"] == "town" else [],
                "townPaths": copy.deepcopy(room.get("townPaths", [])) if room["phase"] == "town" else [],
                "townVillagers": copy.deepcopy(room.get("townVillagers", [])) if room["phase"] == "town" else [],
                "townDecor": copy.deepcopy(room.get("townDecor", {})) if room["phase"] == "town" else {},
                "townSeed": room.get("townSeed", 0),
                "nearbyHouse": self._nearby_house(room, room["players"][player_id]) if room["phase"] == "town" else None,
                "townExitVotes": sum(1 for member in self._voting_players(room) if member.get("townExitReady")),
                "townExitTotal": len(self._voting_players(room)) if room["phase"] == "town" else 0,
                "nearRoute": self._near_route(room, room["players"][player_id]) if room["phase"] == "routes" else None,
                "chest": dict(room["chest"], opened=bool(player_id in room["chest"]["decisions"] or room["players"][player_id]["chestReward"])) if room["phase"] == "chest" and room["chest"] else None,
                "canResumeAtCheckpoint": bool(room["checkpoint"]),
                "abilityOptions": {name: [ability_record(ability) for ability in options] for name, options in ABILITY_SETS.items()},
                "selectedAbilities": list(room["players"][player_id]["abilities"]),
                "abilitySlots": self._ability_slots(room["players"][player_id]),
                "utilitySlots": [dict(item) if item else None for item in room["players"][player_id]["utilitySlots"]],
                "toolSlots": [dict(item) if item else None for item in room["players"][player_id]["toolSlots"]],
            }

    def run_stats(self, code: str, player_id: str) -> list:
        with self.lock:
            room = self.rooms.get(code.upper())
            if not room or player_id not in room["players"]:
                raise ValueError("Room or player not found.")
            return telemetry.overall(room)

    def _configure_companion(self, room, enabled):
        bots = [p for p in room["players"].values() if p.get("bot")]
        if enabled and not bots:
            if len(room["players"]) >= MAX_PLAYERS:
                raise ValueError("The companion needs one of the four party slots.")
            pid = "npc_"+secrets.token_hex(6)
            bot = self._player(pid, "NPC Companion")
            bot["bot"] = True
            room["players"][pid] = bot
        elif not enabled:
            for bot in bots:
                del room["players"][bot["id"]]

    def _choose_companion_hero(self, room):
        taken = {p["class"] for p in room["players"].values() if not p.get("bot")}
        for bot in room["players"].values():
            if not bot.get("bot"):
                continue
            hero = random.choice([hero for hero in CLASSES if hero not in taken])
            bot.update(name=hero+" Companion", **{"class": hero}, hp=CLASSES[hero]["hp"], maxHp=CLASSES[hero]["hp"])
            bot["abilities"] = [random.choice([a[0] for a in ABILITY_SETS[hero] if a[7] == category])
                                for category in ("light", "special", "ultimate")]
            taken.add(hero)

    def _share_clue(self, room, player):
        view = player_puzzle_view(room.get("puzzle"), player["id"], (player["x"], player["y"]))
        if room["phase"] != "puzzle" or not view or not view["clue"]:
            raise ValueError("Read your totem before sharing its clue.")
        own = room["puzzle"]["rooms"][player["id"]]
        own["totemSeen"] = True
        self._say(room, player["id"], player["name"], f"Clue for {view['clueForName']}: {view['clue']}")
        recipient = room["players"].get(own["clueFor"])
        if recipient and recipient.get("bot"):
            recipient["aiRunePuzzle"] = room["puzzle"]["id"]
            recipient["aiMoveAt"] = 0
            self._say(room, recipient["id"], recipient["name"], "Thanks! I'll take the rune you described.")

    def action(self, code: str, player_id: str, payload: dict) -> None:
        with self.lock:
            room = self.rooms.get(code.upper())
            if not room or player_id not in room["players"]:
                raise ValueError("Room or player not found.")
            self._touch_player(room, room["players"][player_id])
            self._action(code, player_id, payload)
            room = self.rooms.get(code.upper())
            if room and payload.get("action") not in ("input", "ping", "chat", "revive", "stopRevive", "disconnect"):
                self._save_checkpoint(room)

    def _action(self, code: str, player_id: str, payload: dict) -> None:
        with self.lock:
            room = self.rooms.get(code.upper())
            if not room or player_id not in room["players"]:
                raise ValueError("Room or player not found.")
            action = str(payload.get("action", ""))
            if action == "disconnect":
                self._disconnect_player(room, room["players"][player_id])
                self._update_presence(room, time.monotonic())
                return
            if action == "ping":
                self._ping(room, room["players"][player_id], payload)
                return
            if action == "leaveRoom":
                self._dismiss_summons(room, player_id)
                del room["players"][player_id]
                if not any(not member.get("bot") for member in room["players"].values()):
                    self._finish_stage_stats(room, "abandoned")
                    if self.storage:
                        self.storage.delete(room["code"])
                    del self.rooms[code.upper()]
                    return
                if room["host"] == player_id:
                    room["host"] = next(pid for pid, member in room["players"].items() if not member.get("bot"))
                for member in room["players"].values():
                    if member.get("reviving") == player_id:
                        member["reviving"] = None
                if room["phase"] == "puzzle":
                    room["puzzle"] = self._new_puzzle(room)
                elif room["phase"] == "routes":
                    room["routeVotes"].pop(player_id, None)
                    if self._routes_ready(room):
                        self._resolve_routes(room)
                elif room["phase"] == "chest" and room["chest"]:
                    room["chest"]["decisions"].pop(player_id, None)
                    self._finish_chest_if_ready(room)
                self._say(room, "system", "The Gauntlet", "A player returned to the main menu.")
                return
            player = room["players"][player_id]
            if action == "dialogueNext":
                progression.advance(self, room, player, payload)
            elif action == "trainSkill":
                progression.train(self, room, player, payload.get("branch"), CLASSES)
            elif action == "runOptions":
                if room["phase"] != "lobby" or player_id != room["host"]:
                    raise ValueError("Only the host can change options before the run.")
                difficulty = payload.get("difficulty", room.get("difficulty", "medium"))
                enabled = payload.get("companion", any(p.get("bot") for p in room["players"].values()))
                if not isinstance(difficulty, str) or difficulty not in DIFFICULTIES or not isinstance(enabled, bool):
                    raise ValueError("Choose Easy, Medium or Hard and a valid companion option.")
                stages=payload.get('stages',room['totalStages'] if room.get('lengthChosen') else DIFFICULTIES[difficulty]['stages'])
                if not isinstance(stages,int) or isinstance(stages,bool) or stages not in (9,20,25,30):
                    raise ValueError('Choose Tester (9 stages), or a 20, 25 or 30 stage run.')
                self._configure_companion(room, enabled)
                room.update(difficulty=difficulty, totalStages=stages,lengthChosen='stages' in payload or room.get('lengthChosen',False))
            elif action == 'target':
                target_id=payload.get('targetId')
                if target_id is not None and (room['phase']!='combat' or not any(e['id']==target_id for e in room['enemies'])):
                    raise ValueError('That target is no longer on the field.')
                player['preferredTarget']=target_id
            elif action == "shareClue":
                self._share_clue(room, player)
            elif action == "class":
                chosen = str(payload.get("class", ""))
                if room["phase"] != "lobby":
                    raise ValueError("Class selection is closed for this run.")
                if chosen not in CLASSES:
                    raise ValueError("Unknown class.")
                if any(p["class"] == chosen for pid, p in room["players"].items() if pid != player_id):
                    raise ValueError("That class is already taken.")
                if player["class"] == chosen:
                    return
                player["class"] = chosen
                player["maxHp"] = progression.max_hp(player, CLASSES)
                player["hp"] = player["maxHp"]
                player["abilities"] = []
                player["abilityCooldowns"] = {}
            elif action == "loadout":
                if room["phase"] != "lobby" or not player["class"]:
                    raise ValueError("Choose a class before setting abilities.")
                selected = payload.get("abilities")
                allowed = {ability[0] for ability in ABILITY_SETS[player["class"]]}
                if (not isinstance(selected, list) or len(selected) > 3 or
                        not all(isinstance(item, str) for item in selected) or
                        len(set(selected)) != len(selected) or any(item not in allowed for item in selected)):
                    raise ValueError("Choose one ability from each category.")
                category_by_id = {ability[0]: ability[7] for ability in ABILITY_SETS[player["class"]]}
                categories = [category_by_id[item] for item in selected]
                if len(set(categories)) != len(categories):
                    raise ValueError("Choose one Light, one Special, and one Ultimate ability.")
                player["abilities"] = [next((item for item in selected if category_by_id[item] == category), None)
                                        for category in ("light", "special", "ultimate") if any(c == category for c in categories)]
            elif action == "chat":
                message = str(payload.get("message", "")).strip()[:240]
                if message:
                    self._say(room, player_id, player["name"], message)
            elif action == "guildPreview":
                chosen = str(payload.get("class", ""))
                self._validate_guild_class(room, player, chosen)
                preview = player.get("guildPreview")
                if not preview or preview["class"] != chosen:
                    options = []
                    for category in ("light", "special", "ultimate"):
                        choices = [ability_record(a) for a in ABILITY_SETS[chosen] if a[7] == category]
                        random.shuffle(choices)
                        options.extend(choices)
                    player["guildPreview"] = {"class": chosen, "options": options,
                                              "selected": [options[i]["id"] for i in (0, 2, 4)]}
            elif action == "guildBack":
                player["guildPreview"] = None
            elif action == "guildChange":
                preview = player.get("guildPreview")
                if not preview:
                    raise ValueError("Choose a hero with the Guildmaster first.")
                chosen = preview["class"]
                self._validate_guild_class(room, player, chosen)
                selected = payload.get("abilities")
                options = {a["id"]: a for a in preview["options"]}
                if (not isinstance(selected, list) or len(selected) != 3 or
                        not all(isinstance(a, str) and a in options for a in selected) or
                        {options[a]["attackType"] for a in selected} != {"light", "special", "ultimate"}):
                    raise ValueError("Choose one Light, one Special, and one Ultimate ability.")
                health_fraction = player["hp"] / player["maxHp"]
                old_class = player["class"]
                self._dismiss_summons(room, player_id)
                player["class"] = chosen
                player["maxHp"] = progression.max_hp(player, CLASSES)
                player["hp"] = max(1, min(player["maxHp"], round(player["maxHp"] * health_fraction)))
                player["abilities"] = [next(a for a in selected if options[a]["attackType"] == category)
                                       for category in ("light", "special", "ultimate")]
                player["abilityCooldowns"] = {}
                player["dashCooldownUntil"] = 0
                for key in ("invisibleUntil", "tauntUntil"):
                    player[key] = 0
                player["classChangeUsed"] = True
                player["guildPreview"] = None
                player["townInteraction"] = None
                self._stock_shop(room, player)
                if room["checkpoint"] and room["checkpoint"].get("townInstance", room["townInstance"]) == room["townInstance"]:
                    room["checkpoint"]["shopStock"][player_id] = copy.deepcopy(player["shopStock"])
                room.setdefault("privateNotices", {})[player_id] = f"You are now a {chosen}. Your class change for this run has been used."
                self._say(room, "system", "Guildmaster", f"{player['name']} changed from {old_class} to {chosen}.")
            elif action == "input":
                if 'sequence' in payload:
                    sequence = int(payload['sequence'])
                    if sequence <= player.get('inputSequence',0): return
                    player['inputSequence'] = sequence
                player["lastInputAt"] = time.monotonic()
                if 'targetId' in payload:
                    player['preferredTarget']=payload['targetId'] if any(e['id']==payload['targetId'] for e in room['enemies']) else None
                if room["phase"] not in ("combat", "town", "routes", "stage_exit", "puzzle", "chest", "peace") or player["status"] != "alive":
                    return
                if progression.locked(room, player) or (room["phase"] == "town" and player.get("townInteraction") == "guildmaster"):
                    player["dx"], player["dy"] = 0, 0
                    return
                dx = max(-1, min(1, float(payload.get("x", 0))))
                dy = max(-1, min(1, float(payload.get("y", 0))))
                length = math.hypot(dx, dy)
                if length > 1:
                    dx, dy = dx / length, dy / length
                player["dx"], player["dy"] = dx, dy
                if length > 0.05:
                    player["facingX"], player["facingY"] = dx, dy
                was_attacking = player["attacking"]
                player["attacking"] = bool(payload.get("attack", False))
                if player["attacking"] and not was_attacking:
                    self._attack(room, player)
            elif action == "dash":
                now = time.monotonic()
                if room["phase"] != "combat" or player["status"] != "alive":
                    raise ValueError("Dash is available during combat while standing.")
                if player.get("dashCooldownUntil", 0) > now:
                    raise ValueError(f"Dash recharges in {math.ceil(player['dashCooldownUntil'] - now)} seconds.")
                dx, dy = player.get("dx", 0), player.get("dy", 0)
                if math.hypot(dx, dy) < 0.05:
                    dx, dy = player.get("facingX", 1), player.get("facingY", 0)
                length = max(0.001, math.hypot(dx, dy))
                dx, dy = dx / length, dy / length
                start_x, start_y = player["x"], player["y"]
                terrain.move(room, player, player["x"] + dx * 116, player["y"] + dy * 116)
                player["facingX"], player["facingY"] = dx, dy
                player["dashCooldownUntil"] = now + 5
                tactical.dashed(player, now, math.hypot(player['x']-start_x, player['y']-start_y))
                self._add_effect(room, "dash", start_x, start_y, CLASSES.get(player["class"], {}).get("color", "#ffffff"),
                                 player["x"], player["y"], 0.32, attack_class=player["class"] or "")
            elif action == "attack":
                self._attack(room, player)
            elif action == "revive":
                self._revive(room, player)
            elif action == "stopRevive":
                player['reviving'] = None
                player['rescueGuardUntil'] = 0
            elif action == "interact":
                self._interact(room, player)
            elif action == "routeVote":
                if player.get("bot"):
                    return
                if room["phase"] != "routes":
                    raise ValueError("There is no route choice right now.")
                route_id = str(payload.get("route", ""))
                if route_id not in {route["id"] for route in room["routes"]}:
                    raise ValueError("That route is no longer available.")
                route = next(route for route in room["routes"] if route["id"] == route_id)
                if math.hypot(player["x"] - route["x"], player["y"] - route["y"]) > 72 or 52 < player["x"] < WIDTH - 52:
                    raise ValueError("Follow the trail all the way to the screen edge before choosing it.")
                room["routeVotes"][player_id] = route_id
                self._say(room, "system", "The Gauntlet", f"{player['name']} votes for {next(r['name'] for r in room['routes'] if r['id'] == route_id)}.")
                if self._routes_ready(room):
                    self._resolve_routes(room)
            elif action == "shopBuy":
                if room["phase"] != "town":
                    raise ValueError("The shop is open in town.")
                item_key = str(payload.get("item", ""))
                if not self._at_merchant(room, player):
                    raise ValueError("Visit the merchant before buying.")
                stock = next((entry for entry in player["shopStock"] if entry["key"] == item_key), None)
                if not stock:
                    raise ValueError("That item is not in stock.")
                if len(player["inventory"]) >= POUCH_CAPACITY:
                    raise ValueError("Your ten-item pouch is full.")
                if room["runes"] < stock["price"]:
                    raise ValueError("The party does not have enough Runes.")
                room["runes"] -= stock["price"]
                player["inventory"].append(self._make_item(item_key, stock["price"]))
                player["shopStock"].remove(stock)
                if room["checkpoint"] and room["checkpoint"].get("townInstance", room["townInstance"]) == room["townInstance"]:
                    room["checkpoint"]["shopStock"][player_id] = copy.deepcopy(player["shopStock"])
                self._say(room, "system", "The Gauntlet", f"{player['name']} bought {ITEMS[item_key]['name']}.")
            elif action == "shopSell":
                if room["phase"] != "town":
                    raise ValueError("Items can be sold in town.")
                if not self._at_merchant(room, player):
                    raise ValueError("Visit the merchant before selling.")
                item_id = str(payload.get("item", ""))
                item = next((entry for entry in player["inventory"] if entry["id"] == item_id), None)
                if not item:
                    raise ValueError("That item is not in your pouch.")
                player["inventory"].remove(item)
                room["runes"] += item["sell"]
                self._say(room, "system", "The Gauntlet", f"{player['name']} sold {item['name']} for {item['sell']} Runes.")
            elif action == "closeShop":
                player["townInteraction"] = None
                player["guildPreview"] = None
            elif action == "useItem":
                item_id = str(payload.get("item", ""))
                item = next((entry for entry in player["inventory"] + [i for i in player["utilitySlots"] if i] if entry["id"] == item_id), None)
                if not item:
                    raise ValueError("That item is not in your pouch.")
                if item["kind"] == "heal":
                    if room["phase"] not in ("town", "combat") or player["status"] != "alive":
                        raise ValueError("You can use a healing draught while alive in combat or town.")
                    if player["hp"] >= player["maxHp"]:
                        raise ValueError("You are already at full health.")
                    player["hp"] = min(player["maxHp"], player["hp"] + item.get("heal", 40))
                elif item["kind"] == "ward":
                    if room["phase"] != "combat" or player["status"] != "alive":
                        raise ValueError("A warding item can be used during combat.")
                    player["wardUntil"] = time.monotonic() + item.get("duration", 30)
                    player["wardFactor"] = item.get("factor", 0.6)
                    player["wardSource"] = player["id"]
                elif item["kind"] == "hint":
                    if room["phase"] != "routes" or not room["routes"]:
                        raise ValueError("Save the lens for a route fork.")
                    easiest = min(route["danger"] for route in room["routes"])
                    room["revealedRoute"] = next(route["id"] for route in room["routes"] if route["danger"] == easiest)
                elif item["kind"] == "mana":
                    if room["phase"] not in ("combat", "town") or player["status"] != "alive":
                        raise ValueError("A Mana Draught can be used while alive in combat or town.")
                    if player["mana"] >= player["maxMana"]:
                        raise ValueError("Your mana is already full.")
                    player["mana"] = min(player["maxMana"], player["mana"] + item.get("mana", 50))
                elif item["kind"] == "buff":
                    if room["phase"] != "combat" or player["status"] != "alive":
                        raise ValueError("A damage tonic can be used while alive in combat.")
                    player["damageBoostUntil"] = max(player["damageBoostUntil"], time.monotonic() + item.get("duration", 10))
                    player["damageBoost"] = item.get("factor", 1.4)
                    player["damageBoostSource"] = player["id"]
                elif item["kind"] == "speed":
                    if room["phase"] != "combat" or player["status"] != "alive":
                        raise ValueError("A speed elixir can be used while alive in combat.")
                    player["speedBoostUntil"] = max(player["speedBoostUntil"], time.monotonic() + item.get("duration", 10))
                    player["speedBoost"] = max(player["speedBoost"], item.get("factor", 1.45))
                elif item["kind"] == "arrows":
                    if room["phase"] != "combat" or player["status"] != "alive":
                        raise ValueError("Special arrows can be prepared while alive in combat.")
                    player["specialAttacks"] = item.get("attacks", 5)
                    player["specialAttackFactor"] = item.get("factor", 1.5)
                else:
                    raise ValueError("That item cannot be used here.")
                if item in player["inventory"]:
                    player["inventory"].remove(item)
                else:
                    slot = player["utilitySlots"].index(item)
                    player["utilitySlots"][slot] = None
                self._say(room, "system", "The Gauntlet", f"{player['name']} used {item['name']}.")
            elif action == "equipItem":
                item_id = str(payload.get("item", ""))
                slot_index = int(payload.get("slot", -1))
                item = next((entry for entry in player["inventory"] if entry["id"] == item_id), None)
                if not item:
                    raise ValueError("That item is not in your pouch.")
                if item["slot"] == "utility":
                    if not 0 <= slot_index < 3:
                        raise ValueError("Choose one of the three utility slots.")
                    displaced = player["utilitySlots"][slot_index]
                    player["utilitySlots"][slot_index] = item
                elif item["slot"] == "tool":
                    if not 0 <= slot_index < 2:
                        raise ValueError("Choose one of the two tool slots.")
                    displaced = player["toolSlots"][slot_index]
                    player["toolSlots"][slot_index] = item
                    player["weapon"] = next((gear for gear in player["toolSlots"] if gear and gear["kind"] == "weapon"), None)
                    player["armor"] = next((gear for gear in player["toolSlots"] if gear and gear["kind"] == "armor"), None)
                else:
                    raise ValueError("That item cannot be equipped.")
                player["inventory"].remove(item)
                if displaced:
                    player["inventory"].append(displaced)
                for summon in room.get('summons', []):
                    if summon['ownerId']==player['id']:
                        tactical.refresh_summon_health(player, summon, SUMMON_TYPES[summon['abilityId']])
                self._say(room, "system", "The Gauntlet", f"{player['name']} equipped {item['name']}.")
            elif action == "unequipItem":
                slot_kind = str(payload.get("slotKind", ""))
                slot_index = int(payload.get("slot", -1))
                slots = player["utilitySlots"] if slot_kind == "utility" else player["toolSlots"] if slot_kind == "tool" else []
                if not 0 <= slot_index < len(slots) or not slots[slot_index]:
                    raise ValueError("That equipment slot is empty.")
                if len(player["inventory"]) >= POUCH_CAPACITY:
                    raise ValueError("Your pouch is full; make room before unequipping.")
                item = slots[slot_index]
                slots[slot_index] = None
                player["inventory"].append(item)
                for summon in room.get('summons', []):
                    if summon['ownerId']==player['id']:
                        tactical.refresh_summon_health(player, summon, SUMMON_TYPES[summon['abilityId']])
                if slot_kind == "tool":
                    player["weapon"] = next((gear for gear in player["toolSlots"] if gear and gear["kind"] == "weapon"), None)
                    player["armor"] = next((gear for gear in player["toolSlots"] if gear and gear["kind"] == "armor"), None)
                self._say(room, "system", "The Gauntlet", f"{player['name']} unequipped {item['name']}.")
            elif action == "townContinue":
                self._vote_town_exit(room, player)
            elif action == "ability":
                slot_index = int(payload.get("slot", 0)) - 1
                if room["phase"] != "combat" or player["status"] != "alive" or not 0 <= slot_index < 3:
                    raise ValueError("Use an ability slot during combat while standing.")
                self._cast_ability(room, player, slot_index)
            elif action == "checkpointResume":
                if player_id != room["host"] or room["phase"] != "defeat" or not room["checkpoint"]:
                    raise ValueError("The host can return the party to its last inn after a wipe.")
                self._dismiss_summons(room)
                room["stage"] = room["checkpoint"]["stage"]
                room["wave"] = room["checkpoint"]["wave"]
                room["town"] = room["checkpoint"]["town"]
                room["region"] = room["checkpoint"].get("region", "woodland")
                for member_id, party_member in room["players"].items():
                    party_member["shopStock"] = copy.deepcopy(room["checkpoint"]["shopStock"].get(member_id, []))
                for key in ("bossesDefeated", "miniBossesSinceBoss", "miniBossesRequired",
                            "regularWavesSinceMiniBoss", "regularWavesRequired", "bossSequence", "stageWave", "stageWaves",
                            "miniBossStages", "bossStages", "puzzlesRequired", "puzzlesCompleted", "puzzleStages",
                            "townsTarget", "townsVisited", "townStages", "townLayout", "townSeed"):
                    room[key] = copy.deepcopy(room["checkpoint"][key])
                for key in ("difficulty", "totalStages"):
                    room[key] = room["checkpoint"].get(key, room.get(key, "medium" if key == "difficulty" else 25))
                for key in ("townInstance", "innRooms"):
                    if key in room["checkpoint"]:
                        room[key] = copy.deepcopy(room["checkpoint"][key])
                for key in ('objectiveStages','townPressureStages','lengthChosen'):
                    room[key]=copy.deepcopy(room['checkpoint'].get(key,{} if key=='objectiveStages' else [] if key=='townPressureStages' else False))
                room['objective']=None
                room["townWelcome"] = None
                room["hazards"] = []
                for key in ("townPaths", "townVillagers", "townDecor"):
                    room[key] = copy.deepcopy(room["checkpoint"].get(key, room.get(key, [] if key != "townDecor" else {})))
                room.update(nextTown=None, forkPending=False)
                room["enemies"] = []
                room["waveStartsAt"] = 0
                for party_member in room["players"].values():
                    party_member["status"] = "alive"
                    party_member["deathRecorded"] = False
                    party_member["hp"] = party_member["maxHp"]
                    party_member["mana"] = party_member["maxMana"]
                    party_member["x"], party_member["y"] = 480, 460
                    party_member["dx"], party_member["dy"] = 0, 0
                    party_member["townInterior"] = None
                    party_member["townReturn"] = None
                    party_member["townExitReady"] = False
                    party_member["townInteraction"] = None
                    party_member["guildPreview"] = None
                    party_member["attacking"] = False
                    party_member["reviving"] = None
                    party_member["wardUntil"] = 0
                    party_member["wardFactor"] = 1.0
                    party_member["damageBoostUntil"] = 0
                    party_member["speedBoostUntil"] = 0
                    party_member["specialAttacks"] = 0
                    party_member["specialAttackFactor"] = 1
                room["phase"] = "town"
                for p in room["players"].values():
                    progression.place_at_checkpoint(room, p)
                self._say(room, "system", "The Gauntlet", "The party returns to its last inn. Carried items remain.")
            elif action == "openChest":
                if room["phase"] != "chest" or not room["chest"]:
                    raise ValueError("There is no chest to open right now.")
                if math.hypot(player["x"] - room["chest"]["x"], player["y"] - room["chest"]["y"]) > 62:
                    raise ValueError("Walk up to the chest before opening it.")
                if player_id in room["chest"]["decisions"] or player["chestReward"]:
                    raise ValueError("You have already made your chest choice.")
                if not room["chest"]["runesAwarded"]:
                    chest_runes = random.randint(5, 12)
                    room["runes"] += chest_runes
                    room["chest"]["runesAwarded"] = True
                    room.setdefault("privateNotices", {})[player_id] = f"Chest opened: {chest_runes} shared Runes."
                    self._say(room, "system", "The Gauntlet", f"The opened chest contains {chest_runes} shared Runes.")
                if not player["curse"] and random.random() < 0.12:
                    curse = dict(random.choice(CURSES))
                    curse["remainingStages"] = 5
                    player["curse"] = curse
                    room["chest"]["decisions"][player_id] = "opened"
                    room.setdefault("privateNotices", {})[player_id] = f"CURSED: {curse['name']} — {curse['description']} See the curse slot in your pouch."
                    self._say(room, "system", "The Gauntlet", f"A hidden curse latched onto {player['name']}! It will fade after five combat or puzzle stages.")
                else:
                    outcome = self._roll_chest_outcome()
                    if outcome == "runes":
                        bonus = random.randint(15, 30)
                        room["runes"] += bonus
                        room["chest"]["decisions"][player_id] = "runes"
                        room.setdefault("privateNotices", {})[player_id] = f"Rune cache: {bonus} extra shared Runes."
                        self._say(room, "system", "The Gauntlet", f"{player['name']} found a cache of {bonus} Runes.")
                    elif outcome == "heal":
                        healed = min(player["maxHp"]-player["hp"], max(1, round(player["maxHp"]*.5)))
                        player["hp"] += healed
                        room["chest"]["decisions"][player_id] = "heal"
                        room.setdefault("privateNotices", {})[player_id] = f"Restoration chest: recovered {healed} HP."
                        self._add_effect(room, "heal", player["x"], player["y"], "#85d9db", duration=.8)
                        self._say(room, "system", "The Gauntlet", f"{player['name']} opened a restoration chest and recovered {healed} HP.")
                    else:
                        item = self._make_item(self._roll_chest_item_key())
                        if len(player["inventory"]) < POUCH_CAPACITY:
                            player["inventory"].append(item)
                            room["chest"]["decisions"][player_id] = "opened"
                            room.setdefault("privateNotices", {})[player_id] = f"Chest loot: {item['rarity']} {item['name']} — added to your pouch."
                            self._say(room, "system", "The Gauntlet", f"{player['name']} found {item['rarity']} loot: {item['name']}.")
                        else:
                            player["chestReward"] = item
                            room.setdefault("privateNotices", {})[player_id] = f"Chest loot: {item['rarity']} {item['name']}. Swap a pouch item to claim it."
                            self._say(room, "system", "The Gauntlet", f"{player['name']} found {item['rarity']} loot, but their pouch is full. They must swap an item to claim it.")
                self._finish_chest_if_ready(room)
            elif action == "chestClaim":
                if room["phase"] != "chest" or not room["chest"] or not player["chestReward"]:
                    raise ValueError("You do not have a pending chest item to claim.")
                replace_id = str(payload.get("replace", ""))
                old_item = next((item for item in player["inventory"] if item["id"] == replace_id), None)
                if not old_item:
                    raise ValueError("Choose one pouch item to swap out.")
                player["inventory"].remove(old_item)
                room["runes"] += old_item["sell"]
                player["inventory"].append(player["chestReward"])
                item_name = player["chestReward"]["name"]
                player["chestReward"] = None
                room.setdefault("privateNotices", {})[player_id] = f"Chest loot claimed: {item_name}. {old_item['name']} sold for {old_item['sell']} Runes."
                room["chest"]["decisions"][player_id] = "opened"
                self._say(room, "system", "The Gauntlet", f"{player['name']} swapped {old_item['name']} for {item_name}; the old item sold for {old_item['sell']} Runes.")
                self._finish_chest_if_ready(room)
            elif action == "start":
                if player_id != room["host"]:
                    raise ValueError("Only the room host can start the run.")
                if room["phase"] != "lobby":
                    raise ValueError("The run has already started.")
                if not player["class"]:
                    raise ValueError("Choose a class before starting.")
                if any(not p["class"] for p in room["players"].values() if not p.get("bot")):
                    raise ValueError("Every player must choose a class first.")
                if any(len(p["abilities"]) != 3 or
                       {next(ability[7] for ability in ABILITY_SETS[p["class"]] if ability[0] == selected)
                        for selected in p["abilities"]} != {"light", "special", "ultimate"}
                       for p in room["players"].values() if not p.get("bot")):
                    raise ValueError("Every player must select one Light, one Special, and one Ultimate ability.")
                self._choose_companion_hero(room)
                room["stage"] = 1
                room["wave"] = 1
                room["bossesDefeated"] = 0
                room["miniBossesSinceBoss"] = 0
                room["miniBossesRequired"] = random.randint(2, 4)
                room["regularWavesSinceMiniBoss"] = 0
                room["regularWavesRequired"] = random.randint(3, 5)
                room["bossSequence"] = random.sample(LARGE_BOSSES, 2) + [random.choice(DRAGON_TYPES)]
                total = room.get("totalStages", 25)
                room["bossStages"] = [round(total*.32), round(total*.64), total]
                if total == 9:
                    room.update(miniBossStages=[2], puzzlesRequired=1, puzzleStages=[5], townsTarget=1)
                else:
                    room["miniBossStages"] = self._build_mini_boss_schedule(room["bossStages"])
                    room["puzzlesRequired"], room["puzzleStages"] = self._build_puzzle_schedule(room["bossStages"])
                    room["townsTarget"] = random.choices((2, 3, 4), weights=(15, 70, 15), k=1)[0]
                room["townsVisited"] = 0
                room['townPressureStages']=[]
                room["townStages"] = [4] if total == 9 else self._build_town_schedule(room["townsTarget"], room["puzzleStages"], room["miniBossStages"] + room["bossStages"], total)
                event_candidates = [stage for stage in range(2, total) if stage not in
                                    room["townStages"] + room["puzzleStages"] + room["miniBossStages"] + room["bossStages"]]
                room["assassinationStage"] = random.choice(event_candidates) if total != 9 and event_candidates and random.random() < 0.08 else None
                room["assassinationUsed"] = False
                if total == 9:
                    room['objectiveStages']={'8':random.choice(('rift','ward','charge'))}
                else:
                    combat_encounters.plan(room)
                room["puzzlesCompleted"] = 0
                room["stageWave"] = 1
                room["stageWaves"] = self._stage_wave_count(len(self._active_players(room)), self._effective_stage(room))
                room["waveStartsAt"] = 0
                room["encounterType"] = "normal"
                room["encounterName"] = ""
                room["phase"] = "combat"
                room["routeEffect"] = random.choice(("wave_size", "enemy_health"))
                self._reset_cooldowns(room)
                self._spawn_wave(room)
                self._say(room, "system", "The Gauntlet", "The run begins!")
            else:
                raise ValueError("Unknown action.")

    def _say(self, room: dict, player_id: str, name: str, message: str) -> None:
        room["messageId"] += 1
        room["chat"].append({
            "id": room["messageId"], "player": player_id, "name": name,
            "message": message, "at": time.time(),
        })
        room["chat"] = room["chat"][-80:]

    def _present_routes(self, room: dict) -> None:
        room["chest"] = None
        room["nextTown"] = random.choice(TOWNS) if room["stage"] + 1 in room.get("townStages", []) else None
        # Store one coin flip for this transition; polling cannot reroll the road.
        room["forkPending"] = not room["nextTown"] and random.random() < 0.5
        paths = [("Moss Road", "combat", "woodland"), ("High Arch", "combat", "ruins"),
                 ("Ashen Pass", "combat", "cavern"), ("Moonwell Way", "combat", "ruins"),
                 ("Frost Veil", "combat", "frost"), ("Glacier Stair", "combat", "frost")]
        chosen = random.sample(paths, 2)
        dangers = random.sample(range(1, 6), len(chosen))
        room["routes"] = [
            {"id": secrets.token_hex(3), "destination": name, "kind": kind, "region": region,
             "danger": dangers[index], "votes": {}, "x": ROUTE_GATES[index][0], "y": ROUTE_GATES[index][1],
             "name": name}
            for index, (name, kind, region) in enumerate(chosen)
        ]
        room["routeVotes"] = {}
        room["revealedRoute"] = None
        room["phase"] = "stage_exit"
        room["projectiles"] = []
        destination = "the next town" if room["nextTown"] else "the fork" if room["forkPending"] else "the next area"
        self._say(room, "system", "The Gauntlet", f"Stage cleared. Gather at the opening on the top edge to reach {destination}.")

    @staticmethod
    def _at_stage_exit(player: dict) -> bool:
        return player["status"] == "alive" and abs(player["x"] - WIDTH / 2) <= 96 and player["y"] <= 48

    def _enter_fork(self, room: dict) -> None:
        room["phase"] = "routes"
        for index, player in enumerate(room["players"].values()):
            player["x"], player["y"] = 480 + (index - (len(room["players"]) - 1) / 2) * 24, HEIGHT - 44
            player["dx"], player["dy"] = 0, 0
            if player.get("bot"):
                player.update(aiRoute=None, aiPathIndex=0, aiMoveAt=0)
        self._say(room, "system", "The Gauntlet", "The road forks. Follow the left or right trail all the way to its edge. Everyone chooses by walking.")

    @staticmethod
    def _on_fork_path(x: float, y: float) -> bool:
        for path in FORK_PATHS:
            for (ax, ay), (bx, by) in zip(path, path[1:]):
                fraction = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) /
                                     ((bx - ax) ** 2 + (by - ay) ** 2)))
                if math.hypot(x - ax - fraction * (bx - ax), y - ay - fraction * (by - ay)) <= 54:
                    return True
        return False

    def _tick_travel(self, room: dict) -> None:
        active = self._voting_players(room)
        if room["phase"] == "stage_exit":
            if active and all(self._at_stage_exit(member) for member in active):
                story = room.get("story", {})
                if not story.get("encountered", True) and room["stage"] >= story["afterStage"]:
                    progression.enter_peace(self, room)
                    return
                if room.get("nextTown"):
                    self._advance_stage(room, {"kind": "town", "destination": room["nextTown"], "region": room.get("region", "woodland")})
                elif room.get("forkPending", True):
                    self._enter_fork(room)
                else:
                    self._advance_stage(room, room["routes"][0])
        elif room["phase"] == "routes":
            for player in active:
                route = self._near_route(room, player)
                if route and (player["x"] <= 52 or player["x"] >= WIDTH - 52):
                    room["routeVotes"][player["id"]] = route["id"]
                else:
                    room["routeVotes"].pop(player["id"], None)
            if self._routes_ready(room):
                self._resolve_routes(room)

    def _resolve_routes(self, room: dict) -> None:
        voters = self._voting_players(room)
        if not voters:
            return
        counts = {route["id"]: sum(room["routeVotes"].get(p["id"]) == route["id"] for p in voters) for route in room["routes"]}
        highest = max(counts.values())
        tied = [route for route in room["routes"] if counts[route["id"]] == highest]
        host_vote = room["routeVotes"].get(room["host"])
        selected = next((route for route in tied if route["id"] == host_vote), None) or random.choice(tied)
        easiest = min(route["danger"] for route in room["routes"])
        hardest = max(route["danger"] for route in room["routes"])
        if selected["danger"] == easiest and easiest != hardest:
            room["routePressure"] = min(6, room["routePressure"] + 1)
        elif selected["danger"] == hardest and easiest != hardest:
            room["routePressure"] = max(-6, room["routePressure"] - 1)
        self._advance_stage(room, selected)

    def _advance_stage(self, room: dict, selected: dict) -> None:
        room["stage"] += 1
        room["wave"] += 1
        room["stageWave"] = 1
        room["stageWaves"] = self._stage_wave_count(len(self._active_players(room)), self._effective_stage(room))
        room["waveStartsAt"] = 0
        self._reset_cooldowns(room)
        room["region"] = selected.get("region", room.get("region", "woodland"))
        room["routes"] = []
        room["routeVotes"] = {}
        room["nextTown"] = None
        room["forkPending"] = False
        if room["stage"] in room["puzzleStages"] and room["puzzlesCompleted"] < room["puzzlesRequired"]:
            room["puzzle"] = self._new_puzzle(room)
            for index, player in enumerate(room["players"].values()):
                player["x"], player["y"] = 480, 468
                player["dx"], player["dy"] = 0, 0
            room["phase"] = "puzzle"
            self._say(room, "system", "The Gauntlet", "Read your totem: in a party it describes a teammate's rune. Share clues, then stand on your answers together. Solo totems describe your own rune.")
        elif selected["kind"] == "town":
            self._enter_town(room, selected["destination"])
        else:
            room["phase"] = "combat"
            self._spawn_wave(room)

    @staticmethod
    def _advance_curses(room: dict) -> None:
        for player in room["players"].values():
            curse = player.get("curse")
            if not curse:
                continue
            curse["remainingStages"] -= 1
            if curse["remainingStages"] <= 0:
                player["curse"] = None
                # The cursed slot is private state; only the affected player learns that it faded.
                room.setdefault("privateNotices", {})[player["id"]] = "Your curse has finally faded."

    @staticmethod
    def _roll_chest_outcome():
        return random.choices(("item", "runes", "heal"), weights=(55, 25, 20), k=1)[0]

    @staticmethod
    def _roll_chest_item_key() -> str:
        rarity = random.choices(
            [entry[0] for entry in LOOT_RARITIES],
            weights=[entry[1] for entry in LOOT_RARITIES],
            k=1,
        )[0]
        candidates = [key for key, item in ITEMS.items() if item["rarity"] == rarity]
        return random.choice(candidates)

    def _finish_chest_if_ready(self, room: dict) -> None:
        if room["chest"] and self._active_players(room) and all(p["id"] in room["chest"]["decisions"] for p in self._active_players(room)):
            room["chest"] = None
            self._present_routes(room)

    @staticmethod
    def _make_item(item_key: str, price: int | None = None) -> dict:
        item = ITEMS[item_key]
        return {"id": secrets.token_hex(5), "key": item_key, "name": item["name"], "rarity": item["rarity"],
                "kind": item["kind"], "slot": item["slot"], "description": item["description"],
                "price": price if price is not None else item["price"], "sell": item["sell"],
                "damage": item.get("damage", 0), "armor": item.get("armor", 0), "color": item.get("color"),
                "effect": item.get("effect"), "effectLabel": item.get("effectLabel", ""),
                "heal": item.get("heal", 40 if item["kind"] == "heal" else 0),
                "mana": item.get("mana", 0),
                "factor": item.get("factor", 1), "duration": item.get("duration", 0),
                "cooldownRestore": item.get("cooldownRestore", 0), "attacks": item.get("attacks", 0)}

    def _stock_shop(self, room: dict, player: dict) -> None:
        class_consumable = {
            "Knight": "warding_tonic", "Wizard": "mana_draught", "Archer": "piercing_arrows",
            "Cleric": "phoenix_flask", "Rogue": "quickstep_elixir", "Druid": "ember_oil",
            "Bard": "quickstep_elixir", "Healer": "healing_draught",
        }.get(player["class"], "healing_draught")
        keys = list(dict.fromkeys(("healing_draught", class_consumable, CLASS_WEAPONS[player["class"]])))
        preferred_build = {'Druid': 'summoners_staff', 'Wizard': 'arcane_conductor',
                           'Healer': 'rescuers_cuirass', 'Rogue': 'pursuit_blade'}.get(player['class'])
        keys.append(preferred_build or random.choice(tuple(tactical.BUILD_ITEMS)))
        keys.append(random.choice([key for key in tactical.BUILD_ITEMS if key not in keys]))
        if random.random() < 0.18:
            keys.append("route_lens")
        if random.random() < 0.3:
            keys.append(random.choice(("phoenix_flask", "stormguard_charm", "dragonbone_armor", "aegis_of_dawn")))
        player["shopStock"] = [{"key": key, **self._make_item(key), "price": ITEMS[key]["price"]} for key in keys]

    @staticmethod
    def _ability_slots(player: dict) -> list[dict]:
        now = time.monotonic()
        abilities = {ability[0]: ability_record(ability) for ability in ABILITY_SETS.get(player["class"], [])}
        return [
            {**abilities[ability_id], "cooldownLeft": math.ceil(max(0, player["abilityCooldowns"].get(ability_id, 0) - now)),
             "summonAlive": ability_id in player.get("activeSummons", {})}
            for ability_id in player["abilities"] if ability_id in abilities
        ]

    @staticmethod
    def _town_npcs(room: dict, player: dict) -> dict:
        if room["phase"] == "peace":
            return {"wounded": {"x": 480, "y": 250}}
        if not player.get("townInterior"):
            return {"gate": {"x": TOWN_GATE[0], "y": TOWN_GATE[1]}}
        house = next((entry for entry in room.get("townLayout", []) if entry["id"] == player["townInterior"]), None)
        service = house.get("service") if house else None
        if service == "innkeeper":
            return progression.npcs(room, player)
        return {service: {"x": TOWN_SERVICE_POSITION[0], "y": TOWN_SERVICE_POSITION[1]}} if service else {}

    def _nearby_npc(self, room: dict, player: dict) -> dict | None:
        npc_names = {"wounded": "Wounded Hunter", "stairs_up": "Stairs upstairs", "stairs_down": "Stairs downstairs", "merchant": "Merchant", "alchemist": "Alchemist", "innkeeper": "Innkeeper", "guildmaster": "Guildmaster", "gate": "Trail Gate"}
        close = [(math.hypot(player["x"] - pos["x"], player["y"] - pos["y"]), key, pos["x"], pos["y"])
                 for key, pos in self._town_npcs(room, player).items()]
        if not close:
            return None
        distance, key, x, y = min(close)
        return {"id": key, "name": npc_names.get(key, "Occupied room" if key.startswith("locked_") else "Guest bed"), "x": x, "y": y} if distance <= 70 else None

    @staticmethod
    def _nearby_house(room: dict, player: dict) -> dict | None:
        if player.get("townInterior"):
            if player.get("innFloor", 1) == 2:
                return None
            return {"id": "exit_house", "name": "Town", "x": 480, "y": 450} if math.hypot(player["x"] - 480, player["y"] - 450) <= 62 else None
        for house in room.get("townLayout", []):
            door_x, door_y = house["x"], house["y"] + 47
            if math.hypot(player["x"] - door_x, player["y"] - door_y) <= 44:
                return {**house, "doorX": door_x, "doorY": door_y}
        return None

    def _at_merchant(self, room: dict, player: dict) -> bool:
        npc = self._nearby_npc(room, player)
        return bool(npc and npc["id"] == "merchant")

    def _validate_guild_class(self, room: dict, player: dict, chosen: str) -> None:
        npc = self._nearby_npc(room, player) if room["phase"] == "town" else None
        if not npc or npc["id"] != "guildmaster" or player.get("townInteraction") != "guildmaster":
            raise ValueError("Talk to the Guildmaster inside the Guild first.")
        if player["status"] != "alive" or not player["class"]:
            raise ValueError("You must be standing to change class.")
        if player.get("classChangeUsed"):
            raise ValueError("You have already changed class once this run.")
        if chosen not in CLASSES:
            raise ValueError("Unknown hero.")
        if chosen == player["class"]:
            raise ValueError("Your current hero is off limits.")
        if any(p["class"] == chosen for p in room["players"].values() if p["id"] != player["id"]):
            raise ValueError("That hero is already taken by a teammate.")

    @staticmethod
    def _town_walkable(room: dict, x: float, y: float) -> bool:
        return not any(abs(x - house["x"]) < 69 and house["y"] - 78 < y < house["y"] + 35
                       for house in room.get("townLayout", []))

    @staticmethod
    def _new_town_layout() -> list[dict]:
        return town_layout.generate(random.randrange(1, 1_000_000))["townLayout"]

    def _vote_town_exit(self, room: dict, player: dict) -> None:
        if player.get("bot"):
            return
        voters = self._voting_players(room)
        if progression.locked(room, player):
            raise ValueError("Listen to the village runner first.")
        if room.get("townsVisited") == 1 and any(not p.get("trainingKnown") for p in self._active_players(room) if not p.get("bot")):
            raise ValueError("Every present hunter must speak to the innkeeper and finish the training tutorial before leaving the first village.")
        if room["phase"] != "town" or player.get("townInterior"):
            raise ValueError("Step outside and gather at the town exit to vote.")
        gate_x, gate_y = TOWN_GATE
        if math.hypot(player["x"] - gate_x, player["y"] - gate_y) > 78:
            raise ValueError("Gather at the town gate before voting to leave.")
        player["townExitReady"] = not player.get("townExitReady", False)
        if player["townExitReady"]:
            ready_count = sum(1 for member in voters if member.get("townExitReady"))
            self._say(room, "system", "The Gauntlet", f"{player['name']} is ready to leave town ({ready_count}/{len(voters)}).")
        else:
            self._say(room, "system", "The Gauntlet", f"{player['name']} changed their vote to stay in town.")
        if voters and all(member.get("townExitReady") and not member.get("townInterior") and
               math.hypot(member["x"] - gate_x, member["y"] - gate_y) <= 78
               for member in voters):
            room["phase"] = "combat"
            room["waveStartsAt"] = 0
            room["stageWave"] = 1
            for member in room["players"].values():
                member["townInteraction"] = None
                member["guildPreview"] = None
                member["townExitReady"] = False
                member.update(townInterior=None, townReturn=None, innFloor=1, dialogue=None)
            self._reset_cooldowns(room)
            self._say(room, "system", "The Gauntlet", "Everyone is ready. The party leaves town together!")
            self._spawn_wave(room)

    @staticmethod
    def _near_route(room: dict, player: dict) -> dict | None:
        near = [(math.hypot(player["x"] - route["x"], player["y"] - route["y"]), route) for route in room["routes"]]
        if not near:
            return None
        distance, route = min(near, key=lambda item: item[0])
        return {"id": route["id"], "name": route["name"]} if distance <= 72 else None

    @staticmethod
    def _reset_cooldowns(room: dict) -> None:
        # New stages require fresh summons; wave spawning does not call this.
        now = time.monotonic()
        room["summons"] = []
        for player in room["players"].values():
            player["activeSummons"] = {}
            player.update(pursuitUntil=0, pursuitSpent=True, rescueGuardUntil=0, rescueGuardReadyAt=0)
            player["abilityCooldowns"] = {
                entry[0]: now + entry[6]
                for entry in ABILITY_SETS.get(player["class"], [])
                if entry[7] == "ultimate" and entry[0] in player["abilities"]
            }

    @staticmethod
    def _build_mini_boss_schedule(boss_stages=None) -> list[int]:
        stages = []
        boundaries = [1]+list(boss_stages or [8, 16, 25])
        for start, end in zip(boundaries, boundaries[1:]):
            count = random.randint(2, 4)
            for index in range(count):
                ideal = start + (index + 1) * (end - start) / (count + 1)
                candidates = [stage for stage in range(start + 1, end) if stage not in stages]
                pick = min(candidates, key=lambda stage: (abs(stage - ideal + random.uniform(-0.45, 0.45)), random.random()))
                stages.append(pick)
        return sorted(stages)

    @staticmethod
    def _build_puzzle_schedule(boss_stages=None) -> tuple[int, list[int]]:
        count = random.choices((1, 2, 3), weights=(65, 30, 5), k=1)[0]
        first, second, last = boss_stages or [8, 16, 25]
        pools = (tuple(range(max(2, first//2), first)), tuple(range(first+2, second)),
                 tuple(range(second+2, last)))
        return count, [random.choice(pool) for pool in pools[:count]]

    @staticmethod
    def _build_town_schedule(count: int, excluded: list[int], boss_stages: list[int], total=25) -> list[int]:
        bands = [(max(2, 1+round(i*(total-1)/4)), round((i+1)*(total-1)/4)) for i in range(4)]
        candidates = [[stage for stage in range(start, end + 1) if stage not in excluded and stage not in boss_stages]
                      for start, end in bands]
        selected = []
        for band in random.sample(candidates, min(count, len(candidates))):
            available = [stage for stage in band if stage not in selected]
            if available:
                selected.append(random.choice(available))
        fallback = [stage for stage in range(2, total) if stage not in excluded and stage not in boss_stages and stage not in selected]
        while len(selected) < count and fallback:
            pick = random.choice(fallback)
            selected.append(pick)
            fallback.remove(pick)
        return sorted(selected)

    def _interact(self, room: dict, player: dict) -> None:
        player_id = player["id"]
        if room["phase"] == "chest":
            self.action(room["code"], player_id, {"action": "openChest"})
            return
        if room["phase"] == "routes":
            route = self._near_route(room, player)
            if not route:
                raise ValueError("Walk up to one of the glowing paths first.")
            self.action(room["code"], player_id, {"action": "routeVote", "route": route["id"]})
            return
        if room["phase"] == "puzzle":
            puzzle_room = room["puzzle"]["rooms"][player_id]
            totem = puzzle_room["totem"]
            if math.hypot(player["x"] - totem["x"], player["y"] - totem["y"]) <= 58:
                puzzle_room["totemSeen"] = True
                return
            rune = next((entry for entry in puzzle_room["runes"]
                         if math.hypot(player["x"] - entry["x"], player["y"] - entry["y"]) <= 40), None)
            if rune and len(self._active_players(room)) > 1:
                return
            if rune and rune["rune"] != puzzle_room["target"] and time.monotonic() - puzzle_room["wrongAt"] >= 1.5:
                puzzle_room["wrongAt"] = time.monotonic()
                room["strainMistakes"] += 1
                self._say(room, "system", "The Gauntlet", f"{player['name']} tested the wrong rune. The run grows slightly more dangerous.")
                return
            raise ValueError("Find the totem for its clue, then stand on the matching rune.")
        if progression.locked(room, player):
            raise ValueError("Continue the dialogue first.")
        if room["phase"] == "peace":
            npc = self._nearby_npc(room, player)
            if not npc:
                raise ValueError("Walk up to the wounded hunter and speak to him.")
            if not player.get("questAccepted"):
                progression.start_dialogue(player, "wounded")
            else:
                room.setdefault("privateNotices", {})[player_id] = "Quest: Find and kill the dragon. Gather at the northern exit to continue."
            return
        if room["phase"] == "town":
            house = self._nearby_house(room, player)
            if player.get("townInterior") and house:
                player["townInterior"] = None
                player["x"], player["y"] = player.get("townReturn") or (house.get("x", 480), house.get("y", 220))
                player["townReturn"] = None
                player["townInteraction"] = None
                player["guildPreview"] = None
                player["dx"], player["dy"] = 0, 0
                room.setdefault("privateNotices", {})[player_id] = "You step back into the village."
                return
            if house and not player.get("townInterior"):
                player["townReturn"] = (player["x"], player["y"])
                player["townInterior"] = house["id"]
                player["innFloor"] = 1
                player["x"], player["y"] = 480, 405
                player["dx"], player["dy"] = 0, 0
                player["townExitReady"] = False
                player["townInteraction"] = None
                player["guildPreview"] = None
                room.setdefault("privateNotices", {})[player_id] = f"You entered {house['name']}. Press E at the door to return to town."
                return
            npc = self._nearby_npc(room, player)
            if not npc:
                raise ValueError("Walk to the door, the shopkeeper, or the town gate to interact.")
            npc_id = npc["id"]
            player["townInteraction"] = npc_id
            player["dx"], player["dy"] = 0, 0
            if npc_id == "alchemist":
                if len(player["inventory"]) < POUCH_CAPACITY:
                    gift = random.choice(("healing_draught", "mana_draught", "quickstep_elixir"))
                    player["inventory"].append(self._make_item(gift))
                    room.setdefault("privateNotices", {})[player_id] = f"The alchemist gives you a {ITEMS[gift]['name']}. Added to your pouch."
                else:
                    player["hp"] = min(player["maxHp"], player["hp"] + 40)
                    player["mana"] = min(player["maxMana"], player["mana"] + 40)
                    room.setdefault("privateNotices", {})[player_id] = "The alchemist restores 40 health and mana; your pouch was full."
            elif npc_id == "innkeeper":
                if not player.get("trainingKnown"):
                    progression.start_dialogue(player, "training")
            elif npc_id == "stairs_up":
                player.update(innFloor=2, x=710, y=435, townInteraction=None)
            elif npc_id == "stairs_down":
                player.update(innFloor=1, x=710, y=385, townInteraction=None)
            elif npc_id.startswith("locked_"):
                player["townInteraction"] = None
                room.setdefault("privateNotices", {})[player_id] = "This guest room is locked. Someone is resting inside."
            elif npc_id.startswith("bed_"):
                progression.checkpoint(self, room, player, npc_id)
                player["townInteraction"] = None
            elif npc_id == "gate":
                self._vote_town_exit(room, player)
            return
        raise ValueError("There is nothing nearby to interact with.")

    def _enter_town(self, room: dict, town_name: str | None = None) -> None:
        room["phase"] = "town"
        room["town"] = town_name or random.choice(TOWNS)
        room["townsVisited"] = room.get("townsVisited", 0) + 1
        room.setdefault('townPressureStages',[]).append(room['stage'])
        room.update(town_layout.generate(random.randrange(1, 1_000_000)))
        for index, party_member in enumerate(room["players"].values()):
            party_member["status"] = "alive"
            party_member["deathRecorded"] = False
            party_member["hp"] = party_member["maxHp"]
            party_member["mana"] = party_member["maxMana"]
            party_member["x"], party_member["y"] = 480 + (index - (len(room["players"]) - 1) / 2) * 42, 460
            party_member["dx"], party_member["dy"] = 0, 0
            party_member["attacking"] = False
            party_member["reviving"] = None
            party_member["wardUntil"] = 0
            party_member["wardFactor"] = 1.0
            party_member["townInteraction"] = None
            party_member["guildPreview"] = None
            party_member["townInterior"] = None
            party_member["townReturn"] = None
            party_member["townExitReady"] = False
            self._stock_shop(room, party_member)
        room["townInstance"] = secrets.token_hex(6)
        room["innRooms"] = progression.rooms()
        room["townWelcome"] = {"x": 480, "y": 345, "lastTick": time.monotonic(), "acknowledged": [], "done": False} if room["townsVisited"] == 1 else None
        for p in room["players"].values():
            p.update(innFloor=1, dialogue=None)
        self._say(room, "system", "The Gauntlet", f"The party reaches {room['town']}. Speak to the innkeeper and find a guest bed upstairs to set a checkpoint.")

    @staticmethod
    def _party_factor(room: dict, values: tuple[float, ...]) -> float:
        return values[max(0, min(3, len(GameWorld._active_players(room)) - 1))]

    @staticmethod
    def _stage_wave_count(player_count: int, stage: int = 1) -> int:
        if stage < 7:
            return 3 if random.random() < .10 else 2
        if player_count >= 3 or stage >= 17:
            return 3
        return 3 if stage >= 13 and random.random() < .75 else 2

    @staticmethod
    def _effective_stage(room: dict) -> int:
        stage = room['stage']
        return min(25, 1+3*(stage-1)) if room.get('totalStages') == 9 and stage > 0 else stage

    @staticmethod
    def _stage_ramp(room: dict) -> float:
        total = 25 if room.get('totalStages') == 9 else room.get("totalStages", 25)
        stage = max(1, min(total, GameWorld._effective_stage(room)))
        ramp = 0.62 + 0.38 * (stage - 1) / max(1, total-1)
        # Add gentle pressure from stage 8, then increase it each stage.
        if stage >= 8:
            ramp += 0.08 + 0.04 * (stage - 8)
        return ramp

    def _spawn_wave(self, room: dict, preserve_players: bool = False) -> None:
        room["hazards"] = []
        terrain.prepare(room)
        if not preserve_players:
            telemetry.start(room, time.monotonic(), ABILITY_SETS)
        if room["stage"] == room.get("assassinationStage") and room["stageWave"] == 1 and not room.get("assassinationUsed"):
            self._spawn_assassination(room)
        elif room["stage"] in room["bossStages"] and room["stageWave"] == room["stageWaves"]:
            self._spawn_large_boss(room)
        elif room["stage"] in room["miniBossStages"] and room["stageWave"] == room["stageWaves"]:
            self._spawn_mini_boss(room)
        else:
            self._spawn_regular_wave(room)
        self._tune_enemy_group(room)
        enemy_roles.assign(room)
        for enemy in room["enemies"]:
            if enemy["kind"] == "minotaur":
                enemy["speed"] *= 1.3
        if room.get("phase") == "combat":
            if preserve_players:
                self._place_enemies_at_random_edge(room)
            else:
                self._position_battle_formation(room)
            if room["encounterType"] == "assassination":
                self._place_assassins_at_edges(room)
        if not preserve_players:
            combat_encounters.prepare(self,room)
        for enemy in room['enemies']:
            if enemy.get('boss'): boss_ai.prepare(room, enemy)

    @staticmethod
    def _tune_enemy_group(room: dict) -> None:
        visits = GameWorld._town_pressure(room)
        elite = room["encounterType"] == "mini_boss"
        mode = DIFFICULTIES[room.get("difficulty", "medium")]["multiplier"]
        strength = 1.15 * mode * (1+.05*max(0, GameWorld._effective_stage(room)-1))
        for enemy in room["enemies"]:
            hp = strength * (1 + .25 * visits) * (1.15 if elite else 1)
            damage = strength * (1 + .20 * visits) * (1.12 if elite else 1)
            speed = (1 + .10 * visits) * (1.12 if elite else 1)
            enemy["hp"] = enemy["maxHp"] = math.ceil(enemy["maxHp"] * hp)
            enemy["damage"] = math.ceil(enemy["damage"] * damage)
            enemy["speed"] *= speed
            enemy["attackRate"] = math.sqrt(mode) * (1 + .12 * visits) * (1.25 if elite else 1)
            if enemy.get("boss") and enemy["kind"] in ("minotaur", "troll"):
                enemy["speed"] *= 2.5
            enemy["elite"] = elite

    def _spawn_assassination(self, room: dict) -> None:
        self._spawn_regular_wave(room, include_dracos=False)
        count = max(1, len(self._active_players(room)))
        originals = list(room["enemies"])
        room["enemies"] = []
        for index in range((6, 12, 18, 24)[max(0, min(3, count - 1))]):
            enemy = copy.deepcopy(originals[index % len(originals)])
            enemy["id"] = secrets.token_hex(4)
            enemy["name"] = "Assassin " + enemy["name"]
            enemy["hp"] = enemy["maxHp"] = math.ceil(enemy["maxHp"] * 1.4)
            enemy["damage"] = max(1, round(enemy["damage"] * 1.25))
            enemy["speed"] *= 1.12
            enemy["assassin"] = True
            enemy["class"] = random.choice(("Rogue", "Knight", "Archer", "Wizard"))
            room["enemies"].append(enemy)
        room["assassinationUsed"] = True
        room["encounterType"] = "assassination"
        room["encounterName"] = "Assassination attempt"
        self._add_effect(room, "ambush", WIDTH / 2, HEIGHT / 2, "#f58b8b", duration=3, text="ASSASSINATION ATTEMPT!")
        self._say(room, "system", "The Gauntlet", "Assassins surround the party! Survive the ambush.")

    @staticmethod
    def _place_assassins_at_edges(room: dict) -> None:
        edges = ("top", "right", "bottom", "left")
        for index, enemy in enumerate(room["enemies"]):
            edge = edges[index % 4]
            along = (index // 4 + 1) / (math.ceil(len(room["enemies"]) / 4) + 1)
            if edge in ("top", "bottom"):
                enemy["x"], enemy["y"] = 32 + along * (WIDTH - 64), 3 if edge == "top" else HEIGHT - 3
            else:
                enemy["x"], enemy["y"] = 3 if edge == "left" else WIDTH - 3, 32 + along * (HEIGHT - 64)
            enemy["entryEdge"] = edge
            enemy["lastAttack"] = time.monotonic() + 1.5

    @staticmethod
    def _place_enemies_at_random_edge(room: dict) -> None:
        edge = random.choice(("top", "right", "bottom", "left"))
        count = len(room["enemies"])
        for index, enemy in enumerate(room["enemies"]):
            along = (index + 1) / (count + 1)
            if edge == "top":
                enemy["x"], enemy["y"] = 32 + along * (WIDTH - 64), 3
            elif edge == "bottom":
                enemy["x"], enemy["y"] = 32 + along * (WIDTH - 64), HEIGHT - 3
            elif edge == "left":
                enemy["x"], enemy["y"] = 3, 32 + along * (HEIGHT - 64)
            else:
                enemy["x"], enemy["y"] = WIDTH - 3, 32 + along * (HEIGHT - 64)
            enemy["entryEdge"] = edge

    @staticmethod
    def _position_battle_formation(room: dict) -> None:
        players = list(room["players"].values())
        player_gap = min(92, 760 / max(1, len(players)))
        player_start = WIDTH / 2 - player_gap * (len(players) - 1) / 2
        for index, player in enumerate(players):
            player["x"], player["y"] = player_start + index * player_gap, HEIGHT - 92
            player["dx"], player["dy"] = 0, 0
            player["attacking"] = False
        for index, summon in enumerate(room.get("summons", [])):
            owner = room["players"].get(summon["ownerId"])
            if owner:
                summon["x"] = max(28, min(WIDTH - 28, owner["x"] + (32 if index % 2 else -32)))
                summon["y"] = owner["y"] - 30
                summon["lastTick"] = time.monotonic()
        enemies = room["enemies"]
        columns = min(len(enemies), 6)
        gap = min(136, 800 / max(1, columns))
        start_x = WIDTH / 2 - gap * (columns - 1) / 2
        for index, enemy in enumerate(enemies):
            row, column = divmod(index, columns)
            row_gap = 56 if enemy.get("boss") or enemy.get("miniBoss") else 48
            enemy["x"] = start_x + column * gap
            enemy["y"] = 82 + row * row_gap

    def _spawn_regular_wave(self, room: dict, *, include_dracos: bool = True) -> None:
        count = max(1, len(self._active_players(room)))
        amounts = {1: (1, 2), 2: (3, 5), 3: (5, 8), 4: (8, 12)}
        minimum, maximum = amounts[max(1, min(4, count))]
        stage = self._effective_stage(room)
        bonus = 4 if stage >= 20 else 2 if stage >= 17 else 1 if stage >= 13 else 0
        if count == 1 and stage >= 20:
            minimum = maximum = 5
        else:
            minimum += bonus*count
            maximum += bonus*count
        amount = random.randint(minimum, maximum)
        if room["routeEffect"] == "wave_size":
            amount = max(minimum, min(maximum, amount + room["routePressure"] * max(1, math.ceil(count / 2))))
        room["enemies"] = []
        strain = self._strain_percent(room["strainMistakes"])
        route_health = room["routePressure"] * 0.025 if room["routeEffect"] == "enemy_health" else 0
        hp_scale = self._party_factor(room, (0.68, 0.78, 0.9, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
        damage_scale = self._party_factor(room, (0.48, 0.68, 0.84, 1.0)) * (0.62 + 0.38 * self._stage_ramp(room))
        speed_scale = self._party_factor(room, (0.72, 0.82, 0.92, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
        dracos = 0
        for index in range(amount):
            name, kind, hp, damage, base_color = random.choice(ENEMIES)
            if include_dracos and stage >= 17 and dracos < min(3, count) and (random.random() < .25 or room.get('totalStages') == 9 and index == 0):
                name, kind, hp, damage, base_color = DRACO
                dracos += 1
            affinity = random.choice(list(AFFINITIES))
            enemy_class = random.choice(tuple(CLASSES))
            angle = (2 * math.pi * index) / max(1, amount)
            base_speed = random.randint(108, 126) if kind == "draco" else random.randint(48, 70)
            room["enemies"].append({
                "id": secrets.token_hex(4), "name": name, "kind": kind,
                "affinity": affinity, "color": AFFINITIES[affinity],
                "baseColor": base_color, "class": enemy_class, "x": 120 + random.random() * (WIDTH - 240),
                "y": 70 + random.random() * (HEIGHT - 140),
                "hp": max(1, math.ceil(hp * hp_scale * (1 + strain) * (1 + route_health))), "maxHp": max(1, math.ceil(hp * hp_scale * (1 + strain) * (1 + route_health))),
                "damage": max(1, round(damage * damage_scale * (1 + strain))), "speed": max(22, round(base_speed * speed_scale)),
                "lastAttack": 0, "stunUntil": 0, "bleedUntil": 0, "bleedDamage": 0, "lastBleedTick": 0,
            })
        room["encounterType"] = "normal"
        room["encounterName"] = ""
        room["regularWavesSinceMiniBoss"] += 1
        self._say(room, "system", "The Gauntlet", f"Wave {room['wave']}: {amount} enemies approach.")

    def _spawn_mini_boss(self, room: dict) -> None:
        count = max(1, len(self._active_players(room)))
        strain = self._strain_percent(room["strainMistakes"])
        route_health = room["routePressure"] * 0.025 if room["routeEffect"] == "enemy_health" else 0
        room["enemies"] = []
        room["encounterType"] = "mini_boss"
        room["regularWavesSinceMiniBoss"] = 0
        room["regularWavesRequired"] = random.randint(3, 5)
        if random.choice(("empowered", "squadron")) == "empowered":
            name, kind, hp, damage, base_color = random.choice(ENEMIES)
            affinity = random.choice(list(AFFINITIES))
            enemy_class = random.choice(tuple(CLASSES))
            hp_scale = self._party_factor(room, (0.68, 0.78, 0.9, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
            damage_scale = self._party_factor(room, (0.48, 0.68, 0.84, 1.0)) * (0.62 + 0.38 * self._stage_ramp(room))
            speed_scale = self._party_factor(room, (0.72, 0.82, 0.92, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
            scaled_hp = math.ceil(hp * (2.8 + 0.2 * room["miniBossesSinceBoss"]) * count * hp_scale * (1 + strain) * (1 + route_health))
            room["encounterName"] = f"Empowered {affinity} {name}"
            room["enemies"].append({
                "id": secrets.token_hex(4), "name": room["encounterName"], "kind": kind,
                "affinity": affinity, "color": AFFINITIES[affinity], "baseColor": base_color, "class": enemy_class,
                "x": random.randint(180, WIDTH - 180), "y": random.randint(100, HEIGHT - 100),
                "hp": scaled_hp, "maxHp": scaled_hp,
                "damage": max(1, round(damage * 1.2 * damage_scale * (1 + strain))), "speed": max(24, round(random.randint(56, 76) * speed_scale)),
                "lastAttack": 0, "stunUntil": 0, "bleedUntil": 0, "bleedDamage": 0, "lastBleedTick": 0,
                "miniBoss": True,
            })
            self._say(room, "system", "The Gauntlet", f"Mini-boss: {room['encounterName']} enters the gauntlet!")
        else:
            amount = math.ceil(2.5 * count)
            room["encounterName"] = "Mini-boss Squadron"
            hp_scale = self._party_factor(room, (0.68, 0.78, 0.9, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
            damage_scale = self._party_factor(room, (0.48, 0.68, 0.84, 1.0)) * (0.62 + 0.38 * self._stage_ramp(room))
            speed_scale = self._party_factor(room, (0.72, 0.82, 0.92, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room))
            for index in range(amount):
                name, kind, hp, damage, base_color = random.choice(ENEMIES)
                affinity = random.choice(list(AFFINITIES))
                enemy_class = random.choice(tuple(CLASSES))
                scaled_hp = max(1, math.ceil(hp * hp_scale * (1 + strain) * (1 + route_health)))
                room["enemies"].append({
                    "id": secrets.token_hex(4), "name": name, "kind": kind,
                    "affinity": affinity, "color": AFFINITIES[affinity], "baseColor": base_color, "class": enemy_class,
                    "x": 120 + random.random() * (WIDTH - 240), "y": 70 + random.random() * (HEIGHT - 140),
                    "hp": scaled_hp, "maxHp": scaled_hp,
                    "damage": max(1, round(damage * damage_scale * (1 + strain))), "speed": max(22, round(random.randint(48, 70) * speed_scale)),
                    "lastAttack": 0, "stunUntil": 0, "bleedUntil": 0, "bleedDamage": 0, "lastBleedTick": 0,
                    "miniBoss": False,
                })
            self._say(room, "system", "The Gauntlet", f"Mini-boss round: a squadron of {amount} enemies advances!")

    def _spawn_large_boss(self, room: dict) -> None:
        boss_index = room["bossesDefeated"]
        boss = room["bossSequence"][boss_index]
        count = max(1, len(self._active_players(room)))
        strain = self._strain_percent(room["strainMistakes"])
        route_health = room["routePressure"] * 0.025 if room["routeEffect"] == "enemy_health" else 0
        hp_scale = count * self._party_factor(room, (0.68, 0.78, 0.9, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room)) * (1 + 0.14 * boss_index) * (1 + strain) * (1 + route_health)
        damage_scale = self._party_factor(room, (0.48, 0.68, 0.84, 1.0)) * (0.62 + 0.38 * self._stage_ramp(room)) * (1 + 0.1 * boss_index) * (1 + strain)
        hp = max(1, math.ceil(boss["hp"] * hp_scale))
        room["enemies"] = [{
            "id": secrets.token_hex(4), "name": boss["name"], "kind": "dragon" if boss_index == 2 else boss["kind"], "class": random.choice(tuple(CLASSES)),
            "affinity": boss["affinity"], "color": AFFINITIES[boss["affinity"]], "baseColor": AFFINITIES[boss["affinity"]],
            "x": WIDTH / 2, "y": HEIGHT / 2,
            "hp": hp, "maxHp": hp, "damage": max(1, round(boss["damage"] * damage_scale)),
            "speed": max(18, round((30 + boss_index * 2) * self._party_factor(room, (0.72, 0.82, 0.92, 1.0)) * (0.76 + 0.24 * self._stage_ramp(room)))), "lastAttack": 0, "stunUntil": 0,
            "bleedUntil": 0, "bleedDamage": 0, "lastBleedTick": 0, "boss": True, "bossPhase": 1,
            "nextBossAttack": time.monotonic()+1.5,
        }]
        room["encounterType"] = "large_boss"
        room["encounterName"] = boss["name"]
        self._say(room, "system", "The Gauntlet", f"LARGE BOSS {boss_index + 1} / 3: {boss['name']} blocks the way!")

    @staticmethod
    def _strain_percent(mistakes: int) -> float:
        early = min(mistakes, 2) * 0.005
        middle = min(max(mistakes - 2, 0), 2) * 0.01
        late = max(mistakes - 4, 0) * 0.02
        return min(0.15, early + middle + late)

    def _damage_enemy(self, room: dict, player: dict, enemy: dict, damage: int, summon_id: str | None = None, *, boost_source=None, boost_factor=None) -> None:
        if enemy not in room["enemies"]:
            return
        now = time.monotonic()
        if enemy.get('vulnerableUntil', 0) > now:
            damage = round(damage*1.35)
        if boost_factor is None:
            boost_factor = player["damageBoost"] if player.get("damageBoostUntil",0)>time.monotonic() else 1
            boost_source = player.get("damageBoostSource")
        if boost_source and boost_factor > 1:
            extra = max(0, min(enemy["hp"], damage)-min(enemy["hp"], round(damage/boost_factor)))
            telemetry.add(room, boost_source, "boostDamageGiven", extra)
        telemetry.add(room, player["id"], "summonDamage" if summon_id else "heroDamage", min(enemy["hp"], max(1, damage)))
        enemy["hp"] -= max(1, damage)
        enemy["damageTaken"] = enemy.get("damageTaken", 0) + 1
        if (enemy.get('boss') and enemy['kind']=='dragon' and enemy.get('bossPhase', 1)==1 and
                not enemy.get('armorWarned') and enemy['hp'] <= enemy['maxHp']*.35):
            enemy['armorWarned'] = True
            self._say(room, 'system', 'The Gauntlet', 'The dragon armor is cracking. Its true form will awaken when the armor breaks!')
        if enemy["hp"] > 0:
            return
        if enemy.get("boss") and enemy["kind"] == "dragon" and enemy.get("bossPhase", 1) == 1:
            boss_ai.second_phase(self, room, enemy, time.monotonic())
            return
        room["enemies"].remove(enemy)
        room["hazards"] = [h for h in room.get("hazards", []) if h["ownerId"] != enemy["id"]]
        telemetry.count(room, player["id"], "kills")
        room["runes"] += random.randint(2, 5)
        self._say(room, "system", "The Gauntlet", f"{enemy['affinity']} {enemy['name']} defeated. Runes collected.")
        if not room["enemies"] and combat_encounters.can_complete(room,time.monotonic()):
            self._complete_encounter(room)

    @staticmethod
    def _add_effect(room: dict, effect_type: str, x: float, y: float, color: str,
                    target_x: float | None = None, target_y: float | None = None,
                    duration: float = 0.35, text: str = "", attack_class: str = "") -> None:
        effect = {"id": secrets.token_hex(4), "type": effect_type, "x": x, "y": y,
                  "targetX": target_x if target_x is not None else x,
                  "targetY": target_y if target_y is not None else y,
                  "color": color, "until": time.time() + duration, "text": text, "class": attack_class}
        room["effects"].append(effect)
        room["effects"] = room["effects"][-80:]

    def _launch_projectile(self, room: dict, *, side: str, owner_id: str, target_id: str,
                           x: float, y: float, damage: int, color: str, attack_class: str,
                           effect_kind: str = "damage", speed: float = 270, splash: int = 0, summon_id: str | None = None,
                           radius: float = 7, turn_rate: float | None = None, ability_id: str = "") -> None:
        target_pool = room["enemies"] + terrain.obstacles(room) if side == "hero" else self._combat_targets(room)
        aimed = next((item for item in target_pool if item["id"] == target_id), None)
        target_x = aimed["x"] if aimed else x + 1
        target_y = aimed["y"] if aimed else y
        if side == "enemy" and aimed:
            lead = min(0.32, math.hypot(target_x - x, target_y - y) / max(speed, 1) * 0.35)
            target_x += aimed.get("dx", 0) * CLASSES.get(aimed.get("class"), {}).get("speed", 140) * lead
            target_y += aimed.get("dy", 0) * CLASSES.get(aimed.get("class"), {}).get("speed", 140) * lead
        dx, dy = target_x - x, target_y - y
        distance = max(0.001, math.hypot(dx, dy))
        room["projectiles"].append({"id": secrets.token_hex(4), "side": side, "ownerId": owner_id,
            "targetId": target_id, "x": x, "y": y, "vx": dx / distance * speed, "vy": dy / distance * speed,
            "expiresAt": time.monotonic() + 4, "damage": max(1, damage), "color": color,
            "class": attack_class, "effectKind": effect_kind, "speed": speed, "splash": splash, "abilityId": ability_id,
            "lastTick": time.monotonic(), "summonId": summon_id, "radius": radius,
            "turnRate": (.65 if side == "enemy" else 0) if turn_rate is None else turn_rate,
            "trackUntil": time.monotonic()+1.1,
            "boostSource": room["players"].get(owner_id,{}).get("damageBoostSource") if side == "hero" else None,
            "boostFactor": room["players"].get(owner_id,{}).get("damageBoost",1) if side == "hero" and room["players"].get(owner_id,{}).get("damageBoostUntil",0)>time.monotonic() else 1})
        if side == 'hero' and owner_id in room['players']:
            tactical.decorate_projectile(room['players'][owner_id], room['projectiles'][-1])

    def _damage_player(self, room: dict, enemy: dict, target: dict, amount: int) -> None:
        if target.get('objectiveWard'):
            combat_encounters.hurt_ward(self,room,target,amount)
            return
        if target.get("summon"):
            self._damage_summon(room, target, amount)
            return
        if target["status"] != "alive":
            return
        now = time.monotonic()
        armor = sum(item.get("armor", 0) for item in target["toolSlots"] if item)
        curse = 1.25 if (target.get("curse") or {}).get("effect") == "frail" else 1
        warded = max(1, round(max(1, amount-armor)*curse*(target['wardFactor'] if target['wardUntil']>now else 1)))
        damage = max(1, round(warded*tactical.rescue_factor(room, target, now)))
        telemetry.add(room, target['id'], 'protectionGiven', max(0, min(target['hp'],warded)-min(target['hp'],damage)))
        telemetry.add(room, target["id"], "heroDamageTaken", min(target["hp"], damage))
        telemetry.add(room, target["id"], "damagePrevented", max(0, amount - damage))
        if target["wardUntil"] > now:
            unwarded = max(1, round(max(1, amount-armor)*curse))
            saved = max(0, min(target["hp"], unwarded)-min(target["hp"],warded))
            telemetry.add(room, target.get("wardSource",target["id"]), "protectionGiven", saved)
        target["hp"] -= damage
        target["damageTaken"] = target.get("damageTaken", 0) + 1
        if target["hp"] <= 0:
            target["hp"] = 0
            target["status"] = "downed"
            target["downedUntil"] = 0
            target["dx"], target["dy"] = 0, 0
            self._say(room, "system", "The Gauntlet", f"{target['name']} is down! Enemies turn toward the standing hunters.")

    def _summon_companion(self, room: dict, player: dict, ability_id: str, damage: int, now: float) -> None:
        template = SUMMON_TYPES[ability_id]
        summon_hp = tactical.summon_health(player, template)
        summon_id = secrets.token_hex(6)
        offset = -32 if len(player.get("activeSummons", {})) == 0 else 32
        summon = {**template, "id": summon_id, "ownerId": player["id"], "abilityId": ability_id,
                  "summon": True, "status": "alive", "hp": summon_hp, "maxHp": summon_hp,
                  "color": AFFINITIES[template["affinity"]], "damage": max(1, damage), "damageTaken": 0,
                  "x": max(28, min(WIDTH - 28, player["x"] + offset)),
                  "y": max(30, min(HEIGHT - 30, player["y"] - 28)),
                  "facingX": player.get("facingX", 1), "facingY": player.get("facingY", 0),
                  "moving": False, "animationUntil": 0, "lastTick": now, "lastAttack": now}
        telemetry.tick(room, now)
        room.setdefault("summons", []).append(summon)
        telemetry.summon_spawn(room, summon, now)
        player.setdefault("activeSummons", {})[ability_id] = summon_id
        player["abilityCooldowns"].pop(ability_id, None)
        self._add_effect(room, "aura", summon["x"], summon["y"], summon["color"], duration=0.6)

    def _remove_summon(self, room: dict, summon: dict, now: float | None = None) -> None:
        if summon not in room.get("summons", []):
            return
        now = time.monotonic() if now is None else now
        telemetry.tick(room, now)
        telemetry.summon_end(room, summon, now, summon["hp"] == 0)
        room["summons"].remove(summon)
        summon["status"] = "fallen"
        owner = room["players"].get(summon["ownerId"])
        if owner:
            owner.setdefault("activeSummons", {}).pop(summon["abilityId"], None)
            owner["abilityCooldowns"][summon["abilityId"]] = now + summon["recharge"]
        self._add_effect(room, "impact", summon["x"], summon["y"], summon["color"], duration=0.4)

    def _dismiss_summons(self, room: dict, owner_id: str | None = None) -> None:
        for summon in list(room.get("summons", [])):
            if owner_id is None or summon["ownerId"] == owner_id:
                self._remove_summon(room, summon)

    def _damage_summon(self, room: dict, summon: dict, amount: int) -> None:
        if summon not in room.get("summons", []):
            return
        telemetry.add(room, summon["ownerId"], "summonDamageTaken", min(summon["hp"], max(1, round(amount))))
        summon["hp"] = max(0, summon["hp"] - max(1, round(amount)))
        summon.pop('gearHealthFraction', None)
        summon["damageTaken"] += 1
        if summon["hp"] == 0:
            self._remove_summon(room, summon)

    def _tick_summons(self, room: dict, now: float) -> None:
        if room["phase"] != "combat" or room.get("waveStartsAt"):
            return
        for summon in list(room.get("summons", [])):
            if room["phase"] != "combat" or room.get("waveStartsAt"):
                break
            owner = room["players"].get(summon["ownerId"])
            if not owner or not owner.get("connected", True):
                self._remove_summon(room, summon, now)
                continue
            dt = min(0.1, max(0, now - summon["lastTick"]))
            tactical.refresh_summon_health(owner, summon, SUMMON_TYPES[summon['abilityId']])
            summon["lastTick"] = now
            target = min(room["enemies"], key=lambda e: math.hypot(e["x"] - summon["x"], e["y"] - summon["y"]), default=None)
            destination = target or owner
            dx, dy = destination["x"] - summon["x"], destination["y"] - summon["y"]
            distance = math.hypot(dx, dy)
            stop_range = summon["range"] if target and terrain.line_clear(room, summon, target) else 20 if target else 55
            summon["moving"] = distance > stop_range
            if distance > 0.001:
                summon["facingX"], summon["facingY"] = dx / distance, dy / distance
            if summon["moving"]:
                step = min(summon["speed"] * dt, distance - stop_range)
                terrain.move(room, summon, summon["x"] + dx / distance * step, summon["y"] + dy / distance * step, avoid=True)
            distance = math.hypot(destination["x"] - summon["x"], destination["y"] - summon["y"])
            if not target or not terrain.line_clear(room, summon, target) or distance > summon["range"] + 0.01 or now - summon["lastAttack"] < summon["attackInterval"]:
                continue
            summon["lastAttack"] = now
            if "lightPower" in summon:
                base = CLASSES[owner["class"]]["damage"]*(1+.03*owner.get("skillRanks",{}).get("power",0)) + sum(i.get("damage",0) for i in owner["toolSlots"] if i)
                boost = owner["damageBoost"] if owner["damageBoostUntil"] > now else 1
                curse = .75 if (owner.get("curse") or {}).get("effect") == "weakened" else 1
                light_damage = max(1,round(round(base*boost*curse)*summon["lightPower"]))
                summon["damage"] = max(1,round(light_damage*summon["damageScale"]))
            summon["animationUntil"] = time.time() + 0.3
            if summon["kind"] == "bird":
                self._launch_projectile(room, side="hero", owner_id=owner["id"], target_id=target["id"],
                    x=summon["x"], y=summon["y"] - 8, damage=summon["damage"], color=summon["color"],
                    attack_class="Druid", effect_kind="lightning", speed=360, summon_id=summon["id"])
                self._add_effect(room, "cast", summon["x"], summon["y"], summon["color"], target["x"], target["y"], 0.25)
            else:
                self._add_effect(room, "slash", summon["x"], summon["y"], summon["color"], target["x"], target["y"], 0.25)
                self._damage_enemy(room, owner, target, summon["damage"], summon["id"],
                    boost_factor=(owner["damageBoost"] if owner["damageBoostUntil"]>now else 1) if "lightPower" in summon else 1,
                    boost_source=owner.get("damageBoostSource"))

    def _tick_projectiles(self, room: dict, now: float) -> None:
        if room["phase"] != "combat":
            room["projectiles"] = []
            return
        remaining = []
        for projectile in room["projectiles"]:
            dt = min(0.12, max(0, now - projectile["lastTick"]))
            projectile["lastTick"] = now
            if now >= projectile["expiresAt"]:
                continue
            if projectile["side"] == "enemy" and now < projectile.get("trackUntil", 0):
                aimed = next((p for p in self._combat_targets(room)
                              if p["id"] == projectile["targetId"] and p["status"] == "alive"), None)
                if aimed:
                    angle = math.atan2(projectile["vy"], projectile["vx"])
                    desired = math.atan2(aimed["y"]-projectile["y"], aimed["x"]-projectile["x"])
                    delta = (desired-angle+math.pi) % (2*math.pi)-math.pi
                    limit = projectile.get("turnRate", .65)*dt
                    angle += max(-limit, min(limit, delta))
                    projectile["vx"], projectile["vy"] = math.cos(angle)*projectile["speed"], math.sin(angle)*projectile["speed"]
            start_x, start_y = projectile["x"], projectile["y"]
            projectile["x"] += projectile["vx"] * dt
            projectile["y"] += projectile["vy"] * dt
            segment_x, segment_y = projectile["x"] - start_x, projectile["y"] - start_y
            segment_length = max(0.001, segment_x * segment_x + segment_y * segment_y)

            def segment_distance(item: dict) -> float:
                fraction = max(0.0, min(1.0, ((item["x"] - start_x) * segment_x + (item["y"] - start_y) * segment_y) / segment_length))
                closest_x, closest_y = start_x + segment_x * fraction, start_y + segment_y * fraction
                return math.hypot(item["x"] - closest_x, item["y"] - closest_y)

            if projectile["side"] == "hero":
                targets = [enemy for enemy in room["enemies"] if segment_distance(enemy) <= projectile.get("radius", 7)+12]
            else:
                targets = [player for player in self._combat_targets(room) if player["status"] == "alive"
                           and segment_distance(player) <= projectile.get("radius", 7)+12]
            hits = [(t, target) for target in targets if (t := terrain.circle_hit(start_x, start_y,
                projectile["x"], projectile["y"], target["x"], target["y"], projectile.get("radius", 7)+12)) is not None]
            first = min(hits, key=lambda pair: pair[0], default=None)
            block = terrain.shot_block(room, start_x, start_y, projectile["x"], projectile["y"], projectile.get("radius", 7))
            if block and (not first or block[0] <= first[0]):
                terrain.damage_cover(self, room, block[1], projectile["damage"])
                continue
            target = first[1] if first else None
            if target is None:
                if (now < projectile["expiresAt"] and -24 <= projectile["x"] <= WIDTH + 24
                        and -24 <= projectile["y"] <= HEIGHT + 24):
                    remaining.append(projectile)
                continue
            self._add_effect(room, "impact", target["x"], target["y"], projectile["color"], duration=0.3, attack_class=projectile["class"])
            if projectile["side"] == "hero":
                owner = room["players"].get(projectile["ownerId"], room["players"][room["host"]])
                targets = [target]
                if projectile["splash"]:
                    targets += [other for other in room["enemies"] if other is not target and
                                math.hypot(other["x"] - target["x"], other["y"] - target["y"]) <= projectile["splash"]
                                and terrain.line_clear(room, target, other)]
                for struck in targets:
                    if projectile["effectKind"] == "stun":
                        self._stun(struck, now)
                        boss_ai.interrupt(self, room, struck, now)
                    if projectile.get('rootDuration'):
                        tactical.root(struck, now, projectile['rootDuration'])
                    if projectile["effectKind"] == "bleed":
                        struck["bleedUntil"] = time.monotonic() + 5
                        struck["bleedDamage"] = max(1, round(projectile["damage"] * 0.35))
                        struck["lastBleedTick"] = time.monotonic()
                        struck["bleedOwner"] = owner["id"]
                        struck["bleedBoostSource"] = projectile.get("boostSource")
                        struck["bleedBoostFactor"] = projectile.get("boostFactor",1)
                    self._damage_enemy(room, owner, struck, projectile["damage"], projectile.get("summonId"), boost_source=projectile.get("boostSource"), boost_factor=projectile.get("boostFactor",1))
                self._chain_projectile(room, owner, projectile, target, targets)
            else:
                struck = [target]
                if projectile["splash"]:
                    struck += [p for p in self._combat_targets(room) if p is not target
                               and p["status"] == "alive"
                               and math.hypot(p["x"]-target["x"], p["y"]-target["y"]) <= projectile["splash"]]
                for ally in struck:
                    self._damage_player(room, projectile, ally, projectile["damage"])
                if self._check_party_wipe(room):
                    break
        room["projectiles"] = [p for p in remaining if now < p["expiresAt"]] if room["phase"] == "combat" else []

    def _chain_projectile(self, room, owner, shot, anchor, struck):
        visited = {enemy['id'] for enemy in struck}
        damage = shot['damage']
        native = shot.get('chainTargets', 0)
        for index in range(native + bool(shot.get('conductorJump'))):
            if room['phase'] != 'combat': break
            choices = [enemy for enemy in room['enemies'] if enemy['id'] not in visited and
                       math.hypot(enemy['x']-anchor['x'], enemy['y']-anchor['y']) <= shot.get('chainRange', 110)
                       and terrain.line_clear(room, anchor, enemy)]
            target = min(choices, key=lambda enemy: math.hypot(enemy['x']-anchor['x'], enemy['y']-anchor['y']), default=None)
            if not target: break
            visited.add(target['id'])
            damage = max(1, round(damage*(shot.get('chainDecay', .65) if index < native else .5)))
            self._add_effect(room, 'cast', anchor['x'], anchor['y'], shot['color'], target['x'], target['y'], .3, attack_class='Wizard')
            self._damage_enemy(room, owner, target, damage, boost_source=shot.get('boostSource'), boost_factor=shot.get('boostFactor', 1))
            anchor = target

    def _tick_enemy(self, room, enemy, target, now):
        if enemy.get('structure'): return
        if enemy.get("targetId") != target["id"]:
            enemy.update(targetId=target["id"], moveDecisionAt=0, bossMoveAt=0)
            pending = enemy.get("pendingAttack")
            pending_target = next((p for p in self._combat_targets(room) if p["id"] == (pending or {}).get("targetId") and p["status"] == "alive"), None)
            if pending and not pending_target:
                enemy.pop("pendingAttack", None)
                room["hazards"] = [h for h in room.get("hazards", []) if h["ownerId"] != enemy["id"] or h["activatesAt"] <= now]
                enemy["nextBossAttack"] = now+.4
            pending_role = enemy.get("roleAttack")
            if pending_role and not any(p["id"] == pending_role["targetId"] and p["status"] == "alive" for p in self._combat_targets(room)):
                enemy.pop("roleAttack", None)
                enemy["roleReadyAt"] = now+.4
        dt = min(.1, max(0, now-enemy.get("lastAiTick", now-.05)))
        enemy["lastAiTick"] = now
        if enemy.get("boss") or enemy.get("miniBoss"):
            boss_ai.tick(self, room, enemy, target, now, dt)
            if enemy.get('rootUntil',0)>now: enemy['moving']=False
            return
        enemy_roles.tick(self, room, enemy, target, now, dt)
        if enemy.get('rootUntil',0)>now: enemy['moving']=False

    def _enemy_class_attack(self, room: dict, enemy: dict, target: dict, now: float) -> None:
        role = enemy.get("class", "Knight")
        ranged = role in ("Wizard", "Archer", "Cleric", "Druid", "Bard", "Healer")
        enemy["lastAttack"] = now
        enemy["animationUntil"] = time.time() + 0.45
        self._add_effect(room, "enemy_attack", enemy["x"], enemy["y"], enemy["color"],
                         target["x"], target["y"], 0.35, attack_class=role)
        if role == "Bard":
            for ally in room["enemies"]:
                if math.hypot(ally["x"] - enemy["x"], ally["y"] - enemy["y"]) <= 240:
                    ally["damageBoost"] = 1.25
                    ally["damageBoostUntil"] = now + 5
            self._add_effect(room, "aura", enemy["x"], enemy["y"], "#f095bf", duration=1, attack_class=role)
        elif role == "Healer":
            wounded = [ally for ally in room["enemies"] if ally["hp"] < ally["maxHp"] and
                       math.hypot(ally["x"] - enemy["x"], ally["y"] - enemy["y"]) <= 220]
            if wounded:
                ally = min(wounded, key=lambda item: item["hp"] / item["maxHp"])
                ally["hp"] = min(ally["maxHp"], ally["hp"] + max(8, enemy["damage"] * 2))
                self._add_effect(room, "heal", enemy["x"], enemy["y"], "#85d9db", ally["x"], ally["y"], 0.6, attack_class=role)
            else:
                speed_scale = self._party_factor(room, (0.68, 0.8, 0.92, 1.0)) * (0.75 + 0.25 * self._stage_ramp(room))
                self._launch_projectile(room, side="enemy", owner_id=enemy["id"], target_id=target["id"],
                    x=enemy["x"], y=enemy["y"], damage=enemy["damage"], color="#85d9db", attack_class=role, speed=200 * speed_scale)
        elif ranged:
            speed_scale = self._party_factor(room, (0.68, 0.8, 0.92, 1.0)) * (0.75 + 0.25 * self._stage_ramp(room))
            speed = {"Wizard": 240, "Archer": 340, "Cleric": 190, "Druid": 210, "Bard": 230}.get(role, 200) * speed_scale
            self._launch_projectile(room, side="enemy", owner_id=enemy["id"], target_id=target["id"],
                x=enemy["x"], y=enemy["y"], damage=enemy["damage"], color=enemy["color"], attack_class=role, speed=speed)
        else:
            damage = enemy["damage"] * (1.25 if role == "Rogue" else 1)
            self._damage_player(room, enemy, target, damage)
            if role == "Rogue" and target["status"] == "alive":
                self._add_effect(room, "bleed", target["x"], target["y"], "#cf6674", duration=0.8, attack_class=role)

    def _complete_encounter(self, room: dict) -> None:
        players = len(self._active_players(room))
        encounter_type = room["encounterType"]
        reward = 5 + 2 * players
        if encounter_type == "mini_boss":
            room["miniBossesSinceBoss"] += 1
            reward += 12 + 4 * players
            self._say(room, "system", "The Gauntlet", "Mini-boss defeated!")
        elif encounter_type == "large_boss":
            room["bossesDefeated"] += 1
            progression.boss_reward(room)
            reward += 40 + 12 * players
            if room["bossesDefeated"] == 3:
                self._finish_stage_stats(room, "cleared")
                room["runes"] += reward
                room["phase"] = "cleared"
                self._say(room, "system", "The Gauntlet", f"The final dragon falls! The party earns {reward} Runes and saves the realm!")
                return
            self._say(room, "system", "The Gauntlet", "The great foe falls. A new stretch lies ahead.")
            room["miniBossesSinceBoss"] = 0
        elif encounter_type == "assassination":
            reward += 25 + 8 * players
            self._say(room, "system", "The Gauntlet", "The assassination attempt is defeated!")
        room["runes"] += reward
        room["hazards"] = []
        if room["stageWave"] < room["stageWaves"]:
            room["stageWave"] += 1
            room["wave"] += 1
            room["phase"] = "combat"
            room["waveStartsAt"] = time.monotonic() + 3
            room["projectiles"] = []
            room["effects"] = []
            self._say(room, "system", "The Gauntlet", f"Wave {room['stageWave']} of {room['stageWaves']} arrives in three seconds!")
            return
        self._finish_stage_stats(room, "cleared")
        self._advance_curses(room)
        self._say(room, "system", "The Gauntlet", f"Stage {room['stage']} cleared. The party earns {reward} Runes.")
        for member in room["players"].values():
            if member["status"] != "alive":
                member["status"] = "alive"
                member["deathRecorded"] = False
                member["hp"] = max(1, round(member["maxHp"] * 0.3))
            member["reviving"] = None
            member["attacking"] = False
        self._offer_chest_or_routes(room)

    def _offer_chest_or_routes(self, room: dict) -> None:
        chance = {"normal": 0.38, "mini_boss": 0.78, "large_boss": 1.0, "assassination": 1.0}.get(room["encounterType"], 0.38)
        if random.random() >= chance:
            self._present_routes(room)
            return
        room["chest"] = {"decisions": {}, "runesAwarded": False, "x": WIDTH / 2, "y": HEIGHT / 2}
        for player in room["players"].values():
            player["chestReward"] = None
        room["phase"] = "chest"
        room["effects"].append({"id": secrets.token_hex(4), "type": "chest_spawn", "x": WIDTH / 2, "y": HEIGHT / 2,
                                "color": "#ffd166", "until": time.time() + 1.4})
        self._say(room, "system", "The Gauntlet", "A treasure chest appears in the arena. Walk up and press E to open it.")

    def _cast_ability(self, room: dict, player: dict, slot_index: int) -> None:
        now = time.monotonic()
        ability_id = player["abilities"][slot_index]
        ability = next((ability_record(entry) for entry in ABILITY_SETS[player["class"]] if entry[0] == ability_id), None)
        if not ability:
            raise ValueError("That ability is not available to this class.")
        if ability_id in player.get("activeSummons", {}):
            raise ValueError(f"{ability['name']} is still alive. Recharge begins when it dies.")
        ready_at = player["abilityCooldowns"].get(ability_id, 0)
        if ready_at > now:
            raise ValueError(f"{ability['name']} is ready in {math.ceil(ready_at - now)} seconds.")
        kind, reach, power = ability["kind"], ability["range"], ability["power"]
        nearby = [enemy for enemy in room["enemies"] if math.hypot(enemy["x"] - player["x"], enemy["y"] - player["y"]) <= reach]
        if kind in ("damage", "stun", "bleed", "dash_strike", "pierce", "target_area"):
            nearby = [e for e in nearby if terrain.line_clear(room, player, e)]
        preferred=player.get('preferredTarget')
        choose=lambda candidates: min(candidates,key=lambda e:(e['id']!=preferred,math.hypot(e['x']-player['x'],e['y']-player['y'])),default=None)
        covers = [o for o in terrain.obstacles(room) if math.hypot(o["x"]-player["x"],o["y"]-player["y"]) <= reach]
        cover_target = min(covers, key=lambda o: math.hypot(o["x"]-player["x"],o["y"]-player["y"]), default=None) if not nearby and ability["attackType"] == "light" else None
        if kind in ("damage", "stun", "bleed", "dash_strike", "pierce", "target_area") and not nearby and not cover_target:
            raise ValueError("No enemy is in range.")
        if kind == "area" and not nearby and not covers:
            raise ValueError("No enemy is close enough.")
        if kind == "revive" and not any(member["status"] in ("downed", "fallen") and
                math.hypot(member["x"] - player["x"], member["y"] - player["y"]) <= reach
                for member in room["players"].values()):
            raise ValueError("No downed ally is close enough to revive.")
        if kind == "team_revive" and not any(member["status"] in ("downed", "fallen") for member in room["players"].values()):
            raise ValueError("No fallen allies need reviving.")
        healing_targets = [m for m in self._active_players(room) if m["status"] == "alive" and m["hp"] < m["maxHp"]
                           and (not reach or math.hypot(m["x"]-player["x"],m["y"]-player["y"]) <= reach)]
        if kind == "team_heal" and not healing_targets:
            raise ValueError("No injured ally is in range.")
        if ability_id in ("healing_ray", "major_mend") and healing_targets:
            healing_targets = [min(healing_targets, key=lambda m: m["hp"]/m["maxHp"])]
        if player["mana"] < ability["manaCost"]:
            raise ValueError(f"{ability['name']} needs {ability['manaCost']} mana.")
        player["mana"] -= ability["manaCost"]
        if ability["attackType"] == "ultimate":
            telemetry.add(room, player["id"], "ultimateCasts", 1)
        if ability["kind"] != "summon":
            player["abilityCooldowns"][ability_id] = now + ability["cooldown"]
        player["animation"] = ability["attackType"]
        player["animationUntil"] = time.time() + 0.45
        base_damage = CLASSES[player["class"]]["damage"]*(1+.03*player.get("skillRanks", {}).get("power", 0)) + sum(item.get("damage", 0) for item in player["toolSlots"] if item)
        curse_factor = 0.75 if (player.get("curse") or {}).get("effect") == "weakened" else 1
        base_damage = round(base_damage * (player["damageBoost"] if player["damageBoostUntil"] > now else 1) * curse_factor)
        if kind in ('damage', 'stun', 'bleed', 'dash_strike', 'pierce', 'area', 'target_area'):
            base_damage = max(1, round(base_damage*tactical.direct_factor(player, now, consume=True)))
        ranged_class = player["class"] in ("Wizard", "Archer", "Cleric", "Druid", "Bard", "Healer")
        if kind in ("damage", "stun", "bleed", "dash_strike", "pierce"):
            nearest = choose(nearby + ([cover_target] if cover_target else []))
            if nearest:
                player["facingX"], player["facingY"] = nearest["x"] - player["x"], nearest["y"] - player["y"]
            if ranged_class and nearest and kind not in ("dash_strike", "bleed"):
                self._add_effect(room, "cast", player["x"], player["y"], CLASSES[player["class"]]["color"],
                                 nearest["x"], nearest["y"], 0.32, attack_class=player["class"])
            elif kind in ("damage", "stun", "bleed", "dash_strike", "pierce"):
                self._add_effect(room, "slash", player["x"], player["y"], CLASSES[player["class"]]["color"],
                                 nearest["x"] if nearest else player["x"], nearest["y"] if nearest else player["y"],
                                 0.34, attack_class=player["class"])
        elif kind in ("team_heal", "revive", "team_revive"):
            self._add_effect(room, "heal", player["x"], player["y"], CLASSES[player["class"]]["color"], duration=0.6, attack_class=player["class"])
        elif kind in ("area", "target_area"):
            center = choose(nearby) if kind == 'target_area' else player
            self._add_effect(room, "cast" if kind=='target_area' else "burst", center["x"], center["y"], CLASSES[player["class"]]["color"], duration=0.55, attack_class=player["class"])
        else:
            self._add_effect(room, "aura", player["x"], player["y"], CLASSES[player["class"]]["color"], duration=0.6, attack_class=player["class"])

        if cover_target:
            player["facingX"], player["facingY"] = cover_target["x"]-player["x"], cover_target["y"]-player["y"]
            if ranged_class:
                self._launch_projectile(room, side="hero", owner_id=player["id"], target_id=cover_target["id"],
                    x=player["x"], y=player["y"]-8, damage=round(base_damage*power),
                    color=CLASSES[player["class"]]["color"], attack_class=player["class"])
            else:
                terrain.damage_cover(self, room, cover_target, round(base_damage*power))
        elif kind in ("damage", "stun", "bleed", "dash_strike"):
            target = choose(nearby)
            if ranged_class and kind in ("damage", "stun"):
                speed = ability.get('projectileSpeed', 360 if player["class"] == "Archer" else 260 if player["class"] == "Wizard" else 220)
                self._launch_projectile(room, side="hero", owner_id=player["id"], target_id=target["id"],
                    x=player["x"], y=player["y"] - 8, damage=round(base_damage * power),
                    color=CLASSES[player["class"]]["color"], attack_class=player["class"], effect_kind=kind, speed=speed,
                    splash=ability.get('splashRadius', 0), ability_id=ability_id)
                target = None
            if target is None:
                pass
            else:
                if kind == "dash_strike":
                    start_x, start_y = player['x'], player['y']
                    distance = max(1, math.hypot(target["x"] - player["x"], target["y"] - player["y"]))
                    terrain.move(room, player, target["x"]-(target["x"]-player["x"])/distance*28, target["y"]-(target["y"]-player["y"])/distance*28)
                    tactical.dashed(player, now, math.hypot(player['x']-start_x, player['y']-start_y))
                if kind == "stun":
                    self._stun(target, now)
                    boss_ai.interrupt(self, room, target, now)
                if kind == "bleed":
                    target["bleedOwner"] = player["id"]
                    target["bleedUntil"] = now + 5
                    target["bleedDamage"] = max(1, round(base_damage * 0.45))
                    target["lastBleedTick"] = now
                    target["bleedBoostSource"] = player.get("damageBoostSource")
                    target["bleedBoostFactor"] = player["damageBoost"] if player["damageBoostUntil"]>now else 1
                self._damage_enemy(room, player, target, round(base_damage * power))
        elif kind == "area":
            for cover in covers:
                terrain.damage_cover(self, room, cover, round(base_damage*power))
            targets = [enemy for enemy in list(room["enemies"]) if math.hypot(enemy["x"] - player["x"], enemy["y"] - player["y"]) <= reach]
            for enemy in targets:
                if ability_id == 'death_bloom': tactical.bleed(player, enemy, now, base_damage*.2)
                self._damage_enemy(room, player, enemy, round(base_damage * power))
        elif kind == 'target_area':
            target = choose(nearby)
            room.setdefault('hazards', []).append(dict(id=secrets.token_hex(5), side='hero', ownerId=player['id'],
                x=target['x'], y=target['y'], radius=ability['blastRadius'], damage=round(base_damage*power),
                color=CLASSES[player['class']]['color'], kind='arrow_rain', activatesAt=now+ability['impactDelay'],
                expiresAt=now+ability['impactDelay']+.3, nextHitAt=now+ability['impactDelay'],
                boostSource=player.get('damageBoostSource'),boostFactor=player['damageBoost'] if player['damageBoostUntil']>now else 1))
        elif kind == "pierce":
            target = choose(nearby)
            if ranged_class:
                self._launch_projectile(room, side="hero", owner_id=player["id"], target_id=target["id"],
                    x=player["x"], y=player["y"] - 8, damage=round(base_damage * power),
                    color=CLASSES[player["class"]]["color"], attack_class=player["class"], speed=360, splash=48, ability_id=ability_id)
            else:
                for enemy in sorted(nearby, key=lambda item: (item["id"]!=preferred, math.hypot(item["x"] - player["x"], item["y"] - player["y"])))[:3]:
                    self._damage_enemy(room, player, enemy, round(base_damage * power))
        elif kind == "self_ward":
            player["wardUntil"] = now + 8
            player["wardFactor"] = power
            player["wardSource"] = player["id"]
        elif kind == "team_ward":
            for member in room["players"].values():
                if not reach or math.hypot(member["x"] - player["x"], member["y"] - player["y"]) <= reach:
                    if member["wardUntil"] <= now or power <= member.get("wardFactor", 1):
                        member["wardUntil"], member["wardFactor"], member["wardSource"] = now+8, power, player["id"]
        elif kind == "self_damage":
            player["damageBoostUntil"], player["damageBoost"] = now + 8, power
            player["damageBoostSource"] = player["id"]
        elif kind == "team_damage":
            for member in room["players"].values():
                member["damageBoostUntil"], member["damageBoost"] = now + 8, power
                member["damageBoostSource"] = player["id"]
        elif kind == "team_heal":
            for member in healing_targets:
                healed = min(member["maxHp"]-member["hp"], power)
                member["hp"] += healed
                telemetry.add(room, player["id"], "healingGiven", healed)
        elif kind == "revive":
            fallen = [member for member in room["players"].values() if member["status"] in ("downed", "fallen") and math.hypot(member["x"] - player["x"], member["y"] - player["y"]) <= reach]
            target = min(fallen, key=lambda member: math.hypot(member["x"] - player["x"], member["y"] - player["y"]))
            self._restore_ally(room, player, target, 0.45)
            self._say(room, "system", "The Gauntlet", f"{player['name']} quickly revived {target['name']}.")
        elif kind == "team_revive":
            revived = []
            for target in room["players"].values():
                if target["status"] in ("downed", "fallen"):
                    self._restore_ally(room, player, target, 0.4)
                    revived.append(target["name"])
            self._say(room, "system", "The Gauntlet", f"{player['name']} called every fallen ally back: {', '.join(revived)}.")
        elif kind == "speed":
            player["speedBoostUntil"], player["speedBoost"] = now + 6, power
        elif kind == "team_speed":
            for member in room["players"].values():
                member["speedBoostUntil"], member["speedBoost"] = now + 6, power
        elif kind == "invisible":
            player["invisibleUntil"] = now + 5
        elif kind == "taunt":
            player["tauntUntil"] = now + 7
        elif kind == "summon":
            light_power = next(entry[4] for entry in ABILITY_SETS[player["class"]]
                               if entry[7] == "light" and entry[0] in player["abilities"])
            light_damage = max(1, round(base_damage * light_power))
            self._summon_companion(room, player, ability_id, round(light_damage * power), now)
            room["summons"][-1].update(lightPower=light_power,damageScale=power)
        elif kind == "blink":
            enemy = min(room["enemies"], key=lambda entry: math.hypot(entry["x"] - player["x"], entry["y"] - player["y"]), default=None)
            if enemy:
                start_x, start_y = player['x'], player['y']
                dx, dy = player["x"] - enemy["x"], player["y"] - enemy["y"]
                distance = max(1, math.hypot(dx, dy))
                terrain.move(room, player, player["x"]+dx/distance*reach, player["y"]+dy/distance*reach)
                tactical.dashed(player, now, math.hypot(player['x']-start_x, player['y']-start_y))
        self._say(room, "system", "The Gauntlet", f"{player['name']} used {ability['name']}.")

    @staticmethod
    def _stun(enemy, now):
        if enemy.get("stunResistUntil",0) > now:
            return
        duration = .25 if enemy.get("boss") else .55 if enemy.get("miniBoss") else .6
        enemy.update(stunUntil=now+duration, stunResistUntil=now+1.8)

    def _attack(self, room: dict, player: dict) -> None:
        if room["phase"] != "combat" or room.get("waveStartsAt") or player["status"] != "alive":
            return
        light = next((a[0] for a in ABILITY_SETS.get(player["class"], [])
                      if a[7] == "light" and a[0] in player["abilities"]), None)
        if light:
            try:
                self._cast_ability(room, player, player["abilities"].index(light))
            except ValueError:
                # Holding keeps trying as targets enter range and the skill recharges.
                pass

    def _revive(self, room: dict, rescuer: dict) -> None:
        if room["phase"] != "combat" or rescuer["status"] != "alive":
            return
        downed = [
            player for player in room["players"].values()
            if player["status"] == "downed"
            and math.hypot(player["x"] - rescuer["x"], player["y"] - rescuer["y"]) <= 62
        ]
        if not downed:
            return
        target = min(downed, key=lambda p: math.hypot(p["x"] - rescuer["x"], p["y"] - rescuer["y"]))
        if rescuer.get('reviving') == target['id']: return
        rescuer['rescueGuardUntil'] = 0
        rescuer["reviving"] = target["id"]
        rescuer["reviveStarted"] = time.monotonic()
        now = time.monotonic()
        if 'rescuer' in tactical.effects(rescuer) and rescuer.get('rescueGuardReadyAt', 0) <= now:
            rescuer.update(rescueGuardUntil=now+2, rescueGuardReadyAt=now+8)

    @staticmethod
    def _record_death(room: dict, player: dict) -> None:
        if not player.get("deathRecorded"):
            telemetry.count(room, player["id"], "deaths")
            player["deathRecorded"] = True

    @staticmethod
    def _restore_ally(room: dict, rescuer: dict, target: dict, health_fraction: float) -> None:
        if target["status"] not in ("downed", "fallen"):
            return
        telemetry.count(room, rescuer["id"], "revives")
        target.update(status="alive", hp=max(1, round(target["maxHp"] * health_fraction)),
                      downedUntil=0, deathRecorded=False)
        telemetry.add(room, rescuer["id"], "healingGiven", target["hp"])

    def _tick_puzzle(self, room: dict) -> None:
        if not room.get("puzzle"):
            return
        active = self._active_players(room)
        if not active:
            return
        assign_clues(room["puzzle"], [p["id"] for p in active], {p["id"]: p["name"] for p in active})
        all_ready = True
        now = time.monotonic()
        for player in active:
            player_id = player["id"]
            puzzle_room = room["puzzle"]["rooms"][player_id]
            standing = next((entry["rune"] for entry in puzzle_room["runes"]
                             if math.hypot(player["x"] - entry["x"], player["y"] - entry["y"]) <= 34), None)
            puzzle_room["standing"] = standing
            if standing != puzzle_room["target"]:
                all_ready = False
                if len(active) == 1 and standing and now - puzzle_room["wrongAt"] >= 2.5:
                    puzzle_room["wrongAt"] = now
                    room["strainMistakes"] += 1
                    self._say(room, "system", "The Gauntlet", f"{player['name']} stands on the wrong rune. The run grows slightly more dangerous.")
        if not all_ready:
            # Only evaluate a complete group answer; individual rune feedback would
            # let each player solve their chamber without exchanging clues.
            if len(active) > 1:
                attempt = tuple(room["puzzle"]["rooms"][p["id"]]["standing"] for p in active)
                if all(attempt) and attempt != room["puzzle"].get("lastAttempt"):
                    room["puzzle"]["lastAttempt"] = attempt
                    room["strainMistakes"] += 1
                    self._say(room, "system", "The Gauntlet", "The group answer does not match. Exchange your totem clues and try again.")
            return
        room["puzzlesCompleted"] += 1
        self._advance_curses(room)
        room["puzzle"] = None
        room["stageWave"] = 1
        room["phase"] = "combat"
        self._add_effect(room, "puzzle_solved", WIDTH / 2, HEIGHT / 2, "#ffe08a", duration=1.2, text="RUNE GATE OPEN")
        self._say(room, "system", "The Gauntlet", "Every adventurer found the right rune. The gate opens!")
        self._reset_cooldowns(room)
        self._spawn_wave(room)

    def _check_party_wipe(self, room: dict) -> bool:
        active = self._active_players(room)
        if room["phase"] != "combat" or not active or any(p["status"] == "alive" for p in active):
            return False
        for player in active:
            self._record_death(room, player)
        self._finish_stage_stats(room, "defeat")
        self._dismiss_summons(room)
        room["phase"] = "defeat"
        room["runes"] -= math.floor(room["runes"] * 0.4)
        message = "The party has fallen. 40% of its Runes are lost; items remain. "
        message += "The host can return to the last inn." if room["checkpoint"] else "The party never reached an inn checkpoint."
        self._say(room, "system", "The Gauntlet", message + " Evil claims the field.")
        return True

    def tick(self) -> None:
        now = time.monotonic()
        with self.lock:
            for room in self.rooms.values():
                if not self._update_presence(room, now):
                    continue
                telemetry.tick(room, now)
                room["effects"] = [effect for effect in room["effects"] if effect["until"] > time.time()]
                # Companions and in-flight attacks cannot clear a stage after everyone falls.
                if self._check_party_wipe(room):
                    room["projectiles"] = []
                    continue
                boss_ai.tick_areas(self, room, now)
                terrain.tick(self, room, now)
                combat_encounters.tick(self,room,now)
                self._check_party_wipe(room)
                if room["phase"] == "defeat":
                    continue
                self._tick_projectiles(room, now)
                progression.tick(self, room, now)
                companion_ai.tick(self, room, now, ABILITY_SETS)
                for player in room["players"].values():
                    if not player.get("connected", True):
                        continue
                    elapsed = min(1.0, max(0, now - player["lastManaTick"]))
                    player["lastManaTick"] = now
                    if room["phase"] == "combat" and player["status"] == "alive":
                        player["mana"] = min(player["maxMana"], player["mana"] + 2 * elapsed*(1+.05*player.get("skillRanks", {}).get("focus", 0)))
                    elif room["phase"] in ("town", "routes", "stage_exit", "puzzle", "chest", "peace"):
                        player["mana"] = min(player["maxMana"], player["mana"] + 6 * elapsed*(1+.05*player.get("skillRanks", {}).get("focus", 0)))
                    if progression.locked(room, player):
                        player.update(dx=0, dy=0, lastMove=now)
                    if room["phase"] in ("town", "routes", "stage_exit", "puzzle", "chest", "peace") and player["status"] == "alive":
                        dt = min(0.1, max(0, now - player["lastMove"]))
                        player["lastMove"] = now
                        speed = CLASSES.get(player["class"], {}).get("speed", 140)
                        if room["phase"] == "town" and player.get("townInterior"):
                            next_x = max(180, min(WIDTH-180, player["x"]+player["dx"]*speed*dt))
                            next_y = max(100, min(HEIGHT-64, player["y"]+player["dy"]*speed*dt))
                            if progression.interior_walkable(room, player, next_x, player["y"]):
                                player["x"] = next_x
                            if progression.interior_walkable(room, player, player["x"], next_y):
                                player["y"] = next_y
                            if player.get("townExitReady"):
                                player["townExitReady"] = False
                        else:
                            next_x = max(28, min(WIDTH - 28, player["x"] + player["dx"] * speed * dt))
                            next_y = max(30, min(HEIGHT - 30, player["y"] + player["dy"] * speed * dt))
                            if room["phase"] == "routes":
                                if self._on_fork_path(next_x, player["y"]):
                                    player["x"] = next_x
                                if self._on_fork_path(player["x"], next_y):
                                    player["y"] = next_y
                            elif room["phase"] == "town":
                                if self._town_walkable(room, next_x, player["y"]):
                                    player["x"] = next_x
                                if self._town_walkable(room, player["x"], next_y):
                                    player["y"] = next_y
                            else:
                                if room["phase"] in ("stage_exit", "chest"):
                                    terrain.move(room, player, next_x, next_y)
                                else:
                                    player["x"], player["y"] = next_x, next_y
                            if room["phase"] == "town" and player.get("townExitReady"):
                                gate_x, gate_y = TOWN_GATE
                                if math.hypot(player["x"] - gate_x, player["y"] - gate_y) > 78:
                                    player["townExitReady"] = False
                        if room["phase"] == "town" and player.get("townInteraction"):
                            npc = self._nearby_npc(room, player)
                            if not npc or npc["id"] != player["townInteraction"]:
                                player["townInteraction"] = None
                                player["guildPreview"] = None
                if room["phase"] in ("stage_exit", "routes"):
                    self._tick_travel(room)
                if room["phase"] == "chest":
                    self._finish_chest_if_ready(room)
                if room["phase"] == "town":
                    active = self._voting_players(room)
                    can_leave = not (room.get("townWelcome") and not room["townWelcome"].get("done")) and (room.get("townsVisited") != 1 or all(p.get("trainingKnown") for p in active if not p.get("bot")))
                    if active and can_leave and all(p.get("townExitReady") and not p.get("townInterior") and
                            math.hypot(p["x"] - TOWN_GATE[0], p["y"] - TOWN_GATE[1]) <= 78 for p in active):
                        # Reuse the normal exit path without reversing its ready vote.
                        active[0]["townExitReady"] = False
                        self._vote_town_exit(room, active[0])
                if room["phase"] == "puzzle":
                    self._tick_puzzle(room)
                    if room["phase"] != "combat":
                        continue
                if room["phase"] != "combat":
                    continue
                if room.get("waveStartsAt"):
                    if now < room["waveStartsAt"]:
                        for member in room["players"].values():
                            if member["status"] != "alive" or not member.get("connected", True):
                                continue
                            dt = min(0.1, max(0, now - member["lastMove"]))
                            member["lastMove"] = now
                            speed = CLASSES.get(member["class"], {}).get("speed", 140)
                            terrain.player_move(room, member, member["dx"], member["dy"], speed, dt)
                        continue
                    room["waveStartsAt"] = 0
                    self._spawn_wave(room, preserve_players=True)
                for player in room["players"].values():
                    if not player.get("connected", True):
                        continue
                    if player["status"] == "downed":
                        continue
                    if player["status"] != "alive":
                        continue
                    dt = min(0.1, max(0, now - player["lastMove"]))
                    player["lastMove"] = now
                    curse_speed = 0.75 if (player.get("curse") or {}).get("effect") == "sluggish" else 1
                    speed = CLASSES.get(player["class"], {}).get("speed", 140) * (player["speedBoost"] if player["speedBoostUntil"] > now else 1) * curse_speed
                    terrain.player_move(room, player, player["dx"], player["dy"], speed, dt)
                    if player["attacking"]:
                        self._attack(room, player)
                for rescuer in room["players"].values():
                    target_id = rescuer.get("reviving")
                    if not target_id or rescuer["status"] != "alive" or not rescuer.get("connected", True):
                        continue
                    target = room["players"].get(target_id)
                    if not target or target["status"] != "downed" or math.hypot(target["x"] - rescuer["x"], target["y"] - rescuer["y"]) > 62:
                        rescuer["reviving"] = None
                        continue
                    duration = 0.8 if rescuer["class"] == "Healer" else 1.8
                    if now - rescuer["reviveStarted"] >= duration:
                        self._restore_ally(room, rescuer, target, 0.3)
                        rescuer["reviving"] = None
                        self._say(room, "system", "The Gauntlet", f"{rescuer['name']} revived {target['name']}.")

                self._tick_summons(room, now)
                for enemy in list(room["enemies"]):
                    if room['phase']!='combat': break
                    if enemy.get("bleedUntil", 0) > now and now - enemy.get("lastBleedTick", 0) >= 1:
                        enemy["lastBleedTick"] = now
                        owner = room["players"].get(enemy.get("bleedOwner"), room["players"][room["host"]])
                        self._damage_enemy(room, owner, enemy, enemy.get("bleedDamage", 0),
                            boost_source=enemy.get("bleedBoostSource"), boost_factor=enemy.get("bleedBoostFactor",1))
                        if room["phase"] != "combat":
                            break
                    if enemy.get("stunUntil", 0) > now:
                        continue
                    available = [p for p in self._combat_targets(room) if p["status"] == "alive"]
                    if not available:
                        break
                    taunting = [p for p in available if p["status"] == "alive" and p.get("tauntUntil", 0) > now]
                    visible = [p for p in available if p["status"] == "alive" and p.get("invisibleUntil", 0) <= now]
                    targets = taunting or visible or [p for p in available if p["status"] == "alive"]
                    if not targets:
                        continue
                    target = min(targets, key=lambda p: math.hypot(p["x"] - enemy["x"], p["y"] - enemy["y"]))
                    wards=combat_encounters.ward(room)
                    if wards and not taunting and sum(map(ord,enemy['id']))%2==0: target=wards[0]
                    squadron = room.get("encounterName") == "Mini-boss Squadron"
                    if squadron:
                        target_pool = taunting or visible or targets
                        enemy_index = room["enemies"].index(enemy)
                        target = target_pool[enemy_index % len(target_pool)]
                    self._tick_enemy(room, enemy, target, now)
                self._check_party_wipe(room)


WORLD = GameWorld(storage_dir=Path(__file__).parent / "data", disconnect_timeout=15)

