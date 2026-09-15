/**
 * @file subtaskFastTravel.c
 * @ingroup Subtasks
 *
 * @brief Fast Travel Subtask
 */
#include "subtask.h"
#include "common.h"
#include "menu.h"
#include "message.h"
#include "sound.h"
#include "save.h"
#include "affine.h"
#include "asm.h"
#include "pauseMenu.h"
#include "fade.h"

extern void (*const Subtask_FastTravel_Functions[])(void);
void sub_080A6E70(void);
u32 sub_080A6D74(u32);
void sub_080A6EE0(u32 param_1);

extern const Transition gUnk_08128024[];

void Subtask_FastTravel(void) {
    FlushSprites();
    Subtask_FastTravel_Functions[gMenu.menuType]();
    if (gMenu.field_0x0 != 0) {
        sub_080A6E70();
    }
    sub_080A6498();
    CopyOAM();
}

#ifdef QUICKSTART
// The hub's own windcrest, Cloud Tops, is row 2 of gUnk_08128024
// (src/menu/kinstoneMenu.c). Its destination there is (0x1e8,0x1a8) =
// (488,424), exactly where the WINDCREST object stands outside the Home of
// the Wind Tribe.
#define QUICKSTART_WINDCREST_INDEX 2
#endif

// State 0 of the fast-travel subtask: vanilla loads the overworld map, picks
// the first revealed crest as the cursor's starting point, and hands over to
// state 1 - the interactive map where the player scrolls between crests and
// confirms.
//
// Under QUICKSTART there is exactly one place to go. Per the user: "the player
// uses the ocarina, the animation of a bird picking them up plays, then the
// player arrives at the Home of the Wind Tribe wind crest" - no map, no
// choosing. So this jumps straight to state 4, which is the state
// Subtask_FastTravel_3 hands to after a confirmed pick: it waits out the fade
// and then performs the transition through the same sub_080A71F4 the vanilla
// path uses.
//
// The map-loading calls are skipped along with the menu, deliberately. They
// only exist to paint the screen state 1 draws on, and running them would put
// a frame of the crest map on screen - a flash of exactly the mechanic this is
// meant to remove. Nothing downstream reads what they set up: sub_080A6E70
// (the cursor and crest markers) is gated on gMenu.field_0x0, which only
// leaves 0 inside state 1.
//
// Everything either side of the menu is untouched. The ocarina animation, the
// bird that carries the player off (Bird_Type8, src/object/bird.c), the fade,
// and the bird that sets them down on arrival (sub_0809D738 via
// sub_0807B2F8, src/playerUtils.c) are all vanilla and all still run.
void Subtask_FastTravel_0(void) {
#ifdef QUICKSTART
    gMenu.field_0x3 = QUICKSTART_WINDCREST_INDEX;
    SetMenuType(4);
    SetFade(FADE_IN_OUT | FADE_INSTANT, 8);
#else
    sub_080A4D34();
    sub_080A4DB8(0xd);
    sub_080A6290();
    gMenu.field_0x3 = sub_080A6D74(0);
    SetMenuType(1);
    SetFade(FADE_INSTANT, 8);
#endif
}

void Subtask_FastTravel_1(void) {
    u32 uVar1;
    u32 uVar2;

    if (gFadeControl.active) {
        return;
    }

    gMenu.field_0x0 = 1;
    uVar2 = 0;

    switch (gInput.newKeys) {
        case DPAD_LEFT:
        case DPAD_UP:
            uVar2 = -1;
            break;
        case DPAD_RIGHT:
        case DPAD_DOWN:
            uVar2 = 1;
            break;
        case A_BUTTON:
        case START_BUTTON:
            gMenu.field_0x0 = 2;
            SetMenuType(2);
            MessageFromTarget(TEXT_INDEX(TEXT_WINDCRESTS, 0x04));
            break;
        case B_BUTTON:
            gMenu.field_0x0 = 3;
            SetMenuType(3);
            break;
    }

    if (uVar2) {
        uVar1 = sub_080A6D74(uVar2);
        if (uVar1 != gMenu.field_0x3) {
            gMenu.field_0x3 = uVar1;
            SoundReq(SFX_TEXTBOX_CHOICE);
        }
    }
}

u32 sub_080A6D74(u32 param_1) {
    u32 uVar1;
    u32 uVar2;
    u32 uVar3;

    uVar3 = gSave.windcrests >> 0x18;
    uVar2 = gMenu.field_0x3;
    if (param_1 == 0) {
        uVar2 = 0;
        if ((uVar3 & 1) == 0) {
            while (++uVar2 < 8 && ((1 << uVar2) & uVar3) == 0) {}
        }
    } else if (uVar3 != 0) {
        do {
            uVar2 = (uVar2 + param_1 + 8) & 7;
        } while ((1 << uVar2 & uVar3) == 0);
    }
    return uVar2 & 7;
}

void Subtask_FastTravel_2(void) {
    u32 tmp;
    switch (sub_08056338()) {
#ifdef EU
        case 0:
            gMenu.field_0x0 = 2;
            break;
        case 1:
            gMenu.field_0x0 = 3;
            tmp = 1;
            break;
        default:
            return;
    }

    if (tmp) {
        SetMenuType(3);
    }
#else
        case 0:
            gMenu.field_0x0 = 2;
            tmp = 3;
            break;
        case 1:
            tmp = 1;
            break;
        default:
            return;
    }
    SetMenuType(tmp);
#endif
}

void Subtask_FastTravel_3(void) {
    if (gMenu.field_0x0 == 2) {
        SetMenuType(4);
        SetFade(FADE_IN_OUT | FADE_INSTANT, 8);
    } else {
        ResetPlayerAnimationAndAction();
        sub_080042D0(&gPlayerEntity.base, (u32)gPlayerEntity.base.animIndex, gPlayerEntity.base.spriteIndex);
        Subtask_Exit();
        gPauseMenuOptions.disabled = 0;
        SoundReq(SFX_MENU_CANCEL);
    }
}

void Subtask_FastTravel_4(void) {
    if (gFadeControl.active == 0) {
        sub_080A71F4(&gUnk_08128024[gMenu.field_0x3]);
    }
}

void sub_080A6E70(void) {
    u32 frameIndex;
    u32 i;

    gOamCmd._4 = 0;
    gOamCmd._6 = 0;
    gOamCmd._8 = 0x400;
    gGenericMenu.unk2c++;
    sub_080A6EE0(gMenu.field_0x3);
    if ((gGenericMenu.unk2c & 0x10) != 0) {
        frameIndex = 0x5d;
    } else {
        frameIndex = 0x5e;
    }

    DrawDirect(DRAW_DIRECT_SPRITE_INDEX, frameIndex);
    for (i = 0; i < 8; i++) {
        if (IS_BIT_SET(gSave.windcrests, i + 24)) {
            sub_080A6EE0(i);
            DrawDirect(DRAW_DIRECT_SPRITE_INDEX, 0x5c);
        }
    }
}

void sub_080A6EE0(u32 param_1) {
    u32 x;
    u32 y;
    RoomHeader* roomHeader;
    const Transition* ptr = &gUnk_08128024[param_1];

    x = (u16)ptr->endX;
    y = (u16)ptr->endY;
    roomHeader = &gAreaRoomHeaders[ptr->area][ptr->room];
    x += roomHeader->map_x;
    y += roomHeader->map_y;
    gOamCmd.x = (s32)(x * DISPLAY_HEIGHT) / 0xf90 + 0x28;
    gOamCmd.y = (s32)(y * DISPLAY_HEIGHT) / 0xf90 + 0xc;
}
