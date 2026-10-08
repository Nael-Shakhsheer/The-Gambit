# The Gauntlet: current-build reassessment

Date: 2026-10-07. This supersedes outdated findings in the earlier design review
where current implementation has addressed them. Planning only; no gameplay changes.

## Evidence and scope

Read current PROJECT_CONTEXT.md, README.md, difficulty audit and validation notes.
Inspected actual lobby, current Druid ability selection, target cycling, summoning,
two-wave early combat, enemy wind-up, cover/debris, poison, stage exit and sound
settings. Used an isolated in-memory server on port 8001 serving the unchanged
current client and game code. Production port 8000 and bed checkpoints were not
restarted or modified. The isolated server and review tab were stopped afterward.

Inspected desktop and 390x844 portrait browser layouts, current abilities/items,
boss AI, objective implementation and puzzle logic. Adult dragon assessment uses
the retained size-comparison artwork, not a live final-boss victory. Did not complete
a normal campaign, test physical phones or human multiplayer, or listen critically
to the sound mix. Automation timing makes this unsuitable as a difficulty benchmark.

## Overall assessment

The current build is materially improved. Presentation and combat legibility have
advanced; target preference and objective encounters provide useful player agency.
The next bottleneck is meaningful choices and coherent pacing, alongside the
confirmed portrait aspect-ratio problem. More asset quantity is a lower priority.

## Earlier recommendations now addressed or partially addressed

- Target preference: click/tap and Tab cycling implemented; Tab visibly produces
  a selected enemy marker and Clear target state.
- Movement: bounded local prediction and sequenced input are implemented. This
  review did not measure real-device latency or establish multiplayer feel.
- Combat art: cover, poison, projectiles and anticipation now have themed sprites.
  Debris reads much better than the prior generic blocks. Permanent role clutter
  is reduced; wind-up labels remain when useful. Local-player marker is clearer.
- Audio: Bfxr effects bank and persistent volume/mute controls implemented. Live
  settings report Sound ready, with no captured error/warning logs. Audio aesthetic
  quality and dense four-player mixing still need listening tests.
- Encounter objectives: rift, ward and charge/rock interactions exist. These should
  now be tuned and playtested before adding many new objective types.
- Challenge/run length: separate selectors work; Tester offers convenient content
  inspection. Tester compresses enemy progression and is not a balanced short-run
  claim or a replacement for normal campaign pacing tests.
- Save messaging: leaving now distinguishes an active server session from durable
  inn-bed recovery. This improves trust, although current-session suspension remains
  a separate possible design decision.
- Dragon art: compact Draco and large adult dragon have distinct silhouettes. The
  new adult design better establishes the final boss's visual importance.

## Highest-priority remaining problems

### 1. Portrait battlefield distortion: confirmed live

At 390x844 the 960x540 canvas displayed at approximately 390.4x628. Its horizontal
scale is .407 while vertical scale is 1.163. The resulting stretch visibly turns
characters and circular zones into tall narrow shapes. It also makes world movement
distances appear different along the two axes. Desktop distortion is less severe
but should be included in the same aspect-ratio audit.

Choose an intentional mobile presentation: preserve world aspect with letterboxing,
use a carefully designed camera, or explicitly support landscape play. Each option
has tradeoffs for offscreen warnings, co-op visibility and control space. Preserve
actual world collision geometry; fix display mapping rather than tweaking combat
to compensate for stretching. Physical thumb/multi-touch tests remain necessary.

Reference: assessment-current-phone.jpg; desktop: assessment-current-desktop.jpg.

### 2. Ability viability, tradeoffs and description accuracy

An isolated GameWorld accepted and started a solo Healer with healing_ray,
major_mend and miracle. That kit has no damaging attack. Guard legal solo builds
or provide a deliberate offensive fallback. Do not rely on an optional companion
to make an otherwise unwinnable kit viable.

Druid Thornshot remains stronger, faster and longer ranged than Briar Bolt while
using the same ordinary damage behavior. Cleric's Sanctified Throw is stronger
and faster than Radiant Flask at the same range. Wizard Frost Lance also has
higher power, greater range and shorter cooldown than Arc Bolt, plus stun. Give
alternatives distinct tactical purposes rather than arbitrarily changing numbers.

Some descriptions promise behavior the shared implementation does not supply:
Rain of Arrows says around your target, but the area branch measures distance
from the player; Death Bloom promises bleeding, but that area branch only deals
damage. Align actual behavior and text before balancing or adding skills. Target
preference also makes unconditional nearest-foe descriptions less accurate.

### 3. Builds that change behavior

Equipment is still primarily flat damage and flat armor. There is progression,
but limited build identity. Start with a few effects that interact with existing
combat: chaining shots, a rescue-focused defense, or a summon specialization with
a clear opportunity cost. Show equipment comparisons. Keep the item catalog small
until those combinations are enjoyable. Existing class identities need different
combat rhythms, particularly Cleric versus Healer and support contribution feedback.

### 4. Boss mechanics should catch up with boss artwork

Minotaur and troll still use the same slam/rocks/charge cycle. Dragon elemental
types use the same attack-selection pattern. The adult dragon now looks distinctive;
its mechanics need equivalent identity. Add one signature mechanic per boss, with
clear safe responses, before introducing more boss types.

Keep wind-ups and recovery windows. The second dragon phase should be foreshadowed
and offer new decisions so its refreshed 1.6x HP pool feels like a climax rather
than an endurance extension. Actual melee/ranged human tests are needed.

### 5. Tune encounter rhythm and difficulty with full runs

Sparse cover and fewer labels create a cleaner field, but some ordinary encounters
still have a large open center and few spatial decisions. Use purposeful obstacle
layouts and mixed roles. Let the new objectives change priorities rather than
merely adding another HP bar or wait timer. Ensure objectives are discoverable
through clear persistent guidance, not only party-chat instructions.

Town pressure now arrives in two steps, addressing the immediate spike partially.
The audit still flags ordinary stage-17 workload jumps as group size and Dracos
arrive together. Test with actual gear/training and town history. Generated wave
HP ratios are workload observations, not player death probabilities.

Measure first-session onboarding, fight/travel/menu time, meaningful reward timing,
boss time, quitting points and perceived fairness. Tester cannot establish standard
run pacing because combat progression accelerates much faster than the normal run.

### 6. Replay variety beyond combat

Rune puzzles still use one share-a-symbol structure. Good as an introductory
communication task; later versions should require complementary reasoning.
Location-only forks still need observable environmental context if hidden route
pressure is intended as a meaningful decision. Preserve mystery and physical paths.

No soundtrack exists yet. After combat mix testing, a restrained ambient/music
layer could connect fighting, towns and bosses emotionally. This is below core
combat/build tuning and the mobile display fix in priority.

## Recommended next work

1. Correct canvas aspect handling, impossible solo kits and inaccurate abilities.
2. Redesign existing ability pairs around real tradeoffs; add a few build effects.
3. Give existing bosses signature mechanics and tune the new objectives.
4. Play matched human solo/duo runs and physical phones, including stage 17,
   purchases, revive contribution and session recovery.
5. Expand skills, items, puzzle families and music after those checks.

The earlier review's missing-audio/targeting/objectives and coupled difficulty/length
criticisms should no longer be repeated as if they remain unimplemented. Existing
regression reports are useful evidence of correctness, not proof of enjoyment.
