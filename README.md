# The Gauntlet

A browser client with a Python authoritative game server. The game supports room codes, parties of up to four, unique class selection, per-class Light/Special/Ultimate ability choices, regenerating mana, party chat, shared movement, themed battlefields, enemy waves and bosses, puzzle paths, shops, equipment, and inn checkpoints. Equipped weapons and armor appear on player sprites and affect combat.

## Run locally

Requires Python 3.10 or newer. No third-party Python packages are required.

Run: python server.py

Open http://127.0.0.1:8000 on the host computer. Do not open `static/index.html` directly; a `file://` page cannot reach the Python API. For another device on the same Wi-Fi, open http://<host-computer-LAN-IP>:8000 and enter the room code.

The development server is not a public deployment. Publishing a public link will require choosing a hosting service and configuring the Python server for it.

## Controls

Sound effects activate after a click, tap or keypress. Open **Sound settings**
on the main menu or under the in-game **Menu** to adjust effects volume, mute,
or play a test sound. Settings are saved in this browser. The retro Bfxr sound
bank ships locally; no audio tool installation is needed to play. Rebuild/tuning
instructions are in `art/audio/WORKFLOW.md`.

- Move: WASD by default, or arrow keys; touch movement pad on phones.
- Light attack: hold left click on the arena or hold the Attack button to repeat
  your equipped Light at its normal cooldown. A quick click/tap also works.
  Release, switch tabs, or open a dialog to stop. Movement and attack can be held together.
- Special: Q. Ultimate: X. Both keys can be changed from Controls & keybindings in the main menu.
- Every hero's Ultimate has a 15-second cooldown, including when a combat stage
  starts. New waves do not restart that timer. Mana costs are unchanged.
- Equipped utilities: 1, 2, and 3 (the number row or numpad), or click/tap their HUD slots.
- Revive: stand near a downed teammate and hold E or Revive. Downed allies have
  no expiry countdown; they stay revivable while someone is standing. Reviving
  takes 1.8 seconds, or 0.8 for Healers. Everyone down at once is still a party wipe.
- Druid: both Light choices fire projectiles. Choose Lightning Bird or Fire Wolf
  for Special, and Ice Bear or Nature Rock Golem for Ultimate. Each attacks the
  nearest enemy. Its ability stays locked while it lives, then recharges for
  8 seconds (Special) or 15 seconds (Ultimate) after death. Each new stage removes
  summons, makes Special ready, and starts Ultimate's 15-second cooldown.
  Summons persist between waves. Special summons deal 90% of the
  equipped Light's damage per hit; Ultimate summons deal twice that Light damage.
- Chat: use Party Chat beside the shared game view.

## Exploring the run

- After clearing a stage and opening any treasure, connected human players gather at the top opening. Non-town transitions have a 50% chance of a fork; otherwise the party advances directly. Town arrivals are direct. At forks, humans walk along the left or right path to the screen edge to vote. A split party uses the human majority, with the host breaking a tie. NPC companions follow and never count toward votes or exit readiness; they still count toward combat difficulty.
- Town layouts shuffle each visit, including the Guild. Enter the Inn, Store, Alchemy Lab, or Guild with E, then approach the NPC inside and press E. Return through the door. Connected human players gather at the village gate and vote with E to leave; the NPC companion is not required.
- The Guildmaster offers one class change per player per run. Your current hero and heroes taken by teammates are disabled. Pick a new hero, review its six shuffled class-specific skills, and choose one Light, one Special, and one Ultimate before confirming. Back out or press Escape to cancel without using the change. Checkpoint recovery keeps your new class and the used allowance.
- Open Pouch and press Expand to read descriptions for carried and equipped items. Equip items anywhere.
- The original 22 equipable items (13 tools and 9 utilities) have individual pixel-art
  icons in the pouch, equipment slots, shop, pending chest loot and utility bar.
  The full catalog and retained artwork are in `art/item-sprites/`. Refresh the
  browser after updating the client or sprites.
- All eight heroes use imported directional sheets, as do Wolf, Serpent Guard, Minotaur, Cave Troll, Cave Spider, Dragon, Chimera, and all four Druid summons. Troll minibosses and the Ancient Stone Behemoth share the troll sheet. Each new hero/summon sheet has idle, movement and general attack/cast animations in eight directions. Elemental enemies keep their colored glows.
- Enemies have three progressive anticipation poses for charge/pounce, heavy
  attacks and ranged/channel attacks, timed to their actual windup. Attack
  release frames also play for bosses. Eight directions use mirrored side views.
- Dracos use the original compact Dragon design. Final Dragons use a new,
  much larger fierce design with broad wings, a long armored body and snarling
  jaws, including idle, walk, attack and charge/breath/channel windup animations.
  Elemental glows and phase-two growth remain. Sources, exact prompts and rebuild
  instructions are retained in `art/dragon-lineage/WORKFLOW.md`.
- Breakable crates and rocks have intact, damaged and debris sprites in all four
  region palettes. Traps show warning and raised-spike states; poison, ice, boss
  hazards, projectiles and combat effects use animated pixel art. Danger outlines
  and aim lanes remain visible. Each existing curse has a distinct icon in the
  affected player's pouch. Sources, prompts, exports and rebuild instructions are
  retained in `art/combat-sprites/WORKFLOW.md`. Refresh the HTTP page for these
  client/sprite changes; no server restart is needed for this art pass.
- Each new run makes one 8% roll for an assassination ambush, with at most one occurrence even after checkpoint recovery. Ambushes bring stronger enemies from all four sides, scaled to party size.
- Canvas animation runs independently of multiplayer polling, interpolates movement, and caches battlefield scenery and elemental glows.
- Woodland, ruins, cavern and frost battlefields use matching pixel-art scenery,
  sampled at 480x270 and displayed without smoothing. The art also remains during
  treasure and stage exits. Retained sources, prompts and rebuild instructions
  are in `art/stage-fields/WORKFLOW.md`; refresh the browser after art changes.
- Fork screens have woodland, ruins, cavern and frost versions matching the
  area the party just left. Both branches retain that style until a route is
  chosen. Their textured paths follow the existing walking corridors. Sources,
  prompts and rebuild steps are retained in `art/fork-fields/WORKFLOW.md`.
- Villages now have woodland, ruins, cavern and frost art matching the area
  just left. All six buildings, their six roof colors, furnished interiors,
  upstairs rooms, beds, stairs and doors are themed. The injured hunter's road
  also matches that region. Shuffled layouts and save/interaction locations
  remain the same. See `art/village-art/WORKFLOW.md` for retained artwork and
  rebuild steps.
- Menus, hero selection, the HUD, shops, dialogs and pouch/equipment displays
  use matching timber, slate and brass styling, with actual hero portraits and
  item icons. Refresh the HTTP page after updating these static assets.

## Party tools and puzzles

- Teammate health and a Needs revive status remain visible during play. Help and
  Gather ping your location; Enemy arms a marker, then click/tap the foe to mark.
  Tap Cancel mark to back out. Pings last five seconds and have a short rate limit.
- Multiplayer totems hold another connected player's clue. Use Share clue or
  Chat, then stand on your answers together. Rune colors do not reveal individual
  correctness; a wrong complete group answer gives shared feedback. Solo totems
  describe your own answer. Disconnections reassign clues to the remaining party.
- Optional How to play is available on the main menu and under the in-game Menu.
  It explains movement, abilities, revives, clues, town services and saves.

## Saved runs and connections

Resting at a bed in an unlocked upstairs inn room writes a party checkpoint to
`data/checkpoints/ROOM.json` using an atomic file replacement. Talking to the
innkeeper does not save. Purchases, equipment, training and Guild changes update
the save while you remain in that saved village. A later village needs its own
bed checkpoint. After restarting `server.py`, players return to the saved bed
with their classes, items, shared Runes and progression intact. Progress after
leaving that village is lost. Runs without a bed checkpoint stay only in memory.
Older saves made before this update remain valid and return to their saved town.

Main menu disconnects without deleting your run. Continue saved run restores
your identity in the same browser and server address; keep that site's browser
data. An invite code creates a new participant in a lobby, not a replacement for
your saved identity. If moving computers, copy `data/` as well as the source;
browser identity must also remain available to reconnect to an existing hero.

A connection is considered offline after 15 seconds without requests; stale
movement stops after two seconds. Offline heroes do not block exits, route votes,
chests or puzzles. Host control moves to a connected player. The world and combat
timers pause when nobody is connected. Rejoining heroes catch up to their party.
Checkpoint files stay local and are excluded from Git. Invalid saves are preserved
and logged rather than overwriting the remaining valid saves.

## Balance observations and next work

Menu → Run stats shows overall per-player totals, including current combat: damage
dealt, damage taken, revives, deaths and kills. Damage dealt includes summons;
damage taken is hero HP lost; kills credit the finishing attacker; deaths count
falling or a party wipe, and revives count each ally rescued. Totals survive stage
changes and checkpoint retries; disk recovery restores the totals saved at the inn.
Older checkpoints start these new counters when this update is loaded. JSON export
contains the same five counters and player labels. Local server
observations append to `data/balance.jsonl`: hero/summon damage, actual HP lost,
armor/ward prevention, summon spawns/deaths/uptime and individual survival times,
stage time, party size, Ultimate casts and opening-cooldown checks. Summon HP
absorbed is measured directly; it is not hypothetical damage prevented to a hero.
Stats are fetched on demand rather than included in every movement poll.

`python -B tools/balance_probe.py` reproduces 90 bot observations across stages
1 and 8, all eight solo heroes and 2–4-player parties. See
`reports/BALANCE_REPORT.md` and `reports/balance-probe.json` for methodology,
limitations and results. These simulations do not replace human playtests.
The saved thirteen-point roadmap is `IMPROVEMENT_BACKLOG.md`.

Checks: `python -B -m unittest discover -s tests -v`, `node --check static/app.js`,
`node --check static/coordination.js`, and `node tests/test_client_actions.cjs`.
The optional canvas regression script `tests/test_damage_flash.cjs` also needs
`@napi-rs/canvas` available to Node; the game itself needs no Node installation.
`node tests/test_town_sprites.cjs` checks the imported NPC and chest animation cells.

## Hunter story and training

A peaceful clearing appears once, after stage one or two, without consuming an
extra combat stage. Speak to the wounded hunter, who was injured by the dragon,
to accept the quest. Menu → Quest shows your objective. Solo and multiplayer
parties continue once all present humans accept and gather at the northern exit.

On the first village visit, a runner approaches and all movement pauses until
present players finish the welcome dialogue. Everyone must then speak to the
innkeeper and finish the training tutorial before the party can leave. Offline
players do not hold up these interactions.
Story dialogue appears in a compact panel near the bottom of the screen so the
world remains visible, including on phones.

Hunter training has three branches, each with three ranks at one point per rank:
Vitality (+4% base maximum HP), Power (+3% base attack damage), and Focus (+5%
mana regeneration). Each hero earns one point for the first inn tutorial and
one for each of the first two great bosses, once per run. Training applies for
that run, follows Guild class changes, and persists in bed checkpoints.

The inn's stairs lead to three guest rooms. Some are locked and occupied; their
doors block entry. Use an available bed to restore party HP/mana and set its
checkpoint. Stairs return to the ground floor.

All heroes regenerate 2 mana/second in combat and 6 outside combat, before Focus
bonuses. Enemies retarget living heroes or summons when an ally goes down;
downed heroes take no further hits during their rescue window. Druid idle/walk
animation is slower, and Ice Bear/Nature Golem art is larger than the Druid.
Character, NPC, enemy and summon ground shadows are circular.

The supplied town pack provides directional idle/walk/gesture animations for the
Merchant, Guildmaster, Alchemist, Innkeeper and eight villager designs. Villagers
remain decorative. The floating chest uses its closed loop until opened, then
its open loop while players finish choosing rewards.

## Towns, routes and enemy pressure

Non-town stage transitions roll once for a fork: 50% fork, 50% direct passage.
Scheduled towns always arrive directly; fork destinations are combat regions.
Villages generate different house arrangements, connected road layouts and tree
placements. Twelve decorative villagers appear outside, without interactions.
Inn checkpoints preserve the generated town and its visit count.

Every town visited eventually increases subsequent enemy waves: +25% health, +20% damage,
+10% movement speed and +12% attack frequency per visit. Half of that visit's
increase applies on the next combat stage and the full increase on the following
stage, added to the normal stage
scaling. Empowered enemies and miniboss squadrons also receive +15% health,
+12% damage/speed and +25% attack frequency; ranged elites approach more closely.
Town pressure does not increase again when returning to an existing checkpoint.

Click Tool 1/2 or Utility 1/2/3 on a pouch item to replace that slot directly.
The displaced item returns to the pouch, including when all ten spaces are full.
Tools can replace a different tool type. Unequipping still needs an empty space.
Cave Spider enemies now use the supplied eight-direction idle/walk/bite sheet.
The saved bot balance report predates this enemy-pressure update.


## Difficulty, companions and combat update

Before starting, the host independently chooses challenge and run length, and can add one NPC companion.
The companion occupies one of the four party slots and randomly selects an
available hero and one ability of each category when the run begins. It uses the
same health, mana, abilities, equipment, revive rules, stats and enemy scaling as
another player. It attacks nearby enemies, avoids marked danger, rescues allies,
opens treasure and follows party transitions. Human teammates can revive it.
In puzzles it reads its totem and shows your clue; use Share clue after reading
your own totem so it can choose its rune. When all humans disconnect the run
pauses, including the companion. Difficulty and companions persist at the inn.
These lobby options require a new run; old saves default to Medium / 25 stages.

| Challenge | Strength multiplier |
| --- | --- |
| Easy | 0.9x |
| Medium (default) | 1.25x |
| Hard | 1.6x |

Run length is Tester (9 stages), Short (20), Standard (25, default), or Long (30). Changing
challenge preserves the selected length. The final dragon occupies the last
stage of the chosen length. Older API clients that never specify a length keep
their former challenge-based default; the current browser always sends both.

Mode multipliers apply to the updated baseline: enemy HP and damage receive
+15% overall and an additional 5% per completed stage. The exact added factor is
`1.15 * mode_multiplier * (1 + 0.05 * (stage - 1))`, on top of existing stage,
party, town and elite scaling. Attack frequency also scales by the square root
of the mode multiplier. Bosses, puzzles, minibosses and town schedules fit the
chosen campaign length, with the final boss on its last stage.

Solo normal waves have 2–3 enemies from stage 13, 3–4 from 17, and five from 20.
Before stage 7, every party size has a 10% chance of a three-wave stage; otherwise
the stage has two waves. From stage 7 the usual party and late-stage rules apply.
Stages 13–16 have a 75% chance of three waves; stage 17 onward always has three.
Larger parties increase those numbers. Bosses and special encounters retain
their own compositions. Normal enemies periodically choose a pursuit goal and
move toward that fixed goal; they no longer strafe in response to player input.
Enemy shots turn gently toward their original target for the first 1.1 seconds,
then travel straight. Boss shots steer more slowly and show larger collision art.

Large bosses and single empowered minibosses have telegraphed attacks: slams,
lingering damage pools, large projectile volleys and committed charges. The
Labyrinth Minotaur King and Ancient Stone Behemoth move 2.5 times as fast as
before, throwing rocks and charging between slams. Boss stuns are shorter to
avoid permanent Shield Bash lock. The dragon must be defeated twice: its second
phase is visually larger, has a fresh HP pool 1.6 times its first-phase maximum,
+35% damage, +20% speed and +25% attack frequency, plus group meteor warnings.
Ground circles and charge corridors warn before damage; move out of them.

The compact pouch has ten spaces. Normal chest outcomes are 55% item, 25% only
shared Runes, and 20% healing, after the existing 12% curse check. Runes/healing
work with a full pouch. The stage exit is marked by an arrow.
The floating chest's open animation is personal: it opens on your screen only
after you open your share, including while choosing a replacement for a full pouch.
The balance probe now covers all eight heroes in solo and two- to four-player
lineups. Human playtesting is still needed; automated comparisons cannot prove
that every difficulty or loadout is equally balanced.

## Battlefield, roles and companion tactics

Combat stages include breakable crates/rocks that block movement and shots.
Your Light attacks can break cover when no visible foe is in range, and area
attacks also damage nearby cover. Traps warn for .75 seconds before firing and
rearm after four seconds. Poison damages living heroes, summons and enemies
once per second; terrain weakens enemies to 1 HP so hunters earn the final kill.
Frost stages can include ice that carries momentum after releasing movement.
Cover damage and terrain persist between waves, then reset for each new stage.

Enemy behavior distinguishes chargers, ranged attackers, ambushers, bruisers and
supports. Short labels and danger marks appear during attack wind-ups. Chargers commit to a rush, ambushers flank and lunge, ranged enemies
keep distance, bruisers announce area swings, and larger groups can include a
support that heals one wounded foe. Downed heroes remain excluded as targets.
Bosses show countdowns, attack lanes/fans or danger circles, then stop during a
visible recovery period. Stronger attack-rate scaling never shortens their wind-up.

NPC companions sidestep incoming shots, escape ground warnings and charge lanes,
alternate escape directions, retreat when a ranged hero is crowded and navigate
around cover. They keep attacking as they move; rescuing yields to immediate danger.
They use their normal hero movement speed and receive normal damage.

Summon damage per hit and death recharge stay as described above. Their health
and attack frequency are lower: Bird 40 HP / 1.15s; Wolf 65 / 1.15s; Bear 125 /
1.4s; Golem 170 / 1.8s. Temporary damage boosts expire on summons too. Repeated
stuns have a 1.8-second resistance window; normal foes are stunned for .6s.
Gentle Mend and Major Mend now heal one injured ally, as their descriptions say.

Detailed contribution logs include actual healing, ward protection credited to
the caster, boost assistance, summon damage/absorbed HP/survival and stage times.
The visible Run stats and its download retain the five overall totals. See
`reports/COMBAT_BALANCE_NOTES.md` and `reports/BALANCE_REPORT.md` for 198 matched
before/after simulations. Reproduce with `python -B tools/balance_probe.py
--before-tuning` and `python -B tools/balance_probe.py`.

Story conversations show your hero and response on the left and the NPC and
dialogue on the right, in compact boxes. Equipped utility icons flank the central
interaction prompt: slot 1 on the left, slots 2/3 on the right. Keys 1/2/3 still
work, as do clicking/tapping the icons. The guide now explains battlefield hazards.


## Deliberate combat, controls and Dracos (2026-10-07)

Normal stages now scatter one or two breakable cover objects and one terrain
zone across the field. They persist through waves. Occasional objective stages
ask you to destroy a summoning rift, defend a ward for 32 seconds against
reinforcements from different edges, or bait a charging sentinel into rocks
for a two-second recovery opening. They begin from stage 4 and avoid scheduled
bosses, minibosses, puzzles, towns and ambushes. Objective stages are one wave;
ward destruction ends the attempt and allows the existing checkpoint retry.

From stage 17, ordinary enemy groups can include Dracos: small dragons with
124 base HP, 7 base damage and 108–126 base movement speed, before regular
scaling. They alternate a gently tracking shot and a close-range bite. Their
1.25s base attack cadence increases DPS through frequency, while .35/.4s
wind-ups remain visible. Moving beyond 55 world units avoids the bite. Their
sprite uses the existing dragon sheets at a smaller scale. Objective
reinforcements and assassination ambushes do not multiply the Draco count.

Click/tap an enemy to prefer it, or use Tab to cycle targets. Clear target or
Escape returns to automatic selection. An out-of-range or blocked preference
falls back to an eligible enemy; this does not extend ability range or bypass
cover. The local hero and selected enemy have distinct markers. Ordinary
combat names and permanent role labels are reduced, while warnings and health
remain visible. The exit keeps its arrow without the rectangular overlay.

The local hero now predicts movement immediately between authoritative server
snapshots; collisions, damage and outcomes remain server-owned. Input requests
are coalesced and sequenced so stale directions cannot overwrite key release.
Other actors still interpolate. Prediction stops after 250ms without a fresh
snapshot. Opening dialogs, downing and transitions stop movement normally.

The compact pouch hides unused equipment slots; Expand shows every slot. A
separate curse sprite slot always shows active curse art, name and remaining
stages, or an empty placeholder. It does not consume one of ten item spaces.
The corrupted dash in chest notices is corrected. Leaving via Main menu now
explains that Continue needs the current server session, while only upstairs
inn-bed checkpoints survive a restart. It offers Keep playing before leaving.

See reports/DIFFICULTY_AUDIT.md for 81 generated campaign curves and the limits
of the historical run evidence, and reports/COMBAT_UPDATE_VALIDATION.md for
regression, protocol and browser checks. Physical-phone and human multiplayer
playtests are still required, including portrait camera/aspect comfort.


## Temporary Tester mode

Choose **Tester · 9 stages** under Run length before starting. It stays available
until the user asks to remove it, and works with Easy, Medium or Hard and an
optional NPC companion. Stage progression maps to the usual 25-stage campaign:
1/4/7/10/13/16/19/22/25. Enemy HP, damage, speed ramp, group sizes, wave counts,
terrain damage and objective HP use that accelerated progression.

Tester has a miniboss at stage 2, great bosses at 3 and 6, a town at 4, a puzzle
at 5, a random rift/ward/charger objective at 8, and the two-phase dragon at 9.
Ordinary late waves guarantee one Draco from Tester stage 7; normal campaigns
retain their stage-17 introduction. Story, inn training/beds, class choices,
15-second Ultimate cooldowns and human-only votes still work normally. The HUD
shows Tester stage progress. Bed checkpoints preserve the mode and schedule.


## Portable ZIP packaging

Run `python -B tools/package_game.py` to package code, runtime sprites, original
art, documentation and tests into `releases/`, with a file manifest, checksum
and archive verification. Add `--include-checkpoints` for a local transfer that
preserves your upstairs-bed saves. Unzip the The-Gauntlet folder, run
`python server.py` there, and open `http://127.0.0.1:8000/`. Python3.10 or later
is required; the game server uses the standard library.

ZIPs, Git metadata, Python caches and data backups are excluded from source
control. Checkpoints remain local and are never included in a GitHub commit.

Add `--runtime-only` for a smaller playable ZIP. The GitHub source includes the
Python server, complete browser client, all runtime sprites and sounds, tests,
and licensed audio rebuild sources. Large original visual-art projects and
reference screenshots remain in the full local source/art ZIP. Neither public
source nor the default playable ZIP contains your bed saves.

## Tactical abilities, equipment and boss identities (2026-10-07)

Druid Briar Bolt spreads damage within 65 world units and briefly roots groups;
Thornshot fires faster and deals more sustained damage to one enemy. Wizard Arc
Bolt jumps to two nearby enemies with decreasing damage; Frost Lance deals less
sustained damage but controls a single enemy. Cleric Radiant Flask splashes a
75-unit cluster; Sanctified Throw is a faster, stronger single-target projectile.
Roots resist repeated application and have shorter duration against bosses.

Archer Rain of Arrows commits to the chosen enemy's position at cast time, up to
380 world units away, then strikes a 110-unit radius after 0.65s. Enemies can
leave that area. Cover blocks target selection. Rogue Death Bloom now applies
five seconds of bleeding to enemies hit. Ability descriptions expose the actual
range, area, delay and effects.

Four additional shop/loot tools encourage different builds. Arcane Conductor
reduces direct projectile damage by 20% in exchange for an extra half-damage
jump. Rescuer's Cuirass has only +1 ordinary armor but protects a manual rescue
for up to two seconds, with an eight-second recharge. Summoner's Staff increases
Druid summon HP by 50% while reducing the Druid's direct damage by 25%. Pursuit
Blade reduces ordinary direct damage by 15% but rewards one damaging follow-up
within two seconds of Dash, Blink or Shadowstep. These effects do not stack with
duplicates. Swapping summon equipment preserves summon health percentage.
Pouch and shop comparisons show damage/armor deltas plus gained and lost effects
for each tool slot. New tools reuse existing item art with distinct border hues.

Great bosses have signature mechanics as well as their familiar attacks:

- Minotaur: bait a charge into cover for a three-second opening and +35% damage.
- Ancient Stone Behemoth: raises and shatters breakable cover.
- Serpent Matriarch: lays connected poison areas; a successful control stun during
  her wind-up interrupts the weave.
- Fire Dragon: commits burning lanes; Ice creates breakable lane barriers;
  Storm marks positions and punishes grouped allies. Dark constrains the arena
  with a ring and Arcane uses alternating cross/center strikes.

The boss tactic line explains each fight. Dragon armor and an armor-cracking
warning foreshadow the larger true form. Phase two strengthens the elemental
mechanic, with a brief transition recovery before attacks resume.

See `reports/TACTICAL_UPDATE_VALIDATION.md` and `reports/TACTICAL_LIGHT_PROBE.md`.
Automated measurements verify implementation and relative attack roles; they
do not replace human multiplayer or physical-phone balance tests.
