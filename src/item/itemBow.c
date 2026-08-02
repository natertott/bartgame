#include "item.h"
#include "save.h"
#include "physics.h"

void sub_08075DF4(ItemBehavior*, u32);
void sub_08075E40(ItemBehavior*, u32);
void ItemBowShoot(ItemBehavior*, u32);
void sub_08075F38(ItemBehavior*, u32);
void sub_08075F84(ItemBehavior*, u32);
void sub_08075D88(ItemBehavior*, u32);

// Doubles the Bow's fire rate, per the user's own request. UpdateItemAnim
// (playerUtils.c) advances the player entity's shared animation by one
// frame and re-syncs this ItemBehavior's own playerFrame/playerFrameIndex/
// playerFrameDuration copies from it; every state-transition check in this
// file (this->playerFrame & 0x80 or & 1) is a threshold/bit test rather
// than an exact-value match, so advancing the animation twice per real
// frame - instead of once - safely halves the time the draw/shoot/recover
// cycle takes without needing to touch the underlying animation asset
// data, and without affecting any other item's own UpdateItemAnim calls
// elsewhere (this wrapper is only ever called from this file).
static void ItemBowUpdateAnimFast(ItemBehavior* this) {
    UpdateItemAnim(this);
    UpdateItemAnim(this);
}

void ItemBow(ItemBehavior* this, u32 index) {
    static void (*const stateFuncs[])(ItemBehavior*, u32) = {
        sub_08075DF4, sub_08075E40, ItemBowShoot, sub_08075F38, sub_08075F84, sub_08075D88,
    };
    stateFuncs[this->stateID](this, index);
}

void sub_08075DF4(ItemBehavior* this, u32 index) {
    if ((gPlayerState.attack_status & 8) == 0) {
        this->priority |= 0x80;
        sub_0806F948(&gPlayerEntity.base);
        sub_08077BB8(this);
        sub_08077D38(this, index);
        gPlayerState.bow_state = 1;
    } else {
        DeleteItemBehavior(this, index);
    }
}

void sub_08075E40(ItemBehavior* this, u32 index) {
    if (gPlayerState.bow_state != 0) {
        if ((gPlayerState.attack_status & 0x80) == 0) {
            ItemBowUpdateAnimFast(this);
            if ((this->playerFrame & 0x80) != 0) {
                this->stateID = 2;
                this->priority &= ~0x80;
                if (gSave.stats.arrowCount != 0) {
                    this->animPriority = 0;
                    gPlayerState.field_0xa &= ~(8 >> index);
                }
            }
            return;
        }
    }
    gPlayerState.bow_state = 0;
    DeleteItemBehavior(this, index);
}

void ItemBowShoot(ItemBehavior* this, u32 index) {
    u8 arrowCount;
    s32 isShooting;

    arrowCount = gSave.stats.arrowCount;
    isShooting = IsItemActive(this);
    if (isShooting && arrowCount != 0) {
        if (((gPlayerState.attack_status & 0x80) != 0) || (gPlayerState.bow_state == 0)) {
            gPlayerState.bow_state = 0;
            DeleteItemBehavior(this, index);
        }
    } else {
        gPlayerState.field_0xa = (8 >> index) | gPlayerState.field_0xa;
        SetItemAnim(this, ANIM_BOW_SHOOT);
        this->animPriority = 0xf;
        this->priority |= 0xf;
        this->stateID = 3;
    }
}

void sub_08075F38(ItemBehavior* this, u32 index) {
    if (((gPlayerState.attack_status & 0x80) == 0) && (gPlayerState.bow_state != 0)) {
        ItemBowUpdateAnimFast(this);
        if ((this->playerFrame & 1) != 0) {
            this->stateID = 4;
        }
    } else {
        gPlayerState.bow_state = 0;
        DeleteItemBehavior(this, index);
    }
}

void sub_08075F84(ItemBehavior* this, u32 index) {
    if (((gPlayerState.attack_status & 0x80) == 0) && (gPlayerState.bow_state != 0)) {
        if (GetInventoryValue(ITEM_ARROW_BUTTERFLY) == 1) {
            sub_08077E3C(this, 5);
        } else {
            ItemBowUpdateAnimFast(this);
        }
        if ((this->playerFrame & 0x80) == 0) {
            return;
        }
    }
    gPlayerState.bow_state = 0;
    DeleteItemBehavior(this, index);
}
