# Independent Cream depth audit

Final source: `9747a92526fe9162d93a1ed46b8a6b8292841bb4`  
Final ROM SHA256: `2b8559c3cac89f483d3a34d48aa6eb5144a4fc2b3b7b265808b800672216a1b1`  
Protected production ROM SHA256: `0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`

**PASS: 5221/5221 report checks.** Full evidence is in
`native-audit.json`, `source-depth.json` and `geometry-audit.json`.
The host adapters retain their pinned headers, source, native metadata and
compile logs in `host-baseline/` and `host-depth/`.

## Native assets and preservation

The audit independently decodes ROM 4bpp nibbles, per-quarter hardware flips,
palette selection and animation payloads. It does not use the asset builder's
packer. All 523 Cream frames exactly match their native source pixels and
RGB555 colors. All 375 appended environment cells are opaque, use existing
Cream banks, and have either FLOOR0/prop0 or SOLID15/prop0 contracts.
Large panel starts/dimensions, every border/shadow lookup and the three native
128×48 backing tables resolve to the exact authored IDs.

Cream uses 861/1024 resident 8px background tiles and10/12 area palette banks.
All existing global tile IDs and physical/glitter metadata remain exact.
Appended entries have neutral Forest classifiers. Forest, Drain and mystery
background pixels, old mapping prefixes, palettes and animations are exact;
new Cream IDs are absent from those regions. Original sprite descriptors,
Bloom/enemy/NPC frames, HUD/fonts/title and original PCM/song metadata are
preserved. Only the explicitly scoped Cream return-portal frame changes.

## Actual pinned-C geometry and cue checks

The test compiles both pinned actual C room/world generators in isolated host
adapters using metadata decoded from their respective frozen ROMs. Rendering
is a no-op here. 64 seeds generate 1600 distinct room layouts; testing the gate-open
bitmasks clear and set produces 3200 room builds. Cape-pit traversal remains
part of the separate native player review.

- Directed graphs, room profiles/features, 8px solidity, ground/overlay/underlay
  physical contracts and exact overlay IDs/placements match production.
- 819988 large wall/backing cells occupy only original empty, unreserved
  midface; 10016 open sill cells occur only at actual directed DROP tiles;
  81050 raised border cells occur only at permanent blocked rims;
  85664 toe cells occur only at real cliff bases. No old rim/drop cells remain
  undressed.
- All 3582 incoming DROP records exactly match `cream_room_arrival()` feet.
  All 3516 active feet receive the center of a real native landing shadow.
  20943 painted parts use the correct stage/part lookup on dry traversable
  floor and preserve overlays. 66 closed source gates emit no cue.
- 3200 repeated visual refreshes preserve the complete Room and landing cache
  byte-for-byte.40 actual gate-unlock operations preserve collision, overlays
  and ground/underlay contracts relative to production.

The compositor only runs during room generation and physical gate changes;
no new scene-wide scan is added to the ordinary frame loop.

## Limits

This is source/native-fidelity and host geometry evidence, not a claim that
static statistics prove attractive art. It does not establish every possible
seed, actual player motion, camera presentation, source-to-destination fall
visibility or subjective border readability. The separately pinned real mGBA
room captures and ordinary live-input drop clips qualify those observations.
Registered whole-room mosaics, source atlases and ordinary gameplay footage
must retain their separate labels.
