# Independent Cream polish review

Game/art source: `687e6c0e999a8df70ef2f7db55f36b9200ddde30`, profiles7–11.
Exact per-ROM hashes, measurements and report paths are in `FINAL_QA.json`.
The final capture helper SHA256 is
`a02e2089d7ac6549a136491ae2b67c633d7783d9feeed5e57baa2b47d1e1f125`.
Its later camera-framing/menu assertions are tool-only changes; individual
reports retain recording-stage helper hashes. No game/art results are patched.

## Verification

All five audits pass:7 has6560/6560 checks (one extra supplied-ROM pin check),
and8–11 each6559/6559,32796 total. Each profile tests64 raw Cream area seeds,
25 rooms and closed/open gates:16000 builds across the five styles, not320
unique source seeds. Graphs, room features, semantic overlays, ground/underlay
physical/glitter contracts and8px collisions match production control0.
All other-region art, Bloom/actors, HUD/fonts and original music are retained.
Existing metatile IDs/metadata stay stable; the old Cream6 depth pictures are
explicitly nonresident/blank in the polish tileset.

The actual C room compositor and exact C blend-admission budget run in isolated
host adapters; only VRAM upload is skipped there. Every admitted masked panel
is a complete native footprint on eligible wall, with its full silhouette
inside a two-pixel alpha margin. Source pixels, RGB555 colors, animation
payloads, palette entries and static alpha classes are decoded independently
from each ROM. Static Cream subtiles are852/879/866/894/892, ten BG banks each;
the separate128-char dynamic reserve stays within1024 hardware chars.

Native mGBA adds15 matched room surveys and real climbs,10 real short drops,
one earned four-row fall, and15 live waterfall-width clips. In all15 matched
rooms,1036 painted metatiles are checked independently at the actual PPU layer:
ROM backing+alpha mask RGB555 union must equal the real BG2screen entries,
flipped VRAM characters and live palette. Dynamic highwater is127/128/127/126/126
chars, respectively. These are direct pixel checks, not just source fidelity.

Wall-to-foot shade continuity, exact incoming arrival anchors, closed-gate
suppression, refresh idempotence and actual gate unlocks pass across the host
sweep. Initial review found an endcap changing side after refresh and a gap
where nonblocking mold interrupted shade. The final pinned C fixes both;
the specific seed6/cell11 and seed5/cell23 regressions pass independently.
Mold and all semantic overlays remain intact.

Actual START item-menu open/START close passes on profiles7 and11. Complete
room/paint maps remain unchanged, native BG2alpha union still matches afterward,
and blend overflow stays zero. This tests dynamic-character lifetime through
a real UI roundtrip rather than assuming the cache survives.

## Capture visibility and fixtures

Registered512×384 mosaics are literal crops of nine frozen240×160 renderer
views, with the HUD hidden only in those private cores. Ordinary screenshots
and GIFs use separate fresh cores with normal HUD and advancing simulation.
Navigation, title seed and ordinary room-load requests are explicit fixtures;
health, inventory, enemy outcomes, gates, terrain, palettes, VRAM and pixels are
not assigned. The established earned four-row harness additionally discloses
standing/height normalization at navigation waypoints; its rewards, bomb use,
gate clearance and fall outcomes are genuine input-driven gameplay.

An early water clip verified offscreen VRAM animation but failed to frame the
three-wide fall. The final helper observes the real eased camera and waits
normal simulation16/16/68 frames for widths1/2/3. All360 sampled water frames
now show the full fall width, sufficient vertical blue body and actual blue
pixels, while the native BG2flow payload independently changes over time.
No manual camera/review-clock assignment enters an ordinary water clip.
The actual generated examples use cells12/18/16 for widths1/2/3 at title seed
0xB4A7. Water art was not stamped into a test room.

## Visual review and practical limits

Actually inspected native healthy/deep7 mosaics; sour8/9/10/11 mosaics; and
seven's three-wide frozen waterfall room and ordinary live water frames.
The wall silhouettes preserve real quiet backing instead of erasing it with
rectangular fills. The variants have distinct shelf/fault/boulder forms,
paired ladders read as one32px structure, and projecting drop undersides are
separate from the raised blocked rim. Blue flow is much clearer than the old
beige strip. Source artists' own atlases and final sampled footage complement
these finite views; no claim is made to have watched every possible seed.

The palette remains restrained and the finite rock kit still repeats forms.
Connected cast shade intentionally has a directional footprint; the final
feather softens its outer boundary but it remains a gameplay cue as well as
material shading. A rope-like ladder option is visually less conventional
than a straight-rung ladder; it is a selectable proposal, not a new mechanic.

Climb input timings remain135/119/151 frames with minimumHP32/30/30. Local
falls retain32 physical/32 simulation ticks; one-row falls retain46 simulation
ticks but take74 physical frames for7–10 and75 for11 versus64 control frames.
Thus the tested transition adds10–11 VBlanks (~0.17–0.18s) of loading. No active
frame-loop composition is added, but this is not a broad combat/FPS profile.
Default0/previous6 byte-exact rebuild verification belongs to the separate
root build evidence. Fidelity statistics do not measure artistic quality,
and finite tested seeds do not establish every possible visual join.
