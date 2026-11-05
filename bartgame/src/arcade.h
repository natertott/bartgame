#ifndef ARCADE_H
#define ARCADE_H
#include "gba.h"

/* The cabinet opens a paused journal. The caller supplies GS_ARCADE in the
   game-state switch and redraws the world when arcade_update returns to play.
   Music continues through the original soundtrack VBlank heartbeat. */
void arcade_open(void);
void arcade_update(void);
bool8 arcade_active(void);

/* Read-only presentation evidence: absolute cursor and first visible row.
   Page0 contains items, page1 enemies. An unseen entry has no preview. */
extern u8 gArcadePage, gArcadeCursor, gArcadeTop, gArcadeDetail, gArcadeSeen;
extern u8 gArcadePreviewSheet, gArcadePreviewFrame, gArcadePreviewSourcePalette;
extern u16 gArcadePreviewTiles;

#endif
