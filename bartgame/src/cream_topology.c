/* Room-local mountain topology. The two graph nodes remain progression
   components; each component can contain several real collision terraces. */
#include "cream_topology.h"
#include "room.h"
#include "util.h"
#include "actor.h"

CreamTopology gCreamTopology EWRAM_BSS;
static u8 sBaseMask[CREAM_TOPO_CELLS] EWRAM_BSS;

static const u16 sFloor[3][4]={
 {MT_CREAM_FLOOR_S0_V0,MT_CREAM_FLOOR_S0_V1,MT_CREAM_FLOOR_S0_V2,MT_CREAM_FLOOR_S0_V3},
 {MT_CREAM_FLOOR_S1_V0,MT_CREAM_FLOOR_S1_V1,MT_CREAM_FLOOR_S1_V2,MT_CREAM_FLOOR_S1_V3},
 {MT_CREAM_FLOOR_S2_V0,MT_CREAM_FLOOR_S2_V1,MT_CREAM_FLOOR_S2_V2,MT_CREAM_FLOOR_S2_V3}
};
static const u16 sWall[3]={MT_CREAM_CLIFF_MID_S0_V0,MT_CREAM_CLIFF_MID_S1_V0,MT_CREAM_CLIFF_MID_S2_V0};
static const u16 sRim[3]={MT_CREAM_RIM_S0,MT_CREAM_RIM_S1,MT_CREAM_RIM_S2};
static const u16 sClimb[3]={MT_CREAM_CLIMB_MID_S0,MT_CREAM_CLIMB_MID_S1,MT_CREAM_CLIMB_MID_S2};
static const u16 sDrop[3]={MT_CREAM_DROP_S0,MT_CREAM_DROP_S1,MT_CREAM_DROP_S2};

static bool8 inside(int x,int y) {return x>=0&&y>=0&&x<CREAM_ROOM_W&&y<CREAM_ROOM_H;}
static int index_at(int x,int y) {return y*CREAM_ROOM_W+x;}
static int owner_of(u8 c) {return !!(c&CT_UPPER);}
static u32 variation(int cell,int salt) {return hash32(gCreamWorld.seed^0x7EAA531Du,cell*719+salt);}
static void reserve(CreamTopology* p,int x0,int y0,int x1,int y1) {
    int x,y;
    for(y=MAX(0,y0);y<=MIN(23,y1);y++)for(x=MAX(0,x0);x<=MIN(31,x1);x++)p->cells[index_at(x,y)]|=CT_RESERVED;
}
static bool8 has_kind(int cell,int t,int kind) {
    int n=cream_node(cell,t),i;
    for(i=0;i<cream_edge_count(n);i++)if(cream_edge(n,i)->kind==kind)return TRUE;
    return FALSE;
}
static void mark_features(CreamTopology* p,const CreamRoomInfo* info) {
    static const u8 flags[5]={CC_CONTENT_CHEST,CC_CONTENT_NPC,CC_CONTENT_HEAL,CC_CONTENT_CACHE,CC_CONTENT_MISSION};
    int t,i,x;
    reserve(p,0,0,3,23);reserve(p,28,0,31,23);
    reserve(p,0,0,31,0);reserve(p,0,23,31,23);
    /* A local plateau cannot attach to the high side of a gated shaft. */
    reserve(p,info->climb_x-1,0,info->climb_x+2,23);
    for(t=0;t<2;t++) {
        const CreamTerraceSpots* sp=&info->terrace[t];
        const Spot* points[5]={&sp->chest,&sp->npc,&sp->heal,&sp->cache,&sp->mission};
        int n=cream_node(info->cell,t);
        for(i=0;i<5;i++)if(sp->content&flags[i])reserve(p,points[i]->x-2,points[i]->y-2,points[i]->x+2,points[i]->y+2);
        if(sp->content&CC_CONTENT_ENTRY)reserve(p,info->return_door.x-2,info->return_door.y-3,info->return_door.x+3,info->return_door.y+2);
        if(has_kind(info->cell,t,CC_CAVE))reserve(p,4,(t==CC_UPPER?6:19)-3,9,(t==CC_UPPER?6:19)+3);
        for(i=0;i<cream_edge_count(n);i++) {
            const CreamEdge* edge=cream_edge(n,i);
            if(edge->kind==CC_DROP) {
                x=t==CC_LOWER?info->climb_x:(edge->flags&CC_LONG_DROP)?27:10;
                /* Keep the entire visible fall shaft, not merely takeoff. */
                reserve(p,x-1,0,x+2,23);
            }
        }
    }
    for(x=3;x<29;x+=5) {
        int y=info->lower_top[x];
        u32 n=hash32(gCreamWorld.seed^0xC0AD1234u,(info->cell+1)*977+x*37+y*97);
        if((n&3)==0&&ABS(x-info->climb_x)>3)reserve(p,x,y,x,y);
    }
    {
        int lower=cream_node(info->cell,CC_LOWER),upper=lower+1,i=cream_find_edge(lower,upper);
        if(i>=0&&cream_edge(lower,i)->kind==CC_CLIMB) {
            int y=info->lower_top[info->climb_x]+1;
            reserve(p,info->climb_x+2,y-1,info->climb_x+4,y+1);
        }
    }
    /* Actual incoming routes retain dry supported arrivals and approaches. */
    for(t=0;t<CC_NODES;t++)for(i=0;i<cream_edge_count(t);i++) {
        const CreamEdge* edge=cream_edge(t,i);int px,py,facing;
        if(cream_cell(edge->target)!=info->cell)continue;
        cream_room_arrival(t,edge,&px,&py,&facing);
        reserve(p,(px>>4)-1,(py>>4)-2,(px>>4)+1,(py>>4)+1);
    }
}

static int room_capacity(const CreamRoomInfo* info,int owner) {
    u8 content=info->terrace[owner].content;
    int n=0;
    if(content&CC_CONTENT_BOSS)return 0;
    if(content&CC_CONTENT_ENEMIES)return CREAM_SPAWN_MAX;
    if(content&CC_CONTENT_CHEST)n++;
    if(content&CC_CONTENT_NPC)n++;
    if(content&CC_CONTENT_HEAL)n++;
    if(content&CC_CONTENT_CACHE)n++;
    if(content&CC_CONTENT_MISSION)n++;
    return n;
}
static int owner_platforms(const CreamTopology* p,int owner) {
    int i,n=0;for(i=0;i<p->platforms;i++)n+=p->platform[i].owner==owner;return n;
}
static bool8 empty_wall(const CreamTopology* p,int x,int y) {
    return inside(x,y)&&!(p->cells[index_at(x,y)]&(CT_SUPPORT|CT_RESERVED));
}
static bool8 source_floor(const CreamTopology* p,int x,int y,int owner) {
    u8 c;
    if(!inside(x,y))return FALSE;
    c=p->cells[index_at(x,y)];
    return (c&CT_SUPPORT)&&!(c&(CT_CLIMB|CT_RESERVED|CT_DROP))&&owner_of(c)==owner&&(c&7)!=7;
}
static bool8 box_clear(const CreamTopology* p,int x,int y,int w,int h) {
    int dx,dy;
    if(x<4||x+w>28||y<1||y+h>23)return FALSE;
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++)if(!empty_wall(p,x+dx,y+dy))return FALSE;
    /* Every change of elevation has a real solid face. No invisible step. */
    for(dy=-1;dy<=h;dy++)for(dx=-1;dx<=w;dx++) {
        if(dx>=0&&dx<w&&dy>=0&&dy<h)continue;
        if(inside(x+dx,y+dy)&&(p->cells[index_at(x+dx,y+dy)]&CT_SUPPORT))return FALSE;
    }
    return TRUE;
}

static void record_drop(CreamTopology* p,int owner,int x,int source_y,int target_y) {
    CreamTopologyDrop* drop;int source_h,target_h,dx;
    if(p->drops>=CREAM_TOPO_LINK_MAX || source_y>=target_y)return;
    source_h=p->cells[index_at(x,source_y)]&7;target_h=p->cells[index_at(x,target_y)]&7;
    if(source_h<=target_h)return;
    for(dx=0;dx<2;dx++) {
        u8 c=p->cells[index_at(x+dx,source_y)],end=p->cells[index_at(x+dx,target_y)];
        if(!(c&CT_SUPPORT)||(c&(CT_CLIMB|CT_RESERVED))||owner_of(c)!=owner ||
           !(end&CT_SUPPORT)||(end&(CT_CLIMB|CT_RESERVED))||owner_of(end)!=owner)return;
    }
    drop=&p->drop[p->drops++];drop->x=x*16+16;drop->y=source_y*16+14;
    drop->landing_x=x*16+16;drop->landing_y=target_y*16+14;
    drop->owner=owner;drop->height=MIN(255,drop->landing_y-drop->y);
    for(dx=0;dx<2;dx++)p->cells[index_at(x+dx,source_y)]|=CT_DROP;
}

/* An attached shelf is carved only from unused rock. The connecting grip
   strip reaches same-owner floor and cannot contact another macrocomponent. */
static bool8 spur(CreamTopology* p,const CreamRoomInfo* info,int x,int y,int w,int h,int owner,bool8 parent_above,int hand) {
    int ax,source=-1,r,dx,dy,source_h,height,top,bottom;
    CreamTopologyPlatform* platform;CreamTopologyClimb* climb;
    if(p->platforms>=CREAM_TOPO_LINK_MAX||p->climbs>=CREAM_TOPO_LINK_MAX ||
       owner_platforms(p,owner)>=room_capacity(info,owner)||!box_clear(p,x,y,w,h))return FALSE;
    if(!(info->terrace[owner].content&CC_CONTENT_ENEMIES)&&h<2)return FALSE;
    ax=hand?x+w-2:x;
    for(r=parent_above?y-1:y+h;r>=1&&r<23;r+=parent_above?-1:1) {
        if(ABS(r-(parent_above?y:y+h-1))>5)break;
        if(source_floor(p,ax,r,owner)&&source_floor(p,ax+1,r,owner)){source=r;break;}
        if(!empty_wall(p,ax,r)||!empty_wall(p,ax+1,r))break;
    }
    if(source<0||ABS(source-(parent_above?y:y+h-1))<2)return FALSE;
    source_h=p->cells[index_at(ax,source)]&7;
    if((p->cells[index_at(ax+1,source)]&7)!=source_h)return FALSE;
    height=source_h+(parent_above?-1:1);
    if(height<0||height>6)return FALSE;
    top=parent_above?source+1:y+h;bottom=parent_above?y-1:source-1;
    for(r=top;r<=bottom;r++)for(dx=-1;dx<=2;dx++) {
        u8 c=p->cells[index_at(ax+dx,r)];
        if(c&CT_SUPPORT)return FALSE;
        if(dx>=0&&dx<2&&(c&CT_RESERVED))return FALSE;
    }
    platform=&p->platform[p->platforms++];
    *platform=(CreamTopologyPlatform){x,y,w,h,owner,height,0};
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++)p->cells[index_at(x+dx,y+dy)]=CT_SUPPORT|(owner?CT_UPPER:0)|height;
    climb=&p->climb[p->climbs++];
    *climb=(CreamTopologyClimb){ax,top,bottom,owner,parent_above?source_h:height,parent_above?height:source_h};
    for(r=top;r<=bottom;r++)for(dx=0;dx<2;dx++)p->cells[index_at(ax+dx,r)]=CT_SUPPORT|CT_CLIMB|(owner?CT_UPPER:0)|height;
    p->max_height=MAX(p->max_height,height);
    /* The opposite shoulder is a real downward alternative, not fake lips
       scattered around the entire boundary. Two columns remain for grips. */
    if(w>=4) {
        int drop_x=hand?x:x+w-2;
        if(parent_above)record_drop(p,owner,drop_x,source,y+h-1);
        else record_drop(p,owner,drop_x,y+h-1,source);
    }
    return TRUE;
}

/* A raised mesa interrupts a broad floor without disconnecting its exterior:
   an extra one-cell clear ring remains outside every solid retaining face. */
static bool8 mesa(CreamTopology* p,const CreamRoomInfo* info,int x,int y,int w,int h,int owner,int hand) {
    int dx,dy,base_h=-1,height,ax=hand?x+w-2:x;
    CreamTopologyPlatform* platform;CreamTopologyClimb* climb;
    if(p->platforms>=CREAM_TOPO_LINK_MAX||p->climbs>=CREAM_TOPO_LINK_MAX ||
       owner_platforms(p,owner)>=room_capacity(info,owner)||x<5||x+w>27||y<3||y+h>21)return FALSE;
    if(!(info->terrace[owner].content&CC_CONTENT_ENEMIES)&&h<2)return FALSE;
    for(dy=-2;dy<=h+1;dy++)for(dx=-2;dx<=w+1;dx++) {
        u8 c=p->cells[index_at(x+dx,y+dy)];
        if(!(c&CT_SUPPORT)||(c&(CT_CLIMB|CT_RESERVED|CT_DROP))||owner_of(c)!=owner)return FALSE;
        if(base_h<0)base_h=c&7;
        else if((c&7)!=base_h)return FALSE;
    }
    height=base_h+1;if(height>6)return FALSE;
    for(dy=-1;dy<=h;dy++)for(dx=-1;dx<=w;dx++)
        p->cells[index_at(x+dx,y+dy)]=(owner?CT_UPPER:0)|height;
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++)p->cells[index_at(x+dx,y+dy)]=CT_SUPPORT|(owner?CT_UPPER:0)|height;
    platform=&p->platform[p->platforms++];*platform=(CreamTopologyPlatform){x,y,w,h,owner,height,0};
    climb=&p->climb[p->climbs++];*climb=(CreamTopologyClimb){ax,y+h,y+h,owner,height,base_h};
    for(dx=0;dx<2;dx++)p->cells[index_at(ax+dx,y+h)]=CT_SUPPORT|CT_CLIMB|(owner?CT_UPPER:0)|height;
    p->max_height=MAX(p->max_height,height);
    if(w>=4)record_drop(p,owner,hand?x:x+w-2,y+h-1,y+h+1);
    return TRUE;
}

static Spot* feature(CreamTerraceSpots* sp,int flag) {
    if(flag==CC_CONTENT_MISSION)return &sp->mission;
    if(flag==CC_CONTENT_CHEST)return &sp->chest;
    if(flag==CC_CONTENT_NPC)return &sp->npc;
    if(flag==CC_CONTENT_HEAL)return &sp->heal;
    return &sp->cache;
}
static void base_spawns(CreamRoomInfo* info,const u8* mask) {
    static const u8 sx[CREAM_SPAWN_MAX]={11,17,27,4,21,14};int t,i;
    for(t=0;t<2;t++) {
        CreamTerraceSpots* sp=&info->terrace[t];int y=t==CC_UPPER?6:19;
        sp->spawn_count=0;
        if(sp->content&CC_CONTENT_BOSS){sp->spawns[0]=(Spot){16,8};sp->spawn_count=1;continue;}
        for(i=0;i<CREAM_SPAWN_MAX;i++) {
            int x=sx[(i+(info->cell%3))%CREAM_SPAWN_MAX];
            if((x>=info->climb_x-1&&x<=info->climb_x+2)||x==24||x==25||
               ((sp->content&CC_CONTENT_MISSION)&&ABS(x-sp->mission.x)<2))continue;
            if(x==4&&has_kind(info->cell,t,CC_CAVE))continue;
            if((sp->content&CC_CONTENT_CACHE)&&!(sp->content&CC_CONTENT_CHEST)&&x==sp->cache.x&&y==sp->cache.y)continue;
            if(mask[index_at(x,y)]==t+1)sp->spawns[sp->spawn_count++]=(Spot){x,y};
        }
    }
}
static void reserve_new(CreamTopology* p) {
    int i;
    for(i=0;i<p->platforms;i++) {
        CreamTopologyPlatform* platform=&p->platform[i];
        reserve(p,platform->x-1,platform->y-1,platform->x+platform->w,platform->y+platform->h);
    }
    for(i=0;i<p->climbs;i++) {
        CreamTopologyClimb* c=&p->climb[i];reserve(p,c->x-1,c->top-1,c->x+2,c->bottom+1);
    }
    for(i=0;i<p->drops;i++) {
        CreamTopologyDrop* d=&p->drop[i];int x=d->x/16-1;
        reserve(p,x-1,d->y/16-1,x+2,d->landing_y/16+1);
    }
}
static void populate(CreamTopology* p,CreamRoomInfo* info) {
    static const u8 flags[5]={CC_CONTENT_MISSION,CC_CONTENT_CHEST,CC_CONTENT_HEAL,CC_CONTENT_NPC,CC_CONTENT_CACHE};
    u8 moved[2]={0,0},enemy_index[2]={0,0};int i,j;
    for(i=0;i<p->platforms;i++) {
        CreamTopologyPlatform* platform=&p->platform[i];int owner=platform->owner;
        CreamTerraceSpots* sp=&info->terrace[owner];
        if(platform->h>=2)for(j=0;j<5;j++) {
            int flag=flags[j],point_x,attempt;Spot* point;
            if(!(sp->content&flag)||(moved[owner]&flag)||(flag==CC_CONTENT_CHEST&&platform->w<4))continue;
            point_x=-1;
            for(attempt=0;attempt<platform->w-(flag==CC_CONTENT_CHEST);attempt++) {
                int cx=platform->x+platform->w-(flag==CC_CONTENT_CHEST?2:1)-attempt,k,clear=1;
                for(k=0;k<(flag==CC_CONTENT_CHEST?2:1);k++)
                    if(p->cells[index_at(cx+k,platform->y-1)]&CT_CLIMB)clear=0;
                if(clear){point_x=cx;break;}
            }
            if(point_x<0)continue;
            point=feature(sp,flag);
            point->x=point_x;
            point->y=platform->y;
            moved[owner]|=flag;platform->content=flag;break;
        }
        if(!platform->content&&(sp->content&CC_CONTENT_ENEMIES)) {
            int slot=enemy_index[owner]++,x=platform->x+platform->w/2,y=platform->y+platform->h-1;
            if(slot>=CREAM_SPAWN_MAX)slot=CREAM_SPAWN_MAX-1;
            sp->spawns[slot]=(Spot){x,y};sp->spawn_count=MAX(sp->spawn_count,slot+1);
            platform->content=CC_CONTENT_ENEMIES;
        }
        /* A nonenemy node has a bounded number of movable content features.
           Its platform capacity was checked before carving a new perch. */
    }
    reserve_new(p);
    /* Existing ground enemies displaced by a retaining face choose nearby
       same-component floor; their count and enemy family are unchanged. */
    for(i=0;i<2;i++)for(j=0;j<info->terrace[i].spawn_count;j++) {
        Spot* sp=&info->terrace[i].spawns[j];u8 c=p->cells[index_at(sp->x,sp->y)];int r,x,y,found=0;
        if((c&CT_SUPPORT)&&!(c&CT_CLIMB)&&owner_of(c)==i)continue;
        for(r=1;r<12&&!found;r++)for(y=MAX(1,sp->y-r);y<=MIN(22,sp->y+r)&&!found;y++)for(x=MAX(4,sp->x-r);x<=MIN(27,sp->x+r);x++) {
            c=p->cells[index_at(x,y)];
            if((c&CT_SUPPORT)&&!(c&(CT_CLIMB|CT_DROP|CT_RESERVED))&&owner_of(c)==i) {*sp=(Spot){x,y};found=1;break;}
        }
    }
}

/* Content moves after geometry is measured. A chest can therefore occupy
   a formerly dry jump shoulder, especially when it shifts away from a grip.
   Keep map arrows and playable drops identical by checking the final pure
   content footprints before retaining an optional descending connection. */
static bool8 drop_content_clear(const CreamRoomInfo* info,int owner,int x,int y) {
    const CreamTerraceSpots* sp=&info->terrace[owner];
    if((sp->content&CC_CONTENT_CHEST) && x>=sp->chest.x && x<=sp->chest.x+1 &&
       y>=sp->chest.y-1 && y<=sp->chest.y)return FALSE;
    if((sp->content&CC_CONTENT_MISSION) && x==sp->mission.x && y==sp->mission.y)return FALSE;
    if((sp->content&CC_CONTENT_HEAL) && x==sp->heal.x && y==sp->heal.y)return FALSE;
    if((sp->content&CC_CONTENT_NPC) && x==sp->npc.x && y==sp->npc.y)return FALSE;
    if((sp->content&CC_CONTENT_CACHE) && !(sp->content&CC_CONTENT_CHEST) &&
       x==sp->cache.x && y==sp->cache.y)return FALSE;
    return TRUE;
}

static void prune_content_drops(CreamTopology* p,const CreamRoomInfo* info,const u8* mask) {
    int i,dx,kept=0;
    for(i=0;i<p->drops;i++) {
        CreamTopologyDrop d=p->drop[i];
        int sx=d.x/16-1,sy=d.y/16,lx=d.landing_x/16-1,ly=d.landing_y/16,clear=1;
        for(dx=0;dx<2;dx++) {
            u8 start=p->cells[index_at(sx+dx,sy)],end=p->cells[index_at(lx+dx,ly)];
            if(!(start&CT_SUPPORT)||!(end&CT_SUPPORT)||(start&CT_CLIMB)||(end&CT_CLIMB)||
               owner_of(start)!=d.owner||owner_of(end)!=d.owner||(start&7)<=(end&7)||
               !drop_content_clear(info,d.owner,sx+dx,sy)||
               !drop_content_clear(info,d.owner,lx+dx,ly))clear=0;
        }
        if(clear)p->drop[kept++]=d;
    }
    p->drops=kept;
    for(i=kept;i<CREAM_TOPO_LINK_MAX;i++)memset(&p->drop[i],0,sizeof(p->drop[i]));
    for(i=0;i<CREAM_TOPO_CELLS;i++)if(mask[i]!=5)p->cells[i]&=~CT_DROP;
    for(i=0;i<kept;i++) {
        int x=p->drop[i].x/16-1,y=p->drop[i].y/16;
        for(dx=0;dx<2;dx++)p->cells[index_at(x+dx,y)]|=CT_DROP;
    }
}

static void construct(int cell,CreamRoomInfo* info,CreamTopology* p,const u8* mask) {
    int x,y,i,target,attempt,archetype;u32 seed=variation(cell,0x71);
    memset(p,0,sizeof(*p));p->cell=cell;p->max_height=4;
    archetype=seed%CT_PEAK_ARENA;
    if(cream_cell(gCreamWorld.goal_node)==cell)archetype=CT_PEAK_ARENA;
    p->archetype=archetype;
    base_spawns(info,mask);
    for(y=0;y<24;y++)for(x=0;x<32;x++) {
        int at=index_at(x,y),m=mask[at],owner=(m==2)||(m!=1&&y<((info->upper_bottom[x]+info->lower_top[x])/2));
        u8 c=(owner?CT_UPPER:0)|(owner?4:0);
        if(m>=1&&m<=5)c|=CT_SUPPORT;
        if(m==3)c=(owner?CT_UPPER:0)|7|CT_SUPPORT|CT_CLIMB;
        if(m==5)c|=CT_DROP;
        if(m==6)c|=CT_RESERVED;
        p->cells[at]=c;
    }
    mark_features(p,info);
    if(archetype==CT_PEAK_ARENA){p->active=1;return;}
    target=archetype==CT_OPEN_SHELF?1:archetype==CT_NARROW_SPURS||archetype==CT_DOUBLE_RIDGE?4:3;
    /* Broad rooms may receive an enclosed raised mesa first. The uniform
       remaining exterior ring guarantees that this cannot strand a route. */
    if(archetype==CT_BROKEN_MESA||archetype==CT_DOUBLE_RIDGE||archetype==CT_HIGH_GROTTO)
        for(attempt=0;attempt<48&&p->platforms<2;attempt++) {
            u32 n=variation(cell,attempt*17+0x941);
            int owner=archetype==CT_HIGH_GROTTO?CC_UPPER:CC_LOWER;
            x=5+n%19;y=owner==CC_UPPER?4:17;
            mesa(p,info,x,y,3+((n>>8)&1),1+((n>>10)&1),owner,(n>>11)&1);
        }
    /* First pass favors roomy useful central shelves; later passes supply
       narrow stepping ledges only where that actual measured rock fits. */
    for(attempt=0;attempt<160&&p->platforms<target;attempt++) {
        u32 n=variation(cell,attempt*31+0x3151);
        int owner=((n>>7)&1),above=owner==CC_UPPER;
        int w=attempt<96?4+(n>>10)%3:3+(n>>10)%3;
        int h=attempt<112?2:1;
        x=4+n%22;y=9+(n>>15)%5;
        /* These two families intentionally chain elevations. They are not
           different names for the same independent shelf scatter. */
        if(archetype==CT_FOLDED_STAIR&&attempt<112) {
            if(!p->platforms){owner=CC_UPPER;above=TRUE;y=10;h=2;w=4+((n>>10)&1);}
            else if(p->platforms==1) {
                owner=CC_UPPER;above=TRUE;y=13;h=1;w=3;
                x=p->platform[0].x+((n>>9)&1);
            } else {owner=CC_LOWER;above=FALSE;y=11;h=2;}
        } else if(archetype==CT_SWITCHBACK&&attempt<112) {
            owner=CC_LOWER;above=FALSE;w=3+((n>>10)&1);h=1;
            if(!p->platforms)y=13;
            else if(p->platforms==1){y=10;x=p->platform[0].x+((n>>9)&1);}
            else {owner=CC_UPPER;above=FALSE;y=1;h=2;}
        }
        if(archetype==CT_NARROW_SPURS&&attempt>48){w=3+((n>>10)&1);h=1+((n>>12)&1);}
        spur(p,info,x,y,w,h,owner,above,(n>>17)&1);
    }
    /* High grotto and folded stair can climb into the otherwise unused rear
       mass. Those perches differ from an extra horizontal band mid-room. */
    if(archetype!=CT_OPEN_SHELF)for(attempt=0;attempt<64&&p->platforms<target;attempt++) {
        u32 n=variation(cell,attempt*43+0xD31);
        x=4+n%22;y=1+((n>>8)&1);
        spur(p,info,x,y,3+((n>>12)&1),1+((n>>13)&1),CC_UPPER,FALSE,(n>>16)&1);
    }
    populate(p,info);
    prune_content_drops(p,info,mask);
    /* Moved feature sites become available to later regional furniture.
       Rebuild reservations from final points rather than keeping ghost sites. */
    for(i=0;i<CREAM_TOPO_CELLS;i++)p->cells[i]&=~CT_RESERVED;
    for(i=0;i<CREAM_TOPO_CELLS;i++)if(mask[i]==6)p->cells[i]|=CT_RESERVED;
    mark_features(p,info);reserve_new(p);p->active=1;
}

void cream_topology_prepare(void) {memset(&gCreamTopology,0,sizeof(gCreamTopology));}

void cream_topology_preview(int cell,CreamRoomInfo* info,CreamTopology* out) {
    CreamRoomInfo local;
    if(!info)info=&local;
    if(!out)return;
    cream_room_preview(CLAMP(cell,0,24),info,sBaseMask);
    construct(info->cell,info,out,sBaseMask);
}

void cream_topology_apply(void) {
    CreamRoomInfo old=gCreamRoom,planned;int x,y,s=MIN(gCreamRoom.stage,2);
    cream_topology_preview(gCreamRoom.cell,&planned,&gCreamTopology);
    gCreamRoom=planned;
    for(y=1;y<23;y++)for(x=4;x<28;x++) {
        int at=index_at(x,y),old_kind=sBaseMask[at];u8 c=gCreamTopology.cells[at];
        bool8 was=old_kind>=1&&old_kind<=5,now=(c&CT_SUPPORT)!=0;
        if(c&CT_CLIMB) {
            if((c&7)!=7)room_set(x,y,sClimb[s]);
        } else if(!was&&now) {
            u32 n=variation(gCreamRoom.cell,x*37+y*97);
            room_set(x,y,sFloor[s][(n&7)<5?0:1+((n>>5)%3)]);
        } else if(was&&!now) {
            room_set(x,y,sWall[s]);
        }
        if((c&CT_DROP)&&!(old_kind==5))room_set(x,y,sDrop[s]);
    }
    /* New shelf fronts have a physical face, including where original solid
       backing did not need a rim before this platform existed. */
    for(int i=0;i<gCreamTopology.platforms;i++) {
        CreamTopologyPlatform* p=&gCreamTopology.platform[i];
        int fy=p->y+p->h;
        for(x=p->x;x<p->x+p->w;x++)if(!(gCreamTopology.cells[index_at(x,fy)]&CT_SUPPORT))room_set(x,fy,sRim[s]);
    }
    cream_room_relocate_features(&old);
}

void cream_topology_sync(void) {
    int x,y;
    if(!gCreamTopology.active||gCreamTopology.cell!=gCreamRoom.cell)return;
    for(y=0;y<24;y++)for(x=0;x<32;x++) {
        int at=index_at(x,y);u16 mt=room_get(x,y),overlay=room_get_overlay(x,y);u8 c=gCreamTopology.cells[at];
        bool8 open=mt<METATILE_COUNT&&metatile_coll[mt]==0&&
            (metatile_type[mt]==TT_FLOOR||metatile_type[mt]==TT_CLIMB||metatile_type[mt]==TT_MYST);
        if(overlay!=MT_NONE&&metatile_coll[overlay])open=FALSE;
        if(!open){gCreamTopology.cells[at]=c&~CT_SUPPORT;continue;}
        if(!(c&CT_SUPPORT)) {
            int dx,dy,best=-1;
            for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++)if(inside(x+dx,y+dy)) {
                u8 neighbor=gCreamTopology.cells[index_at(x+dx,y+dy)];
                if((neighbor&CT_SUPPORT)&&!(neighbor&CT_CLIMB)){best=neighbor;break;}
            }
            if(best<0)best=(y<(gCreamRoom.upper_bottom[x]+gCreamRoom.lower_top[x])/2)?CT_UPPER|4:0;
            c=(c&CT_RESERVED)|(best&(CT_UPPER|CT_HEIGHT_MASK))|CT_SUPPORT;
        }
        if(metatile_type[mt]==TT_CLIMB)c|=CT_CLIMB;
        else c&=~CT_CLIMB;
        gCreamTopology.cells[at]=c;
    }
}

int cream_topology_component_at(int px,int py,int fallback) {
    int x=px>>4,y=(py-4)>>4;u8 c;
    if(!gCreamTopology.active||!inside(x,y))return fallback;
    c=gCreamTopology.cells[index_at(x,y)];
    if(!(c&CT_SUPPORT)) {
        int kind=room_type(x,y);
        if(kind!=TT_FLOOR&&kind!=TT_MYST&&kind!=TT_CLIMB)return fallback;
    }
    if((c&CT_CLIMB)&&(c&7)==7)return fallback;
    return owner_of(c);
}
int cream_topology_height_at(int x,int y) {
    u8 c;
    if(!gCreamTopology.active||!inside(x,y))return -1;
    c=gCreamTopology.cells[index_at(x,y)];
    if(!(c&CT_SUPPORT)) {
        int kind=room_type(x,y);
        if(kind!=TT_FLOOR&&kind!=TT_MYST&&kind!=TT_CLIMB)return -1;
    }
    return c&7;
}
bool8 cream_topology_reserved(int x,int y) {
    return gCreamTopology.active&&inside(x,y)&&(gCreamTopology.cells[index_at(x,y)]&CT_RESERVED);
}
bool8 cream_topology_local_drop(int px,int py,int facing,u16 intent,int* lx,int* ly,int* height) {
    int i;
    if(!gCreamTopology.active||facing!=FACE_S||!(intent&KEY_DOWN))return FALSE;
    for(i=0;i<gCreamTopology.drops;i++) {
        const CreamTopologyDrop* d=&gCreamTopology.drop[i];
        if(ABS(px-d->x)>13||ABS(py-d->y)>6)continue;
        if(room_type_px(px,py-4)!=TT_FLOOR||room_type_px(d->landing_x,d->landing_y-4)!=TT_FLOOR)continue;
        if(room_box_solid(d->landing_x-4,d->landing_y-7,d->landing_x+3,d->landing_y-1))continue;
        if(lx)*lx=d->landing_x;
        if(ly)*ly=d->landing_y;
        if(height)*height=d->height;
        return TRUE;
    }
    return FALSE;
}
