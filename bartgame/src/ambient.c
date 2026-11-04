/* Native 1--7px specular glints. Wet leaves, metal and dirty water can be
   beautiful without turning every walkable tile into an item marker. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "world.h"
#include "game.h"
#include "text.h"
#include "ambient.h"

#define AMBIENT_MAX_SITES (ROOM_MAX_W * ROOM_MAX_H)
#define AMBIENT_VIEW_SITES 24
typedef struct {
    s16 x,y;
    u8 phase,foreground,tx,ty;
} AmbientSite;
static AmbientSite sAmbientSites[AMBIENT_MAX_SITES] EWRAM_BSS;
static u16 sAmbientTile;
static u32 sAmbientFrame;
typedef struct {
    u16 site;
    u8 material;
} AmbientViewSite;
static AmbientViewSite sAmbientView[AMBIENT_VIEW_SITES] EWRAM_BSS;
static u32 sAmbientViewRevision;
static s16 sAmbientViewCamX,sAmbientViewCamY;
static u8 sAmbientViewCount,sAmbientViewValid;
u16 gAmbientSiteCount;
u8 gAmbientPotential,gAmbientVisible,gAmbientPeaks;

static bool8 incidental(u16 mt) {
    return mt==MT_NONE || mt==MT_SPARKLE || mt==MT_SPARKLE_WHITE || mt==MT_BLIGHT_MIST;
}

/* Return which displayed material receives the highlight, not merely what
   happens to share its cell. A nonreflective authored crown hides the floor. */
static int surface(int x,int y) {
    u16 ground=room_get(x,y),overlay=room_get_overlay(x,y);
    if(!incidental(overlay)) {
        if(!metatile_glitter[overlay])return 0;
        return overlay==MT_MYST_SWITCH || overlay==MT_MYST_SWITCH_DOWN ? 1 : 2;
    }
    if(ground==MT_NONE || !metatile_glitter[ground])return 0;
    if(metatile_prop[ground])return metatile_coll[ground] ? 2 : 1;
    if(metatile_type[ground]==TT_CHEST ||
       metatile_type[ground]==TT_CHEST_OPEN)return 2;
    return 1;
}

void ambient_room_reset(void) {
    int tx,ty,k;
    gAmbientSiteCount=gAmbientPotential=gAmbientVisible=gAmbientPeaks=0;
    sAmbientTile=0;
    sAmbientFrame=0xFFFFFFFF;
    sAmbientViewValid=0;
    /* Every authored reflective cell can contribute one glint. The viewport
       still selects at most 24 sites and phases them independently; dry
       paths remain empty while wet leaves and stone can glitter richly. */
    for(ty=0;ty<gRoom.h;ty++) for(tx=0;tx<gRoom.w;tx++) {
        int material=surface(tx,ty);
        if(!material)continue;
        u32 h=hash32(gWorld.seed,(gGame.area*997+gGame.cell*131+ty*ROOM_MAX_W+tx)*97);
        AmbientSite* s=&sAmbientSites[gAmbientSiteCount++];
        s->tx=tx;s->ty=ty;
        s->x=tx*16+4+((h>>8)&7);
        s->y=ty*16+4+((h>>12)&7);
        s->phase=(h>>16)&63;
        s->foreground=material==2;
    }
    /* A stable spatial shuffle avoids spending the viewport's finite glint
       budget only along its top edge in dense, wet rooms. */
    for(k=gAmbientSiteCount-1;k>0;k--) {
        int j=hash32(gWorld.seed,(gGame.area*313+gGame.cell*67+k)*17)%(k+1);
        AmbientSite old=sAmbientSites[k];
        sAmbientSites[k]=sAmbientSites[j];sAmbientSites[j]=old;
    }
    if(gAmbientSiteCount)
        sAmbientTile=sprite_load_sheet(SHEET_GLITTER);
}

typedef struct {
    int left,right,top,bottom,feet;
} AmbientActorBox;

static int foreground_boxes(AmbientActorBox* boxes) {
    int i,count=0;
    /* A sheen on foreground material should not be pasted onto a character
       who has walked in front of that material's southern edge. The boxes
       are identical to the per-glint test; derive each actor's stable
       visual extent only once for this foreground pass. */
    for(i=0;i<ACTOR_MAX;i++) {
        const Actor* a=&gActors[i];
        if(a->kind!=AK_PLAYER && a->kind!=AK_ENEMY && a->kind!=AK_NPC)continue;
        if(a->flags&AF_HIDDEN)continue;
        int px=PX(a->x),py=PX(a->y),z=PX(a->z);
        int width,height;
        actor_visual_size(a,&width,&height);
        int left=px-width/2,right=px+width/2,top=py-z-height,bottom=py-z;
        /* Every selected glint lies in this exact inner viewport. A body
           outside it cannot cover one, regardless of its feet/depth. */
        if(right<=gCamX+4 || left>=gCamX+236 ||
           bottom<=gCamY+HUD_HEIGHT_PIXELS+4 || top>=gCamY+156)continue;
        AmbientActorBox* b=&boxes[count++];
        b->left=left;b->right=right;
        b->top=top;b->bottom=bottom;b->feet=py;
    }
    return count;
}

static bool8 actor_in_front(const AmbientSite* site,const AmbientActorBox* boxes,int count) {
    int i,south=(site->ty+1)*16;
    for(i=0;i<count;i++) {
        const AmbientActorBox* b=&boxes[i];
        if(b->feet>=south && site->x>=b->left && site->x<b->right &&
           site->y>=b->top && site->y<b->bottom)return TRUE;
    }
    return FALSE;
}

static void select_view(void) {
    int i,potential=0;
    /* Keep the original shuffled order and its first24 surviving material
       sites. Selection depends only on camera and live room IDs, not phase
       or actors. The room revision catches opened/broken material and
       preview restoration; reset invalidates changes to the site list. */
    for(i=0;i<gAmbientSiteCount && potential<AMBIENT_VIEW_SITES;i++) {
        const AmbientSite* s=&sAmbientSites[i];
        int x=s->x-gCamX,y=s->y-gCamY;
        if(x<4 || x>=236 || y<HUD_HEIGHT_PIXELS+4 || y>=156)continue;
        int material=surface(s->tx,s->ty);
        if(!material)continue; /* a gate may have opened since room creation */
        sAmbientView[potential].site=i;
        sAmbientView[potential].material=material;
        potential++;
    }
    sAmbientViewCount=potential;
    sAmbientViewRevision=gRoomRevision;
    sAmbientViewCamX=gCamX;sAmbientViewCamY=gCamY;
    sAmbientViewValid=1;
}

static void draw_view(bool8 foreground,AmbientActorBox* boxes) {
    const SpriteSheet* sh=&sheets[SHEET_GLITTER];
    /* This is the generated sheet's literal frame count, not a runtime
       division of its immutable tile descriptor on both draw passes. */
    const int frame_count=SHEET_GLITTER_FRAMES;
    int i,box_count=-1;
    for(i=0;i<sAmbientViewCount;i++) {
        const AmbientViewSite* v=&sAmbientView[i];
        const AmbientSite* s=&sAmbientSites[v->site];
        if((v->material==2)!=foreground)continue;
        int phase=(gFrame+s->phase)&63;
        if(phase>=32 || frame_count<2)continue;
        if(foreground) {
            if(box_count<0)box_count=foreground_boxes(boxes);
            if(actor_in_front(s,boxes,box_count))continue;
        }
        /* Frame zero is blank. Five drawn stages swell into one star and
           fade, then remain dark for the other half of the 64-frame cycle. */
        int frame=1+phase*(frame_count-1)/32;
        if(gOamCount>=(foreground?80:120))continue;
        int x=s->x-gCamX,y=s->y-gCamY;
        draw_sprite(x-3,y-3,SHEET_GLITTER,sAmbientTile,frame,0,foreground?1:2,sh->pal);
        gAmbientVisible++;
        if(frame==frame_count/2)gAmbientPeaks++;
    }
    gAmbientPotential=sAmbientViewCount;
}

static void __attribute__((noinline)) draw_foreground(void) {
    /* Bounded transient IWRAM stack storage, released before Bloom's own
       visibility mask is prepared. No per-glint or persistent actor cache. */
    AmbientActorBox boxes[ACTOR_MAX];
    draw_view(TRUE,boxes);
}

void ambient_draw(bool8 foreground) {
    if(sAmbientFrame!=gFrame) {
        sAmbientFrame=gFrame;
        gAmbientPotential=gAmbientVisible=gAmbientPeaks=0;
    }
    if(!sAmbientTile)return;
    if(!sAmbientViewValid || sAmbientViewRevision!=gRoomRevision ||
       sAmbientViewCamX!=gCamX || sAmbientViewCamY!=gCamY)select_view();
    if(foreground)draw_foreground();
    else draw_view(FALSE,NULL);
}
