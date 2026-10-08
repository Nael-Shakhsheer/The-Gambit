# Multiplayer Game Design Brief

## Working concept

A real-time, top-down pixel-art fantasy adventure for one to four players. A party chooses routes through a dangerous gauntlet of combat stages, towns, separated puzzle paths, mini-bosses, and large bosses. Players join from their own devices and share the same live game state.

The working title **The Shattered Gauntlet** was suggested during planning, but has not been approved.

## Core play

- Top-down view with tiny pixel characters.
- Real-time combat, not turn-based.
- Attacks target a nearby foe automatically so mouse/touch controls stay simple on phones and laptops.
- Supports one to four players.
- Each party member must choose a different class before the run starts; the chosen class stays fixed for the run.

## Classes

The roster began as seven classes and has expanded to eight with the requested dedicated healer.

| Class | Role and traits |
|---|---|
| Knight | Melee attacker and tank. |
| Wizard | Long-range arcane damage, medium HP, and one equipped team-assist spell at a time. |
| Archer | Long-range piercing damage, medium HP, and fast movement. |
| Cleric | Low-HP support who uses splash potions for support abilities. |
| Rogue | Fast and low HP, with high bleed damage and a short invisibility ability. |
| Druid | Lower HP than the Wizard; summons animals to fight. |
| Bard | Low-HP support who raises the team's base stats. |
| Dedicated Healer | Medium HP and low damage; greatly heals teammates and revives downed characters quickly. |

Each class has six abilities: two Light attacks, two Specials, and two Ultimates. Players equip exactly one from each category before the run. Light attacks use left click/tap, Specials use Q, and Ultimates use X. Class cards stay still when hovered; only their border and color highlight.

## Routes and stages

- After stages, players choose between routes. Some routes are easier than others, but their difficulty is hidden and randomized.
- Route choices update a hidden pressure counter that influences later encounters.
- A rare, one-use shop item gives a clear answer about which available route is easier.
- The party votes together when a path forks. If votes tie, the host’s vote wins when it is among the tied choices; otherwise a tied path is chosen at random.
- Route danger and its run-long pressure counter stay hidden. Choosing the easier path raises pressure; choosing the harder path lowers it.
- Each run secretly selects one route-pressure effect: either wave size or enemy health. It never changes both. Route pressure does not change enemy damage.
- Runs include combat, towns for exploration and NPC trading, and cooperative puzzle stages.
- Town routes lead to walkable town maps. Players move between the merchant, alchemist, innkeeper, and trail gate; there is no town-to-town travel action. The inn restores the party and becomes the latest checkpoint.
- Inns are peaceful stages and do not advance curse timers.
- Merchants use the shared Rune pool. Players can buy and sell items into their personal five-item pouch. A rare, one-use Pathfinder's Lens may appear in stock and reveals the easier next route.
- Each combat stage has two waves for one- or two-player parties and three waves for three- or four-player parties. After a wave, players keep their positions during a three-second countdown; the next group rushes in from one randomly chosen arena edge. Every enemy receives one of the eight class combat kits at random, so enemy groups can include ranged attackers and support roles.
- Enemy health, damage, speed, and attack cadence scale with party size and ramp gradually from forgiving early stages. Ranged attacks aim toward a player when fired, then travel in a visible straight path that can be dodged.
- Each boss interval contains a randomly chosen two to four mini-boss stages, spaced across the interval. A mini-boss stage is either one empowered enemy or a squadron of 2.5 times the party size.
- Large bosses appear on stages 8, 16, and 25. The first two are randomized from a pool that includes the Serpent Matriarch, Labyrinth Minotaur King, Ancient Stone Behemoth, Chimera, and Great Wolf Guardian. Stage 25 is always a dragon encounter, with its type randomized between fire, ice, dark magic, arcane, and storm.
- Defeating the third large boss ends the run with a celebratory victory screen. A full-party wipe still returns the party to its latest inn checkpoint and restores the encounter schedule saved there.
- ### Enemy and boss themes

Use a dark fantasy bestiary built around serpent people, minotaurs, wolves, and other monsters.

- **Serpent people:** spear guards, fang archers, venom throwers, and ritual shamans. Mini-boss example: a Venomscale Champion.
- **Minotaurs:** axe chargers, shield brutes, and maze wardens. Mini-boss example: a Hornbreaker Captain.
- **Wolves:** pack runners and howl callers that rally nearby enemies. Mini-boss example: a Direwolf Alpha with a wolf pack.
- **Other monsters:** cave spiders, trolls, harpies, ogres, and stone golems can add variety between factions.
- **Candidate non-dragon large bosses:** Serpent Matriarch, Labyrinth Minotaur King, Ancient Stone Behemoth, Chimera, and Great Wolf Guardian.
- The final boss is always a dragon, with the dragon type randomized (for example, fire, ice, or dark magic).

### Elemental and magical variants

Each creature family can appear with different elemental or magical affinities, changing its pixel-art appearance so variants are easy to recognize. Examples include ember-furred fire wolves, frost-covered wolves, ice-scaled serpent people, shadow-touched minotaurs, and arcane-glowing monsters.

Possible affinities include fire, ice, dark magic, arcane, poison, storm, and nature. Variants should use distinct palettes, markings, silhouettes, and small animated effects (such as embers, frost motes, shadow wisps, or arcane sparks). Their attacks can also gain a matching visual effect and a small thematic behavior difference, while keeping the underlying enemy recognizable.
These are candidate names and enemy types; individual attack patterns and stats remain to be designed.

### Enemy group sizes

Scale normal enemy waves to the number of players currently present:

- Each regular wave scales by party size: solo 1–2 enemies, duo 3–5, trio 5–8, and four players 8–12. Mini-boss squadrons remain 2.5x the party size.
- The alternate mini-boss encounter is one empowered mini-boss enemy.

From stage 8 onward, the shared enemy difficulty curve gains a small initial increase and grows steadily through stage 25. This raises health, damage, movement/projectile speed, and attack frequency for regular enemies, mini-bosses, and large bosses. At stage 8 the added increase is about 2% health/movement speed and 3% damage/attack frequency; by stage 25 it reaches about 18% health/movement speed and 29% damage/attack frequency compared with the previous tuning. Party-size scaling still applies, and this progression does not add waves or enemies.

## Cooperative puzzles

Puzzle stages are separate, private rooms for every player. Each room has six scattered runes and one totem at random positions. The totem gives a short clue; players communicate their clues over text chat, then each stands on the rune that matches their own totem. The puzzle completes only when all players are standing on their correct runes. A run always contains one puzzle; a second is possible and a third is rare. Solo runs use the same room-and-rune rule. Standing on a wrong rune counts as a mistake, but the early strain increase is barely noticeable and repeated mistakes stack up.

### Puzzle mistakes and run difficulty

- Each incorrect final answer adds one point to a hidden, run-long **Gauntlet Strain** counter. Exploring a path or inspecting a clue does not count as a mistake.
- Strain makes later enemy encounters tougher. It does not add more enemies.
- Recommended starting tuning, measured as a cumulative increase from the run's baseline: mistakes 1–2 add 0.5% each; mistakes 3–4 add 1% each; every mistake from 5 onward adds 2%. Cap the increase at 15%.
- For example, two mistakes add 1% total; five add 5%; eight add 11%. The first one or two mistakes should be barely noticeable, while repeated mistakes become a meaningful run-wide penalty.
- The counter persists through checkpoints and applies to future encounters only.
Puzzle examples can use symbols, ordered runes, statue directions, or matching sounds/colors. Keep essential clues visually distinct and avoid relying only on color.

## Combat, downed players, and checkpoints

- When a player's HP reaches zero, they enter a downed state with a revive window.
- Enemies become aggressive when a player is knocked down, making a rescue more dangerous.
- If the entire party is downed, players resume at the closest checkpoint.
- Checkpoints are at town inns.
- On a wipe, players lose 40% of their carried Runes and keep their items. Proposed integer handling: round the lost amount down to a whole Rune.
- Returning to an inn checkpoint restores the party and resumes at that town. Players keep their items and the run loses 40% of its Runes.

## Items, currency, and loadouts

Each player has these equipped slots:

- Three class abilities, chosen at the start of a run.
- Three utility slots for healing items, potions, and temporary buffs.
- Two tool slots for weapons or armor.

Players also have a pouch with up to five unequipped utility or tool items plus a separate hidden sixth slot occupied by a curse. Chest loot goes into an available pouch slot; with a full pouch, players must swap an item and receive its sale value. Equipped weapons and armor appear on the player’s pixel character.

Items range from common to legendary. Players can find, buy, keep, and sell items during a run.

After an encounter, a chest appears in the center of the area. Players walk up and open their share; there is no leave-unopened option. If the pouch is full, they must swap an item to claim the new gear. The first player to open the shared chest also collects its Rune stash. Loot rarity weights are Common 48%, Uncommon 27%, Rare 16%, Epic 7%, and Legendary 2%. Utility finds include healing, wards, mana restoration, speed, damage oil, and special arrows; weapon and armor stats scale with rarity. Each player has 100 mana; abilities spend 20–55 mana based on cooldown. Mana regenerates by 4 per second in combat and 12 per second during peaceful stages. A Mana Draught restores 50 mana.

**Runes** are the currency. Runes drop from enemies and chests, and players also earn them for clearing waves. Town shops can sell instant-heal items, mana-regeneration items, special arrows, special potions, class-specific items, buffs, and other gear. Each merchant’s stock is generated for the individual player’s chosen class, so class-specific weapons match that player. The rare, one-use route hint may appear in shops but does not always spawn.

### Cursed items

- Opening a chest has a 12% chance to attach a curse if that player is not already cursed.
- It applies a debuff and occupies a separate hidden sixth slot, so it does not displace pouch items.
- It cannot be sold or cleansed early.
- It lasts for five completed non-peaceful stages, then expires. Town/inn stages are peaceful and do not count; combat encounters and solved puzzle stages count.
- Current curse effects reduce movement speed, reduce outgoing damage, or increase incoming damage. The cursed slot stays separate from the pouch and the player can see its remaining stage count.


## End screens

- Victory: a large, celebratory screen after the final dragon is defeated.
- Defeat: a dark screen showing evil winning.

## Open design questions

1. What are the final names, attack patterns, and stats for the enemy and boss roster?
