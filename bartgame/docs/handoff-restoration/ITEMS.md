# Additive item and surface restoration

The runtime uses the original migration vocabulary from `docs/newgame/02`,
`03`, `05` and `12`, checked against the readable original `src/playerItem/`
and `include/item.h`. The current Step-and-cut, all current inventory IDs,
PlayerState layout, old art and existing item behavior remain intact.

`legacy_items.h` records 118 original inventory IDs, including unused source
slots. Four additional source values0xFC..FF are explicitly **drop values**,
not inventory IDs: red/blue/green halves and a Beetle spawn. They are handled
before bitset indexing. The source's food reinterpretations have readable
names and effect descriptions. A 56-byte extension keeps inventory, skills,
bottle contents and upgrades independently of the old save record.

New equipment IDs append after the eight old IDs. Metadata supplies names,
verbs, tier, prerequisites, category, repeatability and native16px icon frame.
The menu, journal, reward generator and HUD consume that same metadata.
Bottle1 repeat awards fill the next unowned vessel rather than erasing an
existing bottle's contents. Bag/quiver upgrades stack through three levels.

Restored controls and mechanics:

- Boomerang2px/30outbound updates, Magic2.5px/60 with steering; return speed
  ramps, stuns, switches and pickup retrieval. Multipart enemies receive
  weapon contact before body collision.
- Gust Jar slows movement to0.5, vacuums dust/webs and pulls pickups/enemies;
  medium charge120 and large240. Pacci moves2px/update, flips susceptible
  enemies and charges visible spring holes. Fire Rod4px/update burns and
  melts marked ice. Light Arrows4px/update consume arrow ammunition.
- Pegasus has a16-update windup,3px dash (2.5 Minish), wall bounce and marked
  dash-wall breaks. Mole Mitts dig marked soil/walls with a dig-upgrade speed
  benefit and a distinct digging event hook.
- Spin charge80 (40 Fast), release34updates (68 Long), circular hit area and
  sword-level4/6/8 damage; Great Spin widens it. Roll Thrust (the actual source PL_SWORD_THRUST: trained roll slide,4/6 damage), Dash cuts, Rock Breaker,
  Sword/Peril beams3.5px/update and held-sword Down Thrust are separate skills.
  The previously approved ordinary sword swing keeps its animation and hitbox.
- Four Sword clones stage on visible plates while charging and activate on
  release. Up to three mirror movement and pressure; walls/hurt dissolve them.
- Bottles catch water/fairies, keep two milk servings, drink potions, pour
  water/mineral water on sprouts/ice, consume bottle charms and picolytes.
  A stored fairy automatically rescues a lethal hit. Home Ocarina warps home.
- Flippers enable swimming/dive; swimming upgrade speeds it up. R at a marked
  portal changes Minish form, with new8×16 art and root-owned4×4 collision.
- New visible terrain includes ice inertia, swamp sinking while stationary,
  shallow water, dust, lava/burning, slopes,4conveyors, soft earth/dig walls,
  Pacci spring holes, Minish portal/gaps, clone plates, crumbling floors,
  dash walls, ice blocks and thirsty sprouts. Sparse room state supplements
  actual native tiles; it never makes invisible terrain into a puzzle.
- Enemy slow, silence, freeze, burn, shock, confusion and capture states have
  timers/immunities. Button shaking escapes captures/freeze. Captor retirement
  releases Bloom safely. Movement ownership cannot overwrite death/talking.

Cream climbing, cart/parachute/layers, and the wider interactive-object
vocabulary are separate additive modules, not aliases for these item enums.

## Revised standard bombs

The user explicitly replaced the150-update placed fuse. An equipped A/B/L
press starts charging; release launches once and consumes one seed. Tap≤3
updates drops at the feet;30updates sends24px;60 sends32px. Holding beyond60
never increases range. Flight12–20updates starts at hand height and ends at
floor height. Every travelled pixel checks walls; impact occurs at the last
safe location. The shared `objects_blast` retains terrain reactions,8enemy
and4self damage. Two active bombs remain the limit. Room/menu/hurt interrupts
cancel a held throw without spending ammunition. Remote Bombs remain a
separate optional command-detonated tool; their landed bombs never auto-fuse.
Enemy bomb actors keep their own documented timers.

## Art and resource rules

`art/handoff_items.py` draws all new icons directly at16×16, tool effects at
16×16 and Minish poses at8×16. Two new16-color RGB555 terrain banks are packed
only in annex/Cream sets; old forest and Drain tile/palette payloads are not
changed. Quiet horizontal floor clusters, material outlines and explicit
silhouettes communicate the verbs. Source artwork previews are labeled as
source art and are not passed off as emulator output.

World pickups recycle four-tile streamed slots by live actor ownership. Tool
FX share one resident sheet. Scene reset clears transient tool allocations
but deliberately preserves the new builder's surface records. Root clears
surface records **before** building the next room.

## Verification

- `python tools/handoff_items_review.py` compiles and executes the actual
  `bomb_throw.c` against a deterministic host room/input fixture:259checks,
  including all facings, exact ranges/cap, last-safe wall impact, A/L control,
  cancellation, ammunition/actor exhaustion and remote command detonation.
- ARM syntax checks pass for `legacy_items.c`, `bomb_throw.c` and `items.c`
  against the integrated generated asset definitions.
- Native source art generation validates final hardware-sized indexed pixels.
  Runtime mGBA evidence is recorded by the integrated review; host tests and
  source atlases alone do not establish hardware performance or visual quality.

The first integrated mGBA tool pass used only disclosed inventory/ammunition,
bottle contents and player navigation fixtures. It observed real tool actors,
damage values, arrow spending, Gust charge, Cape height, and actual bomb damage
followed by potion healing and bottled-fairy lethal rescue. It also exposed a
Boots collision-return inversion: a clear movement was mistakenly treated as a
wall. The condition was corrected in source. Re-run the portable
`handoff_items_native.py --bundle BUNDLE --out OUT` on the final bundle; the
initial18/19result is a diagnostic pass, not a claim that the old failing ROM
was verified.

Arrow Butterfly follows the source `itemBow.c` animation-recovery upgrade,
not an invented projectile-speed bonus: it shortens cooldown16→8 while keeping
normal3px and Light4px arrow travel. Four Sword charging works without learning
Spin first, and clones press the same live plates as the hero. Diving has an
explicit submerged visual and vulnerability predicate. Shallow water is1px
walking between dry1.25 and deep0.75; burning forces a3px run, with R to put it
out. These added movement paths reuse the selected Bloom walk poses.
