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

static void rollback(int count) {
    int i;gCreamPolishBlendCount=count;memset(sLookup,0,sizeof(sLookup));
    for(i=0;i<count;i++) {
        unsigned h=key_hash(sBaseKey[i],sPaintKey[i]);
        while(sLookup[h])h=(h+1)&(HASH_SLOTS-1);
        sLookup[h]=i+1;
    }
}

static u8 ink(const Tileset* ts,u16 entry,int x,int y) {
    const u8* pixels=(const u8*)ts->tiles+(entry&1023)*32;
    if(entry&0x400)x=7-x;
    if(entry&0x800)y=7-y;
    return (pixels[y*4+(x>>1)]>>((x&1)*4))&15;
}

static void upload(const Tileset* ts,int index) {
#ifndef CREAM_POLISH_HOST_AUDIT
    vu16* out=CHARBLOCK(0)+(ts->tile_count+index)*16;
    int x,y;
    for(y=0;y<8;y++)for(x=0;x<8;x+=4) {
        u16 word=0;int p;
        for(p=0;p<4;p++) {
            u8 color=ink(ts,sPaintKey[index],x+p,y);
            if(!color)color=ink(ts,sBaseKey[index],x+p,y);
            word|=color<<(p*4);
        }
        *out++=word;
    }
#else
    (void)ts;(void)index;
#endif
}

void cream_polish_blend_reset(void) {
    gCreamPolishBlendCount=gCreamPolishBlendRejected=gCreamPolishBlendOverflow=0;
    memset(sLookup,0,sizeof(sLookup));
    memset(sBases,0xff,sizeof(sBases));
}

bool8 cream_polish_blend_fits(int x,int y,u16 first,int w,int h) {
    const Tileset* ts=&tilesets[TS_CREAM];
    u16 scratch[12][4];
    int dx,dy,q,old_count=gCreamPolishBlendCount;
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
                i=find(b,a,TRUE);
                if(i<0)goto reject;
                if(ts->tile_count+i>=1024){gCreamPolishBlendOverflow++;goto reject;}
                entry=(b&0xf000)|(ts->tile_count+i);
            }
            scratch[p][q]=entry;
        }
    }
    for(q=old_count;q<gCreamPolishBlendCount;q++)upload(ts,q);
    for(dy=0;dy<h;dy++)for(dx=0;dx<w;dx++) {
        int at=(y+dy)*ROOM_MAX_W+x+dx,p=dy*w+dx;
        sBases[at]=gRoom.ground[at];
        for(q=0;q<4;q++)sEntries[at][q]=scratch[p][q];
    }
    return TRUE;
reject:
    rollback(old_count);gCreamPolishBlendRejected++;return FALSE;
}

const u16* cream_polish_blend_entries(int x,int y,u16 base,const Tileset* ts) {
    int at=y*ROOM_MAX_W+x;
    (void)ts;
    if(x<0 || y<0 || x>=CREAM_ROOM_W || y>=CREAM_ROOM_H ||
       gCreamPolishWallPaint[at]==MT_NONE || sBases[at]!=base)return 0;
    return sEntries[at];
}
