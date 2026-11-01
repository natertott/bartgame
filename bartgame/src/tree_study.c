/* A compact tree-art review scene. This is explicitly diagnostic, not a
   replacement for forest generation or a new canopy placement grammar. */
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT == 30
#include "tree_study.h"
#include "video.h"
#include "room.h"
#include "game.h"
#include "world.h"
#include "roomgen.h"
#include "actor.h"
#include "player.h"
#include "canopy_scene.h"

TreeStudyPlacement gTreeStudyPlacements[TREE_STUDY_MAX_PLACEMENTS] EWRAM_BSS;
u16 gTreeStudyInfo[16] EWRAM_BSS;
volatile u16 gTreeStudyRequest;
volatile u8 gTreeStudyPending;
u8 gTreeStudyActive;
static u8 sPreviousAnimation;

#define STUDY_SB_TREES 24
#define STUDY_SB_FLOOR 28
#define STUDY_W 15
#define STUDY_H 10

void tree_study_reset(void) {
    if(gTreeStudyActive)gAnimTiles=sPreviousAnimation;
    gTreeStudyActive=0;
}

int tree_study_priority(int px,int py,int z,int width,int height,int priority) {
    int i,front=0,behind=0;
    if(!gTreeStudyActive || (priority!=1 && priority!=2))return priority;
    int left=px-width/2,right=px+width/2;
    int top=py-z-height,bottom=py-z;
    for(i=0;i<gTreeStudyInfo[4];i++) {
        const TreeStudyPlacement* p=&gTreeStudyPlacements[i];
        if(right<=p->x || left>=p->x+p->w || bottom<=p->y || top>=p->y+p->h)continue;
        /* Ground contact, not top-of-picture position, establishes which
           side of this diagnostic tree the ordinary actor occupies. */
        if(py>=p->y+p->anchor_y)front=1;
        else behind=1;
    }
    if(behind)return 2;
    return front?1:priority;
}

static vu16* study_map(int screen,int x8,int y8) {
    int block=screen+((y8>>5)<<1)+(x8>>5);
    return SCREENBLOCK(block)+(y8&31)*32+(x8&31);
}

static int study_frame(int size,int variety,int state) {
    int i;
    for(i=0;i<TREE_STUDY_COUNT;i++) {
        const TreeStudyFrame* f=&tree_study_frames[i];
        if(f->size==size && f->variety==variety && f->state==state)return i;
    }
    return -1;
}

static void study_place(int frame,int x,int y) {
    int tx,ty,mx,my;
    if(frame<0 || frame>=TREE_STUDY_COUNT ||
       gTreeStudyInfo[4]>=TREE_STUDY_MAX_PLACEMENTS)return;
    const TreeStudyFrame* f=&tree_study_frames[frame];
    int width=f->w*8,height=f->h*8;
    if(x<0 || y<0 || x+width>STUDY_W*16 || y+height>STUDY_H*16)return;
    TreeStudyPlacement* p=&gTreeStudyPlacements[gTreeStudyInfo[4]++];
    p->frame=frame;p->x=x;p->y=y;p->w=width;p->h=height;
    /* A separate shallow root footprint; the crown canvas is not a full
       rectangle of collision. Both sizes use a centered16x8 root base. */
    p->root_x8=(x+width/2-8)/8;p->root_y8=(y+height-8)/8;
    p->root_w8=2;p->root_h8=1;p->anchor_y=30;
    for(ty=0;ty<f->h;ty++)for(tx=0;tx<f->w;tx++)
        *study_map(STUDY_SB_TREES,x/8+tx,y/8+ty)=f->map[ty*f->w+tx];
    for(ty=0;ty<p->root_h8;ty++)for(tx=0;tx<p->root_w8;tx++)
        gRoom.solid[(p->root_y8+ty)*64+p->root_x8+tx]=1;
    /* Ownership only: the existing native-pixel Bloom safeguard can inspect
       these real BG1 pixels without changing semantic room/canopy artwork. */
    for(my=y/16;my<=(y+height-1)/16;my++)
        for(mx=x/16;mx<=(x+width-1)/16;mx++)
            gRoomVisualOverlay[my*ROOM_MAX_W+mx]=MT_CANOPY;
}

void tree_study_begin(void) {
    static const u16 logical_floor[3]={MT_MOSS0,MT_PATH,MT_BLIGHT_FLOOR};
    int x,y,k,request,floor,layout;
    if(!gTreeStudyPending)return;
    gTreeStudyPending=0;
    request=gTreeStudyRequest%6;floor=request%3;layout=request/3;
    memset(gTreeStudyInfo,0,sizeof(gTreeStudyInfo));
    memset(gTreeStudyPlacements,0,sizeof(gTreeStudyPlacements));
    gTreeStudyInfo[0]=1;gTreeStudyInfo[1]=request;
    gTreeStudyInfo[2]=layout;gTreeStudyInfo[3]=floor;
    gTreeStudyInfo[5]=TREE_STUDY_TILE_COUNT;
    gTreeStudyInfo[6]=TREE_STUDY_PALETTE_SLOT;
    gTreeStudyInfo[7]=logical_floor[floor];
    gTreeStudyInfo[8]=120;gTreeStudyInfo[9]=144;
    gTreeStudyInfo[11]=TREE_STUDY_COUNT;

    if(!gTreeStudyActive)sPreviousAnimation=gAnimTiles;
    gGame.area=AREA_FOREST;gGame.state=GS_PLAY;
    tiles_load(TS_FOREST); /* restores the real forest ground palette banks */
    room_clear(STUDY_W,STUDY_H,logical_floor[floor]);
    memset(&gSpots,0,sizeof(gSpots));
    room_render();
    /* Sprite allocation resets enlarged scenery and renders the room again.
       Finish that normal preparation BEFORE installing the review atlas. */
    actors_clear();
    sprites_reset();
    player_init(120,144,FACE_N);
    canopy_scene_reset();
    /* No world tile animation or area-palette pulse may write into the
       compact review atlas. The normal world is restored by tiles_load. */
    gAnimTiles=0;
    dma3_copy32(tree_study_tiles,CHARBLOCK(0),TREE_STUDY_TILE_COUNT*32);
    pal_set_bg(TREE_STUDY_PALETTE_SLOT,tree_study_palette);
    dma3_fill32(0,SCREENBLOCK(STUDY_SB_TREES),0x2000);
    dma3_fill32(0,SCREENBLOCK(STUDY_SB_FLOOR),0x2000);
    for(y=0;y<STUDY_H;y++)for(x=0;x<STUDY_W;x++) {
        int q;
        gRoomVisualGround[y*ROOM_MAX_W+x]=logical_floor[floor];
        gRoomVisualOverlay[y*ROOM_MAX_W+x]=MT_NONE;
        for(q=0;q<4;q++)
            *study_map(STUDY_SB_FLOOR,x*2+(q&1),y*2+(q>>1))=tree_study_floor[floor][q];
    }
    if(!layout) {
        /* Source-contract catalog in a running game: broad row then narrow
           row, each with healthy/sick/dead and both silhouette varieties. */
        for(k=0;k<6;k++) {
            study_place(study_frame(0,k&1,k/2),k*40,24);
            study_place(study_frame(1,k&1,k/2),k*40+8,80);
        }
    } else {
        /* Repeated trees, three visible states, and an open center corridor
           for ordinary Bloom movement. Rectangles never overlap. */
        for(y=0;y<3;y++)for(x=0;x<4;x++) {
            static const u8 columns[4]={0,40,160,200};
            int size=(x==1 || x==2) && y==1;
            int state=(y+(x>>1))%3;
            study_place(study_frame(size,(x+y)&1,state),columns[x]+(size?8:0),24+y*40);
        }
    }
    camera_update(120,128,TRUE);
    REG_BLDCNT=0;REG_BLDY=0;
    gTreeStudyInfo[10]=1;
    gTreeStudyActive=1;
}
#endif
