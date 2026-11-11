/* Map-first Curdled Cream rooms. The graph owns legal routes; these native
   terraces expose exactly those routes with real floor, cliffs and door acts.
   The forest generator and every earlier metatile remain separate. */
#include "cream_room.h"
#include "room.h"
#include "actor.h"
#include "util.h"
#include "video.h"

CreamRoomInfo gCreamRoom;
u8 gCreamOpenEdges[CC_NODES];

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
static const u16 sCliff[3][3][2]={
 {{MT_CREAM_CLIFF_TOP_S0_V0,MT_CREAM_CLIFF_TOP_S0_V1},{MT_CREAM_CLIFF_MID_S0_V0,MT_CREAM_CLIFF_MID_S0_V1},{MT_CREAM_CLIFF_BASE_S0_V0,MT_CREAM_CLIFF_BASE_S0_V1}},
 {{MT_CREAM_CLIFF_TOP_S1_V0,MT_CREAM_CLIFF_TOP_S1_V1},{MT_CREAM_CLIFF_MID_S1_V0,MT_CREAM_CLIFF_MID_S1_V1},{MT_CREAM_CLIFF_BASE_S1_V0,MT_CREAM_CLIFF_BASE_S1_V1}},
 {{MT_CREAM_CLIFF_TOP_S2_V0,MT_CREAM_CLIFF_TOP_S2_V1},{MT_CREAM_CLIFF_MID_S2_V0,MT_CREAM_CLIFF_MID_S2_V1},{MT_CREAM_CLIFF_BASE_S2_V0,MT_CREAM_CLIFF_BASE_S2_V1}}
};
static const u16 sSide[3][2]={
 {MT_CREAM_CLIFF_LEFT_S0_V0,MT_CREAM_CLIFF_RIGHT_S0_V0},
 {MT_CREAM_CLIFF_LEFT_S1_V0,MT_CREAM_CLIFF_RIGHT_S1_V0},
 {MT_CREAM_CLIFF_LEFT_S2_V0,MT_CREAM_CLIFF_RIGHT_S2_V0}
};
static const u16 sClimb[3][3]={
 {MT_CREAM_CLIMB_TOP_S0,MT_CREAM_CLIMB_MID_S0,MT_CREAM_CLIMB_BOTTOM_S0},
 {MT_CREAM_CLIMB_TOP_S1,MT_CREAM_CLIMB_MID_S1,MT_CREAM_CLIMB_BOTTOM_S1},
 {MT_CREAM_CLIMB_TOP_S2,MT_CREAM_CLIMB_MID_S2,MT_CREAM_CLIMB_BOTTOM_S2}
};
static const u16 sRim[3]={MT_CREAM_RIM_S0,MT_CREAM_RIM_S1,MT_CREAM_RIM_S2};
static const u16 sDrop[3]={MT_CREAM_DROP_S0,MT_CREAM_DROP_S1,MT_CREAM_DROP_S2};
static const u16 sPit[3]={MT_CREAM_PIT_S0,MT_CREAM_PIT_S1,MT_CREAM_PIT_S2};
static const u16 sCrack[3]={MT_CREAM_CRACK_S0,MT_CREAM_CRACK_S1,MT_CREAM_CRACK_S2};
static const u16 sWeb[3]={MT_CREAM_WEB_S0,MT_CREAM_WEB_S1,MT_CREAM_WEB_S2};
static const u16 sMold[3]={MT_CREAM_MOLD_S0,MT_CREAM_MOLD_S1,MT_CREAM_MOLD_S2};
static const u16 sCave[3][3][2]={
 {{MT_CREAM_CAVE_S0_0_0,MT_CREAM_CAVE_S0_1_0},{MT_CREAM_CAVE_S0_0_1,MT_CREAM_CAVE_S0_1_1},{MT_CREAM_CAVE_S0_0_2,MT_CREAM_CAVE_S0_1_2}},
 {{MT_CREAM_CAVE_S1_0_0,MT_CREAM_CAVE_S1_1_0},{MT_CREAM_CAVE_S1_0_1,MT_CREAM_CAVE_S1_1_1},{MT_CREAM_CAVE_S1_0_2,MT_CREAM_CAVE_S1_1_2}},
 {{MT_CREAM_CAVE_S2_0_0,MT_CREAM_CAVE_S2_1_0},{MT_CREAM_CAVE_S2_0_1,MT_CREAM_CAVE_S2_1_1},{MT_CREAM_CAVE_S2_0_2,MT_CREAM_CAVE_S2_1_2}}
};
static const u16 sCaveGate[3][3][2]={
 {{MT_CREAM_CAVE_CRACK_S0_0,MT_CREAM_CAVE_CRACK_S0_1},{MT_CREAM_CAVE_WEB_S0_0,MT_CREAM_CAVE_WEB_S0_1},{MT_CREAM_CAVE_WARD_S0_0,MT_CREAM_CAVE_WARD_S0_1}},
 {{MT_CREAM_CAVE_CRACK_S1_0,MT_CREAM_CAVE_CRACK_S1_1},{MT_CREAM_CAVE_WEB_S1_0,MT_CREAM_CAVE_WEB_S1_1},{MT_CREAM_CAVE_WARD_S1_0,MT_CREAM_CAVE_WARD_S1_1}},
 {{MT_CREAM_CAVE_CRACK_S2_0,MT_CREAM_CAVE_CRACK_S2_1},{MT_CREAM_CAVE_WEB_S2_0,MT_CREAM_CAVE_WEB_S2_1},{MT_CREAM_CAVE_WARD_S2_0,MT_CREAM_CAVE_WARD_S2_1}}
};
static const u16 sChest[2][2][2]={
 {{MT_CREAM_CHEST_CLOSED_0_0,MT_CREAM_CHEST_CLOSED_1_0},{MT_CREAM_CHEST_CLOSED_0_1,MT_CREAM_CHEST_CLOSED_1_1}},
 {{MT_CREAM_CHEST_OPEN_0_0,MT_CREAM_CHEST_OPEN_1_0},{MT_CREAM_CHEST_OPEN_0_1,MT_CREAM_CHEST_OPEN_1_1}}
};

static int walk_y(int terrace) {return terrace==CC_UPPER?6:19;}
static int cave_y(int terrace) {return terrace==CC_UPPER?6:19;}
static u32 noise(int x,int y) {return hash32(gCreamWorld.seed^0xC0AD1234u,(gCreamRoom.cell+1)*977+x*37+y*97);}
static int stage(void) {return MIN(gCreamRoom.stage,2);}
static bool8 valid(int x,int y) {return x>=0 && y>=0 && x<CREAM_ROOM_W && y<CREAM_ROOM_H;}

static u16 plain_floor(int x,int y) {
    u32 n=noise(x/3,y/3);
    return sFloor[stage()][(n&7)<5?0:1+((n>>5)%3)];
}

static bool8 has_kind(int node,int kind) {
    int i;
    for(i=0;i<cream_edge_count(node);i++) if(cream_edge(node,i)->kind==kind)return TRUE;
    return FALSE;
}

static bool8 local_climb(void) {
    int lower=cream_node(gCreamRoom.cell,CC_LOWER),upper=lower+1;
    int i=cream_find_edge(lower,upper);
    return i>=0 && cream_edge(lower,i)->kind==CC_CLIMB;
}

void cream_room_reset_progress(void) {memset(gCreamOpenEdges,0,sizeof(gCreamOpenEdges));}

void cream_room_cave_pos(int terrace,int* px,int* py) {
    if(px)*px=7*16;
    if(py)*py=(cave_y(terrace)+1)*16-2;
}

void cream_room_drop_pos(int node,int index,int* px,int* py) {
    const CreamEdge* edge=cream_edge(node,index);
    int x=cream_terrace(node)==CC_LOWER?gCreamRoom.climb_x:10,y;
    if(edge && (edge->flags&CC_LONG_DROP))x=27;
    if(cream_terrace(node)==CC_LOWER)y=22;
    else y=MIN(gCreamRoom.upper_bottom[x],gCreamRoom.upper_bottom[x+1]);
    if(px)*px=x*16+16;
    if(py)*py=y*16+14;
}

/* Gate footprint is generated from the same edge consulted by traversal.
   Three-wide border lanes have full-height cross-sections, not one loose rock
   that can be walked around. Local climb barriers stand at their dry foot. */
static void gate_rect(int node,int index,int* x0,int* y0,int* x1,int* y1) {
    const CreamEdge* e=cream_edge(node,index);int t=cream_terrace(node),other=e?cream_cell(e->target):gCreamRoom.cell;
    int x=gCreamRoom.climb_x,y=walk_y(t);
    *x0=x;*x1=x+1;*y0=*y1=gCreamRoom.lower_top[x];
    if(!e)return;
    if(e->kind==CC_WALK) {
        x=(other%CC_WIDTH < gCreamRoom.cell%CC_WIDTH)?1:30;
        *x0=*x1=x;*y0=y-1;*y1=y+1;
    } else if(e->kind==CC_CAVE) {
        *x0=6;*x1=7;*y0=*y1=cave_y(t)+(e->require==CC_TOKEN_CAPE_PACCI);
    } else if(e->kind==CC_CLIMB && other!=gCreamRoom.cell) {
        *x0=x;*x1=x+1;*y0=*y1=2;
    } else if(e->kind==CC_DROP) {
        cream_room_drop_pos(node,index,&x,&y);x=x/16-1;y=y/16;
        *x0=x;*x1=x+1;*y0=*y1=y;
    }
}

static void paint_gate(int node,int index,bool8 opened) {
    const CreamEdge* e=cream_edge(node,index);int x0,y0,x1,y1,x,y,s=stage();u16 tile;
    if(!e || !e->require)return;
    gate_rect(node,index,&x0,&y0,&x1,&y1);
    if(opened || (gCreamOpenEdges[node]&(1u<<index))) {
        for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
            room_set(x,y,cream_room_floor(x,y));
            if(e->kind==CC_CAVE)room_set_overlay(x,y,MT_NONE);
        }
        return;
    }
    tile=e->require==CC_TOKEN_BOMB?sCrack[s]:(e->require==CC_TOKEN_LAMP || e->require==(CC_TOKEN_BOMB|CC_TOKEN_LAMP))?sWeb[s]:e->require==CC_TOKEN_CAPE_PACCI?sPit[s]:MT_CREAM_WARD;
    if(e->kind==CC_CAVE && e->require!=CC_TOKEN_CAPE_PACCI) {
        int kind=e->require==CC_TOKEN_BOMB?0:(e->require==CC_TOKEN_LAMP || e->require==(CC_TOKEN_BOMB|CC_TOKEN_LAMP))?1:2;
        for(x=x0;x<=x1;x++) {
            room_set_overlay(x,y0,MT_NONE);
            room_set(x,y0,sCaveGate[s][kind][x-x0]);
        }
    } else for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)room_set(x,y,tile);
}

u16 cream_room_floor(int x,int y) {
    int t,i;
    if(!valid(x,y))return plain_floor(CLAMP(x,0,31),CLAMP(y,0,23));
    /* Reconstitute a framed mouth after burning/bombing its native gate. */
    for(t=0;t<2;t++) if(y==cave_y(t) && x>=6 && x<=7 && has_kind(cream_node(gCreamRoom.cell,t),CC_CAVE))
        return sCave[stage()][2][x-6];
    if(x>=gCreamRoom.climb_x && x<=gCreamRoom.climb_x+1) {
        if(local_climb() && y>gCreamRoom.upper_bottom[x] && y<=gCreamRoom.lower_top[x])
            return sClimb[stage()][y==gCreamRoom.lower_top[x]?2:y==gCreamRoom.upper_bottom[x]+1?0:1];
        for(i=0;i<cream_edge_count(cream_node(gCreamRoom.cell,CC_UPPER));i++) {
            const CreamEdge* e=cream_edge(cream_node(gCreamRoom.cell,CC_UPPER),i);
            if(e->kind==CC_CLIMB && cream_cell(e->target)<gCreamRoom.cell && y<=2)return sClimb[stage()][1];
        }
    }
    {
        u16 under=gRoom.underlay[y*ROOM_MAX_W+x];
        if(under!=MT_NONE && under<METATILE_COUNT && (metatile_type[under]==TT_FLOOR || metatile_type[under]==TT_CLIMB))return under;
    }
    return plain_floor(x,y);
}

static void floor_rect(int x0,int y0,int x1,int y1,bool8 path) {
    int x,y;
    for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++) {
        room_set_overlay(x,y,MT_NONE);
        room_set(x,y,path?sPath[stage()][(x+y)&3]:plain_floor(x,y));
    }
}

static int upper_top(const CreamRoomInfo* info,int x) {
    if(info->motif==1)return (x<10 || x>21)?5:3;
    if(info->motif==2)return x>=18 && x<=21?3:5;
    if(info->motif==3)return x<18?4:2;
    return 2+(x<8 || x>25);
}
static bool8 base_terrace(int terrace,int x,int y) {
    int top;
    if(x<2 || x>29)return FALSE;
    if(terrace==CC_UPPER) {
        top=upper_top(&gCreamRoom,x);
        return y>=top && y<=gCreamRoom.upper_bottom[x];
    }
    return y>=gCreamRoom.lower_top[x] && y<=22-(gCreamRoom.motif==3 && x<10);
}

static void profile_info(int cell,CreamRoomInfo* info) {
    int x,peak=cream_cell(gCreamWorld.goal_node)==cell;
    u32 n=hash32(gCreamWorld.seed,cell*101+0xF0);
    info->motif=(n>>4)&3;info->return_door=(Spot){24,20};
    info->climb_x=12+2*(hash32(gCreamWorld.seed,(cell%CC_WIDTH)*53+0xCA)%5);
    for(x=0;x<32;x++) {
        int bump=((x+(n&7))/5)%3;
        info->upper_bottom[x]=peak?11:7+(bump==1?1:0)+(info->motif==2 && x>20?1:0);
        info->lower_top[x]=15+(((x+((n>>8)&7))/7)&1)+(info->motif==3 && x>20?1:0);
    }
}

static void profiles(int cell) {profile_info(cell,&gCreamRoom);}

static void paint_cave(int terrace) {
    int x,y,base=cave_y(terrace),node=cream_node(gCreamRoom.cell,terrace);
    if(!has_kind(node,CC_CAVE))return;
    floor_rect(5,base,8,base+2,FALSE);
    for(y=0;y<3;y++)for(x=0;x<2;x++) {
        if(y<2)room_set_overlay(6+x,base-2+y,sCave[stage()][y][x]);
        else room_set(6+x,base,sCave[stage()][y][x]);
    }
}

static void paint_routes(int terrace) {
    int i,x,y,t=terrace,node=cream_node(gCreamRoom.cell,t),s=stage();
    for(i=0;i<cream_edge_count(node);i++) {
        const CreamEdge* e=cream_edge(node,i);int target=cream_cell(e->target);
        if(e->kind==CC_WALK) {
            x=target%CC_WIDTH < gCreamRoom.cell%CC_WIDTH?0:28;
            floor_rect(x,walk_y(t)-1,x+3,walk_y(t)+1,TRUE);
        } else if(e->kind==CC_CLIMB && target==gCreamRoom.cell) {
            for(x=gCreamRoom.climb_x;x<=gCreamRoom.climb_x+1;x++) {
                int top=gCreamRoom.upper_bottom[x]+1,bottom=gCreamRoom.lower_top[x];
                for(y=top;y<=bottom;y++)room_set(x,y,sClimb[s][y==top?0:y==bottom?2:1]);
            }
            floor_rect(gCreamRoom.climb_x-1,gCreamRoom.lower_top[gCreamRoom.climb_x]+1,gCreamRoom.climb_x+2,walk_y(CC_LOWER),TRUE);
        } else if(e->kind==CC_CLIMB && target<gCreamRoom.cell) {
            for(x=gCreamRoom.climb_x;x<=gCreamRoom.climb_x+1;x++)for(y=0;y<=MAX(3,upper_top(&gCreamRoom,x));y++)room_set(x,y,sClimb[s][y?1:0]);
        } else if(e->kind==CC_DROP) {
            cream_room_drop_pos(node,i,&x,&y);x=x/16-1;y=y/16;
            room_set(x,y,sDrop[s]);room_set(x+1,y,sDrop[s]);
            if(t==CC_LOWER) {room_set(x,23,sDrop[s]);room_set(x+1,23,sDrop[s]);}
        }
    }
    paint_cave(t);
    for(i=0;i<cream_edge_count(node);i++)paint_gate(node,i,FALSE);
}

static void chest_tiles(int terrace,bool8 opened) {
    Spot p=gCreamRoom.terrace[terrace].chest;int x,y;
    for(y=0;y<2;y++)for(x=0;x<2;x++)room_set_overlay(p.x+x,p.y-1+y,sChest[opened!=0][y][x]);
}

void cream_room_set_chest_open(int node,bool8 opened) {
    if(node<0 || node>=CC_NODES || cream_cell(node)!=gCreamRoom.cell || !(gCreamRoom.terrace[cream_terrace(node)].content&CC_CONTENT_CHEST))return;
    chest_tiles(cream_terrace(node),opened);
    room_build_solid();room_render();
}

static void spot_info(CreamRoomInfo* info,int terrace) {
    CreamTerraceSpots* sp=&info->terrace[terrace];int node=cream_node(info->cell,terrace),y=walk_y(terrace);
    sp->content=gCreamWorld.content[node];
    sp->chest=(Spot){24,(u8)(terrace==CC_UPPER?6:20)};
    sp->npc=(Spot){20,(u8)(terrace==CC_UPPER?4:21)};
    sp->heal=(Spot){4,(u8)(terrace==CC_UPPER?7:21)};
    sp->cache=(Spot){27,(u8)(terrace==CC_UPPER?6:21)};
    sp->mission=(Spot){14,(u8)y};
}

static void spots(int terrace) {
    static const u8 sx[CREAM_SPAWN_MAX]={11,17,27,4,21,14};
    CreamTerraceSpots* sp=&gCreamRoom.terrace[terrace];int i,node=cream_node(gCreamRoom.cell,terrace),y=walk_y(terrace);
    spot_info(&gCreamRoom,terrace);
    if(sp->content&CC_CONTENT_ENTRY)floor_rect(23,17,26,21,FALSE);
    if(sp->content&CC_CONTENT_CHEST)chest_tiles(terrace,FALSE);
    if(sp->content&CC_CONTENT_MISSION)room_set_overlay(sp->mission.x,sp->mission.y,MT_CREAM_TRIAL);
    if((sp->content&CC_CONTENT_CACHE) && !(sp->content&CC_CONTENT_CHEST))room_set_overlay(sp->cache.x,sp->cache.y,MT_CREAM_CACHE);
    if(sp->content&CC_CONTENT_HEAL)room_set_overlay(sp->heal.x,sp->heal.y,MT_CREAM_SHRINE);
    /* Lanterns mark actual climb/cave/content approaches rather than filling
       empty floor. Each has a clear standing front outside the route lane. */
    if(local_climb() && terrace==CC_LOWER)room_set_overlay(gCreamRoom.climb_x+3,gCreamRoom.lower_top[gCreamRoom.climb_x]+1,MT_CREAM_LAMP_LIT);
    if(has_kind(node,CC_CAVE))room_set_overlay(4,cave_y(terrace),MT_CREAM_LAMP_LIT);
    room_build_solid();
    sp->spawn_count=0;
    if(sp->content&CC_CONTENT_BOSS) {sp->spawns[0]=(Spot){16,8};sp->spawn_count=1;return;}
    for(i=0;i<CREAM_SPAWN_MAX;i++) {
        int x=sx[(i+(gCreamRoom.cell%3))%CREAM_SPAWN_MAX];
        if((x>=gCreamRoom.climb_x-1 && x<=gCreamRoom.climb_x+2) || x==24 || x==25 || ((sp->content&CC_CONTENT_MISSION) && ABS(x-sp->mission.x)<2))continue;
        if(room_type(x,y)==TT_FLOOR && room_get_overlay(x,y)==MT_NONE && !room_box_solid(x*16+2,y*16+4,x*16+13,y*16+13))sp->spawns[sp->spawn_count++]=(Spot){(u8)x,(u8)y};
    }

}

void cream_room_build(int cell) {
    int x,y,t,s;
    cell=CLAMP(cell,0,CC_ROOMS-1);memset(&gCreamRoom,0,sizeof(gCreamRoom));gCreamRoom.cell=cell;
    gCreamRoom.stage=MIN(gCreamWorld.corruption[cell],2);profiles(cell);s=stage();
    room_clear(CREAM_ROOM_W,CREAM_ROOM_H,sCliff[s][1][0]);
    for(y=0;y<CREAM_ROOM_H;y++)for(x=0;x<CREAM_ROOM_W;x++) {
        bool8 upper=base_terrace(CC_UPPER,x,y),lower=base_terrace(CC_LOWER,x,y);
        if(upper||lower)room_set(x,y,plain_floor(x,y));
        else if(x<2 || x>=30)room_set(x,y,sSide[s][x>=30]);
        else if(x>1 && x<30) {
            int kind=y==gCreamRoom.upper_bottom[x]+1?0:y==gCreamRoom.lower_top[x]-1?2:1;
            room_set(x,y,sCliff[s][kind][((x/3+y/2)&7)==0]);
        }
        if(x>1 && x<30 && y==gCreamRoom.upper_bottom[x]+1)room_set(x,y,sRim[s]);
    }
    /* The top-row peak is a wide upper arena. Raised sides stay outside its
       dry14x8body; lower component remains physically separated below. */
    if(cream_cell(gCreamWorld.goal_node)==cell)floor_rect(4,2,28,11,FALSE);
    for(t=0;t<2;t++)paint_routes(t);
    if((noise(3,9)&3)==0) {
        static const u16 fall[3]={MT_CREAM_FALL_S0,MT_CREAM_FALL_S1,MT_CREAM_FALL_S2};
        for(y=gCreamRoom.upper_bottom[3]+2;y<gCreamRoom.lower_top[3]-1;y++)if(room_type(3,y)==TT_SOLID)room_set(3,y,fall[s]);
    }
    for(t=0;t<2;t++)spots(t);
    /* Contextual mold grows only at cliff feet/outer ledge corners. Never on
       a route, a landing, a chest front, a mission or an enemy marker. */
    for(x=3;x<29;x+=5) {
        y=gCreamRoom.lower_top[x];
        if(room_type(x,y)==TT_FLOOR && (noise(x,y)&3)==0 && ABS(x-gCreamRoom.climb_x)>3)
            room_set_overlay(x,y,sMold[s]);
    }
    room_build_solid();room_render();
}

int cream_room_terrace_at(int px,int py,int current) {
    int x=CLAMP(px>>4,0,31),y=(py-4)>>4;
    if(y<=gCreamRoom.upper_bottom[x])return CC_UPPER;
    if(y>=gCreamRoom.lower_top[x])return CC_LOWER;
    return current;
}

bool8 cream_room_feature_reserved(int x,int y) {
    static const u8 flags[5]={CC_CONTENT_CHEST,CC_CONTENT_NPC,CC_CONTENT_HEAL,CC_CONTENT_CACHE,CC_CONTENT_MISSION};
    int t,i;
    for(t=0;t<2;t++) {
        const CreamTerraceSpots* p=&gCreamRoom.terrace[t];
        const Spot* feature[5]={&p->chest,&p->npc,&p->heal,&p->cache,&p->mission};
        if((p->content&CC_CONTENT_ENTRY) && ABS(x-gCreamRoom.return_door.x)<=2 && ABS(y-gCreamRoom.return_door.y)<=2)return TRUE;
        for(i=0;i<5;i++)if((p->content&flags[i]) && ABS(x-feature[i]->x)<=2 && ABS(y-feature[i]->y)<=2)return TRUE;
    }
    return FALSE;
}

bool8 cream_room_node_floor(int node,int x,int y) {
    int t=cream_terrace(node);
    return cream_cell(node)==gCreamRoom.cell && valid(x,y) && room_type(x,y)==TT_FLOOR &&
           cream_room_terrace_at(x*16+8,y*16+14,t)==t &&
           !room_box_solid(x*16+2,y*16+6,x*16+13,y*16+13);
}

/* Target profiles are derived without changing the loaded source room.
   This matters for long falls: adjacent rooms deliberately have unequal lips. */
static void arrival_profile(int cell,int x,int* upper,int* lower,int* climb) {
    u32 n=hash32(gCreamWorld.seed,cell*101+0xF0);int motif=(n>>4)&3,bump=((x+(n&7))/5)%3;
    *upper=cream_cell(gCreamWorld.goal_node)==cell?11:7+(bump==1)+(motif==2 && x>20);
    *lower=15+(((x+((n>>8)&7))/7)&1)+(motif==3 && x>20);
    *climb=12+2*(hash32(gCreamWorld.seed,(cell%CC_WIDTH)*53+0xCA)%5);
}
void cream_room_arrival(int from_node,const CreamEdge* edge,int* px,int* py,int* facing) {
    int t=edge?cream_terrace(edge->target):CC_LOWER;
    int from=cream_cell(from_node),to=edge?cream_cell(edge->target):gCreamRoom.cell;
    int upper,lower,cx,u2,l2,c2,x=10;
    arrival_profile(to,x,&upper,&lower,&cx);
    *px=16*16;*py=walk_y(t)*16+14;*facing=FACE_N;
    if(!edge)return;
    if(edge->kind==CC_WALK) {
        bool8 east=to%CC_WIDTH>from%CC_WIDTH;
        *px=east?24:CREAM_ROOM_W*16-24;*facing=east?FACE_E:FACE_W;
    } else if(edge->kind==CC_CAVE) {
        cream_room_cave_pos(t,px,py);*py=(cave_y(t)+2)*16+14;*facing=FACE_S;
    } else if(edge->kind==CC_CLIMB) {
        arrival_profile(to,cx,&upper,&lower,&cx);arrival_profile(to,cx+1,&u2,&l2,&c2);
        *px=cx*16+16;*py=from==to?MIN(upper,u2)*16+12:22*16+10;*facing=FACE_N;
    } else if(edge->kind==CC_DROP) {
        if(edge->flags&CC_LONG_DROP)x=27;
        if(from==to || (edge->flags&CC_LONG_DROP)) {
            arrival_profile(to,x,&upper,&lower,&cx);arrival_profile(to,x+1,&u2,&l2,&c2);
            *px=x*16+16;*py=(MAX(lower,l2)+2)*16+14;
        } else {
            CreamRoomInfo target_info;memset(&target_info,0,sizeof(target_info));profile_info(to,&target_info);
            int top=cream_cell(gCreamWorld.goal_node)==to?2:MAX(upper_top(&target_info,cx),upper_top(&target_info,cx+1));
            *px=cx*16+16;*py=(MAX(3,top)+1)*16+14;
        }
        *facing=FACE_S;
    }
}

bool8 cream_room_route(int node,int px,int py,int facing,u16 intent,CreamRoomRoute* out) {
    int i,t=cream_terrace(node),actual=cream_room_terrace_at(px,py,t);
    if(!out || node<0 || node>=CC_NODES || cream_cell(node)!=gCreamRoom.cell)return FALSE;
    memset(out,0,sizeof(*out));
    for(i=0;i<cream_edge_count(node);i++) {
        const CreamEdge* e=cream_edge(node,i);int target=cream_cell(e->target),mode=CCR_NONE,x,y;
        if(e->kind==CC_WALK && ABS(py-(walk_y(t)*16+14))<=18) {
            if(target%CC_WIDTH<gCreamRoom.cell%CC_WIDTH && px<=12 && (intent&KEY_LEFT))mode=CCR_WALK;
            if(target%CC_WIDTH>gCreamRoom.cell%CC_WIDTH && px>=CREAM_ROOM_W*16-12 && (intent&KEY_RIGHT))mode=CCR_WALK;
        } else if(e->kind==CC_CLIMB) {
            if(target==gCreamRoom.cell && actual==CC_UPPER && t==CC_LOWER)mode=CCR_LOCAL_UP;
            else if(target<gCreamRoom.cell && py<=18 && ABS(px-(gCreamRoom.climb_x*16+16))<=15 && (intent&KEY_UP))mode=CCR_CLIMB;
        } else if(e->kind==CC_DROP) {
            if(target==gCreamRoom.cell && actual==CC_LOWER && t==CC_UPPER)mode=CCR_LOCAL_DOWN;
            else if(t==CC_LOWER && target>gCreamRoom.cell && py>=CREAM_ROOM_H*16-18 && ABS(px-(gCreamRoom.climb_x*16+16))<=15 && (intent&KEY_DOWN))mode=CCR_DROP;
            else if(t==CC_UPPER && (intent&KEY_DOWN)) {
                cream_room_drop_pos(node,i,&x,&y);
                if(ABS(px-x)<=15 && py>=y-6 && py<=y+6)mode=CCR_DROP;
            }
        } else if(e->kind==CC_CAVE && facing==FACE_N && (intent&KEY_UP)) {
            cream_room_cave_pos(t,&x,&y);
            if(ABS(px-x)<=13 && py>=y-3 && py<=y+15 && room_type_px(px,py-6)==TT_MYST)mode=CCR_CAVE;
        }
        if(mode) {
            /* Physical use is required for solid bomb/web/ward gates. Cape
               pits remain passable to an actual airborne body and are also
               checked against capabilities by the caller's graph admission. */
            if(e->require && e->require!=CC_TOKEN_CAPE_PACCI && !(gCreamOpenEdges[node]&(1u<<i)))continue;
            out->edge=i;out->mode=mode;out->target=e->target;
            out->rows=ABS(target/CC_WIDTH-gCreamRoom.cell/CC_WIDTH);
            {int lx,ly,lf;cream_room_arrival(node,e,&lx,&ly,&lf);out->x=lx;out->y=ly;}
            return TRUE;
        }
    }
    return FALSE;
}

bool8 cream_room_gate_cleared(int tx,int ty) {
    int t,i,x0,y0,x1,y1;bool8 changed=FALSE;
    for(t=0;t<2;t++) {
        int node=cream_node(gCreamRoom.cell,t);
        for(i=0;i<cream_edge_count(node);i++) {
            const CreamEdge* e=cream_edge(node,i);
            if(!e->require || e->require==CC_TOKEN_CAPE_PACCI)continue;
            gate_rect(node,i,&x0,&y0,&x1,&y1);
            if(tx<x0 || tx>x1 || ty<y0 || ty>y1)continue;
            cream_room_unlock_edge(node,i);changed=TRUE;
        }
    }
    if(changed){room_build_solid();room_render();}
    return changed;
}

/* Used for the final three-gift seal. Reactive single-tool gates still need
   an actual bomb/flame hit before this state is set. */
bool8 cream_room_unlock_edge(int node,int index) {
    if(node<0 || node>=CC_NODES || index<0 || index>=cream_edge_count(node))return FALSE;
    gCreamOpenEdges[node]|=1u<<index;
    {const CreamEdge* e=cream_edge(node,index);int reverse=cream_find_edge(e->target,node);
     if(reverse>=0 && cream_edge(e->target,reverse)->require==e->require)gCreamOpenEdges[e->target]|=1u<<reverse;}
    if(cream_cell(node)==gCreamRoom.cell) {paint_gate(node,index,TRUE);room_build_solid();room_render();}
    return TRUE;
}

/* Pure map preview: it never calls room_set, room_render or changes the live
   profile. Labels are gameplay semantics rather than sampled art colours. */
void cream_room_preview(int cell,CreamRoomInfo* out,u8 mask[CREAM_ROOM_W*CREAM_ROOM_H]) {
    int x,y,t,i;CreamRoomInfo local;
    if(!out)out=&local;
    cell=CLAMP(cell,0,CC_ROOMS-1);memset(out,0,sizeof(*out));out->cell=cell;
    out->stage=MIN(gCreamWorld.corruption[cell],2);profile_info(cell,out);
    for(t=0;t<2;t++)spot_info(out,t);
    if(!mask)return;
    memset(mask,0,CREAM_ROOM_W*CREAM_ROOM_H);
    for(y=0;y<24;y++)for(x=2;x<30;x++) {
        int top=upper_top(out,x);
        if(y>=top && y<=out->upper_bottom[x])mask[y*32+x]=2;
        if(y>=out->lower_top[x] && y<=22-(out->motif==3 && x<10))mask[y*32+x]=1;
    }
    if(cream_cell(gCreamWorld.goal_node)==cell)for(y=2;y<=11;y++)for(x=4;x<=28;x++)mask[y*32+x]=2;
    if(cell==cream_cell(gCreamWorld.entry_node))for(y=17;y<=21;y++)for(x=23;x<=26;x++)mask[y*32+x]=1;
    for(t=0;t<2;t++) {
        int node=cream_node(cell,t),cx=out->climb_x,wy=walk_y(t);
        for(i=0;i<cream_edge_count(node);i++) {
            const CreamEdge* e=cream_edge(node,i);int target=cream_cell(e->target),x0=cx,x1=cx+1,y0=out->lower_top[cx],y1=y0;
            if(e->kind==CC_WALK) {
                int left=target%5<cell%5;
                for(y=wy-1;y<=wy+1;y++)for(x=left?0:28;x<=(left?3:31);x++)mask[y*32+x]=t+1;
                x0=x1=left?1:30;y0=wy-1;y1=wy+1;
            } else if(e->kind==CC_CLIMB) {
                if(target==cell) {
                    for(x=cx;x<=cx+1;x++)for(y=out->upper_bottom[x]+1;y<=out->lower_top[x];y++)mask[y*32+x]=3;
                    for(y=out->lower_top[cx]+1;y<=19;y++)for(x=cx-1;x<=cx+2;x++)mask[y*32+x]=1;
                } else {for(x=cx;x<=cx+1;x++)for(y=0;y<=MAX(3,upper_top(out,x));y++)mask[y*32+x]=3;y0=y1=2;}
            } else if(e->kind==CC_DROP) {
                x0=t==CC_LOWER?cx:(e->flags&CC_LONG_DROP)?27:10;x1=x0+1;
                y0=y1=t==CC_LOWER?22:MIN(out->upper_bottom[x0],out->upper_bottom[x1]);
                mask[y0*32+x0]=mask[y0*32+x1]=5;
                if(t==CC_LOWER)mask[23*32+x0]=mask[23*32+x1]=5;
            } else if(e->kind==CC_CAVE) {
                int cy=cave_y(t);
                for(y=cy;y<=cy+2;y++)for(x=5;x<=8;x++)mask[y*32+x]=t+1;
                for(y=cy-2;y<cy;y++)for(x=6;x<=7;x++)mask[y*32+x]=0;
                mask[cy*32+6]=mask[cy*32+7]=4;
                x0=6;x1=7;y0=y1=cy+(e->require==CC_TOKEN_CAPE_PACCI);
            }
            if(e->require && !(gCreamOpenEdges[node]&(1u<<i)))
                for(y=y0;y<=y1;y++)for(x=x0;x<=x1;x++)mask[y*32+x]=6;
        }
        if(out->terrace[t].content&CC_CONTENT_ENTRY) {Spot p=out->return_door;mask[p.y*32+p.x]=mask[p.y*32+p.x+1]=4;}
        if(out->terrace[t].content&CC_CONTENT_CHEST) {
            Spot p=out->terrace[t].chest;
            for(y=p.y-1;y<=p.y;y++)for(x=p.x;x<=p.x+1;x++)mask[y*32+x]=0;
        }
    }
}
