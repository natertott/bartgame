#ifndef ARCADE_H
#define ARCADE_H
#include "gba.h"

/* The cabinet opens the shared Trophy Case. The caller supplies GS_ARCADE in the
   game-state switch and redraws the world when arcade_update returns to play.
   Music continues through the original soundtrack VBlank heartbeat. */
void arcade_open(void);
void arcade_update(void);
bool8 arcade_active(void);

/* Tabs are Milestones, Items, Creatures, and Cards. The raw entry ID is 255
   when the current filtered list is empty. Hidden entries have no preview. */
extern u8 gArcadePage, gArcadeCursor, gArcadeTop, gArcadeDetail, gArcadeSeen;
extern u8 gArcadeEntry, gArcadeCount, gArcadeFilter;
extern u8 gArcadePreviewSheet, gArcadePreviewFrame, gArcadePreviewSourcePalette;
extern u16 gArcadePreviewTiles;

#endif
