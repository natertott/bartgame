/* BARTGAME: the loaded room, its BG maps, collision grid and camera. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "interactive.h"
#include "game.h"
#include "world.h"
#include "roomgen.h"
#include "myst.h"

Room gRoom EWRAM_BSS;
s16 gCamX, gCamY;
u8 gAnimTiles; /* off while the title owns the charblock */

#define SB_OVERLAY 24
#define SB_GROUND 28

/* the area's tileset: loaded whole into charblocks 0 and 1 when the
   area changes, so each area has the full 1024 subtiles to itself, and
   its palettes into the first slots, so each has PAL_AREA_SLOTS of its
   own */
static const Tileset* sTs = &tilesets[TS_SEWER];

void tiles_load(int set) {
    int i;
    sTs = &tilesets[set];
    dma3_copy32(sTs->tiles, CHARBLOCK(0), sTs->tile_count * 32);
    for (i = 0; i < sTs->pal_count; i++)
        pal_set_bg(i, &sTs->pals[i * 16]);
}

void tiles_init(void) {
    int i;
    tiles_load(TS_SEWER);
    for (i = 0; i < PAL_OBJ_COUNT; i++)
        pal_set_obj(i, &pal_obj[i * 16]);
    pal_set_bg(PAL_SLOT_MENU, &pal_bg[PAL_BG_MENU * 16]);
    pal_set_bg(PAL_SLOT_MAP, &pal_bg[PAL_BG_MAP * 16]);
    pal_set_bg(PAL_SLOT_HUD, &pal_bg[PAL_BG_HUD * 16]); /* the hearts, R's hand */
}

/* Animated metatiles: copy the current frame's four subtiles over the
   base tiles, so every instance in the room animates at once. */
void tiles_animate(void) {
    int i;
    if (!gAnimTiles)
        return;
    for (i = 0; i < sTs->anim_count; i++) {
        const TileAnim* ta = &sTs->anims[i];
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
        gRoom.underlay[i] = fill;
    }
}

void room_set(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.ground[my * ROOM_MAX_W + mx] = mt;
    if (mt == MT_NONE || !metatile_prop[mt])
        gRoom.underlay[my * ROOM_MAX_W + mx] = mt;
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
    const u16* e = &sTs->map[mt * 4];
    m[0] = e[0];
    m[1] = e[1];
    m[32] = e[2];
    m[33] = e[3];
}

/* Physical ground props keep their original logical tile and collision.
   Their transparent artwork is displayed over the stored floor using BG1.
   Meaningful existing overlays win (crowns, portals, event furniture); only
   incidental sparkle/mist is suppressed where it would replace the prop. */
static void render_cell(int x, int y) {
    int i=y*ROOM_MAX_W+x;
    u16 ground=gRoom.ground[i],overlay=gRoom.overlay[i],base=gRoom.underlay[i];
    if (interactive_chest_ready() && (interactive_chest_tile(ground) ||
        interactive_chest_overlay(overlay))) {
        /* The larger OBJ chest owns its complete silhouette. Its original
           logical tile and stored substrate still own physics and rewards. */
        u16 floor=base;
        if (floor==MT_NONE || interactive_chest_tile(floor))
            floor=gGame.area==AREA_MYST ? myst_ground(x,y) : MT_MOSS0;
        map_write(SB_GROUND,x,y,floor);
        if (interactive_chest_overlay(overlay) || overlay==ground || overlay==MT_SPARKLE ||
            overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)
            overlay=MT_NONE;
    } else if (interactive_entry_ready() && interactive_mouth_tile(ground)) {
        /* A continuous wall behind the large portal avoids a second tiny
           doorway visible through transparent pixels around the frame. */
        map_write(SB_GROUND,x,y,roomgen_blighted(gGame.cell) ? MT_BLIGHT_WALL : MT_CANOPY_S);
    } else if (ground!=MT_NONE && metatile_prop[ground] && base!=MT_NONE && base!=ground) {
        map_write(SB_GROUND,x,y,base);
        if (overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)
            overlay=ground;
    } else {
        map_write(SB_GROUND,x,y,ground);
    }
    map_write(SB_OVERLAY,x,y,overlay);
}

/* BG1 now carries transparent material as well as the original crowns.
   A grounded sprite is in front of a prop once its feet pass that prop's
   south edge; flat litter is always below sprites. Keep the authored crown
   occlusion while its feet remain beneath an authored overlay. A fringe
   touching the sprite's upper bounding box is not a tree in front of it.
   Explicit UI, flying-effect and background-shadow priorities stay intact. */
int room_prop_priority(int px,int py,int z,int width,int height,int priority) {
    int x,y,front=0,behind=0;
    int half=MIN(width/2,12), top=py-MIN(height,32)-z, bottom=py-z-1;
    int x0=MAX(0,(px-half)/16),x1=MIN(gRoom.w-1,(px+half)/16);
    int y0=MAX(0,top/16),y1=MIN(gRoom.h-1,bottom/16);
    if(priority!=2)return priority;
    if(px>=0 && py>=4 && px<gRoom.w*16 && py<gRoom.h*16) {
        u16 feet=gRoom.overlay[((py-4)/16)*ROOM_MAX_W+px/16];
        if(feet!=MT_NONE && feet!=MT_SPARKLE && feet!=MT_SPARKLE_WHITE && feet!=MT_BLIGHT_MIST &&
           !(interactive_chest_ready() && interactive_chest_overlay(feet)))
            return priority;
    }
    for(y=y0;y<=y1;y++) for(x=x0;x<=x1;x++) {
        int at=y*ROOM_MAX_W+x;
        u16 mt=gRoom.ground[at],ov=gRoom.overlay[at];
        if(ov!=MT_NONE && ov!=MT_SPARKLE && ov!=MT_SPARKLE_WHITE && ov!=MT_BLIGHT_MIST &&
           !(interactive_chest_ready() && interactive_chest_overlay(ov)))
            continue; /* this cell displays the authored crown, not material */
        if(interactive_chest_ready() && interactive_chest_tile(mt))continue;
        if(mt==MT_NONE || !metatile_prop[mt])continue;
        if(metatile_coll[mt]==0 || py>=(y+1)*16 || z>=16)front=1;
        else if(px>=x*16 && px<(x+1)*16)behind=1;
    }
    return front && !behind ? 1 : priority;
}

void room_render(void) {
    int x, y;
    /* clear both 64x64 maps */
    dma3_fill32(0, SCREENBLOCK(SB_OVERLAY), 0x2000);
    dma3_fill32(0, SCREENBLOCK(SB_GROUND), 0x2000);
    for (y = 0; y < gRoom.h; y++) {
        for (x = 0; x < gRoom.w; x++) {
            render_cell(x,y);
        }
    }
    room_build_solid();
}

void room_change(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    {
        int i=my*ROOM_MAX_W+mx;
        u16 old=gRoom.ground[i],base=gRoom.underlay[i];
        /* Lifting/cutting a prop exposes the exact substrate it covered,
           including rot, shore or trail, rather than the caller's generic
           grass fallback. Chests and lit censers remain material props. */
        if(old!=MT_NONE && metatile_prop[old] && mt!=MT_NONE && !metatile_prop[mt] &&
           metatile_type[mt]==TT_FLOOR && base!=MT_NONE)
            mt=base;
        gRoom.ground[i]=mt;
        if(mt==MT_NONE || !metatile_prop[mt])gRoom.underlay[i]=mt;
    }
    solid_cell_update(mx, my);
    interactive_cell_changed(mx,my);
    render_cell(mx,my);
}

void room_change_overlay(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.overlay[my * ROOM_MAX_W + mx] = mt;
    solid_cell_update(mx, my);
    interactive_cell_changed(mx,my);
    render_cell(mx,my);
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
