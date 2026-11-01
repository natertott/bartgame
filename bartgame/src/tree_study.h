#ifndef TREE_STUDY_H
#define TREE_STUDY_H
#include "gba.h"
#include "assets.h"

#if BART_FOREST_VARIANT == 30
#define TREE_STUDY_MAX_PLACEMENTS 24

/* These are diagnostic placements, not the procedural forest's colliders.
   x/y and w/h are native pixels; root_* are cells on the 8px collision grid. */
typedef struct {
    u8 frame,x,y,w,h;
    u8 root_x8,root_y8,root_w8,root_h8;
    u8 anchor_y;
} TreeStudyPlacement;

extern TreeStudyPlacement gTreeStudyPlacements[TREE_STUDY_MAX_PLACEMENTS];
/* ABI, request, layout, floor choice, placements, resident tile count,
   tree palette slot, logical floor ID, initial Bloom x/y, complete,
   native frame count; remaining words reserved. */
extern u16 gTreeStudyInfo[16];
extern volatile u16 gTreeStudyRequest;
extern volatile u8 gTreeStudyPending;
extern u8 gTreeStudyActive;

/* Retained only in profile30. The harness sets pending+request, then invokes
   this actual ROM function by the existing VBlank callback mechanism.
   Requests0..2: all twelve trees on grass/path/sick grass.
   Requests3..5: a repeated mixed grove on those same native substrates.
   It is never called by normal game flow and changes no saved world data. */
void tree_study_begin(void);
void tree_study_reset(void);
int tree_study_priority(int px,int py,int z,int width,int height,int priority);
#endif
#endif
