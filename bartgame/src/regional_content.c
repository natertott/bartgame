/* Regional content is dealt onto the existing directed world, not selected
   from an annex menu. The plan is seed-only; locations are admitted against
   the actual loaded collision and retained once discovered. */
#include "regional_content.h"
#include "handoff_events.h"
#include "world.h"
#include "cream_world.h"
#include "cream_room.h"
#include "cream_runtime.h"
#include "world_tokens.h"
#include "game.h"
#include "room.h"
#include "player.h"
#include "legacy_items.h"
#include "util.h"
#include "forest_trees.h"

RegionalContentSpots gRegionalSpots EWRAM_BSS;
RegionalContentDiscovery gRegionalDiscovery[RC_ROOMS] EWRAM_BSS;
static RegionalContentPlan sPlan[RC_ROOMS] EWRAM_BSS;
static u32 sPlanSeed[3];
static u8 sPlanReady,sArea,sCell;
static u32 sReach[ROOM_MAX_H] EWRAM_BSS;
static u32 sReserved[ROOM_MAX_H] EWRAM_BSS;
static u32 sCore[ROOM_MAX_H] EWRAM_BSS;
static u32 sForestReserved[ROOM_MAX_H] EWRAM_BSS;
static u32 sForestLandmarks[ROOM_MAX_H] EWRAM_BSS;
static u32 sOriginalReach[ROOM_MAX_H] EWRAM_BSS;
static u32 sComponents[2][ROOM_MAX_H] EWRAM_BSS;
static u8 sComponentReady;
static u16 sQueue[ROOM_MAX_W*ROOM_MAX_H] EWRAM_BSS;
static u8 sRectCount;
static RegionalContentRect sRects[4];
static Spot sAdmittedSpawns[24] EWRAM_BSS;
static u8 sSpawnTerrace[24] EWRAM_BSS;
static u8 sSpawnCount;

int regional_content_index(int area,int cell) {
    if(cell<0||cell>=25)return -1;
    return area==AREA_FOREST?cell:area==AREA_CREAM?25+cell:-1;
}
static int region_area(int region){return region?AREA_CREAM:AREA_FOREST;}
static int entry_cell(int region){return region?cream_cell(gCreamWorld.entry_node):gWorld.entry;}
static int goal_cell(int region){return region?cream_cell(gCreamWorld.goal_node):gWorld.goal;}
static bool8 ordinary_cell(int region,int cell){return cell!=entry_cell(region)&&cell!=goal_cell(region);}
static int cell_stage(int region,int cell) {
    return region?MIN(gCreamWorld.stage[cell*2],gCreamWorld.stage[cell*2+1]):gWorld.cells[cell].stage;
}
static int choose_cell(int region,int excluded0,int excluded1,u32 salt,bool8 early) {
    u32 best=0;int chosen=-1,cell,pass;
    for(pass=0;pass<2&&chosen<0;pass++)for(cell=0;cell<25;cell++) {
        u32 score;
        if(!ordinary_cell(region,cell)||cell==excluded0||cell==excluded1)continue;
        if(!pass&&early&&cell_stage(region,cell)!=0)continue;
        score=hash32(gGame.seed,salt+cell*131+region*3571);
        if(chosen<0||score>best){best=score;chosen=cell;}
    }
    return chosen;
}
static int quest_cell(int kind) {
    int cell,chosen=-1;u32 best=0;
    if(kind!=HQ_BLOCKS)return choose_cell(0,-1,-1,0x51554553u,TRUE);
    /* Broad fields are preferable for the certified5x5 board plus its dry
       walking ring. The physical fit is still checked when placed. */
    for(cell=0;cell<25;cell++)if(ordinary_cell(0,cell)) {
        int broad=gWorld.cells[cell].arch==ARCH_GLADE||gWorld.cells[cell].arch==ARCH_ARENA;
        u32 score=(broad?0x40000000u:0)+(3-MIN(3,gWorld.cells[cell].stage))*0x10000000u+
            (hash32(gGame.seed,0x51554553u+cell*131)&0x0fffffffu);
        if(chosen<0||score>best){chosen=cell;best=score;}
    }
    return chosen;
}
static int red_fusion_cell(void) {
    int cell,chosen=-1;u32 best=0;
    for(cell=0;cell<25;cell++)if(ordinary_cell(1,cell)) {
        int bits=gCreamWorld.content[cell*2]&(CC_CONTENT_CHEST|CC_CONTENT_NPC|CC_CONTENT_HEAL|CC_CONTENT_CACHE|CC_CONTENT_MISSION);
        int count=0,i;u32 score;
        for(i=0;i<8;i++)count+=(bits>>i)&1;
        /* The optional island needs a real five-by-five bank. Prefer a
           lower terrace without existing furniture over a merely early
           shelf whose shrine, chest and landing already consume its room. */
        score=(5-count)*0x10000000u+(3-MIN(3,gCreamWorld.stage[cell*2]))*0x02000000u+
            (hash32(gGame.seed,0x46555332u+cell*131)&0x01ffffffu);
        if(chosen<0||score>best){chosen=cell;best=score;}
    }
    return chosen;
}
static void build_plan(void) {
    static const u8 base[]={HS_ITEM,HS_MINIBOSS,HS_NPC,HS_WAVES,HS_POTS,HS_FAIRY,
        HS_MEMORY_SHOW,HS_MEMORY_INPUT,HS_SWITCHES,HS_BLOCK_TEMPLATE,HS_BLOCK_MAZE,
        HS_TORCHES,HS_CLEANUP,HS_SURVIVE,HS_PORTAL,HS_POCKET,HS_BOSS,HS_GOLD_GATE};
    int region,cell,i,j,quest,green,blue,red,wave[2];
    u32 offset=hash32(gGame.seed,0x52454749u)%46;
    memset(sPlan,RC_NONE,sizeof(sPlan));
    for(region=0;region<2;region++) {
        u8 order[25];int count=0;
        for(cell=0;cell<25;cell++)if(ordinary_cell(region,cell))order[count++]=cell;
        /* A stable permutation spreads content classes across every new
           seed, while retaining exactly one Learn/Recall pair and all12
           mechanism/three traversal pattern opportunities over both areas. */
        for(i=1;i<count;i++) {
            u8 next=order[i];u32 key=hash32(gGame.seed,region*0x10000+next*7919+71);
            j=i;
            while(j>0) {
                u32 prev=hash32(gGame.seed,region*0x10000+order[j-1]*7919+71);
                if(prev<key||(prev==key&&order[j-1]<next))break;
                order[j]=order[j-1];j--;
            }
            order[j]=next;
        }
        for(cell=0;cell<25;cell++) {
            RegionalContentPlan* p=&sPlan[region*25+cell];
            p->area=region_area(region);p->cell=cell;p->field_site=RC_FIELD_BASE+region*25+cell;
            p->quest_kind=HQ_NONE;p->has_wave=0;p->stage=cell_stage(region,cell);
            p->terrace=0;
            if(region) {
                int lo=gCreamWorld.stage[cell*2],hi=gCreamWorld.stage[cell*2+1];
                p->terrace=lo==hi?(hash32(gGame.seed,cell+0x7E22)&1):(hi<lo);
                if(cell==entry_cell(region))p->terrace=cream_terrace(gCreamWorld.entry_node);
                if(cell==goal_cell(region))p->terrace=cream_terrace(gCreamWorld.goal_node);
            }
        }
        for(i=0;i<count;i++) {
            int slot=((i*2+region)*17+offset)%46;
            RegionalContentPlan* p=&sPlan[region*25+order[i]];
            p->interior_site=RC_INTERIOR_BASE+region*23+i;
            if(slot<18)p->event_kind=base[slot];
            else if(slot<30){p->event_kind=HS_OBJECT_COURSE;p->mechanism_variant=slot-18;}
            else if(slot<33){p->event_kind=HS_TRAVERSAL;p->traversal_variant=slot-30;}
            else p->event_kind=base[(slot-33)%14];
        }
    }
    /* A single side quest is selected at run start. Ordinary givers prefer
       the pre-tool Forest; a block giver prefers a broad verified field. */
    i=HQ_POT+hash32(gGame.seed,0x51554537u)%7;quest=quest_cell(i);
    if(quest>=0)sPlan[quest].quest_kind=i;
    green=choose_cell(0,quest,-1,0x46555330u,TRUE);
    blue=choose_cell(0,quest,green,0x46555331u,FALSE);
    red=red_fusion_cell();
    if(green>=0)sPlan[green].fusion_color=0;
    if(blue>=0)sPlan[blue].fusion_color=1;
    if(red>=0)sPlan[25+red].fusion_color=2;
    if(blue>=0)for(i=0;i<RC_ROOMS;i++)if(sPlan[i].event_kind==HS_POCKET) {
        /* The blue fusion opens a real regional pocket entrance. Exchange
           its decoration with the already dealt pocket, retaining every
           unique memory, mechanism and traversal opportunity. */
        u8 kind=sPlan[blue].event_kind,mechanism=sPlan[blue].mechanism_variant,traversal=sPlan[blue].traversal_variant;
        sPlan[blue].event_kind=HS_POCKET;sPlan[blue].mechanism_variant=sPlan[blue].traversal_variant=RC_NONE;
        sPlan[i].event_kind=kind;sPlan[i].mechanism_variant=mechanism;sPlan[i].traversal_variant=traversal;
        break;
    }
    if(hash32(gGame.seed,0x504f5254u)%3) {
        for(i=0;i<RC_ROOMS;i++)if(sPlan[i].event_kind==HS_PORTAL)sPlan[i].event_kind=HS_SURVIVE;
    } else {
        /* A portal's pocket is separate from the blue fusion door, so one
           feature cannot silently bypass the other's physical lock. */
        for(i=RC_ROOMS-1;i>=0;i--)if(sPlan[i].event_kind==HS_ITEM&&sPlan[i].fusion_color!=1){sPlan[i].event_kind=HS_POCKET;break;}
    }
    for(region=0;region<2;region++) {
        u32 best=0;wave[region]=-1;
        for(cell=0;cell<25;cell++) {
            RegionalContentPlan* p=&sPlan[region*25+cell];u32 score;
            if(!ordinary_cell(region,cell)||p->quest_kind||p->fusion_color!=RC_NONE)continue;
            if(!region&&(gWorld.cells[cell].role==ROLE_KEYITEM||
               gWorld.cells[cell].role==ROLE_NPC_HUNT||gWorld.cells[cell].role==ROLE_NPC_FETCH||
               gWorld.cells[cell].role==ROLE_NPC_TORCH))continue;
            score=(3-MIN(3,p->stage))*0x10000000u+(hash32(gGame.seed,cell+region*53+0x57415645u)&0x0fffffffu);
            if(wave[region]<0||score>best){best=score;wave[region]=cell;}
        }
        if(wave[region]>=0)sPlan[region*25+wave[region]].has_wave=1;
    }
    for(i=0;i<RC_ROOMS;i++) {
        RegionalContentPlan* p=&sPlan[i];
        if(region_area(i/25)==AREA_CREAM&&(p->has_wave||p->fusion_color!=RC_NONE)) {
            p->terrace=CC_LOWER;p->stage=gCreamWorld.stage[p->cell*2];
        }
        if(p->interior_site!=RC_NONE&&!p->quest_kind&&p->fusion_color==RC_NONE&&!p->has_wave&&p->traversal_variant==RC_NONE&&
           (hash32(gGame.seed,i+0x4d454348u)&1)==0)
            p->field_mechanism_variant=hash32(gGame.seed,i+0x4649454cu)%4;
    }
    sPlanSeed[0]=gGame.seed;sPlanSeed[1]=gWorld.seed;sPlanSeed[2]=gCreamWorld.seed;sPlanReady=1;
}
static bool8 ensure_plan(void) {
    if(gWorld.entry>=25||gWorld.goal>=25||gWorld.entry==gWorld.goal||
       gCreamWorld.entry_node>=50||gCreamWorld.goal_node>=50||
       cream_cell(gCreamWorld.entry_node)==cream_cell(gCreamWorld.goal_node))return FALSE;
    if(!sPlanReady||sPlanSeed[0]!=gGame.seed||sPlanSeed[1]!=gWorld.seed||sPlanSeed[2]!=gCreamWorld.seed)build_plan();
    return TRUE;
}
void regional_content_clear(void) {
    memset(&gRegionalSpots,0,sizeof(gRegionalSpots));
    memset(sReach,0,sizeof(sReach));memset(sReserved,0,sizeof(sReserved));memset(sCore,0,sizeof(sCore));
    memset(sForestReserved,0,sizeof(sForestReserved));memset(sForestLandmarks,0,sizeof(sForestLandmarks));
    memset(sComponents,0,sizeof(sComponents));sComponentReady=sSpawnCount=0;
    sRectCount=0;sArea=sCell=RC_NONE;
}
void regional_content_new_run(void) {
    sPlanReady=0;memset(gRegionalDiscovery,0,sizeof(gRegionalDiscovery));regional_content_clear();
}
bool8 regional_content_get(int area,int cell,RegionalContentPlan* out) {
    int at=regional_content_index(area,cell);
    if(at<0||!out)return FALSE;
    if(!ensure_plan())return FALSE;
    *out=sPlan[at];return TRUE;
}
static bool8 forest_passable(int cell,int side) {
    int gate=gWorld.cells[cell].gate[side];
    if(gate==GATE_WALL)return FALSE;
    if(!world_trial_gate_ready(cell,side))return FALSE;
    if(world_gate_open(cell,side))return TRUE;
    if(gate==GATE_CRACK)return (gPl.items&ITEM_BOMBS)!=0;
    if(gate==GATE_WEB)return (gPl.items&ITEM_LAMP)!=0;
    if(gate==GATE_CHASM)return (gPl.items&ITEM_CLOAK)!=0;
    if(gate==GATE_THORN)return (gPl.items&ITEM_SWORD)!=0;
    return TRUE;
}
bool8 regional_content_reachable(int area,int cell) {
    RegionalContentPlan p;u8 seen[50],queue[50];int head=0,tail=0,i,n;
    if(!regional_content_get(area,cell,&p))return FALSE;
    memset(seen,0,sizeof(seen));
    if(area==AREA_FOREST) {
        u8 price[25];int changed=1,passes;
        memset(price,255,sizeof(price));price[gWorld.entry]=0;
        /* Count each still-locked key door on the cheapest route instead of
           treating one held key as permission to pass arbitrarily many. */
        for(passes=0;passes<25&&changed;passes++) {
            changed=0;
            for(n=0;n<25;n++)if(price[n]!=255)for(i=0;i<4;i++) {
                int next=cell_neighbor(n,i),cost;
                if(next<0||!forest_passable(n,i))continue;
                cost=price[n]+(gWorld.cells[n].gate[i]==GATE_LOCK&&!world_gate_open(n,i));
                if(cost<price[next]){price[next]=cost;changed=1;}
            }
        }
        return price[cell]!=255&&price[cell]<=gPl.keys;
    }
    if(!handoff_region_unlocked(AREA_CREAM))return FALSE;
    queue[tail++]=gCreamWorld.entry_node;seen[gCreamWorld.entry_node]=1;
    while(head<tail) {
        n=queue[head++];if(n==cream_node(cell,p.terrace))return TRUE;
        for(i=0;i<cream_edge_count(n);i++) {
            const CreamEdge* e=cream_edge(n,i);
            if(e->target<50&&!seen[e->target]&&world_tokens_cream_open(e->require)){seen[e->target]=1;queue[tail++]=e->target;}
        }
    }
    return FALSE;
}
bool8 regional_content_find(int kind,int after,bool8 reachable,RegionalContentPlan* out) {
    int i;
    if(!out||!ensure_plan())return FALSE;
    for(i=MAX(-1,after)+1;i<RC_ROOMS;i++)if(sPlan[i].event_kind==kind&&
        (!reachable||regional_content_reachable(sPlan[i].area,sPlan[i].cell))){*out=sPlan[i];return TRUE;}
    return FALSE;
}
bool8 regional_content_fusion(int color,RegionalContentPlan* out) {
    int i;if(color<0||color>2||!out||!ensure_plan())return FALSE;
    for(i=0;i<RC_ROOMS;i++)if(sPlan[i].fusion_color==color){*out=sPlan[i];return TRUE;}
    return FALSE;
}
bool8 regional_content_door_open(int area,int cell) {
    RegionalContentPlan p;int i;
    if(!regional_content_get(area,cell,&p)||p.interior_site==RC_NONE)return FALSE;
    if(p.fusion_color==1)return (gHandoffState.fusion_flags&2)!=0;
    if(p.event_kind==HS_POCKET) {
        for(i=0;i<RC_ROOMS;i++)if(sPlan[i].event_kind==HS_PORTAL) {
            int site=sPlan[i].interior_site;
            return (gHandoffState.completed[site>>3]&(1u<<(site&7)))!=0;
        }
        return FALSE;
    }
    return TRUE;
}

static bool8 dry(int x,int y,int terrace) {
    int type,surface;
    if(x<1||y<1||x>=gRoom.w-1||y>=gRoom.h-1)return FALSE;
    type=room_type(x,y);surface=legacy_surface_at(x*16+8,y*16+12);
    if(type!=TT_FLOOR&&type!=TT_DOOR_OPEN&&type!=TT_CHEST_OPEN&&type!=TT_SWITCH)return FALSE;
    if(surface==LS_ICE||surface==LS_SWAMP||surface==LS_LAVA||surface==LS_CRUMBLE)return FALSE;
    if(sArea==AREA_CREAM&&cream_room_terrace_at(x*16+8,y*16+14,terrace)!=terrace)return FALSE;
    return !room_box_solid(x*16+3,y*16+5,x*16+12,y*16+14);
}
static bool8 reached(int x,int y){return x>=0&&y>=0&&x<gRoom.w&&y<gRoom.h&&(sReach[y]&(1u<<x));}
static void component(int x,int y,int terrace) {
    static const s8 dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int head=0,tail=0,i;
    memset(sReach,0,sizeof(sReach));
    if(!dry(x,y,terrace))return;
    sReach[y]|=1u<<x;sQueue[tail++]=y*32+x;
    while(head<tail) {
        int at=sQueue[head++];x=at&31;y=at>>5;
        for(i=0;i<4;i++) {
            int xx=x+dx[i],yy=y+dy[i];
            if(!reached(xx,yy)&&dry(xx,yy,terrace)){sReach[yy]|=1u<<xx;sQueue[tail++]=yy*32+xx;}
        }
    }
    memcpy(sComponents[terrace],sReach,sizeof(sReach));sComponentReady|=1u<<terrace;
}
static bool8 landmark_reserved(int x,int y) {
    int i;
    if(x<2||y<2||x>=gRoom.w-2||y>=gRoom.h-2)return TRUE;
    if(sCore[y]&(1u<<x))return TRUE;
    if(sArea==AREA_CREAM) {
        if(cream_room_feature_reserved(x,y))return TRUE;
        /* No terrace lip, climb lane, cave or inter-room arrival can become
           a new optional object's backside or landing. */
        if(ABS(x-gCreamRoom.climb_x)<=2)return TRUE;
        if(y<=gCreamRoom.upper_bottom[x]+1&&y>=gCreamRoom.upper_bottom[x]-1)return TRUE;
        for(i=0;i<2;i++) {
            int px,py;cream_room_cave_pos(i,&px,&py);
            if(ABS(x-px/16)<=2&&ABS(y-py/16)<=2)return TRUE;
        }
    } else {
        if(sForestLandmarks[y]&(1u<<x))return TRUE;
        if(gSpots.has_treasure&&ABS(x-gSpots.treasure.x)<=2&&ABS(y-gSpots.treasure.y)<=2)return TRUE;
        if(gSpots.pocket_kind&&ABS(x-gSpots.pocket_gate.x)<=2&&ABS(y-gSpots.pocket_gate.y)<=2)return TRUE;
        if(gSpots.has_boss&&ABS(x-gSpots.boss.x)<=4&&ABS(y-gSpots.boss.y)<=4)return TRUE;
    }
    return FALSE;
}
static bool8 core_reserved(int x,int y) {
    return landmark_reserved(x,y)||(sArea==AREA_FOREST&&x>=0&&x<32&&y>=0&&y<32&&(sForestReserved[y]&(1u<<x)));
}
bool8 regional_content_reserved(int x,int y) {
    if(sArea!=AREA_FOREST&&sArea!=AREA_CREAM)return FALSE;
    return core_reserved(x,y)||(x>=0&&x<32&&y>=0&&y<32&&(sReserved[y]&(1u<<x)));
}
static void reserve(int x,int y,int w,int h) {
    int xx,yy;
    for(yy=MAX(0,y);yy<MIN((int)gRoom.h,y+h);yy++)for(xx=MAX(0,x);xx<MIN((int)gRoom.w,x+w);xx++)sReserved[yy]|=1u<<xx;
}
static void core_reserve(int x,int y,int w,int h) {
    int xx,yy;for(yy=MAX(0,y);yy<MIN((int)gRoom.h,y+h);yy++)for(xx=MAX(0,x);xx<MIN((int)gRoom.w,x+w);xx++)sCore[yy]|=1u<<xx;
}
static bool8 point_ok(Spot p,int role) {
    int x=p.x,y=p.y,xx,yy;
    if(!reached(x,y)||!reached(x,y+1)||core_reserved(x,y)||core_reserved(x,y+1))return FALSE;
    for(yy=y-(role==0?1:0);yy<=y+1;yy++)for(xx=x-1;xx<=x+1;xx++)
        if(!dry(xx,yy,gRegionalSpots.terrace)||(sReserved[yy]&(1u<<xx)))return FALSE;
    return TRUE;
}
static bool8 choose_point(Spot old,int role,u32 salt,Spot* out) {
    u32 best=0;int x,y,found=0;
    if((old.x||old.y)&&point_ok(old,role)){*out=old;reserve(old.x-1,old.y-(role==0?1:0),3,role==0?3:2);return TRUE;}
    for(y=3;y<gRoom.h-3;y++)for(x=3;x<gRoom.w-3;x++) {
        Spot p={(u8)x,(u8)y};u32 score;
        if(!point_ok(p,role))continue;
        score=hash32(gGame.seed,salt+x*157+y*353+sCell*7919+sArea*11113);
        if(!found||score>best){found=1;best=score;*out=p;}
    }
    if(found)reserve(out->x-1,out->y-(role==0?1:0),3,role==0?3:2);
    return found;
}
static bool8 compact_point(Spot old,Spot* out) {
    u32 best=0;int x,y,xx,yy,pass,found=0;
    for(pass=0;pass<2&&!found;pass++)for(y=3;y<gRoom.h-3;y++)for(x=3;x<gRoom.w-3;x++) {
        int w=pass?1:2;bool8 valid=TRUE;u32 score;
        for(yy=y;yy<=y+1&&valid;yy++)for(xx=x;xx<x+w;xx++)
            if(!reached(xx,yy)||landmark_reserved(xx,yy)||(sReserved[yy]&(1u<<xx))){valid=FALSE;break;}
        if(!valid)continue;
        score=hash32(gGame.seed,x*157+y*353+sCell*7919+sArea*11113+0x48415443u);
        if((old.x==x&&old.y==y))score=0xffffffffu;
        if(!found||score>best){found=1;best=score;out->x=x;out->y=y;}
    }
    if(found)reserve(out->x,out->y,2,2);
    return found;
}
static bool8 rect_ok(int x,int y,int w,int h) {
    int xx,yy;
    if(x<2||y<2||x+w>gRoom.w-2||y+h>gRoom.h-2)return FALSE;
    for(yy=y;yy<y+h;yy++)for(xx=x;xx<x+w;xx++)
        if(!reached(xx,yy)||core_reserved(xx,yy)||(sReserved[yy]&(1u<<xx)))return FALSE;
    return TRUE;
}
static void take_rect(const RegionalContentRect* rect) {
    reserve(rect->x,rect->y,rect->w,rect->h);sRects[sRectCount++]=*rect;
}
bool8 regional_content_rect(int w,int h,RegionalContentRect* out) {
    int x,y,xx,yy,found=0;u32 best=0;
    if(!out||w<1||h<1||w>16||h>12||sRectCount>=4)return FALSE;
    for(y=2;y+h<=gRoom.h-2;y++)for(x=2;x+w<=gRoom.w-2;x++) {
        u32 score;bool8 valid=TRUE;
        for(yy=y;yy<y+h&&valid;yy++)for(xx=x;xx<x+w;xx++)
            if(!reached(xx,yy)||core_reserved(xx,yy)||(sReserved[yy]&(1u<<xx))){valid=FALSE;break;}
        if(!valid)continue;
        score=hash32(gGame.seed,x*811+y*3571+sCell*57+sArea*8911+w*53+h);
        if(!found||score>best){found=1;best=score;out->x=x;out->y=y;out->w=w;out->h=h;}
    }
    if(found)take_rect(out);
    return found;
}
static bool8 removable_wood(u16 mt) {
    if(mt==MT_NONE)return FALSE;
#if BART_FOREST_VARIANT >= 31
    return forest_trees_legacy(mt);
#else
    return (mt>=MT_CANOPY&&mt<=MT_TREE_TRUNK_E)||mt==MT_CANOPY_BLIGHT2;
#endif
}
static bool8 clearing_cell(int x,int y) {
    u16 ground=room_get(x,y),overlay=room_get_overlay(x,y);int type=room_type(x,y);
    if(landmark_reserved(x,y)||(sReserved[y]&(1u<<x)))return FALSE;
    if(overlay!=MT_NONE&&!removable_wood(overlay)&&metatile_prop[overlay])return FALSE;
    if(dry(x,y,gRegionalSpots.terrace))return reached(x,y);
    if(sArea!=AREA_FOREST)return FALSE;
    if((type==TT_SOLID||type==TT_FRONT)&&removable_wood(ground))return TRUE;
    return type==TT_SLOW&&ground==MT_TALL_GRASS;
}
static bool8 clearing_ok(int x,int y,int w,int h,int* count) {
    int xx,yy,touched=0,carved=0;
    if(x<2||y<2||x+w>gRoom.w-2||y+h>gRoom.h-2)return FALSE;
    for(yy=y;yy<y+h;yy++)for(xx=x;xx<x+w;xx++) {
        if(!clearing_cell(xx,yy))return FALSE;
        if(reached(xx,yy))touched=1;else carved++;
    }
    if(!touched)return FALSE;
    /* Even diagonal adjacency to another dry component is rejected. This
       clearing can enlarge the current field, never bypass its item pocket. */
    for(yy=y-1;yy<=y+h;yy++)for(xx=x-1;xx<=x+w;xx++) {
        if(xx>=x&&xx<x+w&&yy>=y&&yy<y+h)continue;
        if(dry(xx,yy,gRegionalSpots.terrace)&&!reached(xx,yy))return FALSE;
    }
    *count=carved;return TRUE;
}
bool8 regional_content_prepare_rect(int w,int h,RegionalContentRect* out) {
    int x,y,xx,yy,carved,best_carved=0,found=0;u32 best=0;
    if(regional_content_rect(w,h,out))return TRUE;
    if(!out||w<1||h<1||w>16||h>12||sRectCount>=4)return FALSE;
    for(y=2;y+h<=gRoom.h-2;y++)for(x=2;x+w<=gRoom.w-2;x++) {
        u32 score;if(!clearing_ok(x,y,w,h,&carved))continue;
        score=hash32(gGame.seed,x*811+y*3571+sCell*57+sArea*8911+w*53+h);
        if(!found||carved<best_carved||(carved==best_carved&&score>best)) {
            found=1;best=score;best_carved=carved;out->x=x;out->y=y;out->w=w;out->h=h;
        }
    }
    if(!found)return FALSE;
    for(yy=out->y;yy<out->y+h;yy++)for(xx=out->x;xx<out->x+w;xx++) {
        u16 ground=room_get(xx,yy),overlay=room_get_overlay(xx,yy);
        if(!dry(xx,yy,gRegionalSpots.terrace))room_set(xx,yy,roomgen_blighted(sCell)?MT_BLIGHT_FLOOR:MT_MOSS0+hash32(gGame.seed,xx+yy*37+sCell*409)%3);
        if(removable_wood(overlay))room_set_overlay(xx,yy,MT_NONE);
        /* Preserve every original ordinary-floor/path drawing. */
        (void)ground;
    }
    room_build_solid();
    for(y=1;y<gRoom.h-1;y++){for(x=1;x<gRoom.w-1;x++)if(reached(x,y)&&dry(x,y,gRegionalSpots.terrace))break;if(x<gRoom.w-1)break;}
    component(x,y,gRegionalSpots.terrace);take_rect(out);
#if BART_FOREST_VARIANT >= 31
    if(sArea==AREA_FOREST)forest_trees_plan();
#endif
    return TRUE;
}
static bool8 inside_rects(int x,int y) {
    int i;for(i=0;i<sRectCount;i++)if(x>=sRects[i].x&&x<sRects[i].x+sRects[i].w&&y>=sRects[i].y&&y<sRects[i].y+sRects[i].h)return TRUE;
    return FALSE;
}
bool8 regional_content_validate_routes(void) {
    int x,y,origin_x=-1,origin_y=-1;u32 old[ROOM_MAX_H];
    if(sArea!=AREA_FOREST&&sArea!=AREA_CREAM)return TRUE;
    memcpy(old,sReach,sizeof(old));
    for(y=1;y<gRoom.h-1&&origin_x<0;y++)for(x=1;x<gRoom.w-1;x++)
        if((sOriginalReach[y]&(1u<<x))&&!inside_rects(x,y)&&dry(x,y,gRegionalSpots.terrace)){origin_x=x;origin_y=y;break;}
    if(origin_x<0)return FALSE;
    component(origin_x,origin_y,gRegionalSpots.terrace);
    for(y=1;y<gRoom.h-1;y++)for(x=1;x<gRoom.w-1;x++)if((sOriginalReach[y]&(1u<<x))&&!inside_rects(x,y)&&!reached(x,y)) {
        memcpy(sReach,old,sizeof(old));memcpy(sComponents[gRegionalSpots.terrace],old,sizeof(old));return FALSE;
    }
    if((gRegionalSpots.has_door&&!regional_content_front_reachable(gRegionalSpots.door))||
       (gRegionalSpots.has_npc&&!regional_content_front_reachable(gRegionalSpots.npc))||
       (gRegionalSpots.has_cache&&!regional_content_front_reachable(gRegionalSpots.cache))) {
        memcpy(sReach,old,sizeof(old));memcpy(sComponents[gRegionalSpots.terrace],old,sizeof(old));return FALSE;
    }
    return TRUE;
}
bool8 regional_content_front_reachable(Spot p){return reached(p.x,p.y+1);}
static bool8 feature_rect(const RegionalContentDiscovery* record,int w,int h,bool8 clearing,RegionalContentRect* out) {
    if(record->mechanism.x>=w/2&&record->mechanism.y>=h/2&&
       rect_ok(record->mechanism.x-w/2,record->mechanism.y-h/2,w,h)) {
        RegionalContentRect old={record->mechanism.x-w/2,record->mechanism.y-h/2,w,h};
        *out=old;take_rect(&old);return TRUE;
    }
    return clearing?regional_content_prepare_rect(w,h,out):regional_content_rect(w,h,out);
}
static bool8 spawn_clear(Spot p,int terrace,bool8 broad,int spacing) {
    int x,y,i,r=broad?1:0;
    if(!dry(p.x,p.y,terrace))return FALSE;
    for(y=p.y-r;y<=p.y+r;y++)for(x=p.x-r;x<=p.x+r;x++)
        if(x<1||y<1||x>=gRoom.w-1||y>=gRoom.h-1||(sReserved[y]&(1u<<x)))return FALSE;
    for(y=p.y-r;y<=p.y+r;y++)for(x=p.x-r;x<=p.x+r;x++)if(!dry(x,y,terrace))return FALSE;
    for(i=0;i<sSpawnCount;i++)if(sSpawnTerrace[i]==terrace&&ABS(p.x-sAdmittedSpawns[i].x)+ABS(p.y-sAdmittedSpawns[i].y)<spacing)return FALSE;
    return TRUE;
}
static void spawn_component(int terrace,Spot origin) {
    int x=-1,y=-1,i;
    if(sComponentReady&(1u<<terrace))return;
    if(dry(origin.x,origin.y,terrace)){x=origin.x;y=origin.y;}
    if(x<0&&sArea==AREA_CREAM) {
        CreamTerraceSpots* part=&gCreamRoom.terrace[terrace];
        for(i=0;i<part->spawn_count;i++)if(dry(part->spawns[i].x,part->spawns[i].y,terrace)){x=part->spawns[i].x;y=part->spawns[i].y;break;}
    }
    if(x<0)for(y=1;y<gRoom.h-1;y++){for(x=1;x<gRoom.w-1;x++)if(dry(x,y,terrace))break;if(x<gRoom.w-1)break;}
    component(x,y,terrace);
    if(terrace!=gRegionalSpots.terrace)memcpy(sReach,sComponents[gRegionalSpots.terrace],sizeof(sReach));
}
static bool8 original_spawn(Spot p,int terrace) {
    int i,count;Spot* spots;
    if(sArea==AREA_CREAM){count=gCreamRoom.terrace[terrace].spawn_count;spots=gCreamRoom.terrace[terrace].spawns;}
    else {count=gSpots.spawn_count;spots=gSpots.spawns;}
    for(i=0;i<count;i++)if(spots[i].x==p.x&&spots[i].y==p.y&&!(sReserved[p.y]&(1u<<p.x)))return TRUE;
    return FALSE;
}
bool8 regional_content_spawn_point(int terrace,int ordinal,Spot* point) {
    int x,y,pass,found=0;u32 best=0;Spot chosen;
    if(!point)return FALSE;
    if(sArea!=AREA_FOREST&&sArea!=AREA_CREAM)return TRUE;
    if(sArea==AREA_FOREST)terrace=0;else terrace&=1;
    if(spawn_clear(*point,terrace,FALSE,1)){chosen=*point;found=1;}
    if(!found) {
        spawn_component(terrace,*point);
        for(pass=0;pass<2&&!found;pass++)for(y=2;y<gRoom.h-2;y++)for(x=2;x<gRoom.w-2;x++) {
            Spot candidate={(u8)x,(u8)y};u32 score;
            if(!(sComponents[terrace][y]&(1u<<x))||(sCore[y]&(1u<<x)))continue;
            if(sArea==AREA_FOREST&&sForestLandmarks[y]&(1u<<x))continue;
            if(original_spawn(candidate,terrace))continue;
            score=hash32(gGame.seed,sCell*7919+ordinal*4099+x*97+y*257+terrace*104729);
            if(found&&score<=best)continue;
            if(!spawn_clear(candidate,terrace,pass==0,pass==0?3:1))continue;
            found=1;best=score;chosen=candidate;
        }
    }
    if(!found)return FALSE;
    *point=chosen;
    if(sSpawnCount<24){sAdmittedSpawns[sSpawnCount]=chosen;sSpawnTerrace[sSpawnCount++]=terrace;}
    return TRUE;
}
void regional_content_place(int area,int cell) {
    RegionalContentPlan p;RegionalContentDiscovery* record;int at,x=-1,y=-1,i;
    bool8 courier=gHandoffState.quest.state==2&&gHandoffState.quest.kind==HQ_COURIER&&
        gHandoffState.quest.target_area==area&&gHandoffState.quest.target_cell==cell;
    Spot none={0,0};
    regional_content_clear();
    at=regional_content_index(area,cell);
    if(at<0||!regional_content_get(area,cell,&p))return;
    sArea=area;sCell=cell;gRegionalSpots.terrace=p.terrace;record=&gRegionalDiscovery[at];
    if(p.interior_site==RC_NONE&&!courier)return; /* no side events in entry/boss rooms */
    if(area==AREA_FOREST)for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        if(roomgen_content_reserved(x,y))sForestReserved[y]|=1u<<x;
        if(roomgen_content_landmark_reserved(x,y))sForestLandmarks[y]|=1u<<x;
    }
    x=y=-1;
    if(area==AREA_CREAM) {
        CreamTerraceSpots* part=&gCreamRoom.terrace[p.terrace];
        for(i=0;i<part->spawn_count;i++)if(dry(part->spawns[i].x,part->spawns[i].y,p.terrace)){x=part->spawns[i].x;y=part->spawns[i].y;break;}
    } else {
        for(i=0;i<gSpots.spawn_count;i++)if(dry(gSpots.spawns[i].x,gSpots.spawns[i].y,0)){x=gSpots.spawns[i].x;y=gSpots.spawns[i].y;break;}
        if(x<0)for(i=0;i<4;i++)if(gWorld.cells[cell].gate[i]!=GATE_WALL) {
            int px,py;roomgen_door_pos(i,&px,&py);
            if(dry(px/16,py/16,0)){x=px/16;y=py/16;break;}
        }
    }
    if(x<0)for(y=2;y<gRoom.h-2;y++){for(x=2;x<gRoom.w-2;x++)if(dry(x,y,p.terrace))break;if(x<gRoom.w-2)break;}
    component(x,y,p.terrace);
    memcpy(sOriginalReach,sReach,sizeof(sReach));
    if(area==AREA_CREAM) {
        /* Reserve the actual directed arrivals and departure lips, rather
           than excluding the entire lower bank where no ledge exists. */
        int n,j;
        for(n=0;n<CC_NODES;n++)for(j=0;j<cream_edge_count(n);j++) {
            const CreamEdge* edge=cream_edge(n,j);int px,py,facing;
            if(cream_cell(edge->target)==cell) {
                cream_room_arrival(n,edge,&px,&py,&facing);core_reserve(px/16-1,py/16-1,3,3);
            }
            if(cream_cell(n)==cell&&edge->kind==CC_DROP) {
                cream_room_drop_pos(n,j,&px,&py);core_reserve(px/16-1,py/16-1,3,3);
            }
        }
    }
    /* Large optional features get their coherent footprint before small
       incidental markers consume it. Givers remain outside the puzzle's
       permanent dry ring, and core geometry is never replaced wholesale. */
    if(p.quest_kind==HQ_BLOCKS&&feature_rect(record,7,7,TRUE,&gRegionalSpots.quest_rect)) {
        gRegionalSpots.mechanism.x=gRegionalSpots.quest_rect.x+3;
        gRegionalSpots.mechanism.y=gRegionalSpots.quest_rect.y+3;
    } else if(p.fusion_color==2&&feature_rect(record,5,5,TRUE,&gRegionalSpots.mechanism_rect)) {
        gRegionalSpots.has_mechanism=1;
    } else if(p.traversal_variant!=RC_NONE&&!p.quest_kind&&!p.has_wave&&p.fusion_color==RC_NONE&&
              feature_rect(record,6,5,TRUE,&gRegionalSpots.traversal_rect)) {
        gRegionalSpots.has_mechanism=1;
    } else if(p.field_mechanism_variant!=RC_NONE&&feature_rect(record,5,4,FALSE,&gRegionalSpots.mechanism_rect)) {
        gRegionalSpots.has_mechanism=1;
    }
    if(gRegionalSpots.has_mechanism) {
        RegionalContentRect* r=gRegionalSpots.traversal_rect.w?&gRegionalSpots.traversal_rect:&gRegionalSpots.mechanism_rect;
        gRegionalSpots.mechanism.x=r->x+r->w/2;gRegionalSpots.mechanism.y=r->y+r->h/2;
    }
    if(p.quest_kind||p.has_wave||p.fusion_color!=RC_NONE||courier) {
        gRegionalSpots.has_npc=choose_point(record->npc,1,0x4e504320u,&gRegionalSpots.npc);
        if(!gRegionalSpots.has_npc)gRegionalSpots.has_npc=compact_point(record->npc,&gRegionalSpots.npc);
    }
    if(p.interior_site!=RC_NONE&&(record->marks&RC_MARK_COMPACT_DOOR)) {
        gRegionalSpots.has_door=compact_point(record->door,&gRegionalSpots.door);gRegionalSpots.compact_door=gRegionalSpots.has_door;
    } else if(p.interior_site!=RC_NONE) {
        gRegionalSpots.has_door=choose_point(record->door,0,0x444f4f52u,&gRegionalSpots.door);
        if(!gRegionalSpots.has_door){gRegionalSpots.has_door=compact_point(record->door,&gRegionalSpots.door);gRegionalSpots.compact_door=gRegionalSpots.has_door;}
    }
    if(p.interior_site!=RC_NONE) {
        gRegionalSpots.has_cache=choose_point(record->cache,1,0x43414348u,&gRegionalSpots.cache);
        if(!gRegionalSpots.has_cache)gRegionalSpots.has_cache=compact_point(record->cache,&gRegionalSpots.cache);
    }
    record->marks=0;record->terrace=p.terrace;
    if(gRegionalSpots.has_door){record->door=gRegionalSpots.door;record->marks|=RC_MARK_DOOR;if(gRegionalSpots.compact_door)record->marks|=RC_MARK_COMPACT_DOOR;}
    if(gRegionalSpots.has_npc){record->npc=gRegionalSpots.npc;if(p.quest_kind||courier)record->marks|=RC_MARK_QUEST;if(p.has_wave)record->marks|=RC_MARK_WAVE;if(p.fusion_color!=RC_NONE)record->marks|=RC_MARK_FUSION;}
    if(gRegionalSpots.has_mechanism){record->mechanism=gRegionalSpots.mechanism;record->marks|=RC_MARK_MECHANISM;}
    if(p.quest_kind==HQ_BLOCKS&&gRegionalSpots.quest_rect.w)record->mechanism=gRegionalSpots.mechanism;
    if(gRegionalSpots.has_cache)record->cache=gRegionalSpots.cache;else record->cache=none;
}
u8 regional_content_marks(int area,int cell,RegionalContentDiscovery* out) {
    RegionalContentPlan p;int at=regional_content_index(area,cell);u8 marks,planned=0;
    if(at<0||!out||!regional_content_get(area,cell,&p))return 0;
    *out=gRegionalDiscovery[at];marks=out->marks;
    if(p.fusion_color!=RC_NONE&&(gHandoffState.fusion_flags&(1u<<p.fusion_color)))marks&=~RC_MARK_FUSION;
    if(gHandoffState.completed[p.field_site>>3]&(1u<<(p.field_site&7)))marks&=~RC_MARK_QUEST;
    if(!p.quest_kind&&!(gHandoffState.quest.kind==HQ_COURIER&&gHandoffState.quest.state==2&&
       gHandoffState.quest.target_area==area&&gHandoffState.quest.target_cell==cell))marks&=~RC_MARK_QUEST;
    if(p.fusion_color==0&&(gHandoffState.fusion_flags&1)&&!(gHandoffState.remaining[p.field_site]&(1u<<14))&&
       (out->cache.x||out->cache.y))marks|=RC_MARK_CACHE;
    if(gHandoffState.contract_state==1&&gHandoffState.contract_kind==HC_ITEM&&
       gHandoffState.contract_target==p.field_site&&(out->cache.x||out->cache.y))marks|=RC_MARK_CACHE;
    if(p.interior_site!=RC_NONE)planned|=RC_MARK_DOOR;
    if(p.quest_kind&&!(gHandoffState.completed[p.field_site>>3]&(1u<<(p.field_site&7))))planned|=RC_MARK_QUEST;
    if(p.has_wave)planned|=RC_MARK_WAVE;
    if(p.fusion_color!=RC_NONE&&!(gHandoffState.fusion_flags&(1u<<p.fusion_color)))planned|=RC_MARK_FUSION;
    planned|=marks&(RC_MARK_CACHE|RC_MARK_MECHANISM|RC_MARK_QUEST);
    out->marks=marks;return planned;
}
