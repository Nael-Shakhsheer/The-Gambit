# Tactical update validation — 2026-10-07

Implemented the user's ability alternatives, accurate effects, build equipment
and boss identities without changing the Python/browser architecture.

## Automated checks

- 157 Python regressions pass. The23 new tactical checks cover splash/roots,
  native and equipment chains, line of sight, cast-range rejection without mana
  spending, committed Rain impact, friendly-fire exclusion, bleed attribution,
  summon health/cost/swap rounding, rescue guarding, actual movement and one-use
  pursuit bonuses, shop stock, cover collision/vulnerability, boss cover cycles,
  poison interruption, all five Dragon signatures, Storm spacing, phase-two
  foreshadowing and paused clocks.
- Node equipment comparison checks pass: stat changes, effect gains/losses,
  duplicate effects, utility replacement and script ordering. Existing client
  action, movement, damage-flash, town-sprite and audio checks pass. Syntax checks
  pass for changed JavaScript.
- HTTP equipment-comparison.js returns200 with JavaScript content type. This
  explicit asset registration was caught during final integration verification.
- `tools/tactical_probe.py` ran12s actual projectile fixtures against one and
  three stationary targets. `TACTICAL_LIGHT_PROBE.md` contains measurements and
  limits. Area attacks outperform focused options in tight groups; Frost trades
  sustained damage for control. These fixtures do not establish human balance.

## Browser checks

Used a separate in-memory server on port8001, leaving production bed files and
rooms intact during QA. Verified the Druid descriptions in class selection,
equipped Summoner's Staff through Tool1, and saw stats and gain/loss comparisons
update correctly. Desktop and390x844 checks show wrapped comparison text without
horizontal overflow, and no browser console errors. Reference screenshots are
`tactical-equipment-desktop.png` and `tactical-equipment-phone.png` in this folder.
New items currently reuse existing art with colored borders.

Remaining: human boss/readability and build behavior testing, full solo/multiplayer
balance runs, and physical-phone controls/performance testing. Portrait arena
aspect stretching is a previously documented issue outside this selected update.
