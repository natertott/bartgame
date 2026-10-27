#ifndef OBJECTS_H
#define OBJECTS_H
#include "gba.h"
#include "actor.h"

/* projectiles */
enum { PJ_SEED, PJ_SPORE, PJ_SHARD, PJ_ARROW };
/* pickups: frames in the items sheet */
enum { PK_HEART, PK_GILT, PK_BOMB, PK_GILT_BIG, PK_KEY, PK_RELIC, PK_GRAIL, PK_ARROW1, PK_ARROW5, PK_ARROW10 };
/* effects */
enum { FX_PUFF, FX_CLANG, FX_BLAST, FX_FLAME, FX_SPARK, FX_BOMB_OBJ, FX_FIREFLY, FX_MOUTH };
#define OBJ_THROWN 20 /* an AK_OBJECT type: a load in flight */

Actor* proj_spawn(int type, int px, int py, int dir, int speed, int damage, bool8 from_player);
Actor* pickup_spawn(int type, int px, int py);
Actor* fx_spawn(int type, int px, int py);
void drop_roll(int px, int py, u32 roll);
void objects_update(void);
void objects_draw(void);
void objects_draw_hand(void); /* newly planted bomb passes from hand to ground */
void objects_room_reset(void);
u16 items_sheet_tile(void);
u16 icon32_frame_tile(int frame); /* one cached 32px icon; draw with frame 0 */
int icon32_frame_palette(int frame); /* cache palette in bag; material bank in world */
void icon32_menu_begin(void);
void icon32_menu_end(void);
void bomb_place(int px, int py);
int bombs_live(void);
Actor* thrown_spawn(int kind, int px, int py, int facing);
u16 lift_sheet_tile(void);

#endif
