"""The tile spec's content: every background tile that renders in the wood,
its mystery rooms and the Drain, as entries an artist can draw from.

An entry: key (the delivery file's name), title, mts (the metatiles it
covers, in delivery order), shape, layer, group, frames and rate,
solid, what it is, what it needs.

shape: ('one',) one tile; ('vars', n) n variants side by side;
('piece', cols, rows) one picture of cols x rows tiles; ('fam', kind)
fifteen edge combinations side by side (kind 'side' or 'corner').
layer: 'ground' (opaque) or 'overlay' (over the sprites, transparent
outside the drawing) or 'both' (a crown on the overlay over trunks on the
ground).
"""

SIDE = ['N', 'E', 'N+E', 'S', 'N+S', 'E+S', 'N+E+S', 'W', 'N+W', 'E+W', 'N+E+W', 'S+W', 'N+S+W', 'E+S+W', 'N+E+S+W']
CORNER = ['NW', 'NE', 'NW+NE', 'SE', 'NW+SE', 'NE+SE', 'NW+NE+SE', 'SW', 'NW+SW', 'NE+SW', 'NW+NE+SW', 'SE+SW', 'NW+SE+SW', 'NE+SE+SW', 'all four']

GROUPS = [
    # area, key, what goes in it; done: the delivered atlases' groups, as imported
    ('wood', 'wood_ground', 'grass in all its variants, flowers, tall grass, bones, the trail, mossy flagstones, the meadow, clover and fairy ring, the trail edges, shores and verges, and the grass round tree trunks and roots (so a trunk tile needs its bark colours here too)'),
    ('wood', 'wood_leaf', 'the canopy walls and their faces and crowns, tree crowns, bushes, stumps, logs, thorns, the lantern post; the hollow and the thicket'),
    ('wood', 'wood_water', 'water, its banks, nicks and lilies, rafts, falls and foam, and the bridges'),
    ('wood', 'wood_stone', 'rocks, boulders, cliffs, pillars, the ruined wall, the statue, pits, the gates, chests, censers, the stairs, the mystery mouths; the cave and the mystery rooms\' plates, pots, chest and spring'),
    ('wood', 'wood_blight', 'the rot, the stains, the blight pool, crystals and snags, and the blighted twin of every wood group (a second palette strip each)'),
    ('wood', 'blight_growth', 'done: the blighted tree\'s crown'),
    ('wood', 'glints', 'done: the wood\'s gold and white sparkles, the Drain\'s glints and its glowing fungus'),
    ('drain', 'drain_stone', 'done: floors and their marks, walls, wall tops, the hole, the arch, the banks, the drain'),
    ('drain', 'drain_water', 'done: water and its marks, bubbles, the waterfall, the grate, the ladder, the teal banner'),
    ('drain', 'drain_props', 'done: the stall, the rug, barrels, crates, skull, pot, gold, rubble, candles, pipes, the red banner, the lantern, the torch'),
]


def E(key, title, mts, shape, layer, group, what, needs='', frames=1, rate=None, solid='walkable'):
    return dict(key=key, title=title, mts=mts, shape=shape, layer=layer, group=group, what=what,
                needs=needs, frames=frames, rate=rate, solid=solid)


def fam(prefix):
    return [prefix + '%x' % m for m in range(1, 16)]


WOOD = [
    ('Ground of the living wood', 'Most of every living room. Mostly plain, so the sprites read against it.', [
        E('grass', 'Grass', ['moss0', 'moss1', 'moss2'], ('vars', 3), 'ground', 'wood_ground',
          'Short dark-olive grass: a few darker blade clusters, a few lit tips. Three variants laid at random.',
          'Each tiles with itself and with the other two in every direction. No single tuft, flower or stone that repeats visibly when 300 of them are laid together.'),
        E('grass_stain', 'Grass, blight stain', ['moss_blight', 'moss_blight2'], ('vars', 2), 'ground', 'wood_ground',
          'Grass with the blight creeping in: a small violet bruise and a thin crack of magenta light. An accent, about one tile in eight.',
          'Edges match plain grass.'),
        E('flowers', 'Flowers', ['moss_flowers', 'moss_flowers2'], ('vars', 2), 'ground', 'wood_ground',
          'Grass with a few small flowers: white star flowers; blue bells. Scattered, and under the gold sparkle of a hidden hoard.',
          'Edges match plain grass; keep the flowers inside the tile.'),
        E('tall_grass', 'Tall grass', ['tall_grass'], ('one',), 'ground', 'wood_ground',
          'A clump of taller, brighter blades on grass. The Bloom walks over it.', 'Edges match plain grass.'),
        E('bones', 'Bones', ['bones'], ('one',), 'ground', 'wood_ground',
          'Grass with old bones half sunk in it: a skull, a rib. An accent in the boneyards and beside dead trees.', 'Edges match plain grass.'),
        E('trail', 'Trail', ['path'], ('one',), 'ground', 'wood_ground',
          'Packed earth, warm brown with small pebbles: the lanes in from the doors, the ways between clearings, the open door gaps.',
          'Tiles with itself in every direction. The grass meets it through the trail edges below.'),
        E('flagstone', 'Mossy flagstone', ['mossy_stone'], ('one',), 'ground', 'wood_ground',
          'An old flat flagstone sunk in moss and grass. The ruins\' floor, the spot where the relic lies, the shrine\'s step once used.',
          'Edges are grass, so it sits on grass on any side.'),
        E('meadow', 'Meadow', ['meadow_%d' % i for i in range(9)], ('piece', 3, 3), 'ground', 'wood_ground',
          'A flower meadow painted whole: taller grass and flowers in a 48x48 patch.', 'Its outer edge fades into plain grass on all four sides.'),
        E('clover', 'Clover patch', ['clover_%d' % i for i in range(4)], ('piece', 2, 2), 'ground', 'wood_ground',
          'A patch of clover, 32x32.', 'Its outer edge fades into plain grass on all four sides.'),
        E('fairy_ring', 'Fairy ring', ['shroomring_%d' % i for i in range(4)], ('piece', 2, 2), 'ground', 'wood_ground',
          'A ring of small pale mushrooms on grass, 32x32. Laid in living and blighted rooms alike.', 'Its outer edge fades into plain grass on all four sides.'),
    ]),
    ('Edges of the living wood', 'No boundary in a living room is a hard line. Each of these is the grass or trail tile with an edge on the marked sides, in fifteen combinations. Read the labels as "the neighbour on that side is water", "is the canopy" or "is grass". Corners where two marked sides meet join round, not square.', [
        E('trail_edge', 'Trail edges', fam('pedge_'), ('fam', 'side'), 'ground', 'wood_ground',
          'The trail with ragged grass creeping over its edge on the marked sides, and a little shadow under the tufts.',
          'The unmarked sides are plain trail. The grass side must meet plain grass.'),
        E('shore', 'Shores', fam('shore_'), ('fam', 'side'), 'ground', 'wood_ground',
          'Grass beside water on the marked sides: a dark soil lip, a strip of sand or mud, reeds dipping in.',
          'The unmarked sides are plain grass. The water tile beside it draws the bank\'s other half, so the two must meet.'),
        E('shore_corner', 'Shore nicks', fam('shore_c'), ('fam', 'corner'), 'ground', 'wood_ground',
          'Grass touching water only at the marked corners: a small curved nick of shore in that corner.',
          'Everything but the marked corners is plain grass.'),
        E('verge', 'Verges', fam('verge_'), ('fam', 'side'), 'ground', 'wood_ground',
          'Grass beside the canopy wall on the marked sides. A wall to the north casts shadow and drops leaves; walls east or west push undergrowth and roots in; a wall to the south has ferns at its foot. A cliff above counts as a wall to the north.',
          'The unmarked sides are plain grass. The wall side must meet the canopy\'s face, its crown or its plain mass.'),
        E('trail_corner', 'Trail nicks', fam('pedge_c'), ('fam', 'corner'), 'ground', 'wood_ground',
          'The trail with grass at the marked corners only: a rounded tongue of grass in that corner, where a trail turns.',
          'Everything but the marked corners is plain trail; the nick meets the trail edges and plain grass round the corner.'),
        E('verge_corner', 'Verge nicks', fam('verge_c'), ('fam', 'corner'), 'ground', 'wood_ground',
          'Grass touching the canopy only at the marked corners: a little shade and a leaf or two hanging in that corner.',
          'Everything but the marked corners is plain grass.'),
    ]),
    ('Water', 'Ponds, rivers and lakes. Water is drawn under the sprites; the Bloom swims or sinks in it. Every water tile has two frames that alternate every 20 frames, so ripples drift.', [
        E('water', 'Open water', ['water'], ('one',), 'ground', 'wood_water',
          'Dark teal-blue depth with slow light ripples.', 'Tiles in every direction in both frames.', frames=2, rate=20),
        E('water_bank', 'Water banks', fam('water_'), ('fam', 'side'), 'ground', 'wood_water',
          'Water with a bank on the marked sides: the lip where ground meets it, a line of foam along it. Ground means grass, the canopy or a cliff.',
          'The unmarked sides are open water. Each bank meets the shore tile beside it.', frames=2, rate=20),
        E('water_nick', 'Water nicks', fam('water_c'), ('fam', 'corner'), 'ground', 'wood_water',
          'Open water with ground touching only at the marked corners: a small rounded bit of bank in that corner.',
          'Everything but the marked corners is open water.', frames=2, rate=20),
        E('lily', 'Lily', ['water_lily'], ('one',), 'ground', 'wood_water',
          'Open water with a lily pad and a small white flower.', 'One in five open water tiles.', frames=2, rate=20),
        E('lily_raft', 'Lily raft', ['raft_%d' % i for i in range(4)], ('piece', 2, 2), 'ground', 'wood_water',
          'A great raft of lily pads on open water, 32x32. Still water underfoot.', 'Its edge is open water on all sides.', frames=2, rate=20),
        E('waterfall', 'Waterfall', ['waterfall'], ('one',), 'ground', 'wood_water',
          'Water pouring off a cliff or out of the canopy: lit streaks falling, foam at the lip. A fall is two tiles wide and one or two tall.',
          'Tiles left-right and up-down. The three frames scroll the water down a third of a tile each, so it loops.', frames=3, rate=6),
        E('foam', 'Foam', ['water_foam'], ('one',), 'ground', 'wood_water',
          'The churn where a fall lands: white foam boiling on water, under each tile of a fall.', 'Tiles left-right; its bottom edge meets open water.', frames=2, rate=10),
    ]),
    ('The canopy', 'The wood\'s walls: the border of every room and the masses between its clearings. Solid.', [
        E('canopy', 'Canopy', ['canopy', 'canopy2'], ('vars', 2), 'ground', 'wood_leaf',
          'A dense mass of leaves, blue-black in the depths to lit green on the tops, round clumps lit from the upper left. Two variants laid at random.',
          'Each tiles with itself and the other in every direction, with no visible seams or grid. Large areas of it fill the screen, so it must not look like wallpaper.', solid='solid'),
        E('canopy_glint', 'Canopy, glint', ['canopy_glint'], ('one',), 'ground', 'wood_leaf',
          'Canopy with two leaves that catch the light and wink. One in seven canopy tiles.', 'Matches canopy on every edge.', frames=2, rate=28, solid='solid'),
        E('canopy_lantern', 'Canopy, lantern', ['canopy_lantern'], ('one',), 'ground', 'wood_leaf',
          'Canopy with a small amber lantern hung in the leaves above a way; its glow flickers.', 'Matches canopy on every edge.', frames=2, rate=10, solid='solid'),
        E('canopy_face', 'Canopy face', ['canopy_s'], ('one',), 'ground', 'wood_leaf',
          'The wall\'s lower edge where ground or water lies below: the canopy above, trunks, roots and deep shadow at its foot.',
          'Repeats left-right. Its top meets canopy; its bottom meets grass, the trail or water.', solid='solid'),
        E('canopy_crown', 'Canopy crown', ['canopy_n'], ('one',), 'ground', 'wood_leaf',
          'The wall\'s upper edge where ground lies above it: the lit, rounded tops of the leaf mass.',
          'Repeats left-right. Its bottom meets canopy; its top meets grass or the trail.', solid='solid'),
    ]),
    ('Trees', 'A tree\'s crown is on the overlay, drawn over the Bloom so she walks behind it, and is transparent outside the leaves. Its trunk tiles are ground, grass included, with only their bottom half solid.', [
        E('tree', 'Oak', ['tree_top_nw', 'tree_top_ne', 'tree_mid_w', 'tree_mid_e', 'tree_trunk_w', 'tree_trunk_e'], ('piece', 2, 3), 'both', 'wood_leaf',
          'A free-standing oak, 32x48: a round crown of lit leaf clumps on the top two rows, the trunk and its roots on grass on the bottom row.',
          'Crown tiles: overlay, transparent round the crown. Trunk tiles: ground, the grass round the trunk matching plain grass.', solid='trunk row: bottom half'),
        E('tree_lantern', 'Oak with a lantern', ['tree2_0', 'tree2_1', 'tree2_2', 'tree2_3', 'tree2_4', 'tree2_5'], ('piece', 2, 3), 'both', 'wood_leaf',
          'The oak of another shape, an amber lantern hung in its crown. One tree in three.', 'As the oak.', solid='trunk row: bottom half'),
        E('great_tree', 'Great tree', ['gtree_%d' % i for i in range(12)], ('piece', 3, 4), 'both', 'wood_leaf',
          'A great tree, 48x64: a crown 48x48 on the top three rows, a thick trunk with a dark hollow in the middle of the bottom row, roots spreading over three tiles of grass.',
          'Crown: overlay, transparent outside the leaves; it may overhang the canopy behind. Roots: ground on grass.', solid='middle root: bottom half'),
        E('great_tree_2', 'Great tree, lopsided', ['gtree2_%d' % i for i in range(12)], ('piece', 3, 4), 'both', 'wood_leaf',
          'A second great tree: lopsided, a lantern on its low branch, a knot in the trunk.', 'As the great tree.', solid='middle root: bottom half'),
        E('blight_tree', 'Blighted tree', ['btree_%d' % i for i in range(12)], ('piece', 3, 4), 'both', 'blight_growth',
          'The blighted rooms\' tree, 48x64 like the great trees: a black twisted trunk, bare branches clawing up, magenta veins of light, glow at the tips.',
          'Branches: overlay, transparent between them. Roots: ground on grass, which the blighted rooms show as their earth.', solid='middle root: bottom half'),
    ]),
    ('On the grass', 'Things that stand on a living room\'s floor. Each is drawn on its own patch of grass that matches plain grass at the tile\'s edges.', [
        E('bush', 'Bush', ['bush'], ('one',), 'ground', 'wood_leaf',
          'A round leafy bush with a few berries. Lifted with R and carried, or cut with the sword.', 'Must match the carried bush in the sprite spec (sheet lift).', solid='solid'),
        E('stone_small', 'Small stone', ['rock_small'], ('one',), 'ground', 'wood_stone',
          'A small mossy stone, light enough to lift.', 'Must match the carried stone in the sprite spec.', solid='solid'),
        E('boulder', 'Boulder', ['boulder'], ('one',), 'ground', 'wood_stone',
          'A dark, cracked, mossy boulder. Only the gauntlet lifts it.', 'Must match the carried boulder in the sprite spec.', solid='solid'),
        E('rocks', 'Rocks', ['rock', 'rock2', 'rock3'], ('vars', 3), 'ground', 'wood_stone',
          'Three fixed rocks: a mossy stone sunk in the soil, tufts over its foot; a flat stone buried to its shoulders, grass over its edge; two stones stacked, moss between, lichen on the top one.',
          'They must read as fixed, unlike the small stone.', solid='solid'),
        E('stump', 'Stump', ['stump'], ('one',), 'ground', 'wood_leaf', 'A cut stump: rings on the top, bark down the sides.', '', solid='solid'),
        E('log', 'Log', ['log'], ('one',), 'ground', 'wood_leaf', 'A short fallen log, the rings of its cut end showing.', '', solid='solid'),
        E('hollow_log', 'Hollow log', ['hlog_0', 'hlog_1'], ('piece', 2, 1), 'ground', 'wood_leaf',
          'A hollow log two tiles long: rings at one end, a dark hollow at the other, moss along its back.', '', solid='solid'),
        E('great_boulder', 'Great boulder', ['gboulder_%d' % i for i in range(4)], ('piece', 2, 2), 'ground', 'wood_stone',
          'A great boulder, 32x32: moss on its crown, lichen, a sapling rooted in a crack.', '', solid='solid'),
        E('tree_rock', 'Rock in the roots', ['treerock_%d' % i for i in range(4)], ('piece', 2, 2), 'ground', 'wood_stone',
          'A stone wedged in the roots of a stump, 32x32; roots of soil-brown wrap the stone.', '', solid='solid'),
        E('pillar', 'Pillar', ['pillar'], ('one',), 'ground', 'wood_stone', 'A broken stone pillar of the old ruins.', 'Two pillars often stand with a ruined wall between them, or four in a square.', solid='solid'),
        E('ruin_wall', 'Ruined wall', ['ruin_wall'], ('one',), 'ground', 'wood_stone', 'A stretch of ruined wall, mossy blocks, set between two pillars.', 'Its left and right edges meet a pillar.', solid='solid'),
        E('statue', 'Shrine statue', ['statue'], ('one',), 'ground', 'wood_stone',
          'A stone statue of a seated hare with a glowing gem: the shrine\'s keeper. A flower tile and a sparkle lie at its feet.', '', solid='bottom half'),
        E('lantern_post', 'Lantern post', ['lantern_post'], ('one',), 'ground', 'wood_leaf',
          'A wooden post with an amber lantern hanging from it; the glow flickers.', '', frames=2, rate=10, solid='bottom half'),
        E('thorns', 'Thorns', ['thorn'], ('one',), 'ground', 'wood_leaf',
          'A bramble of dark vines with magenta barbs, on grass. Cut with the sword. Laid in hedges of three, and as a gate across a door gap.',
          'Repeats left-right and up-down, so a hedge reads as one bramble.', solid='solid'),
    ]),
    ('Cliffs, crossings and pits', '', [
        E('cliff', 'Cliff', ['ledge_s_w', 'ledge_s', 'ledge_s_e'], ('vars', 3), 'ground', 'wood_stone',
          'A cliff the Bloom can jump down going south: a grassy brow on top, a face of mossy stone blocks, a foot of soil. Delivered as its west end, its middle, its east end.',
          'The middle repeats left-right; the ends round off. The ground above and below is grass.', solid='solid (a one-way drop to the south)'),
        E('bridge', 'Bridge', ['bridge'], ('one',), 'ground', 'wood_water',
          'A plank bridge over water running east-west, rails along its top and bottom edges.', 'Repeats left-right; its ends meet the trail or grass.'),
        E('bridge_ns', 'Bridge, north-south', ['bridge_v'], ('one',), 'ground', 'wood_water',
          'The same planks running north-south, rails down the sides.', 'Repeats up-down.'),
        E('pit', 'Chasm', ['pit'], ('one',), 'ground', 'wood_stone',
          'A dark drop with a stone lip on its near edge, filling a door gap: the Petal Cloak leaps it.', 'Repeats left-right.', solid='a fall'),
    ]),
    ('Gates and set pieces', 'A room\'s doors are two-tile gaps in its border of canopy. A gate fills the gap: the same tile placed twice, side by side in a north or south wall, one above the other in an east or west wall. Draw each to read as a whole gate either way.', [
        E('crack', 'Cracked wall', ['crack'], ('one',), 'ground', 'wood_stone',
          'A cracked stone wall plugging the gap. A bomb opens it.', 'Its sides meet the canopy.', solid='solid'),
        E('web', 'Web', ['web'], ('one',), 'ground', 'wood_stone',
          'A thick cobweb strung across the gap, on dark stone. The lamp burns it away to trail.', 'Its sides meet the canopy.', solid='solid'),
        E('door_locked', 'Locked door', ['door_locked'], ('one',), 'ground', 'wood_stone',
          'A heavy door in a stone frame with a lock. A key opens it.', 'Its sides meet the canopy.', solid='solid'),
        E('door_open', 'Open door', ['door_open'], ('one',), 'ground', 'wood_stone',
          'The stone frame opened: the trail running through it. What a bombed wall and an unlocked door become.', 'Its sides meet the canopy; the trail runs in and out.'),
        E('stairs', 'Stairs down', ['stairs_down'], ('one',), 'ground', 'wood_stone',
          'A stone arch with steps going down into the dark: the way back to the Drain.', 'Its sides meet the canopy.'),
        E('chest', 'Chest', ['chest', 'chest_open'], ('vars', 2), 'ground', 'wood_stone',
          'A treasure chest on grass, then the same chest opened and empty.', 'The open chest replaces the closed one in place.', solid='solid'),
        E('censer', 'Censer', ['torch'], ('one',), 'ground', 'wood_stone',
          'A stone censer on a short pillar, cold. The lamp lights it.', '', solid='bottom half'),
        E('censer_lit', 'Censer, lit', ['torch_lit'], ('one',), 'ground', 'wood_stone',
          'The censer lit, a flame flickering in its bowl.', 'Replaces the cold censer in place, so the stone must match it.', frames=2, rate=6, solid='bottom half'),
        E('mouths', 'Mystery mouths', ['mouth_cave', 'mouth_hollow', 'mouth_thicket'], ('vars', 3), 'ground', 'wood_stone',
          'The ways into the mystery rooms, set into a canopy face: a mouth in mossy rock; an opening in a great trunk; a dark tunnel through brambles.',
          'Each stands in a row of canopy faces: its top and sides meet the face, its bottom meets the grass.', solid='the way in'),
    ]),
    ('The blight', 'The wood sickens toward its heart. A blighted room is the living wood itself in the blight\'s colours: every palette group of the wood has a blighted twin, the same colours in the same order turned violet-grey earth, ash trail, indigo leaves, dead grey bark, murky water and magenta light, and a blighted room loads the twins. So the blight has every edge the living wood has, and a redrawn wood is a redrawn blight. Deliver, with each wood group, its blighted twin as a second palette strip. What the blight adds of its own: the stains and the rot in the living rooms on the way in, and the crystals, snags, pools and mist.', [
        E('rot', 'Rot', ['rot_%x%x' % (sd, cn) for sd in range(16) for cn in range(16) if not cn & ((1 if sd & 9 else 0) | (2 if sd & 3 else 0) | (4 if sd & 6 else 0) | (8 if sd & 12 else 0))],
          ('vars', 47), 'ground', 'wood_blight',
          'Bare violet earth where the blight breaks through a sick room\'s grass, in soft blobs of several tiles: the first is the earth alone, then one for every way grass can lie around it. Grass on a side (N, E, S, W) or, where it lies only diagonally, at a corner (NW, NE, SE, SW), in the order sides 0..15 and for each the corners its sides leave free.',
          'Where grass lies, the tile fades into plain grass over a few pixels through dull sick greens, so a blob has no line round it. The earth alone is what a blighted room\'s grass becomes in the twin palette.'),
        E('blight_pool', 'Blight pool', ['blight_pool'], ('one',), 'ground', 'wood_blight',
          'A pool of glowing blight that burns to stand in: a dark rim, a glowing body, slow rings.', 'Drawn on grass, which meets plain grass at the edges.', frames=2, rate=16, solid='walkable, hurts'),
        E('crystal', 'Blight crystals', ['blight_crystal'], ('one',), 'ground', 'wood_blight', 'A cluster of magenta crystals grown out of the grass, glowing at the tips.', 'Drawn on grass.', solid='solid'),
        E('dead_tree', 'Dead tree', ['dead_tree'], ('one',), 'ground', 'wood_blight', 'A small snag the blight has stripped: a crooked trunk, two bare limbs, a knot of light.', 'Drawn on grass.', solid='bottom half'),
    ]),
    ('On the overlay', 'Drawn over the ground and over the sprites, transparent outside the drawing. Keep them small and sparse.', [
        E('sparkle', 'Gold sparkle', ['sparkle'], ('one',), 'overlay', 'wood_spare',
          'A gold glint that winks: marks a hidden hoard, the relic and the shrine, and lies on the floor here and there.', '', frames=3, rate=14),
        E('sparkle_white', 'White stars', ['sparkle_white'], ('one',), 'overlay', 'wood_spare',
          'Two small white four-point stars that wink, over the living rooms\' floors.', '', frames=2, rate=16),
        E('mist', 'Blight mist', ['blight_mist'], ('one',), 'overlay', 'wood_blight',
          'Sparse violet motes of mist drifting over the blighted rooms.', '', frames=2, rate=16),
    ]),
]

MYST = [
    ('The three rooms', 'Behind each mouth in the wood: a damp cave, the hollow of a tree, a thicket of brush. A room is 12x9, 18x12 or 24x16 tiles: a wall border one tile thick, two tiles at the top (the wall mass, then its face), a crown along the bottom wall (its lit top seen from the room), the floor inside shaded toward every wall, the way out in the middle of the bottom wall. The thicket is drawn in the wood\'s own grass, canopy and verges, so the censers and boulders its events stand on meet it.', [
        E('cave', 'Cave', ['cave_wall', 'cave_face', 'cave_crown', 'cave_floor0', 'cave_floor1', 'cave_prop', 'cave_glow', 'cave_exit', 'cave_spring'], ('vars', 9), 'ground', 'wood_stone',
          'Lumps of cool stone for the mass; a face of rock, seams and a little moss; the mass\'s lit tops above a strip of floor; a calm grey floor of gravel; the same with a small puddle (one tile in fourteen); a stalagmite; pale cyan mushrooms; the way out, the floor going down into dark; the fairy\'s spring in a ring of stones.',
          'Mass tiles in every direction. Face and crown repeat left-right. Floors tile with each other. The way out is used twice side by side.', frames=2, rate=12, solid='mass, face, crown, stalagmite: solid'),
        E('cave_edges', 'Cave floor edges', fam('cave_edge_'), ('fam', 'side'), 'ground', 'wood_stone',
          'The floor beside the walls on the marked sides: shade deepening to the wall, and the wall\'s lumps hanging over at east and west. Only N, E, S, W and the four two-side corners are laid.', 'The unmarked sides are plain floor.'),
        E('hollow', 'Hollow', ['hollow_wall', 'hollow_face', 'hollow_crown', 'hollow_floor0', 'hollow_floor1', 'hollow_prop', 'hollow_glow', 'hollow_exit', 'hollow_spring'], ('vars', 9), 'ground', 'wood_leaf',
          'Gnarled bark lumps for the mass; the inner wall of the trunk, its grain running down; the lumps\' lit tops; a floor of packed earth and wood chips; a knuckle of root through it; a burl with a cut top; amber fungus; the way out; the spring.',
          'As the cave.', frames=2, rate=12, solid='mass, face, crown, burl: solid'),
        E('hollow_edges', 'Hollow floor edges', fam('hollow_edge_'), ('fam', 'side'), 'ground', 'wood_leaf',
          'As the cave\'s, in the hollow\'s earth and bark.', 'The unmarked sides are plain floor.'),
        E('thicket', 'Thicket', ['thicket_wall', 'thicket_face', 'thicket_crown', 'thicket_floor0', 'thicket_floor1', 'thicket_prop', 'thicket_glow', 'thicket_exit', 'thicket_spring'], ('vars', 9), 'ground', 'wood_leaf',
          'The wood\'s canopy, its face and crown; its grass; a bramble; glowing flowers; the trail going out; the spring on grass.',
          'As the cave. The censers, boulders and grass of the wood also stand here.', frames=2, rate=12, solid='mass, face, crown, bramble: solid'),
        E('thicket_edges', 'Thicket floor edges', fam('thicket_edge_'), ('fam', 'side'), 'ground', 'wood_ground',
          'The wood\'s verges.', 'The unmarked sides are plain grass.'),
    ]),
    ('Things in every room', 'Drawn on the overlay over any style\'s floor, transparent round the drawing. One drawing serves all three styles.', [
        E('plate', 'Stone plate', ['myst_switch', 'myst_switch_down'], ('vars', 2), 'overlay', 'wood_stone',
          'A round stone plate set in the floor, raised; then pressed down and lit.', 'Keep it low and flat: the Bloom stands on it.'),
        E('pot', 'Pot', ['myst_pot'], ('one',), 'overlay', 'wood_stone', 'A clay pot, lifted or smashed; one in six holds a prize.', 'Must match the carried pot in the sprite spec.'),
        E('room_chest', 'Chest', ['myst_chest', 'myst_chest_open'], ('vars', 2), 'overlay', 'wood_stone', 'A chest, closed and then open.', ''),
    ]),
]

DRAIN = [
    ('The floor', 'The hall\'s flagstones. Every floor tile tiles with every other in any arrangement.', [
        E('d_floor', 'Flagstones', ['sw_floor0'], ('one',), 'ground', 'drain_stone',
          'Worn flagstones in a quiet mottle of two close tones, laid over the whole floor.', 'Tiles in every direction with no visible grid.'),
    ]),
    ('The walls', 'The back wall across the top of the hall is three rows: the wall\'s top course seen from above, then two rows of brick face. The bottom row of the hall is one row of brick face. All of it is solid.', [
        E('d_wall_top', 'Wall top', ['sw_wall_top', 'sw_wall_top_moss'], ('vars', 2), 'ground', 'drain_stone',
          'The top of the wall seen from above: heavy capstones; and with moss over them.', 'Repeats left-right; its bottom meets the brick face.', solid='solid'),
        E('d_wall', 'Brick face', ['sw_wall'], ('one',), 'ground', 'drain_stone',
          'Old wet bricks, the hall\'s wall face.', 'Tiles left-right and up-down (the face is two rows tall). Every marked wall below matches it on every edge.', solid='solid'),
        E('d_wall_drip', 'Bricks, dripping', ['sw_wall_drip'], ('one',), 'ground', 'drain_stone', 'A wet streak down the bricks beside the waterfall, a drop sliding down it and falling.', '', frames=3, rate=9, solid='solid'),
        E('d_pipes', 'Pipe', ['sw_pipe'], ('one',), 'ground', 'drain_stone',
          'A rusted pipe mouth in the wall.', '', solid='solid'),
        E('d_banners', 'Banners', ['sw_banner_teal', 'sw_banner_red'], ('vars', 2), 'ground', 'drain_props', 'Banners hung on the bricks, teal and rust-red, a gold sigil on each.', '', solid='solid'),
        E('d_lantern', 'Lantern', ['sw_lantern'], ('one',), 'ground', 'drain_props', 'A lantern hung on the bricks, its glow flickering.', '', frames=2, rate=10, solid='solid'),
        E('d_torch', 'Wall torch', ['sw_torch_lit'], ('one',), 'ground', 'drain_props', 'A torch burning in an iron sconce on the bricks.', '', frames=2, rate=6, solid='solid'),
        E('d_hole', 'The drain hole', ['sw_hole'], ('one',), 'ground', 'drain_stone', 'A dark round opening in the back wall: the way up to the wood.', '', solid='the way out'),
        E('d_waterfall', 'Waterfall', ['sw_fall_%d' % i for i in range(6)], ('piece', 3, 2), 'ground', 'drain_water',
          'Water pouring out of the back wall into a basin, 48x32: wall stones either side, the fall, its splash at the foot.', 'Its foot meets the basin\'s water below.', frames=2, rate=6, solid='solid'),
        E('d_arch', 'Arch', ['sw_arch', 'sw_arch_r'], ('piece', 2, 1), 'ground', 'drain_stone', 'A dark low arch in the bottom wall, 32x16.', 'Its sides meet the brick face.', solid='top half'),
    ]),
    ('The channel and the pools', 'A channel of dark water crosses the hall, and two pools lie in its lower corners. The water carries no bank of its own: the floor tiles beside it draw the lip.', [
        E('d_water', 'Water', ['sw_water'], ('one',), 'ground', 'drain_water', 'Dark teal sewer water with slow ripples.', 'Tiles in every direction in both frames.', frames=2, rate=20),
        E('d_lily', 'Lily pad', ['sw_lilypad'], ('one',), 'ground', 'drain_water', 'The water with a lily pad on it; two lie in the channel.', 'Matches plain water on every edge.', frames=2, rate=20),
        E('d_bank_above', 'Bank, water below', ['sw_water_edge_n'], ('one',), 'ground', 'drain_stone',
          'Flagstones with the stone lip of the channel along their bottom edge.', 'Repeats left-right; its bottom meets water.'),
        E('d_bank_below', 'Bank, water above', ['sw_water_edge_s'], ('one',), 'ground', 'drain_stone',
          'Flagstones with the lip along their top edge, moss hanging over it.', 'Repeats left-right; its top meets water.'),
        E('d_grate', 'Grate', ['sw_grate', 'sw_grate_r'], ('piece', 2, 1), 'ground', 'drain_water', 'An iron grate over the channel in a brass frame, 32x16, black water beneath: the way across.', 'Laid four high, so its top and bottom meet.'),
        E('d_ladder', 'Ladder down', ['sw_ladder_down'], ('one',), 'ground', 'drain_water', 'A ladder going down over the bank into a pool.', 'It stands in a row of bank tiles.'),
    ]),
    ('The stall and the rug', 'The Peddler keeps a stall under a red awning on the left, a crate beside it; the Gatekeeper stands on a glowing rug on the right. Nothing else lies on the floor.', [
        E('d_drain', 'The great drain', ['sw_drain_nw', 'sw_drain_ne', 'sw_drain_sw', 'sw_drain_se'], ('piece', 2, 2), 'ground', 'drain_stone',
          'A great round drain in the floor, 32x32: an iron ring, bars, darkness below.', 'Its outer edge is flagstone.'),
        E('d_rug', 'Rug', ['sw_rug_nw', 'sw_rug_ne', 'sw_rug_sw', 'sw_rug_se'], ('piece', 2, 2), 'ground', 'drain_props',
          'The Gatekeeper\'s rug, 32x32: violet with a gold border and a faint glow.', 'Its outer edge is flagstone.'),
        E('d_awning', 'Awning', ['sw_awning_l', 'sw_awning_r'], ('piece', 2, 1), 'ground', 'drain_props',
          'The stall\'s red awning, 32x16, scalloped hem, seen from above.', 'Laid twice side by side, so its ends meet.', solid='solid'),
        E('d_crate', 'Crate', ['sw_crate'], ('one',), 'ground', 'drain_props', 'A crate on flagstones beside the stall.', '', solid='solid'),
        E('d_counter', 'Counter', ['sw_counter', 'sw_counter_r'], ('piece', 2, 1), 'ground', 'drain_props', 'The Peddler\'s counter, 32x16: planks on a stone base, his wares on it, a banner hung on its front.', 'Laid twice side by side, so its ends meet.', solid='solid'),
    ]),
    ('On the overlay', 'Glints that wink over the water, the walls and the rug only, so nothing on the open floor looks like a thing to pick up.', [
        E('d_glints', 'Glints', ['sw_glint', 'sw_glint2', 'sw_glint3'], ('vars', 3), 'overlay', 'drain_spare',
          'Three small glints of light, each a different shape and speed.', 'Transparent but for the glint. Rates 12, 14 and 18.', frames=3, rate=12),
    ]),
]

ADDITIONS = [
    ('Gates by orientation', 'Each gate (cracked wall, web, locked and open door, stairs) as two halves, one pair for north and south walls and one for east and west walls, so a door in a side wall can be drawn from the side.'),
    ('Pool banks in the Drain', 'Banks with the water to the left and to the right, and the four outer corners, so the pools and the basin under the waterfall get a lip on every side.'),
]

SPRITES = {
    'wood': 'the Bloom; beetles, bats, slimes, spitters, knights and the Blight Heart; the folk; pickups, effects, arrows and thrown loads; the mouth in the ground',
    'drain': 'the Bloom; the Peddler and the Gatekeeper; pickups and effects',
}
