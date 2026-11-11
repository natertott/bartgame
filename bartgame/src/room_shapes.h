#ifndef ROOM_SHAPES_H
#define ROOM_SHAPES_H
#include "gba.h"
extern u16 gRoomShapeCount;
void room_shapes_clear(void);
void room_shape_tile(int tx,int ty,u16 metatile);
/* Return-1 for the existing8px collision, otherwise the exact native mask. */
int room_shape_solid(int px,int py);
#endif
