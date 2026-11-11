/* BARTGAME: the item buttons, keys in doors, thorns and bushes under the
   sword. The items are the keys to the maze:
     Blightseed Bombs  open cracked walls
     Grail Lamp        burns webs, lights censers, burns thorns
     Petal Cloak       leaps chasms (TMC's cape: 2.0 up, 1.0 forward)
     Thorn Bow         arrows, 2 damage, stopped by walls
     Drain Cap         a mouth in the ground takes the hero home */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "objects.h"
#include "react.h"
#include "game.h"
#include "items.h"
#include "bomb_throw.h"
#include "legacy_items.h"
#include "handoff_mobility.h"

static u8 sDoorMsgLatch;
static u8 sLampFx;

static void use_bow(void) {
    if (player_shoot()) {
        gPl.item_cooldown = legacy_item_owned(LI_ARROW_BUTTERFLY)?8:16;
        player_item_pose(EQ_BOW);
    } else
        sfx_play(SFX_BUMP);
}

/* the Drain Cap: the muck opens under the hero and takes him home; in
   the drain itself it has nowhere to take him */
static void use_hubcap(void) {
    extern GameState gGame;
    gPl.item_cooldown = 30;
    if (gGame.area == AREA_SEWER) {
        textbox_open("The cap hums and goes still. It only knows the way down, and you are down.");
        return;
    }
    player_swallow();
}

static void use_lamp(void) {
    gPl.lamp_timer = 20;
    gPl.item_cooldown = 24;
    sLampFx = 1;
    player_item_pose(EQ_LAMP);
    sfx_play(SFX_LAMP);
}

/* The buttons: each of A, B and L holds what the pause menu gave it.
   The sword is the player's (player.c); the rest is here. */
void items_update(void) {
    Actor* a = gPlayer;
    if(handoff_mobility_busy()){bomb_charge_cancel();return;}
    if(legacy_player_status(LPS_FREEZE)||legacy_player_status(LPS_SHOCK)||legacy_player_status(LPS_CAPTURE)) {
        bomb_charge_cancel();return;
    }
    bomb_charge_update();
    if (a->state == PS_NORMAL && !gPl.item_cooldown && !gBombChargeKey) {
        if (gKeysDown & player_equip_keys(EQ_LAMP))
            use_lamp();
        else if (gKeysDown & player_equip_keys(EQ_CLOAK)) {
            player_cloak_jump();
            gPl.item_cooldown = 10;
        } else if (gKeysDown & player_equip_keys(EQ_BOW))
            use_bow();
        else if (gKeysDown & player_equip_keys(EQ_HUBCAP))
            use_hubcap();
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
    bomb_charge_draw(FALSE);
}
