/* Native alpha on BG2: complete wall silhouettes over their actual backing.
   All mixing happens during room composition. Active actors retain their
   existing priority and the semantic room/overlay/collision stay untouched. */
#include "cream_polish_blend.h"
#include "cream_room.h"

#define CELLS (CREAM_ROOM_W*CREAM_ROOM_H)
#define HASH_SLOTS 512
u16 gCreamPolishBlendCount,gCreamPolishBlendRejected,gCreamPolishBlendOverflow;
static u16 sBaseKey[CREAM_POLISH_BLEND_RESERVE] EWRAM_BSS;
static u16 sPaintKey[CREAM_POLISH_BLEND_RESERVE] EWRAM_BSS;
static u16 sLookup[HASH_SLOTS] EWRAM_BSS;
static u16 sEntries[CELLS][4] EWRAM_BSS;
static u16 sBases[CELLS] EWRAM_BSS;

#if BART_CREAM_VARIANT == 12
static u16 sAdmissionLimit;
void cream_polish_blend_limit(u16 limit) {sAdmissionLimit=MIN(limit,CREAM_POLISH_BLEND_RESERVE);}
#endif

static unsigned key_hash(u16 base,u16 paint) {
    return ((unsigned)base*37u+(unsigned)paint*101u)&(HASH_SLOTS-1);
}

static int find(u16 base,u16 paint,bool8 create) {
    unsigned h=key_hash(base,paint);
    while(sLookup[h]) {
        int i=sLookup[h]-1;
        if(sBaseKey[i]==base && sPaintKey[i]==paint)return i;
        h=(h+1)&(HASH_SLOTS-1);
    }
    if(!create || gCreamPolishBlendCount>=CREAM_POLISH_BLEND_RESERVE)return -1;
    int i=gCreamPolishBlendCount++;
    sBaseKey[i]=base;sPaintKey[i]=paint;sLookup[h]=i+1;
    return i;
}

static u32 native_row(const Tileset* ts,u16 entry,int y) {
    const u32* pixels=(const u32*)ts->tiles+(entry&1023)*8;
    u32 word=pixels[(entry&0x800)?7-y:y];
    if(entry&0x400) {
        word=((word&0x0f0f0f0fu)<<4)|((word>>4)&0x0f0f0f0fu);
        word=((word&0x00ff00ffu)<<8)|((word>>8)&0x00ff00ffu);
        word=(word<<16)|(word>>16);
    }
    return word;
}

static void upload(const Tileset* ts,int index) {
#ifndef CREAM_POLISH_HOST_AUDIT
    vu32* out=(vu32*)(CHARBLOCK(0)+(ts->tile_count+index)*16);
    int y;
    for(y=0;y<8;y++) {
        u32 paint=native_row(ts,sPaintKey[index],y);
        u32 base=native_row(ts,sBaseKey[index],y);
        u32 covered=(paint|(paint>>1)|(paint>>2)|(paint>>3))&0x11111111u;
        covered*=15;
        *out++=paint|(base&~covered);
    }
#else
    (void)ts;(void)index;
#endif
}

void cream_polish_blend_reset(void) {
    gCreamPolishBlendCount=gCreamPolishBlendRejected=gCreamPolishBlendOverflow=0;
    memset(sLookup,0,sizeof(sLookup));
    memset(sBases,0xff,sizeof(sBases));
#if BART_CREAM_VARIANT == 12
    sAdmissionLimit=CREAM_POLISH_BLEND_RESERVE;
#endif
}

#if BART_CREAM_VARIANT == 12
/* A complete carved shaft is admitted atomically, with repeated middle glyphs.
   Planning never uploads a partially admitted strip or consumes failed keys. */
bool8 cream_polish_blend_grid(int x,int y,int w,int h,const u16* paint_grid) {
    const Tileset* ts=&tilesets[TS_CREAM];
    u16 scratch[64][4];
    u16 pending_base[256],pending_paint[256];
    int dx,dy,q,new_count=0,old_count=gCreamPolishBlendCount;
    if(w<1 || h<1 || w*h>64 || x<0 || y<0 || x+w>CREAM_ROOM_W || y+h>CREAM_ROOM_H)return FALSE;
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++) {
        int at=(y+dy)*ROOM_MAX_W+x+dx,p=dy*w+dx;
        u16 base=gRoom.ground[at],paint=paint_grid[p];
        if(paint==MT_NONE)continue;
        if(base>=METATILE_COUNT || paint>=METATILE_COUNT)goto reject;
        for(q=0;q<4;q++) {
            u16 b=ts->map[base*4+q],a=ts->map[paint*4+q],entry;
            unsigned kind=cream_polish_tile_alpha[a&1023];
            if(kind==0)entry=b;
            else if(kind==1)entry=a;
            else {
                int i;
                if((a&0xf000)!=(b&0xf000))goto reject;
                i=find(b,a,FALSE);
                if(i<0) {
                    int n;
                    for(n=0;n<new_count;n++)if(pending_base[n]==b && pending_paint[n]==a)break;
                    if(n==new_count) {
                        if(old_count+new_count>=sAdmissionLimit)goto reject;
                        pending_base[n]=b;pending_paint[n]=a;new_count++;
                    }
                    i=old_count+n;
                }
                if(ts->tile_count+i>=1024){gCreamPolishBlendOverflow++;goto reject;}
                entry=(b&0xf000)|(ts->tile_count+i);
            }
            scratch[p][q]=entry;
        }
    }
    for(q=0;q<new_count;q++)find(pending_base[q],pending_paint[q],TRUE);
    for(q=old_count;q<gCreamPolishBlendCount;q++)upload(ts,q);
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++) {
        int at=(y+dy)*ROOM_MAX_W+x+dx,p=dy*w+dx;
        if(paint_grid[p]==MT_NONE)continue;
        sBases[at]=gRoom.ground[at];
        for(q=0;q<4;q++)sEntries[at][q]=scratch[p][q];
    }
    return TRUE;
reject:
    gCreamPolishBlendRejected++;return FALSE;
}
bool8 cream_polish_blend_fits(int x,int y,u16 first,int w,int h) {
    u16 paint[12];int i;
    if(w<1 || h<1 || w*h>12)return FALSE;
    for(i=0;i<w*h;i++)paint[i]=first+i;
    return cream_polish_blend_grid(x,y,w,h,paint);
}
#else
bool8 cream_polish_blend_fits(int x,int y,u16 first,int w,int h) {
    const Tileset* ts=&tilesets[TS_CREAM];
    u16 scratch[12][4];
    u16 pending_base[48],pending_paint[48];
    int dx,dy,q,new_count=0,old_count=gCreamPolishBlendCount;
    if(w*h>12 || x<0 || y<0 || x+w>CREAM_ROOM_W || y+h>CREAM_ROOM_H)return FALSE;
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++) {
        int at=(y+dy)*ROOM_MAX_W+x+dx,p=dy*w+dx;
        u16 base=gRoom.ground[at],paint=first+p;
        if(base>=METATILE_COUNT || paint>=METATILE_COUNT)goto reject;
        for(q=0;q<4;q++) {
            u16 b=ts->map[base*4+q],a=ts->map[paint*4+q],entry;
            unsigned kind=cream_polish_tile_alpha[a&1023];
            if(kind==0)entry=b;
            else if(kind==1)entry=a;
            else {
                int i;
                if((a&0xf000)!=(b&0xf000))goto reject;
                i=find(b,a,FALSE);
                if(i<0) {
                    int n;
                    for(n=0;n<new_count;n++)if(pending_base[n]==b && pending_paint[n]==a)break;
                    if(n==new_count) {
                        if(old_count+new_count>=CREAM_POLISH_BLEND_RESERVE)goto reject;
                        pending_base[n]=b;pending_paint[n]=a;new_count++;
                    }
                    i=old_count+n;
                }
                if(ts->tile_count+i>=1024){gCreamPolishBlendOverflow++;goto reject;}
                entry=(b&0xf000)|(ts->tile_count+i);
            }
            scratch[p][q]=entry;
        }
    }
    /* Failed candidates perform no cache mutation/rebuild and no VRAM work.
       This matters near a full room's character budget. */
    for(q=0;q<new_count;q++)find(pending_base[q],pending_paint[q],TRUE);
    for(q=old_count;q<gCreamPolishBlendCount;q++)upload(ts,q);
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++) {
        int at=(y+dy)*ROOM_MAX_W+x+dx,p=dy*w+dx;
        sBases[at]=gRoom.ground[at];
        for(q=0;q<4;q++)sEntries[at][q]=scratch[p][q];
    }
    return TRUE;
reject:
    gCreamPolishBlendRejected++;return FALSE;
}

#endif

const u16* cream_polish_blend_entries(int x,int y,u16 base,const Tileset* ts) {
    int at=y*ROOM_MAX_W+x;
    (void)ts;
    if(x<0 || y<0 || x>=CREAM_ROOM_W || y>=CREAM_ROOM_H ||
       gCreamPolishWallPaint[at]==MT_NONE || sBases[at]!=base)return 0;
    return sEntries[at];
}
