# Native repeated-tree review scene

This study covers individual trees, not canopy redesign or production forest
placement. The user's two requested extents are interpreted as 2×2 and 1×2
16-pixel cells: 32×32 and 16×32 native pixels. Both are legal GBA storage
rectangles (uploaded *GBA Sprite Art Guide*, p.2). A visible canvas is distinct
from collision, as the guide explicitly explains on pp.8 and11.

The twelve native pictures comprise two silhouette varieties per size, each
healthy, sick or dead. They use one shared16-ink RGB555 bank, so all three
states can appear together. Original normal forest tiles, palette banks and
canopy remain the profile29 context; the new study atlas is separate in ROM.
It is loaded only by the explicitly requested diagnostic function.

`tree_study_begin` is retained in the profile30 link with an undefined-symbol
linker root. No normal game flow calls it. Older profiles omit the translation
unit entirely; even an empty object can perturb ARM/Thumb veneer order. The
normal profile30 game does not automatically enter the review scene.

The mGBA harness sets `gTreeStudyRequest` and `gTreeStudyPending`, then calls the
real ROM function through the existing VBlank callback mechanism. It never
paints screenshot pixels or injects a substitute image. Requests0–2 render
the twelve-image catalog over actual native grass, dirt path or sick grass;
requests3–5 render repeated mixed trees over those same floors. These rooms
are deliberate diagnostic fixtures, not naturally generated forest encounters.

The function creates a15×10-cell room, loads the normal forest palette banks,
then draws the compact native floor/tree atlas on BG2/BG1. Tree palette slot11
is the last allowed world bank; interface palettes remain reserved. Ordinary
world tile/palette animation is disabled because its original tile destinations
belong to the temporarily replaced atlas. Normal area loading restores the
world atlas. Menu return is outside this initial fixture's review scope.

Every tree has a separate declared 16×8-pixel root footprint on the 8-pixel
collision grid. Its 32×32 or 16×32 canvas is not a solid collision rectangle.
These fixture footprints do not resize existing game colliders. A profile30-only
priority hook sorts ordinary actors in front once their ground contact passes
a tree's authored local y=30 anchor, and behind it before that point. Existing native-pixel
vegetation visibility protects Bloom if he overlaps the picture. One regular
BG plane cannot independently sort fragments against two different overlapping
tree rows; the fixture avoids overlapping tree rectangles and does not claim a
finished procedural multi-object sorting system (guide p.9). The repeated grove reserves a clear center
corridor for ordinary movement and native-scale context.

`gTreeStudyInfo` records the request, layout, floor, picture count, resident
tile count and palette slot. `gTreeStudyPlacements` records every native
rectangle and8-pixel root rectangle. Exact BG1 entries, BG2 floor entries,
palette contents and actual player pixels remain independently inspectable.
Those checks support import fidelity; they do not prove that viewers like the
art or that every production forest layout is already redesigned.

`tiles_load` clears the diagnostic sorting flag, so a later real area load
uses the original game rules and restores the prior tile-animation flag.
That hook and all new code are compiled only in
profile30; earlier profiles retain their exact original source behavior.

An initial diagnostic attempt rendered no trees because `sprites_reset`
called `interactive_room_reset`, which rendered the ordinary room after the
private tree maps had already been installed. That failed output is not a
review artifact. The corrected sequence completes ordinary room and sprite
initialization first, then installs the compact atlas and exact native maps.
Actual hardware now contains all 144 tree map entries, including transparent
ones. The review harness checks those entries, all native BG2 floor entries,
the root grid and a scanline0/160 paired body/guard proof before qualification.

Six catalog/grove substrate contexts and two ordinary walk-around sequences
exercise behind, alongside and in-front relationships plus a push against a
root. Recorded action poses come from game input, not debug frame assignment.
Pillow's merging of duplicate idle GIF frames is handled by preserving their
combined inspection hold time; full-rate MP4s remain separate viewing copies.
