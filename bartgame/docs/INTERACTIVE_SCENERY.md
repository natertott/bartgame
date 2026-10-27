# Readable interactive scenery

The [actual mGBA gallery](../../forest-review/interactive-scenery/README.md)
shows the scenery changes on generated healthy and blighted forest ground,
inside caves, hollows and thickets, and in the Drain. Native screenshots and
matched recordings accompany the playable ROM.

## Scale and visual language

The previous field chest occupied about 15×11 visible pixels; mystery chests
were 14×10. The pressure plate occupied 12×9, while each forest mouth fitted
inside a single 16×16 metatile. These shapes lost their identity among the
larger trees, foliage, growths and richly drawn pickup items.

Chests now have three distinct closed/open designs:

| Design | Visible closed size | Existing rewards |
| --- | --- | --- |
| Wooden | 22×20 | Gilt, bomb supplies; small mystery prizes |
| Brass-banded | 24×21 | Maps, heart pieces; medium mystery prizes |
| Green-and-gold relic | 26×22 | Keys, major equipment and upgrades; large mystery prizes and progression rewards |

The tier reads the existing cell reward or mystery size. It does not reroll
contents, change their value, or create an extra progression chest. Open
lids have a conspicuous dark interior, retain the tier's materials and stay
open on revisits. Their visible size includes the attached ground shadow.

Pressure plates fill a **16×16** footprint. The untouched plate has a dark
central depression and pale bevel; a pressed plate drops to a warmer face
with a bright completion mark. State changes are visible without relying
on a one-pixel vertical shift.

Cave, hollow and thicket entrances use **32×47 visible pixels** on a 32×64
canvas. Their openings are taller than Bloom, with stone, bark/root or leafy
frames and a bright threshold. The corresponding interior exit uses the
same material identity. Locked trial exits show bars, planks or woven roots;
the actual event opening removes the obstruction.

Pits now have a quiet, dark cavity, a recessed near wall and a chipped rim.
Blighted pits retain a restrained violet fracture animation without filling
the void with bright decoration. Cracked barriers use broad broken stone
slabs and fresh fracture edges. Cobwebs use connected ivory spokes and rings.
Locked gates have a large gold keyhole and readable bands. Censers have a
wider bowl and separate unlit/lit silhouettes; pots have a larger rim and
body, and the carried pot matches the new ground vessel.

Healing shrines now use a distinct sun medallion on the standing tile and a
matching votive statue. Ordinary forest flowers no longer serve as their
only affordance. The medallion becomes the existing spent stone after use.
The fairy spring is a clearer recessed basin.

The established palette supplies dark outlines, pale stone/ivory edges and
warm brass highlights. The same materials remain visible against green
forest and purple blight without a new palette or a generic opaque floor
patch. Healthy foliage, blight artwork, loose pickup designs and Bloom's
approved animations are retained. Existing liftable rocks, bushes and thorn
vines were inspected in the gallery and retain their material identities.
The Drain's already tall ladder exit and keeper/shop scenery were audited;
its painted hall artwork remains unchanged.

## Rendering and placement

Logical metatiles retain ownership of collision, interaction, rewards,
persistence and transitions. Oversized chest and portal graphics stream
through one 16-tile chest buffer and one 32-tile entrance buffer. A room
currently contains at most one chest and one mystery entrance or exit;
optional pocket hoards are pickup actors rather than additional chests.
Mystery rooms reserve the chest buffer before the event creates its reward.

The room renderer removes the small chest/mouth image when the large image
is available. It retains the stored floor under a chest and a continuous
wall behind an entrance. Allocation failure preserves the small background
image as a fallback. Chests draw ahead of Bloom when he is behind them, and
behind Bloom when he approaches from the south. Open portals remain behind
the approaching character, avoiding a black opening that masks his head.

Forest mouth placement reserves a wall patch for the larger frame, leaves
a reachable approach and starts at row four or lower so its crown can be
seen below the HUD. This intentionally changes some local entrance positions
and subsequent local dressing. It does not change the generated 5×5 maze,
progression rewards or save format.

Placed pocket hoards remain behind the gate's material until the gate opens.
Their large pickup graphic therefore cannot cover the cracked stones or web
that explains how to reach them. Opening and collection still use the real
bomb, candle or cape mechanics and the existing persistence bits.

The audit also found an existing censer-placement bug: moving a censer away
from an NPC could put its new approach on a solid stump. Placement now
protects NPC speech space and the approaches of all four quest censers.

The inventory cache uses seven slots, the maximum number of distinct icons
drawn together, rather than eight. The existing exact-icon sweep checks that
page changes and palette restoration remain correct. New scenery uses the
existing lift palette; unrelated artwork and palette data stay exact.

## Verification and capture method

The gallery's fixtures select a seed, real room, inventory, starting position
and facing, and clear unrelated actors. Interactions then run through real
button inputs. The capture tool does not inject terrain, reward contents,
mystery descriptors or animation poses. Where an entrance moves, metadata
records the same seed/cell and the changed target/camera honestly.

Native PNGs are exact 240×160 emulator frames. GIFs enlarge whole frames 2×
with nearest-neighbour sampling at approximately 30 fps; palette reduction
is recorded where necessary. Comparison sheets add labels outside the
screenshots. Source-art previews are labelled separately and are not used
as evidence of gameplay. The MP4 is a compressed convenience view.

The interaction probe checks actual OAM, OBJ VRAM, background maps and source
alpha extents. It exercises chest opening and reward persistence, both sides
of each entrance style, closed/open event exits, pressure plates, healing,
barrier occlusion and the previously inaccessible censer quest. Isolated
descriptor fixtures used by the probe are not published as naturally
generated gameplay captures.

The packed-ROM scope check retains every original metatile identifier and
physical contract, with only the new shrine plate appended. It compares all
unrelated terrain animation frames, all 101 Bloom images and effects, item
art, palettes and title data. Only the carried pot changes among existing
sprite frames. The full allocation sweep, room traversal sweep, critical
path/Heart, progression trials, pocket persistence and save checks are
recorded with the final ROM hash in the gallery's validation folder.

## Reproduce

From the inner `bartgame/` directory:

```sh
source /workspace/setup/activate.sh
make -j4
python tools/interactive_probe.py --out /tmp/interactive-probe.json
python tools/interactive_scope.py --out /tmp/interactive-scope.json
python tools/surface_probe.py
python tools/bloom_budget.py --out /tmp/interactive-budget.json
python tools/roomgen_probe.py --seeds 0xB4A7,0xDEADBEEF,6,22 --out /tmp/geometry.json
python tools/mandatory_trials.py
python tools/critical_path.py --seed 0xB4A7 --boss
python tools/pocket_probe.py
python tools/save_probe.py
python tools/interactive_review.py /tmp/interactive-captures
```

The scope tool needs a paired baseline ROM, map and generated header, provided
with `--before-rom`, `--before-map` and `--before-header`. The frozen baseline
is the previous Bloom-suite ROM, SHA256
`d5f9eda0647c0b197011656cd9fd758f2438df6c4e7e212dd100d31fc3f130ac`.
The capture tool accepts `--rom`, `--map`, `--assets-header`, `--match` for the
previous `capture.json`, and `--only` for selected clip names.
