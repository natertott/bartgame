#ifndef CABINET_H
#define CABINET_H
#include "gba.h"

/* One persistent furnishing in the Drain. Collider covers its feet only. */
extern u8 gCabinetActive;
extern s16 gCabinetX, gCabinetY;
void cabinet_room_reset(void);
void cabinet_spawn(int px,int py);
bool8 cabinet_box_solid(int x0,int y0,int x1,int y1);
bool8 cabinet_try_interact(void);
void cabinet_draw(bool8 front);
#endif
