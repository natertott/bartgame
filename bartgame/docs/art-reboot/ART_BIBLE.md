# BARTGAME art direction: gilt and rot

This is the common art direction for the current build and the eight future
areas. The Drain is the hub; the Blighted Forest is area one of nine. Future
area names and themes remain undecided. New art must extend this vocabulary,
not introduce another sprite pack.

The [research](RESEARCH.md), [asset audit](ASSET_AUDIT.md) and
[mockup critique](MOCKUP_CRITIQUE.md) explain the evidence behind these rules.
`art/reboot_core.py` owns the shared inks, perspective and reference shapes.
Metadata in `art/reboot_contracts.json` preserves identifiers and physical
contracts; it contains no source artwork.

## Living direction and decision record

This is the shared, current specification, not a one-time style proposal.
Keep it updated throughout art work. Record each art-direction decision in
the [direction log](ART_DIRECTION_LOG.md), including its reason, user feedback
or reference pages, affected assets, review evidence and remaining tradeoffs.
Keep experimental and adopted choices distinct. Local area studies become
shared rules only when that scope is intentional and recorded.

The [reference register](REFERENCE_REGISTER.md) tracks source availability and
source-specific notes. Incorporate guidance after reading the actual text and
illustrations, and document how it applies at native GBA scale. An inaccessible
reference remains pending; do not imply that it has already informed the art.

## The desired contrast

Excalibur's polished metal and supernatural light exist in the same frame as
mud, damaged bodies, rot and exhaustion. Bataille supplies the tension between
the sacred and the abject, beauty and material excess. Render that tension
through matter and light: a pristine flower beside a black pool, brilliant
brass emerging from greasy masonry, beautiful dew on a diseased branch.

Do not put all beauty in the healthy forest and all ugliness in the blight.
Every area needs both. Corruption changes structure and material—bare limbs,
sagging growths, exposed roots, parasites, slick pools—not just the hue of an
otherwise healthy tree. The forest's progression should preserve occasional
exquisite, luminous things even near the Heart.

Verdigris greens, warm earth and amber/ivory light form the selected base.
Wine, bruised violet and pale fungal flesh belong to corruption. Tarnished
copper, scum green and dark teal belong to the Drain. Gold connects the areas.

## Native construction

- Author at the final pixel size. Screens are 240×160, gameplay cells 16×16
  and hardware subtiles 8×8. Enlarge only for inspection with nearest neighbour.
  No high-resolution generation, filtered reduction or photographic texture.
- Inks start as RGB555 colours. Each 4bpp bank has transparent index zero and
  fifteen painted inks. The engine allows twelve world BG banks per area;
  interface banks remain reserved. OBJ has sixteen banks in total.
- Use valid hardware canvases. A nominal 14×22 body is padded into 32×32 when
  its hands need room; 16×24 is a design box, not a hardware OBJ shape.
- Use a hue-dark one-pixel contour where a sprite must separate from terrain;
  quieter material edges on floors and subordinate architecture. Start with
  two or three deliberate values per small material, rather than filling every
  palette slot. Group highlights into clusters. Avoid decorative pixel noise,
  bevelled clip-art symbols and filtered soft edges. Selective hand-placed
  existing-ink AA on an internal turn is permitted when it reads better at 1×.
- Light comes from the upper left. Lower/right edges and contact shadows are
  darker. Reflective glints are local exceptions, not a second diffuse light.

## Reference-led design sequence and hierarchy

The six uploaded tutorials were read on 2026-10-30. Their page-cited guidance
and deliberate GBA adaptations are recorded as G01–G18 in the
[application matrix](REFERENCE_APPLICATION.md). These principles guide future
art work; they do not imply that every existing game asset has already been
redrawn in this pass.

Start with a native filled silhouette and a few material masses. Identify the
object and its action before adding shadows, surface texture or highlights.
Inspect negative space, proportions and one main identity detail at actual
screen size. For the Drain, frog eyes/jaw and the wizard's flame-tipped staff
carry identity; small outfit marks remain subordinate. A world sprite and its
48×48 portrait use the same identity with different amounts of information.

Then shade volume with broad light-facing and far-side planes, contact shadows
and recessed cavities. Do not build shading from concentric rings parallel to
an outline. Cool shadows and warmer selected highlights should remain clearly
separated after RGB555 quantization. Narrow specular groups distinguish gold
from matte cloth and brick; wet grime has its own sparse attached reflections.
An occasional local reflected-light patch can connect materials without
turning into a second full rim or competing with the main identity detail.

Keep the playable field quieter than important objects. A floor must still
read as gray slimy brick, but every mortar joint, crack and wet patch need not
have equal contrast. Filth accumulates in coherent deposits under plumbing,
in seams and along banks; it is not a repeating grid of small pickup-like
symbols. Reserve local dithering for a material transition where its pattern
and scale help. Neither checkerboard noise nor a blanket anti-dither rule is
the shared direction.

Refine lines and curves at their final coordinates. Regular pixel runs should
not acquire accidental kinks; intentional broken masonry, organic anatomy and
frayed hems may use irregularity to describe their structure. Selective
palette AA differs from automatic blur: moving external contours must remain
crisp on different backgrounds, with no fractional-alpha fringe. Inspect at
1× throughout, using larger integer zooms only to diagnose placement.

Review silhouettes, grayscale value groups, full pose families and actual
scene motion before declaring the art finished. Preserve old/new comparisons
and record the reason for each directional change. Correct palettes in their
authored banks, never by grading a screenshot and calling it an implemented
improvement. Tall-portrait tracing, optional blur/gradients and unrestricted
color from one tutorial are translated into native clusters and useful palette
choices; they do not override the user's GBA-first constraints.

## Scale and contact

| Category | Normal painted extent | Rule |
| --- | --- | --- |
| Bloom | About 14×22; action hands may extend to 18×24 | Compact flower/stem silhouette with a clear face and two root feet. |
| Ordinary humanoid | 14–18×20–24 | Share Bloom's world scale and foot baseline. |
| Small creature | 8–16×8–16 | A few strong masses; readable facing or attack preparation. |
| Armoured enemy/miniboss | 16–24×24–32 | Deliberately larger, with a distinct silhouette and telegraph. |
| Heart/boss | 32–48 pixels across | A commanding mass with a clear vulnerable part; collision must agree. |
| Ordinary world pickup | 8–14 pixels | Never use its menu illustration as the world drop. |
| Important world pickup | Up to 16×16 | Importance comes from silhouette/glint, not a 32-pixel icon. |
| HUD item | 12–16 within a 16×16 canvas | Its own drawing, not a filtered menu image. |
| Menu/reward illustration | 24–28 within 32×32 | More detail, same silhouette, material and light as the world version. |
| Chest | About 20×18–20 closed | Wood, reinforced brass and relic variants share one construction. |
| Plate | 16×16 | Flat, broad footprint with a clear pressed state. |
| Entrance | About 32×40–46 | Opening taller than Bloom, embedded in a material mass. |
| Tree | Usually 32×48; larger groups permitted | A small ground footprint, raised canopy and coherent overhang. |

Feet define actor world positions. All bodies, tools, shadows, carried objects
and projectiles use explicit anchors relative to those feet. Transparent
canvas margins do not define body size or interaction range. A ground shadow
stays on the floor during a jump. A carried pot is the same pot that was on
the floor; it does not become a different barrel.

## Perspective and traversability

Use a consistent three-quarter bird's-eye view: visible tops, short near-side
faces and a small contact shadow. Canopy tops receive clustered light; their
hanging sides are darker. A tree crown is an irregular leaf mass, not a flat
medallion. Buildings in future areas inherit the same top/side distinction.

Walkable ground is comparatively quiet and mid-value. Walls/canopy are darker,
raised and connected. Water has a different value, a continuous bank and a
visible near edge. Pits have a genuinely dark cavity and recessed rim. Ledges
show a consistent vertical face. Do not use an identical dark line for a pit,
walkable path edge and raised wall.

Path and bank corners use shared transition tiles, with a few grass or mud
clusters breaking the grid. Large water features form coherent ponds/rivers;
bridges join usable banks. Terrain texture must not imply a false step, hole
or item. Entrances need an unobstructed approach and enough framing space to
be visible below the HUD.

## Interaction vocabulary

Carry these meanings unchanged into every future area:

- Bombable barriers: broad broken stone with a distinctive branching fracture
  and freshly exposed pale edges. Heavy lift-only boulders remain whole and
  broad; they do not reuse that fracture pattern.
- Burnable silk/brush: connected pale fibres or dry material, contrasting with
  living foliage. Candle censers have a readable bowl and separate flame.
- Cape crossings: a dark, continuous opening whose far bank can be judged.
- Keys: one clear keyhole/lock; repeated decorative metal is not another lock.
- Plates: an inactive raised face becomes a visibly depressed, lit face.
- Treasure: readable lid, latch and bands. Value tiers change construction and
  material while keeping a familiar chest silhouette. Spent states stay clear.
- Healing: a distinct basin, votive or standing medallion, with a visible
  spent/available distinction where the mechanic is one-use.

Clues may misdirect the route, as the maze intends, but material meaning must
remain trustworthy. An optional dirt trail can lead to a detour; an ordinary
floor texture must not masquerade as a bombable wall. Loot beyond a barrier
must not cover the barrier itself.

Treat ambiguous scenery as a failed silhouette before adding detail. A pipe
outlet needs a visible connection, a dark mouth, a lower lip and liquid leaving
that mouth. Falling liquid needs downward motion, a changing sheet or separated
streaks and a landing splash; a static branching contour can read as roots.
An exit arrow uses a filled arrowhead and shaft separated from both the ladder
rungs and surrounding trim. Grime belongs in attached deposits and must not
hide a crate lid, grate bars, a sign or another object's identifying structure.
These readability refinements come from the user's Drain reviews. Final Drain
profile 9 adopts the requested taller ladder, consistent arches, distinct side
walls and left-facing plumbing synthesis. Future areas reuse the semantic
readability rules while choosing their own local architecture.

## Glitter is abundant, with a grammar

Aim for roughly twenty potential ambient glint sites in a viewport, phased so
only a subset peaks at once. Use wet stone, dew, metal, rot, pools and canopy
as their sources. Add fewer, stronger four-point ivory/gold flares around
valuable or sacred objects. The mockup cycle has twenty small sites and six
strong sites, with four strong sites at their bright phase.

Most ambient glints are one to three pixels and attached to surfaces, with
occasional five-to-seven-pixel specular peaks. Loot/sacred glints use a
deliberate cross, attached to a distinct object rather than wandering freely. Enemy projectiles have a
directional body and travel, rather than impersonating stationary treasure
stars. Damage/attack flashes are brief and tightly attached to their action.
Glitter belongs on filthy surfaces too: wetness can be beautiful and repellent.

Never illuminate every point at the same instant or cover paths in independent
random sparkle actors. Budget and stagger the effect; inspect the complete
animation at native size. Brightness hierarchy must survive grayscale viewing.

## Motion

Use economical anticipation, action and recovery. Small sprites need clear
changes in silhouette, not decorative fragments. Walks alternate planted feet;
rolls remain one connected body. Jumps progress through takeoff, flight and
landing with the shadow fixed to the ground. Drowning uses the area's actual
water rather than an opaque blue disk. Death has a distinct settling motion.

Idle breathing keeps the ground contact planted while the head and upper
body move together by a small amount. Secondary cloth and flame motion may
lag. Preserve the signature shape, grip and negative-space gaps in all frames;
do not move the entire sprite up and down to substitute for breathing. The
second Drain study adds a native frog-body breathing pose to coordinate its
existing head bob without changing the original action-frame identifiers.

A sword's blade, leading arc and damage interval share direction, frame and
anchor data. Show actual reach without an opaque fan covering Bloom. The
north-facing shield is ahead of him; its visible rim must not read as a shield
on his back. Held tools are small objects gripped by the hand, never full menu
icons. Check every facing, interruptions, terrain occlusion and release frames
in the emulator before expanding an animation family.

Bloom's selected sword gesture is **Step-and-cut**, with eight coordinated
whole-body/weapon poses per facing: four preparation updates, seven live
updates and seven recovery updates. The roots, hips, shoulders and flower
all contribute to the motion. The apparent step is weight transfer, without
a world-position lunge. Keep this body/blade/contact relationship when adding
future equipment; see [the sword study notes](../SWORD_STUDIES.md).

## Interface

Keep the successful menu, shop and dialogue hierarchy. Redraw their materials,
font, markers and portraits in this vocabulary. Text has high value contrast
and deliberate one-pixel strokes; ornament does not compete with labels.
Use restrained, worn brass frames rather than ornate borders on every object.

The user's selected information hierarchy supersedes the original 24-pixel
HUD: show equipped items, hearts, gilt and a minimap, plus the current ammunition
count when blightseeds or the bow are equipped. Use small separated pods with
minimal local backplates and dark contours, leaving the top-center world
visible. Aim for a maximum 12-pixel painted height along the top. Keep the small
minimap in a separate bottom corner so it does not obscure northern content.
Do not show a key count, unrelated ammunition or context-action prompt.
Non-ammunition equipment uses an icon without an ammunition label.
Author small icons at their final size rather than clipping large illustrations.
Verify ten hearts, half/empty hearts, all three equipment slots, zero and maximum
gilt, conditional ammunition updates, minimap exploration/current-room tracking,
immediate damage/equipment updates, and contrast on bright and dark areas.

Five optional interface studies explore thin relic linework, stained vellum,
black glass, wine-colored reliquary materials and salvaged ledger construction.
Their exact ornament, palette and frames remain exploratory; the compact
information hierarchy applies to every version. Structure and palette are separate
recipes: the user prefers folio, brocade and ledger construction, especially wine
and green, with ivory-wire colors also requested for comparison. Future areas may
select their own palette without changing layout, control meanings, health colors
or map/interaction semantics. No automatic regional palette switch is adopted yet. Keep ornament at panel ends,
corners and selection markers, with clear text fields and consistent controls.
The title is authored directly at 240×160 with a limited shared palette.

Optional menu-layout studies follow the same visual vocabulary but may change
information hierarchy. Retain separate tool/key focus and inspected map cell
across pages; show actual assignment, relevant counts and concise use before
lore in short cards. Keep north up and distinguish player, inspection, known
geometry and discovered markers. A tool's verb may supplement its identity;
do not invent a matching obstacle or required route. Prototype geometry,
palette and layout remain independent choices until selected. Evaluate native
readability and ordinary button response together; polished stills alone do
not establish an effective menu.

## Area adaptation sheet

For each of the eight future areas, fill in these fields before making tiles:

1. Primary solid, floor, liquid and organic materials.
2. One glorious material/light and one filthy material, shown together.
3. Local decay structure and its progression toward the area's endpoint.
4. A small palette extension or bank substitution; shared ink roles stay fixed.
5. Landmark, enemy silhouette and environmental motion specific to that area.
6. Examples of every universal interaction vocabulary in the local material.
7. One native room, one action clip, one high-clutter fight and one menu view.

Do not increase Bloom's size or change the keyhole/web/fracture meanings to make
a new area feel different. Change its material, ecology, architecture and light.

## Production gates

Research and native mockups precede production. Critique at 1×, 2× and in
grayscale; verify palette banks and legal canvases. Then pack the real assets,
measure the whole game's BG/OBJ budgets, and render actual runs. Source mockups
are labelled as such and never substituted for emulator evidence.

The asset coverage report must name every old visual family, its new authoring
module or explicit retirement, and every scale/anchor change. Blank frames and
simple punctuation need honest exceptions, not arbitrary pixels to defeat a
hash comparison. Review the full action suite, pickups, foreground/background,
entrances, all room styles, NPCs, boss, title, HUD, bag, map, dialogue, shop,
death and victory. A pretty forest screenshot alone is not completion.
