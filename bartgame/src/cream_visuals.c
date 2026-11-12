/* Optional Cream synthesis study. The route generator owns every physical
   cell. This compositor only substitutes equal-contract native drawings. */
#include "cream_visuals.h"
#include "room.h"
#include "util.h"

#if BART_CREAM_VARIANT == 6
CreamVisualLanding gCreamVisualLandings[CC_NODES*CC_EDGE_MAX] EWRAM_BSS;
u16 gCreamVisualLandingCount;
u16 gCreamVisualPanelCount,gCreamVisualPanelCells;
u16 gCreamVisualRimCount,gCreamVisualDropCount,gCreamVisualToeCount;
u8 gCreamVisualPanelKinds[7];
static u8 sPanelSpace[CREAM_ROOM_W*CREAM_ROOM_H] EWRAM_BSS;
static u32 sOriginalRows[CREAM_ROOM_H];

static const u16 sMid[3][2]={
 {MT_CREAM_CLIFF_MID_S0_V0,MT_CREAM_CLIFF_MID_S0_V1},
 {MT_CREAM_CLIFF_MID_S1_V0,MT_CREAM_CLIFF_MID_S1_V1},
 {MT_CREAM_CLIFF_MID_S2_V0,MT_CREAM_CLIFF_MID_S2_V1}
};
static const u16 sBase[3][2]={
 {MT_CREAM_CLIFF_BASE_S0_V0,MT_CREAM_CLIFF_BASE_S0_V1},
 {MT_CREAM_CLIFF_BASE_S1_V0,MT_CREAM_CLIFF_BASE_S1_V1},
 {MT_CREAM_CLIFF_BASE_S2_V0,MT_CREAM_CLIFF_BASE_S2_V1}
};
static const u16 sRim[3]={MT_CREAM_RIM_S0,MT_CREAM_RIM_S1,MT_CREAM_RIM_S2};
static const u16 sDrop[3]={MT_CREAM_DROP_S0,MT_CREAM_DROP_S1,MT_CREAM_DROP_S2};
static const u16 sFloor[3][4]={
 {MT_CREAM_FLOOR_S0_V0,MT_CREAM_FLOOR_S0_V1,MT_CREAM_FLOOR_S0_V2,MT_CREAM_FLOOR_S0_V3},
 {MT_CREAM_FLOOR_S1_V0,MT_CREAM_FLOOR_S1_V1,MT_CREAM_FLOOR_S1_V2,MT_CREAM_FLOOR_S1_V3},
 {MT_CREAM_FLOOR_S2_V0,MT_CREAM_FLOOR_S2_V1,MT_CREAM_FLOOR_S2_V2,MT_CREAM_FLOOR_S2_V3}
};
static const u16 sPath[3][4]={
 {MT_CREAM_PATH_S0_V0,MT_CREAM_PATH_S0_V1,MT_CREAM_PATH_S0_V2,MT_CREAM_PATH_S0_V3},
 {MT_CREAM_PATH_S1_V0,MT_CREAM_PATH_S1_V1,MT_CREAM_PATH_S1_V2,MT_CREAM_PATH_S1_V3},
 {MT_CREAM_PATH_S2_V0,MT_CREAM_PATH_S2_V1,MT_CREAM_PATH_S2_V2,MT_CREAM_PATH_S2_V3}
};

static int visual_stage(void) {return MIN(gCreamRoom.stage,2);}
static bool8 in_room(int x,int y) {return x>=0 && y>=0 && x<CREAM_ROOM_W && y<CREAM_ROOM_H;}
static u32 variation(int x,int y) {
    return hash32(gCreamWorld.seed^0xD37A5E61u,(gCreamRoom.cell+1)*1153+x*43+y*137);
}

/* Refuse even a plausible-looking drawing if its logical contract differs.
   Keeping this check local also protects future additions to the art bank. */
static bool8 substitute(int x,int y,u16 replacement) {
    u16 old=room_get(x,y);
    if(!in_room(x,y) || replacement>=METATILE_COUNT || old>=METATILE_COUNT ||
       metatile_type[old]!=metatile_type[replacement] ||
       metatile_coll[old]!=metatile_coll[replacement] ||
       metatile_prop[old]!=metatile_prop[replacement] ||
       metatile_glitter[old]!=metatile_glitter[replacement])return FALSE;
    room_set(x,y,replacement);return TRUE;
}

static bool8 panel_fits(int x,int y,int p) {
    const CreamVisualPanel* panel=&cream_visual_panels[visual_stage()][p];
    int dx,dy;
    if(x<2 || y<0 || x+panel->w>30 || y+panel->h>CREAM_ROOM_H)return FALSE;
    for(dy=0;dy<panel->h;dy++)for(dx=0;dx<panel->w;dx++)
        if(sPanelSpace[(y+dy)*CREAM_ROOM_W+x+dx]!=1)return FALSE;
    /* Alternating the same two halves is still wallpaper. The same complete
       painting cannot immediately meet itself along either axis. */
    for(dy=0;dy<panel->h;dy++) {
        if(x>0 && sPanelSpace[(y+dy)*CREAM_ROOM_W+x-1]==p+2)return FALSE;
        if(x+panel->w<CREAM_ROOM_W && sPanelSpace[(y+dy)*CREAM_ROOM_W+x+panel->w]==p+2)return FALSE;
    }
    for(dx=0;dx<panel->w;dx++) {
        if(y>0 && sPanelSpace[(y-1)*CREAM_ROOM_W+x+dx]==p+2)return FALSE;
        if(y+panel->h<CREAM_ROOM_H && sPanelSpace[(y+panel->h)*CREAM_ROOM_W+x+dx]==p+2)return FALSE;
    }
    return TRUE;
}

static void place_panel(int x,int y,int p) {
    const CreamVisualPanel* panel=&cream_visual_panels[visual_stage()][p];
    int dx,dy;
    for(dy=0;dy<panel->h;dy++)for(dx=0;dx<panel->w;dx++) {
        substitute(x+dx,y+dy,panel->first+dy*panel->w+dx);
        sPanelSpace[(y+dy)*CREAM_ROOM_W+x+dx]=p+2;
    }
    gCreamVisualPanelCount++;gCreamVisualPanelCells+=panel->w*panel->h;
    gCreamVisualPanelKinds[p]++;
}

static int original_run(int x,int y) {
    int left=x,right=x;
    if(y<0 || y>=CREAM_ROOM_H || !(sOriginalRows[y]&(1u<<x)))return 0;
    while(left>2 && (sOriginalRows[y]&(1u<<(left-1))))left--;
    while(right<29 && (sOriginalRows[y]&(1u<<(right+1))))right++;
    return right-left+1;
}

static void wall_panels(void) {
    int x,y,p,s=visual_stage(),best_x=-1,best_y=0,best=-32767,available=0,attempt;
    gCreamVisualPanelCount=gCreamVisualPanelCells=0;
    memset(gCreamVisualPanelKinds,0,sizeof(gCreamVisualPanelKinds));
    memset(sPanelSpace,0,sizeof(sPanelSpace));
    memset(sOriginalRows,0,sizeof(sOriginalRows));
    /* Only native midface backing can host these drawings. A cave, handhold,
       raised rim, waterfall, gate or foreground object is never flattened. */
    for(y=0;y<CREAM_ROOM_H;y++)for(x=2;x<30;x++) {
        int index=y*ROOM_MAX_W+x;u16 mt=gRoom.ground[index];
        if((mt==sMid[s][0] || mt==sMid[s][1]) &&
           gRoom.overlay[index]==MT_NONE && !cream_room_feature_reserved(x,y)) {
            sPanelSpace[y*CREAM_ROOM_W+x]=1;
            sOriginalRows[y]|=1u<<x;available++;
        }
    }
    /* One rare, large, closed blind arch. Prefer the principal cliff, and
       require its full footprint rather than clipping a repeated arch tile. */
    if(available>=24 && (variation(14,11)&3)!=0)for(y=0;y<CREAM_ROOM_H-2;y++)for(x=3;x<27;x++) {
        int score;
        if(!panel_fits(x,y,4))continue;
        score=120-ABS(x+2-16)*4-ABS(y+1-11)*5+(variation(x,y)&15);
        if(y>gCreamRoom.upper_bottom[x] && y<gCreamRoom.lower_top[x])score+=100;
        if(score>best){best=score;best_x=x;best_y=y;}
    }
    if(best_x>=0)place_panel(best_x,best_y,4);
    /* Candidate anchors span the measured faces at unequal x/y offsets.
       A top-to-bottom first-fit would align every 32px panel in two-row bands,
       even with many drawings. Seeded anchors break that mechanical rhythm.
       Quiet backing deliberately occupies at least a third of the face. */
    for(attempt=0;attempt<192 && gCreamVisualPanelCells*3<available*2;attempt++) {
        u32 anchor=variation(attempt*3+7,attempt*11+17),n;
        int choice[4],i,wide,variant;
        x=2+anchor%26;y=(anchor>>8)%(CREAM_ROOM_H-1);
        if(sPanelSpace[y*CREAM_ROOM_W+x]!=1)continue;
        n=variation(x/5+37,y/3+43);wide=(n>>7)&1;variant=(anchor>>17)&1;
        choice[0]=(wide?2:0)+variant;
        choice[1]=(wide?0:2)+((anchor>>19)&1);
        choice[2]=choice[0]^1;choice[3]=choice[1]^1;
        for(i=0;i<4;i++) {
            const CreamVisualPanel* panel;
            p=choice[i];panel=&cream_visual_panels[s][p];
            if((gCreamVisualPanelCells+panel->w*panel->h)*3>available*2)continue;
            if(panel_fits(x,y,p)){place_panel(x,y,p);break;}
        }
    }
    /* A little remainder left by packing is not automatically a new rock.
       Compact paintings belong only to a genuinely narrow original face. */
    for(y=0;y<CREAM_ROOM_H-1;y++)for(x=2;x<30;x++) {
        int first;
        if(sPanelSpace[y*CREAM_ROOM_W+x]!=1 || original_run(x,y)>3 || original_run(x,y+1)>3)continue;
        if((gCreamVisualPanelCells+4)*3>available*2)continue;
        first=5+((variation(x,y)>>13)&1);
        if(panel_fits(x,y,first))place_panel(x,y,first);
        else if(panel_fits(x,y,first==5?6:5))place_panel(x,y,first==5?6:5);
    }
}

static bool8 solid_rim(u16 mt,int s) {
    return mt==sRim[s] || mt==cream_visual_rim[s][0] || mt==cream_visual_rim[s][1] ||
           mt==cream_visual_edge[s][0] || mt==cream_visual_edge[s][1];
}
static bool8 open_drop(u16 mt,int s) {
    return mt==sDrop[s] || mt==cream_visual_drop[s][0] || mt==cream_visual_drop[s][1] ||
           mt==cream_visual_edge[s][2] || mt==cream_visual_edge[s][3];
}
static bool8 raised_rim_at(int x,int y,int s) {
    return in_room(x,y) && solid_rim(room_get(x,y),s) && !open_drop(room_get(x,y-1),s);
}
static bool8 quiet_floor(u16 mt,int s) {
    int i;
    for(i=0;i<4;i++)if(mt==sFloor[s][i])return TRUE;
    for(i=0;i<2;i++)if(mt==cream_visual_floor_toe[s][i])return TRUE;
    for(i=0;i<6;i++)if(mt==cream_visual_landing[s][i])return TRUE;
    return FALSE;
}
static int path_variant(u16 mt,int s) {
    int variant,part;
    for(variant=0;variant<4;variant++) {
        if(mt==sPath[s][variant])return variant;
        for(part=0;part<6;part++)if(mt==cream_visual_landing_path[s][variant][part])return variant;
    }
    return -1;
}

static void ledge_edges(void) {
    int x,y,s=visual_stage(),terrace,i,dx;
    gCreamVisualRimCount=gCreamVisualDropCount=gCreamVisualToeCount=0;
    /* The generated profile already identifies every possible rim/base row.
       Do not rescan the entire room to rediscover those fifty-six cells. */
    for(x=2;x<30;x++) {
        y=gCreamRoom.upper_bottom[x]+1;
        u16 mt=room_get(x,y);
        if(solid_rim(mt,s)) {
            bool8 left=raised_rim_at(x-1,y,s),right=raised_rim_at(x+1,y,s);
            u16 tile=cream_visual_rim[s][(variation(x/2,y)>>3)&1];
            /* A real open takeoff has an ordinary vertical face below it,
               not another raised, apparently impassable curb. */
            if(open_drop(room_get(x,y-1),s))tile=sMid[s][x&1];
            else if(!left)tile=cream_visual_edge[s][0];
            else if(!right)tile=cream_visual_edge[s][1];
            if(substitute(x,y,tile) && solid_rim(tile,s))gCreamVisualRimCount++;
        }
        y=gCreamRoom.lower_top[x]-1;mt=room_get(x,y);
        if(mt==sBase[s][0] || mt==sBase[s][1])substitute(x,y,cream_visual_edge[s][4]);
    }
    /* Only cells already marked by an actual directed DROP can get an open
       sill. A solid gate or cape pit keeps its existing drawing and type. */
    for(terrace=0;terrace<2;terrace++) {
        int node=cream_node(gCreamRoom.cell,terrace);
        for(i=0;i<cream_edge_count(node);i++) {
            const CreamEdge* edge=cream_edge(node,i);int px,py,row,rows;
            if(edge->kind!=CC_DROP)continue;
            cream_room_drop_pos(node,i,&px,&py);x=(px>>4)-1;y=py>>4;
            rows=terrace==CC_LOWER?2:1;
            for(row=0;row<rows;row++)for(dx=0;dx<2;dx++) {
                int tx=x+dx,ty=y+row;u16 tile;
                bool8 left,right;
                if(!open_drop(room_get(tx,ty),s))continue;
                left=open_drop(room_get(tx-1,ty),s);right=open_drop(room_get(tx+1,ty),s);
                tile=cream_visual_drop[s][(tx+ty)&1];
                if(ty!=CREAM_ROOM_H-1) {
                    if(!left)tile=cream_visual_edge[s][2];
                    else if(!right)tile=cream_visual_edge[s][3];
                }
                if(substitute(tx,ty,tile))gCreamVisualDropCount++;
            }
        }
    }
    /* The wall-foot contact shade belongs to the actual floor immediately
       below a cliff base. Paths and objects keep their own clear drawings. */
    for(x=2;x<30;x++) {
        y=gCreamRoom.lower_top[x];
        if(room_get(x,y-1)==cream_visual_edge[s][4] && quiet_floor(room_get(x,y),s) &&
           substitute(x,y,cream_visual_floor_toe[s][variation(x/3,y)&1]))gCreamVisualToeCount++;
    }
}

static void landing_shadows(void) {
    int from,i,s=visual_stage();
    gCreamVisualLandingCount=0;
    /* Scan once per room/gate change, never in the frame loop. The bound is
       the entire directed graph, so no unusual seed silently loses a cue. */
    for(from=0;from<CC_NODES;from++)for(i=0;i<cream_edge_count(from);i++) {
        const CreamEdge* edge=cream_edge(from,i);CreamVisualLanding* cue;int px,py,facing,part;
        bool8 active;
        if(edge->kind!=CC_DROP || cream_cell(edge->target)!=gCreamRoom.cell)continue;
        cue=&gCreamVisualLandings[gCreamVisualLandingCount++];
        cream_room_arrival(from,edge,&px,&py,&facing);
        cue->x=px;cue->y=py;cue->from=from;cue->edge=i;
        cue->x0=(px>>4)-1;cue->y0=py>>4;cue->parts=0;
        cue->flags=(edge->flags&CC_LONG_DROP)?CREAM_VISUAL_LONG:0;
        if(edge->require)cue->flags|=CREAM_VISUAL_GATED;
        /* Cape cracks remain physical pits even after the cloak is acquired.
           Their destination is still real. Other gates need actual clearing. */
        active=!edge->require || edge->require==CC_TOKEN_CAPE_PACCI ||
               (gCreamOpenEdges[from]&(1u<<i));
        if(!active)continue;
        cue->flags|=CREAM_VISUAL_ACTIVE;
        for(part=0;part<6;part++) {
            int x=cue->x0+part%3,y=cue->y0+part/3,pv;u16 tile,old;
            if(!in_room(x,y))continue;
            old=room_get(x,y);pv=path_variant(old,s);
            if(pv<0 && !quiet_floor(old,s))continue;
            tile=pv<0?cream_visual_landing[s][part]:cream_visual_landing_path[s][pv][part];
            if(substitute(x,y,tile))cue->parts|=1u<<part;
        }
    }
}

void cream_visuals_refresh(void) {ledge_edges();landing_shadows();}
void cream_visuals_build(void) {wall_panels();cream_visuals_refresh();}
#endif
