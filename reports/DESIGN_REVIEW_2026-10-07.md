# The Gauntlet: developer design review

Date: 2026-10-07. Planning recommendations, not authorization to implement them.

## Scope and judgment

Reviewed the live localhost client: lobby/ability selection, early woodland combat,
cleared arenas, wounded hunter road, village, inn and pouch. Also inspected current
ability/item definitions, difficulty scaling, boss AI, puzzle logic, handoff and
existing balance reports. This was a limited browser inspection, not a complete
campaign playtest, controlled reaction-time test, human multiplayer test or physical
phone test. Late-game findings below are implementation-based risks.

The game has a substantial playable foundation. Its strongest direction is an
accessible cooperative fantasy expedition: friends enter quickly, fight together,
rescue one another, exchange private clues and recover in physical villages. Keep
that identity, the browser/Python architecture and the existing physical exploration.

The next milestone should improve decision quality and moment-to-moment feel.
Additional hero counts, art packs and longer campaigns will have less value until
the existing combat, builds and run pacing are convincing.

## Recommended priorities

### 1. Combat control and feedback

Most offensive abilities select the nearest enemy. That keeps touch play accessible,
but limits deliberate focus fire on a support enemy or a boss. Prototype optional
pointer target preference on desktop and a target-lock option on touch, retaining
nearest-target fallback. Show the selected target clearly. Test before adopting;
manual aiming everywhere would change the game's accessibility.

Add consistent impact sounds, casts, enemy wind-ups, damage and loot sounds with
volume controls. No audio playback system was found in the inspected client. Build
feedback around existing damage flashes and telegraphs, with distinct impacts and
clear successful/failed cast feedback. Keep screenshake subtle and optional. Avoid
large hit pauses that disrupt real-time multiplayer.

Success criterion: players can identify their target, hit, incoming heavy attack
and reason an ability failed without reading chat.

### 2. Meaningful ability choices and viable solo kits

Druid Thornshot has higher power, longer range and shorter cooldown than Briar Bolt:
1.0/300/.45s versus .9/280/.55s. Their implementations both use ordinary damage
projectiles, so the latter lacks an obvious compensating advantage. Cleric's two
Light attacks also have the same reach and ordinary damage behavior, with one
stronger and faster. Give alternatives different purposes before adding more.

A solo Healer can choose Gentle Mend, Major Mend or Quick Revival, and a healing
or revival Ultimate, leaving no damaging ability. Ensure every accepted solo kit
can finish encounters. Options include a separate basic offensive action or an
explicit offensive Light requirement in solo; choose deliberately with the user.

Clarify Cleric versus Healer: area/zone support versus direct rescue is a promising
division. Knight taunt needs a clear solo use or a solo warning. Give buffs, wards,
summons and rescue contribution visible feedback instead of treating damage as
the only satisfying contribution.

Success criterion: each ability pair presents a real situational tradeoff, and
every legal solo kit can progress without depending on an optional companion.

### 3. Run pacing and encounter objectives

Different regional pictures do not by themselves create different fights. Cover,
traps, poison and ice are good foundations; design encounters around them. Add a
small number of objectives such as destroying a summoning structure, defending a
ward or surviving while opening a gate. Make each force a different positioning
decision. Test a short sequence before expanding the campaign.

The opening has combat, hunter dialogue, village welcome, inn tutorial and save
navigation. Measure first useful attack, first reward, first build decision and
first boss. Teach actions in context, keep mandatory exposition short, and allow
repeat players to skip previously understood explanations without losing rewards.
Keep physical towns and forks, but remove repeated waiting and aimless backtracking.

Success criterion: the first ten minutes demonstrate fighting, cooperation and a
meaningful upgrade, with a clear reason to continue.

### 4. Difficulty clarity and full-run balance

Current enemies receive stage, party, mode, town, route/strain and encounter scaling.
Town visits add health, damage, movement speed and attack frequency. That can make
a restorative destination feel followed by an unexplained spike. Preserve challenge
but audit these interactions against actual equipment and training progression.

Easy/Medium/Hard also change campaign length from 20 to 25 to 30 stages. Consider
separating difficulty from expedition length so a harder challenge does not also
require a longer session. This is a proposed design change, not an implemented one.

The existing probes help locate risks, but their late-stage base-gear/no-town cases
do not model normal campaigns. Record human full-run clear rates, damage taken,
time, purchases, deaths and where players quit. Judge fairness by whether a player
can explain and improve after a death, not just by aggregate damage totals.

Preserve the requested 15-second opening Ultimate cooldown. Existing simulations
show some early stages finish before it becomes available; test encounter pacing
around that constraint rather than silently changing it.

### 5. Equipment that changes play

Current weapons and armor mainly add damage or subtract damage per hit. Give a
small set of items distinct effects and opportunity costs: a chain projectile with
lower single-target power, armor that supports rescue, or a summon-focused tool
that trades owner damage for summon durability. Avoid adding large catalogs first.

Show equipped-versus-new comparisons and explain the practical benefit. Shared
Runes need visible purchase attribution so spending does not create party confusion.

Success criterion: a player can describe their build by its behavior rather than
only its rarity or damage number.

### 6. Boss identities and phase payoff

Bosses already have wind-ups, attack corridors and recovery windows; keep them.
Minotaur and troll currently share the same slam/rocks/charge sequence. Dragon
elements share the same attack selection. Add one signature spatial mechanic to
each boss and elemental dragon before multiplying the boss roster.

For example, a minotaur could exploit charge lanes while a behemoth rearranges
cover; Fire could leave spreading unsafe ground and Ice could divide safe movement
lanes. Telegraph new rules before punishing them.

The dragon's refreshed second HP pool is 1.6 times phase one's maximum. Make the
transition visibly foreshadowed and mechanically different so the additional
endurance feels like a climax. This needs a human late-game test.

### 7. Readability and art hierarchy

Live views show cohesive woodland/ruin environments and inviting village interiors.
Character scale, very small overhead labels and several dark role/hazard panels
compete with combat. The default hero is much larger than town NPCs; fit those
scales intentionally. Match hazard/cover art to the surrounding detailed pixel art.

Make local-player identification, health, danger and active target the strongest
signals. Use fewer permanent labels and preserve names/details on demand. Health
currently uses a green bar despite earlier handoff guidance specifying red; choose
one convention explicitly and make health distinct from mana at a glance.

The empty pouch uses a substantial portion of the live view. Favor a smaller
compact state and reserve expanded inspection for safe moments. Validate crowded
four-player scenes, summons and bosses, not only single-character screenshots.

### 8. Routes, puzzles and rewards with understandable consequences

Location-only forks preserve surprise, but a hidden easier/harder modifier without
an observable clue is mostly a guess. Add environmental hints or remembered local
information without revealing future encounter types or numerical difficulty.
Keep the Lens valuable as the explicit clearer hint.

The current cooperative puzzle is a useful communication tutorial: share a symbol
clue and stand on the rune. Randomizing positions adds little reasoning variety.
Later puzzles should combine complementary information, sequences or roles, with
equivalent solo logic and retained disconnect recovery.

Unavoidable chest curses with no remedy may make rewards feel punitive. Test player
reaction before changing the agreed five-stage/no-cleansing rule. Potential future
counterplay could be a clearly signaled risk/reward bargain rather than an invisible
penalty; this would require an explicit design decision.

### 9. Session trust and mobile validation

Inn checkpoints are a useful recovery loop. Distinguish saving a checkpoint from
suspending the current session, and show the last save and how much progress is at
risk when leaving. A longer portable-browser game needs predictable resume behavior.
Any suspend feature should preserve the intended consequences of defeat.

Physical-phone and real multiplayer testing are still required. Test move + attack
+ dodge with actual thumbs, landscape and portrait, keyboard focus, shared shop
spending, revival, simultaneous interactions, disconnects and input latency. A
responsive screenshot does not establish comfortable touch gameplay.

## Suggested development sequence

1. Fix impossible/clearly dominated loadouts and misleading ability descriptions.
2. Improve combat feedback, audio and HUD hierarchy; prototype target preference.
3. Build a compact slice with three distinct encounter objectives, one rewarding
   town visit and one signature boss. Use existing architecture and art.
4. Introduce a few behavior-changing equipment choices and audit progression/scaling.
5. Run fresh-player solo, companion and human-party sessions plus physical phones.
6. Expand campaign content only after that slice is repeatedly enjoyable.

Planning principle: evaluate each proposal by the player decision it creates,
development cost, interaction with existing systems and a concrete playtest signal.
This review does not replace the older backlog or approve all proposed mechanics.
