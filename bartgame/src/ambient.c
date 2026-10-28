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

#define AMBIENT_MAX_SITES 256
#define AMBIENT_VIEW_SITES 24
typedef struct {
    s16 x,y;
    u8 phase,foreground,tx,ty;
} AmbientSite;
static AmbientSite sAmbientSites[AMBIENT_MAX_SITES] EWRAM_BSS;
static u16 sAmbientTile;
static u32 sAmbientFrame;
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
    int bx,by,k;
    gAmbientSiteCount=gAmbientPotential=gAmbientVisible=gAmbientPeaks=0;
    sAmbientTile=0;
    sAmbientFrame=0xFFFFFFFF;
    /* At most one reflection in each 32px patch. Choose an authored shiny
       material within it, so a nearby dry path never receives a stray star. */
    for(by=0;by<gRoom.h;by+=2) for(bx=0;bx<gRoom.w;bx+=2) {
        u32 h=hash32(gWorld.seed,(gGame.area*997+gGame.cell*131+by*32+bx)*97);
        for(k=0;k<4;k++) {
            int at=(k+(h&3))&3,tx=bx+(at&1),ty=by+(at>>1);
            if(tx>=gRoom.w || ty>=gRoom.h)continue;
            int material=surface(tx,ty);
            if(!material)continue;
            AmbientSite* s=&sAmbientSites[gAmbientSiteCount++];
            s->tx=tx;s->ty=ty;
            s->x=tx*16+4+((h>>8)&7);
            s->y=ty*16+4+((h>>12)&7);
            s->phase=(h>>16)&63;
            s->foreground=material==2;
            break;
        }
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

static bool8 actor_in_front(const AmbientSite* site) {
    int i;
    /* A sheen on foreground material should not be pasted onto a character
       who has walked in front of that material's southern edge. */
    for(i=0;i<ACTOR_MAX;i++) {
        const Actor* a=&gActors[i];
        if(a->kind!=AK_PLAYER && a->kind!=AK_ENEMY && a->kind!=AK_NPC)continue;
        if(a->flags&AF_HIDDEN)continue;
        int px=PX(a->x),py=PX(a->y),z=PX(a->z);
        if(py<(site->ty+1)*16)continue;
        int width,height;
        actor_visual_size(a,&width,&height);
        if(site->x>=px-width/2 && site->x<px+width/2 &&
           site->y>=py-z-height && site->y<py-z)return TRUE;
    }
    return FALSE;
}

void ambient_draw(bool8 foreground) {
    int i,potential=0;
    if(sAmbientFrame!=gFrame) {
        sAmbientFrame=gFrame;
        gAmbientPotential=gAmbientVisible=gAmbientPeaks=0;
    }
    if(!sAmbientTile)return;
    const SpriteSheet* sh=&sheets[SHEET_GLITTER];
    int frame_count=sh->tile_count/sh->frame_tiles;
    for(i=0;i<gAmbientSiteCount && potential<AMBIENT_VIEW_SITES;i++) {
        const AmbientSite* s=&sAmbientSites[i];
        int x=s->x-gCamX,y=s->y-gCamY;
        if(x<4 || x>=236 || y<HUD_HEIGHT_PIXELS+4 || y>=156)continue;
        int material=surface(s->tx,s->ty);
        if(!material)continue; /* a gate may have opened since room creation */
        potential++;
        if((material==2)!=foreground)continue;
        int phase=(gFrame+s->phase)&63;
        if(phase>=32 || frame_count<2)continue;
        if(foreground && actor_in_front(s))continue;
        /* Frame zero is blank. Five drawn stages swell into one star and
           fade, then remain dark for the other half of the 64-frame cycle. */
        int frame=1+phase*(frame_count-1)/32;
        if(gOamCount>=(foreground?80:120))continue;
        draw_sprite(x-3,y-3,SHEET_GLITTER,sAmbientTile,frame,0,foreground?1:2,sh->pal);
        gAmbientVisible++;
        if(frame==frame_count/2)gAmbientPeaks++;
    }
    gAmbientPotential=potential;
}
