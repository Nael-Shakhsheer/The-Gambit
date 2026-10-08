# Difficulty audit — 2026-10-07

Generated 108 complete schedule/stat curves: all three challenges, the three normal lengths plus Tester (9 stages), parties of 1/2/4 and route pressure -4/0/6. These sample spawned waves and boss/elite/objective compositions; they are not played campaign clears.

The local server has 53 recorded stage observations spanning stages 1–25. Their player/test provenance is unverified. 0 rows record challenge/town/route context, so older logs cannot establish which stacking factor caused a spike. New telemetry captures those fields. No names or room identities are exported.

Town pressure retains its eventual +25% HP / +20% damage per visit, but arrives in two steps: 50% on the first combat stage after town, 100% on the second. Legacy saves without arrival history retain their existing accumulated pressure. This reduces the immediate first-visit increase to +12.5% HP / +10% damage, before the independent stage/party/mode/elite/route factors.

Challenge and campaign length are independent. A Hard 20-stage run and an Easy 30-stage run are valid; event schedules fit the selected length. Length affects the normalized stage ramp and boss spacing, so it is not a cosmetic timer.

Tester maps physical stages 1–9 to combat progression 1/4/7/10/13/16/19/22/25. This accelerates enemy stats, ordinary group size, waves, terrain damage and objective HP. Its bosses are at 3/6/9, miniboss at 2, town at 4, puzzle at 5, objective at 8; ordinary waves guarantee a Draco from Tester stage 7. Normal campaigns still introduce Dracos at stage 17. Tester curves are labelled length 9 and should not be pooled with ordinary runs.

Largest ordinary adjacent-wave HP ratios in the sampled curves (random foe count/type also changes these):

| Challenge | Length | Party | Route pressure | Stage | Dracos | Total enemy HP ratio |
| --- | --- | --- | --- | --- | --- | --- |
| hard | 9 | 1 | 0 | 5 | 0 | 4.09× |
| medium | 9 | 1 | 0 | 5 | 0 | 4.07× |
| easy | 9 | 1 | 0 | 5 | 0 | 4.03× |
| hard | 20 | 1 | 0 | 17 | 1 | 3.12× |
| medium | 20 | 1 | -4 | 17 | 1 | 3.12× |

Interpretation: total wave HP is workload, not a single-enemy strength multiplier. Random group size and enemy composition create larger workload changes than the smoothed town factor. Stage 17 also increases ordinary group size and introduces durable Dracos; their counts are captured above and in the JSON. Boss/elite transitions are intentionally excluded from that table; their raw samples remain in the JSON. Do not tune every spike from aggregate HP alone.

## Required human checks

- Play matched solo and two-human runs with the same challenge/length; compare the stages just before and after each town, gear/training purchased, knockdowns, clear time and whether losses felt readable.
- Test on a physical phone: hold movement plus attack, change direction, dash away from warnings, tap a preferred enemy, clear it, revive and release, equip/swap utilities, and use landscape dialogue.
- Use two real devices for shared spending and reconnect: buy simultaneously with limited Runes, disconnect at an exit, rejoin during combat, and check the missing player neither blocks votes nor creates duplicate purchases.
- At an inn bed, verify the checkpoint message. Leave/rejoin with the server running, then deliberately restart after a saved town and confirm only bed progress returns.

Physical-phone comfort and human multiplayer coordination have not been established by this audit. Automated regression and protocol checks are separate from those playtests.
