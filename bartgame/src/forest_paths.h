#ifndef FOREST_PATHS_H
#define FOREST_PATHS_H
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT == 32
/* Recompose visible wear only. The walkable room and gate collision stay
   unchanged; path is the generator's32x24 route/landing scratch grid. */
void forest_paths_refine(int cell,u8* path);
#endif
#endif
