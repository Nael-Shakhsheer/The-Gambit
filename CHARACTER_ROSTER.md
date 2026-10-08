# The Gauntlet character roster

Current implementation, checked against `game.py` on 2026-10-07.

## Playable heroes

| Hero | Role |
| --- | --- |
| Knight | Melee tank |
| Wizard | Ranged arcane caster |
| Archer | Fast ranged piercing attacks |
| Cleric | Splash-potion support |
| Rogue | Fast bleed damage and invisibility |
| Druid | Elemental summoner with projectile Light attacks |
| Bard | Team damage and movement buffs |
| Healer | Strong healing and quick revives |

## Regular enemy families

- Serpent Guard
- Minotaur
- Wolf
- Cave Spider
- Cave Troll
- Draco — small dragon, introduced in normal waves from stage 17

Each family can receive Fire, Ice, Dark, Arcane, Poison, Storm or Nature affinity.
Their combat roles determine their attacks. Dracos keep their own alternating
projectile/bite kit, with fast pursuit and high HP. Their 7 base damage per hit
is below the troll's 12; their 1.25-second attack interval is half a bruiser's.
Stage, party, challenge and town scaling still apply. Each ordinary wave rolls
a 25% Draco chance per enemy, capped at one per party member and three total.
Dracos are excluded from empowered/squadron and assassination generation.

## Miniboss and ambush variants

- Empowered minibosses use one of the five regular enemy families, with a name
  such as **Empowered Poison Serpent Guard**.
- A **Mini-boss Squadron** is a group of the regular enemy families.
- Ambush enemies are named **Assassin Serpent Guard**, **Assassin Minotaur**,
  **Assassin Wolf**, **Assassin Cave Spider** or **Assassin Cave Troll**, with
  randomized affinities and stronger stats.

## Large bosses

- Serpent Matriarch
- Labyrinth Minotaur King
- Ancient Stone Behemoth
- Chimera
- Great Wolf Guardian

## Final dragon types

- Fire Dragon
- Ice Dragon
- Dark Magic Dragon
- Arcane Dragon
- Storm Dragon

## Village NPCs

| NPC | Building | Service |
| --- | --- | --- |
| Innkeeper | Inn | Introduces hunter stat training; upstairs beds set checkpoints |
| Merchant | Store | Buy and sell items |
| Alchemist | Alchemy Lab | Potion gift or restoration |
| Guildmaster | Guild | One class change per player per run |
| Villagers | Random outdoor locations | Decorative; currently non-interactable |
| Village runner | First town | Welcomes hunters and explains the inn |
| Wounded hunter | Peaceful road after stage 1 or 2 | Introduces the dragon quest |

## Druid companions

- Lightning Bird (Special)
- Fire Wolf (Special)
- Ice Bear (Ultimate)
- Nature Rock Golem (Ultimate)

These allies have independent health, movement and nearest-enemy attack AI.
Their ability stays locked until death, then recharges for 8 seconds (Special)
or 15 seconds (Ultimate).
They persist between waves, but each new stage removes them and resets their
abilities so they must be summoned again.
Special summons hit for 90% of the equipped Light attack's damage, and Ultimate
summons for twice that damage. Each combat stage starts the Ultimate's cooldown,
as it does for every other hero.

The Trail Gate is an interactive town exit rather than a character.
