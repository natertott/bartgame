#ifndef GAME_H
#define GAME_H
#include "gba.h"

enum { GS_TITLE, GS_PLAY, GS_TRANSITION, GS_TEXT, GS_MAP, GS_DEAD, GS_WIN, GS_PILOT };
enum { AREA_SEWER, AREA_FOREST, AREA_MYST };

typedef struct {
    u8 state;
    u8 area;        /* AREA_SEWER or AREA_FOREST */
    u8 cell;        /* forest cell index */
    u8 timer;
    u32 seed;
    u32 run_frames;
    u16 deaths;
    u16 kills;
} GameState;

extern GameState gGame;

void game_init(void);
void game_update(void);
void game_win(void);
void game_return_to_hub(void); /* the Drain Cap: fade, the hub's spawn, from the ceiling */

#endif
