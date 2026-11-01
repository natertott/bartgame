# Leaf-crown canopy: actual mGBA recording method

Frozen game/art source: `ead9bb68ca1cec93c8969dd813deda94c919af07`.
Capture tool SHA256: `a6aac83dc3ff7ad83801329dc0a04bcb8f923d36efb951ad544678f3f2579e9d`.
Selection-plan SHA256: `d37d3507d5f3019707254de534f1503118f309eaf5680776f66c25624f806e60`.

The final run records eight contexts from prior profile 19 and eight from new
profile 29: five natural generated geometries, two ordinary-input motion
sequences and one menu return in each. Profile 19 passes 188/188 checks; profile
29 passes 232/232, for 420/420 across 800 video observations. Four full-rate MP4
viewing copies and four exact sampled-palette GIFs accompany untouched 240×160
framebuffers and native filmstrips. Failed and superseded pilots remain separate;
these final reports are not edited into their passing state.

## Actual generation and controlled starting conditions

The ROM generates the world and room through its normal code. The held fixture
selects seed, room, player position/facing and inventory/health, and clears
unrelated enemies. It initializes a native standing frame before more than two
seconds of ordinary standing settle; recorded action poses come from actual
inputs. It does not replace generated terrain, collision, render maps, active
poses, action timers, jump height or framebuffer pixels.

After generation, enemy clearing and settle, the tool assigns one disclosed
common global action-RNG starting state. It records the previous value,
assignment and readback, with unchanged room, world and progress hashes and no
intervening emulation frame. Different room-loading durations can consume
different unrelated-enemy random draws before that point. Strict initial/final
RNG, physical arrays, maze, progress, ordinary input and ordered mechanic-state
comparisons remain active throughout the recorded sequences.

## Native art, alpha and ground verification

The reader checks resident VRAM bytes, authored animation data, legal palette
banks and actual BG1 map entries against the frozen ROM. For profile 29 it checks
every prefab subtile, including entirely transparent tile-zero entries. An
alpha gap must clear the old picture; retaining an opaque old alias fails.

At every sampled hardware observation, every solid canopy cell's actual BG2
quarters must equal its native visual-ground metatile, and the substrate must
be a non-prop floor. Valid stored floors are preserved. Otherwise the reader
independently checks the first real floor neighbor in S/N/E/W order; only the
fallback uses sick grass for stage >= 3 or the arena, otherwise native moss0..2
selected by the unchanged stateless unsigned32 room hash. An invented interior
path or canopy-wall panel fails this material check.

Every hardware sample retains counts, a canonical full-snapshot hash and twelve
spatial samples. Each context retains one complete raw cell snapshot with
visual/underlay IDs, four logical neighbor IDs, expected material and actual/ROM
BG2 quarters. All sample hashes must agree within the context. Logical collision
and walkability remain separate from these display-only floor choices.

Full-room BG1 RGBA and BG2 RGB exports in the broad healthy/deep contexts are
read-only layer reconstructions. BG1 native ink zero becomes transparent. They
contain no combined player, HUD or world composite and are labelled separately
from actual framebuffers. Source art/catalog images and palette-inspection GIFs
are likewise source evidence, not emulator screenshots.

## Actual character visibility and timing limits

The reader pairs hardware at visible scanline zero with the completed framebuffer
at scanline 160. It checks current native Bloom pixels, any exact native lower
body fragment and actual BG1 opacity/priority. Only a byte-validated attached cape
at the exact body anchor can join the displayed-character composite; weapons,
other actors, UI and nearby foliage never count. These samples retain at least
37 meaningful exact-color character pixels and a connected component of 14.
That is finite coverage, not an all-position or all-animation visibility claim.

Every recorded ordinary playing interval advances one gameplay update per IRQ,
with zero missed intervals outside the menu case. The same three zero-update
opening handoff intervals occur in both menu probes. Displayed world planes
return at tick 50 in prior profile 19 and tick 49 in new profile 29, one video frame sooner in this
fixture. In both, the first returned world frame precedes restored hero OAM by
one frame; this inherited interface return is disclosed rather than called
canopy occlusion. Absolute menu tick lists therefore differ while in-room cadence
passes.

Fresh final-bundle transition measurements request the same normal seed 6 / cell 4
transition and observe first post-run PLAY. Prior19 takes 47 video/VBlank frames;
new profile 29 takes 45, each with two mainloop updates. At GBA 59.7275 Hz these are about
0.79s and 0.75s. This is a local loading measurement, not a worst-case guarantee
or a new broad CPU benchmark. The earlier profile 6 measurement of 28 frames is
historical evidence from a different published control, not a fresh third ROM in
this focused run.

Native PNGs are authoritative. MP4s are lossy, full-rate, integer-enlarged viewing
copies. GIFs are published only after exact sampled RGB round-trip checks. Raw
all-frame recordings remain local; useful native phases and filmstrips are
published separately. The art's reference resemblance and background blending
still require visual judgment; mechanical checks do not certify aesthetics.
