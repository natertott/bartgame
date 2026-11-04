
#include <stdio.h>
#include <stdlib.h>
#include "game.h"
#include "world.h"
#include "room.h"
#include "roomgen.h"
#if BART_FOREST_VARIANT >= 31
#include "forest_trees.h"
#endif
GameState gGame;
u32 gFrame;

#include "forest_paths.h"
static unsigned long qa_trail_calls,qa_trail_physics_failures;
static void qa_trail_refine(int cell,u8* path);
#define forest_paths_refine qa_trail_refine
#include "/workspace/bartgame/bartgame/src/roomgen.c"
#undef forest_paths_refine
static void qa_trail_refine(int cell,u8* path) {
    u16 before[32*24],overlay[32*24];int x,y,changed=0;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x,mt=room_get(x,y);
        before[q]=metatile_coll[mt]|(metatile_type[mt]<<8);overlay[q]=room_get_overlay(x,y);
    }
    forest_paths_refine(cell,path);qa_trail_calls++;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x,mt=room_get(x,y);
        if(before[q]!=(metatile_coll[mt]|(metatile_type[mt]<<8))||overlay[q]!=room_get_overlay(x,y))changed=1;
    }
    if(changed){qa_trail_physics_failures++;printf("FAIL seed=%u cell=%d trail refinement changes physical type/collision or authored overlay\n",gWorld.seed,cell);}
}

/* Independent traversal reads the completed native collision grid, not a
   reconstruction of the generator's candidate/placement predicates. */
static unsigned char seen[4096];
static int queue[4096],failures,printed;
static unsigned long rooms,approaches,pockets,determinism,boundaries,feet_rooms;
static unsigned long trees,wood_cells,authored_cells,preview_checks,root_checks,opened_state_rooms,cache_checks,frame_seen[12],stage_state[4][3];
static const int land[4][2]={{15,2},{30,11},{15,22},{1,11}};
static void fail(unsigned seed,int cell,const char* why,int x,int y) {
    failures++;if(printed++<40)printf("FAIL seed=%u cell=%d %s (%d,%d)\n",seed,cell,why,x,y);
}
static int blocked(int qx,int qy,int items) {
    int x=qx/2,y=qy/2,t;
    if(qx<0||qy<0||qx>=gRoom.w*2||qy>=gRoom.h*2)return 1;
    t=room_type(x,y);
    if(t==TT_THORN||t==TT_LIFT1)return 0;
    if((items&1)&&t==TT_CRACK)return 0;
    if((items&2)&&t==TT_WEB)return 0;
    if((items&4)&&t==TT_PIT)return 0;
    if(t==TT_PIT||t==TT_WATER||t==TT_MYST||t==TT_EXIT)return 1;
    return gRoom.solid[qy*64+qx]!=0;
}
static void flood(int x,int y,int items) {
    static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int a,b,head=0,tail=0,i;memset(seen,0,sizeof(seen));
    for(b=0;b<2;b++)for(a=0;a<2;a++) {
        int qx=x*2+a,qy=y*2+b,p=qy*64+qx;
        if(!blocked(qx,qy,items)){seen[p]=1;queue[tail++]=p;}
    }
    while(head<tail) {
        int p=queue[head++],x=p%64,y=p/64;
        for(i=0;i<4;i++) {
            int nx=x+dx[i],ny=y+dy[i],n=ny*64+nx;
            if(!blocked(nx,ny,items)&&!seen[n]){seen[n]=1;queue[tail++]=n;}
        }
    }
}
static int reaches(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    return seen[y*128+x*2]||seen[y*128+x*2+1]||seen[(y*2+1)*64+x*2]||seen[(y*2+1)*64+x*2+1];
}
static void target(unsigned seed,int cell,const char* label,Spot p,int offset) {
    approaches++;if(!reaches(p.x,p.y+offset))fail(seed,cell,label,p.x,p.y+offset);
}
/* Bloom's implemented feet box is10×8, offset(0,-4), not a point on an
   8px collision quarter. A separate2px position lattice catches clear-looking
   8px slits that the earlier quarter flood can falsely call traversable.
   Every8px blocker remains wider than a lattice step. */
static unsigned char feet_seen[256*192];
static int feet_queue[256*192];
static int feet_free(int x,int y,int items) {
    int px=x*2,py=y*2,qx,qy;
    if(px<5||py<8||px+4>=gRoom.w*16||py>gRoom.h*16)return 0;
    for(qy=(py-8)/8;qy<=(py-1)/8;qy++)
        for(qx=(px-5)/8;qx<=(px+4)/8;qx++)if(blocked(qx,qy,items))return 0;
    return 1;
}
static void feet_flood(int sx,int sy,int items) {
    static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int x,y,head=0,tail=0,i;memset(feet_seen,0,sizeof(feet_seen));
    for(y=sy*8;y<(sy+1)*8;y++)for(x=sx*8;x<(sx+1)*8;x++) {
        int p=y*256+x;
        if(feet_free(x,y,items)){feet_seen[p]=1;feet_queue[tail++]=p;}
    }
    while(head<tail) {
        int p=feet_queue[head++],x=p%256,y=p/256;
        for(i=0;i<4;i++) {
            int nx=x+dx[i],ny=y+dy[i],n=ny*256+nx;
            if(nx<0||ny<0||nx>=256||ny>=192||feet_seen[n]||!feet_free(nx,ny,items))continue;
            feet_seen[n]=1;feet_queue[tail++]=n;
        }
    }
}
static int feet_reaches(int x,int y) {
    int a,b;
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    for(b=y*8;b<(y+1)*8;b++)for(a=x*8;a<(x+1)*8;a++)if(feet_seen[b*256+a])return 1;
    return 0;
}
static void feet_target(unsigned seed,int cell,const char* label,Spot p,int off) {
    if(!feet_reaches(p.x,p.y+off))fail(seed,cell,label,p.x,p.y+off);
}
static void feet_inspect(unsigned seed,int cell) {
    const Cell*c=&gWorld.cells[cell];int start=-1,s,i;
    for(s=0;s<4;s++)if(c->gate[s]){start=s;break;}
    if(start<0)return;
    feet_rooms++;feet_flood(land[start][0],land[start][1],0);
    for(s=0;s<4;s++)if(c->gate[s]&&!feet_reaches(land[s][0],land[s][1]))
        fail(seed,cell,"10x8feet cannot reach door landing",land[s][0],land[s][1]);
    if(gSpots.has_chest)feet_target(seed,cell,"10x8feet chest approach",gSpots.chest,1);
    if(gSpots.has_npc)feet_target(seed,cell,"10x8feet NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)feet_target(seed,cell,"10x8feet relic approach",gSpots.relic,0);
    if(gSpots.has_boss)feet_target(seed,cell,"10x8feet boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)feet_target(seed,cell,"10x8feet shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)feet_target(seed,cell,"10x8feet mouth approach",gSpots.mouth,1);
    for(i=0;i<gSpots.torch_count;i++)feet_target(seed,cell,"10x8feet torch approach",gSpots.torches[i],1);
}
static int gate_allowed(const Cell* c,int side,int items) {
    int g=c->gate[side];
    if(g==GATE_WALL)return 0;
    if(g==GATE_CRACK)return (items&1)||world_gate_open(gGame.cell,side);
    if(g==GATE_WEB)return (items&2)||world_gate_open(gGame.cell,side);
    if(g==GATE_CHASM)return (items&4)!=0;
    if(g==GATE_LOCK)return world_gate_open(gGame.cell,side);
    return 1;
}
static void boundary(unsigned seed,int cell,int items) {
    const Cell*c=&gWorld.cells[cell];int x,y,side;
    boundaries++;
    for(y=0;y<gRoom.h*2;y++)for(x=0;x<gRoom.w*2;x++) {
        int at=y*64+x,x0,y0,x1,y1;
        if(x&&y&&x!=gRoom.w*2-1&&y!=gRoom.h*2-1)continue;
        if(!seen[at])continue;
        side=y==0?SIDE_N:x==gRoom.w*2-1?SIDE_E:y==gRoom.h*2-1?SIDE_S:SIDE_W;
        roomgen_gate_tiles(side,&x0,&y0,&x1,&y1);
        /* North has a gate on row1 and an open visual forecourt on row0. */
        if(side==SIDE_N)y0=y1=0;
        if(!gate_allowed(c,side,items)||x/2<x0||x/2>x1||y/2<y0||y/2>y1)
            fail(seed,cell,"escape outside the allowed gate cutset",x,y);
    }
}
static void inspect(unsigned seed,int cell) {
    const Cell*c=&gWorld.cells[cell];int s,start=-1,i,items;
    for(s=0;s<4;s++)if(c->gate[s]){start=s;break;}
    if(start<0){fail(seed,cell,"no arrival side",0,0);return;}
    flood(land[start][0],land[start][1],0);
    for(s=0;s<4;s++)if(c->gate[s]&&!reaches(land[s][0],land[s][1]))
        fail(seed,cell,"door inner landing unreachable",land[s][0],land[s][1]);
    if(gSpots.has_chest)target(seed,cell,"chest approach",gSpots.chest,1);
    if(gSpots.has_npc)target(seed,cell,"NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)target(seed,cell,"relic approach",gSpots.relic,0);
    if(gSpots.has_boss)target(seed,cell,"boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)target(seed,cell,"shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)target(seed,cell,"mouth approach",gSpots.mouth,1);
    if(c->role==ROLE_KEYITEM&&!gSpots.has_mouth)fail(seed,cell,"mandatory task has no entrance",0,0);
    for(i=0;i<gSpots.spawn_count;i++)target(seed,cell,"spawn approach",gSpots.spawns[i],0);
    for(i=0;i<gSpots.torch_count;i++)target(seed,cell,"quest torch approach",gSpots.torches[i],1);
    if(c->role==ROLE_NPC_TORCH&&gSpots.torch_count!=4)fail(seed,cell,"quest lacks four censers",0,0);
    if(gSpots.has_treasure&&gSpots.pocket_kind>=1&&gSpots.pocket_kind<=3) {
        Spot p=gSpots.treasure;int item=1<<(gSpots.pocket_kind-1),open=c->opened&CELL_POCKET_OPEN;pockets++;
        if(!open&&reaches(p.x,p.y))fail(seed,cell,"pocket bypasses required item",p.x,p.y);
        flood(land[start][0],land[start][1],item);
        if(!reaches(p.x,p.y))fail(seed,cell,"pocket blocked with right item",p.x,p.y);
        flood(land[start][0],land[start][1],7^item);
        if(!open&&reaches(p.x,p.y))fail(seed,cell,"pocket accepts wrong items",p.x,p.y);
    }
    for(items=0;items<8;items++) {
        flood(land[start][0],land[start][1],items);boundary(seed,cell,items);
    }
}


/* Independent landscape checks use the completed semantic room, not the
   generator's proposed candidate/rejection predicates or decoration counters. */
static unsigned long qa_water_components,qa_water_cells,qa_bridge_runs,qa_bridge_landings;
static unsigned long qa_lights,qa_unanchored_lights,qa_detail_cells,qa_context_details,qa_ledge_cells;
static unsigned long qa_landscape_failures;
static unsigned long qa_motifs[6];
static int qa_deck(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y);return mt==MT_BRIDGE?1:mt==MT_BRIDGE_V?2:0;
}
static int qa_water(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y),kind=forest_v2_water_kind[mt];
    return (kind>=1&&kind<=3)||mt==MT_WATERFALL;
}
static int qa_wet(int x,int y) {return qa_water(x,y)||qa_deck(x,y);}
static int qa_dry_landing(int x,int y) {
    if(x<1||y<2||x>=gRoom.w-1||y>=gRoom.h-1||qa_wet(x,y))return 0;
    int t=room_type(x,y),dx,dy;
    if(t!=TT_FLOOR&&t!=TT_SLOW&&t!=TT_DOOR_OPEN&&t!=TT_STAIRS)return 0;
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
        if(gRoom.solid[(y*2+dy)*64+x*2+dx])return 0;
    return reaches(x,y);
}
static int qa_path(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    int mt=room_get(x,y);
    return mt==MT_PATH||mt==MT_PATH_EDGE_N||mt==MT_BLIGHT_VEIN||
           (mt>=MT_PEDGE_1&&mt<=MT_PEDGE_F)||(mt>=MT_PEDGE_C1&&mt<=MT_PEDGE_CF);
}
static int qa_feature_near(int x,int y,int d) {
    int i;
    for(i=0;i<gSpots.torch_count;i++)
        if(ABS(x-gSpots.torches[i].x)+ABS(y-gSpots.torches[i].y)<=d)return 1;
    return (gSpots.has_chest&&ABS(x-gSpots.chest.x)+ABS(y-gSpots.chest.y)<=d)||
           (gSpots.has_npc&&ABS(x-gSpots.npc.x)+ABS(y-gSpots.npc.y)<=d)||
           ((gSpots.has_relic||gWorld.cells[gGame.cell].role==ROLE_RELIC)&&ABS(x-gSpots.relic.x)+ABS(y-gSpots.relic.y)<=d)||
           (gSpots.has_shrine&&ABS(x-gSpots.shrine.x)+ABS(y-gSpots.shrine.y)<=d)||
           (gSpots.has_mouth&&ABS(x-gSpots.mouth.x)+ABS(y-(gSpots.mouth.y+1))<=d)||
           (gSpots.has_treasure&&ABS(x-gSpots.treasure.x)+ABS(y-gSpots.treasure.y)<=d)||
           (gSpots.has_treasure&&ABS(x-gSpots.pocket_gate.x)+ABS(y-gSpots.pocket_gate.y)<=d)||
           (gSpots.has_boss&&ABS(x-gSpots.boss.x)+ABS(y-gSpots.boss.y)<=d);
}
static int qa_route_anchor(int x,int y) {
    int dx,dy;
    if(qa_feature_near(x,y,4))return 1;
    for(dy=-3;dy<=3;dy++)for(dx=-3;dx<=3;dx++)
        if(ABS(dx)+ABS(dy)<=3&&(qa_path(x+dx,y+dy)||qa_deck(x+dx,y+dy)))return 1;
    return 0;
}
static int qa_detail(int mt) {
    return mt==MT_BONES||mt==MT_STUMP||mt==MT_SICK_STUMP||mt==MT_SICK_ROCK||
           mt==MT_ROCK||mt==MT_ROCK2||mt==MT_ROCK3||mt==MT_LOG||
           mt==MT_HLOG_0||mt==MT_HLOG_1||mt==MT_ROCK_SMALL||mt==MT_BUSH;
}
static int qa_detail_context(int x,int y) {
    int dx,dy;
    if(qa_feature_near(x,y,4))return 1;
    for(dy=-3;dy<=3;dy++)for(dx=-3;dx<=3;dx++) {
        int nx=x+dx,ny=y+dy,mt;
        if(ABS(dx)+ABS(dy)>3||nx<0||ny<0||nx>=gRoom.w||ny>=gRoom.h)continue;
        mt=room_get(nx,ny);
        if(forest_v2_canopy_kind[mt]||qa_wet(nx,ny)||
           (mt==MT_MOSSY_STONE))return 1;
    }
    return 0;
}
static void qa_landscape(unsigned seed,int cell) {
    unsigned char wet_seen[768]={0};int q[768],x,y,i,component_count=0,water_count=0,deck_count=0;
    int lamp_x[128],lamp_y[128],lamp_count=0,lamp_seen[128]={0};
    int start=-1,s,failures_before=failures;
    for(s=0;s<4;s++)if(gWorld.cells[cell].gate[s]){start=s;break;}
    if(start>=0)flood(land[start][0],land[start][1],0);
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int mt=room_get(x,y),d=qa_deck(x,y),at=y*32+x;
        if(qa_water(x,y)){water_count++;qa_water_cells++;}
        if(d)deck_count++;
        if(qa_detail(mt)) {qa_detail_cells++;qa_context_details+=qa_detail_context(x,y);}
        if(mt==MT_LEDGE_N||mt==MT_LEDGE_S||mt==MT_LEDGE_S_W||mt==MT_LEDGE_S_E)qa_ledge_cells++;
        if(mt==MT_LANTERN_POST) {
            qa_lights++;
            if(lamp_count<128){lamp_x[lamp_count]=x;lamp_y[lamp_count]=y;lamp_seen[lamp_count]=qa_route_anchor(x,y);lamp_count++;}
            else fail(seed,cell,"too many lanterns for contextual audit",x,y);
        }
        if(qa_wet(x,y)&&!wet_seen[at]) {
            int head=0,tail=0,tiles=0;wet_seen[at]=1;q[tail++]=at;
            component_count++;qa_water_components++;
            while(head<tail) {
                int p=q[head++],cx=p%32,cy=p/32,j;tiles++;
                static const int dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
                for(j=0;j<4;j++) {
                    int nx=cx+dx[j],ny=cy+dy[j],next=ny*32+nx;
                    if(qa_wet(nx,ny)&&!wet_seen[next]){wet_seen[next]=1;q[tail++]=next;}
                }
            }
            if(tiles==1)fail(seed,cell,"isolated one-cell water/deck component",x,y);
        }
        if(d&&!(d==1?qa_deck(x-1,y)==1:qa_deck(x,y-1)==2)) {
            int ex=x,ey=y,wet_neighbor=0,j;
            while(d==1?qa_deck(ex+1,ey)==1:qa_deck(ex,ey+1)==2){if(d==1)ex++;else ey++;}
            qa_bridge_runs++;qa_bridge_landings+=2;
            int ax=d==1?x-1:x,ay=d==1?y:y-1,bx=d==1?ex+1:ex,by=d==1?ey:ey+1;
            if(!qa_dry_landing(ax,ay)||!qa_dry_landing(bx,by))fail(seed,cell,"bridge lacks two dry reachable full-footprint landings",x,y);
            for(j=0;j<=(d==1?ex-x:ey-y);j++) {
                int px=x+(d==1?j:0),py=y+(d==2?j:0);
                wet_neighbor|=d==1?(qa_water(px,py-1)||qa_water(px,py+1)):(qa_water(px-1,py)||qa_water(px+1,py));
            }
            if(!wet_neighbor)fail(seed,cell,"bridge deck does not cross visible water",x,y);
        }
    }
    for(s=0;s<lamp_count;s++)for(i=0;i<lamp_count;i++)if(lamp_seen[i]) {
        int j;for(j=0;j<lamp_count;j++)if(ABS(lamp_x[j]-lamp_x[i])+ABS(lamp_y[j]-lamp_y[i])<=4)lamp_seen[j]=1;
    }
    for(i=0;i<lamp_count;i++)if(!lamp_seen[i]){qa_unanchored_lights++;fail(seed,cell,"lantern lacks route/feature or connected clue chain",lamp_x[i],lamp_y[i]);}
#if BART_FOREST_VARIANT == 32
    int motif=gForestCohesionInfo[1];
    if(gForestCohesionInfo[0]!=1||motif>=6)fail(seed,cell,"invalid room motif ABI",motif,gForestCohesionInfo[0]);
    else qa_motifs[motif]++;
    if(motif==2&&(water_count<13||component_count!=1))fail(seed,cell,"pond motif lacks a coherent thirteen-cell water body",water_count,component_count);
#endif
    qa_landscape_failures+=failures-failures_before;
}


static unsigned digest(const void* data,unsigned n) {
    const unsigned char*p=data;unsigned h=2166136261u;
    while(n--){h^=*p++;h*=16777619u;}return h;
}
#if BART_FOREST_VARIANT >= 31
/* This expected-set contract is independent of the planner's candidate and
   grouping code: forest metadata marks wood; the old native drawing canvases
   contribute only their actual nonzero collision bases. */
static int old_tree(u16 mt) {
    return (mt>=MT_TREE_TOP_NW&&mt<=MT_TREE_TRUNK_E)||
           (mt>=MT_TREE2_0&&mt<=MT_TREE2_5)||
           (mt>=MT_GTREE_0&&mt<=MT_GTREE_11)||
           (mt>=MT_GTREE2_0&&mt<=MT_GTREE2_11)||
           (mt>=MT_BTREE_0&&mt<=MT_BTREE_11)||
           (mt>=MT_BIRCH_0&&mt<=MT_BIRCH_5)||
           (mt>=MT_FIR_0&&mt<=MT_FIR_5)||
           (mt>=MT_SICKTREE_0&&mt<=MT_SICKTREE_5)||
           mt==MT_DEAD_TREE||mt==MT_FOREST_BLIGHT_DEAD_TREE;
}
static void tree_inspect(unsigned seed,int cell) {
    unsigned char owners[1024];int i,x,y,count=gForestTreeStats[1],owned=0,expected=0;
    memset(owners,0,sizeof(owners));
    if(gForestTreeStats[0]!=1||!forest_trees_active()||gForestTreeStats[10]||count<=0||count>FOREST_TREES_MAX)
        fail(seed,cell,"invalid/empty/overflowed live tree scene",count,gForestTreeStats[10]);
    for(i=0;i<count;i++) {
        ForestTree*t=&gForestTrees[i];int w,dx;
        if(t->frame>=12){fail(seed,cell,"invalid native frame",i,t->frame);continue;}
        w=forest_tree_width[t->frame]/16;x=t->x/16;y=(t->y+16)/16;
        if(t->x%16||t->y%16||x<0||y<0||x+w>gRoom.w||y>=gRoom.h||(w!=1&&w!=2)) {
            fail(seed,cell,"tree base outside logical room",x,y);continue;
        }
        trees++;frame_seen[t->frame]++;
        stage_state[gWorld.cells[cell].stage<4?gWorld.cells[cell].stage:3][forest_tree_state[t->frame]]++;
        for(dx=0;dx<w;dx++) {
            int at=y*32+x+dx,mt=room_get(x+dx,y);root_checks++;owned++;
            if(++owners[at]!=1||gForestTreeRoots[at]!=i+1)
                fail(seed,cell,"base cell lacks unique matching native tree owner",x+dx,y);
            if(!metatile_coll[mt]||(!forest_v2_canopy_kind[mt]&&!old_tree(mt)))
                fail(seed,cell,"tree invents a blocker over unrelated terrain",x+dx,y);
            if(t->root_mask[dx]!=metatile_coll[mt])
                fail(seed,cell,"native root record changes original collision mask",x+dx,y);
        }
    }
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int mt=room_get(x,y),at=y*32+x;
        int root=metatile_coll[mt]&&(forest_v2_canopy_kind[mt]||old_tree(mt));
        if(root){expected++;if(forest_v2_canopy_kind[mt])wood_cells++;else authored_cells++;}
        if(root!=(owners[at]!=0)||root!=(gForestTreeRoots[at]!=0))
            fail(seed,cell,"solid tree base and native picture ownership differ",x,y);
    }
    if(owned!=expected||expected!=gForestTreeStats[2]+gForestTreeStats[3])
        fail(seed,cell,"tree/base totals disagree",owned,expected);
}
static unsigned tree_digest(void) {
    return digest(gForestTrees,gForestTreeStats[1]*sizeof(ForestTree))^
           digest(gForestTreeRoots,sizeof(gForestTreeRoots))^digest(gForestTreeStats,sizeof(gForestTreeStats));
}
static void cache_check(unsigned seed,int cell) {
    Room held=gRoom;unsigned before=tree_digest();int x,y;
    /* Live redraw/menu return must not reroll trees after a clearable bush
       exposes floor. A fresh native room entry resets this cache separately. */
    for(y=2;y<gRoom.h-2;y++)for(x=1;x<gRoom.w-1;x++) {
        int mt=room_get(x,y);
        if(mt==MT_BUSH||mt==MT_THORN||mt==MT_TALL_GRASS) {
            room_set(x,y,MT_MOSS0);room_build_solid();forest_trees_plan();cache_checks++;
            if(before!=tree_digest())fail(seed,cell,"live bush-clear redraw rerolls resident trees",x,y);
            gRoom=held;return;
        }
    }
    forest_trees_plan();cache_checks++;
    if(before!=tree_digest())fail(seed,cell,"live same-room redraw rerolls resident trees",0,0);
}
#endif
static void build(int cell) {
    gGame.cell=cell;roomgen_build_internal(cell,FALSE);room_build_solid();
#if BART_FOREST_VARIANT >= 31
    /* The hardware-native entry pipeline calls tiles_load(), which clears
       the live scene cache. Suppress VRAM but preserve that lifecycle here. */
    forest_trees_reset();
    unsigned prior=digest(&gRoom,sizeof(gRoom));
    forest_trees_plan();
    if(prior!=digest(&gRoom,sizeof(gRoom)))fail(gWorld.seed,cell,"tree plan mutates semantic room/collision",0,0);
#endif
}

static unsigned long qa_relic_cases,qa_relic_layout_failures;
static void qa_relic_collection(unsigned seed,int cell) {
    u8 paths[32*24],lamps[32*24],flags=gWorld.cells[cell].flags;int x,y,mismatch=0,shown=0;
    if(gWorld.cells[cell].role!=ROLE_RELIC)return;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x;paths[q]=qa_path(x,y);lamps[q]=room_get(x,y)==MT_LANTERN_POST;
    }
    gWorld.cells[cell].flags|=CF_RELIC_TAKEN;build(cell);qa_relic_cases++;
    if(gSpots.has_relic)mismatch=1;
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int q=y*32+x;
        if(paths[q]!=qa_path(x,y)||lamps[q]!=(room_get(x,y)==MT_LANTERN_POST)) {
            if(shown++<4)printf("RELIC_DIFF seed=%u cell=%d pos=%d,%d road=%d->%d lamp=%d->%d\n",seed,cell,x,y,paths[q],qa_path(x,y),lamps[q],room_get(x,y)==MT_LANTERN_POST);
            mismatch=1;
        }
    }
    if(mismatch){qa_relic_layout_failures++;fail(seed,cell,"relic collection changes remembered trail/lantern layout",0,0);}
    gWorld.cells[cell].flags=flags;build(cell);
}

int main(int argc,char**argv) {
    unsigned n=argc>1?strtoul(argv[1],0,0):512,k;int cell;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    for(k=1;k<=n;k++) {
        unsigned seed=k<=8?(unsigned[]){0,1,7,42,0xb4a7,0xdeadbeef,0xffffffff,0x80000000}[k-1]:hash32(0xd2170e5u,k);
        world_generate(seed);
        for(cell=0;cell<CELLS;cell++) {
            unsigned before;RoomSpots spots;
            build(cell);inspect(seed,cell);qa_landscape(seed,cell);if(k<=32)feet_inspect(seed,cell);rooms++;
#if BART_FOREST_VARIANT >= 31
            unsigned tree_before=tree_digest();unsigned info_before=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo));tree_inspect(seed,cell);
            if(k<=32) {
                u8 marks[MP_COUNT*2];
                unsigned room_before=digest(&gRoom,sizeof(gRoom));
                roomgen_preview_events((cell+7)%CELLS,marks);preview_checks++;if(info_before!=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo)))fail(seed,cell,"paused-map preview corrupts live motif metadata",0,0);
                if(tree_before!=tree_digest()||room_before!=digest(&gRoom,sizeof(gRoom)))
                    fail(seed,cell,"paused-map preview corrupts resident trees or Room",0,0);
                cache_check(seed,cell);
            }
#endif
            before=digest(&gRoom,sizeof(gRoom));spots=gSpots;
            build(cell);determinism++;
            if(before!=digest(&gRoom,sizeof(gRoom))||digest(&spots,sizeof(spots))!=digest(&gSpots,sizeof(gSpots)))
                fail(seed,cell,"return build is nondeterministic",0,0);
#if BART_FOREST_VARIANT >= 31
            if(tree_before!=tree_digest())fail(seed,cell,"return tree plan is nondeterministic",0,0);if(info_before!=digest(gForestCohesionInfo,sizeof(gForestCohesionInfo)))fail(seed,cell,"return room motif metadata is nondeterministic",0,0);
#endif
            qa_relic_collection(seed,cell);
            if(k<=32) {
                u8 old_open=gWorld.cells[cell].opened;
                gWorld.cells[cell].opened|=15|CELL_POCKET_OPEN;
                build(cell);inspect(seed,cell);feet_inspect(seed,cell);opened_state_rooms++;
#if BART_FOREST_VARIANT >= 31
                tree_inspect(seed,cell);
#endif
                gWorld.cells[cell].opened=old_open;
            }
        }
        if(k%64==0){printf("PROGRESS seeds=%u rooms=%lu failures=%d\n",k,rooms,failures);fflush(stdout);}
        if(failures>100)break;
    }
    printf("RESULT {\"requested_seeds\":%u,\"rooms\":%lu,\"opened_state_rooms\":%lu,\"approaches\":%lu,\"pockets\":%lu,\"determinism\":%lu,\"boundary_inventory_checks\":%lu,\"feet_box_rooms\":%lu,\"trees\":%lu,\"wood_cells\":%lu,\"authored_cells\":%lu,\"root_ownership_checks\":%lu,\"preview_preservation_checks\":%lu,\"live_scene_cache_checks\":%lu,\"frame_counts\":[",n,rooms,opened_state_rooms,approaches,pockets,determinism,boundaries,feet_rooms,trees,wood_cells,authored_cells,root_checks,preview_checks,cache_checks);
    for(cell=0;cell<12;cell++)printf("%s%lu",cell?",":"",frame_seen[cell]);
    printf("],\"stage_state_counts\":[");
    for(cell=0;cell<4;cell++)printf("%s[%lu,%lu,%lu]",cell?",":"",stage_state[cell][0],stage_state[cell][1],stage_state[cell][2]);
    printf("],\"landscape\":{\"water_components\":%lu,\"water_cells\":%lu,\"bridge_runs\":%lu,\"bridge_landing_checks\":%lu,\"lantern_posts\":%lu,\"unanchored_lanterns\":%lu,\"detail_cells\":%lu,\"details_near_material_context\":%lu,\"ledge_cells\":%lu,\"failures\":%lu,\"trail_refine_calls\":%lu,\"trail_physics_failures\":%lu,\"relic_collection_cases\":%lu,\"relic_layout_failures\":%lu,\"motifs\":[%lu,%lu,%lu,%lu,%lu,%lu]},\"failures\":%d}\n",qa_water_components,qa_water_cells,qa_bridge_runs,qa_bridge_landings,qa_lights,qa_unanchored_lights,qa_detail_cells,qa_context_details,qa_ledge_cells,qa_landscape_failures,qa_trail_calls,qa_trail_physics_failures,qa_relic_cases,qa_relic_layout_failures,qa_motifs[0],qa_motifs[1],qa_motifs[2],qa_motifs[3],qa_motifs[4],qa_motifs[5],failures);
    return failures?1:0;
}
