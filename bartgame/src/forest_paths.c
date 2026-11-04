/* Native room trails join places instead of tracing every coarse-plan loop.
   This pass only substitutes ordinary zero-collision floor pictures. */
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT == 32
#include "forest_paths.h"
#include "room.h"
#include "roomgen.h"
#include "world.h"
#include "util.h"

#define PW FOREST_W
#define PH FOREST_H
#define PN (PW*PH)
#define NO_NODE 0xffff
#define PATH_MID 4
#define PATH_HIDDEN 8
#define PATH_BANK 16
#define ANCHOR_MAX 32

static u8 sOld[PN] EWRAM_BSS;
static u8 sChosen[PN] EWRAM_BSS;
static u8 sWalk[PN] EWRAM_BSS;
static u16 sHeap[PN] EWRAM_BSS;
static u16 sWhere[PN] EWRAM_BSS;
static u16 sDistance[PN] EWRAM_BSS;
static u16 sParent[PN] EWRAM_BSS;
static int sHeapSize;

static bool8 trail(u16 mt) {
    return mt==MT_PATH || (mt>=MT_PEDGE_1 && mt<=MT_PEDGE_F) ||
           (mt>=MT_PEDGE_C1 && mt<=MT_PEDGE_CF);
}

static bool8 ordinary_floor(u16 mt) {
    if(mt==MT_NONE || metatile_coll[mt] || metatile_type[mt]!=TT_FLOOR || metatile_prop[mt])return FALSE;
    return trail(mt) || (mt>=MT_MOSS0 && mt<=MT_MOSS2) || mt==MT_MOSS_SHADE ||
        mt==MT_MOSS_BLIGHT || mt==MT_MOSS_BLIGHT2 ||
        (mt>=MT_BLIGHT_GROUND0 && mt<=MT_BLIGHT_FLOOR) || mt==MT_BLIGHT_FLOOR2 ||
        (mt>=MT_FOREST_ROT0 && mt<=MT_FOREST_ROT7) ||
        (mt>=MT_SHORE_1 && mt<=MT_VERGE_F);
}

static u16 calm_floor(int cell,int x,int y) {
    if(roomgen_blighted(cell))return MT_BLIGHT_FLOOR;
    u32 h=hash32(gWorld.seed,cell*1237+x*53+y*193);
    return h%19==0 ? MT_MOSS1 : MT_MOSS0;
}

static bool8 better(int a,int b) {
    return sDistance[a]<sDistance[b] || (sDistance[a]==sDistance[b] && a<b);
}

static void heap_up(int at) {
    int q=sHeap[at];
    while(at>0) {
        int parent=(at-1)/2,n=sHeap[parent];
        if(!better(q,n))break;
        sHeap[at]=n;sWhere[n]=at;at=parent;
    }
    sHeap[at]=q;sWhere[q]=at;
}

static void heap_put(int q) {
    int at=sWhere[q];
    if(at==NO_NODE)at=sHeapSize++;
    sHeap[at]=q;sWhere[q]=at;heap_up(at);
}

static int heap_take(void) {
    int result=sHeap[0],q=sHeap[--sHeapSize],at=0;
    sWhere[result]=NO_NODE;
    if(!sHeapSize)return result;
    while(at*2+1<sHeapSize) {
        int child=at*2+1;
        if(child+1<sHeapSize && better(sHeap[child+1],sHeap[child]))child++;
        if(!better(sHeap[child],q))break;
        sHeap[at]=sHeap[child];sWhere[sHeap[at]]=at;at=child;
    }
    sHeap[at]=q;sWhere[q]=at;
    return result;
}

static int nearest_walk(int x,int y) {
    int dx,dy,best=-1,rank=9999;
    for(dy=-3;dy<=3;dy++)for(dx=-3;dx<=3;dx++) {
        int xx=x+dx,yy=y+dy;
        if(xx<1 || yy<2 || xx>=PW-1 || yy>=PH-1)continue;
        int q=yy*PW+xx,cost=(ABS(dx)+ABS(dy))*8+(sOld[q]?0:2);
        if(!sWalk[q] || cost>=rank)continue;
        rank=cost;best=q;
    }
    return best;
}

static void anchor(u16* nodes,int* count,int x,int y) {
    int q=nearest_walk(x,y),i;
    if(q<0 || *count>=ANCHOR_MAX)return;
    for(i=0;i<*count;i++)if(nodes[i]==q)return;
    nodes[(*count)++]=q;
}

/* Positive edge weights and a nearest-network stop create a tree of route
   connections. Old wear is preferred, but unused cycles are not painted. */
static bool8 connect(int start,const u8* path,int cell) {
    int i,found=-1;
    if(sChosen[start])return TRUE;
    for(i=0;i<PN;i++)sWhere[i]=sDistance[i]=sParent[i]=NO_NODE;
    sHeapSize=0;sDistance[start]=0;heap_put(start);
    while(sHeapSize) {
        int q=heap_take(),x=q%PW,y=q/PW,k;
        if(sChosen[q]){found=q;break;}
        /* Fixed native direction order keeps wear smooth and repeatable;
           a room hash rotates equal-cost choices without consuming RNG. */
        int first=hash32(gWorld.seed,cell*79)&3;
        static const s8 step[4][2]={{0,-1},{1,0},{0,1},{-1,0}};
        for(k=0;k<4;k++) {
            int direction=(k+first)&3,xx=x+step[direction][0],yy=y+step[direction][1];
            if(xx<1 || yy<2 || xx>=PW-1 || yy>=PH-1)continue;
            int next=yy*PW+xx;
            if(!sWalk[next])continue;
            int weight=sOld[next]?2:5;
            if(path[next]&PATH_HIDDEN)weight+=7;
            int previous=sParent[q];
            if(previous!=NO_NODE && (previous-q)!=(q-next))weight++;
            int distance=sDistance[q]+weight;
            if(distance>=sDistance[next])continue;
            sDistance[next]=distance;sParent[next]=q;heap_put(next);
        }
    }
    if(found<0)return FALSE;
    /* Parents point towards the new anchor. The final existing-network
       endpoint is kept, and every added floor cell is an actual route. */
    for(i=found;i!=NO_NODE;i=sParent[i])sChosen[i]=1;
    return TRUE;
}

void forest_paths_refine(int cell,u8* path) {
    const Cell* c=&gWorld.cells[cell];
    u16 nodes[ANCHOR_MAX];
    int count=0,x,y,i;
    memset(sOld,0,sizeof(sOld));memset(sChosen,0,sizeof(sChosen));memset(sWalk,0,sizeof(sWalk));
    for(y=2;y<PH-1;y++)for(x=1;x<PW-1;x++) {
        int q=y*PW+x;
        u16 mt=room_get(x,y),ov=room_get_overlay(x,y);
        sOld[q]=trail(mt);
        bool8 clear=mt!=MT_NONE && !metatile_coll[mt] &&
            (metatile_type[mt]==TT_FLOOR || metatile_type[mt]==TT_SLOW || metatile_type[mt]==TT_DOOR_OPEN) &&
            (ov==MT_NONE || !metatile_coll[ov]);
        sWalk[q]=clear;
        if(gSpots.has_npc && x==gSpots.npc.x && y==gSpots.npc.y)sWalk[q]=0;
    }
    for(i=0;i<4;i++)if(c->gate[i]!=GATE_WALL) {
        int xx=i==SIDE_W?2:i==SIDE_E?PW-3:PW/2;
        int yy=i==SIDE_N?3:i==SIDE_S?PH-3:PH/2;
        if((path[yy*PW+xx]&PATH_HIDDEN) && count)continue;
        anchor(nodes,&count,xx,yy);
    }
    /* Each actual crossing owns both bank approaches, even when the road
       to another optional feature is deliberately withheld. */
    for(y=2;y<PH-1;y++)for(x=1;x<PW-1;x++) {
        u16 mt=room_get(x,y);
        if(mt==MT_BRIDGE && room_get(x-1,y)!=mt) {
            int end=x;while(room_get(end+1,y)==mt)end++;
            anchor(nodes,&count,x-1,y);anchor(nodes,&count,end+1,y);
        } else if(mt==MT_BRIDGE_V && room_get(x,y-1)!=mt) {
            int end=y;while(room_get(x,end+1)==mt)end++;
            anchor(nodes,&count,x,y-1);anchor(nodes,&count,x,end+1);
        }
    }
    u32 cue=hash32(gWorld.seed,cell*193+7741);
    if(gSpots.has_mouth)anchor(nodes,&count,gSpots.mouth.x,gSpots.mouth.y+1);
    if(gSpots.has_npc)anchor(nodes,&count,gSpots.npc.x,gSpots.npc.y+1);
    if(gSpots.has_chest && (cue&3))anchor(nodes,&count,gSpots.chest.x,gSpots.chest.y+1);
    if(gSpots.has_shrine && (cue&4))anchor(nodes,&count,gSpots.shrine.x,gSpots.shrine.y+1);
    /* The dais survives collection; its remembered route must survive too. */
    if((gSpots.has_relic || c->role==ROLE_RELIC) && (cue&8))anchor(nodes,&count,gSpots.relic.x,gSpots.relic.y+1);
    if(gSpots.has_boss)anchor(nodes,&count,gSpots.boss.x,gSpots.boss.y+2);
    if(!count)return;
    sChosen[nodes[0]]=1;
    for(i=1;i<count;i++)connect(nodes[i],path,cell);
    for(y=2;y<PH-1;y++)for(x=1;x<PW-1;x++) {
        int q=y*PW+x;u16 mt=room_get(x,y);
        bool8 show=sChosen[q] && !(path[q]&PATH_HIDDEN);
        if(trail(mt) && !show)room_set(x,y,calm_floor(cell,x,y));
        else if(show && ordinary_floor(mt))room_set(x,y,MT_PATH);
        /* Transparent furniture must not reveal a discarded road rectangle. */
        if(trail(gRoom.underlay[q]) && !show)gRoom.underlay[q]=calm_floor(cell,x,y);
        path[q]&=PATH_BANK|PATH_HIDDEN;
        if(show || (path[q]&PATH_BANK))path[q]|=PATH_MID;
    }
}
#endif
