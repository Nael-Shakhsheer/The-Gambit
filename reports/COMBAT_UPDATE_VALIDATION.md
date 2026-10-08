# Combat/control update validation — 2026-10-07

## Automated checks

- 134 Python regressions passed, including existing campaign/story/save/companion
  behavior and the new objective, movement sequence, target, town pressure and
  Draco tests.
- Node checks passed for immediate movement prediction/release/diagonals, stale
  snapshots, teleports/downing, cover destruction, ice, town rooms and fork paths.
- Held-attack, mouse release, simultaneous touch controls and dialog blocking
  checks passed. Imported animation checks covered 936 hero/enemy/summon cells.
- Damage-feedback pixel/alpha checks passed for heroes, enemies and all four
  summons. NPC/villager/chest checks covered 864 directional cells and 18 chest
  frames. Client JavaScript syntax checks passed.
- Draco checks exercise the stage-17 boundary, party caps, stronger HP/speed but
  lower hits, an actual shot–bite–shot cycle, a missed bite after moving away,
  cover occlusion, downed-target cancellation and ordinary objective reinforcements.

## Browser and HTTP checks

An isolated server on port 8001 used its own in-memory GameWorld and did not
write production saves. Test fixtures can override HP, positioning, attack
readiness and timers to isolate UI cases; their screenshots are not balance
measurements. The main server on port 8000 remained separate.

At 1280×720, the in-game Draco sprite and shot wind-up, selected-target ring,
ward objective, sparse cover, curse sprite, stronger local hero marker and exit
arrow were inspected. The exit rectangle is removed. Tab changes Auto target to
Clear target, and Clear returns to Auto. Main menu explains in-memory Continue
versus disk bed checkpoints; Keep playing cancels that exit.

The lobby was exercised through the actual browser controls: Hard plus Short
was accepted; changing challenge to Easy preserved Short after polling. The
separate protocol check tested every challenge/length pair through the real
HTTP endpoints, with two simulated identities, disconnect/reconnect and stale
input after key release. See PROTOCOL_CHECK.md. Simulated identities are not
human multiplayer playtests.

At 390×844, document width and content width were both 390px. The compact empty
pouch measured 272px tall, showed only equipped utilities plus the curse slot,
and loaded the curse PNG. Expanded equipment keeps all slots available. The
existing portrait canvas stretches the world; phone camera/aspect behavior and
multi-touch comfort still require physical-device testing. No claim of physical
phone testing is made here.

The isolated scene averaged about 0.30–0.34ms of canvas drawing per frame on
this machine, with startup maxima around 8–12ms. A previous local lobby request
sample had median 3.64ms and maximum 29ms. These narrow measurements support
removing input/poll/interpolation delay; they do not establish performance on
another device or network. Local prediction remains bounded at 250ms and the
server owns collision and combat results.

Screenshots: dracos-combat-preview.png, combat-update-phone.png,
challenge-length-preview.png, ward-combat-preview.png and stage-exit-preview.png.

## Difficulty evidence and limits

DIFFICULTY_AUDIT.md and difficulty-audit.json contain 108 generated campaign
curves and 53 historical stage observations spanning stages 1–25. Those older
observations have unverified player/test provenance and lack challenge/town/
route metadata. New telemetry records that context. Generated curves include
Draco counts and flag stage 17's combined group-size/composition jump. Town
pressure reaches half its increment on the first stage after town, then its
full existing increment on the next.

Human solo/duo runs, shared spending/reconnect with real devices, and physical
phone movement/attack/dash/rescue tests remain pending. They are listed in the
audit and backlog; regression and screenshot checks do not substitute for them.

## Activation

Python changes require restarting server.py, and client changes require a
refresh. The user subsequently authorized automatic restarts for updates. Bed checkpoints
were backed up, then the main server was restarted to activate the changes and
again to activate Tester mode. Live HTTP verified the new assets, independent
length, sequenced input, targeting, revive cancellation and Tester9 selection.
Tester browser and regression checks also passed; its damage/time fast-forward
completion test is not human playtesting. See PROJECT_CONTEXT.md for details.


Tester mode adds a nine-stage end-to-end schedule and accelerated standard
progression. Regressions cover both dragon phases and exact completion at9,
checkpoint restoration, normal campaigns unaffected and late Dracos at Tester7.
The 108-curve audit labels Tester length9 separately. Screenshot:
tester-mode-preview.png. Browser verified Hard plus Tester persists and starts
with Tester1/9 and the normal15s opening Ultimate cooldown.
