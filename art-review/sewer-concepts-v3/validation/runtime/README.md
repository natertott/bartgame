# Third Drain study: actual mGBA review

Final source: `22b0af6` (full hash in each frozen build record). The superseded
`e354268` pilot remains under `pilot-e354268/`; final publication must use the
new root-level reports and captures.

The independent packed-art audit passes **20,845/20,845** checks. Every native
active tile frame, actor/portrait frame and handrail survives RGB555/4bpp
packing exactly; fixed room physical data, Bloom/Step-and-cut, ambient glitter
and unrelated art remain unchanged. Build-time painter/fixture hashes match
all nine frozen provenance records, including the repaired outlet fixture.

All **88 actual mGBA cases pass 1,280/1,280 runtime checks**: nine room views,
shop and wizard dialogue for each of eight recipes. The added centered cistern
view uses `(240,118)`, camera `(120,14)` and 288 ordinary idle updates. The
sheet and impact metatiles animate in real VRAM using exact ROM frames; the
small outlet's unique `swh_241` allocation also changes through exact ROM
frames in its dedicated right-outfall view. No terrain, action state, pose or
animation-clock writes are used by the camera/standing fixtures.

All idle samples run one update per VBlank; maximum sampled OAM is42/128.
All88 GIFs preserve their exact palette; largest individual color union is66.
Final sewer BG allocation is601,598,603,606,587,600,588,606 /1024 tiles across
recipes1..8, with one area palette bank each. These are sample measurements,
not a worst-case game performance claim.

Native full-context images for all five options and chronological actual
actor/water crops were inspected. The ladder arrow is below the HUD; pale
vertical water, descending streaks, foam and ripples separate flow from the
old dark root shapes. The gold bank outlet now retains its dark round mouth
and falling water in the actual map. Crate lids and barrel staves are clear.
No sampled actor/rail/staff-grip blocker was found. Option4 remains denser and
darker; option5 has more small-paver rhythm; option2 uses split jets. These
are choices for the user rather than a quality score.

Observed pose union is11/15 frog bodies,4/5 heads,5/6 wizard frames and4/4
flames. All authored frames are statically audited and shown in the source
atlas; the recordings are not claimed to activate every pose. Rest/breathe
feet have identical source rows and actual head/body OAM offsets remain
`(8,6)` / `(8,7)`. The counter can hide feet, so source and hardware evidence
are distinguished from direct visual observation.
