# Leaf-crown canopy: ground and alpha integration

Status: profile 29 exploration. The user's new Pokémon Emerald reference
rejects the prior ten adaptive tree studies, especially the featureless dark
purple-black field behind their exposed branches. The new art is authored
at native GBA dimensions; this note describes its renderer integration.
No Pokémon sprite pixels are copied into the game.

## Why the previous pictures formed panels

There were three cooperating causes, not just a palette problem:

1. The previous large native drawings deliberately included opaque, mostly
   untextured quiet backing around sparse branches and small leaf patches.
2. `canopy_scene_apply_cell` changed BG2 under every interior solid forest
   cell to `MT_BLIGHT_WALL`. Its new quiet tile made a continuous dark field.
3. `record_piece` retained the original BG1 adjacency/infill entry whenever
   a complete authored 8×8 subtile was transparent. A clear region in the
   native composition therefore did not always reveal the local ground.

Adding alpha to sparse branch art alone would exchange the dark panel for
large grass holes inside a solid forest collider. The new painter must make
recognizable, dense overlapping leaf crowns carry the blocked mass, with
short visible trunks and localized underskirt/contact shadows. Quiet residual
pieces must also be actual leaf clusters rather than a flat dark plane.

## Focused profile 29 renderer changes

`src/canopy_scene.c` keeps the existing room-first component measurement,
native fitting, placement records and protected approach rules. The nine
native roles and separate 64×16 solid-branch map keep the existing descriptor
ABI. There is no new full-room pixel buffer, tile streaming or runtime image
resize.

For profile 29 only:

- Placed art writes every native BG1 entry, including complete transparent
  8×8 subtiles. Its true alpha silhouette reveals BG2 rather than retaining
  a hidden infill square.
- The compositor leaves BG2 as drawn by `render_cell`. That function already
  chooses the actual stored floor from `gRoom.underlay` when it is valid,
  otherwise a local, appropriate grass/soil floor. A profile 29 canopy-only
  fallback uses native moss 0–2 when no valid stored or neighboring floor
  exists; deep/arena rooms use the accepted sick floor. It never invents a
  dirt path under a remote forest interior. The compositor does not replace
  that floor with a dark wall tile.
- Unclaimed solid-mask cells keep the new painter's leafy adjacency/infill
  art. The art and its corner rules, rather than a purple ground slab,
  establish the forest's outer contact.

The regular floor remains logically blocked where the generated forest mask
is solid. Small exterior leaf notches and trunk contacts may show ground,
while broad gaps through a blocked mass are an art failure to correct. The
actual native canopy opacity still drives the existing Bloom safeguard;
projected foliage retains walkable collision and reserved feature clearances.

The optimized row masks, IWRAM candidate search, palette clock and cached menu
redraw remain unchanged. The entry-cost tradeoff of adaptive composition is
not silently claimed to be solved by this artwork revision.

## Preservation and evidence

Both renderer changes are preprocessor-gated to profile 29. Historical
profiles 0–28 retain their original generated assets and C execution paths.
Profiles 0–18 still omit the adaptive translation unit, preserving their
linker input order. Actual old-profile ROM identities must be checked rather
than inferred only from the guard. Representative profiles 19 and 28 were
rebuilt in separate build folders and match their prior frozen ROMs exactly
(`09aa5274…` and `420cc65e…`). The complete preprocessed C body also matches
the prior source for every adaptive profile 19–28. These focused preservation
checks do not claim a fresh rebuild of all historical profiles.

Real mGBA checks should cover a healthy broad crown, deep broad crown,
isolated growth, narrow strips and separated/concave fragments. Verify exact
resident BG1 entries including transparent subtiles, unchanged logical
geometry/collision, actual floor visibility at alpha margins, clear protected
features, and Bloom under the projected leaf edge. Native source diagrams are
not substitutes for these framebuffer views. This note does not claim visual
success before the new captures are inspected.

## First actual-room integration review

The first five natural profile 29 geometries pass 141 capture checks,
including every authored BG1 map entry (blank subtiles included) and the
native stored/local BG2 floor beneath every planned solid cell. The large
featureless purple-black backdrop is removed. This technical result is not
an approval of the image: broad views expose a second problem where crowns
pasted beyond their native canvas are cut into straight leafy panels.

The next correction is deliberately in the art. Complete unequal crown lobes
and shaded skirts must end organically inside each native extent. A uniform
inset would merely turn the problem into a rectangular grass halo, so real
outer gaps must vary with the crown anatomy. Narrow gaps may show the actual
ground without promising a player-width passage; large internal grass voids
remain unacceptable inside a blocked mass.

The renderer does not substitute a whole boundary tile with a repeated leaf
band, and does not add a dynamic per-pixel clipping atlas. Either would obscure
the native composition or consume the small remaining tile budget before the
simpler silhouette fix has been judged. Adjacent stand joins and outer edges
must be inspected again in actual rooms after the artist's contact pass.

A first full-room substrate inspection also found a separate material issue:
`barrier_floor` falls back to `MT_PATH` when neither stored nor neighboring
floor is available. That made healthy interior alpha reveal brown soil
rectangles even though a generic floor-type check passed. Profile 29 therefore
uses a dedicated canopy-only floor helper. It preserves valid non-prop floor
underlay first, then the first real non-prop floor neighbor in south, north,
east, west order. Otherwise deep/arena rooms receive `MT_BLIGHT_FLOOR`; healthy
rooms choose `MT_MOSS0..2` using stateless `hash32(seed, y*32+x) % 3`. Existing
barriers, water and paths keep their prior floor rules. No world RNG call or
logical room write is added. Actual checks must establish substrate material,
not merely that its metatile type is floor.

## Second actual-room integration review

The second five natural geometries pass 146 capture checks, now including the
exact source-material fallback condition as well as native map/floor proof.
Healthy interiors reveal moss instead of artificial brown path patches, and
the artist's complete crown skirts expose small real-ground gaps. The large
purple-black slab is materially removed. There is no additional engine-level
boundary clipping in this pass.

Some adjacent compositions and narrow column pieces still form tidy rows or
straightish seams. These remain art/placement-kit tradeoffs to judge in the
actual screenshots. Replacing them with a repeated boundary strip would not
supply more natural tree anatomy. The engine owns the actual native alpha and
local substrate; those properties do not alone establish aesthetic success.
