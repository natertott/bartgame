#include "global.h"
#include "entity.h"
#include "item.h"
#include "physics.h"
#include "playeritem.h"

// Fire Rod - modeled directly on ItemPacciCane's shape (itemPacciCane.c):
// raise the item, spawn its projectile partway through the animation, and
// delete the behavior once the animation finishes. The projectile itself
// (PLAYER_ITEM_FIRE_ROD_PROJECTILE, src/playerItem/playerItemFireRodProjectile.c)
// was already a complete, working implementation - a straight-line shot with
// real collision/hitbox/tile-interaction handling - it just had no real
// item wired up to ever create it (item.c previously mapped ITEM_FIRE_ROD to
// ItemDebug, a stub).
void sub_QuickStartFireRod_Raise(ItemBehavior*, u32);
void sub_QuickStartFireRod_Shoot(ItemBehavior*, u32);

void ItemFireRod(ItemBehavior* this, u32 index) {
    static void (*const stateFuncs[])(ItemBehavior*, u32) = {
        sub_QuickStartFireRod_Raise,
        sub_QuickStartFireRod_Shoot,
    };
    stateFuncs[this->stateID](this, index);
}

void sub_QuickStartFireRod_Raise(ItemBehavior* this, u32 index) {
    this->priority |= 0xf;
    sub_08077D38(this, index);
    sub_0806F948(&gPlayerEntity.base);
    sub_08077BB8(this);
}

void sub_QuickStartFireRod_Shoot(ItemBehavior* this, u32 index) {
    if ((this->playerFrame & 0x80) != 0) {
        DeleteItemBehavior(this, index);
    } else {
        if ((this->playerFrame & 0x40) != 0) {
            // NOT CreatePlayerItemWithParent - that sets parent to the
            // ItemBehavior itself (this), but PlayerItemFireRodProjectile_Init
            // (unlike e.g. PlayerItemBoomerang_Init, which self-initializes
            // super->parent = &gPlayerEntity.base) does CopyPosition(super->
            // parent, super) expecting parent to already be a real Entity
            // with real position data - confirmed by the only other real
            // caller (playerItemShield.c's reflection code), which explicitly
            // sets super->child->parent to a real entity before creating one.
            // Same shape here: create it directly and set parent/
            // animationState/collisionLayer from the player ourselves.
            Entity* projectile = CreatePlayerItem(PLAYER_ITEM_FIRE_ROD_PROJECTILE, 0, 0, this->behaviorId);
            if (projectile != NULL) {
                projectile->parent = &gPlayerEntity.base;
                projectile->animationState = gPlayerEntity.base.animationState;
                projectile->collisionLayer = gPlayerEntity.base.collisionLayer;
            }
        }
        UpdateItemAnim(this);
    }
}
