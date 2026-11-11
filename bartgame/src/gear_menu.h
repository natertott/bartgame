#ifndef GEAR_MENU_H
#define GEAR_MENU_H
#include "gba.h"
/* Additive Satchel and directed Cream atlas. Original pause pages remain. */
void gear_menu_open(void);
void gear_menu_open_map(void);
void gear_menu_update(void);
bool8 gear_menu_active(void);
/* Resolve a regional interior back to its generated parent for map access. */
int gear_menu_region(int* cell);
/* Read-only map review telemetry. Coordinates are relative to the native
   128x96 chamber diagram; source_* is the exact tile anchor before tethering. */
typedef struct {u8 tile_x,tile_y,ch; s16 source_x,source_y,x,y;} GearMapMarker;
extern GearMapMarker gGearMapMarkers[24];
extern u8 gGearMapMarkerCount;
#endif
