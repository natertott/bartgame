/* BARTGAME: the loaded room, its BG maps, collision grid and camera. */
#include "gba.h"
#include "video.h"
#include "room.h"

Room gRoom EWRAM_BSS;
s16 gCamX, gCamY;
u8 gAnimTiles; /* off while the title owns the charblock */

#define SB_OVERLAY 24
#define SB_GROUND 28

void tiles_init(void) {
    int i;
    dma3_copy32(tileset_tiles, CHARBLOCK(0), TILESET_TILE_COUNT * 32);
    for (i = 0; i < PAL_BG_COUNT; i++)
        pal_set_bg(i, &pal_bg[i * 16]);
    for (i = 0; i < PAL_OBJ_COUNT; i++)
        pal_set_obj(i, &pal_obj[i * 16]);
    /* text uses palette 15 entries: 1 ink, 2 shadow */
    pal_set_bg(15, &pal_bg[PAL_BG_HUD * 16]);
}

/* Animated metatiles: copy the current frame's four subtiles over the
   base tiles, so every instance in the room animates at once. */
void tiles_animate(void) {
    int i;
    if (!gAnimTiles)
        return;
    for (i = 0; i < TILE_ANIM_COUNT; i++) {
        const TileAnim* ta = &tile_anims[i];
        if (ta->frames == 0)
            continue;
        if ((gFrame % ta->speed) != 0)
            continue;
        int f = (gFrame / ta->speed) % ta->frames;
        /* subtiles are tl, tr, bl, br: consecutive in the tileset for animated metatiles */
        dma3_copy32(ta->data + f * 64, CHARBLOCK(0) + ta->tile * 16, 128);
    }
}

void room_clear(int w, int h, u16 fill) {
    int i;
    gRoom.w = w;
    gRoom.h = h;
    for (i = 0; i < ROOM_MAX_W * ROOM_MAX_H; i++) {
        gRoom.ground[i] = fill;
        gRoom.overlay[i] = MT_NONE;
    }
}

void room_set(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.ground[my * ROOM_MAX_W + mx] = mt;
}

void room_set_overlay(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.overlay[my * ROOM_MAX_W + mx] = mt;
}

u16 room_get(int mx, int my) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return MT_BLACK;
    return gRoom.ground[my * ROOM_MAX_W + mx];
}

u16 room_get_overlay(int mx, int my) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return MT_NONE;
    return gRoom.overlay[my * ROOM_MAX_W + mx];
}

u8 room_type(int mx, int my) {
    u16 mt = room_get(mx, my);
    if (mt == MT_NONE)
        return TT_SOLID;
    return metatile_type[mt];
}

u8 room_type_px(int px, int py) {
    if (px < 0 || py < 0)
        return TT_SOLID;
    return room_type(px >> 4, py >> 4);
}

static void solid_cell_update(int mx, int my) {
    u16 mt = gRoom.ground[my * ROOM_MAX_W + mx];
    u8 mask = (mt == MT_NONE) ? 15 : metatile_coll[mt];
    /* overlay solids (rare) add to the mask */
    u16 ov = gRoom.overlay[my * ROOM_MAX_W + mx];
    if (ov != MT_NONE && metatile_coll[ov] && metatile_type[ov] != TT_FLOOR)
        mask |= metatile_coll[ov];
    u8* s = &gRoom.solid[(my * 2) * 64 + mx * 2];
    s[0] = (mask >> 3) & 1;
    s[1] = (mask >> 2) & 1;
    s[64] = (mask >> 1) & 1;
    s[65] = mask & 1;
}

void room_build_solid(void) {
    int x, y;
    memset(gRoom.solid, 1, sizeof(gRoom.solid));
    for (y = 0; y < gRoom.h; y++)
        for (x = 0; x < gRoom.w; x++)
            solid_cell_update(x, y);
}

static void map_write(int sb_base, int mx, int my, u16 mt) {
    int tx = mx * 2, ty = my * 2;
    int sb = sb_base + ((ty >> 5) << 1) + (tx >> 5);
    vu16* m = SCREENBLOCK(sb) + (ty & 31) * 32 + (tx & 31);
    if (mt == MT_NONE) {
        m[0] = m[1] = m[32] = m[33] = 0;
        return;
    }
    const u16* e = &metatile_map[mt * 4];
    m[0] = e[0];
    m[1] = e[1];
    m[32] = e[2];
    m[33] = e[3];
}

void room_render(void) {
    int x, y;
    /* clear both 64x64 maps */
    dma3_fill32(0, SCREENBLOCK(SB_OVERLAY), 0x2000);
    dma3_fill32(0, SCREENBLOCK(SB_GROUND), 0x2000);
    for (y = 0; y < gRoom.h; y++) {
        for (x = 0; x < gRoom.w; x++) {
            map_write(SB_GROUND, x, y, gRoom.ground[y * ROOM_MAX_W + x]);
            map_write(SB_OVERLAY, x, y, gRoom.overlay[y * ROOM_MAX_W + x]);
        }
    }
    room_build_solid();
}

void room_change(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.ground[my * ROOM_MAX_W + mx] = mt;
    solid_cell_update(mx, my);
    map_write(SB_GROUND, mx, my, mt);
}

void room_change_overlay(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.overlay[my * ROOM_MAX_W + mx] = mt;
    solid_cell_update(mx, my);
    map_write(SB_OVERLAY, mx, my, mt);
}

bool8 room_solid_px(int px, int py) {
    if (px < 0 || py < 0 || px >= gRoom.w * 16 || py >= gRoom.h * 16)
        return TRUE;
    return gRoom.solid[(py >> 3) * 64 + (px >> 3)];
}

/* Any solid 8x8 cell touching the inclusive pixel box? */
bool8 room_box_solid(int x0, int y0, int x1, int y1) {
    int x, y;
    if (x0 < 0 || y0 < 0 || x1 >= gRoom.w * 16 || y1 >= gRoom.h * 16)
        return TRUE;
    for (y = y0 >> 3; y <= (y1 >> 3); y++)
        for (x = x0 >> 3; x <= (x1 >> 3); x++)
            if (gRoom.solid[y * 64 + x])
                return TRUE;
    return FALSE;
}

void room_load_def(const RoomDef* def) {
    int x, y;
    room_clear(def->w, def->h, MT_BLACK);
    for (y = 0; y < def->h; y++) {
        for (x = 0; x < def->w; x++) {
            gRoom.ground[y * ROOM_MAX_W + x] = def->ground[y * def->w + x];
            gRoom.overlay[y * ROOM_MAX_W + x] = def->overlay ? def->overlay[y * def->w + x] : MT_NONE;
        }
    }
    room_render();
}

int room_px_w(void) {
    return gRoom.w * 16;
}
int room_px_h(void) {
    return gRoom.h * 16;
}

/* The camera centers on the target and clamps to the room. */
void camera_update(int tx, int ty, bool8 snap) {
    int cx = tx - 120;
    int cy = ty - 88;
    int maxx = room_px_w() - 240;
    int maxy = room_px_h() - 160;
    if (maxx < 0)
        maxx = 0;
    if (maxy < 0)
        maxy = 0;
    cx = CLAMP(cx, 0, maxx);
    cy = CLAMP(cy, 0, maxy);
    if (snap) {
        gCamX = cx;
        gCamY = cy;
    } else {
        /* ease toward the target, never more than 4 px a frame */
        int dx = cx - gCamX, dy = cy - gCamY;
        gCamX += CLAMP(dx, -4, 4);
        gCamY += CLAMP(dy, -4, 4);
    }
    gBgScroll[1][0] = gBgScroll[2][0] = gCamX;
    gBgScroll[1][1] = gBgScroll[2][1] = gCamY;
}
