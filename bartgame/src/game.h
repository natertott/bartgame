#ifndef GAME_H
#define GAME_H
#include "gba.h"

enum { GS_TITLE, GS_PLAY, GS_TRANSITION, GS_TEXT, GS_MAP, GS_DEAD, GS_WIN };
enum { AREA_SEWER, AREA_FOREST };

typedef struct {
    u8 state;
    u8 area;        /* AREA_SEWER or AREA_FOREST */
    u8 cell;        /* forest cell index */
    u8 timer;
    u32 seed;
    u16 run_frames;
} GameState;

extern GameState gGame;

void game_init(void);
void game_update(void);

#endif
