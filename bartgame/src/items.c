/* BARTGAME: the B button, the L button, keys in doors, thorns under the
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

static void cycle_item(void) {
    int i;
    for (i = 0; i < BITEM_COUNT; i++) {
        gPl.bitem = (gPl.bitem + 1) % BITEM_COUNT;
        if (gPl.bitem == BITEM_NONE)
            continue;
        if (gPl.bitem == BITEM_BOMBS && (gPl.items & ITEM_BOMBS))
            break;
        if (gPl.bitem == BITEM_LAMP && (gPl.items & ITEM_LAMP))
            break;
        if (gPl.bitem == BITEM_CLOAK && (gPl.items & ITEM_CLOAK))
            break;
    }
    sfx_play(SFX_MENU);
}

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

void items_update(void) {
    Actor* a = gPlayer;
    if (gKeysDown & KEY_L)
        cycle_item();
    if ((gKeysDown & KEY_B) && a->state == PS_NORMAL && !gPl.item_cooldown) {
        switch (gPl.bitem) {
            case BITEM_BOMBS: use_bomb(); break;
            case BITEM_LAMP: use_lamp(); break;
            case BITEM_CLOAK: player_cloak_jump(); gPl.item_cooldown = 10; break;
            default: break;
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
