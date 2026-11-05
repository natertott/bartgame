# Production arcade, discovery and enemy qualification

`tools/arcade_journal_review.py` drives an uninstrumented production ROM in
mGBA0.10.5. A bundle contains its matching ROM, ELF, linker map, assets header
and source commit. The report binds source, ROM and tool hashes to the actual
native screenshots, GIFs, controls encoded in the matching helper and checks.

```sh
source /workspace/setup/activate.sh
python tools/arcade_journal_review.py \
  --bundle /path/to/frozen/bundle --out /path/to/review
```

The complete suite includes `journal,discovery_profiles,natural,music,save`.
`--suites` selects smaller private diagnostics; partial runs are not relabeled
as a complete qualification.

The cabinet test positions Bloom on the real upper bank, walks toward the
cabinet and presses A. It exercises known and unknown entries, Items/Enemies,
notes, Back and Start. Unknown entries must have no preview. Modal sampling
checks that actors and the run clock pause while the video clock continues.
On exit it compares the unchanged terrain/collision, borrowed portrait tiles,
portrait palette and BG3 controls/scroll. Actual source material palettes and
native sprite bytes must match every displayed catalogue entry.

Discovery has two separate evidence paths. A clean profile establishes the
three starting tools and no enemies. Real generated encounters then populate
all encountered enemy types through normal drawing, and those earned records
must survive a new run. Separate explicitly serialized, checksummed profile
fixtures provide complete24-item/9-enemy UI coverage. Those catalogue fixtures
are not claimed as earned exploration. They also exercise newest-generation
selection, torn-record fallback, invalid-record rejection and independent
appearance records. Three frame/palette pairings cover all selected frame
styles with independent color choices. Normal death/save, reboot and Continue
must preserve the collection and appearance settings. The pre-existing
six-check save helper separately tests legacyv1 migration and version2 runs.

The natural-room census uses the normal procedural roster in all25 rooms of
seed0xB4A7. It does not remove or inject enemies. Navigation uses the game's
transition request, and Bloom is positioned on real safe ground near a new
creature for camera coverage. Player health is replenished; enemy HP, state,
timers, facing and poses are never assigned. Every sampled streamed frame is
matched against its exact native ROM payload after the real VBlank upload.
Ordinary AI/animation continues. Each room contributes120 steady samples after
camera warmup; allocation must remain below the reserved HUD boundary. These
finite workloads do not certify arbitrary future populations or every seed.
The companion production-enemy review covers controlled combat and slot reuse.

Music checks establish natural title/Drain/forest mappings, continued playback
through a real sword effect, DMA1/timer control and the measured32768Hz sample
clock. Reading a running timer's low register does not read its reload value;
the sample-rate check uses actual elapsed video frames and accumulated sample
counts. The companion original-music review supplies full-loop, guard, waveform
and all-five-context evidence.

All PNGs remain untouched240×160 mGBA framebuffers. GIFs sample those native
frames with GBA-derived durations, and decoded pixels/timings are checked.
No artwork, terrain, palette, OAM or VRAM is injected by this helper. The only
actor-death assignment exercises the actual run-save path; it does not stand
in for a combat victory. No external user's save file is opened or modified.
