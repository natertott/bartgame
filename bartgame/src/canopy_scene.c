/* Room-shaped canopy composition. Hardware 8px cells store the drawing;
   they are never the unit at which trees are designed or selected. */
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT >= 19
#include "canopy_scene.h"
#include "room.h"
#include "game.h"
#include "world.h"
#include "util.h"
#include "video.h"

#define STRIDE 32
#define MAP_STRIDE 64
#define SB_CANOPY 24
#define SB_FLOOR 28

u8 gAdaptiveCanopyMask[32*32] EWRAM_BSS;
u16 gAdaptiveCanopyComponent[32*32] EWRAM_BSS;
CanopyComponent gAdaptiveCanopyComponents[CANOPY_SCENE_MAX_COMPONENTS] EWRAM_BSS;
CanopyPlacement gAdaptiveCanopyPlacements[CANOPY_SCENE_MAX_PLACEMENTS] EWRAM_BSS;
u16 gAdaptiveCanopyStats[16] EWRAM_BSS;
static u16 sPicture[64*64] EWRAM_BSS;
static u16 sQueue[32*32] EWRAM_BSS;
/* Small hot lookup masks belong in IWRAM; the large resident scene does not. */
static u32 sAvailableRows[32];
static u32 sOpenRows[32];
static u32 sOpenColumns[32];
static u8 sPlanned[32*32] EWRAM_BSS;
static u8 sActive,sPaletteStage,sPalettePhase;
static u8 sRoomCell,sRoomWidth,sRoomHeight;
static u32 sRoomSeed;
/* Native drawings span at most six cells horizontally and four vertically. */
static const u8 sBitCount[64] __attribute__((section(".iwram.rodata")))={
    0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
};

/* The shared hash32 expression, inlined into the IWRAM fit search. This
   changes neither the generator stream nor placement jitter/tie order. */
static inline u32 score_hash(u32 a,u32 b) {
    u32 h=a*0x9E3779B1u^(b+0x7F4A7C15u);
    h^=h>>15;h*=0x85EBCA77u;h^=h>>13;h*=0xC2B2AE3Du;h^=h>>16;
    return h;
}

static vu16* map_at(int base,int x8,int y8) {
    int sb=base+((y8>>5)<<1)+(x8>>5);
    return SCREENBLOCK(sb)+(y8&31)*32+(x8&31);
}

static bool8 inside(int x,int y) {
    return x>=0 && y>=0 && x<gRoom.w && y<gRoom.h;
}

static bool8 eligible(int x,int y) {
    if(!inside(x,y))return FALSE;
    int at=y*STRIDE+x;
    u16 mt=gRoom.ground[at],ov=gRoom.overlay[at];
    if(mt==MT_NONE || !forest_v2_canopy_kind[mt])return FALSE;
    if(ov!=MT_NONE && ov!=MT_SPARKLE && ov!=MT_SPARKLE_WHITE && ov!=MT_BLIGHT_MIST)
        return FALSE;
    return room_canopy_scene_reserved(x,y)==FALSE;
}

static bool8 open_floor(int x,int y) {
    if(!inside(x,y))return FALSE;
    u16 mt=room_get(x,y);
    if(mt==MT_NONE)return FALSE;
    int type=metatile_type[mt];
    return (type==TT_FLOOR || type==TT_SLOW || type==TT_DOOR_OPEN || type==TT_STAIRS) &&
           !metatile_prop[mt] && metatile_coll[mt]==0;
}

void canopy_scene_reset(void) {
    sActive=FALSE;sPaletteStage=sPalettePhase=255;
    memset(gAdaptiveCanopyMask,0,sizeof(gAdaptiveCanopyMask));
    memset(gAdaptiveCanopyComponent,0,sizeof(gAdaptiveCanopyComponent));
    memset(gAdaptiveCanopyStats,0,sizeof(gAdaptiveCanopyStats));
}

static bool8 fits(int x,int y,int w,int h) {
    if(x<0 || y<0 || x+w>gRoom.w || y+h>gRoom.h)return FALSE;
    u32 span=((1u<<w)-1u)<<x;
    int row;
    /* One bit per logical cell. Clearing a chosen footprint costs at most
       four row writes; it never rebuilds a room-sized prefix table. */
    for(row=y;row<y+h;row++)
        if((sAvailableRows[row]&span)!=span)return FALSE;
    return TRUE;
}

static int edge_score(int x,int y,int w,int h,int role) {
    u32 wm=(1u<<w)-1u,hm=(1u<<h)-1u;
    int south=y+h<gRoom.h?sBitCount[(sOpenRows[y+h]>>x)&wm]:0;
    int north=y>0?sBitCount[(sOpenRows[y-1]>>x)&wm]:0;
    int side=x>0?sBitCount[(sOpenColumns[x-1]>>y)&hm]:0;
    if(x+w<gRoom.w)side+=sBitCount[(sOpenColumns[x+w]>>y)&hm];
    /* Native trunks face down-screen. Expose that face to the clearing
       whenever possible instead of hiding the only tree at row zero. */
    int score=south*120+north*18+side*32;
    score-=ABS((x*2+w)-gRoom.w)*2+ABS((y+h)-gRoom.h/2);
    score+=(score_hash(gWorld.seed,(gGame.cell+1)*127+x*23+y*71+role*311)&31);
    return score;
}

static bool8 IWRAM_CODE best_position(int component,int role,int* bx,int* by) {
    const CanopyPrefab* p=&canopy_prefabs[role];
    int x,y,best=-32767;
    int x0=0,y0=0,x1=gRoom.w-p->w,y1=gRoom.h-p->h;
    if(component<=CANOPY_SCENE_MAX_COMPONENTS) {
        const CanopyComponent* c=&gAdaptiveCanopyComponents[component-1];
        x0=c->x0;y0=c->y0;
        x1=MIN(x1,c->x1+1-p->w);y1=MIN(y1,c->y1+1-p->h);
    }
    *bx=*by=-1;
    /* Restrict the search without changing ascending candidate/tie order. */
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
        if(gAdaptiveCanopyComponent[y*STRIDE+x]!=component || !fits(x,y,p->w,p->h))continue;
        int score=edge_score(x,y,p->w,p->h,role);
        if(score>best){best=score;*bx=x;*by=y;}
    }
    return *bx>=0;
}

static bool8 record_piece(int component,int role,int x,int y,int flags) {
    if(gAdaptiveCanopyStats[3]>=CANOPY_SCENE_MAX_PLACEMENTS) {
        gAdaptiveCanopyStats[10]|=2;return FALSE;
    }
    const CanopyPrefab* p=&canopy_prefabs[role];
    int n=gAdaptiveCanopyStats[3]++,dx,dy;
    CanopyPlacement* out=&gAdaptiveCanopyPlacements[n];
    out->component=component;out->role=role;out->x=x;out->y=y;
    out->w=p->w;out->h=p->h;out->flags=flags;
    u32 span=((1u<<p->w)-1u)<<x;
    for(dy=0;dy<p->h;dy++)sAvailableRows[y+dy]&=~span;
    for(dy=0;dy<p->h;dy++)for(dx=0;dx<p->w;dx++) {
        int at=(y+dy)*STRIDE+x+dx;
        if(flags&CANOPY_SCENE_OVERHANG)sPlanned[at]=CANOPY_SCENE_OVERHANG;
        else gAdaptiveCanopyStats[5]++;
    }
    if(component && component<=CANOPY_SCENE_MAX_COMPONENTS) {
        gAdaptiveCanopyComponents[component-1].placements++;
        gAdaptiveCanopyComponents[component-1].painted+=p->w*p->h;
    }
    const u16* picture=(role==CANOPY_ROLE_BRANCH && !(flags&CANOPY_SCENE_OVERHANG))?
        canopy_solid_branch:p->map;
    for(dy=0;dy<p->h*2;dy++)for(dx=0;dx<p->w*2;dx++) {
        u16 entry=picture[dy*p->w*2+dx];
#if BART_FOREST_VARIANT >= 29
        /* Leaf-crown art owns its complete native alpha silhouette. A blank
           8px piece is a real gap to the local ground, not permission to
           keep an opaque infill panel behind the authored crown. */
        sPicture[(y*2+dy)*MAP_STRIDE+x*2+dx]=entry;
#else
        /* A completely blank source subtile adds no rectangle over the
           quiet organic backing. Partial native alpha stays untouched. */
        if((entry&1023)!=0)
            sPicture[(y*2+dy)*MAP_STRIDE+x*2+dx]=entry;
#endif
    }
    gAdaptiveCanopyStats[7]=MAX(gAdaptiveCanopyStats[7],p->w*16);
    gAdaptiveCanopyStats[8]=MAX(gAdaptiveCanopyStats[8],p->h*16);
    return TRUE;
}

static void compose_component(int id,int area) {
    static const u8 support[]={CANOPY_ROLE_GROVE,CANOPY_ROLE_BORDER,
        CANOPY_ROLE_TREE,CANOPY_ROLE_COLUMN,CANOPY_ROLE_BRANCH,CANOPY_ROLE_CLUMP,
        CANOPY_ROLE_ROOTS,CANOPY_ROLE_SMALL};
    int x,y,pass,placed=0,covered=0;
    if(best_position(id,CANOPY_ROLE_HERO,&x,&y) && record_piece(id,CANOPY_ROLE_HERO,x,y,0)) {
        const CanopyPrefab* p=&canopy_prefabs[CANOPY_ROLE_HERO];
        covered=p->w*p->h;placed++;
    }
    /* A shallow disconnected mass calls for a long limb, not a procession
       of 16px icons or the roots of a tree whose crown does not fit. */
    if(id<=CANOPY_SCENE_MAX_COMPONENTS &&
       gAdaptiveCanopyComponents[id-1].y0==gAdaptiveCanopyComponents[id-1].y1) {
        const CanopyPrefab* p=&canopy_prefabs[CANOPY_ROLE_BRANCH];
        while(best_position(id,CANOPY_ROLE_BRANCH,&x,&y) &&
              record_piece(id,CANOPY_ROLE_BRANCH,x,y,0)) {
            covered+=p->w*p->h;
        }
    }
    /* Unequal anatomical groups fill useful inner edges. A large connected
       border is not reduced to one distant hero followed by tiny stamps. */
    for(pass=0;pass<4 && covered*100<area*88;pass++) {
        int k;
        for(k=0;k<ARRAY_COUNT(support);k++) {
            int role=support[k];
            /* Use small remnants only after native larger drawings have
               exhausted the actual remaining rectangles. */
            if(role==CANOPY_ROLE_SMALL && area>1 && pass<2)continue;
            if(best_position(id,role,&x,&y) && record_piece(id,role,x,y,0)) {
                const CanopyPrefab* p=&canopy_prefabs[role];
                covered+=p->w*p->h;placed++;
            }
            if(gAdaptiveCanopyStats[3]>=CANOPY_SCENE_MAX_PLACEMENTS)return;
        }
    }
    (void)placed;
}

static void add_projection(void) {
    const CanopyPrefab* p=&canopy_prefabs[CANOPY_ROLE_BRANCH];
    int x,y,added=0;
    /* A few broad boughs are attached to a continuous forest edge. They
       are not independent items dropped into random grass. */
    for(y=1;y+p->h<=gRoom.h && added<4;y++)for(x=0;x+p->w<=gRoom.w && added<4;x++) {
        int dx,dy,okay=1,attached=0;
        if((hash32(gWorld.seed,gGame.cell*991+x*37+y*151)&7)!=0)continue;
        for(dy=0;dy<p->h && okay;dy++)for(dx=0;dx<p->w;dx++) {
            int at=(y+dy)*STRIDE+x+dx;
            if(sPlanned[at] || !room_canopy_projection_clear(x+dx,y+dy)) {okay=0;break;}
            attached+=(sPlanned[(y-1)*STRIDE+x+dx]&CANOPY_SCENE_SOLID)!=0;
        }
        if(okay && attached>=p->w-1 && record_piece(0,CANOPY_ROLE_BRANCH,x,y,CANOPY_SCENE_OVERHANG)) {
            gAdaptiveCanopyStats[6]+=p->w*p->h;added++;
        }
    }
}

void canopy_scene_build(void) {
    static const s8 step[4][2]={{0,-1},{1,0},{0,1},{-1,0}};
    int x,y,k,total=0;
    /* Returning from a menu redraws the room. Reuse the native scene when
       its actual solid footprint is unchanged; no rectangle search or
       component traversal belongs in the normal gameplay frame loop. */
    if(sActive && gGame.area==AREA_FOREST && sRoomSeed==gWorld.seed &&
       sRoomCell==gGame.cell && sRoomWidth==gRoom.w && sRoomHeight==gRoom.h) {
        bool8 same=TRUE;
        for(y=0;y<gRoom.h && same;y++)for(x=0;x<gRoom.w;x++)
            if(eligible(x,y)!=((sPlanned[y*STRIDE+x]&CANOPY_SCENE_SOLID)!=0)) {
                same=FALSE;break;
            }
        if(same) {
            gAdaptiveCanopyStats[11]++;
            for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++)canopy_scene_apply_cell(x,y);
            sPaletteStage=sPalettePhase=255;
            canopy_scene_palette_tick();
            return;
        }
    }
    canopy_scene_reset();
    if(gGame.area!=AREA_FOREST)return;
    u32 started=gFrame,phase_started;
    sActive=TRUE;gAdaptiveCanopyStats[0]=1;
    sRoomSeed=gWorld.seed;sRoomCell=gGame.cell;sRoomWidth=gRoom.w;sRoomHeight=gRoom.h;
    memset(sPlanned,0,sizeof(sPlanned));
    memset(sAvailableRows,0,sizeof(sAvailableRows));
    memset(sOpenRows,0,sizeof(sOpenRows));
    memset(sOpenColumns,0,sizeof(sOpenColumns));
    for(y=0;y<gRoom.h*2;y++)for(x=0;x<gRoom.w*2;x++)
        sPicture[y*MAP_STRIDE+x]=*map_at(SB_CANOPY,x,y);
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        if(eligible(x,y)) {
            sPlanned[y*STRIDE+x]=CANOPY_SCENE_SOLID;
            sAvailableRows[y]|=1u<<x;total++;
        }
        if(open_floor(x,y)) {sOpenRows[y]|=1u<<x;sOpenColumns[x]|=1u<<y;}
    }
    gAdaptiveCanopyStats[4]=total;
    gAdaptiveCanopyStats[12]=gFrame-started;phase_started=gFrame;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int at=y*STRIDE+x,head=0,tail=0,id,area=0,x0=x,x1=x,y0=y,y1=y;
        if(!sPlanned[at] || gAdaptiveCanopyComponent[at])continue;
        id=++gAdaptiveCanopyStats[1];sQueue[tail++]=at;gAdaptiveCanopyComponent[at]=id;
        while(head<tail) {
            int q=sQueue[head++],cx=q%STRIDE,cy=q/STRIDE;
            area++;x0=MIN(x0,cx);x1=MAX(x1,cx);y0=MIN(y0,cy);y1=MAX(y1,cy);
            for(k=0;k<4;k++) {
                int nx=cx+step[k][0],ny=cy+step[k][1],next=ny*STRIDE+nx;
                if(!inside(nx,ny) || !(sPlanned[next]&CANOPY_SCENE_SOLID) || gAdaptiveCanopyComponent[next])continue;
                gAdaptiveCanopyComponent[next]=id;sQueue[tail++]=next;
            }
        }
        if(id<=CANOPY_SCENE_MAX_COMPONENTS) {
            CanopyComponent* c=&gAdaptiveCanopyComponents[id-1];
            c->id=id;c->area=area;c->x0=x0;c->x1=x1;c->y0=y0;c->y1=y1;c->placements=c->painted=0;
            gAdaptiveCanopyStats[2]++;
        } else gAdaptiveCanopyStats[10]|=1;
        compose_component(id,area);
    }
    gAdaptiveCanopyStats[13]=gFrame-phase_started;phase_started=gFrame;
    add_projection();
    memcpy(gAdaptiveCanopyMask,sPlanned,sizeof(sPlanned));
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++)canopy_scene_apply_cell(x,y);
    canopy_scene_palette_tick();
    gAdaptiveCanopyStats[14]=gFrame-phase_started;
    gAdaptiveCanopyStats[15]=gFrame-started;
}

bool8 canopy_scene_owns(int mx,int my) {
    return sActive && inside(mx,my) && gAdaptiveCanopyMask[my*STRIDE+mx];
}

void canopy_scene_apply_cell(int mx,int my) {
    if(!sActive || !inside(mx,my))return;
    int at=my*STRIDE+mx,flag=sPlanned[at],dx,dy;
    if(!flag)return;
    if((flag&CANOPY_SCENE_OVERHANG) && !room_canopy_projection_clear(mx,my)) {
        gAdaptiveCanopyMask[at]=0;return;
    }
    if((flag&CANOPY_SCENE_SOLID) && !eligible(mx,my)) {
        gAdaptiveCanopyMask[at]=0;return;
    }
    gAdaptiveCanopyMask[at]=flag;
#if BART_FOREST_VARIANT < 29
    /* Only deep interior cells receive an opaque underbrush ground plane.
       Boundary alpha still reveals the actual local soil, not a black box. */
    if((flag&CANOPY_SCENE_SOLID) && mx>0 && my>0 && mx+1<gRoom.w && my+1<gRoom.h &&
       (sPlanned[at-1]&1) && (sPlanned[at+1]&1) &&
       (sPlanned[at-STRIDE]&1) && (sPlanned[at+STRIDE]&1)) {
        const u16* bg=room_canopy_scene_entries(MT_BLIGHT_WALL);
        for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)*map_at(SB_FLOOR,mx*2+dx,my*2+dy)=bg[dy*2+dx];
        gRoomVisualGround[at]=MT_BLIGHT_WALL;
    }
#endif
    /* Profile29 retains render_cell's actual stored/local grass or soil on
       BG2. Dense leaves and their authored undersides define the canopy on
       BG1; alpha is never backed by a forced purple-black ground plane. */
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
        *map_at(SB_CANOPY,mx*2+dx,my*2+dy)=sPicture[(my*2+dy)*MAP_STRIDE+mx*2+dx];
    /* Ownership marker only. Native scene pictures are the resident BG1
       entries above; logical cells/collision never receive this marker. */
    gRoomVisualOverlay[at]=(flag&CANOPY_SCENE_OVERHANG)?
        forest_v2_fringe_alias[1][1]:forest_v2_canopy_alias[1][0][0][0];
}

void canopy_scene_palette_tick(void) {
    if(!sActive || gGame.area!=AREA_FOREST)return;
    int stage=CLAMP(gWorld.cells[gGame.cell].stage,0,3),phase=(gFrame>>3)&3;
    gAdaptiveCanopyStats[9]=stage;
    if(stage!=sPaletteStage || phase!=sPalettePhase) {
        pal_set_bg(CANOPY_PALETTE_SLOT,canopy_stage_colors[stage][phase]);
        sPaletteStage=stage;sPalettePhase=phase;
    }
}
#endif
