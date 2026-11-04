/* Approved compact trees in ordinary generated rooms, profile31 only.
   Every old solid wood cell has a visible tree base. Upper and lower16px
   halves use separate transparent planes, so overlapping rows never erase
   one another's alpha or require composited/repainted source art. */
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT >= 31
#include "forest_trees.h"
#include "room.h"
#include "roomgen.h"
#include "game.h"
#include "world.h"
#include "video.h"
#include "util.h"

ForestTree gForestTrees[FOREST_TREES_MAX] EWRAM_BSS;
u16 gForestTreeStats[FOREST_TREES_STATS] EWRAM_BSS;
u16 gForestTreeRoots[32*32] EWRAM_BSS;
static u16 sUpper[64*64] EWRAM_BSS;
static u16 sLower[64*64] EWRAM_BSS;
static u8 sRoots[32*32] EWRAM_BSS;
static u8 sActive;
static u32 sRoomSeed;
static u8 sRoomCell,sRoomWidth,sRoomHeight;

static bool8 between(u16 mt,u16 first,u16 last) {
    return mt>=first && mt<=last;
}

bool8 forest_trees_wood(u16 mt) {
    return mt!=MT_NONE && forest_v2_canopy_kind[mt]!=0;
}

bool8 forest_trees_legacy(u16 mt) {
    if(mt==MT_NONE)return FALSE;
    return forest_trees_wood(mt) ||
        between(mt,MT_TREE_TOP_NW,MT_TREE_TRUNK_E) ||
        between(mt,MT_TREE2_0,MT_TREE2_5) ||
        between(mt,MT_GTREE_0,MT_GTREE_11) ||
        between(mt,MT_GTREE2_0,MT_GTREE2_11) ||
        between(mt,MT_BTREE_0,MT_BTREE_11) ||
        between(mt,MT_BIRCH_0,MT_BIRCH_5) ||
        between(mt,MT_FIR_0,MT_FIR_5) ||
        between(mt,MT_SICKTREE_0,MT_SICKTREE_5) ||
        mt==MT_DEAD_TREE || mt==MT_FOREST_BLIGHT_DEAD_TREE;
}

void forest_trees_reset(void) {
    sActive=FALSE;
    memset(gForestTreeStats,0,sizeof(gForestTreeStats));
    memset(gForestTreeRoots,0,sizeof(gForestTreeRoots));
}

bool8 forest_trees_active(void) {
    return sActive && gGame.area==AREA_FOREST;
}

static int state_at(u32 h) {
    int v=h%100,stage=gForestTreeStats[9];
    if(stage==0)return v<86 ? 0 : 1;
    if(stage==1)return v<55 ? 0 : v<95 ? 1 : 2;
    if(stage==2)return v<30 ? 0 : v<80 ? 1 : 2;
    return v<18 ? 0 : v<60 ? 1 : 2;
}

static int frame_at(int width,int state,int variety) {
    int f;
    for(f=0;f<FOREST_TREE_FRAME_COUNT;f++)
        if(forest_tree_width[f]==width && forest_tree_state[f]==state &&
           forest_tree_variety[f]==variety)return f;
    return 0;
}

static bool8 incidental(u16 mt) {
    return mt==MT_NONE || mt==MT_SPARKLE || mt==MT_SPARKLE_WHITE || mt==MT_BLIGHT_MIST;
}

static bool8 upper_clear(int x,int y) {
    if(x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return FALSE;
    u16 mt=room_get(x,y),ov=room_get_overlay(x,y);
    /* Tree source replaces old crowns. Other authored objects own their
       pixels. Features and standing approaches remain clear of overhang. */
    if(!incidental(ov) && !forest_trees_legacy(ov))return FALSE;
    if(forest_trees_wood(mt))return TRUE;
    if(room_canopy_scene_reserved(x,y))return FALSE;
    if(forest_trees_legacy(mt))return TRUE;
    return room_canopy_projection_clear(x,y);
}

static void add_tree(int x,int row,int cells,int flags) {
    int n=gForestTreeStats[1],dx,dy;
    if(n>=FOREST_TREES_MAX) {gForestTreeStats[10]++;return;}
    u32 h=hash32(gWorld.seed,(gGame.cell+1)*19381+row*97+x*17+flags*4099);
    int state=state_at(h),frame=frame_at(cells*16,state,(h>>9)&1);
    ForestTree* t=&gForestTrees[n];
    t->x=x*16;t->y=(row-1)*16;t->frame=frame;t->flags=flags;
    t->root_mask[0]=metatile_coll[room_get(x,row)];
    t->root_mask[1]=cells==2 ? metatile_coll[room_get(x+1,row)] : 0;
    for(dx=0;dx<cells;dx++)gForestTreeRoots[row*32+x+dx]=n+1;
    gForestTreeStats[1]++;
    gForestTreeStats[state+4]++;
    gForestTreeStats[cells==2 ? 7 : 8]++;
    /* Non-overlapping pictures within a row; upper and lower halves of
       neighboring rows overlap through hardware alpha on BG1/BG3. */
    for(dx=0;dx<cells;dx++) {
        bool8 top=upper_clear(x+dx,row-1);
        if(!top && row>0)gForestTreeStats[11]++;
        for(dy=0;dy<4;dy++) {
            int sy=(row-1)*2+dy,xx;
            if(sy<0 || sy>=gRoom.h*2 || (dy<2 && !top))continue;
            for(xx=0;xx<2;xx++) {
                int sx=x*2+dx*2+xx;
                int source=dy*(cells*2)+dx*2+xx;
                (dy<2?sUpper:sLower)[sy*64+sx]=forest_tree_entries[frame][source];
            }
        }
    }
}

void forest_trees_plan(void) {
    int x,y;
    /* A menu return redraws the same planted stand. Cutting a bush can
       expose floor, but must not reroll a neighboring tree's form/crown.
       Actual room loads always call tiles_load -> forest_trees_reset. */
    if(forest_trees_active() && sRoomSeed==gWorld.seed && sRoomCell==gGame.cell &&
       sRoomWidth==gRoom.w && sRoomHeight==gRoom.h)return;
    forest_trees_reset();
    if(gGame.area!=AREA_FOREST)return;
    sActive=TRUE;gForestTreeStats[0]=1;
    sRoomSeed=gWorld.seed;sRoomCell=gGame.cell;
    sRoomWidth=gRoom.w;sRoomHeight=gRoom.h;
    gForestTreeStats[9]=gWorld.cells[gGame.cell].stage;
    memset(sUpper,0,sizeof(sUpper));memset(sLower,0,sizeof(sLower));
    memset(sRoots,0,sizeof(sRoots));
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        u16 mt=room_get(x,y);
        if(forest_trees_wood(mt) && metatile_coll[mt]) {
            sRoots[y*32+x]=FOREST_TREE_WOOD;gForestTreeStats[2]++;
        } else if(forest_trees_legacy(mt) && metatile_coll[mt]) {
            sRoots[y*32+x]=FOREST_TREE_AUTHORED;gForestTreeStats[3]++;
        }
    }
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int kind=sRoots[y*32+x],cells=1;
        if(!kind || gForestTreeRoots[y*32+x])continue;
        /* Broad trees repeat often, but single remaining cells always have
           a narrow native drawing. Do not pair distinct physical masks. */
        if(x+1<gRoom.w && sRoots[y*32+x+1]==kind && !gForestTreeRoots[y*32+x+1] &&
           metatile_coll[room_get(x,y)]==metatile_coll[room_get(x+1,y)] &&
           upper_clear(x,y-1)==upper_clear(x+1,y-1) &&
           (kind==FOREST_TREE_AUTHORED || (hash32(gWorld.seed,y*137+x*43+gGame.cell)&3)!=0))
            cells=2;
        add_tree(x,y,cells,kind);
    }
}

static vu16* map_at(int base,int x,int y) {
    return SCREENBLOCK(base+((y>>5)<<1)+(x>>5))+(y&31)*32+(x&31);
}

void forest_trees_apply_cell(int x,int y) {
    int dx,dy;
    if(!forest_trees_active() || x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return;
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++) {
        int sx=x*2+dx,sy=y*2+dy;
        u16 top=sUpper[sy*64+sx];
        *map_at(FOREST_TREES_SB_BASE,sx,sy)=sLower[sy*64+sx];
        if((top&1023) && upper_clear(x,y)) *map_at(24,sx,sy)=top;
    }
    gForestTreeStats[12]++;
}

void forest_trees_render(void) {
    int x,y;
    if(!forest_trees_active())return;
    dma3_fill32(0,SCREENBLOCK(FOREST_TREES_SB_BASE),0x2000);
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++)forest_trees_apply_cell(x,y);
    gForestTreeStats[12]=0;
}

bool8 forest_trees_overlay_cell(int x,int y) {
    if(!forest_trees_active() || x<0 || y<0 || x>=gRoom.w || y>=gRoom.h)return FALSE;
    int dx,dy;
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++) {
        int tx=x*2+dx,ty=y*2+dy;
        u16 entry=sUpper[ty*64+tx];
        if((entry&1023) && entry==*map_at(24,tx,ty))return TRUE;
    }
    return FALSE;
}

static bool8 plane_ink(int x,int y,int base,const u16* picture) {
    if(!forest_trees_active() || x<0 || y<0 || x>=gRoom.w*16 || y>=gRoom.h*16)return FALSE;
    int tx=x/8,ty=y/8;
    u16 expected=picture[ty*64+tx],entry=*map_at(base,tx,ty);
    if(!(expected&1023) || expected!=entry)return FALSE;
    int ix=x&7,iy=y&7;
    if(entry&0x400)ix=7-ix;
    if(entry&0x800)iy=7-iy;
    const vu16* tile=CHARBLOCK(0)+(entry&1023)*16;
    return ((tile[iy*2+ix/4]>>((ix&3)*4))&15)!=0;
}

bool8 forest_trees_overlay_px(int x,int y) {
    return plane_ink(x,y,24,sUpper);
}

bool8 forest_trees_base_px(int x,int y) {
    return plane_ink(x,y,FOREST_TREES_SB_BASE,sLower);
}

bool8 forest_trees_occludes_px(int x,int y,int priority) {
    return forest_trees_overlay_px(x,y) ||
        (priority==3 && forest_trees_base_px(x,y));
}

bool8 forest_trees_occludes_body(int px,int py,int z,int width,int height,int priority) {
    int x,y;
    if(!forest_trees_active())return FALSE;
    int x0=MAX(0,(px-width/2)/8),x1=MIN(gRoom.w*2-1,(px+width/2-1)/8);
    int y0=MAX(0,(py-z-height)/8),y1=MIN(gRoom.h*2-1,(py-z-1)/8);
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
        u16 top=sUpper[y*64+x],base=sLower[y*64+x];
        if(((top&1023) && top==*map_at(24,x,y)) ||
           (priority==3 && (base&1023) && base==*map_at(FOREST_TREES_SB_BASE,x,y)))return TRUE;
    }
    return FALSE;
}

static bool8 lower_box_ink(const ForestTree* t,int x0,int y0,int x1,int y1) {
    int y;
    x0=MAX(0,x0-t->x);x1=MIN(forest_tree_width[t->frame],x1-t->x);
    y0=MAX(16,y0-t->y);y1=MIN(32,y1-t->y);
    if(x0>=x1 || y0>=y1)return FALSE;
    /* Exact authored alpha, one32-bit AND per intersecting native row.
       All lower halves are installed unmodified; no pixel VRAM scan is
       needed in the hot actor sorting path. Span32 avoids a shift by32. */
    u32 span=0xffffffffu>>(32-(x1-x0));
    u32 mask=span<<x0;
    for(y=y0;y<y1;y++)if(forest_tree_opaque_rows[t->frame][y]&mask)return TRUE;
    return FALSE;
}

int forest_trees_priority(int px,int py,int z,int width,int height,int priority) {
    int x,y,front=0,behind=0;
    if(!forest_trees_active() || priority!=2)return priority;
    int x0=px-MIN(width/2,16),x1=px+MIN(width/2,16);
    int y0=py-z-MIN(height,64),y1=py-z;
    int cx0=MAX(0,x0/16),cx1=MIN(gRoom.w-1,x1/16);
    /* The only possible overhang is the upper16 band north of a root.
       Consult these few local owner cells, never every tree in the room. */
    int cy0=MAX(0,(y0-16)/16),cy1=MIN(gRoom.h-1,(y1+16)/16);
    for(y=cy0;y<=cy1;y++) {
      int previous=0;
      for(x=cx0;x<=cx1;x++) {
        int owner=gForestTreeRoots[y*32+x];
        if(!owner || owner==previous)continue;
        previous=owner;
        const ForestTree* t=&gForestTrees[owner-1];
        int w=forest_tree_width[t->frame];
        int left=t->x+forest_tree_anchor_x[t->frame]-w/2;
        if(x1<=left || x0>=left+w || y1<=t->y || y0>=t->y+32)continue;
        if(py>=t->y+forest_tree_anchor_y[t->frame] || z>=16)front=1;
        /* BG1 already covers priority2. Priority3 is needed only where
           actual root-plane ink would cover this body; a transparent tree
           bounding corner must not push Bloom behind unrelated grass. */
        else if(lower_box_ink(t,MAX(x0,left),MAX(y0,t->y+16),
                             MIN(x1,left+w),MIN(y1,t->y+32)))behind=1;
      }
    }
    return behind ? 3 : front ? 1 : priority;
}

u16 forest_trees_video(u16 flags) {
    if((flags&(DCNT_BG1|DCNT_BG2))==(DCNT_BG1|DCNT_BG2)) {
        REG_BG2CNT=(REG_BG2CNT&~3)|BGCNT_PRIO(forest_trees_active()?3:2);
        if(forest_trees_active()) {
            REG_BG3CNT=BGCNT_PRIO(2)|BGCNT_CHARBASE(0)|BGCNT_SCREENBASE(FOREST_TREES_SB_BASE)|BGCNT_SIZE_64x64;
            return flags|DCNT_BG3;
        }
        REG_BG3CNT=BGCNT_PRIO(3)|BGCNT_CHARBASE(3)|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;
        gBgScroll[3][0]=gBgScroll[3][1]=0;
    } else if(flags&DCNT_BG3) {
        int chars=((REG_BG3CNT>>8)&31)==22 ? REG_BG3CNT&(3<<2) : BGCNT_CHARBASE(3);
        REG_BG3CNT=BGCNT_PRIO(3)|chars|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;
        gBgScroll[3][0]=gBgScroll[3][1]=0;
    }
    return flags;
}

void forest_trees_scroll(void) {
    if(forest_trees_active() && (REG_DISPCNT&(DCNT_BG1|DCNT_BG2))==(DCNT_BG1|DCNT_BG2)) {
        gBgScroll[3][0]=gBgScroll[1][0];gBgScroll[3][1]=gBgScroll[1][1];
    }
}
#endif
