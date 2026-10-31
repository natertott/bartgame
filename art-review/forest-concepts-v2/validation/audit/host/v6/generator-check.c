
#include <stdio.h>
#include <stdlib.h>
#include "game.h"
#include "world.h"
#include "room.h"
#include "roomgen.h"
GameState gGame;
u32 gFrame;
/* Include the actual generator, allowing its existing non-render build path.
   No generator implementation or placement predicate is reproduced here. */
#include "/workspace/bartgame/bartgame/src/roomgen.c"
static unsigned char seen[4096];
static int queue[4096], failures, printed;
static unsigned long rooms, logs, pockets, requirements, worlds, arches;
static const int landing[4][2]={{15,2},{30,11},{15,22},{1,11}};
static void fail(unsigned seed,int cell,const char* reason,int x,int y) {
    failures++;
    if(printed++<24)printf("FAIL seed=%u cell=%d %s (%d,%d)\n",seed,cell,reason,x,y);
}
static unsigned graph_reach(int items) {
    unsigned seen=1u<<gWorld.entry;int changed=1,i,side;
    while(changed) {
        changed=0;
        for(i=0;i<CELLS;i++)if(seen&(1u<<i))for(side=0;side<4;side++) {
            int gate=gWorld.cells[i].gate[side],nx=i%5+(side==1)-(side==3),ny=i/5+(side==2)-(side==0),n;
            if(nx<0||ny<0||nx>=5||ny>=5)continue;
            n=ny*5+nx;
            if(gate==GATE_WALL||gate==GATE_LOCK||gate==GATE_EXIT||
               (gate==GATE_CRACK&&items<1)||(gate==GATE_WEB&&items<2)||(gate==GATE_CHASM&&items<3))continue;
            if(!(seen&(1u<<n))){seen|=1u<<n;changed=1;}
        }
    }
    return seen;
}
static void world_check(unsigned seed) {
    int item,cell,side;worlds++;
    for(item=0;item<3;item++) {
        int target=gWorld.key_cell[item];unsigned seen=graph_reach(item);
        if(!(seen&(1u<<target)))fail(seed,target,"mandatory prize blocked by future item/lock",item,0);
        if(seen&(1u<<gWorld.goal))fail(seed,gWorld.goal,"boss bypasses mandatory event",item,0);
        if(gWorld.cells[target].role!=ROLE_KEYITEM||gWorld.cells[target].role_arg!=item+1||!gWorld.myst[target])
            fail(seed,target,"mandatory task/reward missing",item,0);
        if(MYST_KIND(gWorld.myst[target])==MK_TORCHES||MYST_KIND(gWorld.myst[target])==MK_BOULDERS)
            fail(seed,target,"mandatory task needs unavailable optional equipment",item,0);
    }
    if(!(graph_reach(3)&(1u<<gWorld.goal)))fail(seed,gWorld.goal,"boss inaccessible with all three items",0,0);
    for(cell=0;cell<CELLS;cell++)for(side=0;side<4;side++) {
        int nx=cell%5+(side==1)-(side==3),ny=cell/5+(side==2)-(side==0);
        if(nx>=0&&ny>=0&&nx<5&&ny<5&&gWorld.cells[cell].gate[side]!=gWorld.cells[ny*5+nx].gate[(side+2)%4])
            fail(seed,cell,"asymmetric neighboring gates",side,0);
    }
}
static int blocked(int qx,int qy,int items) {
    int x=qx/2,y=qy/2,t;
    if(qx<0||qy<0||qx>=gRoom.w*2||qy>=gRoom.h*2)return 1;
    t=metatile_type[gRoom.ground[y*32+x]];
    if(t==TT_THORN||t==TT_LIFT1)return 0;
    if((items&1)&&t==TT_CRACK)return 0;
    if((items&2)&&t==TT_WEB)return 0;
    if((items&4)&&t==TT_PIT)return 0;
    if(t==TT_WATER||t==TT_PIT||t==TT_MYST||t==TT_EXIT)return 1;
    return gRoom.solid[qy*64+qx]!=0;
}
static void flood(int x,int y,int items) {
    int i,head=0,tail=0,dx,dy;
    static const int ax[4]={0,1,0,-1},ay[4]={-1,0,1,0};
    memset(seen,0,sizeof(seen));
    for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++) {
        int qx=x*2+dx,qy=y*2+dy,p=qy*64+qx;
        if(!blocked(qx,qy,items)&&!seen[p]){seen[p]=1;queue[tail++]=p;}
    }
    while(head<tail) {
        int p=queue[head++],qx=p%64,qy=p/64;
        for(i=0;i<4;i++) {
            int nx=qx+ax[i],ny=qy+ay[i],n=ny*64+nx;
            if(!blocked(nx,ny,items)&&!seen[n]){seen[n]=1;queue[tail++]=n;}
        }
    }
}
static int reaches(int x,int y) {
    if(x<0||y<0||x>=gRoom.w||y>=gRoom.h)return 0;
    return seen[y*2*64+x*2]||seen[y*2*64+x*2+1]||seen[(y*2+1)*64+x*2]||seen[(y*2+1)*64+x*2+1];
}
static void target(unsigned seed,int cell,const char*name,Spot p,int offset) {
    requirements++;
    if(!reaches(p.x,p.y+offset))fail(seed,cell,name,p.x,p.y+offset);
}
static void inspect(unsigned seed,int cell) {
    Cell* c=&gWorld.cells[cell];int side,start=-1,i,x,y;
    for(side=0;side<4;side++)if(c->gate[side]){start=side;break;}
    if(start<0){fail(seed,cell,"no room entrance",0,0);return;}
    room_build_solid();flood(landing[start][0],landing[start][1],0);
    for(side=0;side<4;side++)if(c->gate[side]&&!reaches(landing[side][0],landing[side][1]))
        fail(seed,cell,"door landing disconnected",landing[side][0],landing[side][1]);
    if(gSpots.has_chest)target(seed,cell,"chest approach",gSpots.chest,1);
    if(gSpots.has_npc)target(seed,cell,"NPC approach",gSpots.npc,1);
    if(gSpots.has_relic)target(seed,cell,"relic approach",gSpots.relic,0);
    if(gSpots.has_boss)target(seed,cell,"boss approach",gSpots.boss,0);
    if(gSpots.has_shrine)target(seed,cell,"shrine approach",gSpots.shrine,1);
    if(gSpots.has_mouth)target(seed,cell,"mouth approach",gSpots.mouth,1);
    if(c->role==ROLE_KEYITEM&&!gSpots.has_mouth)fail(seed,cell,"mandatory event has no mouth",0,0);
    if(c->role==ROLE_NPC_TORCH&&gSpots.torch_count!=4)fail(seed,cell,"torch quest count",0,0);
    for(i=0;i<gSpots.torch_count;i++)target(seed,cell,"torch approach",gSpots.torches[i],1);
    for(i=0;i<gSpots.spawn_count;i++)target(seed,cell,"spawn approach",gSpots.spawns[i],0);
    /* A two-cell log has two occupied cells, actual collision under both,
       and a safe original floor. This checks resulting geometry, not the
       generator's candidate/placement condition. */
    for(y=0;y<gRoom.h;y++)for(x=0;x<gRoom.w;x++) {
        int at=y*32+x,mt=gRoom.ground[at];
        if(mt==MT_HLOG_0) {
            int j;logs++;
            if(x+1>=gRoom.w||gRoom.ground[at+1]!=MT_HLOG_1)fail(seed,cell,"incomplete large log",x,y);
            for(j=0;j<2;j++) {
                int u=gRoom.underlay[at+j],dx,dy;
                if(metatile_coll[u]||metatile_type[u]==TT_WATER||metatile_type[u]==TT_PIT)
                    fail(seed,cell,"log substrate is not dry passable ground",x+j,y);
                for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
                    if(!gRoom.solid[(y*2+dy)*64+(x+j)*2+dx])
                        fail(seed,cell,"large log collision misses visible cell",x+j,y);
            }
        }
        if(mt==MT_HLOG_1&&(x<1||gRoom.ground[at-1]!=MT_HLOG_0))fail(seed,cell,"orphan large log half",x,y);
        if(gRoom.overlay[at]==MT_F2_ARCH_0) {
            int j;arches++;
            if(x+1>=gRoom.w||gRoom.overlay[at+1]!=MT_F2_ARCH_1)fail(seed,cell,"incomplete overhead arch",x,y);
            for(j=0;j<2;j++) {
                int ground=gRoom.ground[at+j],dx,dy;
                if(metatile_coll[ground]||metatile_type[ground]==TT_WATER||metatile_type[ground]==TT_PIT)
                    fail(seed,cell,"underpass visible lane is not actually passable",x+j,y);
                for(dy=0;dy<2;dy++)for(dx=0;dx<2;dx++)
                    if(gRoom.solid[(y*2+dy)*64+(x+j)*2+dx])fail(seed,cell,"underpass quarter is blocked",x+j,y);
            }
        }
        if(gRoom.overlay[at]==MT_F2_ARCH_1&&(x<1||gRoom.overlay[at-1]!=MT_F2_ARCH_0))fail(seed,cell,"orphan overhead arch half",x,y);
    }
    if(gSpots.has_treasure&&gSpots.pocket_kind>=1&&gSpots.pocket_kind<=3) {
        int item=1<<(gSpots.pocket_kind-1),opened=c->opened&CELL_POCKET_OPEN;
        Spot p=gSpots.treasure;pockets++;
        if(!opened&&reaches(p.x,p.y))fail(seed,cell,"item pocket bypassable with no future item",p.x,p.y);
        flood(landing[start][0],landing[start][1],item);
        if(!reaches(p.x,p.y))fail(seed,cell,"pocket inaccessible with its required item",p.x,p.y);
        flood(landing[start][0],landing[start][1],7^item);
        if(!opened&&reaches(p.x,p.y))fail(seed,cell,"pocket accepts wrong items",p.x,p.y);
    }
}
int main(int argc,char**argv) {
    unsigned seed,count=argc>1?strtoul(argv[1],0,0):20000;int cell,profile;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    for(seed=1;seed<=count;seed++) {
        for(profile=0;profile<WORLD_PROFILE_COUNT;profile++) {
            world_generate_tuned(seed,&world_profiles[profile]);world_check(seed);
        }
        world_generate(seed);
        for(cell=0;cell<CELLS;cell++) {
            gGame.cell=cell;roomgen_build_internal(cell,FALSE);inspect(seed,cell);rooms++;
        }
        if(seed%500==0){printf("PROGRESS seeds=%u rooms=%lu failures=%d\n",seed,rooms,failures);fflush(stdout);}
        if(failures>100)break;
    }
    printf("RESULT {\"requested_seeds\":%u,\"seeds\":%lu,\"world_graphs\":%lu,\"rooms\":%lu,\"logs\":%lu,\"underpasses\":%lu,\"item_pockets\":%lu,\"required_approaches\":%lu,\"failures\":%d}\n",count,rooms/CELLS,worlds,rooms,logs,arches,pockets,requirements,failures);
    return failures?1:0;
}
