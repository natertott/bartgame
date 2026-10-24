#ifndef SAVE_H
#define SAVE_H
#include "gba.h"

/* One save file in SRAM: the wood as generated and as the run has
   changed it, the hero's state and the run's counts. A continued run
   wakes in the drain. */
void save_write(void);
bool8 save_exists(void);
bool8 save_load(void);
void save_erase(void);

#endif
