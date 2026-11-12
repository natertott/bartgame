# Regional traversal and retained compatibility court

The current regional integration is described in [Regional mechanisms](REGIONAL_MECHANISMS.md). The court descriptions below document the retained compatibility layouts; normal content is placed by the Forest/Cream generator.

## Current regional qualification

C4 source `51880a55e6ecf86728f3a0923e5547e7bdeed5a0` passes 23,487 regional
host checks across both modules, including 8,382 mobility checks, plus 1,511
retained-course traversal checks. A field stamp is transactional: the real
post-stamp route validator must pass, or its ground/overlay/underlay is restored.

The final 167/167 native bundle uses fresh seeded cores and requires a living
player in GS_PLAY at every substantive result. It proves actual outdoor cart
boarding/wet-rail ride/dry dismount, upper bridge and lower underpass routes,
controlled parachute descent, refusal of unearned caches and once-only
100/20-gilt claims. Seed 15 also proves the parachute on Cream 15's actual
field. All three interior templates remain dry for 120 frames without
Flippers, then return to their actual parent by southward walking. The cart
channel ends above the ordinary south arrival/return bank.

Equipment/ammunition/skills, standing/navigation, player protection and a
decrease to 0 gilt before isolated reward accounting are disclosed fixtures.
No player HP or completion/fusion/claim flags are assigned. The
[main native report](../../../regional-handoff-review/validation/mechanisms/report.json),
[cart field report](../../../regional-handoff-review/validation/mechanisms-fields/report.json)
and [Cream field report](../../../regional-handoff-review/validation/mechanisms-cream/report.json)
carry the traces; [Regional mechanisms](REGIONAL_MECHANISMS.md) records the
full ROM/harness identity. Workspace originals are under
`/workspace/setup/regional-integration/mechanisms-live-c4/`.
Earlier depleted-health diagnostic runs are invalidated.

## Historical compatibility court

The Challenge desk's appended Traversal Court supplies three real movement
systems without changing any existing Drain/Forest/Cream room artwork.
`handoff_events.c` exclusively dispatches its build, interaction, movement,
collision, update and draw hooks, avoiding duplicate simulation. Player floor
and priority hooks apply only while this court is active.

- A brass minecart follows four connected rail segments using fixed-point
  motion. A boards it; A again requests dismount at the next round station.
  Both station exits are dry. Riding consumes ordinary player movement and
  item input; dismount restores walking and a valid safe-ground history.
- R on the western arrow shelf launches an original silk parachute. Left/right
  steers within the landing shelf, up slows descent, down speeds it and A folds
  it for a faster drop. The height, steering bounds, lower landing and control
  restoration are mechanical state, not a sprite-only imitation of falling.
- A slatted bridge has two collision planes at the same screen coordinates.
  The end ramps enter the upper deck, whose side rails prevent lateral leaks.
  The middle bank remains a distinct walkable lower underpass. Raised feet
  suppress the underlying water hazard; upper Bloom uses OBJ priority1 so the
  BG1 deck stays behind Bloom and priority0 HUD/dialogue stays readable.

Red kinstone fusion also inserts a physical bridge to the optional island's
100-gilt cache. Its claimed bit persists in the existing per-run annex
completion array; rebuilding the court cannot farm the prize. Ordinary paths
and the permanent southern exit remain available without fusion.

`art/handoff_mobility.py` appends17 native16×16 metatiles and10 original32×32
OBJ frames. All use unchanged existing `lh_earth`, `lh_element` and gear banks.
Horizontal material clusters, sparse upper-left metal highlights, open bridge
slats and a pale recognizable parachute preserve the common art direction.
The old Bloom sprite supplies the rider and hanging body; it is not repainted.

`tools/handoff_mobility_host.py` compiles the actual C movement/course module
with explicit host input/room fixtures. It passes1,511 checks for both bridge
planes, priority, hazard masks, cardinals and safe cart stops, all descent
controls/bounds, once-only fusion rewards, and inert hooks outside the new
court. This qualifies movement/state logic. Native emulator input, visual and
performance qualification remains a separate integration check.


## Final native controls

Exact release3 SHA-256
`b348cf4d628aee1abb9b71d8885a9f04094332c5252490ff2dd8f8e7cd0bf1b8`
passes32mGBA controls in `tools/mobility_native_review.py`. The upper bridge
uses a real support provider in both ordinary and legacy floor/swim logic.
With Flippers owned, A fires a bow above confirmed underlying water; below,
the same A input dives and consumes no arrow. Unsupported lower water still
drowns. These opposite controls caught and corrected a real double-floor-check
regression before publishing. B/DrainCap and L/Boots cannot overwrite cart
movement. Actual fusion, prize, hazard death/save and coldContinue also pass.

Only player navigation, explicit temporary gear/ingredient fixtures and private
SRAM are assigned. Gates, completions, AI, terrain, OAM/VRAM, palettes and PPU
pixels are never assigned. Temporary gear is restored before the genuine death
checkpoint. PNG/GIFs are untouched native framebuffer captures.
