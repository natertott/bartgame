#ifndef HUB_SERVICES_H
#define HUB_SERVICES_H
#include "gba.h"

/* The second exit repeats the selected Forest ladder's native BG stamp.
   These anchors are shared with the game state's entry/return logic. */
#define HUB_CREAM_LADDER_X 312
#define HUB_CREAM_LADDER_FOOT 71
#define HUB_CREAM_RETURN_Y 94

/* Call build after the original Drain definition loads; enter after the
   ordinary player/NPC sprite allocations. Other areas remain inert. */
void hub_services_build(void);
void hub_services_enter(void);
/* Returns the A/R input actually consumed by a physical service. */
u16 hub_services_try_interact(u16 pressed);
void hub_services_draw(bool8 front);
bool8 hub_services_box_solid(int x0,int y0,int x1,int y1);

#endif
