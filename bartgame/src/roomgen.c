/* BARTGAME: a forest room from a maze cell. Deterministic from the world
   seed and the cell index, so a room is the same every visit.

   A room is 32x24 metatiles and starts as solid canopy. The generator
   carves it: a corridor in from each open door, two to four clearings,
   and winding paths between them whose width wanders between three
   tiles and one, so a glade opens and then the trunks squeeze in. A
   clearing can be a lake round an island, and a path that meets water
   runs straight over it on planks. A river may meander across the room,
   bridged where the paths cross it. A room with no water may rise: the
   upper part stands behind a cliff of ledges the hero can drop from, and
   one ramp leads back up. A soil trail follows the middle of every path.

   Then the dressing: trees in the big clearings, bushes and stones that
   narrow the paths without ever closing them, flowers, tall grass,
   lantern posts, the archetype's ruins or bones or crystals, and a hoard
   dug into the wall behind a bush or a boulder. The canopy is tiled by
   what lies beside it: a face of trunks above ground, a lit crown below
   it, lanterns hung over the paths. Everything the run depends on is
   placed on ground the flood from the first door reaches, and a door the
   flood misses is carved to. */
#include "gba.h"
#include "util.h"
#include "room.h"
#include "world.h"
#include "roomgen.h"

RoomSpots gSpots;
static Rng sR;
static u8 sReach[FOREST_W * FOREST_H];

#define W FOREST_W
#define H FOREST_H

/* the carve mask: what a tile will be before it is dressed */
enum { M_WALL, M_FLOOR, M_WATER, M_BRIDGE_H, M_BRIDGE_V, M_LEDGE, M_RAMP };
static u8 sMask[H][W];
/* the paths: which way they run where they run, and their middle line */
#define P_H 1
#define P_V 2
#define P_MID 4
static u8 sPath[H][W];

typedef struct {
    s8 x, y, rx, ry;
    u8 lake;
} Clearing;
static Clearing sClear[5];
static int sClearCount;

/* ------------------------------------------------------------ helpers -- */
static bool8 inside(int x, int y) {
    return x >= 0 && y >= 0 && x < W && y < H;
}

/* the carvable part: the border stays, two rows thick on top so the
   wall's face shows under the canopy */
static bool8 interior(int x, int y) {
    return x >= 1 && y >= 2 && x <= W - 2 && y <= H - 2;
}

static u8 type_at(int x, int y) {
    return inside(x, y) ? room_type(x, y) : TT_SOLID;
}

static bool8 passable(int x, int y) {
    u8 t = type_at(x, y);
    return t == TT_FLOOR || t == TT_SLOW || t == TT_HURT || t == TT_THORN || t == TT_DOOR_OPEN || t == TT_STAIRS;
}

static bool8 in_ellipse(int dx, int dy, int rx, int ry) {
    return dx * dx * ry * ry + dy * dy * rx * rx <= rx * rx * ry * ry;
}

/* door opening tiles per side: two metatiles */
void roomgen_gate_tiles(int side, int* x0, int* y0, int* x1, int* y1) {
    switch (side) {
        case SIDE_N: *x0 = W / 2 - 1; *x1 = W / 2; *y0 = 1; *y1 = 1; break;
        case SIDE_S: *x0 = W / 2 - 1; *x1 = W / 2; *y0 = H - 1; *y1 = H - 1; break;
        case SIDE_E: *x0 = W - 1; *x1 = W - 1; *y0 = H / 2 - 1; *y1 = H / 2; break;
        default: *x0 = 0; *x1 = 0; *y0 = H / 2 - 1; *y1 = H / 2; break;
    }
}

/* where the player stands when arriving from a side, in pixels */
void roomgen_door_pos(int side, int* px, int* py) {
    switch (side) {
        case SIDE_N: *px = W * 8; *py = 2 * 16 + 20; break;
        case SIDE_S: *px = W * 8; *py = (H - 1) * 16 - 4; break;
        case SIDE_E: *px = (W - 1) * 16 - 6; *py = H * 8 + 8; break;
        default: *px = 1 * 16 + 6; *py = H * 8 + 8; break;
    }
}

/* Near a door, or in the lane a player walks along when entering: a
   chest there opens itself as the hero arrives, a torch there blocks the
   door. The lane is the four tiles wide the door is centred on, for the
   first six tiles into the room. */
static bool8 near_door(int x, int y) {
    int s, x0, y0, x1, y1;
    for (s = 0; s < 4; s++) {
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        if (ABS(x - x0) <= 3 && ABS(y - y0) <= 3)
            return TRUE;
        if (ABS(x - x1) <= 3 && ABS(y - y1) <= 3)
            return TRUE;
    }
    if (x >= W / 2 - 2 && x <= W / 2 + 1 && (y <= 6 || y >= H - 7))
        return TRUE;
    if (y >= H / 2 - 2 && y <= H / 2 + 1 && (x <= 6 || x >= W - 7))
        return TRUE;
    return FALSE;
}

static bool8 is_floor(int x, int y) {
    return interior(x, y) && type_at(x, y) == TT_FLOOR && room_get_overlay(x, y) == MT_NONE;
}

/* plain ground, nothing drawn on it yet: the tiles the dressing may take */
static bool8 is_plain(int x, int y) {
    u16 t;
    if (!is_floor(x, y))
        return FALSE;
    t = room_get(x, y);
    return t < MT_MOSS_FLOWERS2 || (t >= MT_BLIGHT_GROUND0 && t <= MT_BLIGHT_FLOOR) || t == MT_MOSS_SHADE;
}

/* a w by h block of plain ground, away from the doors */
static bool8 fits_plain(int x, int y, int w, int h) {
    int dx, dy;
    for (dy = 0; dy < h; dy++)
        for (dx = 0; dx < w; dx++)
            if (!is_plain(x + dx, y + dy) || near_door(x + dx, y + dy))
                return FALSE;
    return TRUE;
}

/* a painting that spans tiles: base + i row-major on the ground */
static void stamp_ground(int x, int y, int w, int h, u16 base) {
    int dx, dy;
    for (dy = 0; dy < h; dy++)
        for (dx = 0; dx < w; dx++)
            room_set(x + dx, y + dy, base + dy * w + dx);
}

/* 3x3 of floor around (x,y) */
static bool8 clear3(int x, int y) {
    int dx, dy;
    for (dy = -1; dy <= 1; dy++)
        for (dx = -1; dx <= 1; dx++)
            if (!is_floor(x + dx, y + dy))
                return FALSE;
    return TRUE;
}

/* Could a solid stand here without cutting the ground in two? The floor
   round it must form a single run round the ring of eight, so whatever
   went through this tile can go round it instead. */
static bool8 simple_spot(int x, int y) {
    static const s8 ring[8][2] = { { -1, -1 }, { 0, -1 }, { 1, -1 }, { 1, 0 }, { 1, 1 }, { 0, 1 }, { -1, 1 }, { -1, 0 } };
    int i, runs = 0, orth = 0;
    if (!is_floor(x, y) || near_door(x, y))
        return FALSE;
    for (i = 0; i < 8; i++) {
        bool8 f = is_floor(x + ring[i][0], y + ring[i][1]);
        bool8 g = is_floor(x + ring[(i + 1) & 7][0], y + ring[(i + 1) & 7][1]);
        if (f && !g)
            runs++;
        if ((i & 1) && f)
            orth++;
    }
    return runs == 1 && orth >= 1;
}

/* The same test for a w by h block: the floor round it must form a
   single run round its ring. */
static bool8 simple_block(int x, int y, int w, int h) {
    int ring[32][2], n = 0, i, runs = 0, any = 0;
    int rx0 = x - 1, ry0 = y - 1, rx1 = x + w, ry1 = y + h;
    for (i = rx0; i < rx1; i++) { ring[n][0] = i; ring[n][1] = ry0; n++; }
    for (i = ry0; i < ry1; i++) { ring[n][0] = rx1; ring[n][1] = i; n++; }
    for (i = rx1; i > rx0; i--) { ring[n][0] = i; ring[n][1] = ry1; n++; }
    for (i = ry1; i > ry0; i--) { ring[n][0] = rx0; ring[n][1] = i; n++; }
    for (i = 0; i < n; i++) {
        bool8 f = is_floor(ring[i][0], ring[i][1]);
        bool8 g = is_floor(ring[(i + 1) % n][0], ring[(i + 1) % n][1]);
        if (f && !g)
            runs++;
        if (f)
            any = 1;
    }
    return runs == 1 && any;
}

/* ------------------------------------------------------------ carving -- */
static void carve(int x, int y) {
    if (interior(x, y) && sMask[y][x] == M_WALL)
        sMask[y][x] = M_FLOOR;
}

static void carve_ellipse(int cx, int cy, int rx, int ry) {
    int x, y;
    for (y = cy - ry; y <= cy + ry; y++)
        for (x = cx - rx; x <= cx + rx; x++)
            if (in_ellipse(x - cx, y - cy, rx, ry))
                carve(x, y);
}

/* a w by w block of path round (x, y), marked with the way it runs */
static void carve_block(int x, int y, int w, bool8 horiz) {
    int dx, dy;
    for (dy = 0; dy < w; dy++)
        for (dx = 0; dx < w; dx++) {
            int px = x + dx - w / 2, py = y + dy - w / 2;
            carve(px, py);
            if (interior(px, py) && sMask[py][px] == M_FLOOR)
                sPath[py][px] |= horiz ? P_H : P_V;
        }
    if (interior(x, y) && sMask[y][x] == M_FLOOR)
        sPath[y][x] |= P_MID;
}

/* A winding path from (x0,y0) to (x1,y1). It mostly heads along the
   longer remaining axis but wanders; every few steps its width changes,
   three tiles, two, or a squeeze of one. Over water it runs straight and
   one plank wide. */
static void carve_path(int x0, int y0, int x1, int y1) {
    int x = x0, y = y0, w = 2, steps = 0, next = 4 + rng_range(&sR, 4), guard = 0;
    int lock = -1; /* on planks the path keeps its axis: 0 x, 1 y */
    bool8 horiz = ABS(x1 - x0) >= ABS(y1 - y0);
    carve_block(x, y, w, horiz);
    while ((x != x1 || y != y1) && guard++ < 600) {
        int ax = ABS(x1 - x), ay = ABS(y1 - y);
        if (lock == 0 && ax)
            horiz = TRUE;
        else if (lock == 1 && ay)
            horiz = FALSE;
        else if (ax == 0)
            horiz = FALSE;
        else if (ay == 0)
            horiz = TRUE;
        else
            horiz = (rng_range(&sR, 4) < 3) ? (ax >= ay) : (ax < ay);
        if (horiz)
            x += (x1 > x) ? 1 : -1;
        else
            y += (y1 > y) ? 1 : -1;
        if (interior(x, y) && (sMask[y][x] == M_WATER || sMask[y][x] == M_BRIDGE_H || sMask[y][x] == M_BRIDGE_V)) {
            if (sMask[y][x] == M_WATER)
                sMask[y][x] = horiz ? M_BRIDGE_H : M_BRIDGE_V;
            lock = horiz ? 0 : 1;
            steps = 0;
            continue;
        }
        lock = -1;
        carve_block(x, y, w, horiz);
        if (++steps >= next) {
            static const u8 widths[6] = { 1, 1, 2, 2, 2, 3 };
            w = widths[rng_range(&sR, 6)];
            next = (w == 1) ? 3 + rng_range(&sR, 3) : 4 + rng_range(&sR, 5);
            steps = 0;
        }
    }
}

/* A clearing's heart becomes a lake: a ring of water round an island, or
   a pond with no island when it is small. The paths already through it
   stay dry, as causeways. */
static void fill_lake(const Clearing* c) {
    int x, y, irx = c->rx - 3, iry = c->ry - 2;
    for (y = c->y - c->ry + 1; y <= c->y + c->ry - 1; y++)
        for (x = c->x - c->rx + 1; x <= c->x + c->rx - 1; x++) {
            if (!interior(x, y) || sMask[y][x] != M_FLOOR || sPath[y][x])
                continue;
            if (!in_ellipse(x - c->x, y - c->y, c->rx - 1, c->ry - 1))
                continue;
            if (irx >= 1 && iry >= 1 && in_ellipse(x - c->x, y - c->y, irx, iry))
                continue;
            sMask[y][x] = M_WATER;
        }
}

/* A river two tiles wide meandering across the room. Ground it crosses
   becomes water; a path it crosses gets planks, straight across. */
static void carve_river(bool8 horizontal) {
    static s8 at[W];     /* the river's position along its length */
    static u8 open[W];   /* it crosses ground here */
    int i, pos = horizontal ? 6 + rng_range(&sR, H - 12) : 7 + rng_range(&sR, W - 14);
    int len = horizontal ? W : H;
    for (i = 0; i < len; i++) {
        int k;
        if (i && (i & 3) == 0)
            pos += (int)rng_range(&sR, 3) - 1;
        at[i] = pos;
        open[i] = 0;
        for (k = 0; k < 2; k++) {
            int x = horizontal ? i : pos + k, y = horizontal ? pos + k : i;
            if (interior(x, y) && sMask[y][x] != M_WALL)
                open[i] = 1;
        }
    }
    for (i = 1; i < len - 1; i++) {
        int k, bridge = 0, seen = 0;
        for (k = -2; k <= 2; k++)
            if (i + k >= 0 && i + k < len && open[i + k])
                seen = 1;
        if (!seen)
            continue; /* it runs on under the trees */
        for (k = 0; k < 2; k++) {
            int x = horizontal ? i : at[i] + k, y = horizontal ? at[i] + k : i;
            if (interior(x, y) && sMask[y][x] == M_FLOOR && (sPath[y][x] & (P_H | P_V)))
                bridge = 1;
        }
        for (k = 0; k < 2; k++) {
            int x = horizontal ? i : at[i] + k, y = horizontal ? at[i] + k : i;
            if (!interior(x, y))
                continue;
            if (sMask[y][x] == M_FLOOR)
                sMask[y][x] = bridge ? (horizontal ? M_BRIDGE_V : M_BRIDGE_H) : M_WATER;
            else if (sMask[y][x] == M_WALL)
                sMask[y][x] = M_WATER;
        }
    }
}

/* The upper part of the room rises. Where the ground runs on from row ty
   into row ty+1 a cliff of ledges takes the step: the hero drops from
   them, and one crossing is a ramp back up. Rows the side doors use are
   left alone. */
static void raise_terrace(void) {
    static const u8 rows[5] = { 7, 8, 13, 14, 15 };
    int ty = rows[rng_range(&sR, 5)], x, n = 0, ramp;
    for (x = 1; x < W - 1; x++)
        if (sMask[ty][x] == M_FLOOR && sMask[ty + 1][x] == M_FLOOR)
            n++;
    if (n < 2)
        return;
    ramp = rng_range(&sR, n);
    for (x = 1; x < W - 1; x++) {
        if (sMask[ty][x] != M_FLOOR || sMask[ty + 1][x] != M_FLOOR)
            continue;
        if (ramp-- == 0) {
            sMask[ty + 1][x] = M_RAMP;
            sPath[ty + 1][x] |= P_MID | P_V;
        } else {
            sMask[ty + 1][x] = M_LEDGE;
        }
    }
}

/* ----------------------------------------------------------- dressing -- */
/* The floor: mostly plain grass, so the sprites read; the blight, the
   flowers, the tall grass and the bones are accents. */
static u16 moss_pick(void) {
    int r = rng_range(&sR, 40);
    if (r < 30)
        return MT_MOSS0 + rng_range(&sR, 3);
    if (r < 33)
        return MT_MOSS_BLIGHT;
    if (r < 35)
        return MT_MOSS_BLIGHT2;
    if (r < 37)
        return MT_MOSS_FLOWERS;
    if (r < 38)
        return MT_MOSS_FLOWERS2;
    if (r < 39)
        return MT_TALL_GRASS;
    return MT_BONES;
}

/* The deep rooms: grass stained violet, the arena purple to the walls. */
static u16 blight_pick(bool8 arena) {
    int r = rng_range(&sR, 20);
    if (arena)
        return r < 15 ? MT_BLIGHT_FLOOR : r < 18 ? MT_BLIGHT_VEIN : MT_BLIGHT_GROUND0;
    return r < 17 ? MT_BLIGHT_GROUND0 + (r & 1) : MT_BLIGHT_GROUND2;
}

/* a free-standing tree: 2x3, crown on the overlay, trunks solid. Both
   trunks must stand without closing a way. */
static bool8 place_tree(int x, int y) {
    int dx, dy;
    if (x < 1 || y < 2 || x + 1 > W - 2 || y + 2 > H - 2)
        return FALSE;
    for (dy = 0; dy < 2; dy++)
        for (dx = 0; dx < 2; dx++)
            if (!is_floor(x + dx, y + dy))
                return FALSE;
    if (!simple_spot(x, y + 2) || near_door(x + 1, y + 2))
        return FALSE;
    room_set(x, y + 2, MT_TREE_TRUNK_W);
    if (!simple_spot(x + 1, y + 2)) {
        room_set(x, y + 2, MT_MOSS0);
        return FALSE;
    }
    room_set(x + 1, y + 2, MT_TREE_TRUNK_E);
    room_set_overlay(x, y, MT_TREE_TOP_NW);
    room_set_overlay(x + 1, y, MT_TREE_TOP_NE);
    room_set_overlay(x, y + 1, MT_TREE_MID_W);
    room_set_overlay(x + 1, y + 1, MT_TREE_MID_E);
    return TRUE;
}

/* the great tree: a 3x3 crown on the overlay over anything, a row of
   roots on plain ground, the trunk solid where it closes no way */
static bool8 place_great_tree(int x, int y) {
    int dx, dy;
    if (x < 1 || y < 2 || x + 2 > W - 2 || y + 3 > H - 2)
        return FALSE;
    for (dy = 0; dy < 3; dy++)
        for (dx = 0; dx < 3; dx++)
            if (room_get_overlay(x + dx, y + dy) != MT_NONE || near_door(x + dx, y + dy))
                return FALSE;
    if (!is_plain(x, y + 3) || !is_plain(x + 1, y + 3) || !is_plain(x + 2, y + 3) || !simple_spot(x + 1, y + 3))
        return FALSE;
    for (dy = 0; dy < 3; dy++)
        for (dx = 0; dx < 3; dx++)
            room_set_overlay(x + dx, y + dy, MT_GTREE_0 + dy * 3 + dx);
    room_set(x, y + 3, MT_GTREE_9);
    room_set(x + 1, y + 3, MT_GTREE_10);
    room_set(x + 2, y + 3, MT_GTREE_11);
    return TRUE;
}

/* n solid pieces of w by h on plain ground, each where it closes no way */
static void scatter_block(u16 base, int w, int h, int n, int tries) {
    int i;
    for (i = 0; i < tries && n > 0; i++) {
        int x = 2 + rng_range(&sR, W - 4 - w), y = 3 + rng_range(&sR, H - 5 - h);
        if (fits_plain(x, y, w, h) && simple_block(x, y, w, h)) {
            stamp_ground(x, y, w, h, base);
            n--;
        }
    }
}

/* n ground paintings of w by h on plain ground */
static void scatter_ground(u16 base, int w, int h, int n, int tries) {
    int i;
    for (i = 0; i < tries && n > 0; i++) {
        int x = 2 + rng_range(&sR, W - 4 - w), y = 3 + rng_range(&sR, H - 5 - h);
        if (fits_plain(x, y, w, h)) {
            stamp_ground(x, y, w, h, base);
            n--;
        }
    }
}

/* n solid things on the grass, each where it narrows a way but never
   closes one */
static void scatter_solid(u16 mt, int n, int tries) {
    int i;
    for (i = 0; i < tries && n > 0; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (is_plain(x, y) && simple_spot(x, y)) {
            room_set(x, y, mt);
            n--;
        }
    }
}

/* n ground accents on plain grass: the trail and the water keep */
static void scatter_floor(u16 mt, int n) {
    int i;
    for (i = 0; i < n; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (is_plain(x, y))
            room_set(x, y, mt);
    }
}

/* a pocket dug two tiles into the wall beside a path, a bush or a
   boulder across its mouth, a hoard inside */
static void dig_alcove(bool8 blighted) {
    static const s8 d[4][2] = { { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } };
    int i;
    for (i = 0; i < 80; i++) {
        int x = 3 + rng_range(&sR, W - 6), y = 4 + rng_range(&sR, H - 8);
        int k = rng_range(&sR, 4);
        int mx = x + d[k][0], my = y + d[k][1];         /* the mouth */
        int ix = x + 2 * d[k][0], iy = y + 2 * d[k][1]; /* the hoard */
        if (!is_plain(x, y) || near_door(x, y) || near_door(mx, my))
            continue;
        if (!interior(mx, my) || !interior(ix, iy) || mx < 2 || mx > W - 3 || my < 3 || my > H - 3)
            continue;
        if (sMask[my][mx] != M_WALL || sMask[iy][ix] != M_WALL)
            continue;
        /* the pocket must be walled on its other sides, so it is a pocket */
        if (sMask[iy + d[k][0]][ix + d[k][1]] != M_WALL || sMask[iy - d[k][0]][ix - d[k][1]] != M_WALL)
            continue;
        if (sMask[iy + d[k][0]][ix + d[k][1]] != M_WALL)
            continue;
        sMask[my][mx] = M_FLOOR;
        sMask[iy][ix] = M_FLOOR;
        room_set(mx, my, (rng_next(&sR) & 1) ? MT_BOULDER : MT_BUSH);
        room_set(ix, iy, blighted ? MT_BLIGHT_FLOOR : MT_MOSS_FLOWERS);
        room_set_overlay(ix, iy, MT_SPARKLE);
        gSpots.treasure.x = ix;
        gSpots.treasure.y = iy;
        gSpots.has_treasure = 1;
        return;
    }
}

/* ------------------------------------------------------- reachability -- */
/* flood from (sx, sy) over passable tiles into sReach */
static void flood_reach(int sx, int sy) {
    static u16 q[W * H];
    int qh = 0, qt = 0;
    memset(sReach, 0, sizeof(sReach));
    if (!passable(sx, sy))
        return;
    sReach[sy * W + sx] = 1;
    q[qt++] = sy * W + sx;
    while (qh < qt) {
        int c = q[qh++];
        int x = c % W, y = c / W;
        static const s8 d[4][2] = { { 0, -1 }, { 1, 0 }, { 0, 1 }, { -1, 0 } };
        int i;
        for (i = 0; i < 4; i++) {
            int nx = x + d[i][0], ny = y + d[i][1];
            if (nx < 0 || ny < 0 || nx >= W || ny >= H)
                continue;
            if (sReach[ny * W + nx] || !passable(nx, ny))
                continue;
            sReach[ny * W + nx] = 1;
            q[qt++] = ny * W + nx;
        }
    }
}

static bool8 reached(int x, int y) {
    return sReach[y * W + x];
}

/* Find a reached spot, not near a door. mode 0: any floor (a monster
   stands anywhere); 1: a solid may stand there; 2: 3x3 of floor. */
static bool8 find_spot(Spot* out, int tries, int mode) {
    int i;
    for (i = 0; i < tries; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!reached(x, y) || near_door(x, y))
            continue;
        if (!is_floor(x, y))
            continue;
        if (mode == 2 && !clear3(x, y))
            continue;
        if (mode == 1 && !simple_spot(x, y))
            continue;
        out->x = x;
        out->y = y;
        return TRUE;
    }
    return FALSE;
}

/* carve passable tiles toward the room center from a blocked spot: the
   repair step when the flood misses a door. Water gets planks. */
static void carve_to_center(int x, int y) {
    int cx = W / 2, cy = H / 2;
    while (x != cx || y != cy) {
        bool8 horiz = (x != cx);
        if (interior(x, y) && !passable(x, y)) {
            room_set(x, y, (room_type(x, y) == TT_WATER) ? (horiz ? MT_BRIDGE : MT_BRIDGE_V) : MT_PATH);
            room_set_overlay(x, y, MT_NONE);
        }
        if (horiz)
            x += (cx > x) ? 1 : -1;
        else
            y += (cy > y) ? 1 : -1;
    }
    if (!passable(cx, cy)) {
        room_set(cx, cy, MT_PATH);
        room_set_overlay(cx, cy, MT_NONE);
    }
}

/* A spot for something the run depends on. Tries for clearance, then
   for a spot that blocks nothing, then opens the room's middle. */
static void ensure_spot(Spot* out) {
    if (find_spot(out, 300, 2))
        return;
    if (find_spot(out, 500, 1))
        return;
    int cx = W / 2, cy = H / 2, dx, dy;
    for (dy = -1; dy <= 1; dy++)
        for (dx = -1; dx <= 1; dx++) {
            room_set(cx + dx, cy + dy, MT_PATH);
            room_set_overlay(cx + dx, cy + dy, MT_NONE);
        }
    out->x = cx;
    out->y = cy;
}

/* ---------------------------------------------------------- the build -- */
void roomgen_build(int cell) {
    Cell* c = &gWorld.cells[cell];
    int x, y, s, i;
    int nodes[4][2], nn = 0;
    bool8 water = FALSE;
    rng_seed(&sR, hash32(gWorld.seed, cell * 7919 + 13));
    memset(&gSpots, 0, sizeof(gSpots));
    memset(sMask, 0, sizeof(sMask));
    memset(sPath, 0, sizeof(sPath));
    bool8 blighted = (c->stage >= 3) || (c->arch == ARCH_ARENA);
    bool8 arena = (c->arch == ARCH_ARENA), entry = (c->arch == ARCH_ENTRY);

    room_clear(W, H, MT_CANOPY);
    for (y = 0; y < H; y++)
        for (x = 0; x < W; x++)
            room_set_overlay(x, y, MT_NONE);

    /* the door corridors, two wide and three deep, and their inner ends */
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1, k;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        for (k = 1; k <= 3; k++) {
            int ox = (s == SIDE_E) ? -k : (s == SIDE_W) ? k : 0;
            int oy = (s == SIDE_N) ? k : (s == SIDE_S) ? -k : 0;
            carve(x0 + ox, y0 + oy);
            carve(x1 + ox, y1 + oy);
            if (interior(x0 + ox, y0 + oy))
                sPath[y0 + oy][x0 + ox] |= P_MID | ((s == SIDE_N || s == SIDE_S) ? P_V : P_H);
            if (interior(x1 + ox, y1 + oy))
                sPath[y1 + oy][x1 + ox] |= P_MID | ((s == SIDE_N || s == SIDE_S) ? P_V : P_H);
            if (k == 3) {
                nodes[nn][0] = x1 + ox;
                nodes[nn][1] = y1 + oy;
                nn++;
            }
        }
    }

    /* the clearings */
    sClearCount = 0;
    if (arena) {
        sClear[0].x = W / 2; sClear[0].y = H / 2; sClear[0].rx = 12; sClear[0].ry = 8; sClear[0].lake = 0;
        sClearCount = 1;
    } else if (entry) {
        sClear[0].x = W / 2; sClear[0].y = H / 2 + 1; sClear[0].rx = 9; sClear[0].ry = 5; sClear[0].lake = 0;
        sClear[1].x = 6 + rng_range(&sR, 4); sClear[1].y = 5 + rng_range(&sR, 3); sClear[1].rx = 3; sClear[1].ry = 2; sClear[1].lake = 0;
        sClearCount = 2;
    } else {
        int k = 3 + rng_range(&sR, 3);
        for (i = 0; i < k; i++) {
            Clearing* cl = &sClear[i];
            cl->x = 6 + rng_range(&sR, W - 12);
            cl->y = 5 + rng_range(&sR, H - 10);
            cl->rx = 3 + rng_range(&sR, 4);
            cl->ry = 2 + rng_range(&sR, 3);
            cl->lake = (cl->rx >= 4 && cl->ry >= 3 && (c->arch == ARCH_POND || rng_range(&sR, 3) == 0)) ? 1 : 0;
            if (cl->lake)
                water = TRUE;
        }
        sClearCount = k;
    }
    for (i = 0; i < sClearCount; i++)
        carve_ellipse(sClear[i].x, sClear[i].y, sClear[i].rx, sClear[i].ry);
    for (i = 0; i < sClearCount; i++)
        if (sClear[i].lake)
            fill_lake(&sClear[i]);

    /* paths: each door to its nearest clearing; the clearings in a chain;
       one more link for a loop when there are three or more */
    for (i = 0; i < nn; i++) {
        int best = 0, bd = 1 << 30, k;
        for (k = 0; k < sClearCount; k++) {
            int d = ABS(nodes[i][0] - sClear[k].x) + ABS(nodes[i][1] - sClear[k].y);
            if (d < bd) {
                bd = d;
                best = k;
            }
        }
        carve_path(nodes[i][0], nodes[i][1], sClear[best].x, sClear[best].y);
    }
    for (i = 0; i + 1 < sClearCount; i++)
        carve_path(sClear[i].x, sClear[i].y, sClear[i + 1].x, sClear[i + 1].y);
    if (sClearCount >= 3 && (rng_next(&sR) & 1))
        carve_path(sClear[0].x, sClear[0].y, sClear[sClearCount - 1].x, sClear[sClearCount - 1].y);

    /* a river, or a terrace: never both */
    if (!arena && !entry && (c->arch == ARCH_POND || rng_range(&sR, 3) == 0)) {
        carve_river(rng_next(&sR) & 1);
        water = TRUE;
    }
    if (!arena && !entry && !water && (c->arch == ARCH_RUINS || c->arch == ARCH_BONEYARD || rng_range(&sR, 3) == 0))
        raise_terrace();

    /* lay the ground */
    for (y = 0; y < H; y++) {
        for (x = 0; x < W; x++) {
            u16 mt;
            switch (sMask[y][x]) {
                case M_FLOOR:
                    if (sPath[y][x] & P_MID)
                        mt = blighted ? MT_BLIGHT_VEIN : MT_PATH;
                    else
                        mt = blighted ? blight_pick(arena) : moss_pick();
                    break;
                case M_WATER: {
                    /* banks where ground lies beside it; lilies only on open water */
                    int bank = ((y == 0 || sMask[y - 1][x] != M_WATER) ? 1 : 0) | ((x == W - 1 || sMask[y][x + 1] != M_WATER) ? 2 : 0) |
                               ((y == H - 1 || sMask[y + 1][x] != M_WATER) ? 4 : 0) | ((x == 0 || sMask[y][x - 1] != M_WATER) ? 8 : 0);
                    if (bank) {
                        mt = MT_WATER + bank;
                    } else {
                        /* open water: ground at a corner nicks it */
                        int diag = ((y == 0 || x == 0 || sMask[y - 1][x - 1] != M_WATER) ? 1 : 0) |
                                   ((y == 0 || x == W - 1 || sMask[y - 1][x + 1] != M_WATER) ? 2 : 0) |
                                   ((y == H - 1 || x == W - 1 || sMask[y + 1][x + 1] != M_WATER) ? 4 : 0) |
                                   ((y == H - 1 || x == 0 || sMask[y + 1][x - 1] != M_WATER) ? 8 : 0);
                        mt = diag ? MT_WATER_C1 + diag - 1 : (rng_range(&sR, 5) == 0) ? MT_WATER_LILY : MT_WATER;
                    }
                    break;
                }
                case M_BRIDGE_H: mt = MT_BRIDGE; break;
                case M_BRIDGE_V: mt = MT_BRIDGE_V; break;
                case M_LEDGE: mt = MT_LEDGE_S; break;
                case M_RAMP: mt = MT_PATH; break;
                default: mt = MT_CANOPY; break;
            }
            room_set(x, y, mt);
        }
    }
    /* a lily raft on each lake's open water, where two by two of water
       has water all round */
    for (i = 0; i < sClearCount; i++) {
        Clearing* cl = &sClear[i];
        int done = 0;
        if (!cl->lake)
            continue;
        for (y = cl->y - cl->ry; y <= cl->y + cl->ry && !done; y++)
            for (x = cl->x - cl->rx; x <= cl->x + cl->rx && !done; x++) {
                int dx, dy, ok = 1;
                for (dy = -1; dy <= 2 && ok; dy++)
                    for (dx = -1; dx <= 2; dx++) {
                        if ((dx == -1 || dx == 2) && (dy == -1 || dy == 2))
                            continue;
                        if (!inside(x + dx, y + dy) || sMask[y + dy][x + dx] != M_WATER) {
                            ok = 0;
                            break;
                        }
                    }
                if (ok) {
                    stamp_ground(x, y, 2, 2, MT_RAFT_0);
                    done = 1;
                }
            }
    }
    /* the ends of a cliff */
    for (y = 2; y < H - 1; y++)
        for (x = 1; x < W - 1; x++)
            if (sMask[y][x] == M_LEDGE) {
                bool8 l = sMask[y][x - 1] == M_LEDGE, r = sMask[y][x + 1] == M_LEDGE;
                if (!l && r)
                    room_set(x, y, MT_LEDGE_S_W);
                else if (l && !r)
                    room_set(x, y, MT_LEDGE_S_E);
            }
    /* grass in the shadow of a wall or a cliff is darker */
    if (!blighted)
        for (y = 2; y < H; y++)
            for (x = 0; x < W; x++)
                if (sMask[y][x] == M_FLOOR && (sMask[y - 1][x] == M_WALL || sMask[y - 1][x] == M_LEDGE) && room_get(x, y) < MT_MOSS_FLOWERS2)
                    room_set(x, y, MT_MOSS_SHADE);

    /* the canopy: a face where ground lies below it, a lit crown where
       ground lies above it, lanterns hung over the ways */
    for (y = 0; y < H; y++) {
        for (x = 0; x < W; x++) {
            u16 mt;
            if (sMask[y][x] != M_WALL)
                continue;
            u8 below = (y + 1 < H) ? sMask[y + 1][x] : M_WALL;
            u8 above = (y > 0) ? sMask[y - 1][x] : M_WALL;
            u8 below2 = (y + 2 < H) ? sMask[y + 2][x] : M_WALL;
            if (below != M_WALL && below != M_WATER)
                mt = MT_CANOPY_S;
            else if (above != M_WALL && above != M_WATER)
                mt = MT_CANOPY_N;
            else if (blighted)
                mt = MT_CANOPY_BLIGHT;
            else if (below == M_WALL && below2 != M_WALL && below2 != M_WATER && rng_range(&sR, 6) == 0 && (x < W / 2 - 2 || x > W / 2 + 1 || y > 1))
                mt = MT_CANOPY_LANTERN;
            else if (rng_range(&sR, 7) == 0)
                mt = MT_CANOPY_GLINT;
            else
                mt = (rng_next(&sR) & 1) ? MT_CANOPY : MT_CANOPY2;
            room_set(x, y, mt);
        }
    }

    /* door openings and their gates through the border */
    for (s = 0; s < 4; s++) {
        int g = c->gate[s];
        int x0, y0, x1, y1;
        if (g == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        if (s == SIDE_N) {
            room_set(x0, 0, MT_PATH); room_set(x1, 0, MT_PATH);
            room_set(x0, 1, MT_PATH); room_set(x1, 1, MT_PATH);
        } else if (s == SIDE_S) {
            room_set(x0, H - 1, MT_PATH); room_set(x1, H - 1, MT_PATH);
        } else if (s == SIDE_E) {
            room_set(W - 1, y0, MT_PATH); room_set(W - 1, y1, MT_PATH);
        } else {
            room_set(0, y0, MT_PATH); room_set(0, y1, MT_PATH);
        }
        u16 gt = MT_PATH;
        bool8 open = world_gate_open(cell, s);
        switch (g) {
            case GATE_THORN: gt = MT_THORN; break;
            case GATE_CRACK: gt = open ? MT_DOOR_OPEN : MT_CRACK; break;
            case GATE_WEB: gt = open ? MT_PATH : MT_WEB; break;
            case GATE_LOCK: gt = open ? MT_DOOR_OPEN : MT_DOOR_LOCKED; break;
            case GATE_CHASM: gt = MT_PIT; break;
            case GATE_EXIT: gt = MT_STAIRS_DOWN; break;
            default: break;
        }
        if (g != GATE_OPEN) {
            room_set(x0, y0, gt);
            room_set(x1, y1, gt);
            if (g == GATE_CHASM && s == SIDE_N) {
                /* a pit band through the whole opening, 1 deep */
                room_set(x0, 1, MT_PIT); room_set(x1, 1, MT_PIT);
                room_set(x0, 0, MT_PATH); room_set(x1, 0, MT_PATH);
            }
        }
    }

    /* dressing: the pieces that span tiles first (a great tree, a meadow
       or a fairy ring in the big clearings, a great boulder, a hollow
       log, clover), then trees, a lantern at a clearing's heart, then
       the things that narrow the ways */
    if (!arena) {
        int want = (c->arch == ARCH_GROVE) ? 2 : (rng_range(&sR, 3) != 0) ? 1 : 0, k;
        for (k = 0; k < 40 && want > 0; k++)
            if (place_great_tree(1 + rng_range(&sR, W - 5), 2 + rng_range(&sR, H - 8)))
                want--;
    }
    for (i = 0; i < sClearCount; i++) {
        Clearing* cl = &sClear[i];
        int k;
        if (cl->lake || arena)
            continue;
        if (cl->rx >= 4 && cl->ry >= 3) {
            for (k = 0; k < 10; k++) {
                int px = cl->x - cl->rx + 1 + rng_range(&sR, cl->rx * 2 - 3), py = cl->y - cl->ry + 1 + rng_range(&sR, cl->ry * 2 - 3);
                if (blighted && fits_plain(px, py, 2, 2)) {
                    stamp_ground(px, py, 2, 2, MT_SHROOMRING_0);
                    break;
                }
                if (!blighted && fits_plain(px, py, 3, 3)) {
                    stamp_ground(px, py, 3, 3, MT_MEADOW_0);
                    break;
                }
            }
        }
        if (cl->rx >= 4 && cl->ry >= 3) {
            int want = 1 + rng_range(&sR, 2);
            for (k = 0; k < 12 && want > 0; k++) {
                int tx = cl->x - cl->rx + 1 + rng_range(&sR, cl->rx * 2 - 2), ty = cl->y - cl->ry + rng_range(&sR, cl->ry);
                if (place_tree(tx, ty))
                    want--;
            }
        }
        if (cl->rx >= 3 && (rng_next(&sR) & 1) && is_plain(cl->x, cl->y + 1) && simple_spot(cl->x, cl->y + 1))
            room_set(cl->x, cl->y + 1, MT_LANTERN_POST);
    }
    if (!arena) {
        if (rng_next(&sR) & 1)
            scatter_block(MT_GBOULDER_0, 2, 2, 1, 40);
        if (rng_next(&sR) & 1)
            scatter_block(MT_HLOG_0, 2, 1, 1, 40);
        if (blighted)
            scatter_ground(MT_SHROOMRING_0, 2, 2, 1 + rng_range(&sR, 2), 30);
        else
            scatter_ground(MT_CLOVER_0, 2, 2, 1 + rng_range(&sR, 2), 30);
    }
    if (!blighted) {
        scatter_solid(MT_BUSH, 4 + rng_range(&sR, 4), 120);
        scatter_solid(MT_ROCK_SMALL, 1 + rng_range(&sR, 3), 80);
        scatter_solid(MT_STUMP, rng_range(&sR, 2), 40);
        scatter_solid(MT_LOG, rng_range(&sR, 2), 40);
        scatter_solid(MT_LANTERN_POST, rng_range(&sR, 2), 40);
        scatter_floor(MT_TALL_GRASS, 8);
        scatter_floor(MT_MOSS_FLOWERS, 6);
    } else {
        scatter_solid(MT_BLIGHT_CRYSTAL, 2 + rng_range(&sR, 3), 80);
        scatter_solid(MT_DEAD_TREE, 1 + rng_range(&sR, 2), 60);
        scatter_solid(MT_BOULDER, rng_range(&sR, 2), 40);
        scatter_floor(MT_BLIGHT_VEIN, 5);
    }
    switch (c->arch) {
        case ARCH_GROVE:
            scatter_solid(MT_THORN, 2 + rng_range(&sR, 2), 60);
            scatter_solid(MT_LOG, 1, 40);
            break;
        case ARCH_RUINS:
            scatter_solid(MT_PILLAR, 2 + rng_range(&sR, 3), 80);
            scatter_solid(MT_RUIN_WALL, 1 + rng_range(&sR, 3), 60);
            scatter_floor(MT_MOSSY_STONE, 10);
            if (rng_range(&sR, 3) == 0)
                scatter_solid(MT_STATUE, 1, 40);
            break;
        case ARCH_THICKET:
            scatter_solid(MT_THORN, 5 + rng_range(&sR, 4), 120);
            scatter_solid(MT_BUSH, 3, 60);
            scatter_solid(MT_STUMP, 1, 40);
            break;
        case ARCH_BONEYARD:
            scatter_floor(MT_BONES, 10);
            scatter_floor(MT_BLIGHT_POOL, 3);
            scatter_solid(MT_DEAD_TREE, 1 + rng_range(&sR, 2), 40);
            scatter_solid(MT_ROCK, 2, 40);
            break;
        case ARCH_POND:
            scatter_solid(MT_ROCK, 2, 40);
            scatter_floor(MT_MOSS_FLOWERS, 4);
            break;
        case ARCH_ARENA:
            room_set(W / 2 - 9, H / 2 - 5, MT_BLIGHT_CRYSTAL);
            room_set(W / 2 + 8, H / 2 - 5, MT_BLIGHT_CRYSTAL);
            room_set(W / 2 - 9, H / 2 + 5, MT_DEAD_TREE);
            room_set(W / 2 + 8, H / 2 + 5, MT_DEAD_TREE);
            scatter_floor(MT_BLIGHT_POOL, 2);
            break;
        case ARCH_ENTRY:
            scatter_floor(MT_MOSS_FLOWERS, 6);
            if (is_plain(W / 2 - 3, H / 2 + 4))
                room_set(W / 2 - 3, H / 2 + 4, MT_LANTERN_POST);
            if (is_plain(W / 2 + 2, H / 2 + 4))
                room_set(W / 2 + 2, H / 2 + 4, MT_LANTERN_POST);
            break;
        default:
            break;
    }
    if (!arena && !entry && rng_range(&sR, 5) < 3)
        dig_alcove(blighted);

    /* keep the door approaches open: two tiles in from each opening */
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1, k;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        for (k = 1; k <= 2; k++) {
            int ox = (s == SIDE_E) ? -k : (s == SIDE_W) ? k : 0;
            int oy = (s == SIDE_N) ? k : (s == SIDE_S) ? -k : 0;
            int ax = x0 + ox, ay = y0 + oy, bx = x1 + ox, by = y1 + oy;
            if (interior(ax, ay) && (!passable(ax, ay) || room_get_overlay(ax, ay) != MT_NONE)) {
                room_set(ax, ay, MT_PATH);
                room_set_overlay(ax, ay, MT_NONE);
            }
            if (interior(bx, by) && (!passable(bx, by) || room_get_overlay(bx, by) != MT_NONE)) {
                room_set(bx, by, MT_PATH);
                room_set_overlay(bx, by, MT_NONE);
            }
        }
    }

    /* connectivity: flood from the first open door's inner tile, carve to
       any other door that is cut off */
    {
        int sx = -1, sy = -1, pass;
        for (s = 0; s < 4 && sx < 0; s++) {
            int x0, y0, x1, y1;
            if (c->gate[s] == GATE_WALL)
                continue;
            roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
            sx = x0 + ((s == SIDE_W) ? 1 : (s == SIDE_E) ? -1 : 0);
            sy = y0 + ((s == SIDE_N) ? 1 : (s == SIDE_S) ? -1 : 0);
        }
        if (sx < 0) {
            sx = W / 2;
            sy = H / 2;
        }
        for (pass = 0; pass < 3; pass++) {
            bool8 ok = TRUE;
            flood_reach(sx, sy);
            for (s = 0; s < 4; s++) {
                int x0, y0, x1, y1, ix, iy;
                if (c->gate[s] == GATE_WALL)
                    continue;
                roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
                ix = x0 + ((s == SIDE_W) ? 1 : (s == SIDE_E) ? -1 : 0);
                iy = y0 + ((s == SIDE_N) ? 1 : (s == SIDE_S) ? -1 : 0);
                if (!reached(ix, iy)) {
                    carve_to_center(ix, iy);
                    carve_to_center(sx, sy);
                    ok = FALSE;
                }
            }
            if (ok)
                break;
        }
        flood_reach(sx, sy);
    }

    /* role objects */
    switch (c->role) {
        case ROLE_KEYITEM:
        case ROLE_CHEST:
        case ROLE_KEYCHEST:
            ensure_spot(&gSpots.chest);
            gSpots.has_chest = 1;
            room_set(gSpots.chest.x, gSpots.chest.y, (c->flags & CF_CHEST_OPEN) ? MT_CHEST_OPEN : MT_CHEST);
            break;
        case ROLE_NPC_HUNT:
        case ROLE_NPC_FETCH:
            ensure_spot(&gSpots.npc);
            gSpots.has_npc = 1;
            break;
        case ROLE_NPC_TORCH:
            ensure_spot(&gSpots.npc);
            gSpots.has_npc = 1;
            for (i = 0; i < 4; i++) {
                Spot t;
                ensure_spot(&t);
                if (t.x == gSpots.npc.x && t.y == gSpots.npc.y && is_floor(t.x, t.y + 2))
                    t.y += 2;
                gSpots.torches[gSpots.torch_count++] = t;
                room_set(t.x, t.y, (c->flags & CF_QUEST_DONE) ? MT_TORCH_LIT : MT_TORCH);
            }
            break;
        case ROLE_RELIC:
            if (!(c->flags & CF_RELIC_TAKEN)) {
                ensure_spot(&gSpots.relic);
                gSpots.has_relic = 1;
                room_set(gSpots.relic.x, gSpots.relic.y, MT_MOSSY_STONE);
                room_set_overlay(gSpots.relic.x, gSpots.relic.y, MT_SPARKLE);
            }
            break;
        case ROLE_SHRINE:
            if (find_spot(&gSpots.shrine, 300, 2)) {
                gSpots.has_shrine = 1;
                room_set(gSpots.shrine.x, gSpots.shrine.y, MT_STATUE);
                room_set(gSpots.shrine.x, gSpots.shrine.y + 1, (c->flags & CF_SHRINE_USED) ? MT_MOSSY_STONE : MT_MOSS_FLOWERS);
                room_set_overlay(gSpots.shrine.x, gSpots.shrine.y + 1, MT_SPARKLE);
            }
            break;
        case ROLE_GOAL:
            gSpots.boss.x = W / 2;
            gSpots.boss.y = H / 2 - 1;
            gSpots.has_boss = 1;
            break;
        default:
            break;
    }
    /* the hoard must be reachable once its stopper is lifted */
    if (gSpots.has_treasure && !reached(gSpots.treasure.x, gSpots.treasure.y)) {
        int mx = gSpots.treasure.x, my = gSpots.treasure.y, k, ok = 0;
        static const s8 d[4][2] = { { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } };
        for (k = 0; k < 4; k++) {
            int nx = mx + d[k][0], ny = my + d[k][1];
            u8 t = type_at(nx, ny);
            if ((t == TT_LIFT1 || t == TT_LIFT2) && inside(nx + d[k][0], ny + d[k][1]) && reached(nx + d[k][0], ny + d[k][1]))
                ok = 1;
        }
        if (!ok)
            gSpots.has_treasure = 0;
    }
    /* monster spots: the rooms are bigger, so a few more */
    {
        int n = c->density + (c->density ? 2 : 0);
        for (i = 0; i < n && gSpots.spawn_count < 12; i++) {
            Spot sp;
            if (find_spot(&sp, 60, 0))
                gSpots.spawns[gSpots.spawn_count++] = sp;
        }
    }
    /* gold on the floor: the wood is rotten, but it shines */
    for (i = 0; i < 12; i++) {
        int px = 2 + rng_range(&sR, W - 4), py = 3 + rng_range(&sR, H - 5);
        if (is_floor(px, py))
            room_set_overlay(px, py, MT_SPARKLE);
    }
    room_render();
}
