#ifndef INTERACTIVE_H
#define INTERACTIVE_H
#include "gba.h"

/* Enlarged scenery keeps the saved room's existing logical tile. */
void interactive_room_reset(void);
void interactive_cell_changed(int x, int y);
void interactive_draw(bool8 behind);
int interactive_chest_tier(void); /* wooden, brass, relic: existing reward only */
bool8 interactive_chest_tile(u16 mt);
bool8 interactive_chest_overlay(u16 mt);
bool8 interactive_chest_ready(void);
bool8 interactive_entry_ready(void);
bool8 interactive_mouth_tile(u16 mt);

#endif
