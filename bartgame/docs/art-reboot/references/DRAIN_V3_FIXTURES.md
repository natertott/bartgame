# Drain third-pass fixtures — native source review

Latest user feedback is the direct source: round gate language of #1/#4,
ladder construction of #1, market cues of #1/#2, wizard-corner atmosphere of
#1/#2/#5 with #4 damage; remove ambiguous storage/plumbing blobs and rootlike
water. These are exploratory Drain options, not a global style selection.

`art/sewer_v3_fixtures.py` installs nine native indexed fixture painters into
the opt-in concept painter. All final drawings use palette indices 0..15 on
the original 480x320 source map; runtime slices original 16x16 tile IDs. No
objects, movement rules, collision, trigger, glitter, Bloom or placements change.

- Ladder: #1-style round frame in five hardware/decay treatments; strong metal
  rails/rungs; ONE solid ivory up-arrow 11x11 on a dark 15x15 sign. Actual-run
  review identified the previous arrow's y19 placement under the 24px HUD.
  New sign: x160..174,y32..46 beside lane in original right-jamb overlay;
  x144..159 remains visibly open. This is runtime evidence, not source advice.
- Cistern: round gold frame/barred cavity retained; bolted, stone-shouldered,
  chipped/bent and worn-grand variants. Water is a broad straight sheet with
  broken downward-moving light packets, detached spray, pale impact foam and
  broken expanding pool arcs. Five pours: broad single; split spillways;
  narrow recessed; wider broken lip; narrow with spreading apron. No twisting
  stems. First review found a solid pillar effect; added broken fringe/foam
  and coordinated contrasting aqua/silver palette with terrain agent.
- Small outlet: short connected brass elbow, circular black mouth, obvious
  lower lip, liquid beginning at the lip and impact ripple in actual stream.
  Descriptive plumbing rather than a gold icon or implied new interaction.
- Markets: striped low canvas, patched scallops, salvage-board roof, ragged
  stripes and once-fine torn roll canopy. Separate jars/tied sack/tabletop and
  differing joinery. Existing frog and front-counter occlusion stay anchored.
- Wizard corners: worn rug silhouettes, broken brass border, chipped shelf,
  varying candles and simple center marks. Damage exposes gray floor rather
  than false pits. Purple actor remains separate; no extra BG bank.
- Storage: timber lids show planks, joins and braces. Barrel has a warm wooden
  bunged lid, vertical staves, thin dull hoops. Terrain pass moved slime from
  the identity-carrying lid down to its foot; pipe shaft stays legible.

Existing G01–G18 guide native silhouette/form, directional planes, material
highlights, quiet field/functional hierarchy and clean pixel runs. No new
outside source was read or claimed in this iteration.

Local proofs: fixtures-first-pass.png exposed pillar-like falls;
fixtures-water-ladder-revised.png/.gif show corrected fringe/foam and arrow.
Native asset assemblies at 2x nearest-neighbor, NOT emulator captures. Fixture
API exercised for five styles x eight phases, inks <=15. Runtime/packed proof
is recorded separately by the parent/runtime team.

Tradeoff: pouring sheets still need motion to fully communicate water. The
body is intentionally continuous rather than detached decorative pixels. The
round architecture stays related between styles because that is the user's
preferred construction.

## Final alias correction from assembled-room review

The first direct-layer pipe looked legible, but the original reused walkable
IDs erased its upper riser and mouth when the REAL map was assembled. The
fixed layout has unique bank IDs swh_230/231 at (27,9)/(28,9), and a unique
animated stream ID swh_241 at (28,10). The final outlet therefore mounts ON
the bank with a short horizontal connection to the side wall: flange
x448..463,y145..159, dark cavity x452..460,y148..155 and liquid/spray entirely
inside x448..463,y155..175. There is no longer a pretend floor riser.
This keeps the same physical room and uses the existing eight-frame water
slot, with no new object or ID. `fixtures-outfall-alias-corrected.png/.gif`
are rendered from T.full_layers (assembled original map IDs), not direct
private _layers. They visibly retain a round gold pipe mouth and moving water.
