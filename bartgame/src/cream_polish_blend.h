#ifndef CREAM_POLISH_BLEND_H
#define CREAM_POLISH_BLEND_H
#include "room.h"

/* Paint is a renderer-only ground layer. It never occupies semantic BG1. */
extern u16 gCreamPolishWallPaint[ROOM_MAX_W*ROOM_MAX_H];
extern u16 gCreamPolishBlendCount,gCreamPolishBlendRejected,gCreamPolishBlendOverflow;
void cream_polish_blend_reset(void);
bool8 cream_polish_blend_fits(int x,int y,u16 first,int w,int h);
const u16* cream_polish_blend_entries(int x,int y,u16 base,const Tileset* ts);
#endif
