#ifndef FOREST_TREES_H
#define FOREST_TREES_H
#include "gba.h"

#if BART_FOREST_VARIANT >= 31
#define FOREST_TREES_MAX 768
#define FOREST_TREES_SB_BASE 12
#define FOREST_TREES_STATS 16
enum { FOREST_TREE_WOOD=1, FOREST_TREE_AUTHORED=2 };
/* Native canvas origin in world pixels. Roots occupy the lower16 band;
   root_mask contains the original per-cell 8px collision masks (not alpha).
   Broad frames consume two16px cells; narrow frames consume one. */
typedef struct {
    s16 x,y;
    u8 frame,flags,root_mask[2];
} ForestTree;
extern ForestTree gForestTrees[FOREST_TREES_MAX];
/* version,count,wood cells,authored cells,healthy,sick,dead,broad,narrow,
   stage,overflow,clipped upper cells,cached cell redraws,reserved,unused,unused */
extern u16 gForestTreeStats[FOREST_TREES_STATS];
/* One-based owning tree index at each physical base cell, zero elsewhere. */
extern u16 gForestTreeRoots[32*32];
/* Last actual BG1/BG2/BG3 scroll values written by video_flush. Hardware
   HOFS/VOFS registers are write-only; this is provenance, not a readback. */
extern s16 gForestTreeDisplayedScroll[6];

void forest_trees_reset(void);
/* Pure room-geometry planning: no VRAM, no RNG stream, no Room mutation.
   Called only for a live room; previews never touch this resident scene. */
void forest_trees_plan(void);
void forest_trees_render(void);
void forest_trees_apply_cell(int x,int y);
bool8 forest_trees_active(void);
bool8 forest_trees_legacy(u16 mt);
bool8 forest_trees_wood(u16 mt);
bool8 forest_trees_overlay_cell(int x,int y);
bool8 forest_trees_overlay_px(int x,int y);
bool8 forest_trees_base_px(int x,int y);
/* Native visibility guard: priority3 bodies are also behind BG3 bases. */
bool8 forest_trees_occludes_px(int x,int y,int priority);
bool8 forest_trees_occludes_body(int px,int py,int z,int width,int height,int priority);
int forest_trees_priority(int px,int py,int z,int width,int height,int priority);
/* video_show hands BG3 back to the menu when BG1/BG2 are not requested. */
u16 forest_trees_video(u16 flags);
void forest_trees_scroll(void);
#endif
#endif
