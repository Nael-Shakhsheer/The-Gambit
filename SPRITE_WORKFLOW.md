# Sprite creation workflow

Saved on 2026-10-06 after the approved Cave Troll concept and animation sheet.
The user prefers exact horizontal mirrors for eligible directions so future
sprites need fewer generated views. Preserve this choice for future renders.

## Cave Spider follow-up

The next creature is retained under `art/cave-spider/`. Its `WORKFLOW.md`
and `PROMPTS.txt` record the exact process. One generated five-direction
source sheet supplied South, Southeast, East, Northeast and North; the
other three directions are exact horizontal mirrors. Measuring occupied
row bounds avoided clipping feet or importing fragments from adjacent rows.
Use equal scaling on both axes, and a smaller detached-fragment threshold
for thin legs (3 pixels here, rather than the troll's 12).

`art/exports/Cave-Spider-Sprite-Import-v1.zip` includes the finished sheet,
metadata, instructions, an importer that preserves Troll, and creation
sources. Exact mirrors, distinct frames, extracted archive integrity,
checksums, baseline/Troll-compatible imports, backups, repeat imports,
no-write checks and JavaScript syntax passed. The spider has not been
imported into the actual game or evaluated in live gameplay.

## Files from this session

- Approved design: `art/samples/cave-troll-concept-v1.png`
- Concept prompt: `art/samples/cave-troll-concept-v1-prompt.txt`
- Final sample sheet: `art/samples/cave-troll-spritesheet-v1.png`
- Frame metadata: `art/samples/cave-troll-spritesheet-v1.json`
- Exact generation prompts: `art/samples/cave-troll-spritesheet-v1-prompts.txt`
- Rebuild script: `art/samples/build-troll-sheet.ps1`
- Retained source images: `art/samples/source/`

These art samples are not imported into the game's renderer. Cave Troll still
uses canvas art. Do not represent the sheet as tested in gameplay.

## Use this process for the next creature

1. Generate and approve one character pose first. Use existing Knight,
   Minotaur and Serpent sheets as style references, plus the approved troll
   when useful. Match their camera, dark outlines, compact proportions,
   limited palette and discrete pixel shading. Request actual transparency.
2. Preserve that approved design as the identity reference for animation.
3. Generate only five source directions: South, Southeast, East, Northeast,
   North. For a faster first preview, start with South, East and North, then
   add the two diagonal strips. Generate small strips rather than repeatedly
   attempting a full eight-direction sheet.
4. Use nine frames per source direction: 0-2 idle, 3-5 movement, 6-8 attack.
   Specify anticipation, swing and impact for attacks; specify alternating
   foot placement for movement. Keep each row's facing fixed throughout.
5. Inspect source poses before assembly. North must show the back throughout;
   Northeast must show the back and right side. Verify the weapon stays
   identifiable, feet are inside cells, and movement frames differ visibly.
6. Assemble exact cells with ordinary image operations. Generate the new
   artwork with imagegen, then use exact horizontal flips for the mirrors
   the user explicitly requested:
   - East -> West
   - Southeast -> Southwest
   - Northeast -> Northwest
   Keep North and South separate. Mirror the complete padded cell after
   normalization so opposite frames align perfectly.
7. Save the PNG, metadata, source images, exact prompts and assembly script
   together in the project. Make the source map and outputs relative to the
   script/project, with no original computer paths as requirements.

Horizontal mirroring intentionally swaps the weapon hand and asymmetric
shoulder details. The user authorized mirroring in this session. If a future
design requires fixed asymmetric markings or legible lettering, generate
that particular opposite direction separately.

## Sheet layout used here

The final PNG is **612 x 612**, a **9 x 9** grid of **68 x 68** cells.
Each source cell is sampled with nearest-neighbor interpolation into a
**48 x 48** drawing area, with **10 pixels of padding** on every side.
This is the delivered sample geometry; the generated source images were
larger and were not guaranteed to use a literal 48-pixel drawing grid.

Row 0 contains eight static facing previews and one transparent blank cell.
Rows 1-8 contain animation strips in the game's established order:

| Row | Direction | Source |
| --- | --- | --- |
| 1 | South | Separate source |
| 2 | Southeast | Separate source |
| 3 | East | Separate source |
| 4 | Northeast | Separate source |
| 5 | North | Separate source |
| 6 | Northwest | Horizontal mirror of row 4 |
| 7 | West | Horizontal mirror of row 3 |
| 8 | Southwest | Horizontal mirror of row 2 |

Every animation row uses columns **0-2 idle**, **3-5 walk**, **6-8 attack**.

The script removes alpha below 32 and detached components smaller than 12
pixels after scaling, to remove fragments from adjacent generated cells.
Review this cleanup threshold for creatures with detached effects or very
small separated body parts. It runs before mirroring.

## Rebuild this sample

On Windows with PowerShell 7, from the project directory:

```powershell
& './art/samples/build-troll-sheet.ps1'
```

The script uses System.Drawing, retained local PNGs, relative paths and no
network access. Rebuilding requires no additional image generation.
For a new creature, reuse the layout and mirror operations, change the input
files and source row map, then save its own script and output filenames.
This optional art tooling does not change the Python game's requirements.

## Import package

`art/exports/Cave-Troll-Sprite-Import-v1.zip` contains the final sheet as
`static/sprites/troll-idle.png`, matching JSON metadata, `import_troll.py`,
`IMPORT.md`, this workflow and the retained `art/samples/` files. The importer
backs up existing files and makes the four required renderer edits. It can
check compatibility without writing, and repeated imports are idempotent.
The package has been checked after extraction, including checksums, asset
copying, backups, repeat imports and JavaScript syntax in an isolated copy.
The actual game has not been imported or checked in live gameplay.

After edits to the source art or packaging files, recreate the ZIP with:

```powershell
python art/exports/build_cave_troll_package.py
```

The builder includes PNG/JSON, import instructions and tool, generation
sources, and a checksum manifest, then checks ZIP integrity. Revalidate the
importer if its code or the game renderer changes.

## Limits observed in this session

Two generated full eight-direction sheets repeated or mixed directions.
The four-direction source had clearer cardinal poses. The delivered sample
uses South, East and North from that source, plus Southeast and Northeast
from the eight-direction draft. Its diagonal angles are approximate and
animation timing/pose quality have not been evaluated in gameplay.

Treat generation as a source of poses. Use deterministic assembly for exact
grids, transparency cleanup and mirrors. Inspect every frame before importing
a future sprite, and use explicit frame ranges in the renderer: its current
non-Minotaur defaults differ from this sample's 3/3/3 organization.

## Wolf, Druid and summon batch (2026-10-06)

The six-asset batch is retained in `art/wolf-druid-pack/` with a single
manifest-driven builder: Wolf, Druid, Lightning Bird, Fire Wolf, Ice Bear and
Nature Rock Golem. See that folder's `WORKFLOW.md` and `prompts/` for exact
generation instructions and reusable source assembly. All six use the same
612x612 export and 3/3/3 animation layout. Fire Wolf references the gray Wolf
source to keep its canine proportions. Lightning Bird requires measured
horizontal separators to prevent extended wings leaking into nearby cells.
Record source row/column bounds in the manifest and rebuild locally; do not
regenerate mirrored directions. Preserve small detached cast effects rather
than applying Troll's more aggressive fragment cleanup to every character.

`art/exports/Wolf-Druid-Summons-Sprite-Import-v1.zip` is the complete handoff.
The retained `art/exports/build_wolf_druid_package.py` recreates it. Its importer
adds six sprite registrations, Wolf enemy mapping, 3/3/3 frame ranges and the
four summon hooks inside existing damage tint. This package has not been
installed in the game by the sprite-generation task.

## Archer, Cleric, Rogue, Bard and Healer batch (2026-10-06)

`art/hero-party-pack/` retains this five-hero batch using the same eight-direction
612x612 export, 68px cells and 3/3/3 frame ranges. Five source directions are
generated and the three eligible opposites are mirrored. Its manifest records
both occupied row bounds and source column gaps. Bard note effects and Rogue
slashes need slightly wider attack crops; one Cleric cast also needs an adjusted
boundary. Use uniform 48/187 scaling and trim empty horizontal margins before
centering crops. The builder measures these bounds in C# for faster rebuilding.

The complete handoff is
`art/exports/Archer-Cleric-Rogue-Bard-Healer-Sprite-Import-v1.zip`, recreated by
`art/exports/build_hero_party_package.py`. Sources, exact prompts, art review,
preview, crop manifest and rebuild script are inside the package. The importer
adds the five loader registrations and general idle/move/attack frame ranges.
It preserves existing lists, including the Wolf/Druid pack if already imported.
The art is prepared for import; this task has not installed it into the game.

## Town NPCs, eight villagers and floating chest (2026-10-06)

`art/town-npc-pack/` retains Merchant, helmetless regal armored Guildmaster,
Alchemist, distinctive villager-like Innkeeper and eight villager variants.
Generate Villager 01 once, then edit that same source separately for each
remaining variant. Preserve its camera, compact proportions, grid and poses;
change clothing, skin, hair and simple headwear. All exact prompts are retained.

Character layout matches the 612x612/68px eight-direction convention, but its
three frame groups are idle, walk and peaceful gesture. Explicit metadata and
an independent town loader keep these separate from combat attack animation.
Generate five directions and mirror three eligible opposites after cleanup.
Use measured row/column bounds, uniform nearest-neighbor sampling and horizontal
alpha bounds trimming to keep props inside cells. The manifest and PowerShell
builder retain the measured crops for deterministic rebuilds.

Chest uses a 612x136 sheet: nine closed poses and nine open poses, 160ms each.
Bake `[0,-2,-3,-3,-1,1,3,3,2]` vertical offsets into the two loops. No opening
transition is included. `build-chest-animation.ps1` composes the exported cells
into transparent animated PNG previews at 3x nearest-neighbor scale, retaining
the same timing. See WORKFLOW.md and ASSET_REVIEW.json in the source folder.

Complete handoff: `art/exports/Town-NPCs-Villagers-Floating-Chest-Sprite-Import-v1.zip`.
Rebuild with `art/town-npc-pack/build-sheets.ps1` and then
`python art/exports/build_town_npc_package.py`. The package includes sources,
prompts, manifests, export metadata, previews, art builders, importer, runtime
loader, instructions and checksums. Assets were inspected; importer execution
and live gameplay were not evaluated, and this batch is not installed.
