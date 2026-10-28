# Native art and emulator verification

Final ROM examined here: SHA-256
`41dc680068c094416e92152d4c22637c10d6a055d2bee63ce7700c419490e92d`.
Frozen comparison: `bbd08678b1e10fb110e562a6374b0242cb8e73affbdd747f033fd0ce99619eee`.
All runtime observations use mGBA 0.10.5. Later release reports must identify
their own ROM hash rather than silently attributing these results to another ROM.

## What the probes establish

`tools/art_reboot_probe.py` passes **6,577/6,577** checks against this final ROM.
It decodes the built ROM, checks all 913 metatile identifiers and physical
contracts, and checks native ownership of all 354 original sprite frames plus
17 small HUD items and six glitter frames. It compares indexed drawings with
the frozen ROM, checks the separate menu illustrations, all interface tiles,
font ownership, six portraits, native title colour count, palette quantization,
hardware sprite shapes, compact character/pickup dimensions and BG budgets.
It also examines actual hardware OAM/OBJ VRAM, held-item grips, north/south
shield depth, arrows at their nocks, naturally spawned small world pickups,
HUD bounds and ambient/OAM limits. The native title contains 27 colours.

Geometric redraw claims have narrow, explicit exceptions. Two `none` sprite
frames and the blank menu illustration remain transparent. Uniform pit/black
fills remain uniform. Nine lowercase letter shapes (`c n o r s u v x z`) and
ten space/punctuation/symbol glyphs retain their primitive bit patterns. Four
straight interface primitives (`UI_SLOT_L`, `UI_ROW_L`, `UI_BUB_JOIN`, `UI_RULE`)
also retain their geometry. They are owned by the new generators and use the
new palettes. This is not a claim that all 97 glyph shapes or all 51 interface
tile bit patterns changed.

The phase-aware `tools/bloom_probe.py` passes **435/435** checks. Its 96 contact
cases cover four facings, three live sword poses, four box edges and inclusive
contact versus one pixel outside. Targets are frozen ordinary enemies; the
local floor fixture removes unrelated hazards. ROM-authored phase geometry
supplies the changing combat bounds. Timing and hardware rendering are also
checked, together with sword pickup gathering, seed deflection, bush cutting,
hurt cancellation, roll protection and queued attack recovery. The sword
retains its 15-update action and 11 damaging updates; its physical region now
follows the visible distal blade/trail rather than the former static envelope.
The test checks AABB combat boundaries; it does not claim per-pixel collision.

`tools/bloom_suite_probe.py` passes **469/469** checks for the broader suite.
Sprite identification reads the ROM's sheet descriptor, so a missing 32×32
Bloom cannot silently skip a check formerly written for a 64×32 sprite.

## Actual-run review coverage

`tools/art_reboot_review.py` produced **171 recorded cases** on this ROM:

- 40 screen clips: title, three Drain views, all 25 generated forest cells,
  cave/hollow/thicket interiors, five enemy species, the Heart fight/victory,
  and death/return dialogue.
- 91 Bloom action clips across Drain, healthy forest, blight and a naturally
  generated cave, plus lift/carry/throw, item acquisition, fall, drowning,
  hurt, death and Drain Cap special cases. All 149 activation checks pass.
- 40 interactive scenery cases, with all 32 interaction activation checks
  passing and no missing cases.

A separate full-Heart camera clip supplements the 171 canonical cases so the
whole naturally spawned boss can be inspected at fighting distance.

These use seeded real runs and ordinary buttons. Position, facing, inventory,
healing and removal of unrelated enemies are disclosed review fixtures.
Generated terrain, chest contents and mystery descriptors are not replaced.
Controlled enemy contact used in special action tests is labelled. PNGs are
exact 240×160 framebuffers; GIFs use nearest-neighbour 2× enlargement and retain
the frames' colours. Filmstrips display chronological emulator frames.

The action trace union reaches **99 of 101 Bloom source frames**. `jump_n` and
`jump_e` are redrawn legacy descriptor entries that the current renderer does
not select: cape jumps use the cape family, and swallowing uses `jump_s`.
They must not be reported as activated animation cases. Unused enum states
`talk` and `frozen`, swimming and sprinting also remain outside implemented
gameplay. Separate interface review covers menus, map, shops and portraits.

## Measured and corrected HUD contact latency

`tools/art_reboot_latency.py` pairs the frozen before/after ROMs with the same
quiet-floor fixture and a valid, ordinarily spawned beetle. It records video
boundaries, actual `gGame.run_frames`, VBlank count, state, HP, damage-active
flag and hardware sword effect. Integration testing found and corrected a
dirty-HUD regression; these are the actual paired measurements:

| ROM / HUD load | Video frames from logical hurt to replacement hardware OAM |
| --- | --- |
| Frozen before `bbd08678` | 1, 1, 1, 1, 1 |
| Superseded candidate `6baf5a3c` | 3, 3, 3, 3, 3 |
| Final `41dc6800`, normal 24 HP | 1 in all 10 trials |
| Final `41dc6800`, maximum 80 HP / ten hearts | 1 in all 10 trials |

Damage becomes inactive immediately at logical hurt in both builds. The old
hardware picture remains during preparation, and the sword effect is absent
at the first replacement OAM upload. The superseded candidate's measured
two-video-frame worsening was fixed by packed HUD spans and cached native
vitals artwork. The final build restores the baseline's one-frame replacement
at both tested HUD loads, preserving the rendered HUD pixels. Representative
quiet/action performance tests alone are not proof of worst-case 60 Hz
performance; the dirty-HUD workload is measured separately. The paired sample
is not a reason to mask a lingering effect with a permissive timeout:
`bloom_probe.py` explicitly checks the first changed hardware OAM after hurt.

A manually changed HP fixture can also delay input sampling during the HUD
flush. The gathering test settles that fixture and holds a real button until
the attack starts, then checks the reached heart. It first proves the heart
is outside body contact, so the test cannot pass through body pickup alone.

Raw reports are written by these tools to the requested output paths. The
frozen final review resides at `/workspace/setup/art-reboot-final/review`
in the development workspace; published review links belong in the release
README, not in these reproducible probe method notes.
