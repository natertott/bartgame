# GBA art reboot: evidence and design conclusions

Research date: 2026-10-28. This distinguishes hardware facts, measured native
assets, implementation evidence and proposed BARTGAME rules. References are
studied for their construction; their graphics are not production assets.

## Hardware comes first

Tonc's [video chapter](https://github.com/gbadev-org/tonc/blob/36b7def42d12ec799b4f42b4a15c115273c3f9f9/content/video.md),
[tile overview](https://github.com/gbadev-org/tonc/blob/36b7def42d12ec799b4f42b4a15c115273c3f9f9/content/objbg.md)
and [object chapter](https://github.com/gbadev-org/tonc/blob/36b7def42d12ec799b4f42b4a15c115273c3f9f9/content/regobj.md)
establish the actual constraints:

- The display is **240×160**, about **59.73 Hz**, with **RGB555** colour:
  32 levels per channel, 32,768 possible colours. This is not a global
  16-colour machine.
- BG and OBJ each have a separate 256-entry palette. In the selected 4bpp
  workflow these become sixteen banks, each containing fifteen painted
  colours plus transparent index zero. The existing engine reserves some
  banks for its interface; the theoretical hardware maximum is not its
  available world-art budget.
- Hardware tiles are **8×8**; a 16×16 gameplay cell comprises four tiles.
  A 4bpp tile costs 32 bytes. Repeated and mirrored tiles can share data.
- Regular hardware object canvases include 16×16, 16×32, 32×32 and 32×64;
  they are not arbitrary PNG sizes. There are 128 OAM entries, 32 KiB of
  tiled-mode OBJ VRAM and additional scanline constraints. A character can
  use multiple objects; a large canvas need not contain a large body.
- Layer priority, transparency and sorting are hardware behaviours. They
  must be demonstrated in the running engine rather than simulated by
  painting a handsome composited screenshot.

Draw mockups directly on indexed native canvases. Quantize proposed inks to
RGB555 before judging them. Use integer pixel clusters and opaque/transparent
edges; enlarge only for inspection, using nearest-neighbour sampling. A
240×160 PNG alone does not prove implementability: count its palette banks,
unique 8×8 tiles, objects and per-frame effects, then pack and run it.

## Measured Pokémon evidence

These measurements use the native indexed PNGs published by the `pret`
decompilation projects. Visible bounds exclude palette index zero. Frame
sizes are cross-checked against the games' graphics declarations, not inferred
from the size of an enlarged web illustration.

| Native example | Frame allocation | Painted bounds measured | Implication |
| --- | --- | --- | --- |
| FireRed Red, nine walking poses | 16×32 | 14–15 wide, 18–19 high | The protagonist occupies about one tile in width, not two. |
| FireRed policeman, nine poses | 16×32 | 13–15 wide, 19–20 high | NPCs share the protagonist's scale and foot baseline. |
| FireRed overworld item ball | 16×16 | 10×10 | A world pickup can be recognizable well below one tile. |
| FireRed potion bag icon | 24×24 image | 15×21 | Menu illustrations are a separate display category. |
| FireRed Poké Ball bag icon | 24×24 image | 18×18 | The world version is deliberately smaller. |
| Emerald overworld Zigzagoon, three poses | 16×16 | 14×15, 14×14, 16×12 | Small creatures change silhouette without becoming noisy. |
| FireRed overworld Snorlax | 32×32 | 24×22 | An exceptional large blocker is larger than the human. |
| Emerald overworld Kyogre | 32×32 | Up to 32×32 | Large story creatures have a different scale class. |
| Emerald Rayquaza still poses | 64×64 | 32×30 in the first three poses | Allocation and visible size must remain separate even for large actors. |

Primary sources:
[FireRed declarations](https://github.com/pret/pokefirered/blob/master/src/data/object_events/object_event_graphics_info.h),
[Red PNG](https://github.com/pret/pokefirered/blob/master/graphics/object_events/pics/people/red_normal.png),
[policeman PNG](https://github.com/pret/pokefirered/blob/master/graphics/object_events/pics/people/policeman.png),
[world item](https://github.com/pret/pokefirered/blob/master/graphics/object_events/pics/misc/item_ball.png),
[bag potion](https://github.com/pret/pokefirered/blob/master/graphics/items/icons/potion.png),
[bag ball](https://github.com/pret/pokefirered/blob/master/graphics/items/icons/poke_ball.png),
[Snorlax](https://github.com/pret/pokefirered/blob/master/graphics/object_events/pics/pokemon/snorlax.png),
[Emerald declarations](https://github.com/pret/pokeemerald/blob/master/src/data/object_events/object_event_graphics_info.h),
[Zigzagoon](https://github.com/pret/pokeemerald/blob/master/graphics/object_events/pics/pokemon/zigzagoon.png),
[Kyogre](https://github.com/pret/pokeemerald/blob/master/graphics/object_events/pics/pokemon/kyogre.png),
[Rayquaza](https://github.com/pret/pokeemerald/blob/master/graphics/object_events/pics/pokemon/rayquaza.png).

This is a measured sample, not a universal size requirement. Pokémon's battle
portraits and trainer portraits are not evidence for overworld scale. The
important failure in the current game is precisely that a detailed bag icon
has become a giant ground object while the player has grown to match it.

## The Minish Cap: actions, depth and readable spaces

The clean public [Minish Cap decompilation](https://github.com/zeldaret/tmc)
provides useful implementation evidence:

- [The sword](https://github.com/zeldaret/tmc/blob/master/src/playerItem/playerItemSword.c)
  is a separate player-item entity. Its hitbox offsets and dimensions are
  selected from the player's current animation frame, and incorporate
  visual offsets. Animation, direction, grip and contact belong to one
  contract; a fixed icon pasted onto a moving body cannot provide it.
- [The shield](https://github.com/zeldaret/tmc/blob/master/src/playerItem/playerItemShield.c)
  inherits player animation direction and selects a directional hitbox.
  A north-facing shield must belong ahead of the torso, while a back-worn
  cape belongs behind it. Directional occlusion is part of the design.
- [The player hitbox](https://github.com/zeldaret/tmc/blob/master/src/playerHitbox.c)
  has 6×6 half-extents and a small vertical offset. A ground collision
  footprint is not the entire head, hat, body and weapon silhouette.
- [Bush behaviour](https://github.com/zeldaret/tmc/blob/master/src/object/bush.c)
  separates the object, collision, lifting and effects. An object keeps its
  identity between standing, lifting, carrying and breaking.

The repository explicitly excludes the commercial graphics needed to build
it. Therefore this research does **not** invent an exact Minish Cap Link
pixel height or claim to have measured a complete Link sheet. The quantitative
size table above is Pokémon evidence. The transferable Zelda design analysis
is about relationships: consistent top/side planes, small feet below an
expressive head, distinct blockers, visible approach space, stable hand
anchors and action-specific silhouettes.

Use a slight top-down view consistently: show the tops of heads, pots and
walls, with their near faces below. A dark vertical face and attached shadow
identify a raised solid; a light rim around a genuinely dark cavity identifies
a hole. Water has continuous banks, and a bridge ends on traversable ground.
Ground texture must not mimic wall tops, webs, pickups or sword trails.
Clearings, thresholds and uncluttered approach tiles are visual information.

## Rules to carry into the new mockups

These are proposals derived from the evidence, not Nintendo specifications:

1. **Scale ladder.** Start Bloom near 16×20 painted pixels, NPCs 14–18×20–24,
   ordinary creatures 12–18, elites 20–28, brutes around 24–32 and bosses
   40–64. Keep ordinary pickups around 8–14, important loose items 12–16,
   regular chests around one tile and major chests around 24. Larger menu
   illustrations never automatically become larger world objects.
2. **One construction language.** Shared ink outline, three-tone material
   ramps, upper-left light, connected clusters, consistent foot anchors and
   restrained internal texture across characters, rocks, buildings and UI.
   No soft photo-like glow or antialiasing around isolated sprites.
3. **Affordances use shape and state.** Broken stone has a deep fracture;
   silk has a connected radial mesh; keys correspond to a keyhole; jump
   gaps have a continuous drop face. States change silhouette/value, not
   merely hue. Thresholds need negative space and a clear approach.
4. **Tools are performed.** Design body and weapon together in every facing.
   Use anticipation, one readable active sweep and recovery. Stabilize the
   feet and grip; show the actual hit extent; keep sprite depth correct.
   Test actions against light stone, dark soil, foliage and violet decay.
5. **Quiet floor, strong actors.** High-frequency detail and pale highlights
   belong to actors, hazards and destinations. Use broad floor clusters and
   larger connected terrain masses. Per-cell decoration should not compete
   with the navigation graph.
6. **Filth and glory coexist.** Put luminous gilt beside algae, splendid
   petals on rotten stems, bright reliquaries in stained stone. Avoid a
   clean green game abruptly replaced by a different purple game.
7. **Lots of glitter, controlled peaks.** Many small staggered glints can
   animate across wet grime and gold. Reserve the largest cross-stars and
   near-white accents for the player, interactables, attacks and discoveries.
   Let dirty material remain visibly dirty between flashes. This achieves
   Excalibur-like radiance with native clusters rather than a blurred bloom
   filter covering the playfield.
8. **Nine-area consistency.** Keep scale, perspective, shared gold/ivory,
   outline weight, tool meanings and animation grammar invariant. Each new
   area changes its material ramps, ecological shapes and one filth/glory
   pairing. It does not introduce a new character rendering style.

Critique each mockup at 1×, grayscale and reduced-detail views. Ask first
where Bloom is, where the floor ends, what can be picked up, where to enter,
what needs an item and where the next threat will hit. A beautiful enlargement
that cannot answer those questions at 240×160 should be rejected.
