# Balance probe — 2026-10-07

198 simulations: all eight heroes in solo and 2–4-player lineups, stages 1, 8 and 16, two seeds each. Additional solo cases test Wolf/Golem. Controlled observations, not human playtests or a final class ranking.

Bots approach inside Light range, use the companion's defensive movement and cast equipped skills. They do not revive, use items or choose gear. Default first skills except Druid uses Thornshot. Stage 8 includes its boss wave. Four-minute timeouts count as failures. Higher stages start with fresh base gear and no town training, so their failures do not represent normal geared progression. Deterministic terrain, identifiers and seeds allow before/after tuning comparisons.

| Stage / lineup | Clears | Median clear s | Hero damage | Healing | Wards | Boost assistance | Hero HP lost | Summon damage | Summon HP absorbed | Summon deaths/spawns | Ends before Ult |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1: Knight | 2/2 | 10.6 | 408 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 2/2 |
| 1: Knight + Archer | 2/2 | 14.5 | 1087 | 0 | 0 | 193 | 0 | 0 | 0 | 0/0 | 4/4 |
| 1: Knight + Archer + Healer | 2/2 | 17.1 | 1677 | 10 | 11 | 251 | 10 | 0 | 0 | 0/0 | 0/6 |
| 1: Knight + Archer + Healer + Wizard | 2/2 | 19.3 | 3051 | 59 | 33 | 648 | 59 | 0 | 0 | 0/0 | 0/8 |
| 1: Wizard | 2/2 | 11.8 | 408 | 0 | 0 | 133 | 0 | 0 | 0 | 0/0 | 2/2 |
| 1: Wizard + Knight | 2/2 | 15.1 | 1087 | 0 | 11 | 96 | 23 | 0 | 0 | 0/0 | 2/4 |
| 1: Wizard + Knight + Archer | 2/2 | 14.2 | 1664 | 0 | 8 | 359 | 8 | 0 | 0 | 0/0 | 3/6 |
| 1: Wizard + Knight + Archer + Healer | 2/2 | 18.7 | 3056 | 51 | 24 | 649 | 55 | 0 | 0 | 0/0 | 0/8 |
| 1: Archer | 2/2 | 11.4 | 408 | 0 | 0 | 147 | 0 | 0 | 0 | 0/0 | 2/2 |
| 1: Archer + Knight | 2/2 | 14.3 | 1079 | 0 | 0 | 182 | 0 | 0 | 0 | 0/0 | 2/4 |
| 1: Archer + Knight + Healer | 2/2 | 17.0 | 1676 | 16 | 18 | 251 | 16 | 0 | 0 | 0/0 | 0/6 |
| 1: Archer + Knight + Healer + Wizard | 2/2 | 17.3 | 3048 | 65 | 33 | 679 | 69 | 0 | 0 | 0/0 | 0/8 |
| 1: Cleric | 2/2 | 23.6 | 400 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/2 |
| 1: Cleric + Knight | 2/2 | 19.2 | 1068 | 6 | 0 | 0 | 6 | 0 | 0 | 0/0 | 0/4 |
| 1: Cleric + Knight + Archer | 2/2 | 15.9 | 1664 | 4 | 4 | 282 | 4 | 0 | 0 | 0/0 | 0/6 |
| 1: Cleric + Knight + Archer + Healer | 2/2 | 20.9 | 3068 | 47 | 19 | 535 | 47 | 0 | 0 | 0/0 | 0/8 |
| 1: Rogue | 2/2 | 10.9 | 408 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 2/2 |
| 1: Rogue + Knight | 2/2 | 13.9 | 1091 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 4/4 |
| 1: Rogue + Knight + Archer | 2/2 | 13.6 | 1681 | 0 | 4 | 171 | 4 | 0 | 0 | 0/0 | 3/6 |
| 1: Rogue + Knight + Archer + Healer | 2/2 | 16.5 | 3054 | 32 | 19 | 319 | 53 | 0 | 0 | 0/0 | 0/8 |
| 1: Druid (lightning_bird/ice_bear) | 2/2 | 11.9 | 276 | 0 | 0 | 0 | 0 | 132 | 11 | 0/2 | 2/2 |
| 1: Druid + Knight (lightning_bird/ice_bear) | 2/2 | 15.3 | 897 | 0 | 4 | 0 | 15 | 182 | 0 | 0/3 | 2/4 |
| 1: Druid + Knight + Archer (lightning_bird/ice_bear) | 2/2 | 15.9 | 1526 | 0 | 4 | 179 | 3 | 146 | 21 | 0/3 | 3/6 |
| 1: Druid + Knight + Archer + Healer (lightning_bird/ice_bear) | 2/2 | 19.6 | 2825 | 55 | 50 | 370 | 59 | 251 | 66 | 0/4 | 0/8 |
| 1: Bard | 2/2 | 17.0 | 408 | 0 | 0 | 114 | 0 | 0 | 0 | 0/0 | 0/2 |
| 1: Bard + Knight | 2/2 | 15.9 | 1091 | 0 | 0 | 251 | 0 | 0 | 0 | 0/0 | 2/4 |
| 1: Bard + Knight + Archer | 2/2 | 14.6 | 1661 | 0 | 4 | 456 | 4 | 0 | 0 | 0/0 | 3/6 |
| 1: Bard + Knight + Archer + Healer | 2/2 | 15.7 | 3067 | 41 | 12 | 805 | 60 | 0 | 0 | 0/0 | 0/8 |
| 1: Healer | 2/2 | 30.7 | 408 | 0 | 0 | 0 | 0 | 0 | 0 | 0/0 | 0/2 |
| 1: Healer + Knight | 2/2 | 17.7 | 1080 | 3 | 3 | 0 | 3 | 0 | 0 | 0/0 | 0/4 |
| 1: Healer + Knight + Archer | 2/2 | 16.8 | 1664 | 4 | 4 | 298 | 4 | 0 | 0 | 0/0 | 0/6 |
| 1: Healer + Knight + Archer + Wizard | 2/2 | 18.3 | 3064 | 62 | 12 | 690 | 66 | 0 | 0 | 0/0 | 0/8 |
| 8: Knight | 2/2 | 40.2 | 2409 | 0 | 22 | 0 | 23 | 0 | 0 | 0/0 | 0/2 |
| 8: Knight + Archer | 2/2 | 45.1 | 5651 | 0 | 58 | 1001 | 83 | 0 | 0 | 0/0 | 0/4 |
| 8: Knight + Archer + Healer | 2/2 | 73.1 | 9588 | 348 | 222 | 1492 | 498 | 0 | 0 | 0/0 | 0/6 |
| 8: Knight + Archer + Healer + Wizard | 2/2 | 78.3 | 14670 | 416 | 296 | 2741 | 476 | 0 | 0 | 0/0 | 0/8 |
| 8: Wizard | 2/2 | 43.9 | 2409 | 0 | 0 | 797 | 21 | 0 | 0 | 0/0 | 0/2 |
| 8: Wizard + Knight | 2/2 | 49.4 | 5622 | 0 | 108 | 851 | 191 | 0 | 0 | 0/0 | 0/4 |
| 8: Wizard + Knight + Archer | 2/2 | 55.0 | 9603 | 0 | 131 | 2031 | 124 | 0 | 0 | 0/0 | 0/6 |
| 8: Wizard + Knight + Archer + Healer | 2/2 | 78.0 | 14654 | 294 | 150 | 2708 | 294 | 0 | 0 | 0/0 | 0/8 |
| 8: Archer | 2/2 | 38.3 | 2409 | 0 | 0 | 867 | 19 | 0 | 0 | 0/0 | 0/2 |
| 8: Archer + Knight | 2/2 | 45.4 | 5630 | 0 | 59 | 964 | 94 | 0 | 0 | 0/0 | 0/4 |
| 8: Archer + Knight + Healer | 2/2 | 70.2 | 9603 | 382 | 266 | 1482 | 404 | 0 | 0 | 0/0 | 0/6 |
| 8: Archer + Knight + Healer + Wizard | 2/2 | 76.7 | 14649 | 400 | 209 | 2754 | 400 | 0 | 0 | 0/0 | 0/8 |
| 8: Cleric | 2/2 | 100.3 | 2373 | 26 | 0 | 0 | 26 | 0 | 0 | 0/0 | 0/2 |
| 8: Cleric + Knight | 2/2 | 67.7 | 5624 | 194 | 152 | 0 | 194 | 0 | 0 | 0/0 | 0/4 |
| 8: Cleric + Knight + Archer | 2/2 | 67.7 | 9593 | 371 | 248 | 1380 | 373 | 0 | 0 | 0/0 | 0/6 |
| 8: Cleric + Knight + Archer + Healer | 2/2 | 94.7 | 14652 | 406 | 217 | 1740 | 406 | 0 | 0 | 0/0 | 0/8 |
| 8: Rogue | 2/2 | 37.5 | 2409 | 0 | 0 | 0 | 57 | 0 | 0 | 0/0 | 0/2 |
| 8: Rogue + Knight | 2/2 | 45.9 | 5655 | 0 | 204 | 0 | 252 | 0 | 0 | 0/0 | 0/4 |
| 8: Rogue + Knight + Archer | 2/2 | 51.5 | 9613 | 0 | 175 | 1102 | 232 | 0 | 0 | 0/0 | 0/6 |
| 8: Rogue + Knight + Archer + Healer | 2/2 | 80.3 | 14659 | 504 | 254 | 1684 | 692 | 0 | 0 | 0/0 | 0/8 |
| 8: Druid (lightning_bird/ice_bear) | 2/2 | 39.0 | 1513 | 0 | 0 | 0 | 0 | 896 | 410 | 6/6 | 0/2 |
| 8: Druid + Knight (lightning_bird/ice_bear) | 2/2 | 53.3 | 4733 | 0 | 32 | 0 | 141 | 897 | 495 | 6/6 | 0/4 |
| 8: Druid + Knight + Archer (lightning_bird/ice_bear) | 2/2 | 57.1 | 8267 | 0 | 139 | 1240 | 199 | 1326 | 555 | 6/8 | 0/6 |
| 8: Druid + Knight + Archer + Healer (lightning_bird/ice_bear) | 2/2 | 74.3 | 12955 | 415 | 210 | 1511 | 441 | 1742 | 797 | 9/11 | 0/8 |
| 8: Bard | 1/2 | 88.0 | 1702 | 0 | 0 | 373 | 113 | 0 | 0 | 0/0 | 0/2 |
| 8: Bard + Knight | 2/2 | 53.5 | 5640 | 0 | 60 | 1336 | 192 | 0 | 0 | 0/0 | 0/4 |
| 8: Bard + Knight + Archer | 2/2 | 76.2 | 9613 | 0 | 273 | 2790 | 425 | 0 | 0 | 0/0 | 0/6 |
| 8: Bard + Knight + Archer + Healer | 2/2 | 81.7 | 14662 | 568 | 199 | 3397 | 734 | 0 | 0 | 0/0 | 0/8 |
| 8: Healer | 2/2 | 145.5 | 2393 | 114 | 0 | 0 | 114 | 0 | 0 | 0/0 | 0/2 |
| 8: Healer + Knight | 2/2 | 70.7 | 5653 | 236 | 64 | 0 | 236 | 0 | 0 | 0/0 | 0/4 |
| 8: Healer + Knight + Archer | 2/2 | 69.7 | 9603 | 517 | 303 | 1451 | 543 | 0 | 0 | 0/0 | 0/6 |
| 8: Healer + Knight + Archer + Wizard | 2/2 | 81.1 | 14664 | 358 | 250 | 2648 | 410 | 0 | 0 | 0/0 | 0/8 |
| 16: Knight | 2/2 | 58.8 | 3656 | 0 | 80 | 0 | 107 | 0 | 0 | 0/0 | 0/2 |
| 16: Knight + Archer | 2/2 | 72.4 | 8419 | 0 | 150 | 1277 | 200 | 0 | 0 | 0/0 | 0/4 |
| 16: Knight + Archer + Healer | 2/2 | 121.0 | 15177 | 785 | 434 | 2377 | 1018 | 0 | 0 | 0/0 | 0/6 |
| 16: Knight + Archer + Healer + Wizard | 1/2 | 99.5 | 13907 | 279 | 240 | 2937 | 744 | 0 | 0 | 0/0 | 0/8 |
| 16: Wizard | 2/2 | 66.9 | 3663 | 0 | 0 | 1135 | 0 | 0 | 0 | 0/0 | 0/2 |
| 16: Wizard + Knight | 2/2 | 92.5 | 8429 | 0 | 145 | 1451 | 243 | 0 | 0 | 0/0 | 0/4 |
| 16: Wizard + Knight + Archer | 2/2 | 95.6 | 15211 | 0 | 215 | 3404 | 365 | 0 | 0 | 0/0 | 0/6 |
| 16: Wizard + Knight + Archer + Healer | 2/2 | 141.7 | 22700 | 894 | 607 | 4623 | 1375 | 0 | 0 | 0/0 | 0/8 |
| 16: Archer | 2/2 | 59.7 | 3669 | 0 | 0 | 1273 | 13 | 0 | 0 | 0/0 | 0/2 |
| 16: Archer + Knight | 2/2 | 89.8 | 8405 | 0 | 231 | 1791 | 334 | 0 | 0 | 0/0 | 0/4 |
| 16: Archer + Knight + Healer | 1/2 | 92.8 | 15154 | 324 | 264 | 2968 | 689 | 0 | 0 | 0/0 | 0/6 |
| 16: Archer + Knight + Healer + Wizard | 1/2 | 100.0 | 16760 | 551 | 251 | 3778 | 1016 | 0 | 0 | 0/0 | 0/8 |
| 16: Cleric | 2/2 | 151.1 | 3624 | 208 | 0 | 0 | 208 | 0 | 0 | 0/0 | 0/2 |
| 16: Cleric + Knight | 1/2 | 84.1 | 7284 | 348 | 241 | 0 | 583 | 0 | 0 | 0/0 | 0/4 |
| 16: Cleric + Knight + Archer | 2/2 | 131.8 | 15178 | 647 | 457 | 2589 | 1040 | 0 | 0 | 0/0 | 0/6 |
| 16: Cleric + Knight + Archer + Healer | 1/2 | 116.5 | 22109 | 1424 | 426 | 2479 | 1789 | 0 | 0 | 0/0 | 0/8 |
| 16: Rogue | 1/2 | 52.5 | 2350 | 0 | 0 | 0 | 144 | 0 | 0 | 0/0 | 0/2 |
| 16: Rogue + Knight | 2/2 | 72.0 | 8409 | 0 | 171 | 0 | 309 | 0 | 0 | 0/0 | 0/4 |
| 16: Rogue + Knight + Archer | 1/2 | 75.8 | 13270 | 0 | 181 | 1764 | 534 | 0 | 0 | 0/0 | 0/6 |
| 16: Rogue + Knight + Archer + Healer | 2/2 | 165.2 | 22706 | 623 | 406 | 3301 | 1125 | 0 | 0 | 0/0 | 0/8 |
| 16: Druid (lightning_bird/ice_bear) | 2/2 | 58.6 | 2321 | 0 | 0 | 0 | 56 | 1348 | 581 | 5/9 | 0/2 |
| 16: Druid + Knight (lightning_bird/ice_bear) | 2/2 | 76.5 | 6858 | 0 | 113 | 0 | 306 | 1542 | 963 | 12/15 | 0/4 |
| 16: Druid + Knight + Archer (lightning_bird/ice_bear) | 2/2 | 96.1 | 13599 | 0 | 261 | 1956 | 548 | 1587 | 1342 | 17/18 | 0/6 |
| 16: Druid + Knight + Archer + Healer (lightning_bird/ice_bear) | 1/2 | 96.7 | 15458 | 205 | 261 | 1331 | 650 | 2207 | 1511 | 19/21 | 0/8 |
| 16: Bard | 0/2 | — | 1473 | 0 | 0 | 364 | 150 | 0 | 0 | 0/0 | 0/2 |
| 16: Bard + Knight | 1/2 | 101.3 | 5933 | 0 | 313 | 797 | 446 | 0 | 0 | 0/0 | 0/4 |
| 16: Bard + Knight + Archer | 1/2 | 82.0 | 12623 | 0 | 201 | 3281 | 444 | 0 | 0 | 0/0 | 0/6 |
| 16: Bard + Knight + Archer + Healer | 2/2 | 159.1 | 22745 | 706 | 412 | 4594 | 1116 | 0 | 0 | 0/0 | 0/8 |
| 16: Healer | 1/2 | 187.2 | 3565 | 354 | 0 | 0 | 354 | 0 | 0 | 0/0 | 0/2 |
| 16: Healer + Knight | 2/2 | 111.2 | 8405 | 458 | 364 | 0 | 458 | 0 | 0 | 0/0 | 0/4 |
| 16: Healer + Knight + Archer | 2/2 | 106.9 | 15198 | 772 | 530 | 2191 | 835 | 0 | 0 | 0/0 | 0/6 |
| 16: Healer + Knight + Archer + Wizard | 2/2 | 129.1 | 22724 | 581 | 486 | 4579 | 1008 | 0 | 0 | 0/0 | 0/8 |
| 1: Druid (fire_wolf/nature_golem) | 2/2 | 13.2 | 258 | 0 | 0 | 0 | 0 | 150 | 52 | 0/2 | 2/2 |
| 8: Druid (fire_wolf/nature_golem) | 2/2 | 39.5 | 1564 | 0 | 0 | 0 | 0 | 845 | 704 | 6/8 | 0/2 |
| 16: Druid (fire_wolf/nature_golem) | 2/2 | 63.4 | 2504 | 0 | 0 | 0 | 27 | 1170 | 1165 | 10/12 | 0/2 |

Columns total both seeds, including failures. Raw JSON separates every participant, includes summon survival durations and combined uptime. Healing counts actual HP restored, including revives; wards credit their caster for actual HP saved after armor. Boost assistance is the extra HP removed by a supported hero, already included in that hero's damage; do not sum those columns. Summon HP absorbed is actual HP lost, not an estimate of damage a hero would have taken. The visible Run stats remain the five requested overall totals.

Live reports append to `data/balance.jsonl`. Validate tuning with matched human runs (stage, party size, gear and loadout); these bots cannot establish that every hero is balanced. See COMBAT_BALANCE_NOTES.md for tuning evidence and remaining limits.
