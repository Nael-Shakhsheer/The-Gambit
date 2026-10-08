# Combat balance observations — 2026-10-07

198 matched simulations before and after summon/stun tuning. Both sets use the new environment, enemy roles, boss timings and defensive bot movement. Each hero leads solo, duo, trio and four-player lineups at stages 1, 8 and 16; two seeds per case plus Wolf/Golem solo variants. The old 90-case baseline is preserved separately as `balance-before-combat-update.json` and is not a controlled tuning comparison.

| Lead hero | Clears before → after (24 cases) | Final direct + summon damage | Healing restored | Ward HP saved | Boost assistance |
|---|---:|---:|---:|---:|---:|
| Knight | 23 → 23 | 36152 | 0 | 1463 | 0 |
| Wizard | 23 → 24 | 33844 | 0 | 83 | 10465 |
| Archer | 23 → 22 | 43325 | 0 | 0 | 14498 |
| Cleric | 24 → 22 | 20322 | 2846 | 0 | 0 |
| Rogue | 21 → 22 | 29711 | 0 | 0 | 0 |
| Druid | 24 → 23 | 34961 | 0 | 0 | 0 |
| Bard | 18 → 19 | 15702 | 0 | 0 | 12074 |
| Healer | 23 → 23 | 14056 | 3459 | 0 | 0 |

These totals cover different compositions and amounts of combat. They are observations, not a fair one-number ranking. Healing measures actual HP restored (including revives). Protection credits the ward caster after armor and caps at remaining HP. Boost assistance overlaps the receiver’s damage, including self buffs; do not add it to damage. Summon HP absorbed is actual HP lost, not a claim of damage otherwise prevented to a player. Raw reports retain each summon’s death/survival duration and combined summon uptime.

Changes in this pass:

- Summon per-hit damage remains 90% of equipped Light for Specials and 200% for Ultimates. Bird HP 55→40 and attack interval .85→1.15s; Wolf 90→65 and .75→1.15s; Bear 180→125 and 1.1→1.4s; Golem 240→170 and 1.4→1.8s. Death recharge remains 8/15s. Temporary damage boosts now expire on living summons too.
- Normal stuns last .6s with 1.8s between accepted stuns; miniboss/boss durations remain .55/.25s. Damage and ability cooldowns remain unchanged. This closes the repeated Light stun lock.
- Gentle Mend and Major Mend heal only the most injured eligible ally, matching their descriptions. Full-health heal casts are rejected without spending mana. Expired wards no longer leave a stale stronger mitigation factor.

In the six Druid/Knight/Archer/Healer cases, Druid summon damage fell from 6,242 to 4,200, absorbed HP from 3,289 to 2,374, and average measured summon lifetime from 13.5s to 12.9s. That lineup cleared six cases before tuning and five after. Solo Druid still cleared all six Bird/Bear cases. This reduces automatic contribution without removing the summoner’s role.

24 of 66 cleared stage-one cases finished before the 15-second opening Ultimate cooldown. The user-requested opening cooldown remains 15s; this limitation is documented for future human playtesting.

Bots use the real ability, mana, damage, cover and enemy rules. They dodge but do not rescue, spend runes, select equipment or train. Late-stage cases deliberately start at base gear with no town visits; they do not model a normal progressed run. Only two seeds and the first default kit were used for most heroes; alternative healer/revive/support builds need matched human runs. The data cannot prove every hero is balanced. No additional flat hero damage buffs were inferred from these aggregate totals.

Live measurements append to `data/balance.jsonl`. The visible Run stats and its download retain the five requested overall totals. Reproduce with `python -B tools/balance_probe.py --before-tuning` followed by `python -B tools/balance_probe.py`. Before-tuning only substitutes the previous summon/stun constants inside its simulation process; it never changes game files, live rooms or checkpoints.
