#ifndef CREAM_VISUALS_H_INCLUDED
#define CREAM_VISUALS_H_INCLUDED
#include "cream_room.h"

/* Read-only review telemetry. Each incoming directed DROP keeps its exact
   destination feet, even when its source gate has not yet been opened.
   parts bits 0..5 describe the painted cells in a three-by-two floor patch. */
enum { CREAM_VISUAL_LONG=1, CREAM_VISUAL_GATED=2, CREAM_VISUAL_ACTIVE=4 };
typedef struct {
    s16 x,y;
    u8 from,edge,x0,y0,parts,flags;
} CreamVisualLanding;
extern CreamVisualLanding gCreamVisualLandings[CC_NODES*CC_EDGE_MAX];
extern u16 gCreamVisualLandingCount;
extern u16 gCreamVisualPanelCount,gCreamVisualPanelCells;
extern u16 gCreamVisualRimCount,gCreamVisualDropCount,gCreamVisualToeCount;
extern u8 gCreamVisualPanelKinds[7];

/* Build once after the semantic room and its features have been drawn.
   Refresh only re-dresses borders and destination floors after gate changes. */
void cream_visuals_build(void);
void cream_visuals_refresh(void);

/* Polish studies7--11 compose only after regional content has claimed its
   final footprints. These declarations add no storage to earlier builds. */
typedef struct { u8 x,y,w,h; } CreamPolishFall;
extern u16 gCreamPolishWallPaint[32*32];
extern u8 gCreamPolishShadeRole[CREAM_ROOM_W*CREAM_ROOM_H];
extern CreamPolishFall gCreamPolishFall;
extern u16 gCreamPolishLadderCells,gCreamPolishUndersideCells;
void cream_polish_prepare(void);
#endif
