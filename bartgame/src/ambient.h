#ifndef AMBIENT_H
#define AMBIENT_H
#include "gba.h"

/* Surface-attached glitter uses no actors and never advances world RNG. */
void ambient_room_reset(void);
void ambient_draw(bool8 foreground);
extern u16 gAmbientSiteCount;
extern u8 gAmbientPotential, gAmbientVisible, gAmbientPeaks;

#endif
