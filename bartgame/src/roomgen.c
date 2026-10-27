/* BARTGAME: a forest room from a maze cell. Deterministic from the world
   seed and cell index, so returning with an item restores the same place.

   A coarse clearing/corridor plan reserves a connected route between the
   doors. Tile-scale ellipses soften the clearings; continuous meandering
   watersheds widen into pond basins; crossings extend to protected dry
   banks, and terraced ground has ramps and falls rather than random ledges.
   Shores, verges and path-edge families blend materials afterwards.

   A reserved route is distinct from its dirt artwork: grass can conceal
   one exit's lane, and a tempting dirt spur can lead to an optional pocket.
   Those pockets are walled glades with bomb, candle or cape access. They
   never contain mandatory progress. Required mouths, actors and objects
   are placed only on the entry component, and mandatory mouths have a
   deterministic fallback when random wall-face trials find nothing. */
#include "gba.h"
#include "util.h"
#include "room.h"
#include "world.h"
#include "roomgen.h"
#include "myst.h"

RoomSpots gSpots;
static Rng sR;
static u8 sReach[FOREST_W * FOREST_H];

#define W FOREST_W
#define H FOREST_H

/* the carve mask: what a tile will be before it is dressed */
enum { M_WALL, M_FLOOR, M_WATER, M_BRIDGE_H, M_BRIDGE_V, M_LEDGE, M_RAMP, M_FALL };
static int sTerraceRow; /* the cliff's row, or -1 */
static u8 sMask[H][W];
/* the paths: which way they run where they run, and their middle line */
#define P_H 1
#define P_V 2
#define P_MID 4
#define P_BANK 16 /* dry bridge landing: never dressed with solids */
#define P_HIDDEN 8 /* a traversable lane whose worn trail has grown over */
static u8 sPath[H][W];
/* the room's trail (the blight's vein in a blighted room) and whether it
   is blighted, for the helpers that put ground down */
static u16 sTrail;
static bool8 sBlighted;
static u8 sStage;
static bool8 reached(int x, int y);


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

static bool8 watery(u8 m) {
    return m == M_WATER || m == M_FALL;
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
    if(sPath[y][x] & P_BANK) return FALSE;
    return t < MT_MOSS_FLOWERS2 || (t >= MT_BLIGHT_GROUND0 && t <= MT_BLIGHT_FLOOR) || t == MT_BLIGHT_FLOOR2 || t == MT_MOSS_SHADE ||
           (t >= MT_SHORE_1 && t <= MT_VERGE_F);
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

/* ------------------------------------------------------------- chunks -- */
/* The room is planned on a grid of 3x3-tile chunks, ten across and
   seven down over the carvable part (x 1..30, y 2..22). Every chunk is
   a piece from a bank: forest, open ground, a path of some width running
   out of one side or more, water, a plank bridge, a cliff with or
   without its ramp. The plan is laid in strokes that span chunks, so a
   lake, a river, a cliff or a path is a shape and never a scatter of
   tiles, and the pieces along a stroke are chosen to meet: a path's
   band always holds the middle line, a bridge is the middle line over
   water, a cliff's ledge row is the chunk's last row with a landing
   forced under it. Then each chunk is expanded into the mask and the
   tile passes (shores, verges, trail edges, the canopy's faces) finish
   the seams. */
#define CW 10
#define CH 7
#define CX0 1
#define CY0 2
enum { K_FOREST, K_OPEN, K_PATH, K_WATER, K_BRIDGE, K_CLIFF, K_CLIFF_RAMP };
#define C_N 1
#define C_E 2
#define C_S 4
#define C_W 8
typedef struct {
    u8 kind;
    u8 conn;  /* C_*: the sides a path runs out of this chunk */
    u8 width; /* a path's: 1, 2 or 3 tiles */
    u8 shift; /* a two-wide band takes the middle and the low (0) or high (1) line */
    u8 lake;  /* water of a lake, else of a river */
} Chunk;
static Chunk sChunk[CH][CW];
typedef struct {
    s8 x, y, w, h;
} CRect;
static CRect sClear[4];
static int sClearCount;
static bool8 sWater;

static bool8 cinside(int cx, int cy) {
    return cx >= 0 && cy >= 0 && cx < CW && cy < CH;
}

static Chunk* chunk(int cx, int cy) {
    return &sChunk[cy][cx];
}

static u8 ckind(int cx, int cy) {
    return cinside(cx, cy) ? sChunk[cy][cx].kind : K_FOREST;
}

static bool8 cwatery(int cx, int cy) {
    u8 k = ckind(cx, cy);
    return k == K_WATER || k == K_BRIDGE;
}

/* a path runs out of this chunk by side (a C_* bit): forest becomes a
   path of some width, water a bridge, open ground keeps a trail */
static void cjoin(int cx, int cy, int side) {
    static const u8 widths[6] = { 1, 1, 2, 2, 2, 3 };
    Chunk* k = chunk(cx, cy);
    if (k->kind == K_FOREST) {
        k->kind = K_PATH;
        k->width = widths[rng_range(&sR, 6)];
        k->shift = rng_next(&sR) & 1;
    } else if (k->kind == K_WATER) {
        k->kind = K_BRIDGE;
    }
    k->conn |= side;
}

static void door_chunk(int cx, int cy, int conn) {
    Chunk* k = chunk(cx, cy);
    k->kind = K_PATH;
    k->width = 3;
    k->conn |= conn;
}

/* A winding path of chunks from a to b: mostly along the longer axis
   left, but wandering; over water it keeps its axis, so planks run
   straight. */
static void cpath(int x0, int y0, int x1, int y1) {
    int x = x0, y = y0, guard = 0, lock = -1;
    while ((x != x1 || y != y1) && guard++ < 100) {
        int ax = ABS(x1 - x), ay = ABS(y1 - y), nx = x, ny = y, s;
        bool8 horiz;
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
            nx += (x1 > x) ? 1 : -1;
        else
            ny += (y1 > y) ? 1 : -1;
        s = horiz ? ((nx > x) ? 1 : 3) : ((ny > y) ? 2 : 0);
        cjoin(x, y, 1 << s);
        cjoin(nx, ny, 1 << ((s + 2) & 3));
        lock = cwatery(nx, ny) ? (horiz ? 0 : 1) : -1;
        x = nx;
        y = ny;
    }
}

/* a rectangle of chunks inside the forest's rim, over no other clearing */
static bool8 crect_free(int x, int y, int w, int h) {
    int i, j;
    if (x < 1 || y < 1 || x + w > CW - 1 || y + h > CH - 1)
        return FALSE;
    for (j = y; j < y + h; j++)
        for (i = x; i < x + w; i++)
            if (sChunk[j][i].kind != K_FOREST)
                return FALSE;
    return TRUE;
}

static void add_clearing(int x, int y, int w, int h) {
    int i, j;
    for (j = y; j < y + h; j++)
        for (i = x; i < x + w; i++)
            sChunk[j][i].kind = K_OPEN;
    sClear[sClearCount].x = x;
    sClear[sClearCount].y = y;
    sClear[sClearCount].w = w;
    sClear[sClearCount].h = h;
    sClearCount++;
}

/* A river one chunk wide meandering across the room, through open ground
   and under the trees where ground lies beside it. A path it meets must
   cross it, and does, on planks; a path running along it, or a cliff,
   sends the river elsewhere. */
static void river(bool8 vertical) {
    int tries;
    for (tries = 0; tries < 6; tries++) {
        int len = vertical ? CH : CW, i, ok = 1, lim = (vertical ? CW : CH) - 2;
        int pos = vertical ? 2 + rng_range(&sR, CW - 4) : 1 + rng_range(&sR, CH - 2);
        s8 at[CW];
        for (i = 0; i < len; i++) {
            if (i && (i & 1) == 0)
                pos += (int)rng_range(&sR, 3) - 1;
            pos = CLAMP(pos, 1, lim);
            at[i] = pos;
        }
        for (i = 0; i < len && ok; i++) {
            int cx = vertical ? at[i] : i, cy = vertical ? i : at[i];
            Chunk* k = chunk(cx, cy);
            if (k->kind == K_PATH || k->kind == K_BRIDGE) {
                int across = vertical ? (C_E | C_W) : (C_N | C_S), along = vertical ? (C_N | C_S) : (C_E | C_W);
                if (!(k->conn & across) || (k->conn & along))
                    ok = 0;
            } else if (k->kind == K_OPEN && (k->conn & (vertical ? (C_N | C_S) : (C_E | C_W)))) {
                ok = 0;
            } else if (k->kind == K_CLIFF || k->kind == K_CLIFF_RAMP) {
                ok = 0;
            }
        }
        if (!ok)
            continue;
        for (i = 0; i < len; i++) {
            int cx = vertical ? at[i] : i, cy = vertical ? i : at[i];
            Chunk* k = chunk(cx, cy);
            switch (k->kind) {
                case K_FOREST: {
                    u8 a = vertical ? ckind(cx - 1, cy) : ckind(cx, cy - 1);
                    u8 b = vertical ? ckind(cx + 1, cy) : ckind(cx, cy + 1);
                    if (a != K_FOREST || b != K_FOREST)
                        k->kind = K_WATER;
                    break;
                }
                case K_OPEN: k->kind = k->conn ? K_BRIDGE : K_WATER; break;
                case K_PATH: k->kind = K_BRIDGE; break;
                default: break;
            }
        }
        sWater = TRUE;
        return;
    }
}

/* A cliff across the room: along one row of chunks, open ground with
   ground under it ends in a ledge the hero drops from, and where a path
   runs down through it a ramp carries the path. A path running along the
   row, or water in it, sends the cliff to another row. */
static void terrace(void) {
    static const u8 rows[4] = { 1, 2, 4, 5 };
    int tries, cx;
    for (tries = 0; tries < 4; tries++) {
        int r = rows[rng_range(&sR, 4)], n = 0, ok = 1;
        for (cx = 0; cx < CW && ok; cx++) {
            Chunk* k = chunk(cx, r);
            u8 below = ckind(cx, r + 1);
            bool8 ground_below = (below == K_OPEN || below == K_PATH);
            if (k->kind == K_WATER || k->kind == K_BRIDGE)
                ok = 0;
            else if (k->kind == K_PATH && ((k->conn & (C_E | C_W)) || !ground_below))
                ok = 0;
            else if ((k->kind == K_OPEN || k->kind == K_PATH) && ground_below)
                n++;
        }
        if (!ok || n < 2)
            continue;
        for (cx = 0; cx < CW; cx++) {
            Chunk* k = chunk(cx, r);
            u8 below = ckind(cx, r + 1);
            if (below != K_OPEN && below != K_PATH)
                continue;
            if (k->kind == K_PATH)
                k->kind = K_CLIFF_RAMP;
            else if (k->kind == K_OPEN)
                k->kind = (k->conn & (C_N | C_S)) ? K_CLIFF_RAMP : K_CLIFF;
        }
        sTerraceRow = CY0 + r * 3 + 1;
        return;
    }
}

/* the plan: doors, clearings and their lakes, the paths between, then a
   river or a cliff */
static void plan(const Cell* c, bool8 arena, bool8 entry) {
    int s, i, nodes[4][2], nn = 0;
    memset(sChunk, 0, sizeof(sChunk));
    sClearCount = 0;
    sWater = FALSE;
    /* the doors: a landing three deep, the width of its two chunks */
    for (s = 0; s < 4; s++) {
        if (c->gate[s] == GATE_WALL)
            continue;
        if (s == SIDE_N) {
            door_chunk(4, 0, C_N | C_S); door_chunk(5, 0, C_N | C_S);
            nodes[nn][0] = 4 + (rng_next(&sR) & 1); nodes[nn][1] = 0;
        } else if (s == SIDE_S) {
            door_chunk(4, CH - 1, C_N | C_S); door_chunk(5, CH - 1, C_N | C_S);
            nodes[nn][0] = 4 + (rng_next(&sR) & 1); nodes[nn][1] = CH - 1;
        } else if (s == SIDE_E) {
            door_chunk(CW - 1, 3, C_E | C_W);
            nodes[nn][0] = CW - 1; nodes[nn][1] = 3;
        } else {
            door_chunk(0, 3, C_E | C_W);
            nodes[nn][0] = 0; nodes[nn][1] = 3;
        }
        nn++;
    }
    /* the clearings: rectangles of open chunks */
    if (arena) {
        add_clearing(1, 1, CW - 2, CH - 2);
    } else if (entry) {
        add_clearing(3, 2, 4, 3);
        {
            int x = (rng_next(&sR) & 1) ? 1 : CW - 3, y = 1 + rng_range(&sR, 2);
            if (crect_free(x, y, 2, 2))
                add_clearing(x, y, 2, 2);
        }
    } else {
        int want = 3 + rng_range(&sR, 2), tries;
        for (tries = 0; tries < 60 && sClearCount < want; tries++) {
            int w = 2 + rng_range(&sR, 2), h = 2 + rng_range(&sR, 2), x, y;
            if (sClearCount == 0 && (rng_next(&sR) & 1))
                w++;
            x = 1 + rng_range(&sR, CW - 1 - w);
            y = 1 + rng_range(&sR, CH - 1 - h);
            if (crect_free(x, y, w, h))
                add_clearing(x, y, w, h);
        }
        /* a lake in the heart of a wide clearing, a ring of ground round it */
        for (i = 0; i < sClearCount; i++) {
            CRect* r = &sClear[i];
            int ix, iy, iw, ih, x, y;
            if (r->w < 3 || !(c->arch == ARCH_POND || rng_range(&sR, 3) == 0))
                continue;
            ix = r->x + 1;
            iw = r->w - 2;
            if (r->h >= 3) {
                iy = r->y + 1;
                ih = r->h - 2;
            } else {
                iy = r->y;
                ih = r->h;
            }
            for (y = iy; y < iy + ih; y++)
                for (x = ix; x < ix + iw; x++) {
                    sChunk[y][x].kind = K_WATER;
                    sChunk[y][x].lake = 1;
                }
            sWater = TRUE;
        }
    }
    /* paths: each door to its nearest clearing, the clearings in a chain,
       one more link for a loop when there are three */
    for (i = 0; i < nn; i++) {
        int best = 0, bd = 1 << 30, k;
        for (k = 0; k < sClearCount; k++) {
            int d = ABS(nodes[i][0] - (sClear[k].x + sClear[k].w / 2)) + ABS(nodes[i][1] - (sClear[k].y + sClear[k].h / 2));
            if (d < bd) {
                bd = d;
                best = k;
            }
        }
        cpath(nodes[i][0], nodes[i][1], sClear[best].x + sClear[best].w / 2, sClear[best].y + sClear[best].h / 2);
    }
    for (i = 0; i + 1 < sClearCount; i++)
        cpath(sClear[i].x + sClear[i].w / 2, sClear[i].y + sClear[i].h / 2, sClear[i + 1].x + sClear[i + 1].w / 2, sClear[i + 1].y + sClear[i + 1].h / 2);
    if (sClearCount >= 3 && (rng_next(&sR) & 1))
        cpath(sClear[0].x + sClear[0].w / 2, sClear[0].y + sClear[0].h / 2, sClear[2].x + sClear[2].w / 2, sClear[2].y + sClear[2].h / 2);
    /* here and there a path opens into a pocket of glade and closes again */
    {
        int cx, cy;
        for (cy = 1; cy < CH - 1; cy++)
            for (cx = 1; cx < CW - 1; cx++) {
                Chunk* k = chunk(cx, cy);
                if (k->kind == K_PATH && k->width < 3 && rng_range(&sR, 4) == 0)
                    k->kind = K_OPEN;
            }
    }
    /* a river, or a cliff: never both */
    /* Water is drawn as a continuous tile-scale watershed after expansion,
       so a river cannot break into disconnected three-tile squares. */
    if (!arena && !entry && !sWater && (c->arch == ARCH_RUINS || c->arch == ARCH_BONEYARD || rng_range(&sR, 3) == 0))
        terrace();
}

/* does line i of three lie in a band of this width? the middle always does */
static bool8 in_band(int i, int w, int shift) {
    return w == 3 || i == 1 || (w == 2 && i == (shift ? 2 : 0));
}

/* every chunk into the mask: the kinds' shapes, the paths' bands and
   their middle lines as trails */
static void expand(void) {
    int cx, cy, dx, dy;
    for (cy = 0; cy < CH; cy++) {
        for (cx = 0; cx < CW; cx++) {
            Chunk* k = chunk(cx, cy);
            int ox = CX0 + cx * 3, oy = CY0 + cy * 3;
            int w = (k->kind == K_BRIDGE) ? 1 : k->width;
            for (dy = 0; dy < 3; dy++) {
                for (dx = 0; dx < 3; dx++) {
                    u8 m = M_WALL, p = 0;
                    bool8 ew = (k->conn & (C_E | C_W)) != 0, ns = (k->conn & (C_N | C_S)) != 0;
                    bool8 along_h = (dx == 1 || (dx == 0 && (k->conn & C_W)) || (dx == 2 && (k->conn & C_E)));
                    bool8 along_v = (dy == 1 || (dy == 0 && (k->conn & C_N)) || (dy == 2 && (k->conn & C_S)));
                    bool8 h = ew && in_band(dy, w, k->shift) && along_h;
                    bool8 v = ns && in_band(dx, w, k->shift) && along_v;
                    bool8 midh = ew && dy == 1 && along_h, midv = ns && dx == 1 && along_v;
                    switch (k->kind) {
                        case K_OPEN:
                            m = M_FLOOR;
                            if (midh || midv)
                                p = P_MID;
                            break;
                        case K_PATH:
                            if (h || v) {
                                m = M_FLOOR;
                                p = (h ? P_H : 0) | (v ? P_V : 0) | ((midh || midv) ? P_MID : 0);
                            }
                            break;
                        case K_WATER:
                            m = M_WATER;
                            break;
                        case K_BRIDGE:
                            m = midh ? M_BRIDGE_H : midv ? M_BRIDGE_V : M_WATER;
                            break;
                        case K_CLIFF:
                            m = (dy == 2) ? M_LEDGE : M_FLOOR;
                            if (midh && dy != 2)
                                p = P_MID;
                            break;
                        case K_CLIFF_RAMP:
                            m = (dy == 2) ? ((dx == 1) ? M_RAMP : M_LEDGE) : M_FLOOR;
                            if (dx == 1)
                                p = P_MID | P_V;
                            else if (midh && dy != 2)
                                p = P_MID;
                            break;
                        default:
                            break;
                    }
                    sMask[oy + dy][ox + dx] = m;
                    sPath[oy + dy][ox + dx] = p;
                }
            }
        }
    }
    /* a lake's corners are nicked round; the ground under a cliff is a
       landing the ledges drop onto */
    for (cy = 0; cy < CH; cy++) {
        for (cx = 0; cx < CW; cx++) {
            Chunk* k = chunk(cx, cy);
            int ox = CX0 + cx * 3, oy = CY0 + cy * 3;
            if (k->kind == K_WATER && k->lake) {
                bool8 n = cwatery(cx, cy - 1), e = cwatery(cx + 1, cy), s = cwatery(cx, cy + 1), w = cwatery(cx - 1, cy);
                if (!n && !w) sMask[oy][ox] = M_FLOOR;
                if (!n && !e) sMask[oy][ox + 2] = M_FLOOR;
                if (!s && !w) sMask[oy + 2][ox] = M_FLOOR;
                if (!s && !e) sMask[oy + 2][ox + 2] = M_FLOOR;
            }
            if ((k->kind == K_CLIFF || k->kind == K_CLIFF_RAMP) && cy + 1 < CH)
                for (dx = 0; dx < 3; dx++)
                    if (sMask[oy + 3][ox + dx] == M_WALL)
                        sMask[oy + 3][ox + dx] = M_FLOOR;
            /* a clearing's outer corners are rounded off by the trees,
               a path's bends are rounded in */
            if (k->kind == K_OPEN) {
                bool8 n = ckind(cx, cy - 1) == K_FOREST, e = ckind(cx + 1, cy) == K_FOREST;
                bool8 s = ckind(cx, cy + 1) == K_FOREST, w = ckind(cx - 1, cy) == K_FOREST;
                if (n && w && !sPath[oy][ox]) sMask[oy][ox] = M_WALL;
                if (n && e && !sPath[oy][ox + 2]) sMask[oy][ox + 2] = M_WALL;
                if (s && w && !sPath[oy + 2][ox]) sMask[oy + 2][ox] = M_WALL;
                if (s && e && !sPath[oy + 2][ox + 2]) sMask[oy + 2][ox + 2] = M_WALL;
            }
            if (k->kind == K_PATH && k->width < 3) {
                if ((k->conn & (C_N | C_E)) == (C_N | C_E)) sMask[oy][ox + 2] = M_FLOOR;
                if ((k->conn & (C_N | C_W)) == (C_N | C_W)) sMask[oy][ox] = M_FLOOR;
                if ((k->conn & (C_S | C_E)) == (C_S | C_E)) sMask[oy + 2][ox + 2] = M_FLOOR;
                if ((k->conn & (C_S | C_W)) == (C_S | C_W)) sMask[oy + 2][ox] = M_FLOOR;
            }
        }
    }
}

/* Organic clearings are the broad volumes of a landscape, not a grid of
   identical square rooms. Corridors keep their reserved middle line. */
static void shape_clearings(void) {
    int i, x, y;
    for (i = 0; i < sClearCount; i++) {
        CRect* r = &sClear[i];
        int cx = CX0 + r->x * 3 + r->w * 3 / 2;
        int cy = CY0 + r->y * 3 + r->h * 3 / 2;
        int rx = r->w * 3 / 2 + 1, ry = r->h * 3 / 2 + 1;
        for (y = MAX(2, cy - ry); y <= MIN(H - 2, cy + ry); y++) {
            for (x = MAX(1, cx - rx); x <= MIN(W - 2, cx + rx); x++) {
                int dx = x - cx, dy = y - cy;
                int d = dx * dx * ry * ry + dy * dy * rx * rx;
                int limit = rx * rx * ry * ry;
                if (sMask[y][x] == M_WALL && d < limit * 4 / 5)
                    sMask[y][x] = M_FLOOR;
                else if (sMask[y][x] == M_FLOOR && !(sPath[y][x] & P_MID) && d > limit &&
                         x >= CX0 + r->x * 3 && x < CX0 + (r->x + r->w) * 3 &&
                         y >= CY0 + r->y * 3 && y < CY0 + (r->y + r->h) * 3)
                    sMask[y][x] = M_WALL;
            }
        }
    }
}

/* A river is one continuous band, two or three tiles wide, whose banks
   drift by at most one tile per row. Try orientations/locations that cross
   a path rather than run along it: every plank has land at both ends. */
static void watershed(const Cell* c, bool8 arena, bool8 entry) {
    int tries, i, j;
    if (arena || entry || sTerraceRow >= 0 ||
        (c->arch != ARCH_POND && hash32(gWorld.seed, c->dist + 719) % 4))
        return;
    for (tries = 0; tries < 12; tries++) {
        bool8 vertical = (hash32(gWorld.seed, c->dist * 17 + tries) & 1) != 0;
        int length = vertical ? H - 4 : W - 2;
        int limit = vertical ? W : H;
        int width = 2 + (tries & 1), ok = 1;
        int pos = 4 + hash32(gWorld.seed, c->dist * 43 + tries) % (limit - 9);
        s8 at[W];
        for (i = 0; i < length; i++) {
            if (i && i % 4 == 0)
                pos += (int)(hash32(gWorld.seed, tries * 997 + i * 31 + c->dist) % 3) - 1;
            pos = CLAMP(pos, 3, limit - width - 3);
            at[i] = pos;
            for (j = 0; j < width; j++) {
                int x = vertical ? pos + j : i + 1;
                int y = vertical ? i + 2 : pos + j;
                if (sMask[y][x] == M_LEDGE || sMask[y][x] == M_RAMP ||
                    ((sPath[y][x] & P_MID) && !(sPath[y][x] & (vertical ? P_H : P_V))))
                    ok = 0;
            }
        }
        if (!ok)
            continue;
        for (i = 0; i < length; i++) {
            for (j = 0; j < width; j++) {
                int x = vertical ? at[i] + j : i + 1;
                int y = vertical ? i + 2 : at[i] + j;
                if (sPath[y][x] & P_MID)
                    sMask[y][x] = vertical ? M_BRIDGE_H : M_BRIDGE_V;
                else
                    sMask[y][x] = M_WATER;
            }
        }
        if(c->arch==ARCH_POND) {
            int mid=length*2/3;
            int bx=vertical ? at[mid]+width/2 : mid+1;
            int by=vertical ? mid+2 : at[mid]+width/2;
            int x,y;
            for(y=MAX(3,by-3);y<=MIN(H-3,by+3);y++)
                for(x=MAX(2,bx-4);x<=MIN(W-3,bx+4);x++) {
                    int dx=x-bx,dy=y-by;
                    if(dx*dx*9+dy*dy*16>144 || (sPath[y][x]&P_MID) ||
                       sMask[y][x]==M_LEDGE || sMask[y][x]==M_RAMP) continue;
                    sMask[y][x]=M_WATER;
                }
        }
        sWater = TRUE;
        return;
    }
}

/* Trails are suggestions, not a graph overlay. Occasionally one arrival
   lane has been reclaimed by grass. A few fading sections suggest the
   route, but the dirt never reveals every junction. Physical floor and
   the reserved lane remain, so dressing cannot close the hidden route. */
static void trail_story(const Cell* c, bool8 arena, bool8 entry) {
    int x, y, side, active[4], n = 0;
    u32 clue = hash32(gWorld.seed, c->dist * 59 + c->arch * 13 + 881);
    if (arena || entry)
        return;
    for (side = 0; side < 4; side++)
        if (c->gate[side] != GATE_WALL)
            active[n++] = side;
    if (n < 2 || clue % 4 == 0)
        return;
    side = active[(clue >> 4) % n];
    for (y = 2; y < H - 1; y++)
        for (x = 1; x < W - 1; x++) {
            int d = side == SIDE_N ? y : side == SIDE_S ? H - 1 - y : side == SIDE_W ? x : W - 1 - x;
            if (d >= 2 && d < 9 && (sPath[y][x] & P_MID) && !(sPath[y][x] & P_BANK) && sMask[y][x] == M_FLOOR)
                sPath[y][x] |= P_HIDDEN;
        }
}

/* Finish every crossing as a bridge between real banks. The old chunk
   corners could leave a plank ending in water. Extend that same crossing
   axis through its channel, then reserve a dry landing against dressing. */
static void bridge_landings(void) {
    int x,y,dir;
    for(y=2;y<H-1;y++) for(x=1;x<W-1;x++) {
        u8 m=sMask[y][x];
        bool8 horizontal=m==M_BRIDGE_H;
        if(m!=M_BRIDGE_H && m!=M_BRIDGE_V) continue;
        for(dir=-1;dir<=1;dir+=2) {
            int dx=horizontal ? dir : 0,dy=horizontal ? 0 : dir;
            int tx=x+dx,ty=y+dy;
            while(interior(tx,ty) && (watery(sMask[ty][tx]) || sMask[ty][tx]==m)) {
                sMask[ty][tx]=m;
                sPath[ty][tx]|=P_MID|(horizontal ? P_H : P_V);
                tx+=dx;ty+=dy;
            }
            if(interior(tx,ty)) {
                if(sMask[ty][tx]==M_WALL || sMask[ty][tx]==M_LEDGE)
                    sMask[ty][tx]=M_FLOOR;
                sPath[ty][tx]|=P_MID|P_BANK|(horizontal ? P_H : P_V);
            }
        }
    }
}

/* Water pours off the cliff: in a run of ledges four or more long, two
   ledges become a fall, a pool of water gathers on the high ground
   behind them and a churned pool on the low ground under them, as far
   as the ground allows. One or two a cliff. */
static void add_waterfalls(void) {
    int ty = sTerraceRow, made = 0, want = 1 + (int)(rng_next(&sR) & 1), guard = 0;
    if (ty < 0)
        return;
    while (made < want && guard++ < 30) {
        int fx = 2 + rng_range(&sR, W - 6), k, ok = 1, dy;
        for (k = -1; k <= 2; k++)
            if (sMask[ty + 1][fx + k] != M_LEDGE)
                ok = 0;
        if (!ok)
            continue;
        sMask[ty + 1][fx] = M_FALL;
        sMask[ty + 1][fx + 1] = M_FALL;
        for (k = 0; k < 2; k++) {
            if (sMask[ty][fx + k] == M_FLOOR && !(sPath[ty][fx + k] & P_MID))
                sMask[ty][fx + k] = M_WATER;
            for (dy = 2; dy <= 3; dy++) {
                if (ty + dy >= H - 1 || sMask[ty + dy][fx + k] != M_FLOOR || (sPath[ty + dy][fx + k] & P_MID))
                    break;
                sMask[ty + dy][fx + k] = M_WATER;
            }
        }
        made++;
    }
}

/* ----------------------------------------------------------- dressing -- */
/* The floor: mostly plain grass, so the sprites read; the blight, the
   flowers, the tall grass and the bones are accents. */
/* The grass and its accents. The blight shows in it by depth: none in
   the living wood, a stain here and there from the first stage on, and
   patches of stained ground in the sick rooms (lay_rot). */
static u16 moss_pick(int stage) {
    int r = rng_range(&sR, 40);
    if (r < 33)
        return MT_MOSS0 + rng_range(&sR, 3);
    if (r < 35)
        return stage ? ((r & 1) ? MT_MOSS_BLIGHT2 : MT_MOSS_BLIGHT) : MT_MOSS0 + (r & 1);
    if (r < 37)
        return MT_MOSS_FLOWERS;
    if (r < 38)
        return MT_MOSS_FLOWERS2;
    if (r < 39)
        return MT_TALL_GRASS;
    return MT_BONES;
}

/* The blighted rooms' floor: the blight floor, now and then pitted, its
   pits glowing; their trail is the vein. */
static u16 blight_pick(void) {
    return (rng_range(&sR, 8) == 0) ? MT_BLIGHT_FLOOR2 : MT_BLIGHT_FLOOR;
}

/* a free-standing tree: 2x3, crown on the overlay, trunks solid. Both
   trunks must stand without closing a way. */
static bool8 place_tree_kind(int x, int y, u16 crown, u16 trunk) {
    int dx, dy;
    u16 was;
    if (x < 1 || y < 2 || x + 1 > W - 2 || y + 2 > H - 2)
        return FALSE;
    for (dy = 0; dy < 2; dy++)
        for (dx = 0; dx < 2; dx++)
            if (!is_floor(x + dx, y + dy))
                return FALSE;
    if (!simple_spot(x, y + 2) || near_door(x + 1, y + 2))
        return FALSE;
    was = room_get(x, y + 2);
    room_set(x, y + 2, trunk);
    if (!simple_spot(x + 1, y + 2)) {
        room_set(x, y + 2, was);
        return FALSE;
    }
    room_set(x + 1, y + 2, trunk + 1);
    room_set_overlay(x, y, crown);
    room_set_overlay(x + 1, y, crown + 1);
    room_set_overlay(x, y + 1, crown + 2);
    room_set_overlay(x + 1, y + 1, crown + 3);
    return TRUE;
}

/* a living tree: one in three with a lantern hung in it */
static bool8 place_tree(int x, int y) {
    int roll=rng_range(&sR,12);
    if ((sStage==1 && roll==0) || (sStage==2 && roll<6))
        return place_tree_kind(x,y,MT_SICKTREE_0,MT_SICKTREE_4);
    if (roll<3) return place_tree_kind(x,y,MT_BIRCH_0,MT_BIRCH_4);
    if (roll<6) return place_tree_kind(x,y,MT_FIR_0,MT_FIR_4);
    if (roll<8) return place_tree_kind(x,y,MT_TREE2_0,MT_TREE2_4);
    return place_tree_kind(x,y,MT_TREE_TOP_NW,MT_TREE_TRUNK_W);
}

/* a tree of 3x4, a great tree or the blight's: a 3x3 crown on the
   overlay over anything, a row of roots on plain ground, the trunk solid
   where it closes no way */
static bool8 place_big_tree(int x, int y, u16 base) {
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
            room_set_overlay(x + dx, y + dy, base + dy * 3 + dx);
    room_set(x, y + 3, base + 9);
    room_set(x + 1, y + 3, base + 10);
    room_set(x + 2, y + 3, base + 11);
    return TRUE;
}

static bool8 place_great_tree(int x, int y) {
    return place_big_tree(x, y, (rng_next(&sR) & 1) ? MT_GTREE2_0 : MT_GTREE_0);
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

/* n rocks, each of one of three shapes: sunk in moss, buried flat,
   stacked */
static void scatter_rocks(int n, int tries) {
    static const u16 kinds[3] = { MT_ROCK, MT_ROCK2, MT_ROCK3 };
    int i;
    for (i = 0; i < tries && n > 0; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (is_plain(x, y) && simple_spot(x, y)) {
            room_set(x, y, kinds[rng_range(&sR, 3)]);
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

/* The grass's edge at (x, y), or 0 where it meets only grass: a shore
   on the sides water lies (or a nick where it lies at a corner only); a
   verge on the sides the canopy stands or a cliff drops. */
static u16 grass_edge(int x, int y) {
    int wm, dm, xm;
    wm = (watery(sMask[y - 1][x]) ? 1 : 0) | (watery(sMask[y][x + 1]) ? 2 : 0) | (watery(sMask[y + 1][x]) ? 4 : 0) | (watery(sMask[y][x - 1]) ? 8 : 0);
    if (wm)
        return MT_SHORE_1 + wm - 1;
    dm = (watery(sMask[y - 1][x - 1]) ? 1 : 0) | (watery(sMask[y - 1][x + 1]) ? 2 : 0) | (watery(sMask[y + 1][x + 1]) ? 4 : 0) | (watery(sMask[y + 1][x - 1]) ? 8 : 0);
    if (dm)
        return MT_SHORE_C1 + dm - 1;
    xm = ((sMask[y - 1][x] == M_WALL || sMask[y - 1][x] == M_LEDGE) ? 1 : 0) | (sMask[y][x + 1] == M_WALL ? 2 : 0) |
         (sMask[y + 1][x] == M_WALL ? 4 : 0) | (sMask[y][x - 1] == M_WALL ? 8 : 0);
    return xm ? MT_VERGE_1 + xm - 1 : 0;
}

/* grass, or grass at an edge */
static bool8 grass_family(u16 t) {
    return t <= MT_MOSS_BLIGHT2 || (t >= MT_SHORE_1 && t <= MT_VERGE_F);
}

/* after the mask changed late (an alcove dug): the canopy's faces and
   crowns, and the grass's edges, drawn again round it */
static void refresh_edges(int x0, int y0, int x1, int y1) {
    int x, y;
    for (y = MAX(y0, 1); y <= MIN(y1, H - 2); y++)
        for (x = MAX(x0, 1); x <= MIN(x1, W - 2); x++) {
            u16 t = room_get(x, y);
            if (sMask[y][x] == M_WALL) {
                bool8 below = sMask[y + 1][x] != M_WALL && sMask[y + 1][x] != M_FALL;
                bool8 above = sMask[y - 1][x] != M_WALL && sMask[y - 1][x] != M_WATER;
                if (below)
                    room_set(x, y, sBlighted ? MT_BLIGHT_WALL : MT_CANOPY_S);
                else if (above)
                    room_set(x, y, sBlighted ? MT_CANOPY_BLIGHT : MT_CANOPY_N);
                else if (t == MT_CANOPY_S || t == MT_CANOPY_N || t == MT_BLIGHT_WALL)
                    room_set(x, y, sBlighted ? MT_CANOPY_BLIGHT : MT_CANOPY);
            } else if (!sBlighted && sMask[y][x] == M_FLOOR && !(sPath[y][x] & P_MID) && grass_family(t)) {
                u16 e = grass_edge(x, y);
                room_set(x, y, e ? e : MT_MOSS0 + ((x + y) % 3));
            }
        }
}

/* a pocket dug two tiles into the wall beside a path, a bush or a
   boulder across its mouth, a hoard inside */
static void dig_alcove(int cell) {
    static const s8 d[4][2] = { { 0, -1 }, { 0, 1 }, { -1, 0 }, { 1, 0 } };
    int i, kind = 1 + hash32(gWorld.seed, cell * 313 + 29) % 3;
    int length = kind == 3 ? 2 : 1;
    for (i = 0; i < 160; i++) {
        int x = 3 + rng_range(&sR, W - 6), y = 4 + rng_range(&sR, H - 8);
        int k = rng_range(&sR, 4), dx = d[k][0], dy = d[k][1];
        int ix = x + (length + 1) * dx, iy = y + (length + 1) * dy;
        int n, ok = 1;
        if (!is_plain(x,y) || !reached(x,y) || near_door(x,y) || !interior(ix,iy))
            continue;
        /* The neck and hoard are entirely in virgin canopy, and a wall
           encloses both flanks and the back: no free route round a gate. */
        for (n = 1; n <= length + 1; n++) {
            int tx=x+n*dx, ty=y+n*dy;
            if (!interior(tx,ty) || !inside(tx+dy,ty+dx) || !inside(tx-dy,ty-dx) ||
                sMask[ty][tx]!=M_WALL || type_at(tx,ty)!=TT_SOLID ||
                sMask[ty+dx][tx+dy]!=M_WALL || type_at(tx+dy,ty+dx)!=TT_SOLID ||
                sMask[ty-dx][tx-dy]!=M_WALL || type_at(tx-dy,ty-dx)!=TT_SOLID)
                ok=0;
        }
        if (!inside(ix+dx,iy+dy) || sMask[iy+dy][ix+dx]!=M_WALL || type_at(ix+dx,iy+dy)!=TT_SOLID)
            ok=0;
        if (!ok)
            continue;
        for (n=1;n<=length;n++) {
            int tx=x+n*dx,ty=y+n*dy;
            bool8 opened=(gWorld.cells[cell].opened & CELL_POCKET_OPEN)!=0;
            sMask[ty][tx]=M_FLOOR;
            room_set(tx,ty,kind==3 ? MT_PIT : opened ? sTrail : kind==1 ? MT_CRACK : MT_WEB);
            room_set_overlay(tx,ty,MT_NONE);
        }
        /* Where the forest is thick enough, the alcove opens into a
           two-by-two glade beyond its neck. Check its whole outer ring
           before opening it: an optional item never gains a free bypass. */
        {
            int sign=(hash32(gWorld.seed,cell*19)&1) ? 1 : -1;
            int px=dy*sign,py=dx*sign,a,b,wide=1;
            for(b=0;b<2;b++) for(a=0;a<2;a++) {
                int tx=ix+a*px+b*dx,ty=iy+a*py+b*dy,k2;
                if(!interior(tx,ty) || sMask[ty][tx]!=M_WALL || type_at(tx,ty)!=TT_SOLID) {wide=0;continue;}
                for(k2=0;k2<4;k2++) {
                    int nx=tx+d[k2][0],ny=ty+d[k2][1];
                    if(!inside(nx,ny)) {wide=0;continue;}
                    /* The one front edge is the intended gate neck. */
                    if(nx==ix-dx && ny==iy-dy) continue;
                    if(sMask[ny][nx]!=M_WALL || type_at(nx,ny)!=TT_SOLID) wide=0;
                }
            }
            if(wide) for(b=0;b<2;b++) for(a=0;a<2;a++) {
                int tx=ix+a*px+b*dx,ty=iy+a*py+b*dy;
                sMask[ty][tx]=M_FLOOR;
                room_set(tx,ty,sBlighted ? MT_BLIGHT_FLOOR : MT_MOSS0+(a+b)%3);
                room_set_overlay(tx,ty,MT_NONE);
            }
        }
        sMask[iy][ix]=M_FLOOR;
        room_set(ix,iy,sBlighted ? MT_BLIGHT_FLOOR : MT_MOSS0);
        room_set_overlay(ix,iy,(gWorld.cells[cell].opened & CELL_LOOTED) ? MT_NONE : MT_SPARKLE);
        /* The tempting dirt spur points into optional content, not
           necessarily to the next mandatory gate. The clue can mislead. */
        room_set(x,y,sTrail);
        for(n=1;n<=4;n++) {
            int tx=x-n*dx,ty=y-n*dy;
            if(!interior(tx,ty) || !is_floor(tx,ty)) break;
            if(sPath[ty][tx]&P_MID) {
                int j;
                for(j=1;j<n;j++) room_set(x-j*dx,y-j*dy,sTrail);
                break;
            }
        }
        gSpots.treasure.x=ix; gSpots.treasure.y=iy;
        gSpots.has_treasure=1;
        gSpots.pocket_gate.x=x+dx; gSpots.pocket_gate.y=y+dy;
        gSpots.pocket_kind=kind;
        refresh_edges(MIN(x,ix)-1,MIN(y,iy)-1,MAX(x,ix)+1,MAX(y,iy)+1);
        return;
    }
}

/* ------------------------------------------------- the chunk dressing -- */
/* What stands on open ground is laid by the chunk, as a designed piece:
   a tree, a ring of bushes, a fall of rocks, a ruined wall between its
   pillars, a colonnade, a hedge of thorns, two dead trees and their
   bones, a cluster of crystals, a lantern among flowers, a meadow, a
   clover patch, a hollow log by its stump, a great boulder, a tree on
   its rock, a fairy ring, a pool. Each thing checks it closes no way.
   Only what reads alone on a tile is still scattered alone: bushes,
   rocks, posts, stumps, logs, pillars, flowers and grass. */
enum { V_PLAIN, V_MEADOW, V_TREE, V_BUSHES, V_ROCKS, V_RUIN, V_COLONNADE, V_THORNS, V_DEAD, V_CRYSTAL,
       V_LANTERN, V_CLOVER, V_LOG, V_GBOULDER, V_TREEROCK, V_SHROOMRING, V_POOL };

/* plain ground that is not the trail and not a door's lane */
static bool8 plain_free(int x, int y) {
    return is_plain(x, y) && !(sPath[y][x] & P_MID) && !near_door(x, y);
}

static bool8 plain_block(int x, int y, int w, int h) {
    int dx, dy;
    for (dy = 0; dy < h; dy++)
        for (dx = 0; dx < w; dx++)
            if (!plain_free(x + dx, y + dy))
                return FALSE;
    return TRUE;
}

static void solid_at(int x, int y, u16 mt) {
    if (plain_free(x, y) && simple_spot(x, y))
        room_set(x, y, mt);
}

static void floor_at(int x, int y, u16 mt) {
    if (plain_free(x, y))
        room_set(x, y, mt);
}

static void block_at(int x, int y, int w, int h, u16 base, bool8 solid) {
    if (plain_block(x, y, w, h) && (!solid || simple_block(x, y, w, h)))
        stamp_ground(x, y, w, h, base);
}

static int pick_variant(const Cell* c, bool8 blighted) {
    int r = rng_range(&sR, 16);
    if (blighted)
        return r < 4 ? V_DEAD : r < 8 ? V_CRYSTAL : r < 10 ? V_POOL : r < 12 ? V_TREE : V_PLAIN;
    switch (c->arch) {
        case ARCH_GROVE: return r < 7 ? V_TREE : r < 9 ? V_LOG : r < 11 ? V_BUSHES : r < 12 ? V_TREEROCK : r < 13 ? V_CLOVER : V_PLAIN;
        case ARCH_RUINS: return r < 5 ? V_RUIN : r < 7 ? V_COLONNADE : r < 9 ? V_ROCKS : r < 11 ? V_TREE : r < 12 ? V_GBOULDER : V_PLAIN;
        case ARCH_THICKET: return r < 5 ? V_THORNS : r < 9 ? V_BUSHES : r < 11 ? V_TREE : r < 12 ? V_LOG : V_PLAIN;
        case ARCH_BONEYARD: return r < 5 ? V_DEAD : r < 7 ? V_POOL : r < 9 ? V_ROCKS : r < 10 ? V_TREE : r < 11 ? V_GBOULDER : V_PLAIN;
        case ARCH_POND: return r < 3 ? V_ROCKS : r < 5 ? V_LANTERN : r < 7 ? V_CLOVER : r < 9 ? V_TREE : r < 10 ? V_MEADOW : V_PLAIN;
        default:
            return r < 4 ? V_TREE : r < 6 ? V_BUSHES : r < 7 ? V_ROCKS : r < 8 ? V_LANTERN : r < 9 ? V_CLOVER : r < 10 ? V_LOG : r < 11 ? V_MEADOW : r < 12 ? V_GBOULDER : r < 13 ? V_TREEROCK : V_PLAIN;
    }
}

static void dress_chunk(int cx, int cy, int v, bool8 blighted) {
    static const u16 rocks[3] = { MT_ROCK, MT_ROCK2, MT_ROCK3 };
    int ox = CX0 + cx * 3, oy = CY0 + cy * 3, r = rng_range(&sR, 2);
    switch (v) {
        case V_MEADOW: block_at(ox, oy, 3, 3, MT_MEADOW_0, FALSE); break;
        case V_TREE:
            if (blighted)
                place_tree_kind(ox + r, oy, MT_BTREE_0, MT_BTREE_4);
            else
                place_tree(ox + r, oy);
            break;
        case V_BUSHES:
            solid_at(ox, oy, MT_BUSH); solid_at(ox + 2, oy + 1, MT_BUSH); solid_at(ox + 1, oy + 2, MT_BUSH);
            break;
        case V_ROCKS:
            solid_at(ox, oy, rocks[rng_range(&sR, 3)]); solid_at(ox + 2, oy + 1, rocks[rng_range(&sR, 3)]); solid_at(ox + 1, oy + 2, MT_ROCK_SMALL);
            break;
        case V_RUIN:
            solid_at(ox, oy, MT_PILLAR); solid_at(ox + 1, oy, MT_RUIN_WALL); solid_at(ox + 2, oy, MT_PILLAR);
            floor_at(ox, oy + 2, MT_MOSSY_STONE); floor_at(ox + 2, oy + 1, MT_MOSSY_STONE);
            break;
        case V_COLONNADE:
            solid_at(ox, oy, MT_PILLAR); solid_at(ox + 2, oy, MT_PILLAR); solid_at(ox, oy + 2, MT_PILLAR); solid_at(ox + 2, oy + 2, MT_PILLAR);
            floor_at(ox + 1, oy + 1, MT_MOSSY_STONE);
            break;
        case V_THORNS:
            if (r) {
                floor_at(ox, oy, MT_THORN); floor_at(ox + 1, oy, MT_THORN); floor_at(ox + 2, oy, MT_THORN);
            } else {
                floor_at(ox, oy, MT_THORN); floor_at(ox, oy + 1, MT_THORN); floor_at(ox, oy + 2, MT_THORN);
            }
            break;
        case V_DEAD:
            solid_at(ox, oy, MT_DEAD_TREE); solid_at(ox + 2, oy + 1, MT_DEAD_TREE);
            floor_at(ox + 1, oy + 2, blighted ? MT_BLIGHT_FLOOR2 : MT_BONES); floor_at(ox, oy + 2, blighted ? MT_BLIGHT_FLOOR : MT_BONES);
            break;
        case V_CRYSTAL:
            solid_at(ox + 1, oy, MT_BLIGHT_CRYSTAL); solid_at(ox, oy + 1, MT_BLIGHT_CRYSTAL); solid_at(ox + 2, oy + 1, MT_BLIGHT_CRYSTAL);
            floor_at(ox + 1, oy + 1, MT_BLIGHT_VEIN); floor_at(ox + 1, oy + 2, MT_BLIGHT_VEIN);
            break;
        case V_LANTERN:
            solid_at(ox + 1, oy + 1, MT_LANTERN_POST);
            floor_at(ox, oy, MT_MOSS_FLOWERS); floor_at(ox + 2, oy + 2, MT_MOSS_FLOWERS2);
            break;
        case V_CLOVER:
            block_at(ox + r, oy + r, 2, 2, MT_CLOVER_0, FALSE);
            floor_at(ox + 2 - r * 2, oy + 2 - r * 2, MT_MOSS_FLOWERS);
            break;
        case V_LOG:
            block_at(ox, oy + 1, 2, 1, MT_HLOG_0, TRUE);
            solid_at(ox + 2, oy, MT_STUMP);
            break;
        case V_GBOULDER: block_at(ox + r, oy + r, 2, 2, MT_GBOULDER_0, TRUE); break;
        case V_TREEROCK: block_at(ox + r, oy + r, 2, 2, MT_TREEROCK_0, TRUE); break;
        case V_SHROOMRING: block_at(ox + r, oy + r, 2, 2, MT_SHROOMRING_0, FALSE); break;
        case V_POOL:
            floor_at(ox + 1, oy + 1, MT_BLIGHT_POOL); floor_at(ox + 2, oy, blighted ? MT_BLIGHT_FLOOR2 : MT_BONES);
            break;
        default: break;
    }
}

/* Clusters follow shade and banks. A little litter in the clearing is
   deliberate; a random checkerboard of every possible prop is not. */
static void undergrowth(const Cell* c) {
    int patch;
    for(patch=0;patch<8;patch++) {
        int x=2+rng_range(&sR,W-4),y=3+rng_range(&sR,H-5),dx,dy;
        bool8 bank=watery(sMask[y][x-1]) || watery(sMask[y][x+1]) ||
                   sMask[y-1][x]==M_WALL || sMask[y+1][x]==M_WALL;
        if(!bank && patch>2) continue;
        for(dy=-1;dy<=1;dy++) for(dx=-1;dx<=1;dx++) {
            if(!plain_free(x+dx,y+dy) || (ABS(dx)+ABS(dy)>1 && (rng_next(&sR)&1))) continue;
            if(c->stage>=2 && rng_range(&sR,3)<c->stage-1)
                floor_at(x+dx,y+dy,MT_SICK_BONES);
            else
                floor_at(x+dx,y+dy,bank ? MT_FERN_PATCH : MT_LEAF_LITTER);
        }
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
        if (!is_floor(x, y) || (mode && (sPath[y][x] & P_BANK)))
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
            bool8 water=room_type(x,y)==TT_WATER;
            room_set(x, y, water ? (horiz ? MT_BRIDGE : MT_BRIDGE_V) : sTrail);
            sMask[y][x]=water ? (horiz ? M_BRIDGE_H : M_BRIDGE_V) : M_FLOOR;
            sPath[y][x]|=P_MID|(horiz ? P_H : P_V);
            room_set_overlay(x, y, MT_NONE);
        }
        if (horiz)
            x += (cx > x) ? 1 : -1;
        else
            y += (cy > y) ? 1 : -1;
    }
    if (!passable(cx, cy)) {
        room_set(cx, cy, sTrail);
        sMask[cy][cx]=M_FLOOR;
        sPath[cy][cx]|=P_MID;
        room_set_overlay(cx, cy, MT_NONE);
    }
}

/* A spot for something opened or lit from the south: a chest, a censer.
   Clearance first, then any spot that blocks nothing, always with open,
   reached ground in front of it; then the room's middle. */
static void ensure_spot(Spot* out);
static void ensure_fronted_spot(Spot* out) {
    int k;
    for (k = 0; k < 400; k++)
        if (find_spot(out, 1, 2) && is_floor(out->x, out->y + 1) && reached(out->x, out->y + 1))
            return;
    for (k = 0; k < 600; k++)
        if (find_spot(out, 1, 1) && is_floor(out->x, out->y + 1) && reached(out->x, out->y + 1))
            return;
    ensure_spot(out);
}

/* A spot for someone to talk to: clearance round them and two tiles of
   open, reached ground below, where the hero stands to speak. */
static void ensure_npc_spot(Spot* out) {
    int k;
    for (k = 0; k < 400; k++)
        if (find_spot(out, 1, 2) && is_floor(out->x, out->y + 2) && reached(out->x, out->y + 1) && reached(out->x, out->y + 2))
            return;
    ensure_fronted_spot(out);
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
            room_set(cx + dx, cy + dy, sTrail);
            room_set_overlay(cx + dx, cy + dy, MT_NONE);
        }
    out->x = cx;
    out->y = cy;
}

/* The mask alone, for the map: the same seed, plan, expansion, door
   lanes and falls as the build, and nothing after. It overwrites the
   generator's scratch, which nothing reads once a room is built. */
void roomgen_preview(int cell, const u8** mask, const u8** path) {
    Cell* c = &gWorld.cells[cell];
    int s;
    bool8 arena = (c->arch == ARCH_ARENA), entry = (c->arch == ARCH_ENTRY);
    rng_seed(&sR, hash32(gWorld.seed, cell * 7919 + 13));
    memset(sMask, 0, sizeof(sMask));
    memset(sPath, 0, sizeof(sPath));
    sTerraceRow = -1;
    plan(c, arena, entry);
    expand();
    shape_clearings();
    watershed(c, arena, entry);
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1, k;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        for (k = 1; k <= 6; k++) {
            int ox = (s == SIDE_E) ? -k : (s == SIDE_W) ? k : 0;
            int oy = (s == SIDE_N) ? k : (s == SIDE_S) ? -k : 0;
            carve(x0 + ox, y0 + oy);
            carve(x1 + ox, y1 + oy);
            if (interior(x0 + ox, y0 + oy) && watery(sMask[y0 + oy][x0 + ox]))
                sMask[y0 + oy][x0 + ox] = (s == SIDE_N || s == SIDE_S) ? M_BRIDGE_V : M_BRIDGE_H;
            if (interior(x1 + ox, y1 + oy) && watery(sMask[y1 + oy][x1 + ox]))
                sMask[y1 + oy][x1 + ox] = (s == SIDE_N || s == SIDE_S) ? M_BRIDGE_V : M_BRIDGE_H;
            if (interior(x0 + ox, y0 + oy))
                sPath[y0 + oy][x0 + ox] |= P_MID;
            if (interior(x1 + ox, y1 + oy))
                sPath[y1 + oy][x1 + ox] |= P_MID;
        }
    }
    add_waterfalls();
    bridge_landings();
    trail_story(c, arena, entry);
    *mask = &sMask[0][0];
    *path = &sPath[0][0];
}

/* ---------------------------------------------------------- the build -- */
/* ------------------------------------------------------------ the rot -- */
/* The blight breaking through a sick room's grass: a few soft blobs of
   the stained ground, kept only where every tile round is ground off
   the trail (so no edge of grass is broken), never a strip one tile
   wide, now and then a tile of it lit. Laid last, over nothing that was
   put down. */
static bool8 grassy(u16 t) {
    return t <= MT_TALL_GRASS;
}

static void lay_rot(int stage) {
    static u8 rot[H][W];
    s8 bx[6], by[6];
    u8 br[6];
    int n, k, x, y;
    if (stage < 1)
        return;
    n = (stage >= 2) ? 4 + rng_range(&sR, 3) : 1 + rng_range(&sR, 2);
    /* each blob's heart on open grass */
    for (k = 0; k < n; k++) {
        int t;
        for (t = 0; t < 40; t++) {
            bx[k] = 2 + rng_range(&sR, W - 4);
            by[k] = 3 + rng_range(&sR, H - 5);
            if (grassy(room_get(bx[k], by[k])))
                break;
        }
        br[k] = (stage >= 2) ? 4 + rng_range(&sR, 3) : 3 + rng_range(&sR, 2);
    }
    memset(rot, 0, sizeof(rot));
    for (y = 1; y < H - 1; y++)
        for (x = 1; x < W - 1; x++) {
            int f = rng_range(&sR, 64) - 32;
            for (k = 0; k < n; k++) {
                int dx = x - bx[k], dy = y - by[k], r2 = br[k] * br[k], d2 = dx * dx + dy * dy;
                if (d2 < r2)
                    f += (r2 - d2) * 256 / r2;
            }
            if (f >= 128 && grassy(room_get(x, y)) && room_get_overlay(x, y) == MT_NONE)
                rot[y][x] = 1;
        }
    for (y = 1; y < H - 1; y++)
        for (x = 1; x < W - 1; x++) {
            int dx, dy, ok = rot[y][x];
            for (dy = -1; dy <= 1 && ok; dy++)
                for (dx = -1; dx <= 1; dx++)
                    if (sMask[y + dy][x + dx] != M_FLOOR || (sPath[y + dy][x + dx] & P_MID))
                        ok = 0;
            if (ok)
                rot[y][x] = 2;
        }
    /* no strips one tile wide: a patch is a patch */
    for (k = 0; k < 3; k++)
        for (y = 1; y < H - 1; y++)
            for (x = 1; x < W - 1; x++)
                if (rot[y][x] == 2 && ((rot[y - 1][x] != 2 && rot[y + 1][x] != 2) || (rot[y][x - 1] != 2 && rot[y][x + 1] != 2)))
                    rot[y][x] = 1;
    for (y = 1; y < H - 1; y++)
        for (x = 1; x < W - 1; x++)
            if (rot[y][x] == 2)
                room_set(x, y, (rng_range(&sR, 8) == 0) ? MT_BLIGHT_GROUND2 : MT_BLIGHT_GROUND0 + (rng_next(&sR) & 1));
}

bool8 roomgen_blighted(int cell) {
    const Cell* c = &gWorld.cells[cell];
    return (c->stage >= 3) || (c->arch == ARCH_ARENA);
}

void roomgen_build(int cell) {
    Cell* c = &gWorld.cells[cell];
    int x, y, s, i;
    rng_seed(&sR, hash32(gWorld.seed, cell * 7919 + 13));
    memset(&gSpots, 0, sizeof(gSpots));
    memset(sMask, 0, sizeof(sMask));
    memset(sPath, 0, sizeof(sPath));
    sTerraceRow = -1;
    bool8 blighted = roomgen_blighted(cell);
    sBlighted = blighted;
    sStage = c->stage;
    sTrail = blighted ? MT_BLIGHT_VEIN : MT_PATH;
    bool8 arena = (c->arch == ARCH_ARENA), entry = (c->arch == ARCH_ENTRY);

    room_clear(W, H, MT_CANOPY);
    for (y = 0; y < H; y++)
        for (x = 0; x < W; x++)
            room_set_overlay(x, y, MT_NONE);

    /* the plan in chunks, then the mask from it */
    plan(c, arena, entry);
    expand();
    shape_clearings();
    watershed(c, arena, entry);

    /* the door corridors: two wide and six deep from each opening, a
       trail, so the lane a hero walks in by is always open to where the
       chunk paths take over */
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1, k;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        for (k = 1; k <= 6; k++) {
            int ox = (s == SIDE_E) ? -k : (s == SIDE_W) ? k : 0;
            int oy = (s == SIDE_N) ? k : (s == SIDE_S) ? -k : 0;
            carve(x0 + ox, y0 + oy);
            carve(x1 + ox, y1 + oy);
            if (interior(x0 + ox, y0 + oy) && watery(sMask[y0 + oy][x0 + ox]))
                sMask[y0 + oy][x0 + ox] = (s == SIDE_N || s == SIDE_S) ? M_BRIDGE_V : M_BRIDGE_H;
            if (interior(x1 + ox, y1 + oy) && watery(sMask[y1 + oy][x1 + ox]))
                sMask[y1 + oy][x1 + ox] = (s == SIDE_N || s == SIDE_S) ? M_BRIDGE_V : M_BRIDGE_H;
            if (interior(x0 + ox, y0 + oy))
                sPath[y0 + oy][x0 + ox] |= P_MID | ((s == SIDE_N || s == SIDE_S) ? P_V : P_H);
            if (interior(x1 + ox, y1 + oy))
                sPath[y1 + oy][x1 + ox] |= P_MID | ((s == SIDE_N || s == SIDE_S) ? P_V : P_H);
        }
    }
    add_waterfalls();
    bridge_landings();
    trail_story(c, arena, entry);

    /* lay the ground */
    for (y = 0; y < H; y++) {
        for (x = 0; x < W; x++) {
            u16 mt;
            switch (sMask[y][x]) {
                case M_FLOOR:
                    if ((sPath[y][x] & (P_MID | P_HIDDEN)) == P_MID)
                        mt = sTrail;
                    else
                        mt = blighted ? blight_pick() : moss_pick(c->stage);
                    break;
                case M_WATER: {
                    /* banks where ground lies beside it; lilies only on open water */
                    int bank = ((y == 0 || !watery(sMask[y - 1][x])) ? 1 : 0) | ((x == W - 1 || !watery(sMask[y][x + 1])) ? 2 : 0) |
                               ((y == H - 1 || !watery(sMask[y + 1][x])) ? 4 : 0) | ((x == 0 || !watery(sMask[y][x - 1])) ? 8 : 0);
                    if (y > 0 && sMask[y - 1][x] == M_FALL) {
                        mt = MT_WATER_FOAM; /* the churn under a fall */
                    } else if (bank) {
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
                case M_FALL: mt = MT_WATERFALL; break;
                case M_RAMP: mt = sTrail; break;
                default: mt = MT_CANOPY; break;
            }
            room_set(x, y, mt);
        }
    }
    /* lily rafts on the open water of the lakes: two by two of water with
       water all round, one raft to a lake, two to a room at most */
    {
        int rafts = 0, lx = -99, ly = -99;
        for (y = 2; y < H - 3 && rafts < 2; y++)
            for (x = 1; x < W - 3 && rafts < 2; x++) {
                int dx, dy, ok = 1;
                if (ABS(x - lx) < 8 && ABS(y - ly) < 8)
                    continue;
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
                    rafts++;
                    lx = x;
                    ly = y;
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
    /* the transitions: no generic boundary is a hard line. Plain grass
       that meets water gets a shore on those sides (or a nick where
       water lies at a corner only); grass that meets the canopy, or
       stands under a cliff, gets a verge; a trail gets grass creeping
       over its edges where grass lies beside it. The pack draws them in
       the living grass only, so a blighted room has none. */
    for (y = 1; y < H - 1 && !blighted; y++)
        for (x = 1; x < W - 1; x++) {
            u16 t;
            if (sMask[y][x] != M_FLOOR)
                continue;
            t = room_get(x, y);
            if ((sPath[y][x] & (P_MID | P_HIDDEN)) == P_MID) {
                int pm = ((sMask[y - 1][x] == M_FLOOR && ((sPath[y - 1][x] & (P_MID | P_HIDDEN)) != P_MID)) ? 1 : 0) | ((sMask[y][x + 1] == M_FLOOR && ((sPath[y][x + 1] & (P_MID | P_HIDDEN)) != P_MID)) ? 2 : 0) |
                         ((sMask[y + 1][x] == M_FLOOR && ((sPath[y + 1][x] & (P_MID | P_HIDDEN)) != P_MID)) ? 4 : 0) | ((sMask[y][x - 1] == M_FLOOR && ((sPath[y][x - 1] & (P_MID | P_HIDDEN)) != P_MID)) ? 8 : 0);
                if (pm && t == MT_PATH)
                    room_set(x, y, MT_PEDGE_1 + pm - 1);
                continue;
            }
            if (t > MT_MOSS_BLIGHT2)
                continue;
            t = grass_edge(x, y);
            if (t)
                room_set(x, y, t);
        }

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
            if (below != M_WALL && below != M_FALL)
                /* a face over ground, and over water too: trunks at the water's edge */
                mt = blighted ? ((rng_range(&sR, 5) == 0) ? MT_BLIGHT_WALL_LIT : (rng_next(&sR) & 1) ? MT_BLIGHT_WALL : MT_BLIGHT_WALL2) : MT_CANOPY_S;
            else if (above != M_WALL && above != M_WATER)
                /* the pack draws no blighted crown: the sick canopy goes to the edge */
                mt = blighted ? MT_CANOPY_BLIGHT : MT_CANOPY_N;
            else if (blighted)
                mt = (rng_range(&sR, 3) == 0) ? MT_CANOPY_BLIGHT2 : MT_CANOPY_BLIGHT;
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
            room_set(x0, 0, sTrail); room_set(x1, 0, sTrail);
            room_set(x0, 1, sTrail); room_set(x1, 1, sTrail);
        } else if (s == SIDE_S) {
            room_set(x0, H - 1, sTrail); room_set(x1, H - 1, sTrail);
        } else if (s == SIDE_E) {
            room_set(W - 1, y0, sTrail); room_set(W - 1, y1, sTrail);
        } else {
            room_set(0, y0, sTrail); room_set(0, y1, sTrail);
        }
        u16 gt = sTrail;
        bool8 open = world_gate_open(cell, s);
        switch (g) {
            case GATE_THORN: gt = MT_THORN; break;
            case GATE_CRACK: gt = open ? MT_DOOR_OPEN : MT_CRACK; break;
            case GATE_WEB: gt = open ? sTrail : MT_WEB; break;
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
                room_set(x0, 0, sTrail); room_set(x1, 0, sTrail);
            }
        }
    }

    /* dressing: a great tree or two whose crown lies over the forest
       above its roots; then every open chunk gets its piece; then what
       may stand alone on a tile, narrowing the ways but never closing
       one; then the ground's accents */
    if (!arena && !blighted) {
        int want = (c->arch == ARCH_GROVE) ? 2 : (rng_range(&sR, 3) != 0) ? 1 : 0, k;
        for (k = 0; k < 40 && want > 0; k++) {
            int cx = rng_range(&sR, CW), cy = 1 + rng_range(&sR, CH - 1);
            if (ckind(cx, cy) == K_OPEN && ckind(cx, cy - 1) != K_WATER && place_great_tree(CX0 + cx * 3, CY0 + cy * 3 - 3))
                want--;
        }
    }
    if (!arena) {
        int cx, cy;
        for (cy = 0; cy < CH; cy++)
            for (cx = 0; cx < CW; cx++)
                if (ckind(cx, cy) == K_OPEN)
                    dress_chunk(cx, cy, pick_variant(c, blighted), blighted);
    }
    if (!blighted) {
        scatter_solid(MT_BUSH, 3 + rng_range(&sR, 3), 120);
        scatter_solid(MT_ROCK_SMALL, 1 + rng_range(&sR, 3), 80);
        scatter_rocks(1 + rng_range(&sR, 2), 60);
        scatter_solid(MT_STUMP, rng_range(&sR, 2), 40);
        scatter_solid(MT_LOG, rng_range(&sR, 2), 40);
        scatter_solid(MT_LANTERN_POST, rng_range(&sR, 2), 40);
        undergrowth(c);
        scatter_floor(MT_TALL_GRASS, 6);
        scatter_floor(MT_MOSS_FLOWERS, 5);
        scatter_floor(MT_MOSS_FLOWERS2, 3);
        if(c->stage>=2) {
            scatter_solid(MT_SICK_STUMP,2,50);
            scatter_solid(MT_SICK_ROCK,2,50);
        }
    } else {
        /* the pack draws stones and bones on grass: the blight keeps to its own */
        scatter_floor(MT_BLIGHT_FLOOR2, 3);
        scatter_solid(MT_SICK_ROCK,2,50);
        scatter_solid(MT_SICK_STUMP,2,50);
    }
    switch (blighted && !arena ? ARCH_COUNT : c->arch) {
        case ARCH_RUINS:
            scatter_solid(MT_PILLAR, 1 + rng_range(&sR, 2), 80);
            scatter_floor(MT_MOSSY_STONE, 10);
            if (rng_range(&sR, 3) == 0)
                scatter_solid(MT_STATUE, 1, 40);
            break;
        case ARCH_THICKET:
            scatter_solid(MT_BUSH, 3, 60);
            break;
        case ARCH_BONEYARD:
            scatter_floor(MT_BONES, 8);
            scatter_rocks(1, 40);
            break;
        case ARCH_POND:
            scatter_rocks(2, 40);
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
                room_set(ax, ay, sTrail);
                room_set_overlay(ax, ay, MT_NONE);
            }
            if (interior(bx, by) && (!passable(bx, by) || room_get_overlay(bx, by) != MT_NONE)) {
                room_set(bx, by, sTrail);
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

    /* the mystery's mouth: a face of the wall with reached ground below */
    if (gWorld.myst[cell]) {
        int tries, style = MYST_STYLE(gWorld.myst[cell]);
        for (tries = 0; tries < 400; tries++) {
            int mx = 2 + rng_range(&sR, W - 4), my = 1 + rng_range(&sR, H - 4);
            if (sMask[my][mx] == M_WALL && sMask[my + 1][mx] == M_FLOOR && is_floor(mx, my + 1) && reached(mx, my + 1) && !near_door(mx, my + 1) &&
                room_get_overlay(mx, my) == MT_NONE) {
                room_set(mx, my, style == MY_CAVE ? MT_MOUTH_CAVE : style == MY_HOLLOW ? MT_MOUTH_HOLLOW : MT_MOUTH_THICKET);
                gSpots.mouth.x = mx;
                gSpots.mouth.y = my;
                gSpots.has_mouth = 1;
                break;
            }
        }
        if (!gSpots.has_mouth) {
            /* Guaranteed task access even when no random wall-face trial
               succeeded: connect a secluded face to the central clearing. */
            int mx = (hash32(gWorld.seed,cell) & 1) ? 4 : W-5, my = 3;
            int ax,ay,rx=W/2,ry=H/2;
            for(ay=2;ay<H-1;ay++) for(ax=1;ax<W-1;ax++)
                if(reached(ax,ay)) {rx=ax;ry=ay;}
            carve_to_center(mx,my+1);
            carve_to_center(rx,ry);
            sMask[my][mx]=M_WALL;
            room_set(mx,my,style==MY_CAVE ? MT_MOUTH_CAVE : style==MY_HOLLOW ? MT_MOUTH_HOLLOW : MT_MOUTH_THICKET);
            room_set_overlay(mx,my,MT_NONE);
            gSpots.mouth.x=mx; gSpots.mouth.y=my; gSpots.has_mouth=1;
            flood_reach(W/2,H/2);
        }
    }
    /* role objects */
    switch (c->role) {
        case ROLE_KEYITEM:
            /* Its reward is earned in the mandatory mystery, not handed
               out by a second free chest in the forest. */
            break;
        case ROLE_CHEST:
        case ROLE_KEYCHEST:
            ensure_fronted_spot(&gSpots.chest);
            gSpots.has_chest = 1;
            room_set(gSpots.chest.x, gSpots.chest.y, (c->flags & CF_CHEST_OPEN) ? MT_CHEST_OPEN : MT_CHEST);
            break;
        case ROLE_NPC_HUNT:
        case ROLE_NPC_FETCH:
            ensure_npc_spot(&gSpots.npc);
            gSpots.has_npc = 1;
            break;
        case ROLE_NPC_TORCH:
            ensure_npc_spot(&gSpots.npc);
            gSpots.has_npc = 1;
            for (i = 0; i < 4; i++) {
                /* a censer wants open ground in front of it, to the south,
                   where the hero stands to swing the lamp */
                Spot t;
                ensure_fronted_spot(&t);
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
    /* Side pockets never hold a mandatory reward. Their entrance is on
       the already-proved connected component, their interior deliberately
       inaccessible until the player returns with the corresponding item. */
    if (!arena && !entry && (hash32(gWorld.seed, cell * 73 + 211) % 5 < 4))
        dig_alcove(cell);
    /* monster spots: the rooms are bigger, so a few more */
    {
        int n = c->density + (c->density ? 2 : 0);
        for (i = 0; i < n && gSpots.spawn_count < 12; i++) {
            Spot sp;
            if (find_spot(&sp, 60, 0))
                gSpots.spawns[gSpots.spawn_count++] = sp;
        }
    }
    /* the map's marks for this cell */
    {
        u8* m = gWorld.mark[cell];
        memset(m, 0, MP_COUNT * 2);
        if (gSpots.has_mouth) { m[MP_MOUTH * 2] = gSpots.mouth.x + 1; m[MP_MOUTH * 2 + 1] = gSpots.mouth.y + 1; }
        if (gSpots.has_npc) { m[MP_NPC * 2] = gSpots.npc.x + 1; m[MP_NPC * 2 + 1] = gSpots.npc.y + 1; }
        if (gSpots.has_chest) { m[MP_CHEST * 2] = gSpots.chest.x + 1; m[MP_CHEST * 2 + 1] = gSpots.chest.y + 1; }
        if (gSpots.has_relic) { m[MP_RELIC * 2] = gSpots.relic.x + 1; m[MP_RELIC * 2 + 1] = gSpots.relic.y + 1; }
        if (gSpots.has_shrine) { m[MP_SHRINE * 2] = gSpots.shrine.x + 1; m[MP_SHRINE * 2 + 1] = gSpots.shrine.y + 1; }
    }
    if (!blighted)
        lay_rot(c->stage);
    /* gold on the floor: the wood is rotten, but it shines; white stars
       over the living rooms, a mist over the rotten ones */
    for (i = 0; i < 12; i++) {
        int px = 2 + rng_range(&sR, W - 4), py = 3 + rng_range(&sR, H - 5);
        if (is_floor(px, py))
            room_set_overlay(px, py, MT_SPARKLE);
    }
    for (i = 0; i < (blighted ? 14 : 10); i++) {
        int px = 2 + rng_range(&sR, W - 4), py = 3 + rng_range(&sR, H - 5);
        if (is_floor(px, py))
            room_set_overlay(px, py, blighted ? MT_BLIGHT_MIST : MT_SPARKLE_WHITE);
    }
    /* Skin only after placement, spawn selection and map marks are finished.
       Coordinate hashes add variety without consuming the layout RNG. All
       replacements retain the original type and quarter collision mask. */
    for (y = 0; y < H; y++) {
        for (x = 0; x < W; x++) {
            u16 mt = room_get(x, y);
            u32 ink = hash32(gWorld.seed, cell * 7919 + y * W + x);
            if (mt == MT_BLIGHT_FLOOR || mt == MT_BLIGHT_FLOOR2) {
                int dx=x-W/2,dy=y-H/2;
                bool8 heart_vein=arena && ((ABS(dx*2+dy)%7==0) || (ABS(dx-dy*2)%9==0) ||
                                        (dx*dx+dy*dy>=25 && dx*dx+dy*dy<=36));
                room_set(x,y,heart_vein ? MT_FOREST_ROT7 : MT_FOREST_ROT0+ink%8);
            }
            else if (mt == MT_CANOPY || mt == MT_CANOPY2)
                room_set(x, y, MT_FOREST_CANOPY0 + ((x + (gWorld.seed & 1)) & 1) + 2 * ((y + ((gWorld.seed >> 1) & 1)) & 1));
        }
    }
    room_render();
}
