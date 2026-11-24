#ifndef HUB_SERVICES_H
#define HUB_SERVICES_H
#include "gba.h"

/* The second exit repeats the selected Forest ladder's native BG stamp.
   These anchors are shared with the game state's entry/return logic. */
#define HUB_CREAM_LADDER_X 312
#define HUB_CREAM_LADDER_FOOT 71
#define HUB_CREAM_RETURN_Y 94

/* Stamp the second ladder after loading the authored Drain terrain. */
void hub_services_build(void);

#endif
