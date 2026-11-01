
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
#include "/workspace/bartgame/bartgame/src/roomgen.c"
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
int main(int argc,char**argv) {
    unsigned n=argc>1?strtoul(argv[1],0,0):512,k;int cell;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    for(k=1;k<=n;k++) {
        unsigned seed=k<=8?(unsigned[]){0,1,7,42,0xb4a7,0xdeadbeef,0xffffffff,0x80000000}[k-1]:hash32(0xd2170e5u,k);
        world_generate(seed);
        for(cell=0;cell<CELLS;cell++) {
            unsigned before;RoomSpots spots;
            build(cell);inspect(seed,cell);if(k<=32)feet_inspect(seed,cell);rooms++;
#if BART_FOREST_VARIANT >= 31
            unsigned tree_before=tree_digest();tree_inspect(seed,cell);
            if(k<=32) {
                u8 marks[MP_COUNT*2];
                unsigned room_before=digest(&gRoom,sizeof(gRoom));
                roomgen_preview_events((cell+7)%CELLS,marks);preview_checks++;
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
            if(tree_before!=tree_digest())fail(seed,cell,"return tree plan is nondeterministic",0,0);
#endif
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
    printf("],\"failures\":%d}\n",failures);
    return failures?1:0;
}
