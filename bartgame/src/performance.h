#ifndef PERFORMANCE_H
#define PERFORMANCE_H
#include "gba.h"

/* Development-only CPU-cycle accounting. Timers2/3 are unused by the game;
   normal builds contain neither the timer reads nor this data/code. */
enum {
    PF_TOTAL, PF_VIDEO, PF_TEXT_FLUSH, PF_UPLOAD, PF_TILE_ANIMATION,
    PF_INPUT, PF_GAME, PF_SOUND, PF_PLAYER_UPDATE, PF_ITEMS_UPDATE,
    PF_ENEMIES_UPDATE, PF_NPCS_UPDATE, PF_OBJECTS_UPDATE, PF_ROOM_EVENTS,
    PF_CAMERA_DARK, PF_HUD, PF_GLITTER_FRONT, PF_FOLK_FRONT,
    PF_INTERACTIVE_BACK, PF_PLAYER_DRAW, PF_ENEMIES_DRAW, PF_FOLK_DRAW,
    PF_OBJECTS_DRAW, PF_INTERACTIVE_FRONT, PF_GLITTER_BACK, PF_COUNT
};
#if BART_PROFILE
extern u32 gPerfWorking[PF_COUNT],gPerfCycles[PF_COUNT];
extern u32 gPerfSequence;
void perf_init(void);
u32 perf_clock(void);
void perf_frame_begin(void);
void perf_frame_end(void);
#define PERF_CALL(id,call) do { u32 perf_at=perf_clock(); call; \
    gPerfWorking[id]+=perf_clock()-perf_at; } while(0)
#else
#define perf_init() ((void)0)
#define perf_frame_begin() ((void)0)
#define perf_frame_end() ((void)0)
#define PERF_CALL(id,call) do { call; } while(0)
#endif
#endif
