/* BARTGAME: a forest room from a cell. Deterministic from the world seed
   and the cell index, so a room is the same every visit.

   The room is 24x16 metatiles: a canopy border (two thick on top so the
   trunks show), door openings two wide in the middle of each open side,
   the gate tiles in the opening, an archetype's features inside, then a
   flood check from the north door so every door and every placed thing
   can be reached with the sword alone (thorns count as passable). */
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

static u16 moss_pick(void) {
    int r = rng_range(&sR, 20);
    if (r < 12)
        return MT_MOSS0 + rng_range(&sR, 3);
    if (r < 15)
        return MT_MOSS_BLIGHT;
    if (r < 17)
        return MT_MOSS_BLIGHT2;
    if (r < 19)
        return MT_MOSS_FLOWERS;
    return MT_BONES;
}

static int inside(int x, int y) {
    return x >= 1 && y >= 2 && x <= W - 2 && y <= H - 2;
}

static u8 type_at(int x, int y) {
    return room_type(x, y);
}

static bool8 passable(int x, int y) {
    u8 t = type_at(x, y);
    return t == TT_FLOOR || t == TT_SLOW || t == TT_HURT || t == TT_THORN || t == TT_DOOR_OPEN || t == TT_STAIRS;
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

static void place_rect(int x0, int y0, int x1, int y1, u16 mt) {
    int x, y;
    for (y = y0; y <= y1; y++)
        for (x = x0; x <= x1; x++)
            if (inside(x, y))
                room_set(x, y, mt);
}

/* a free-standing tree: 2x3, canopy on the overlay, trunks solid */
static void place_tree(int x, int y) {
    if (x < 1 || y < 2 || x + 1 > W - 2 || y + 2 > H - 2)
        return;
    room_set_overlay(x, y, MT_TREE_TOP_NW);
    room_set_overlay(x + 1, y, MT_TREE_TOP_NE);
    room_set_overlay(x, y + 1, MT_TREE_MID_W);
    room_set_overlay(x + 1, y + 1, MT_TREE_MID_E);
    room_set(x, y + 2, MT_TREE_TRUNK_W);
    room_set(x + 1, y + 2, MT_TREE_TRUNK_E);
}

static bool8 is_floor(int x, int y) {
    return inside(x, y) && type_at(x, y) == TT_FLOOR && room_get_overlay(x, y) == MT_NONE;
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

static bool8 near_door(int x, int y) {
    int s, x0, y0, x1, y1;
    for (s = 0; s < 4; s++) {
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        if (ABS(x - x0) <= 3 && ABS(y - y0) <= 3)
            return TRUE;
        if (ABS(x - x1) <= 3 && ABS(y - y1) <= 3)
            return TRUE;
    }
    return FALSE;
}

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

/* Find a spot with clearance, reachable, not near a door. */
static bool8 find_spot(Spot* out, int tries, bool8 need_clear) {
    int i;
    for (i = 0; i < tries; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!reached(x, y) || near_door(x, y))
            continue;
        if (need_clear && !clear3(x, y))
            continue;
        if (!is_floor(x, y))
            continue;
        out->x = x;
        out->y = y;
        return TRUE;
    }
    return FALSE;
}

/* carve passable tiles toward the room center from a blocked spot: the
   repair step when the flood misses something */
static void carve_to_center(int x, int y) {
    int cx = W / 2, cy = H / 2;
    while (x != cx || y != cy) {
        if (inside(x, y) && !passable(x, y)) {
            room_set(x, y, MT_PATH);
            room_set_overlay(x, y, MT_NONE);
        }
        if (x != cx)
            x += (cx > x) ? 1 : -1;
        else
            y += (cy > y) ? 1 : -1;
    }
}

static void features_glade(void) {
    int i, n = 2 + rng_range(&sR, 3);
    for (i = 0; i < n; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            room_set(x, y, (rng_next(&sR) & 1) ? MT_ROCK : MT_STUMP);
    }
    for (i = 0; i < 6; i++)
        room_set(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_MOSS_FLOWERS);
}

static void features_grove(void) {
    int i, n = 3 + rng_range(&sR, 3);
    for (i = 0; i < n; i++) {
        int x = 2 + rng_range(&sR, W - 5), y = 2 + rng_range(&sR, H - 6);
        if (!near_door(x, y + 2) && !near_door(x + 1, y + 2))
            place_tree(x, y);
    }
    for (i = 0; i < 3; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            room_set(x, y, MT_THORN);
    }
}

static void features_ruins(void) {
    int i;
    /* a broken wall line and some pillars, mossy stone underfoot */
    int wy = 4 + rng_range(&sR, H - 9);
    int wx0 = 3 + rng_range(&sR, 6), wx1 = wx0 + 4 + rng_range(&sR, 8);
    for (i = wx0; i <= wx1 && i < W - 2; i++) {
        if (near_door(i, wy))
            continue;
        int r = rng_range(&sR, 6);
        room_set(i, wy, r == 0 ? MT_PILLAR : r < 4 ? MT_RUIN_WALL : MT_MOSSY_STONE);
    }
    for (i = 0; i < 4; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            room_set(x, y, MT_PILLAR);
    }
    for (i = 0; i < 10; i++)
        room_set(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_MOSSY_STONE);
}

static void features_pond(void) {
    int cx = 6 + rng_range(&sR, W - 12), cy = 5 + rng_range(&sR, H - 10);
    int rx = 2 + rng_range(&sR, 3), ry = 1 + rng_range(&sR, 2);
    int x, y;
    for (y = cy - ry; y <= cy + ry; y++)
        for (x = cx - rx; x <= cx + rx; x++) {
            int dx = (x - cx) * ry, dy = (y - cy) * rx;
            if (dx * dx + dy * dy <= rx * rx * ry * ry && inside(x, y) && !near_door(x, y))
                room_set(x, y, MT_WATER);
        }
    int i;
    for (i = 0; i < 3; i++) {
        int px = 2 + rng_range(&sR, W - 4), py = 3 + rng_range(&sR, H - 5);
        if (!near_door(px, py))
            room_set(px, py, MT_ROCK);
    }
    for (i = 0; i < 4; i++)
        room_set_overlay(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_SPARKLE);
}

static void features_thicket(void) {
    int i, n = 10 + rng_range(&sR, 8);
    for (i = 0; i < n; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            room_set(x, y, (rng_range(&sR, 4) == 0) ? MT_STUMP : MT_THORN);
    }
    for (i = 0; i < 2; i++) {
        int x = 2 + rng_range(&sR, W - 5), y = 2 + rng_range(&sR, H - 6);
        if (!near_door(x, y + 2) && !near_door(x + 1, y + 2))
            place_tree(x, y);
    }
}

static void features_boneyard(void) {
    int i;
    for (i = 0; i < 8; i++)
        room_set(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_BONES);
    for (i = 0; i < 4; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            place_rect(x, y, x + 1, y, MT_BLIGHT_POOL);
    }
    for (i = 0; i < 3; i++) {
        int x = 2 + rng_range(&sR, W - 4), y = 3 + rng_range(&sR, H - 5);
        if (!near_door(x, y))
            room_set(x, y, MT_ROCK);
    }
    /* a chasm with a ledge above it: one-way drop */
    {
        int x = 4 + rng_range(&sR, W - 10), y = 5 + rng_range(&sR, H - 10);
        if (!near_door(x, y) && !near_door(x + 3, y + 1)) {
            place_rect(x, y + 1, x + 3, y + 1, MT_PIT);
            place_rect(x, y, x + 3, y, MT_LEDGE_S);
        }
    }
}

static void features_arena(void) {
    room_set(3, 4, MT_PILLAR);
    room_set(W - 4, 4, MT_PILLAR);
    room_set(3, H - 4, MT_PILLAR);
    room_set(W - 4, H - 4, MT_PILLAR);
    int i;
    for (i = 0; i < 14; i++)
        room_set(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_MOSSY_STONE);
    for (i = 0; i < 6; i++)
        room_set(3 + rng_range(&sR, W - 6), 4 + rng_range(&sR, H - 7), MT_MOSS_BLIGHT2);
    place_rect(W / 2 - 2, 2, W / 2 + 1, 2, MT_BLIGHT_POOL);
}

static void features_entry(void) {
    int i;
    for (i = 0; i < 6; i++)
        room_set(2 + rng_range(&sR, W - 4), 3 + rng_range(&sR, H - 5), MT_MOSS_FLOWERS);
    room_set(4, 5, MT_STUMP);
    room_set(W - 5, 5, MT_ROCK);
    room_set_overlay(6, 9, MT_SPARKLE);
    room_set_overlay(W - 7, 10, MT_SPARKLE);
}

void roomgen_build(int cell) {
    Cell* c = &gWorld.cells[cell];
    int x, y, s;
    rng_seed(&sR, hash32(gWorld.seed, cell * 7919 + 13));
    memset(&gSpots, 0, sizeof(gSpots));

    room_clear(W, H, MT_MOSS0);
    for (y = 0; y < H; y++)
        for (x = 0; x < W; x++)
            room_set(x, y, moss_pick());
    /* the canopy border */
    for (x = 0; x < W; x++) {
        room_set(x, 0, (rng_next(&sR) & 1) ? MT_CANOPY : MT_CANOPY2);
        room_set(x, 1, MT_CANOPY_S);
        room_set(x, H - 1, MT_CANOPY_N);
    }
    for (y = 0; y < H; y++) {
        room_set(0, y, (rng_next(&sR) & 1) ? MT_CANOPY : MT_CANOPY2);
        room_set(W - 1, y, (rng_next(&sR) & 1) ? MT_CANOPY : MT_CANOPY2);
    }
    /* door openings and their gates */
    for (s = 0; s < 4; s++) {
        int g = c->gate[s];
        int x0, y0, x1, y1;
        if (g == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        /* the whole opening through the border is path */
        if (s == SIDE_N) {
            place_rect(x0, 0, x1, 1, MT_PATH);
            room_set(x0, 0, MT_PATH);
            room_set(x1, 0, MT_PATH);
            room_set(x0, 1, MT_PATH);
            room_set(x1, 1, MT_PATH);
        } else if (s == SIDE_S) {
            room_set(x0, H - 1, MT_PATH);
            room_set(x1, H - 1, MT_PATH);
        } else if (s == SIDE_E) {
            room_set(W - 1, y0, MT_PATH);
            room_set(W - 1, y1, MT_PATH);
        } else {
            room_set(0, y0, MT_PATH);
            room_set(0, y1, MT_PATH);
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
            if (g == GATE_CHASM) {
                /* a pit band through the whole opening, 1 deep */
                if (s == SIDE_N) {
                    room_set(x0, 1, MT_PIT);
                    room_set(x1, 1, MT_PIT);
                    room_set(x0, 0, MT_PATH);
                    room_set(x1, 0, MT_PATH);
                }
            }
        }
    }
    /* features */
    switch (c->arch) {
        case ARCH_GLADE: features_glade(); break;
        case ARCH_GROVE: features_grove(); break;
        case ARCH_RUINS: features_ruins(); break;
        case ARCH_POND: features_pond(); break;
        case ARCH_THICKET: features_thicket(); break;
        case ARCH_BONEYARD: features_boneyard(); break;
        case ARCH_ARENA: features_arena(); break;
        default: features_entry(); break;
    }
    /* keep the door approaches open: two tiles in from each opening */
    for (s = 0; s < 4; s++) {
        int x0, y0, x1, y1;
        if (c->gate[s] == GATE_WALL)
            continue;
        roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
        int ax = x0, ay = y0, bx = x1, by = y1;
        int k;
        for (k = 1; k <= 2; k++) {
            int ox = (s == SIDE_E) ? -k : (s == SIDE_W) ? k : 0;
            int oy = (s == SIDE_N) ? k : (s == SIDE_S) ? -k : 0;
            if (inside(ax + ox, ay + oy)) {
                if (!passable(ax + ox, ay + oy) || room_get_overlay(ax + ox, ay + oy) != MT_NONE) {
                    room_set(ax + ox, ay + oy, MT_PATH);
                    room_set_overlay(ax + ox, ay + oy, MT_NONE);
                }
            }
            if (inside(bx + ox, by + oy)) {
                if (!passable(bx + ox, by + oy) || room_get_overlay(bx + ox, by + oy) != MT_NONE) {
                    room_set(bx + ox, by + oy, MT_PATH);
                    room_set_overlay(bx + ox, by + oy, MT_NONE);
                }
            }
        }
    }
    /* connectivity: flood from the first open door's inner tile, carve to
       any other door that is cut off */
    {
        int sx = -1, sy = -1;
        for (s = 0; s < 4 && sx < 0; s++) {
            if (c->gate[s] == GATE_WALL)
                continue;
            int x0, y0, x1, y1;
            roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
            sx = x0 + ((s == SIDE_W) ? 1 : (s == SIDE_E) ? -1 : 0);
            sy = y0 + ((s == SIDE_N) ? 1 : (s == SIDE_S) ? -1 : 0);
        }
        if (sx < 0) {
            sx = W / 2;
            sy = H / 2;
        }
        int pass;
        for (pass = 0; pass < 3; pass++) {
            flood_reach(sx, sy);
            bool8 ok = TRUE;
            for (s = 0; s < 4; s++) {
                if (c->gate[s] == GATE_WALL)
                    continue;
                int x0, y0, x1, y1;
                roomgen_gate_tiles(s, &x0, &y0, &x1, &y1);
                int ix = x0 + ((s == SIDE_W) ? 1 : (s == SIDE_E) ? -1 : 0);
                int iy = y0 + ((s == SIDE_N) ? 1 : (s == SIDE_S) ? -1 : 0);
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
            if (find_spot(&gSpots.chest, 200, TRUE)) {
                gSpots.has_chest = 1;
                room_set(gSpots.chest.x, gSpots.chest.y, (c->flags & CF_CHEST_OPEN) ? MT_CHEST_OPEN : MT_CHEST);
            }
            break;
        case ROLE_NPC_HUNT:
        case ROLE_NPC_FETCH:
            if (find_spot(&gSpots.npc, 200, TRUE))
                gSpots.has_npc = 1;
            break;
        case ROLE_NPC_TORCH: {
            int i;
            if (find_spot(&gSpots.npc, 200, TRUE))
                gSpots.has_npc = 1;
            for (i = 0; i < 4; i++) {
                Spot t;
                if (find_spot(&t, 200, TRUE)) {
                    gSpots.torches[gSpots.torch_count++] = t;
                    room_set(t.x, t.y, (c->flags & CF_QUEST_DONE) ? MT_TORCH_LIT : MT_TORCH);
                }
            }
            break;
        }
        case ROLE_RELIC:
            if (!(c->flags & CF_RELIC_TAKEN) && find_spot(&gSpots.relic, 200, TRUE)) {
                gSpots.has_relic = 1;
                room_set(gSpots.relic.x, gSpots.relic.y, MT_MOSSY_STONE);
                room_set_overlay(gSpots.relic.x, gSpots.relic.y, MT_SPARKLE);
            }
            break;
        case ROLE_SHRINE:
            if (find_spot(&gSpots.shrine, 200, TRUE)) {
                gSpots.has_shrine = 1;
                room_set(gSpots.shrine.x, gSpots.shrine.y, MT_PILLAR);
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
    /* enemy spawn spots */
    {
        int i, n = c->density;
        for (i = 0; i < n && gSpots.spawn_count < 12; i++) {
            Spot sp;
            if (find_spot(&sp, 60, FALSE))
                gSpots.spawns[gSpots.spawn_count++] = sp;
        }
    }
    /* a few sparkles on the floor */
    {
        int i;
        for (i = 0; i < 2; i++) {
            int px = 2 + rng_range(&sR, W - 4), py = 3 + rng_range(&sR, H - 5);
            if (is_floor(px, py))
                room_set_overlay(px, py, MT_SPARKLE);
        }
    }
    room_render();
}
