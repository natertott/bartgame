# Charting the world: the mapexplore build and its mGBA overlay

The purpose of this pair is to turn walking around the world into DATA - an
edge list of rooms with the requirements to cross between them, and the tile
classes that impose those requirements. It is stage 2 of the
world-reachability model in the roadmap.

## The build

    make mapexplore          # -> tmc.gba, copy it aside as tmc-mapexplore.gba

Vanilla Minish Cap with the whole main quest done except the Vaati fight:

* **every item** - all 20 gating items verified held at boot (all three
  swords, both bombs and bows and boomerangs, both shields, lantern, gust
  jar, Pacci Cane, Mole Mitts, Roc's Cape, Pegasus Boots, Grip Ring, Power
  Bracelets, Flippers), plus the four Elements and every sword skill;
* **every dungeon cleared**, the Elemental Sanctuary sequence done,
  `global_progress` 9;
* **all 100 kinstone fusions already fused**, which is what holds the
  overworld in its post-fusion shape - dozens of bridges, NPCs and obstacles
  in roomInit.c gate on `CheckKinstoneFused`;
* kinstone DROPS left enabled, so the bag still fills if you want it;
* deliberately NOT set: `ENDING`, `GAMECLEAR`, `LV6_CLEAR`. The point is to
  stop just short of Vaati.

It boots into South Hyrule Field just outside Hyrule Town's south gate.
(Not inside the town: a direct boot-spawn there freezes the pause menu -
`gArea.dungeon_idx` underflows for non-dungeon areas and
`DrawDungeonMapActually` indexes with it unchecked.)

QUICKSTART is off in this build. You are walking VANILLA's world, which is
the world the requirements model is about.

## The overlay

In mGBA: **Tools > Scripting > Load script**, pick
`tools/quickstart/mapexplore.lua`.

It gives three things:

**A live panel** - area and room by name, the room's size and origin, your
world/local/tile position, the collision layer, the tile class under your
feet, the four neighbouring collision bytes, and which gating items you
hold.

**A room-change line, logged automatically.** Every door, seam and border
you cross writes a `ROOM a / b -> c / d` line plus the arrival coordinates.
That log IS the edge list of the world graph, written as you walk it - it is
the single most valuable output, and it costs you nothing to collect.

**A waypoint on L+R** - the same stamp on demand, for pinning a spot you
want to come back to or a square you had to do something special to reach.

## What to record, and why the tile class matters

When you find a square that needs an item, note its **tile class** - the
`coll / type / act` triple the panel prints. The requirement is a property
of the CLASS, not of that square: the fifteen region rooms already surveyed
hold ~24,000 tiles but only 397 distinct classes, so recording "this class
needs the Flippers" once teaches the model every tile of that kind in the
game. That 60:1 ratio is what makes charting the whole world tractable.

Worth a note whenever you see one:

* a square you could only reach with a specific item (class + item);
* a border or seam that is one-way (the room-change log shows the direction
  you actually crossed);
* a room whose parts do not connect (walk between them - if you cannot, the
  model needs to know they are separate components, and what joins them);
* anything a kinstone fusion opened, since this build has them all fused and
  a real run will not.

## Regenerating the script

Area and room names are baked in at generation time, from the decomp's
headers:

    python3 tools/quickstart/make_mapexplore_lua.py

Edit the logic in `mapexplore_body.lua` and re-run that; `mapexplore.lua`
is generated and self-contained (no `require`, so mGBA can load it from
anywhere).
