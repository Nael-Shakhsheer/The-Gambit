# The Gauntlet - project handoff

Last updated: **2026-10-09**.

## Latest GitHub publication — 2026-10-09

The user requested publishing the current playable build to
Nael-Shakhsheer/The-Gauntlet main, including the HUD, all 48 ability icons,
eight hero casting atlases and shared ability animation integration.
157 Python tests passed, as did Node syntax, equipment comparison, movement,
audio and held-attack/client checks. Public uploads exclude saved data, large
authoring projects, release archives and machine cleanup records. The earlier
tracked October 6 ZIP remains on GitHub; its local cleanup is not a request to
erase repository history. Record the verified publication commit after upload.

Publication completed and remote main/tree verified:
https://github.com/Nael-Shakhsheer/The-Gauntlet/commit/c47db9e6576e31b3fe9805c056c34886be5399ff
All 357 current public game files match GitHub blob hashes; the retained legacy
ZIP brings the repository to 358 files. This includes all 57 new runtime PNGs,
source and metadata for icons/casting animations. Saves and cleanup records were
excluded. GitHub's main archive downloads the complete playable source build.

## Ability casting poses and shared ultimate eruptions — 2026-10-09

Eight new hero animation atlases add three-frame Light, Special and Ultimate
body sequences. Each has eight directions: five generated views and three
deterministic mirrors. All 48 ability IDs connect to these class/type body
sequences and their own artwork/colors/effect treatments. Alternatives share
their class/type physical sequence; there are not 48 independent body atlases.
Druid crouches/kneels to trace summoning circles, Archer draws a massive bow,
Bard uses a full-size concert harp, and the other five heroes have matching
physical casting actions. Original idle/move sheets remain intact.

Every successful Ultimate has glowing rising pixel ribbons, expanding ground
energy, class/ability particles and its actual name visible to teammates. Shared
cast IDs and relative elapsed/remaining time come from ability_animations.py,
through player snapshots and ability_cast effects. Held Light attacks cannot
erase a longer Special/Ultimate pose. Class, stage, status and scene changes
guard stale animations; final-enemy kills can finish their brief cast into loot
or exit. Actual affected recipient IDs drive teammate buff/heal/revive particles.
Projectile visuals use existing literal ability art, including ice shards,
arrows, bottles, thorns and musical notes. Cover-target shots also retain IDs.

The four Druid summons have circle emergence and lightning/fire/ice/stone attack
particles. Enemy windup sheets still follow actual role/boss attack progress,
with concentrated energy, charge dust and release particles. Normal enemy
attacks now select imported attack frames too. Enemy support healing, pounces,
charges, heavy strikes, Draco shot/bite cycles and all adult Dragon affinities
keep their current creature bodies and committed directions. Combat rules,
cooldowns, mana, inputs, movement and damage/spawn timing are unchanged.

static/ability-animations.js is registered in the server static whitelist and
integrated into app.js/combat-environment.js. audio.js follows public cast IDs
to avoid duplicate or missed cast cues. Eight generated source atlases, exact
prompts, references, 48-ID coverage, hashes, 576-cell crop/mirror manifest,
PowerShell exporter and native preview are retained in art/ability-animations.
Gutter detection is necessary: equal fractional crops cut off source feet.
Fixed per-hero scale and foot baseline match the old sheets; ultimate props
remain larger. See WORKFLOW.md. preview.html is a local artwork viewer using
the actual renderer, with all 48 choices and eight directions; it makes no rooms.

Artwork/native exports were visually reviewed; Python/JavaScript syntax checks
passed. No automated gameplay tests or full multiplayer play-through were run.
Both disk checkpoints were copied and SHA256-matched to
data/backups/before-cast-animations-20261009-123304 before the authorized restart.
Python updates require a restart; static assets require clients to refresh.

## Ability icons and recharge rings — 2026-10-09

All 48 ability choices now have distinct literal pixel-art designs, including
an ice shard for Frost Lance and separate Druid summon icons. Individual
64×64 transparent icons and a complete 6×8 atlas/metadata live in static/sprites.
Lobby and Guild ability choices show the same icons as the equipped HUD.

The central ability bar now contains Light, Special and Ultimate, between the
two tools. It reuses the actual held-Attack button and retains its input listeners;
buttons persist across cooldown snapshots. Numeric ability countdowns are
replaced by a clockwise glowing red ring. The full ring becomes green when
cooldown readiness is confirmed, mana is sufficient and the hero can act.
Names, shortcut hints and mana costs remain. Active Druid summons show Active
with an empty ring and begin refilling after death. Low mana remains labeled.
Desktop HUD/world offsets and narrow-screen icon sizes accommodate the circles.

The private ability-slot snapshot adds fractional cooldownRemaining alongside
the existing rounded cooldownLeft. The client advances visuals between polls
but does not show Ready before server confirmation. Ability rules, cooldown
durations, costs and saves are unchanged. Python requires a restart for the
precise field; static changes require a browser refresh.

art/ability-icons retains eight built-in ImageGen sources, all exact prompts,
48 design descriptions, a style reference, deterministic PowerShell exporter,
crop/export manifest and catalog/cooldown previews. Artwork was visually
reviewed; no implementation tests or full live gameplay checks were run for
this request. See art/ability-icons/WORKFLOW.md for rebuilding.

Activated on port 8000 after copying and SHA256-checking both bed checkpoint
files to data/backups/before-ability-icons-20261009-115336. The identified old
server was stopped under the existing restart authorization; the current
project's server.py is now running in exec session 5719. Live rooms reset;
both disk checkpoints remain intact. Refresh the game page to load the icons.

## HUD tools, utilities and rune star — 2026-10-09

Tool 1 and Tool 2 now flank the bottom HUD's central ability/interaction space.
They show the equipped tool sprites and open the pouch when clicked. The three
utility slots sit directly under Help/Gather/Enemy; their click actions and 1/2/3
shortcuts still use the utility items. The movement pad is hidden for mouse/keyboard
devices through the hover/fine-pointer media query and remains on touch devices.
The center retains working Special/Ultimate controls and cooldown labels, ready
for the user's future ability sprites/animations; no new artwork was supplied.

The STAR puzzle rune and totem clue now draw matching five-point symbols in slate
and brass frames, replacing the old six-point sprite for that sigil. The fallback
text glyph is also a five-point star. Other rune artwork is unchanged.
Client syntax and existing held-attack, movement and equipment-comparison checks
passed. An isolated browser fixture using the actual HTML/render functions verified
1280x720 and 390x844 layouts without horizontal overflow, utility click dispatch,
tool-to-pouch behavior and both star drawings. Physical-phone testing remains open.
Refresh the HTTP game page; no server restart is required.

## Consolidated OneDrive backup — 2026-10-08

The user requested one complete backup and removal of game files that only take
up space. The verified backup is the sibling file
`../The-Gauntlet-Complete-Backup-2026-10-08.zip` (800,772,746 bytes; SHA256
bbb89c40483b81d9844bdf7ac8f91ad09c4ffe03a8980cec82f4f826d00b0925).
It contains the complete current project including original art, saved data and
Git database, plus the older laptop copy and release history. All archived entries
passed CRC and SHA256 checks. Current files have their ordinary layout inside
The-Gauntlet/. Historical versions share identical content through _Backup/INDEX.json
and _History/, with _Backup/RESTORE_HISTORY.py for restoration. Old release ZIP
wrappers were flattened; all member-file contents were retained. Python bytecode
caches were omitted as regenerable files. OneDrive cloud sync was not verified.

Cleanup completed after the user explicitly approved the exact deletion list.
Removed the older laptop copy, releases, original visual art folders, reference
screenshots, data/backups, bytecode caches, stale package manifest and old root ZIP.
All 2,262 removal candidates were checked against the backup's source hashes or
identified as disposable caches/generated metadata before deletion. Git storage
was compacted. Removed 2,338,372,728 bytes; after adding the single backup and Git
compaction, net space reduction is 1,538,468,847 bytes (about 1.54 GB).
See reports/CLEANUP_2026-10-08.json for the completed audit.

The current working game, all 215 static files, art/audio, both bed checkpoints
and active Git repository remain. Runtime file hashes matched before/after and
live HTTP checks passed for the page, client scripts, Druid sprite and Bard audio.
The server was not restarted. Visual authoring paths mentioned below and in
README.md now refer to archived material: extract The-Gauntlet/art/ from the
complete backup when editing original art. Historical versions can be restored
using the archive's _Backup/RESTORE_HISTORY.py.
The root legacy ZIP removal is a local Git working-tree deletion; cleanup changes
have not been committed or published to GitHub.

## Tactical update and publication — 2026-10-07

Publication completed and remote main/tree verified on2026-10-08:
https://github.com/Nael-Shakhsheer/The-Gauntlet/commit/92e417c5f4db837c80aa9d28153eb496e247031d
The code commit contains290 files, including the prior October6 archive, all147
runtime binary assets and142 source/document/test files. Every runtime asset SHA
matches the verified local build; private checkpoints are excluded. Earlier
publication-pending notes below are historical. The large ZIP upload was replaced
by a complete runnable source commit through the authenticated GitHub connector.
The local main branch now tracks origin/main. Its Git index was connected with
a mixed reset that preserved the working files, original art and both saves;
the previously published legacy ZIP was restored into the root. Large visual
authoring art and reference screenshots are locally ignored, while audio rebuild
sources remain tracked. Git publishing through the connector works; the native
Git credential store has no signed-in account, so future native pushes may need
sign-in. Public fetches work.

The user selected the reassessment's ability alternatives, description accuracy,
behavioral gear and signature bosses for implementation. `tactical_rules.py`
holds ability metadata, four build items, roots/bleed and equipment modifiers.
Druid Briar controls groups versus focused Thornshot; Wizard Arc chains versus
lower-DPS Frost control; Cleric Radiant splashes versus focused Sanctified Throw.
Rain of Arrows is a committed targeted area (380 cast range, 110 radius, .65s
delay), and Death Bloom actually bleeds for five seconds. Actual control honors
resistance, line of sight and attribution. Universal Ultimate cooldown remains15s.

Conductor, rescue cuirass, summoner staff and pursuit blade have explicit costs;
unique effects do not stack. Summon gear preserves health fraction without swap
healing. Pursuit requires actual Dash/Blink/Shadowstep movement and consumes one
follow-up. Rescue protection ends with the channel and has8s recharge. Shops
offer build tools, and pouch/shop comparisons show stats and gained/lost effects.
`equipment-comparison.js` is registered in the HTTP static whitelist. New item
icons reuse existing sprites with distinct borders. Concurrent Bfxr audio work
and adult Dragon/Draco art were preserved.

Great Minotaur charges collide with cover and create3s vulnerability (+35%).
Behemoth raises/shatters cover, Matriarch lays interruptible connected poison,
and Fire/Ice/Storm/Dark/Arcane Dragons each alter the spatial problem. Boss state
includes concise tactics and armor/true-form labels. Phase two is foreshadowed,
changes elemental tactics and starts with brief recovery. Cover stays bounded,
clear of standing actors, and friendly Rain cannot damage heroes.

157 Python tests passed, including23 tactical regressions. Node tests passed for
equipment comparison, audio, movement, held attack, personal chests, damage
flash and town sprites. Isolated port8001 browser verified descriptions, one-click
staff replacement and comparison gain/loss updates, desktop and390x844 wrapping,
with no console errors. The twelve-second light probe verifies roles in stationary
one/three-target fixtures, not human balance. See reports/TACTICAL_UPDATE_VALIDATION.md.

Activated on port8000 after hash-checking both bed checkpoint copies in
data/backups/before-tactical-20261007-223417/. The prior audio server was stopped
under the existing restart authorization and replaced by the current root's
server.py (exec session76303). Live equipment-comparison.js returned200. Live
rooms reset as expected; both disk saves remain intact. The verified playable
ZIP passed all157 Python tests after extraction into a fresh temporary folder.

GitHub publication is authorized for Nael-Shakhsheer/The-Gauntlet main. The old
branch still held the October6 ZIP when the user checked: a large ZIP connector
upload failed and no commit had been published. Use source plus all runtime assets
instead. Never claim completion until the remote head is verified. Public source
excludes data/checkpoints, release archives, large original visual art and reference
screenshots; full local ZIP preserves art and optionally saves. `package_game.py`
supports --runtime-only and excludes stale root PACKAGE_MANIFEST.json.

## Current-build reassessment — 2026-10-07

The planning chat reassessed the latest build; see
`reports/DESIGN_REASSESSMENT_2026-10-07.md`. It credits implemented targeting,
prediction, objectives, sprites, audio and independent run length. Limited early
Druid combat and 390x844 browser inspection used a separate in-memory port8001
server; production rooms/checkpoints were left intact. Portrait aspect stretching
is confirmed (960x540 canvas displayed about390x628). An isolated kit check also
confirmed an all-healing solo Healer can still start. Remaining proposals prioritize
display/kit correctness, ability tradeoffs, behavioral equipment, boss identities
and human full-run/phone tests. No gameplay changes; this does not authorize all
recommendations. Desktop/phone reference images are alongside the report.

## Retro sound effects — 2026-10-07

The first audio layer is implemented using actual Bfxr 1.0.4 synthesis code
(the user's "BXFR" was interpreted as Bfxr after checking its official site).
Twenty small local WAVs in `static/audio/` cover class Light attacks, Specials,
Ultimates, dash, damage, healing, down/revive, loot/curses, interactions, stage
and puzzle clears, ambush/dragon phase warnings and impacts. No soundtrack yet.
`static/audio.js` reads confirmed snapshots through `app.js`, suppresses repeated
effects and stale reconnect/background events, attenuates/pans remote sounds,
limits voices and uses a compressor. It changes no gameplay, save formats or
action protocol. Very brief events between polls can be missed.

Main-menu Sound settings and in-game Menu → Sound settings provide a 45% default
effects volume, mute and Test sound. Preferences persist per browser/site in
`gauntlet-audio`. Click/tap/key gestures create/resume audio; sounds before
activation are discarded. Failed audio cannot block the game. WAVs are served
by a restricted `/audio/` route and the new script is registered in `server.py`.
Refresh the HTTP page to load audio. No editor, npm packages or audio API key
is needed at runtime.

`art/audio/WORKFLOW.md`, `sounds.json`, `build-sounds.cjs`, source hashes, retained
Bfxr source and MIT/Apache license texts provide a portable rebuild/tuning path.
Run `node art/audio/build-sounds.cjs`; Node is only needed for authoring. The
20 mono 44.1kHz/16-bit files total about 400KB, with bounded peaks/short fades.

Validation: 134 Python regressions and existing held-input/client sprite checks
passed; the new Node audio checks cover activation, attack/damage/dash/status
feedback, deduplication, reconnect/background suppression, mute, bounded bursts
and all WAV headers/levels. JS syntax passed. Browser verified live sound-bank
loading/decoding (Sound ready), Test sound with no console errors, mute, keyboard
volume control, main and in-game entry points, and modal fit at 390×844. Screenshot:
`reports/audio-settings-phone.jpg`. Human headphone mix review and physical-phone
audio-policy testing remain; automated checks do not judge the sound aesthetically.

The server was restarted under the standing authorization after copying and
hash-checking both bed checkpoints to `data/backups/before-audio-20261007-200314/`.
It now runs on port8000 (exec session46002, PID28064 at activation). The earlier
server PID27224 and extra restart process35444 were stopped. In-memory rooms
reset; bed saves were preserved. Do not assume process IDs remain current later.

## Draco and adult Dragon sprites — 2026-10-07

The compact Dragon design from the first combat sprite pack now belongs to
Dracos, with dedicated `draco-idle` and `draco-windup-v1` PNG/JSON files. It is
copied exactly from the original game sheets. Existing Draco shot/bite behavior
and spawn/balance rules are preserved. The renderer maps shot preparation to
channel frames and bite preparation to heavy frames; movement returns to live
facing after recovery instead of retaining the previous attack direction.

Final Dragons now use a new fierce adult design with an elongated snarling head,
large ivory horns, heavy charcoal scales, broad leathery wings, four clawed legs
and a long barbed tail. `dragon-adult-idle-v2` and `dragon-adult-windup-v2` are
1044×1044 sheets with 116×116 cells and a 96×96 native artwork footprint, versus
Draco's 68×68 cells and 48×48 artwork. Both have eight directions, using exact
mirrors for eligible west-facing views. Idle, movement, attack and progressive
charge/breath/channel windup animations are imported. Elemental glows and the
final boss's phase-two growth remain.

Client base/windup renderers use the new adult filenames and a larger display
tile. Adult health bars/glows/shadows are sized for the larger body; the shared
damage-flash canvas is enlarged to fit the wings. No server rules or checkpoint
formats were changed by this art pass. Other concurrent Draco gameplay changes
in `game.py` and `enemy_roles.py` were preserved.

`art/dragon-lineage/` retains the compact references, adult concept, two generated
animation sources, exact prompts, crop manifest, builder, artwork inspection
inventory, animation gallery and field size comparison. The shared combat pack
exporter now accepts a separate manifest and configurable cell/footprint sizes,
while its original pack keeps the same defaults. Artwork was visually reviewed;
no implementation tests or live gameplay checks were run for this art pass.
Refresh the browser for the new art.

## Combat sprites and cursed item art — 2026-10-07

The current browser client renders seven enemy families (Minotaur, Troll,
Serpent, Wolf, Spider, Dragon and Chimera/`monster`) with new attack anticipation
sheets. Each has three progressive frames for charge/pounce, heavy attack and
aim/channel preparation in eight directions. West-facing directions are exact
mirrors of the corresponding east-facing source poses. Dragon and Chimera also
have new idle/movement/attack base sheets, replacing their procedural fallback
once loaded. Existing enemy identity, elemental glows and boss sizing remain.

Fresh room snapshots feed `GauntletCombatEnvironment.observe`; relative server
windup progress advances the body animation and holds the loaded pose until the
attack releases. Facing remains committed through release/charge. Boss recovery
triggers its attack release frames even without server `animationUntil`.
Cancellation without recovery/charge returns to normal animation. Visual state
is pruned with removed entities and reset between room/stage changes.

Four regional cover atlases provide crate/rock intact, damaged (half HP) and
destroyed debris states, hit shake and a short destruction burst. Terrain sprites
cover trap plates, warning seams and raised spikes, bubbling poison and ice
glimmers. Trap activation follows the authoritative warning/cooldown transition.
Animated warning runes, slams, meteor impacts and damaging pools stay clipped to
the actual hazard radius. Existing precise danger boundaries, aim lanes,
countdowns, progress bars and loading fallbacks remain. Arrow, rock, orb,
lightning and dagger flight sprites and hit/burst/slash/bleed/heal/aura/cast/dash
effects replace the former generic shapes when loaded.

Ashen Shackles (`sluggish`), Brittle Oath (`frail`) and Hollow Edge (`weakened`)
have individual transparent icons displayed beside the existing private curse
description in the affected player's pouch. This introduces no new curse or
equipment slot and preserves curse duration and privacy.

Pack: `art/combat-sprites/` retains 19 original asset requests, corrected sources,
all exact prompts, identity/palette references, manifest, export builder,
inspection inventory and preview galleries. Runtime PNG/JSON files are in
`static/sprites/`; client changes are in `static/combat-environment.js`,
`static/app.js` and `static/style.css`. Source and exported artwork were visually
reviewed and normalized with nearest-neighbor scaling/binary alpha. No gameplay
or implementation tests were run for this art pass. Refresh the HTTP browser
page; Python/server rules, startup dependencies and checkpoint data are unchanged.

## Planning review — 2026-10-07

The user designated a chat for developer critique and forward design. The current
review is saved in `reports/DESIGN_REVIEW_2026-10-07.md`, with a live visual reference
in `reports/design-review-live.jpg`. It combines limited browser inspection of the
early game with current source/report review; it is not a completed campaign,
human multiplayer balance test or physical-phone test. Priorities include combat
feedback/target control, viable and meaningful loadouts, encounter pacing, stacked
difficulty, behavioral equipment and boss identity. These are planning proposals,
not approval to implement the entire review. No gameplay code changed.

This file saves the project's working context for a new chat or another computer.
It is a summary of decisions and implementation, not a copy of the conversation.
Read `README.md` for the normal startup instructions. `GAME_DESIGN.md` contains
earlier planning and can disagree with the more recent decisions below.

## Continue on another computer

1. Copy and extract `The-Gauntlet-Laptop-2026-10-06.zip` on the laptop. The archive
   includes the source, instructions, and all imported sprites. The original
   sprite ZIP files on the home PC's D: drive are not required.
2. Install Python 3.10 or newer if needed. No third-party Python packages are
   required.
3. Open the extracted **The Gauntlet** folder as the coding workspace in Codex or
   ChatGPT Work. Start a new chat with the prompt below.
4. In a terminal in that folder, run `python server.py` (or `py server.py` on
   Windows if that is how Python is installed). Open `http://127.0.0.1:8000/`.

Suggested new-chat prompt:

> Read AGENTS.md, PROJECT_CONTEXT.md, and README.md. Continue working on The
> Gauntlet from its current state. Preserve the agreed game design and existing
> features. I prefer you to implement routine changes without repeatedly asking
> for approval. My next change is: [describe the change].

The archive is a snapshot; subsequent edits on one computer do not automatically
update the other. Copy an updated project back before continuing there. Active
rooms run in server memory, while inn checkpoints persist under data/checkpoints/.
Copy data/ too when transferring saved runs; combat progress since the inn is not saved.
Keybindings and browser room identity are stored in that browser's localStorage.

## Product and user preferences

- A real-time, top-down, cooperative pixel fantasy game for **1-4 players**.
  Friends join from phones or laptops using a room code without accounts or an
  installation. The game is not turn based.
- During play, the game fills the playing view. HP is a red bottom bar; mana is
  blue; three equipped utility slots appear on the right side of the bottom HUD.
- Combat, explorable towns, physical fork paths, and separate puzzle rooms form
  a run. Avoid replacing these with full-screen choice popups.
- Keep future destinations' encounter types and difficulty hidden. Boss and town
  counters and raw phase titles such as STAGE_EXIT should not appear in the HUD.
- Sprites should resemble the supplied directional pixel art, with distinct
  elemental glows. Town characters are smaller so they fit the buildings.
- The user wants implementation to proceed autonomously for ordinary changes.
  Do not ask for approval at every turn.

## Architecture and file map

| File | Responsibility |
| --- | --- |
| `game.py` | Authoritative GameWorld, classes/abilities, actions, movement, combat, enemies, difficulty, stage schedules, routes, towns, economy, inventories, checkpoints |
| `puzzles.py` | Puzzle creation and private per-player room/clue views |
| `server.py` | Standard-library HTTP server, room/join/action/state APIs, static assets, simulation loop |
| `static/app.js` | Browser input, polling, interpolated canvas rendering, sprite animation, HUD and menus |
| `static/index.html` | Client page structure |
| `static/style.css` | Pixel fantasy UI, responsive playing view, menus and overlays |
| `progression.py` / `static/progression.js` | Hunter story, first-village welcome/tutorial, stat training, upstairs inn rooms and bed checkpoints |
| `static/town-sprites.js` | Supplied service NPC, villager and floating chest animation renderer |
| `static/sprites/` | Imported Knight, Wizard, Serpent Guard, Minotaur and Cave Troll PNG sheets with JSON metadata |
| `README.md` | Running and playing the game |
| `GAME_DESIGN.md` | Earlier broader design notes; some sections are outdated |

The server ticks at approximately 20 Hz. The browser polls state at approximately
10 Hz and renders independently using requestAnimationFrame and interpolation.
The arena coordinate system is 960 x 540. No framework or package install is
currently needed.

HTTP APIs: `POST /api/rooms`, `POST /api/join`, `POST /api/action`, and
`GET /api/state?room=...&player=...`. Static files are served by the same server.
Sprite PNG/JSON requests are restricted to the `static/sprites` directory.

## Heroes and controls

Only one player can choose each class in a party. There are now **eight** classes
(the initial seven gained a separate Healer).

| Hero | Role | Base HP |
| --- | --- | --- |
| Knight | Melee tank | 150 |
| Wizard | Ranged arcane caster with support options | 100 |
| Archer | Fast ranged piercing attacks | 105 |
| Cleric | Splash-potion support | 85 |
| Rogue | Fast bleed damage and temporary invisibility | 80 |
| Druid | Elemental summoner with projectile Light attacks | 80 |
| Bard | Team damage and movement buffs | 75 |
| Healer | Strong healing and rapid revives, low damage | 110 |

Each class has two Light, two Special and two Ultimate choices in
`ABILITY_SETS`. Equip one from each category, for three abilities total. The
source is authoritative for ability names, powers, mana costs and cooldowns.

- Move with WASD by default; arrows and a touch pad also work.
- Left click / touch Light button: Light attack. Q: Special. X: Ultimate.
  Main-menu Controls & keybindings can remap relevant actions.
- Space: directional dash, five-second recharge.
- E: interact. Hold E near a downed teammate to revive in combat.
- 1, 2, 3 or numpad 1, 2, 3: equipped utilities. Clicking the slots also works.
  Gameplay hotkeys should not fire while typing in chat or another input.
- Light, Special and dash cooldowns refresh when entering a new stage. Summons
  are removed. Every hero's equipped Ultimate starts on its full cooldown,
  including the first combat stage and combat following towns or puzzles.
  New waves do not restart the Ultimate timer.
- Built-in party text chat supports puzzle coordination.

### Druid summons

Both Light choices, Briar Bolt and Thornshot, launch projectiles. Equip one
Special and one Ultimate from the following choices, using the normal loadout:

| Category | Summon | HP | Attack | Recharge after death |
| --- | --- | --- | --- | --- |
| Special | Lightning Bird | 55 | Ranged lightning projectile | 8 seconds |
| Special | Fire Wolf | 90 | Melee | 8 seconds |
| Ultimate | Ice Bear | 180 | Melee | 15 seconds |
| Ultimate | Nature Rock Golem | 240 | Melee | 15 seconds |

Summons chase and attack their nearest enemy independently. Enemy melee and
projectiles can damage and kill them. Their ability is locked while alive;
recharge begins only at death, and the HUD shows Alive or the remaining timer.
One equipped Special summon and one equipped Ultimate summon can coexist.
Special summon hits deal 90% of the equipped Light attack's damage, rounded to
an integer; both Ultimate summons hit for exactly twice that Light damage.
Damage uses the owner's equipment, active damage buffs and curse at cast time.
Summons have no timed expiry. Survivors keep their HP between waves within a
stage. At the next stage, all summons disappear. Special becomes ready again,
and Ultimate begins its full 15-second cooldown. This replaces any unfinished
death recharge. Players must cast them again. Wave countdowns and new waves do
not reset them.
Leaving the room, changing class, checkpoint recovery or a full-party wipe
dismisses them. They cannot continue the run after every hero falls.
Each has distinct animated canvas art, a friendly name, an HP bar, and damage
flash support. The former timed spirit-wolf damage buff has been replaced.

## Combat, difficulty and run progression

- At the start of a combat stage, players form a line near the bottom and enemies
  begin near the top with space between them.
- Clearing a wave starts a **three-second countdown** at the top. Retain the
  current scenery and player positions; the next enemies run in from an edge.
- Ordinary wave base counts are currently 1-2 / 3-5 / 5-8 / 8-12 for one / two /
  three / four players. Stages have two waves for one or two players, three for
  three or four. Party size also scales enemy HP, damage, speed, aggression and
  projectile speed. Hidden route modifiers can change these base results.
- Enemy families include Serpent Guard, Minotaur, Wolf, Cave Spider and Cave
  Troll. Mobs receive combat kits drawn from the eight hero classes, including
  ranged and support attacks. They can move while attacking; squadrons flank and
  try to surround players. Minotaurs receive a 30% speed boost.
- Enemy projectiles aim once and then travel straight so they can be dodged.
  Heroes and enemies have attack animation/effects, including projectiles.
- A short attack-range indicator surrounds the local hero during combat.
- Downed players have an eight-second revive window. The Healer revives faster.
  Enemies become more aggressive around knockdowns. A full-party wipe recovers
  at the latest inn checkpoint, loses 40% of shared Runes, and retains items.
- Gradual added difficulty starts at **stage 8**. `_stage_ramp` uses
  `0.62 + 0.38 * (stage - 1) / 24`, then adds `0.08 + 0.04 * (stage - 8)` for
  stage 8 onward, clamped to stages 1-25. Existing stat/cadence calculations use
  that ramp. This latest tuning did not add extra waves or extra enemies.
- Large bosses occur at **stages 8, 16 and 25**. The last is always a randomized
  dragon. Two to four miniboss stages are distributed through each boss interval.
  Miniboss encounters use an empowered enemy or a larger squadron.
- First-boss pool: Serpent Matriarch, Labyrinth Minotaur King, Ancient Stone
  Behemoth, Chimera, Great Wolf Guardian. Dragon types: Fire, Ice, Dark Magic,
  Arcane and Storm.
- One 8% roll per new run determines whether an assassination ambush is scheduled
  on an eligible combat stage. It can occur at most once even after checkpoint
  recovery. Stronger enemies enter from all four sides, scaled to party size.
- Victory celebrates the final dragon defeat; defeat uses a dark presentation.

## Physical exploration and routes

- Stage rewards use a physical chest in the arena. Approach and press E; announce
  obtained loot to the player. There is no separate "leave unopened" choice.
- After combat and any treasure, prompt the party to gather at the top opening.
  This transitions into a **separate fork area**.
- Follow the left or right trail all the way to its screen edge. Everyone must
  reach an exit; majority wins a split vote and the host breaks a tie. Moving
  away cancels a player's vote. The server constrains movement to the trails.
- Fork signs show actual **location names**, not encounter spoilers. The sign
  was moved upward onto grass to avoid covering the path.
- A hidden pressure counter changes with the chosen path. Its run modifier
  affects **wave size OR enemy HP**, never both together. A rare, one-use
  Pathfinder's Lens provides a clear indication of the easier route.

## Towns, items and checkpoints

- Runs schedule 2-4 towns, weighted 15% / 70% / 15% for two / three / four. Counts
  are hidden. Village names: Mossgate, Bellweather, Hearthrest, Silverbrook and
  Rookhaven.
- Each village shuffles building locations and appearance. Players walk around
  outside, then enter individual building interiors with E at the door.
- Innkeeper, Merchant, Alchemist and Guildmaster are inside the Inn, Store,
  Alchemy Lab and Guild. All six buildings, including the two decorative houses,
  share the shuffled location and appearance system on every town visit.
  Approach the NPC and press E. There are additional decorative houses.
- The Guildmaster opens a hero picker and allows **one class change per player
  per run**. The current hero and heroes already taken by teammates are disabled.
  Selecting a hero previews that hero's six class-specific skills with the two
  options in each category shuffled and one random default choice per category.
  Each hero currently has exactly six skills, so randomization changes their
  order/default loadout rather than drawing new skills or borrowing other classes.
  Choose one Light, one Special and one Ultimate, then confirm to spend the change.
  Back out, Escape, or return to the hero list without spending it. Previewing and
  polling do not change the live class/loadout. The server validates location,
  class availability, the loadout and the per-player limit atomically.
- A class change retains carried/equipped items, mana, curses and HP percentage,
  updates base HP and class-specific merchant stock, and resets ability/dash
  cooldowns. The class, loadout and used allowance survive later towns and wipes.
  Village entry and checkpoint recovery spawn below the lower building row; the
  main path runs between buildings so the new sixth building does not block it.
- Upstairs beds in unlocked inn rooms restore the party and record the checkpoint;
  innkeepers teach and offer stat training. Merchant stock is
  class-specific (e.g. Wizard wands rather than Knight swords). Alchemist has
  potion/restoration interaction. There is no town-to-town travel menu.
- To leave, every player gathers at the outside gate and presses E to vote.
  Moving away cancels that player's readiness.
- Currency is **Runes**, shared by the party, earned through enemies, chests and
  rewards. Utilities include healing, mana, temporary buffs, special arrows and
  route hints. Loot rarities range from Common through Legendary.
- Equipment: three utility slots, two tool slots (weapon/armor), ten carried
  pouch items. Equip/unequip anywhere; selling requires a merchant. Equipment
  overlays change the hero's appearance and affect combat.
- Pouch opens as a bottom-center bar. **Expand** reveals item descriptions and
  **Collapse** returns to the compact view.
- Curses occupy their own hidden sixth pouch slot; they cannot be sold or
  cleansed and must expire naturally after five completed combat/puzzle stages.
  Towns do not reduce the timer. Current curses slow movement, reduce outgoing
  damage, or increase incoming damage. Chest curse chance is 12% when uncursed.

## Puzzles

- Schedule 1-3 puzzles per run, weighted 65% / 30% / 5%. One is guaranteed;
  a third is rare.
- Players are separated into private rooms containing scattered rune sigils and
  a randomly placed clue totem. Clues require communication across the party.
  Rooms and completion adjust to party size, including solo play.
- Players must stand at their matching rune; all must be correct to proceed.
  Totem/rune use matching clear sigils and colors when the clue is revealed.
- Wrong answers increase hidden run strain slightly: 0.5% per first two mistakes,
  1% per next two, 2% each from the fifth, capped at 15%. It persists across wipes.
- Intro/clue dialogue disappears after **three seconds** and can be reread with E.
  Standing on a rune closes the dialogue and does not create a warning popup.
  Wrong-rune penalties and party chat feedback remain. Totem proximity is now
  physical proximity only; reading a clue remembers it without treating every
  later location as the totem, so E on a rune cannot reopen the clue panel.

## Art and recent changes

- Sprite workflow saved on 2026-10-06 in `SPRITE_WORKFLOW.md`. The user approved
  a generated Cave Troll concept and explicitly requested horizontal mirrors
  for eligible directions. Generate South, Southeast, East, Northeast and
  North; mirror East to West, Southeast to Southwest and Northeast to
  Northwest. Mirroring swaps weapon hands and asymmetric details.
- `art/samples/cave-troll-spritesheet-v1.png` is a 612x612 animation sample
  with 68px cells and idle/walk/attack columns 0-2/3-5/6-8. Its prompts,
  sources, metadata and relative-path rebuild script are retained beside it.
  Diagonal poses are approximate. Cave Troll was subsequently imported into
  the actual game; see the latest implementation notes below. Follow the
  saved workflow for future art.
- `art/exports/Cave-Troll-Sprite-Import-v1.zip` packages this approved sheet,
  metadata, import instructions, a Python importer, and the saved creation
  sources/workflow. The importer backs up files, registers Troll, uses the
  3/3/3 frame ranges, and maps enemy kind `troll` to it. ZIP integrity,
  checksums, import/backups/idempotence and JavaScript syntax passed using an
  isolated extracted copy. The actual game was not modified by packaging.
  `art/exports/build_cave_troll_package.py` recreates the archive.
- `art/exports/Cave-Spider-Sprite-Import-v1.zip` is the next completed art
  package. It includes a 612x612 PNG, 68px cell metadata, Python importer,
  import instructions and retained prompts/source art under `art/cave-spider/`.
  It uses five generated directions and three exact horizontal mirrors, with
  idle/scuttle/bite columns 0-2/3-5/6-8. The importer preserves existing Troll
  entries and supports the original renderer too. Exact mirror pixels,
  distinct frames, ZIP/checksums, isolated imports/backups/idempotence,
  no-write checks and JavaScript syntax passed. Spider is not imported into
  the actual game or checked in live gameplay. Its `WORKFLOW.md` and
  `art/exports/build_cave_spider_package.py` retain the repeatable process.

- Heroes and enemies briefly take on a red hue when damaged. The client keeps
  per-entity damage tracks, flashes for 220ms and fades during the last 100ms.
  A reusable isolated canvas applies the tint only to the character's opaque
  pixels, including imported sprites and hero equipment; elemental glows,
  scenery, name labels and HP bars retain their normal colors.
- `game.py` reports a `damageTaken` event counter for each hero/enemy through
  the shared damage methods, including projectile, melee, area and bleed hits.
  This catches a hit even if healing occurs before the next state poll. The
  client also detects HP decreases for a server process started before this
  update, so a browser refresh can enable the effect without losing active rooms.
  Restarting an older server process enables the counters. Healing, initial spawning and
  a class change's base-HP adjustment do not start a flash.
- `CHARACTER_ROSTER.md` lists the currently implemented heroes, enemy families,
  bosses, dragon types, village NPCs and generated enemy variants.
- Imported directional sprites: Knight, Wizard, Serpent Guard, Minotaur. The
  latest completed change was the Minotaur sprite import from the supplied
  `16-bit_pixel_art_aggress-Idle-spritesheet.zip`.
- All are 9x9 sheets. Row zero provides facing poses; remaining rows correspond
  to South, Southeast, East, Northeast, North, Northwest, West and Southwest.
  Knight/Serpent/Minotaur use 68px cells; Wizard uses 64px cells.
- In `static/app.js`, `heroSprites` and `drawImportedHero` handle imported sheets.
  Minotaur uses columns 0-2 for idle, 3-5 for movement, 6-8 for attack. Other
  sheets have their own pose selections. Imported enemies retain elemental glows
  without hero equipment overlays; bosses/minibosses are scaled larger.
- Enemy affinities Fire, Ice, Dark, Arcane, Poison, Storm and Nature add colored
  glows around the base sprite rather than replacing it with unrelated art.
- Performance work separated rendering from polling, interpolated positions,
  cached scenery/glows, and reduced repeated DOM work. Stage scenery stays
  stable between waves. Town sprites use a smaller scale than combat sprites.
- Recent changes also removed the raw phase-title badge, moved the fork sign,
  and added the gentle difficulty ramp after stage 7.

## Known limits and unfinished requirements

- **No public deployment yet.** Localhost works on the host computer. Same-LAN
  devices use the host's LAN IP; a public link requires a hosting decision and
  deployment. The original multiplayer challenge wanted a public link.
- Runs without an upstairs bed checkpoint, and progress beyond the saved village,
  are lost on restart. Bed checkpoints persist locally under `data/checkpoints/`.
- All eight heroes, five enemy families, four Druid summons, town NPCs, villagers
  and the floating chest have supplied art. Remaining enemy families use canvas art.
- Guild class switching is implemented. `tests/test_guild.py` covers town layout,
  canceling, class-specific randomization, invalid requests, teammate conflicts,
  retained equipment, and checkpoint/once-per-run behavior. Run with
  `python -B -m unittest discover -s tests -v`.
- Balance is evolving from the user's play feedback. Recent syntax checks and
  sprite HTTP checks passed, but comprehensive multiplayer/mobile playtesting
  has not been performed. Do not claim gameplay was fully verified.
- At this handoff, Git exists locally but has no commits and no remote. Nothing
  has been uploaded or published for the laptop transfer.

Latest completed gameplay change: Druid projectile Lights and four independent
elemental summons, requested on 2026-10-06. `tests/test_druid.py` covers projectile
impact, targeting, summon deaths, independent locks, exact recharge durations,
stage transitions, rewards, party wipes, leaving and Guild class changes.
Eighteen Python regression tests and the JavaScript syntax check passed.
Isolated browser checks verified all four summon visuals, the Druid loadout,
and independent Alive locks; the browser reported no errors. Client canvas
checks also cover all four summon renderers and their damage flashes.
`tests/test_damage_flash.cjs` uses Node with @napi-rs/canvas to
verify damage tracking, fade timing, actual tint pixels, transparency, healing
and class-change behavior. Browser checks used an isolated damage fixture with
imported and drawn heroes/enemies; no fixture behavior is in the game. The
earlier Guild browser checks covered cancellation, skill selection, confirmation,
second-change lockout and a 390px phone layout.

Follow-up on 2026-10-06: removed rune warning popups and corrected the remembered
totem proximity flag. Standing on a rune closes any open puzzle dialogue;
E can reread the clue only at the totem. Wrong-rune penalties and chat remain.
`tests/test_puzzle_feedback.py` covers the penalty without a popup, E on a wrong
rune, remembered clues away from the totem, and the shared 58px interaction radius.
All 22 Python tests and JavaScript syntax checks passed; a client function check
verified rune overlay suppression and totem rereading. Restarted the actual
server at port 8000 and verified the new Druid ability list plus spawning Fire
Wolf and Nature Rock Golem in normal combat. Existing rooms were cleared by the
restart; the Druid changes and damage event counters are now active.

Follow-up on 2026-10-06: summons now reset at each new stage, together
with their ability locks and death recharge timers. New waves preserve live
summons, their health and ongoing death recharge. The updated Druid regression
checks exercise actual route-to-stage progression and next-wave spawning.
All 23 Python tests passed. The server was restarted to activate this change.

Latest balance follow-up on 2026-10-06: Druid Special summon damage is now 90%
of the equipped Light's hit damage; both Ultimate summons deal 200%. Every
hero's equipped Ultimate begins each combat stage on its full normal cooldown.
Combat after towns or puzzles applies the opening cooldown, while subsequent
waves preserve it. `tests/test_stage_cooldowns.py` covers both Ultimate choices
for all eight heroes, the first stage, route progression, waves, towns and
puzzles. Druid tests cover both Light choices with equipment, buffs and curses.
All 27 Python regression tests passed.
Restarted the live server on port 8000 and checked all 16 Ultimate choices via
the HTTP API: opening casts were rejected on cooldown, Light/Special remained
ready, and the updated Druid damage multipliers were present. Test rooms were
removed after verification.


## Latest implementation — party tools, durable inns, Cave Troll and held attacks

The user selected roadmap items 4, 5, 12 and 13. All thirteen critique points
are saved in IMPROVEMENT_BACKLOG.md; other items remain deferred.

- `telemetry.py` measures each combat stage, preserving stats between waves:
  actual hero/summon damage (overkill capped), hero/summon HP lost, armor/ward
  prevention, summon survival/uptime/spawns/deaths, elapsed stage time, party
  size, Ultimate casts and whether the stage ended before its opening recharge.
  Bird projectiles retain summon credit after their caster dies. Bleed credits
  its source hero. Rejoining participants are added to the report.
- `run_storage.py` writes atomic versioned inn checkpoints and local append-only
  `data/balance.jsonl`. Production `WORLD` uses the project data folder and a
  15-second disconnect timeout. Plain `GameWorld()` remains isolated for tests.
  Town entry and town transactions save; process restart restores that town,
  player identities, classes/loadouts, items, Guild usage, Runes and schedules.
  Transient summons/buffs/movement are reset. Same-origin browser localStorage
  retains identity; Main menu disconnects and Continue saved run reconnects.
  Pre-inn runs and post-inn combat progress do not survive a server restart.
- Offline heroes do not take enemy aggro or block exits, forks, chests, town
  votes, puzzle answers, or party wipe detection. Stale input stops after two
  seconds; the client refreshes held input every half second. Host transfers
  to an active participant. All-offline rooms pause; reconnect shifts monotonic
  combat deadlines forward by paused duration. Offline heroes remain reserved
  for their returning players, including their chosen classes.
- Cooperative totems form a clue cycle among active players. A player's clue
  describes the next player's rune. Private views never expose whether their
  own multiplayer rune is correct; the whole group answer is evaluated together.
  A new incorrect full arrangement incurs one penalty rather than repeated
  waiting penalties. Solo retains its own clue and feedback. Disconnections
  reassign the cycle; reconnect adds a chamber if the stage began while absent.
- `static/coordination.js` contains teammate HP/rescue HUD, five-second Help/
  Gather/targeted Enemy pings, Share clue, optional five-page guide, resumable
  menu flow and on-demand Run stats/JSON download. `GET /api/stats` keeps reports
  out of the ten-per-second state payload. Phone controls have 44px minimum
  targets and split skill names/statuses; underlying canvas aspect/camera
  behavior is unchanged and remains a future mobile improvement.
- Cave Troll assets imported from `art/exports/Cave-Troll-Sprite-Import-v1.zip`
  after checksum verification. `static/sprites/troll-idle.png/json` use 68px
  cells, eight directions, idle columns 0–2, walk 3–5, attack 6–8. All enemy
  kind `troll` variants use them, including the Stone Behemoth. Existing glows,
  scale, damage tint and fallback remain; Druid golems keep their own art.
- Hold left click on the arena or hold Attack to repeat the **equipped** Light
  with its actual cooldown/range/effects. Pointer release/cancel, focus loss,
  hidden tabs and dialogs stop it. Touch movement and attack are independent.
  `_attack` now calls the equipped Light through `_cast_ability`, replacing the
  unused generic attack path that had different damage and cooldown behavior.
  Rising attack input fires immediately so brief taps cannot fall between ticks.

Validation: 39 Python tests pass, JavaScript syntax checks pass, both Node client
checks pass (held input transitions and all 72 Troll animation cells, plus canvas
red-flash/summon rendering). Isolated port-8001 browser checks covered teammate
health/rescue/offline states, Troll rendering, 390×844 and 844×390 HUD geometry,
quick Help pings, teammate clue display/sharing, guide pages, Run stats, and
Continue saved run. Atomic save/load and reconnect timing have backend tests.

`tools/balance_probe.py` produces `reports/BALANCE_REPORT.md` and raw JSON for
90 deterministic bot simulations: stages 1/8, all eight solo heroes, parties
of 2/3/4 with Druid versus Wizard, and both Druid summon loadouts solo. Bots
approach and cast; they do not dodge, revive, equip items or act like humans.
Use the methodology in the report before drawing balance conclusions. No
additional damage/cooldown nerf was applied. Human-run telemetry is now available.

Activated the update on the live port-8000 server. HTTP smoke checks verified held Thornshot repeats and stops on release, the on-demand stats API responds, and Troll assets plus coordination.js are served. The old pre-persistence rooms were cleared by this activation restart. New inn checkpoints now protect future restarts. Temporary preview server stopped; reports/gameplay-preview.png is a labelled QA-fixture screenshot showing the imported Troll and updated HUD.


## 2026-10-06: overall stats, varied villages, progression and Cave Spider

Latest user request implemented:
- `/api/stats` and Menu → Run stats now return/display overall totals per player:
  damageDealt, damageTaken, revives, deaths, kills, plus name/class labels.
  `room.runStats` accumulates across waves, stages and checkpoint retries. Damage
  counts actual HP lost, includes summon damage, excludes summon HP from hero
  damage taken, and credits the finishing attacker with each kill (including
  delayed summon projectiles). Deaths count falling or party wipe once per life;
  downed heroes rescued in time are not deaths. All revive methods count each
  rescued ally. Inn disk snapshots include totals. Legacy saves without runStats
  start counters after the update. Stage balance telemetry remains local for
  the previously requested contribution analysis; it is no longer the stats UI.
- `_present_routes` saves one 50% fork decision for each non-town transition.
  `_tick_travel` enters a fork or advances directly using `_advance_stage`.
  Scheduled towns arrive directly. The offered fork routes are combat regions.
- `town_layout.py` generates scattered, staggered, row and column house layouts
  with shuffled services/roofs. Grid searches connect the gate/crossroads to all
  doors around house footprints. Roads, trees and 12 non-interactable villagers
  are serialized as townPaths/townDecor/townVillagers. New towns vary spatially;
  inn snapshots preserve scenery on resume. Legacy town saves regenerate roads
  from their saved house positions. Villagers are scenery and never NPC services.
- `_spawn_wave` tunes fresh enemies after selecting their encounter. Every town
  visit adds +25% HP, +20% damage, +10% speed, +12% attack frequency relative to
  untuned values. Miniboss encounters (empowered and squadron) additionally use
  ×1.15 HP, ×1.12 damage/speed, ×1.25 attack frequency. Ranged elites close to 88%
  of their normal range. Town pressure applies on all following waves/stages;
  checkpoint resumes preserve visit count and do not count another town visit.
- Pouch Tool 1/2 and Utility 1/2/3 directly swap incoming and equipped items,
  including a full five-item pouch and different tool types. Displaced items
  return to the pouch. Client swap buttons remain enabled and wrap on phones.
- Supplied Cave-Spider-Sprite-Import-v1.zip assets were checksum verified and
  imported into static/sprites/spider-idle.png/json. Spider uses 68px cells in
  a 612px sheet: eight compass rows, idle 0–2, scuttle 3–5, bite 6–8. All enemy
  kind spider variants use it with existing glows/scaling/damage tint/fallback.
- Existing balance-probe reports are historical baselines before this update.

Validation: 49 Python tests pass. JavaScript syntax, held-input checks, all 144
Troll/Spider directional animation cells, and canvas damage-flash/summon checks
pass. Browser testing on isolated port 8001 verified the generated town, villagers,
full-pouch armor-for-weapon and utility swaps, overall stats, 390×844 stats/pouch
layout without horizontal overflow, and the imported Spider in-game. No browser
console errors were observed. Preview screenshots under reports/ are QA fixtures:
town-update-preview.png, run-stats-preview.png, spider-update-preview.png.

Live activation: port 8000 restarted with this update. HTTP smoke checks confirm
client/Spider assets and the five-counter stats endpoint. The existing UTAE4 inn
checkpoint restores with its saved houses plus generated connected roads and
12 villagers. Existing legacy saves start the new totals at zero. Refresh the
client to load the updated scripts. Temporary QA server stopped after testing.

## 2026-10-06: Wolf, Druid and four summon sprite package

Created `art/exports/Wolf-Druid-Summons-Sprite-Import-v1.zip` with six transparent
612x612 sheets and JSON metadata: Wolf, Druid, Lightning Bird, Fire Wolf, Ice Bear
and Nature Rock Golem. Each uses the established 68px cells, eight compass
directions, idle 0–2, movement 3–5 and attack 6–8. West/Northwest/Southwest are
exact mirrors. Five-direction generation sources, exact prompts, measured crop
bounds, `build-sheets.ps1`, labelled preview and workflow are retained under
`art/wolf-druid-pack/`. Lightning Bird uses measured columns to keep extended
wings inside their own frames. Other sources use measured vertical row bands.

The ZIP includes `import_wolf_druid.py`, `IMPORT.md`, all six PNG/JSON pairs,
source/rebuild files and checksums. The importer registers all six sheets,
maps wolf enemies, enables their 3/3/3 animation ranges, and hooks summon art
inside damage tint before procedural flipping. It preserves the affinity ring,
shadow, health/name labels and existing renderer registrations. Summon sizes:
Golem 1.5x, Bear 1.35x, Fire Wolf 1.15x, Bird 1x. Druid has a general staff-cast
sequence for Light/Special/Ultimate. The package contains no gameplay changes.

This package is prepared for handoff; these six sheets have not been installed
in `static/sprites/` by this task. Sheets were visually inspected and their
export geometry, transparency, frame variation, mirrored pixels and ZIP hashes
checked. No live gameplay review or importer execution was performed for this
batch. Rebuild the ZIP with `python art/exports/build_wolf_druid_package.py`.

## 2026-10-06: Archer, Cleric, Rogue, Bard and Healer sprite package

Created `art/exports/Archer-Cleric-Rogue-Bard-Healer-Sprite-Import-v1.zip` for
the five remaining heroes. Each sheet is transparent 612x612 with 68px cells,
eight directions, idle 0–2, movement 3–5 and general attack/cast 6–8. West,
Northwest and Southwest are exact mirrors. Archer uses green ranger gear and
bow/quiver; Cleric ivory/gold robes and holy flask; Rogue charcoal/violet hood
and twin daggers; Bard rose/burgundy gear and lute; Healer ivory/teal robes and
mercy rod. General attack/cast poses serve Light/Special/Ultimate, while the
game continues to draw the actual projectiles, support effects and invisibility.

`art/hero-party-pack/` retains five original source sheets, exact prompts,
measured row/column crop bounds, final sheets and metadata, animation preview,
`ASSET_REVIEW.json`, `WORKFLOW.md` and `build-sheets.ps1`. Column adjustments
keep Bard notes, Rogue slashes and one Cleric cast from crossing crop boundaries.
The ZIP includes these files, five ready-to-import PNG/JSON pairs, checksums,
`import_heroes.py` and `IMPORT.md`. The importer extends the loader and two
3/3/3 animation lists; it preserves existing sprite registrations and can be
used before or after the Wolf/Druid pack in the supported renderer. Existing
files are backed up and unchanged repeated imports do not write files again.

All five sheets were visually inspected. Export grids, padding, alpha, distinct
frames and exact mirrors passed asset checks; ZIP content hashes were checked.
These sheets are prepared for import and have not been installed into the game
by this task. Importer execution and live gameplay were not evaluated. No
gameplay/server files changed. Rebuild the ZIP with
`python art/exports/build_hero_party_package.py`.


## 2026-10-06: Campaign difficulty, companion AI, boss rework and sprite imports

Implemented the user's campaign/combat request and both subsequent sprite ZIPs.
Current runtime imports supersede the earlier "prepared, not installed" entries:
all eight hero sprites are active, plus Wolf and LightningBird/FireWolf/IceBear/
NatureGolem. Copied static PNG/JSON pairs from the supplied packages and checked
SHA256 sums; did not execute their import scripts. New sheets use eight facing
rows and 3 idle / 3 walk / 3 attack frames. Hero effects, gear and damage tints
remain in the existing canvas renderer; summon rings and HP bars are retained.

`companion_ai.py` controls an optional normal player flagged `bot=True`:
random available hero/loadout at run start, shared party scaling, nearest-enemy
combat, normal mana/cooldown costs, hazards, reviving, loot/equipment, travel,
town votes and cooperative puzzles. A human must Share clue for its rune;
its inscription appears in a persistent HUD as well as the puzzle panel.
Bots do not inherit host, time out or keep an all-human-offline run simulating.
They reset fork navigation every visit and persist in inn checkpoints.

Host-only lobby runOptions chooses Easy (20 stages, .9), Medium (25, 1.25),
Hard (30, 1.6). Medium defaults for old checkpoints. Difficulty/totalStages
persist in checkpoint and checkpointResume metadata. All event schedules adapt
to totalStages; final dragon is last. Enemy HP/damage added factor is
1.15 * mode_multiplier * (1+.05*(stage-1)), composed once per spawn with existing
stage/party/town/elite factors. Mode attack frequency is sqrt(multiplier).
Solo normal waves: stage13 2–3,17 3–4,20+5; party increases enemy count.
Stages13–16 three waves 75%,17+ always three. Boss waves keep boss compositions.

All Ultimates now use 15s opening AND recast cooldown. Legacy mana costs are
captured before normalization (no unintended cost reduction). Druid summon
abilities retain alive locks and 8s/15s death recharge. Ten pouch slots,
compact scrollable grid, direct tool/utility swaps; phone buttons44px.
Chest rolls item/runes/heal55/25/20 after existing12% curse chance; no new items
were invented. Replaced stage exit text with an arrow.

`boss_ai.py` adds warning circles, ticking pools, slams, large shot fans and
fixed-direction charges with swept collisions. Minotaur King and Stone Behemoth
movement2.5x. Single empowered minibosses also use special attacks. Dragon phase2
revives at1.6x first maxHP,1.35x damage,1.2x speed,1.25x attack frequency and larger
art, with party meteor strikes; final kill/victory only after second phase.
Shield Bash boss stun.25s, single miniboss.55s, normal1.5s. Normal pursuit goals
update every.6–1s, bosses.75s; removed mirrored strafing. Enemy projectiles steer
for1.1s at bounded.65rad/s (boss.35); no instantaneous tracking. Offline pause
shifts all new attack/hazard/homing clocks.

Validation:70 Python regression tests passed, Node syntax/held-input checks,
936 directional imported animation-cell checks, canvas damage/summon alpha
checks. Isolated HTTP8001 preview verified lobby difficulty/NPC selection,
normal Fire Wolf cast+Alive lock, all four summons, all five newly imported
heroes, dragon phase2/warnings, full10-item tool+utility swapping and390px pouch
geometry with no horizontal overflow. Screenshots in reports/:
hero-party-update-preview.png, summons-update-preview.png,
campaign-update-preview.png, campaign-pouch-phone.png. Preview uses disposable
fixtures; production contains no QA routes. Old balance reports are historical,
not rerun under this tuning. Human balance/long-run playtesting remains useful.
No skill-tree code was implemented: user asked only for a proposal in chat.

Live activation: restarted server.py on HTTP8000; all client files and22 new
sprite PNG/JSON responses match disk. Existing inn checkpoints preserved.
Canvas verification also rendered all11 new PNGs and tested actual imported
summon damage tints with alpha preserved. Isolated preview server/tab closed;
viewport override reset. Refresh the live browser to load updated static files.

## 2026-10-06: Town characters and floating treasure chest package

Prepared `art/exports/Town-NPCs-Villagers-Floating-Chest-Sprite-Import-v1.zip`:
Merchant, Guildmaster, Alchemist, Innkeeper, eight related villager designs,
and a floating Treasure Chest. Guildmaster has regal silver/gold armor and a
purple cape with his helmet off. Innkeeper has an ordinary villager build,
ginger moustache, brick vest, teal apron and mug. Villagers share a compact base
with different clothing, skin, hair and occasional headwear.

The twelve character PNGs are transparent 612x612, 68px cells: preview row,
eight facing rows, three idle / three walk / three peaceful gesture frames.
Northwest, West and Southwest are exact horizontal mirrors. Chest is 612x136,
two nine-frame closed/open floating loops at 160ms per frame (1.44s cycle).
Vertical offsets are baked into its frames; avoid adding a second bob.
Animated PNG previews for both chest states and a twelve-character gallery
are retained in `art/town-npc-pack/` alongside all thirteen sources/prompts,
measured crop manifests, metadata, asset review and reusable art builders.

This package is prepared for import, not installed. Existing live hero, enemy
and summon imports from the campaign update remain in place. The new package's
stdlib Python importer adds an independent `static/town-sprites.js` loader,
three small hooks in the villager/service-NPC/chest draw functions, and a defer
script before app.js. It preserves labels, interaction rings and procedural
fallbacks; does not replace app.js wholesale or change server/data formats.
Existing twelve stationary villagers cycle through eight designs with varied
facings/phases. The open chest loop is supplied for future use because looted
chests currently disappear. Import directions are inside the ZIP in IMPORT.md.

Asset inspection passed for all 864 directional character animation cells:
binary transparency, padding, frame variation and exact eligible mirrors.
Chest has eighteen distinct exported cells and two nine-frame animated previews
at 160ms per frame. Importer execution and live gameplay were not evaluated in
this art task. Rebuild art with `./art/town-npc-pack/build-sheets.ps1` in
PowerShell 7; rebuild the ZIP with `python art/exports/build_town_npc_package.py`.

## 2026-10-07: Battlefield art revamp

Implemented the requested new style for all four combat regions: woodland
clearing, ancient ruined courtyard, crystal cavern and frostlands. Each uses a
full-field pixel-art background matching the imported hero sprites. Quiet flat
central ground and clear top/bottom passages keep fighting space readable;
trees, masonry, crystals and snow-covered rocks are concentrated at edges.
Scenery is decorative, with no new collision or server changes.

`static/sprites/field-woodland-v1.png`, `field-ruins-v1.png`,
`field-cavern-v1.png` and `field-frost-v1.png` are 480x270 and render at the
existing 960x540 canvas size without smoothing. `fieldArt` in static/app.js
preloads them via the existing sprite route and invalidates the terrain cache
on successful loads. `drawArenaBackdrop` reuses the cached regional background
through combat, treasure and stage-exit phases. Old procedural props are used
only if the image is unavailable, avoiding duplicate scenery over the art.
Each region has one static field; the former stage-dependent scattered props
remain only in fallback rendering. Town, fork and puzzle renderers keep their
own scenery. Existing hero, summon, NPC, chest and progression code is retained.

Source images, four exact generation prompts, relative-path manifest,
PowerShell export/gallery builder, overview preview and art review are retained
in `art/stage-fields/`. Built-in image generation used the hero-party gallery
as a style reference. Nearest-neighbor export gives a consistent two-pixel
display grid; the source drawings' literal pixel clusters remain approximate.
Rebuild with `./art/stage-fields/build-fields.ps1`. Art was visually inspected;
implementation tests and live gameplay checks were not run for this request.
Refresh http://127.0.0.1:8000/ to load the static update; no server restart needed.

## Hunter story, training, bed saves and town sprites — 2026-10-07

The latest story/tutorial request authorizes the previously proposed stat tree.
`progression.py` owns dialogue, quest, training and inn progress;
`static/progression.js` renders those flows, the clearing and upstairs guest rooms.

- A peaceful clearing follows stage 1 or 2 once, without consuming another stage.
  Speak to the wounded hunter to accept the find/kill dragon quest. Present humans
  accept and gather at the northern exit; bots accept automatically. Menu → Quest
  shows the objective. First-village runner approaches with two dialogue pages;
  all party movement/attacks freeze until present humans finish. Each present
  human then completes the innkeeper tutorial before the south gate opens.
- Four-page innkeeper tutorial opens training: three ranks each in Vitality
  (+4% base max HP), Power (+3% base damage), Focus (+5% mana regeneration),
  one point per rank. Each hero earns one point for the tutorial and one for
  each of the first two great bosses, once per run. Ranks survive Guild changes
  and use the new hero's base stats. No account-level progression or respec.
- Inn stairs lead to three rooms, one/two randomly occupied and locked. Free
  beds restore party HP/mana and set disk checkpoints. Talking to the innkeeper
  no longer restores resources or saves. Checkpoint updates apply only in the
  saved village; a later village needs a new bed save. Restore/wipe recovery
  places heroes inside the saved guest room; reconnect preserves interior
  position. Older automatic inn saves stay valid and bind to their original town.
- Enemies target only living heroes/summons. Downing their target releases
  pursuit and pending aimed boss attacks. Projectile, splash, hazard and charge
  damage ignore downed heroes; further hits cannot shorten rescue time.
  Mana recovery is 2/s combat, 6/s otherwise, before Focus (previously 4/12).
- All character/NPC/enemy/summon shadows are circles. Druid idle frames 550ms,
  walk frames 300ms with subdued bob; Bear scale 2.15 and Golem 2.5 make their
  visible art slightly taller than the combat Druid.
- Manually imported the supplied town pack: four service NPCs, eight villager
  designs, floating chest, 26 PNG/JSON files and inspected town-sprites.js.
  No package importer script was executed. Directional NPC idle/walk/gesture
  animation preserves interactions; villagers remain decorative. Chest uses
  baked floating animation and its open loop during pending loot; existing
  rewards/curses/full-pouch behavior stays intact. server.py serves both new JS files.

Validation: 82 Python regressions passed, including legacy migration and disk
bed recovery through the state API. Node held-attack/936 animation-cell checks,
actual-PNG damage/alpha tests, 864 NPC/villager cells and 18 chest frames passed.
Isolated browser QA covered hunter quest, runner, tutorial, training purchase
(Druid HP 80→84), stairs, bed save and floating chest healing. Console clean.
390×844 training fits without horizontal overflow and has 44px action buttons.
Saved previews in reports include town, training, phone, guest rooms and chest.
Temporary port-8001 server stopped; viewport override reset. Functional checks
do not replace human multiplayer balance or physical-phone playtesting.

Activated Python changes on port 8000. Existing checkpoints were backed up under
data/backups/before-hunter-update-* and stayed byte-identical. All 32 client and
NPC/chest live static responses match disk. Refresh to load the client; start a
new run for the early story/welcome. Historical notes above predate bed saves.

## Human votes, compact dialogue and no downed countdown — 2026-10-07

- `_voting_players` includes connected humans only. Town exits, physical fork
  voting, direct route actions and departure/rejoin checks use that group.
  NPC/stale offline votes do not affect route totals, majority or host ties.
  Human votes resolve immediately without waiting for the companion's position.
  Stage/peace exits also require humans only. No-human rooms cannot advance.
  NPCs still count in combat difficulty, party slots, chest loot and puzzles.
- `activeVoterCount` drives fork/stage HUD denominators; town vote totals and chat
  readiness counts are human-only. Leaving town clears interiors/dialogue for
  the entire party and carries the companion into combat with the humans.
- Story dialogue is a bottom panel, max 540px wide / 300px tall (280px phone cap),
  with a lighter backdrop. All dialogue pages and server-owned movement locks
  remain. Browser QA: 540×181 desktop panel; 352×194 at 390×844, no horizontal
  overflow, 44px Continue button. Screenshots: reports/compact-dialogue-preview.png
  and reports/compact-dialogue-phone.png.
- Removed the downed expiry mechanic and HUD countdown. Allies remain downed
  indefinitely while someone is alive, including when old timer values exist.
  Party wipe still occurs if everyone goes down. Manual revive channel remains
  1.8s (Healer 0.8s); instant revive abilities still work. HUD says Needs revive.
  How-to-play text updated. Deaths count actual wipes, not downing or waiting.

Validation: 89 Python regressions passed, including six human-vote cases and
late revival after a 60-second wait. Client syntax and held-attack/936 animation
cell checks passed; compact dialogue verified on desktop and phone browser.

Follow-up in the same update: stages 1–6 have a 10% three-wave chance for every
party size, otherwise two waves. Stage 7+ retains existing party/late-stage rules.
The state API provides a per-viewer chest.opened value derived from that hero's
decision or pending chestReward; the renderer uses it instead of shared
runesAwarded. A teammate opening/looting never opens another player's chest art.
The new regressions cover exact probability boundaries and separate views for
unopened, pending-full-pouch and claimed shares; 91 server tests pass.
Node client regression also verifies personal chest rendering when shared Runes
have already been awarded. Activated on the live port-8000 server; checkpoint
backups retained under data/backups/before-vote-chest-update-*. All four updated
client responses match disk. Temporary dialogue preview server stopped and its
browser tab removed; phone viewport reset.

## 2026-10-07: Fork screens match the previous region

Implemented four regional fork backgrounds: woodland, ruins, cavern and frost,
matching the corresponding battlefields. `drawForkBackdrop` in static/app.js
selects `room.region`, which game.py already preserves throughout stage exit
and the fork. Destination region is assigned only in `_advance_stage` after
route selection, so both branches show the area just left without revealing
future scenery. No server, progression, save format or route-voting changes.

The new `static/sprites/fork-REGION-v1.png` files are 480x270, displayed at
960x540 without smoothing. A separate fork canvas caches them and invalidates
on artwork loads. While unavailable, the current region's battlefield and
region-colored procedural paths provide the fallback. Existing signs, names,
edge votes and Lens hints remain dynamic; signboards have simple pixel trim,
and dark label panels keep text legible over the frost background.

`art/fork-fields/` retains four generated sources, exact prompts, layout guide,
relative-path manifest, export/gallery builder, preview and art review.
Built-in image generation used the canonical fork guide and each battlefield
as layout/style references. Sources had approximate path widths/positions;
the exporter clears the exact walking corridors using trail textures sampled
from the generated art. Manifest coordinates match FORK_PATHS, with 108px-wide
roads, rounded joins/caps and a subtle outer trim. Scenery adds no collision.
Rebuild with `./art/fork-fields/build-forks.ps1`.

Artwork was visually reviewed, including canonical exported paths and clear
stem/side exits. Implementation tests and live gameplay checks were not run
for this request. Refresh http://127.0.0.1:8000/ to load the static change;
no server restart is needed. Battlefield, town, puzzle and hunter art remain
as currently implemented.

## 2026-10-07: Complete equipment and utility icon set

Created individual pixel-art sprites for every equipable ITEMS entry: 22 total,
13 tools (10 weapons, 3 armor) and 9 utilities. Catalog was extracted from
game.py using AST/literal_eval without importing the game or touching rooms.
Complete names, rarities and existing effects are retained in
`art/item-sprites/ITEM_CATALOG.md` and catalog.json. No new items or stat changes.

`static/sprites/item-KEY-v1.png` files are 64x64 transparent cells with artwork
uniformly fitted to a maximum 48px footprint. Nearest-neighbor sampling and
binary alpha give crisp edges. `item-icons-v1.png` is a 384x256 atlas, six columns
and four rows, with two empty cells; `item-icons-v1.json` maps every stable key
to its rectangle, filename, name, type and rarity. Original pixel clusters and
color palette remain approximate. All 22 final sprites were visually inspected.

`createItemSprite`/`decorateItemLabel` in static/app.js add sprites to quick
pouch items, equipped slots, merchant stock, town inventory, pending chest loot,
swap choices, route-lens action and utility hotbar. Item names, descriptions,
prices, action buttons and keyboard behavior are preserved. Unknown/missing art
keeps text, and the hotbar restores its former symbol on image failure. Icons
are decorative for accessibility because adjacent names identify the items.
CSS uses 32px icons and 24px in compact equipped slots/phone hotbar; text retains
compact truncation and expanded wrapping. Existing on-character gear overlays
are unchanged. No Python/server/save changes or restart required.

`art/item-sprites/` retains all 22 sources and exact prompts, the immutable style
reference, manifest, catalog, gallery, PowerShell builder and asset/export
reviews. Built-in image generation used one call per item with transparency.
Rebuild via `./art/item-sprites/build-items.ps1`. The complete art handoff is
`art/exports/Equipable-Items-Sprite-Pack-v1.zip`, recreated by
`python art/exports/build_item_sprite_package.py`. This ZIP contains art/source
files and metadata, not an automatic importer or whole client replacement.
Sprites are already integrated into this project; refresh the browser to load
them. Implementation tests and live gameplay checks were not run for this
request; art/export inspection does not establish live UI behavior.

## 2026-10-07: Environmental combat, roles, balance and conversation HUD

Implemented the four newly selected improvements, plus subsequent dialogue,
utility placement and companion AI requests. Preserve all imported art hooks.
`combat_environment.py` owns stage-local cover, traps, poison and frost ice.
Crates/rocks block swept movement and projectiles (the nearest collision wins),
take Light/AOE damage and remain broken between waves. New stages regenerate
them using a room terrain seed. Poison affects living actors once/second, and
traps have .75s warnings/4s rearming. Enemy terrain damage is nonlethal so players
receive kills. Ice blends velocity, including release momentum. Summons and
foes detour around cover; dash/strike/blink no longer tunnel through it.

`enemy_roles.py` assigns family roles: minotaur charger, serpent ranged,
wolf/spider ambusher, troll bruiser; the last ordinary enemy in groups of 3+
can become support, excluding assassins. Supports heal one wounded living foe
after a warning. All roles commit to windups and recovery, use independent
movement decisions and cancel attacks aimed at downed targets. Empowered/boss
enemies retain boss_ai patterns. Boss timings are fixed 1–1.5s windups and
1–1.5s recovery (charges add their .7s travel), with locked charge endpoints,
shot fans, danger circles and recovery labels. Charge speed caps at 420.
`static/combat-environment.js` renders these overlays over the regional artwork.
It tolerates old server attack state while waiting for an upgrade restart.

Companions now predict incoming projectiles, escape marked ground/charge danger,
alternate .65s dodge commitments, sidestep periodically, kite when ranged and
crowded, and choose short cover waypoints. Normal speed/stats/damage still apply.
Immediate danger interrupts a revive attempt. All new clocks participate in
disconnect pause/resume so warnings, recovery and dodge timers cannot expire offline.

Balance: preserve 90%/200% Light damage and 8/15s death recharge. Bird HP40 and
interval1.15; Wolf65/1.15; Bear125/1.4; Golem170/1.8. Live summon attacks recompute
their equipped Light contribution so temporary boosts expire. Stuns gain1.8s
resistance; normal stun.6s, mini.55, boss.25. Healer Gentle/ Major Mend now target
one injured ally. Empty healing casts do not consume mana. Expired wards no
longer keep stale mitigation. Telemetry v2 records actual healing/revival HP,
ward HP saved credited to caster, and captured projectile/bleed boost assistance.
Boost assistance overlaps attacker damage; never add those totals together.
Run stats/UI/download still show only five overall fields.

`tools/balance_probe.py` runs198 cases for all heroes, sizes1–4, stages1/8/16,
two seeds; solo Wolf/Golem extras. `--before-tuning` substitutes old summon/stun
constants only inside its process. Matched JSON and readable findings live in
reports/. Initial90-case old-combat baseline is retained separately. Fresh base
gear/no training and limited seeds mean this is not a final balance claim.
24/66 cleared stage-one simulations ended before the15s opening Ultimate timer;
keep that timer as requested and validate further with humans.

Story dialogue uses two compact panels: player left, NPC right, facing sprites
and corresponding text/response. All original acknowledgement/quest/training
rules remain. Utility icons flank central E interaction (1 left,2/3 right),
retain accessible names/tooltips and click/tap/keyboard use. Six-page optional
guide includes environmental gameplay. Browser checks at1280x720/390x844/844x390
verified conversation layout, reachable landscape responses and actual mana
utility consumption. Screenshots in reports/.
111 Python regression tests and client/town sprite checks passed at this point.
Server was restarted on port8000 after the user explicitly authorized ending
their unsaved stage3 Druid/companion run. Existing CEVKC/UTAE4 bed checkpoints
were copied to `data/backups/before-combat-update-20261007-.../` before restarting.
Live HTTP smoke confirmed the new script200, a scaled two-member combat room,
three cover objects/two terrain zones, role assignment and15s opening Ultimate.
Refresh the browser to load the updated client. Temporary QA servers/tabs are
closed after verification; the normal server remains running.

## 2026-10-07: Themed villages, house interiors, hunter road and UI refresh

Village rendering now follows the previous area's `room.region`, matching the
woodland, ruins, cavern and frost battle/fork art. All six existing building
roles have distinct exteriors in every theme: inn, store, alchemy lab, guild,
cottage and lodge. Their original six roof colors remain available through
deterministic recoloring (144 exterior variations). Names and shuffled layouts
remain server-owned. Ground and the original 44/30px roads are cached at half
world resolution, using the matching fork trail texture. Building silhouettes
fit the existing collision footprint; doors retain their existing coordinates.

Every theme has six distinct furnished downstairs interiors, an upstairs inn
background, and tree/gate/bed/stair/open-door/closed-door props. Caverns use
luminous mushrooms in place of trees. Upstairs floor textures and windows are
assembled on the authoritative three-room plan. Beds have three quilt colors;
doors, occupied rooms, save prompts and stairs remain dynamic. Frost exterior
props retain snow while indoor stairs/doors were corrected to clean surfaces.
The wounded hunter now has four themed road/clearing backgrounds, with the
central 108px trail and open exits; NPC, bandage and quest interaction remain
separate. No new collision, mechanics, save format or Python changes.

Runtime art is `static/sprites/village-REGION-KIND-v1.png` (28 files), plus
eight `portrait-HERO-v1.png` menu images cropped from current hero idle sheets.
Client integration is in static/app.js and static/progression.js. The previous
procedural drawing remains as a loading/missing-art fallback. Refresh the HTTP
game page; no server restart is required for this update.

The requested follow-up UI pass is implemented in static/style.css, app.js and
index.html: entry/party menus, hero and ability selection, chat, HUD, meters,
utilities, compact/expanded pouch, equipment, merchants, loot swaps, route and
puzzle panels, guild, training, story/quest/guide/settings/stats dialogs and
victory/defeat views use timber/slate/brass/parchment styling. Actual hero
portraits replace class glyphs. Pouch items have larger icons, textual rarity
and matching border accents, equipment captions and an informative empty
state. IDs, actions and keyboard behavior are retained. Existing recent HUD
utility/interaction placement and compact dialogue portraits are preserved.

`art/village-art/` retains 24 built-in image_gen originals/specifications,
three corrective edits and their originals, references, manifest, PowerShell export
and preview builders, workflow, UI scope and art/export review records.
Sources have approximate pixel clusters/palettes; exports use nearest-neighbor
sampling and binary alpha for sprites. Atlas bleed is removed by component
filtering, roof recoloring preserves shading, woodland/ruins floor plates were
corrected to a single biome throughout, and backgrounds use generated
textures. Rebuild with `./art/village-art/build-villages.ps1`, then
`./art/village-art/build-previews.ps1`. No API key or fallback CLI was used.

Artwork and export geometry were inspected. Implementation tests and live
gameplay/UI checks were not requested or run for this change; those remain a
separate validation step. Preserve the existing Python/server/client design
and data/checkpoints when transferring this project.


## 2026-10-07: Deliberate encounters, controls, length selector and Dracos

Implementation follows the user's continuing combat/control update and newest
Draco enemy request. Preserve the concurrent imported battlefield/effect and
village/UI artwork; these changes use those existing sprite hooks.

New files: static/movement.js, combat_encounters.py,
tests/test_deliberate_combat.py, tests/test_dracos.py, tests/test_movement.cjs,
tools/audit_difficulty.py, and reports/COMBAT_UPDATE_VALIDATION.md. The movement
script is registered in server.py and deferred before app.js. Its browser
initialization is guarded for the still-running older server until activation.

Local movement prediction replays normalized direction history against server
position/speed/slide state, reconciles small errors over 100ms, snaps larger
teleports and stops after 250ms without a snapshot. It matches cover/ice,
town/interior/locked-room and fork collision. Server movement remains authoritative.
Polling targets 50ms including request/render time. Input sends are coalesced,
sequenced and release-safe; stopRevive now cancels human revive channels.

Terrain is one or two widely scattered breakables and one random trap/poison/
(frost-only possible ice) zone per stage, with spacing and open entry/exit lanes.
They persist through waves. Objective plans start at stage4, exclude scheduled
boss/mini/puzzle/town/ambush stages, have at least three stages between them and
are saved in inn snapshots. Rift: destroy structure to stop 5s reinforcements,
then clear foes. Ward: survive32s, intercept enemies from alternating edges,
then clear foes; ward destruction defeats the attempt without charging hero
death counters. Charge: sentinel plus two rocks; cover collision creates2s
recovery. Objectives use the standard damage/projectile/target/finish systems.
Ward is a combat target outside the hero/summon roster. Offline clock shifting
includes objective spawn/deadline. Checkpoint restore defaults old saves safely.

Normal enemy groups introduce Dracos at STAGE17 (confirmed by the user), rather
than global wave17. Base HP124, damage7, speed108–126, all ordinary scaling still
applies. Per-enemy25% introduction roll, maximum min(3,active party size) per
wave. Dracos keep their own role; supports are chosen from other families.
Assassin generation explicitly excludes Dracos and objective reinforcements
clone an ordinary foe. Dracos alternate a300-speed, radius8, turnRate.3 projectile
and a55-range bite; .35/.4s wind-ups, .25s recovery,1.25s base attack interval
with existing capped rate scaling. A bite can miss; it still advances the cycle.
Downed targets are excluded and cancelled pending attacks retarget normally.
Existing dragon-idle/windup sheets render Dracos at1.25 scale versus hero1.65,
ordinary enemies1.5 and larger bosses. Warnings show SHOT/BITE and aim/range.
CHARACTER_ROSTER.md is updated.

Optional target preference: click/tap a foe, Tab cycles, Escape/Clear restores
auto. Server selection prefers that foe only when legal for the attack, falling
back for range/cover. Input carries preference to avoid click/attack races.
Summons retain nearest-enemy AI. Local hero and selected target have clear
markers; ordinary combat names/permanent role panels and attack-range fills
are reduced. Danger wind-ups and health remain. The exit rectangle is removed
while preserving the earlier requested arrow.

Compact pouch hides unused utility/tool slots; Expand exposes all. Always show
a dedicated curse sprite/name/stages slot (or placeholder), outside ten carried
spaces, using curse-sluggish/weakened/frail-v1.png. Existing expanded curse
status is retained. Chest notice mojibake is fixed, with a guarded client repair
for the older server. Main-menu exit explains current in-memory Continue versus
persistent upstairs bed checkpoints and permits cancelling. Optional guide is
six pages, including new objectives and target preference.

Challenge and campaign length are independent: Easy.9/Medium1.25/Hard1.6 and
Short20/Standard25/Long30. runOptions captures values before disabling selectors;
renderClasses does not reset them while a request is pending. Explicit stages
mark lengthChosen; later challenge-only API edits preserve it. Legacy clients
without any explicit length keep their earlier default mapping. Inn snapshots
persist lengthChosen. The user's stuck-Long bug is caused by the older active
Python backend still coupling Hard to30; it is fixed in source and isolated HTTP
and browser checks, and requires production restart.

Town pressure increments smoothly: new town arrival history gives half a visit
on the next combat stage, a full visit on the following stage, preserving eventual
+25%HP/+20%damage/+10%speed/+12%attack rate per visit. Legacy checkpoints without
arrival history retain their accumulated pressure. Telemetry now captures
challenge/length/town visits/route pressure/town arrival history. The audit
reports81 generated schedules and53 historical stage observations (unverified
provenance, no old contextual metadata); it cannot establish human balance.
Stage17 composition and group size are explicit audit concerns. Required human
solo/multiplayer and physical-phone testing stays in the backlog and report.

Validation:129 Python tests pass; Node held-input, movement, damage/alpha,
936 hero/enemy/summon cells and864 NPC/villager cells/18 chest frames pass;
JavaScript syntax passes. Isolated HTTP tested nine challenge/length pairs,
simulated two-member synchronization, disconnect/reconnect and stale movement
release. Browser checked1280x720 and390x844, actual Draco rendering/wind-up,
ward HUD, selection/clear, session exit/cancel, length persistence and curse
art. Phone compact pouch272px, no horizontal overflow. Existing portrait canvas
aspect distortion and physical-phone comfort remain outstanding. Isolated scene
average draw time~.30–.34ms; limited local measurement, not a general benchmark.
See reports/COMBAT_UPDATE_VALIDATION.md, DIFFICULTY_AUDIT.md and PROTOCOL_CHECK.md.

Activation status at this entry: source complete and tested; production Python
server on port8000 has not been restarted. RoomAAT4A is at stage1 exit without
an inn checkpoint; explicit confirmation to discard that run and restart was
requested. Preserve data/checkpoints and back them up before an approved restart.
Static files need refresh, but movement.js and new APIs require the backend
restart. The previous server session ID is6629. Temporary QA server28722 on8001
and browser tab21 are cleanup-only fixtures, not user runs.


## 2026-10-07: Tester mode and automatic restart authorization

The user explicitly said not to ask permission for server restarts moving
forward. This is standing authorization for updates; it is recorded in AGENTS.md.
Back up bed checkpoints before restarting, then activate and check the server.
Do not re-ask solely because live rooms reset. Both CEVKC/UTAE4 checkpoint copies
were verified before the Draco restart in data/backups/before-dracos-update-
20261007-172623, with SHA256 manifest. A further backup before Tester activation
is data/backups/before-tester-update-20261007-173949.

Dracos/control/objective/independent-length updates were activated, then Tester
mode was added and activated in a second automatic restart. Normal server now
runs on port8000 (exec session99711); source and running backend agree. Temporary
QA servers30557/28722 are stopped; the later Tester preview40959 is cleanup only.
Previous unsaved live roomAAT4A resets under the user's explicit authorization.

Temporary Tester is a Run length option9, independent of difficulty/companion,
kept until the user requests removal. Its physical stages1–9 map to standard
25-stage progression1/4/7/10/13/16/19/22/25 through GameWorld._effective_stage.
This drives stage ramp, per-stage strength, normal group size/Draco threshold,
stage wave count, terrain damage and objective HP. Schedules are explicit and
non-overlapping: miniboss2, bosses3/6/9, town4, puzzle5, objective8. No assassination
roll in Tester; scarce normal stages stay available for the requested content.
Late ordinary waves guarantee the first Draco at Tester stage7, while normal
campaigns keep stage17. Normal cooldowns/story/tutorial/summon/vote rules remain.
Mode derives from totalStages==9, already saved in bed snapshots. State adds
 testerMode/balanceStage; HUD shows TesterN/9; lobby describes compressed pacing.
Telemetry records those fields to distinguish fast tests from ordinary runs.

134 Python regressions pass, including five Tester checks for repeated schedules
on all difficulties, reference25-stage stat equivalence, early late-game groups
and three-wave stages/Dracos, disk bed recovery and an accelerated actual wave/
boss/puzzle/inn-transition test that finishes after both dragon phases at9. That
test fast-forwards damage/time and is not human balance evidence. Existing Node
checks pass and browser confirmed Tester9 sticks on changing toHard, then starts
with Tester1/9 and15s Ultimate. Live HTTP confirmed Tester9 accepted and preserved
on a challenge-only edit. Audit expanded to108 curves including Tester; physical
phone/human balance checks remain outstanding.

User additionally requested a ZIP of the latest game and a new commit to their
The-Gauntlet GitHub repository, explicitly invoking GitHub. The local Git repo
has no commits/remotes and no configured author. Plugin management confirms
GitHub installed/enabled, but no repository connector tools are exposed in this
chat's available tools. Git credential manager has no non-interactive GitHub
credential, and the in-app GitHub browser is signed out. Repository URL was
requested; no URL is assumed. Package preparation continues independently of
that access step. Private data/checkpoints must remain excluded from GitHub by
.gitignore; preserve them in the local transfer ZIP.

## 2026-10-07: New workspace and portable handoff

The user switched this chat to `The gauntlet` and requested running the game
there. Its initially empty working folder was populated from the verified
Dracos/Tester source-art ZIP: all 879 file hashes matched, including the two
existing bed checkpoints. The game now runs from this folder on port8000
(exec session58290); the HTTP page and app/movement/combat/style assets return200.
The live browser was opened through Codex. The older laptop folder remains intact.

The repository is https://github.com/Nael-Shakhsheer/The-Gauntlet, default branch
main. The connected GitHub plugin now exposes repository tools and confirms
the owning account has push permission. Its prior contents are README.md and an
older ZIP. Publishing is prepared as runnable source and all runtime sprites,
preserving the existing archive/history. The separately prepared playable ZIP
includes all game code and runtime sprites; it excludes private checkpoints,
balance logs, large original art projects and screenshot reports. The full local
source-art ZIP retains original artwork and the saved bed checkpoints. Both
packages have per-file hash manifests and archive verification. The earlier full
package passed all 134 Python regressions after extraction. Publication is not
complete until the branch head is verified against the new commit.
