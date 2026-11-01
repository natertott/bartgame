#ifndef CANOPY_SCENE_H
#define CANOPY_SCENE_H
#include "gba.h"
#include "assets.h"

#if BART_FOREST_VARIANT >= 19
/* These are native drawings, not sizes at which one image is rescaled. */
enum {
    CANOPY_ROLE_SMALL, CANOPY_ROLE_CLUMP, CANOPY_ROLE_TREE,
    CANOPY_ROLE_GROVE, CANOPY_ROLE_HERO, CANOPY_ROLE_BRANCH,
    CANOPY_ROLE_ROOTS, CANOPY_ROLE_BORDER, CANOPY_ROLE_COLUMN
};
enum { CANOPY_SCENE_SOLID=1, CANOPY_SCENE_OVERHANG=2 };
#define CANOPY_SCENE_MAX_COMPONENTS 128
#define CANOPY_SCENE_MAX_PLACEMENTS 256

typedef struct {
    u16 id,area;
    u8 x0,y0,x1,y1;
    u16 placements,painted;
} CanopyComponent;
typedef struct {
    u16 component;
    u8 role,x,y,w,h,flags;
} CanopyPlacement;

extern u8 gAdaptiveCanopyMask[32*32];
extern u16 gAdaptiveCanopyComponent[32*32];
extern CanopyComponent gAdaptiveCanopyComponents[CANOPY_SCENE_MAX_COMPONENTS];
extern CanopyPlacement gAdaptiveCanopyPlacements[CANOPY_SCENE_MAX_PLACEMENTS];
/* version,components,recorded-components,placements,eligible,painted,
   projected,largest-role-width-px,largest-role-height-px,stage,overflow,
   cached-redraws; remaining words reserved */
extern u16 gAdaptiveCanopyStats[16];

void canopy_scene_reset(void);
void canopy_scene_build(void);
void canopy_scene_apply_cell(int mx,int my);
void canopy_scene_palette_tick(void);
bool8 canopy_scene_owns(int mx,int my);
#endif
#endif
