# Native mockups: selection, critique and production gate

These are design mockups, not screenshots of the running game. Their source
canvases are 240×160. Enlargements use nearest-neighbour sampling solely for
inspection; no high-resolution image was generated or reduced into an asset.

## Initial studies

Both studies use the same room layout, compact character, objects and HUD.
Direction A uses cool verdigris foliage and quiet grass, with warm wood,
brass and ivory for interaction. Direction B warms the same woodland into
tarnished olive. A was selected: its warm-object/cool-world separation is
clearer, while B lets mud, paths and foliage merge too often.

The initial A study was still a layout and scale demonstration. Its square
banks, repeating leaf wall, rounded tree crowns, generic arch, clean Drain
and mostly recoloured blight did not satisfy the proposed art direction.
Those failures were recorded before production rather than accepted as the
new standard.

## Revisions in the three-scene board

- The canopy uses larger broken leaf masses and a darker hanging side plane.
  Healthy trees have an irregular crown and flared roots. Corrupted trees
  have a different anatomy: exposed crooked limbs, wet cambium, hanging
  ulcers and parasitic pale fungus.
- Paths connect through chipped verges. Convex pond corners have grass
  wedges, banks have a visible near face, and broad mud/leaf accumulations
  collect at believable edges.
- The hollow is a rooted trunk opening, the thicket carries connected leaf
  pilasters, and the Drain has a stone-framed ladder with distinct rungs.
- The Drain places grease, green drips and scum directly below corroded
  copper outlets. The blight has dark wine-coloured pools and roots rather
  than simply changing the healthy water and trees to purple.
- Each scene deliberately juxtaposes dirt and glory. Clean brass sits beside
  sewage and grease; a pale flower grows through rot; a small polished
  chest rests beside damp earth. Corruption is not an excuse to make every
  object bright pink.
- Twenty tiny ambient glitter positions favour canopy and wet edges. Six
  larger interaction/specular positions have staggered phases, with four
  showing a bright five-pixel flare at a time. Four-frame GIFs demonstrate
  the staggering. This is abundant glitter with a size hierarchy, rather
  than one white effect repeated over every walkable floor tile.
- Bloom has a contact shadow, connected limbs and a much smaller silhouette.
  The pickup key is readable through shape and warm value contrast rather
  than occupying the same area as the player.

## Measured source scale

| Asset | Visible size | Source canvas |
| --- | --- | --- |
| Bloom, normal front/back | 14×22 | 16×24 |
| Key pickup | 13×14 | 16×16 |
| Coin pickup | 10×12 | 16×16 |
| Closed chest including attached shadow | 20×19 | 32×32 |
| Hollow/thicket including root flare | 32×46 | 32×48 |
| Cave arch | 31×42 | 32×48 |
| Healthy tree | 32×48 | 32×48 |
| Corrupted tree | 32×47 | 32×48 |
| Pressure plate | 16×16 | 16×16 |

The source canvases are design boxes. Production must pad them to valid OBJ
shapes or split them into valid pieces; 16×24 and 32×48 are not hardware OBJ
sizes. Normal Bloom can fit a padded 16×32 object, while action arms can use
a 32×32 streamed object. The mockup hardware report explicitly plans legal
padded shapes and does not pretend that the design boxes are directly usable.

## Hardware evidence

`tools/art_reboot_mockups.py` records the actual indices and palette bank of
every background stamp. It verifies that each occupied 8×8 background cell
uses one sixteen-colour bank, deduplicates 4bpp subtiles with hardware flips,
and counts the resident banks. Every ink is aligned to RGB555 channel values.
The selected forest uses 182 unique background subtiles and four background
banks; deep blight uses 182 and two; the Drain uses 20 and two. The compact
HUD uses a separate bank. Source sprites also use one sixteen-colour bank
per frame. Exact counts and conservative legal-OBJ padding/OAM bounds are
saved in `constraints.json` alongside the images.

Those counts prove these particular mockups are representable under the
stated background and sprite limits. They do not prove that the complete
procedural game, every animation frame, menus and effects fit together in the
production engine. That requires the later actual-ROM packing and residency
checks. The mockup retains many floor fixtures as independent source stamps
for clarity; a production pack may bake static stains into background tiles.

## Remaining critique before calling production finished

1. The reduced scale and material grammar are established, but a static
   front/back Bloom does not validate sword, shield, jumping, lifting or
   directional occlusion. Those need deliberately drawn key poses and real
   playback on every ground material.
2. The lower-detail ground helps navigation, yet repeated path marks and
   large quiet panels can still look schematic. Production needs a small,
   intentional set of connected edge and stain variants, not random noise
   sprinkled into every tile.
3. Hollow and thicket frames are more material-specific now, but their
   placement must grow out of surrounding wall masses. Dropping the same
   free-standing portal into every clearing would recreate the pasted-on
   appearance that prompted this reboot.
4. The Drain's greasy surfaces are directional and its ladder is visible,
   but keeper faces, shop dressing and contact shadows need the same native
   drawing grammar. A cohesive room cannot be obtained by replacing only
   its interactive objects.
5. Glitter placement in these authored examples is intentional. Procedural
   production must preserve its hierarchy and bright-pixel budget, including
   enemy telegraphs, rather than converting every sparkle into a pickup cue.
6. The compact HUD is a proposal. Five-pixel labels and 20-pixel height must
   remain legible in emulator output and through dialogue/menu transitions.
   The existing slot language should survive; its final spacing is not
   proved by this source image.

The production acceptance gate is therefore consistency across all active
assets and actual GBA rendering, not an attractive isolated forest image.
