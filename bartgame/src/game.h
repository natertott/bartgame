#ifndef GAME_H
#define GAME_H
#include "gba.h"

enum { GS_TITLE, GS_PLAY, GS_TRANSITION, GS_TEXT, GS_MAP, GS_DEAD, GS_WIN, GS_ARCADE };
enum { AREA_SEWER, AREA_FOREST, AREA_MYST, AREA_CREAM, AREA_HANDOFF };

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
extern u8 gStartingDraft;

#if BART_FOREST_VARIANT >= 31
/* Developer camera-only panorama fixture. Zero in ordinary gameplay. The
   review harness preserves native world/actors and requests an actual PPU
   view, never injects artwork or room geometry. */
extern u8 gForestReviewEnabled;
extern s16 gForestReviewCamera[2];
extern u32 gForestReviewClock;
#endif

void game_init(void);
void game_update(void);
void game_win(void);
void game_win_chain(void); /* additional handoff Earth Element ending */
void game_legacy_boss_defeated(int type);
void game_travel_cream(int node,int px,int py,int facing,int drop_rows);
void game_open_handoff(int site,int kind);
void game_leave_cream(void); /* visible entry stairs use the matching Drain arch */
void game_give_key_item(int cell); /* reward of a completed required trial, once */
void game_return_to_hub(void); /* the Drain Cap: fade, the hub's spawn, from the ceiling */

#endif
