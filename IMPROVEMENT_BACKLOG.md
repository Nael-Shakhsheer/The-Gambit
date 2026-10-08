# The Gauntlet improvement backlog

2026-10-07 tactical follow-up implemented: distinct Druid/Wizard/Cleric Light
roles, committed targeted Rain of Arrows, actual Death Bloom bleed, four build
items with opportunity costs and replacement comparisons, and signature mechanics
for the great Minotaur, Behemoth, Matriarch and elemental Dragons. Dragon phase
two is foreshadowed and changes the elemental pattern. See README and
reports/TACTICAL_UPDATE_VALIDATION.md. Human full-run/phone balance checks remain.



Saved from the design review on 2026-10-06. These are planned improvements, not

permission to change every system at once. The user selected items 4, 5, 12 and

13 for the current implementation.



1. **Attack warnings:** readable wind-ups and danger areas before heavy attacks.

2. **Distinct bosses:** individual attacks, movement patterns and health phases.

3. **Recognizable enemies:** predictable family behavior and visible role variants.

4. **Total contribution balance — current work:** measure hero/summon damage,

   damage absorbed, summon survival, stage time and opening Ultimate availability

   across solo and multiplayer. Keep real observations separate from simulations.

5. **Cooperative puzzles — current work:** each player's totem holds another

   player's clue; retain a self-contained solo version.

6. **Hero identity:** signature mechanics and clearer Cleric/Healer differences.

7. **Combat objectives:** occasional defense, spawning structures, hazards and terrain.

8. **Equipment builds:** meaningful effects and tradeoffs beyond flat stat upgrades.

9. **Guild variety:** larger class-specific skill pools and randomized subsets.

10. **Consistent art:** matching sprites, character scale and readable combat labels.

11. **Audio feedback:** distinct combat, summon, warning and loot sounds with volume controls.

12. **Coordination/mobile HUD — current work:** teammate health, revive timers,

    Help/Gather/Target pings and comfortable mobile controls.

13. **Run protection/introduction — current work:** durable inn checkpoints,

    reconnect/disconnect handling and a short optional how-to-play guide.



Implemented on 2026-10-06: contribution logging and downloadable run stats;

90 repeatable bot comparisons; teammate-held puzzle clues and solo fallback;

party health/rescue timers and Help/Gather/Enemy pings; larger phone controls;

atomic inn checkpoints, reconnect/host transfer and optional five-page guide.



Balance investigation continues with human solo/multiplayer runs. The current

measurements show summon safety and short opening stages deserve further tuning;

this pass intentionally retains the requested damage and Ultimate cooldown values.

Mobile HUD checks cover 390×844 and 844×390 browser viewports; physical phone

playtesting and the canvas camera/aspect behavior remain future refinement work.



Also completed in this session: Cave Troll sprite import and hold-to-attack using

the equipped Light skill. Deferred items remain queued for future sessions.



Completed on 2026-10-07: supplied town NPC/villager/floating chest art, circular
character shadows, slower Druid animation, larger ultimate summons, living-only
enemy targeting and slower mana recovery. The approved hunter story introduces
the dragon quest and first-village stat training. Upstairs inn beds replace
automatic entry/innkeeper saves; old checkpoints remain compatible. Browser
training and bed flows and 82 server regressions passed. Human balance and
physical-phone playtesting remain queued.

Completed next on 2026-10-07: destructible cover, warning traps, poison and
slippery ice; visible charger/ranged/support/ambusher/bruiser roles; boss wind-ups,
attack lanes and recovery windows; all-hero contribution measurements and matched
198-case tuning comparisons. Reduced summon health/cadence, prevented continuous
stun locks and corrected single-target healing. See reports/COMBAT_BALANCE_NOTES.md.
Companions now dodge/kite rather than holding position under fire. Player/NPC
dialogues use compact left/right panels, and utility icons flank the centre E
prompt. Earlier revive timers were removed at the user's request; keep them removed.
Human balance tests across alternative kits, physical-phone tests and remaining
backlog ideas are still queued. These implemented selections do not authorize
unrelated equipment, audio or skill-pool changes.

Resolved on 2026-10-07: `stopRevive` now cancels the human revive channel on release/blur.


Completed in the subsequent combat/control pass: local movement prediction and
sequenced/coalesced input, sparse scattered cover and hazards, a dedicated curse
sprite slot, chest-notice encoding, rift/ward/positioning objectives, optional
target preference, quieter labels and stronger local/selected/health cues,
compact empty equipment, independent challenge/run length, explicit session
versus checkpoint exit copy, two-step town pressure, and stage-17 Dracos with
alternating shot/bite attacks. The 81-curve audit and protocol checks are in
reports/. Automated checks do not replace the queued physical-phone and human
multiplayer runs; historical logs lack enough context to establish those results.


Temporary Tester9 mode is available until the user asks to remove it. It
compresses normal25-stage combat progression and scheduled content into9 stages.
Keep Tester observations separate from normal campaign balance evidence.
