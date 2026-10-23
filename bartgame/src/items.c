/* BARTGAME: the item buttons, keys in doors, thorns and bushes under the
   sword. The items are the keys to the maze:
     Blightseed Bombs  open cracked walls
     Grail Lamp        burns webs, lights censers, burns thorns
     Petal Cloak       leaps chasms (TMC's cape: 2.0 up, 1.0 forward) */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "objects.h"
#include "react.h"
#include "items.h"

static u8 sDoorMsgLatch;
static u8 sLampFx;

static void use_bomb(void) {
    Actor* a = gPlayer;
    if (gPl.bombs == 0 || bombs_live() >= 2)
        return;
    int px = PX(a->x), py = PX(a->y);
    switch (a->facing) {
        case FACE_N: py -= 18; break;
        case FACE_S: py += 14; break;
        case FACE_E: px += 16; break;
        default: px -= 16; break;
    }
    /* never inside a wall: fall back to the feet */
    if (room_solid_px(px, py - 4))
        px = PX(a->x), py = PX(a->y);
    gPl.bombs--;
    bomb_place(px, py);
    gPl.item_cooldown = 12;
}

static void use_lamp(void) {
    gPl.lamp_timer = 20;
    gPl.item_cooldown = 24;
    sLampFx = 1;
    sfx_play(SFX_LAMP);
}

/* The buttons: each of A, B and L holds what the pause menu gave it.
   The sword is the player's (player.c); the rest is here. */
void items_update(void) {
    Actor* a = gPlayer;
    if (a->state == PS_NORMAL && !gPl.item_cooldown) {
        if (gKeysDown & player_equip_keys(EQ_BOMBS))
            use_bomb();
        else if (gKeysDown & player_equip_keys(EQ_LAMP))
            use_lamp();
        else if (gKeysDown & player_equip_keys(EQ_CLOAK)) {
            player_cloak_jump();
            gPl.item_cooldown = 10;
        }
    }
    /* the lamp's flame */
    if (gPl.lamp_timer) {
        int x0, y0, x1, y1;
        if (player_lamp_box(&x0, &y0, &x1, &y1)) {
            react_burn_box(x0, y0, x1, y1);
            if (sLampFx) {
                sLampFx = 0;
                fx_spawn(FX_FLAME, (x0 + x1) / 2, (y0 + y1) / 2 + 8);
            }
        }
    }
    /* the sword cuts thorns */
    {
        int x0, y0, x1, y1;
        if (player_sword_box(&x0, &y0, &x1, &y1))
            react_cut_box(x0, y0, x1, y1);
    }
    /* keys in doors: walking into a locked door */
    if (a->state == PS_NORMAL && a->coll) {
        int px = PX(a->x), py = PX(a->y) - 6;
        int tx = px >> 4, ty = py >> 4;
        if (a->coll & COLL_N) ty = (py - 8) >> 4;
        else if (a->coll & COLL_S) ty = (py + 8) >> 4;
        else if (a->coll & COLL_E) tx = (px + 8) >> 4;
        else tx = (px - 8) >> 4;
        if (room_type(tx, ty) == TT_DOOR) {
            if (!room_door_unlock(tx, ty)) {
                if (!sDoorMsgLatch) {
                    sDoorMsgLatch = 1;
                    textbox_open("Locked. The wood keeps its keys in chests and in the hands of the dead.");
                }
            }
        } else {
            sDoorMsgLatch = 0;
        }
    } else if (!a->coll) {
        sDoorMsgLatch = 0;
    }
}

void items_draw(void) {
}
