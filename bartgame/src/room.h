#ifndef ROOM_H
#define ROOM_H
#include "gba.h"
#include "assets.h"

#define ROOM_MAX_W 32
#define ROOM_MAX_H 32
#define MT_NONE 0xFFFF

/* The loaded room: two metatile layers and an 8x8-cell solidity grid. */
typedef struct {
    u8 w, h; /* in metatiles */
    u16 ground[ROOM_MAX_W * ROOM_MAX_H];
    u16 overlay[ROOM_MAX_W * ROOM_MAX_H];
    u8 solid[64 * 64]; /* 1 = solid 8x8 cell */
} Room;

extern Room gRoom;
extern s16 gCamX, gCamY;
extern u8 gAnimTiles;

/* object kinds in authored rooms (art/rooms.py) */
#define OBJ_NPC 1
#define OBJ_EXIT 2
#define OBJ_SPAWN 3
#define OBJ_SHOP 4
#define OBJ_SIGN 5

void tiles_init(void);
void tiles_animate(void);
void room_clear(int w, int h, u16 fill);
void room_set(int mx, int my, u16 mt);
void room_set_overlay(int mx, int my, u16 mt);
void room_change(int mx, int my, u16 mt);
void room_change_overlay(int mx, int my, u16 mt);
u16 room_get(int mx, int my);
u16 room_get_overlay(int mx, int my);
u8 room_type(int mx, int my);
u8 room_type_px(int px, int py);
void room_build_solid(void);
void room_render(void);
bool8 room_solid_px(int px, int py);
bool8 room_box_solid(int x0, int y0, int x1, int y1);
void room_load_def(const RoomDef* def);
void camera_update(int tx, int ty, bool8 snap);
int room_px_w(void);
int room_px_h(void);

#endif
