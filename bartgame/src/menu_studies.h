#ifndef MENU_STUDIES_H
#define MENU_STUDIES_H
#include "gba.h"

typedef struct { s16 x,y; } MSPoint;
typedef struct { s16 x,y,w,h; } MSRect;
enum { MS_GRID, MS_LIST, MS_WHEEL, MS_FOCUS, MS_RIBBON };
enum { MS_MAP_TERRAIN, MS_MAP_PARCHMENT, MS_MAP_GRAPH, MS_MAP_ROUTE, MS_MAP_DUAL };
enum { MS_EQUIPMENT=1, MS_STATUS=2, MS_PURPOSE=4, MS_LABELS=8, MS_PREVIEW=16 };
typedef struct {
    const char* name;
    const char* purpose;
    u8 mode;             /* GRID, LIST, WHEEL, FOCUS or RIBBON */
    u8 icon_size;        /* 16 or32: native HUD or menu drawings */
    u8 flags;
    u8 map_mode;
    MSPoint slots[7];    /* top-left icon origin, order is game item order */
    MSRect detail;       /* selected name/description; x/y/w/h multiples8 */
    MSRect equipment;    /* optional three assignment icons; same alignment */
    MSRect status;       /* optional truthful expedition/current-room stats */
    MSRect overview;     /* map page primary interior (multiples8) */
    MSRect chamber;      /* secondary map region in DUAL, or explicit zoom */
    MSRect map_info;     /* current room/legend region (may be zero-sized) */
    MSRect preview;      /* optional separate ITEM/KEY map preview; zero usesoverview */
} MenuLayout;
const MenuLayout* menu_layout_a(int number); /*1..5*/
const MenuLayout* menu_layout_b(int number); /*6..10*/
const MenuLayout* menu_study_layout(int number);
extern const char* const menu_study_names[11];
/* Read-only presentation state; real controls change it. */
extern u8 gMenuStudyPage,gMenuStudyCursor,gMenuStudyMapCell,gMenuStudyZoom;
/* Map diagnostics report actual visible types and tethered native positions.
   Bits use You,Door,Task,Chest,Heal,Heart,Folk,Relic,Gate order. */
typedef struct { u8 cell,kind; s16 x,y,source_x,source_y; u8 tile_x,tile_y; } MenuMapMarker;
extern u16 gMenuMapEvents[25];
extern MenuMapMarker gMenuMapMarkers[16];
extern u8 gMenuMapMarkerCount;
extern u16 gMenuStudyDrawFrames; /* most recent completed redraw, video IRQ ticks */
#endif
