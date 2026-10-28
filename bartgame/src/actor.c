/* BARTGAME: the actor pool, movement against tiles, hit tests, drawing. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "interactive.h"
#include "ambient.h"

Actor gActors[ACTOR_MAX];

const Hitbox gHitboxes[] = {
    [HB_HERO] = { 0, -11, 6, 10 },
    [HB_HERO_FEET] = { 0, -4, 5, 4 },
    [HB_SMALL] = { 0, -6, 5, 5 },
    [HB_MED] = { 0, -8, 7, 7 },
    [HB_TALL] = { 0, -13, 7, 13 },
    [HB_BIG] = { 0, -16, 14, 14 },
    [HB_PROJ] = { 0, -6, 3, 3 },
    [HB_SWORD] = { 0, -8, 8, 8 },
    [HB_BLAST] = { 0, -8, 20, 20 },
    [HB_HEART] = { 0, -22, 14, 20 },
    [HB_ARROW] = { 0, -14, 3, 3 },
    [HB_PERSON] = { 0, -12, 7, 12 },
};

void actors_clear(void) {
    memset(gActors, 0, sizeof(gActors));
}

Actor* actor_new(u8 kind, u8 type, int px, int py) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++) {
        Actor* a = &gActors[i];
        if (a->kind == AK_NONE) {
            memset(a, 0, sizeof(*a));
            a->kind = kind;
            a->type = type;
            a->x = px << 16;
            a->y = py << 16;
            a->facing = FACE_S;
            a->dir = DIR_S;
            a->hitbox = HB_MED;
            a->prio = 2;
            return a;
        }
    }
    return NULL;
}

void actor_free(Actor* a) {
    a->kind = AK_NONE;
}

int actor_count(u8 kind) {
    int i, n = 0;
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == kind)
            n++;
    return n;
}

Actor* actor_find(u8 kind, u8 type) {
    int i;
    for (i = 1; i < ACTOR_MAX; i++)
        if (gActors[i].kind == kind && gActors[i].type == type)
            return &gActors[i];
    return NULL;
}

int dir_to_facing(int dir) {
    return ((dir + 4) >> 3) & 3;
}

int facing_to_dir(int facing) {
    return facing * 8;
}

/* The feet box of the actor if it stood at (px, py). */
bool8 actor_feet_box_solid(const Actor* a, int px, int py) {
    const Hitbox* hb = &gHitboxes[HB_HERO_FEET];
    if (a->kind != AK_PLAYER)
        hb = &gHitboxes[a->hitbox];
    int cx = px + hb->ox, cy = py + hb->oy;
    int hw = hb->hw, hh = hb->hh;
    if (a->kind != AK_PLAYER) {
        /* enemies collide with a short box at their feet */
        hh = MIN(hh, 5);
        cy = py - hh;
    }
    return room_box_solid(cx - hw, cy - hh, cx + hw - 1, cy + hh - 1);
}

/* Move with tile collision, one pixel at a time when blocked, with corner
   assist: a hero caught on the edge of a tile is nudged around it. */
bool8 actor_move(Actor* a, int speed, int dir) {
    int d8 = dir * 8;
    s32 vx = (speed * SIN(d8)) >> 14;
    s32 vy = -(speed * COS(d8)) >> 14;
    a->vx = vx;
    a->vy = vy;
    a->coll = 0;
    if (a->flags & AF_FLYING) {
        a->x += vx << 8;
        a->y += vy << 8;
        return FALSE;
    }
    /* X axis */
    if (vx) {
        s32 nx = a->x + (vx << 8);
        int px = PX(nx), py = PX(a->y);
        if (!actor_feet_box_solid(a, px, py)) {
            a->x = nx;
        } else {
            int step = vx > 0 ? 1 : -1;
            int cx = PX(a->x);
            while (cx != px && !actor_feet_box_solid(a, cx + step, py))
                cx += step;
            a->x = cx << 16;
            a->coll |= vx > 0 ? COLL_E : COLL_W;
            /* corner assist */
            if (a->kind == AK_PLAYER) {
                const Hitbox* hb = &gHitboxes[HB_HERO_FEET];
                int ex = cx + step * hb->hw + (step > 0 ? 0 : -1) + step;
                int top = py + hb->oy - hb->hh, bot = py + hb->oy + hb->hh - 1;
                if (!room_solid_px(ex, top) && !room_solid_px(ex, top + 3) && room_solid_px(ex, bot)) {
                    if (!actor_feet_box_solid(a, cx, py - 1))
                        a->y -= 1 << 16;
                } else if (!room_solid_px(ex, bot) && !room_solid_px(ex, bot - 3) && room_solid_px(ex, top)) {
                    if (!actor_feet_box_solid(a, cx, py + 1))
                        a->y += 1 << 16;
                }
            }
        }
    }
    /* Y axis */
    if (vy) {
        s32 ny = a->y + (vy << 8);
        int px = PX(a->x), py = PX(ny);
        if (!actor_feet_box_solid(a, px, py)) {
            a->y = ny;
        } else {
            int step = vy > 0 ? 1 : -1;
            int cy = PX(a->y);
            while (cy != py && !actor_feet_box_solid(a, px, cy + step))
                cy += step;
            a->y = cy << 16;
            a->coll |= vy > 0 ? COLL_S : COLL_N;
            if (a->kind == AK_PLAYER) {
                const Hitbox* hb = &gHitboxes[HB_HERO_FEET];
                int ey = cy + hb->oy + step * hb->hh + (step > 0 ? -1 : 0) + step;
                int lft = px - hb->hw, rgt = px + hb->hw - 1;
                if (!room_solid_px(lft, ey) && !room_solid_px(lft + 3, ey) && room_solid_px(rgt, ey)) {
                    if (!actor_feet_box_solid(a, px - 1, cy))
                        a->x -= 1 << 16;
                } else if (!room_solid_px(rgt, ey) && !room_solid_px(rgt - 3, ey) && room_solid_px(lft, ey)) {
                    if (!actor_feet_box_solid(a, px + 1, cy))
                        a->x += 1 << 16;
                }
            }
        }
    }
    return a->coll != 0;
}

void actor_move_free(Actor* a, int speed, int dir) {
    int d8 = dir * 8;
    s32 vx = (speed * SIN(d8)) >> 14;
    s32 vy = -(speed * COS(d8)) >> 14;
    a->vx = vx;
    a->vy = vy;
    a->x += vx << 8;
    a->y += vy << 8;
}

/* TMC's GravityUpdate, with z positive up: 0.125 px/frame^2. */
void actor_gravity(Actor* a) {
    if (a->z <= 0 && a->zvel <= 0) {
        a->z = 0;
        a->zvel = 0;
        return;
    }
    a->z += a->zvel;
    a->zvel -= Q16(0.125);
    if (a->z <= 0) {
        a->z = 0;
        a->zvel = 0;
    }
}

static void actor_box(const Actor* a, int* x0, int* y0, int* x1, int* y1) {
    const Hitbox* hb = &gHitboxes[a->hitbox];
    int cx = PX(a->x) + hb->ox, cy = PX(a->y) + hb->oy;
    *x0 = cx - hb->hw;
    *x1 = cx + hb->hw - 1;
    *y0 = cy - hb->hh;
    *y1 = cy + hb->hh - 1;
}

bool8 actors_overlap(const Actor* a, const Actor* b) {
    int ax0, ay0, ax1, ay1, bx0, by0, bx1, by1;
    actor_box(a, &ax0, &ay0, &ax1, &ay1);
    actor_box(b, &bx0, &by0, &bx1, &by1);
    if (ax1 < bx0 || bx1 < ax0 || ay1 < by0 || by1 < ay0)
        return FALSE;
    /* z: within 12 px of each other */
    int dz = PX(a->z) - PX(b->z);
    return ABS(dz) < 12;
}

bool8 actor_box_overlap(const Actor* a, int x0, int y0, int x1, int y1) {
    int ax0, ay0, ax1, ay1;
    actor_box(a, &ax0, &ay0, &ax1, &ay1);
    return !(ax1 < x0 || x1 < ax0 || ay1 < y0 || y1 < ay0);
}

/* 32-step direction from a to b (atan2 on an 8-way coarse grid refined). */
int actor_dir_to(const Actor* a, const Actor* b) {
    int dx = PX(b->x) - PX(a->x);
    int dy = PX(b->y) - PX(a->y);
    /* octant by comparing |dx| and |dy| with 2.414 ratios: 32 steps */
    int adx = ABS(dx), ady = ABS(dy);
    int t; /* 0..8 within the quadrant, N=0 ... E=8 */
    if (adx == 0 && ady == 0)
        return DIR_S;
    /* angle from north toward east in the first quadrant, 0..8 */
    if (adx >= ady * 5)
        t = 8;
    else if (adx * 5 <= ady)
        t = 0;
    else if (adx >= ady * 2)
        t = 7;
    else if (adx * 2 <= ady)
        t = 1;
    else if (adx * 3 >= ady * 4)
        t = 6;
    else if (adx * 4 <= ady * 3)
        t = 2;
    else if (adx > ady)
        t = 5;
    else if (adx < ady)
        t = 3;
    else
        t = 4;
    if (dx >= 0 && dy < 0)
        return t;              /* NE quadrant */
    if (dx >= 0 && dy >= 0)
        return 16 - t;         /* SE */
    if (dx < 0 && dy >= 0)
        return 16 + t;         /* SW */
    return (32 - t) & 31;      /* NW */
}

int actor_dist2(const Actor* a, const Actor* b) {
    int dx = PX(b->x) - PX(a->x);
    int dy = PX(b->y) - PX(a->y);
    return dx * dx + dy * dy;
}

/* ------------------------------------------------------------ sprites -- */
static u16 sNextTile;
static u16 sSheetTile[SHEET_COUNT];

/* single frames resident on their own, for a sheet whose frames are
   never on screen together (the folk: one of each kind in a room) */
#define FRAME_CACHE 8
static struct { u8 sheet, frame; u16 tile; } sFrameCache[FRAME_CACHE];
static u8 sFrameCount;

void sprites_reset(void) {
    int i;
    sNextTile = OBJ_TILE_FIRST_FREE;
    for (i = 0; i < SHEET_COUNT; i++)
        sSheetTile[i] = 0xFFFF;
    sFrameCount = 0;
    interactive_room_reset();
    ambient_room_reset();
}

u16 sprite_load_frame(int sheet, int frame) {
    int i;
    const SpriteSheet* sh = &sheets[sheet];
    for (i = 0; i < sFrameCount; i++)
        if (sFrameCache[i].sheet == sheet && sFrameCache[i].frame == frame)
            return sFrameCache[i].tile;
    if (sFrameCount == FRAME_CACHE || sNextTile + sh->frame_tiles > OBJ_TILE_SHEETS_END)
        return 0;
    u16 base = sNextTile;
    sNextTile += (sh->frame_tiles + 1) & ~1;
    dma3_copy32(sh->tiles + frame * sh->frame_tiles * 16, OBJ_TILE(base), sh->frame_tiles * 32);
    sFrameCache[sFrameCount].sheet = sheet;
    sFrameCache[sFrameCount].frame = frame;
    sFrameCache[sFrameCount].tile = base;
    sFrameCount++;
    return base;
}

/* tiles held for a sprite whose frames stream in one at a time (the
   hub's two keepers): nothing is copied */
u16 sprite_alloc(int tiles) {
    if (sNextTile + tiles > OBJ_TILE_SHEETS_END)
        return 0;
    u16 base = sNextTile;
    sNextTile += (tiles + 1) & ~1;
    return base;
}

u16 sprite_load_sheet(int sheet) {
    if (sSheetTile[sheet] != 0xFFFF)
        return sSheetTile[sheet];
    const SpriteSheet* sh = &sheets[sheet];
    if (sNextTile + sh->tile_count > OBJ_TILE_SHEETS_END)
        return 0;
    u16 base = sNextTile;
    sNextTile += (sh->tile_count + 1) & ~1;
    dma3_copy32(sh->tiles, OBJ_TILE(base), sh->tile_count * 32);
    sSheetTile[sheet] = base;
    return base;
}

void actor_set_sheet(Actor* a, int sheet, u16 tile) {
    const SpriteSheet* sh = &sheets[sheet];
    a->sheet = sheet;
    a->tile = tile;
    a->w = sh->w;
    a->h = sh->h;
    a->pal = sh->pal;
}

void draw_sprite(int sx, int sy, int sheet, u16 tile, int frame, int hflip, int prio, int pal) {
    const SpriteSheet* sh = &sheets[sheet];
    if (sx <= -sh->w || sx >= 240 || sy <= -sh->h || sy >= 160)
        return;
    OamEntry* o = oam_alloc();
    if (!o)
        return;
    o->attr0 = ATTR0_Y(sy) | (sh->shape << 14);
    o->attr1 = ATTR1_X(sx) | ATTR1_SIZE(sh->size) | (hflip ? ATTR1_HFLIP : 0);
    o->attr2 = ATTR2_TILE(tile + frame * sh->frame_tiles) | ATTR2_PRIO(prio) | ATTR2_PAL(pal);
}

void actor_draw(Actor* a) {
    if (a->flags & AF_HIDDEN)
        return;
    if (a->iframes && (gFrame & 2))
        return; /* hurt blink */
    int sx = PX(a->x) - a->w / 2 - gCamX;
    int sy = PX(a->y) - a->h - PX(a->z) - gCamY;
    int prio=room_prop_priority(PX(a->x),PX(a->y),PX(a->z),a->w,a->h,a->prio);
    draw_sprite(sx, sy, a->sheet, a->tile, a->frame, a->hflip, prio, a->pal);
}

/* ---------------------------------------------------- vram upload queue -- */
#define VQ_MAX 16
static struct {
    const void* src;
    volatile void* dst;
    u32 bytes;
} sVq[VQ_MAX];
static u8 sVqCount;

void vram_queue(const void* src, volatile void* dst, u32 bytes) {
    if (sVqCount < VQ_MAX) {
        sVq[sVqCount].src = src;
        sVq[sVqCount].dst = dst;
        sVq[sVqCount].bytes = bytes;
        sVqCount++;
    }
}

void vram_flush_queue(void) {
    int i;
    for (i = 0; i < sVqCount; i++)
        dma3_copy32(sVq[i].src, sVq[i].dst, sVq[i].bytes);
    sVqCount = 0;
}
