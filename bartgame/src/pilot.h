#ifndef PILOT_H
#define PILOT_H
#include "gba.h"

/* The Drain art pilot (built with ART_PILOT: make pilot): the artist's
   native 240x160 scene, shown exactly as delivered for a raw capture. */
void pilot_show(void);
bool8 pilot_update(void); /* true once Start has faded it out and the game's VRAM is put back */

#endif
