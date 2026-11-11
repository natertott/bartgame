#ifndef HANDOFF_MOBILITY_H
#define HANDOFF_MOBILITY_H
#include "gba.h"
enum { HMOB_WALK, HMOB_CART, HMOB_PARACHUTE };
/* Only the new traversal annex owns these states; existing maps keep their
   selected collision, movement, player artwork and bridge presentation. */
extern u8 gMobilityMode,gMobilityLayer,gMobilityCartPoint;
extern s16 gMobilityCartX,gMobilityCartY;
void handoff_mobility_build(u32 seed);
bool8 handoff_mobility_busy(void);
bool8 handoff_mobility_pre_player(void);
void handoff_mobility_update(void);
void handoff_mobility_draw(void);
bool8 handoff_mobility_box_solid(int x0,int y0,int x1,int y1);
bool8 handoff_mobility_interact(void);
bool8 handoff_mobility_handles_floor(int px,int py);
int handoff_mobility_priority(int original);
#endif
