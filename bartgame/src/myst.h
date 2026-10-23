#ifndef MYST_H
#define MYST_H
#include "gba.h"

/* The mystery rooms: behind a mouth in a forest room's wall, a cave, the
   hollow of a tree or a thicket, small, medium or large, holding one
   event of a kind the size allows. gWorld.myst[cell] packs kind, size
   and style; gWorld.myst_flags[cell] holds the run's state. */
enum { MK_NONE, MK_POTS, MK_CHEST, MK_NPC, MK_FAIRY, MK_WAVES, MK_SURVIVE, MK_MINIBOSS, MK_SWITCHES, MK_TORCHES, MK_BOULDERS, MK_COUNT };
enum { MS_SMALL, MS_MEDIUM, MS_LARGE };
enum { MY_CAVE, MY_HOLLOW, MY_THICKET };
#define MYST_KIND(m) ((m) & 15)
#define MYST_SIZE(m) (((m) >> 4) & 3)
#define MYST_STYLE(m) (((m) >> 6) & 3)
#define MYST_PACK(kind, size, style) ((kind) | ((size) << 4) | ((style) << 6))
#define MF_DONE 1 /* the reward is taken */
#define MF_SEEN 2 /* the room was entered */
#define SIDE_MOUTH 4 /* a from_side for load_forest: at the mouth */

void myst_build(int cell);           /* the room, from the cell's mystery */
void myst_start_pos(int* px, int* py);
void myst_enter(void);               /* after the hero stands: the event begins */
void myst_update(void);              /* each play frame in the room */
void myst_chest_opened(int tx, int ty);
void myst_tile_cleared(int tx, int ty); /* a pot or a boulder lifted or broken */
bool8 myst_stranger_trade(void);     /* the stranger's deal; TRUE when it paid */
bool8 myst_done(void);
int myst_kind(void);

#endif
