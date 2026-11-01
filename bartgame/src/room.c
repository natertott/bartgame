/* BARTGAME: the loaded room, its BG maps, collision grid and camera. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "interactive.h"
#include "game.h"
#include "world.h"
#include "roomgen.h"
#include "myst.h"
#include "appearance.h"
#if BART_FOREST_VARIANT >= 19
#include "canopy_scene.h"
#endif

Room gRoom EWRAM_BSS;
s16 gCamX, gCamY;
u8 gAnimTiles; /* off while the title owns the charblock */
#if BART_FOREST_VARIANT >= 6
u16 gRoomVisualGround[ROOM_MAX_W * ROOM_MAX_H] EWRAM_BSS;
u16 gRoomVisualOverlay[ROOM_MAX_W * ROOM_MAX_H] EWRAM_BSS;
#endif

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
#if BART_FOREST_VARIANT >= 19
    canopy_scene_reset();
#endif
}

void tiles_init(void) {
    int i;
    tiles_load(TS_SEWER);
    for (i = 0; i < PAL_OBJ_COUNT; i++)
        pal_set_obj(i, &pal_obj[i * 16]);
    pal_set_bg(PAL_SLOT_MENU, &pal_bg[PAL_BG_MENU * 16]);
    pal_set_bg(PAL_SLOT_MAP, &pal_bg[PAL_BG_MAP * 16]);
    pal_set_bg(PAL_SLOT_HUD, &pal_bg[PAL_BG_HUD * 16]); /* the hearts, R's hand */
    appearance_apply(); /* restore the player's independent frame/color choice */
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
#if BART_FOREST_VARIANT >= 6
    /* Authored glow breathes only in world BG banks. Neither shared OBJ
       material nor the reserved HUD/menu/sparkle palettes are changed. */
    if (gGame.area != AREA_SEWER && gGame.state == GS_PLAY) {
        int set = (int)(sTs - tilesets), phase = (gFrame >> 3) & 3;
        if(set >= 0 && set < TILESET_COUNT)
            for(i=0;i<FOREST_V2_PULSE_COUNT;i++) {
                int slot=forest_v2_pulse_slots[set][i];
                if(slot!=255)pal_set_bg(slot,forest_v2_pulse_colors[i][phase]);
            }
    }
#endif
#if BART_FOREST_VARIANT >= 19
    if(gGame.state==GS_PLAY)canopy_scene_palette_tick();
#endif
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
#if BART_FOREST_VARIANT >= 6
    if(sb_base==SB_GROUND)gRoomVisualGround[my*ROOM_MAX_W+mx]=mt;
    else if(sb_base==SB_OVERLAY)gRoomVisualOverlay[my*ROOM_MAX_W+mx]=mt;
#endif
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
static bool8 barrier_material(u16 mt) {
    return mt == MT_CRACK || mt == MT_WEB;
}

static u16 barrier_floor(int x,int y,u16 base) {
    static const s8 d[4][2]={{0,1},{0,-1},{1,0},{-1,0}};
    int k;
    if (base!=MT_NONE && metatile_type[base]==TT_FLOOR && !metatile_prop[base])
        return base;
    /* Continue the adjacent lane beneath transparent silk; a wall's stored
       substrate is not the floor of the pocket cut through that wall. */
    for(k=0;k<4;k++) {
        int nx=x+d[k][0],ny=y+d[k][1];
        if(nx<0 || ny<0 || nx>=gRoom.w || ny>=gRoom.h)continue;
        u16 mt=room_get(nx,ny);
        if(mt!=MT_NONE && metatile_type[mt]==TT_FLOOR && !metatile_prop[mt])
            return mt;
    }
    if(gGame.area==AREA_MYST)return myst_ground(x,y);
    return roomgen_blighted(gGame.cell) ? MT_BLIGHT_FLOOR : MT_PATH;
}

#if BART_FOREST_VARIANT >= 6
static int forest_canopy_at(int x,int y) {
    if(x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return 1;
    u16 mt=room_get(x,y);
    return mt==MT_NONE ? 0 : forest_v2_canopy_kind[mt];
}

static bool8 forest_water_at(int x,int y) {
    if(x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return FALSE;
    u16 mt=room_get(x,y);
    return mt!=MT_NONE && forest_v2_water_kind[mt];
}

static bool8 forest_isolated_water(int x,int y,u16 mt) {
    int kind=mt==MT_NONE?0:forest_v2_water_kind[mt];
    return gGame.area==AREA_FOREST && kind>=1 && kind<=3 &&
           !forest_water_at(x,y-1) && !forest_water_at(x+1,y) &&
           !forest_water_at(x,y+1) && !forest_water_at(x-1,y);
}

static u16 forest_picture(int x,int y,u16 mt) {
    if(gGame.area!=AREA_FOREST || mt==MT_NONE)return mt;
    int kind=forest_v2_canopy_kind[mt];
#if BART_FOREST_VARIANT >= 19
    /* Legacy connector IDs now join the room-shaped stand. They need the
       same organic contact silhouette as the surrounding mass, not a
       separate opaque quiet rectangle beneath the native drawing. */
    if(kind==3)kind=2;
#endif
    if(kind==1 || kind==2) {
        int n=forest_canopy_at(x,y-1),e=forest_canopy_at(x+1,y);
        int s=forest_canopy_at(x,y+1),w=forest_canopy_at(x-1,y);
        int mask=(!n?1:0)|(!e?2:0)|(!s?4:0)|(!w?8:0);
        int corners=(!n||!w||forest_canopy_at(x-1,y-1)?0:1)|
                    (!n||!e||forest_canopy_at(x+1,y-1)?0:2)|
                    (!s||!e||forest_canopy_at(x+1,y+1)?0:4)|
                    (!s||!w||forest_canopy_at(x-1,y+1)?0:8);
        return forest_v2_canopy_alias[kind-1][(x&1)|((y&1)<<1)][mask][corners];
    }
    kind=forest_v2_water_kind[mt];
    if(kind>=1 && kind<=3) {
        int n=forest_water_at(x,y-1),e=forest_water_at(x+1,y);
        int s=forest_water_at(x,y+1),w=forest_water_at(x-1,y);
        int mask=(!n?1:0)|(!e?2:0)|(!s?4:0)|(!w?8:0);
        int corners=(!n||!w||forest_water_at(x-1,y-1)?0:1)|
                    (!n||!e||forest_water_at(x+1,y-1)?0:2)|
                    (!s||!e||forest_water_at(x+1,y+1)?0:4)|
                    (!s||!w||forest_water_at(x-1,y+1)?0:8);
        if(kind==1)return forest_v2_water_alias[mask][corners];
        if(mask==15)return forest_v2_water_isolated[kind-2];
    }
    return mt;
}

/* Do not cover rewards, switches, speakers, thresholds or their approaches. */
static bool8 forest_projection_clear(int x,int y,u16 ground,u16 overlay) {
    if(gGame.area!=AREA_FOREST || ground==MT_NONE || metatile_type[ground]!=TT_FLOOR ||
       metatile_prop[ground] || (overlay!=MT_NONE && overlay!=MT_SPARKLE &&
       overlay!=MT_SPARKLE_WHITE && overlay!=MT_BLIGHT_MIST))return FALSE;
    if((gSpots.has_chest && ABS(x-gSpots.chest.x)<=1 && ABS(y-gSpots.chest.y)<=1) ||
       (gSpots.has_npc && ABS(x-gSpots.npc.x)<=1 && ABS(y-gSpots.npc.y)<=1) ||
       (gSpots.has_relic && ABS(x-gSpots.relic.x)<=1 && ABS(y-gSpots.relic.y)<=1) ||
       (gSpots.has_treasure && ABS(x-gSpots.treasure.x)<=1 && ABS(y-gSpots.treasure.y)<=1) ||
       (gSpots.has_mouth && ABS(x-gSpots.mouth.x)<=1 && ABS(y-gSpots.mouth.y)<=2) ||
       (gSpots.has_shrine && ABS(x-gSpots.shrine.x)<=1 && ABS(y-gSpots.shrine.y)<=2))
        return FALSE;
    return TRUE;
}

static u16 forest_projection(int x,int y,u16 ground,u16 overlay) {
    if(!forest_projection_clear(x,y,ground,overlay))return overlay;
    int n=forest_canopy_at(x,y-1),e=forest_canopy_at(x+1,y);
    int s=forest_canopy_at(x,y+1),w=forest_canopy_at(x-1,y);
    int mask=(n?1:0)|(e?2:0)|(s?4:0)|(w?8:0);
    if(!mask)return overlay;
    int kind=(n>=2 || e>=2 || s>=2 || w>=2)?1:0;
    return forest_v2_fringe_alias[kind][mask];
}
#endif

#if BART_FOREST_VARIANT >= 19
const u16* room_canopy_scene_entries(u16 mt) {
    return &sTs->map[mt*4];
}

bool8 room_canopy_scene_reserved(int x,int y) {
    int k;
    /* A large entry OBJ owns its frame, dark opening and the approach.
       A canopy component may wrap behind it, but never replace it. */
    if((gSpots.has_mouth && ABS(x-gSpots.mouth.x)<=1 &&
        y>=gSpots.mouth.y-2 && y<=gSpots.mouth.y+1) ||
       (gSpots.has_shrine && ABS(x-gSpots.shrine.x)<=1 && ABS(y-gSpots.shrine.y)<=2) ||
       (gSpots.has_chest && ABS(x-gSpots.chest.x)<=1 && ABS(y-gSpots.chest.y)<=1) ||
       (gSpots.has_npc && ABS(x-gSpots.npc.x)<=1 && ABS(y-gSpots.npc.y)<=1) ||
       (gSpots.has_relic && ABS(x-gSpots.relic.x)<=1 && ABS(y-gSpots.relic.y)<=1) ||
       (gSpots.has_treasure && ABS(x-gSpots.treasure.x)<=1 && ABS(y-gSpots.treasure.y)<=1))
        return TRUE;
    for(k=0;k<gSpots.torch_count;k++)
        if(ABS(x-gSpots.torches[k].x)<=1 && y>=gSpots.torches[k].y-1 &&
           y<=gSpots.torches[k].y+1)return TRUE;
    return FALSE;
}

bool8 room_canopy_projection_clear(int x,int y) {
    if(x<0 || y<0 || x>=gRoom.w || y>=gRoom.h || room_canopy_scene_reserved(x,y))
        return FALSE;
    return forest_projection_clear(x,y,room_get(x,y),room_get_overlay(x,y));
}
#endif

static void render_cell(int x, int y) {
    int i=y*ROOM_MAX_W+x;
    u16 ground=gRoom.ground[i],overlay=gRoom.overlay[i],base=gRoom.underlay[i];
#if BART_FOREST_VARIANT >= 6
    u16 picture=ground;
    if(forest_isolated_water(x,y,ground)) {
        if(overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST) {
            /* Exterior alpha reveals this soil, not a healthy-green square
               baked into a pond on dirt or diseased grass. */
            map_write(SB_GROUND,x,y,barrier_floor(x,y,base));
            overlay=forest_picture(x,y,ground);
        } else {
            /* The two world planes are already occupied. Preserve an
               authored crown/event and a visible water surface beneath it,
               never an alpha hole to the backdrop. */
            map_write(SB_GROUND,x,y,MT_WATER);
        }
    } else if(gGame.area==AREA_FOREST && ground!=MT_NONE &&
       (forest_v2_canopy_kind[ground]==1 || forest_v2_canopy_kind[ground]==2
#if BART_FOREST_VARIANT >= 19
        || forest_v2_canopy_kind[ground]==3
#endif
       ) &&
       (overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)) {
        /* Rounded foliage is a true foreground silhouette over local soil,
           not a green rectangle painted onto a dirt or water boundary. */
        map_write(SB_GROUND,x,y,barrier_floor(x,y,base));
        overlay=forest_picture(x,y,ground);
    } else if(interactive_landmark_tile(x,y)) {
        picture=barrier_floor(x,y,base);
        if(overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE)overlay=MT_NONE;
        map_write(SB_GROUND,x,y,picture);
    } else if(gGame.area==AREA_FOREST && ground!=MT_NONE && forest_v2_special_tree[ground] &&
              (overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)) {
        map_write(SB_GROUND,x,y,barrier_floor(x,y,base));
        overlay=ground;
    } else
#endif
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
    } else if (barrier_material(ground)
#if BART_FOREST_VARIANT >= 6
               || ground==MT_THORN || ground==MT_DOOR_LOCKED
#endif
               ) {
        /* The obstacle must cover the hoard beyond it, while its transparent
           corners and silk reveal a continuous local floor. Physics still
           reads the original CRACK/WEB tile and unchanged collision mask. */
        map_write(SB_GROUND,x,y,barrier_floor(x,y,base));
        if(overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)
            overlay=ground;
    } else if (ground!=MT_NONE && metatile_prop[ground] && base!=MT_NONE && base!=ground) {
        map_write(SB_GROUND,x,y,base);
        if (overlay==MT_NONE || overlay==MT_SPARKLE || overlay==MT_SPARKLE_WHITE || overlay==MT_BLIGHT_MIST)
            overlay=ground;
    } else {
#if BART_FOREST_VARIANT >= 6
        picture=forest_picture(x,y,ground);
        map_write(SB_GROUND,x,y,picture);
#else
        map_write(SB_GROUND,x,y,ground);
#endif
    }
#if BART_FOREST_VARIANT >= 6 && BART_FOREST_VARIANT < 19
    overlay=forest_projection(x,y,ground,overlay);
#endif
    map_write(SB_OVERLAY,x,y,overlay);
}

#if BART_FOREST_VARIANT >= 6
u16 room_visual_ground(int x,int y) {return gRoomVisualGround[y*ROOM_MAX_W+x];}
u16 room_visual_overlay(int x,int y) {return gRoomVisualOverlay[y*ROOM_MAX_W+x];}
bool8 room_recoil_fringe_front(int px,int py) {
    if(gGame.area!=AREA_FOREST || px<0 || py<1 || px>=gRoom.w*16 || py>=gRoom.h*16)return FALSE;
    int at=((py-1)/16)*ROOM_MAX_W+px/16;
    u16 ground=gRoom.ground[at],overlay=gRoomVisualOverlay[at];
    return ground!=MT_NONE && metatile_type[ground]==TT_FLOOR &&
           metatile_coll[ground]==0 && overlay!=MT_NONE && forest_v2_low_fringe[overlay];
}
static bool8 overhead_at_body(int px,int py,int z,int width,int height) {
    int x,y,x0=MAX(0,(px-width/2)/16),x1=MIN(gRoom.w-1,(px+width/2)/16);
    int y0=MAX(0,(py-z-height)/16),y1=MIN(gRoom.h-1,(py-z-1)/16);
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
        u16 mt=gRoomVisualOverlay[y*ROOM_MAX_W+x];
        if(mt!=MT_NONE && forest_v2_overhead[mt])return TRUE;
    }
    return FALSE;
}

static bool8 water_surface_at_body(int px,int py,int z,int width,int height) {
    int x,y,x0=MAX(0,(px-width/2)/16),x1=MIN(gRoom.w-1,(px+width/2)/16);
    int y0=MAX(0,(py-z-height)/16),y1=MIN(gRoom.h-1,(py-z-1)/16);
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
        u16 mt=gRoomVisualOverlay[y*ROOM_MAX_W+x];
        if(mt!=MT_NONE && metatile_type[mt]==TT_WATER)return TRUE;
    }
    return FALSE;
}
#endif

#if BART_FOREST_VARIANT >= 11
static bool8 canopy_overlay_cell(int x,int y) {
    if(gGame.area!=AREA_FOREST || x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return FALSE;
    u16 mt=gRoomVisualOverlay[y*ROOM_MAX_W+x];
    /* A timber roof is an underpass, not the foliage-visibility exception. */
    if(mt==MT_NONE || mt==MT_F2_ARCH_0 || mt==MT_F2_ARCH_1)return FALSE;
    return forest_v2_overhead[mt] || forest_v2_special_tree[mt] || forest_v2_canopy_kind[mt];
}

bool8 room_canopy_overlay_px(int px,int py) {
    if(px<0 || py<0 || !canopy_overlay_cell(px/16,py/16))return FALSE;
    int tx=px/8,ty=py/8;
    int sb=SB_OVERLAY+((ty>>5)<<1)+(tx>>5);
    u16 entry=SCREENBLOCK(sb)[(ty&31)*32+(tx&31)];
    int x=px&7,y=py&7;
    if(entry&0x400)x=7-x;
    if(entry&0x800)y=7-y;
    const vu16* tile=CHARBLOCK(0)+(entry&1023)*16;
    return ((tile[y*2+x/4]>>((x&3)*4))&15)!=0;
}

bool8 room_canopy_overlaps_body(int px,int py,int z,int width,int height) {
    int x,y,x0=MAX(0,(px-width/2)/16),x1=MIN(gRoom.w-1,(px+width/2-1)/16);
    int y0=MAX(0,(py-z-height)/16),y1=MIN(gRoom.h-1,(py-z-1)/16);
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)
        if(canopy_overlay_cell(x,y))return TRUE;
    return FALSE;
}
#endif

/* BG1 now carries transparent material as well as the original crowns.
   A grounded sprite is in front of a prop once its feet pass that prop's
   south edge; flat litter is always below sprites. Keep the authored crown
   occlusion while its feet remain beneath an authored overlay. A fringe
   touching the sprite's upper bounding box is not a tree in front of it.
   Explicit UI, flying-effect and background-shadow priorities stay intact. */
static bool8 floor_mark(u16 mt) {
    return mt==MT_MYST_SWITCH || mt==MT_MYST_SWITCH_DOWN;
}

int room_prop_priority(int px,int py,int z,int width,int height,int priority) {
    int x,y,front=0,behind=0;
    int half=MIN(width/2,16), top=py-MIN(height,64)-z, bottom=py-z-1;
    int x0=MAX(0,(px-half)/16),x1=MIN(gRoom.w-1,(px+half)/16);
    int y0=MAX(0,top/16),y1=MIN(gRoom.h-1,bottom/16);
#if BART_FOREST_VARIANT >= 6
    if((priority==1 || priority==2) && overhead_at_body(px,py,z,width,height))return 2;
#endif
    if(priority!=2)return priority;
    if(px>=0 && py>=4 && px<gRoom.w*16 && py<gRoom.h*16) {
        u16 feet=gRoom.overlay[((py-4)/16)*ROOM_MAX_W+px/16];
        if(feet!=MT_NONE && feet!=MT_SPARKLE && feet!=MT_SPARKLE_WHITE && feet!=MT_BLIGHT_MIST && !floor_mark(feet) &&
           !(interactive_chest_ready() && interactive_chest_overlay(feet)))
            return priority;
    }
    for(y=y0;y<=y1;y++) for(x=x0;x<=x1;x++) {
        int at=y*ROOM_MAX_W+x;
        u16 mt=gRoom.ground[at],ov=gRoom.overlay[at];
        if(floor_mark(ov)) {
            front=1; /* A plate belongs beneath feet, not above the body. */
            continue;
        }
        if(ov!=MT_NONE && ov!=MT_SPARKLE && ov!=MT_SPARKLE_WHITE && ov!=MT_BLIGHT_MIST &&
           !(interactive_chest_ready() && interactive_chest_overlay(ov)))
            continue; /* this cell displays the authored crown, not material */
        if(interactive_chest_ready() && interactive_chest_tile(mt))continue;
        if(mt==MT_NONE || (!metatile_prop[mt] && !barrier_material(mt)
#if BART_FOREST_VARIANT >= 6
                          && !forest_v2_special_tree[mt]
#endif
                          ))continue;
        if(metatile_coll[mt]==0 || py>=(y+1)*16 || z>=16)front=1;
        else if(px>=x*16 && px<(x+1)*16)behind=1;
    }
#if BART_FOREST_VARIANT >= 6
    /* The water surface is below bodies, unlike a canopy. Also test dry
       actors whose heads overlap a neighboring pond, not only feet in it. */
    if(!behind && water_surface_at_body(px,py,z,width,height))return 1;
#endif
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
#if BART_FOREST_VARIANT >= 19
    canopy_scene_build();
#endif
}

void room_change(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    {
        int i=my*ROOM_MAX_W+mx;
        u16 old=gRoom.ground[i],base=gRoom.underlay[i];
#if BART_FOREST_VARIANT >= 6
        if((old==MT_THORN || old==MT_CRACK || old==MT_WEB || old==MT_DOOR_LOCKED) &&
           mt!=MT_NONE && (metatile_type[mt]==TT_FLOOR || metatile_type[mt]==TT_DOOR_OPEN))
            mt=barrier_floor(mx,my,base);
#endif
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
#if BART_FOREST_VARIANT >= 6
    int nx,ny;
    for(ny=MAX(0,my-1);ny<=MIN(gRoom.h-1,my+1);ny++)
        for(nx=MAX(0,mx-1);nx<=MIN(gRoom.w-1,mx+1);nx++)
            if(nx!=mx || ny!=my)render_cell(nx,ny);
#endif
#if BART_FOREST_VARIANT >= 19
    for(ny=MAX(0,my-1);ny<=MIN(gRoom.h-1,my+1);ny++)
        for(nx=MAX(0,mx-1);nx<=MIN(gRoom.w-1,mx+1);nx++)
            canopy_scene_apply_cell(nx,ny);
#endif
}

void room_change_overlay(int mx, int my, u16 mt) {
    if (mx < 0 || my < 0 || mx >= gRoom.w || my >= gRoom.h)
        return;
    gRoom.overlay[my * ROOM_MAX_W + mx] = mt;
    solid_cell_update(mx, my);
    interactive_cell_changed(mx,my);
    render_cell(mx,my);
#if BART_FOREST_VARIANT >= 19
    canopy_scene_apply_cell(mx,my);
#endif
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
