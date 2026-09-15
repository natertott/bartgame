/**
 * @file specialChest.c
 * @ingroup Objects
 *
 * @brief Special Chest object
 */
#include "entity.h"
#include "flags.h"
#include "object.h"
#include "player.h"
#include "room.h"
#include "sound.h"

extern void AddInteractableChest(Entity*);
extern void OpenSmallChest(u32 pos, u32 layer);

void SpecialChest(Entity* this) {
    if (this->action == 0) {
        if (CheckLocalFlag(this->type)) {
            DeleteThisEntity();
        }
        this->action = 1;
        this->collisionLayer = 1;
        AddInteractableChest(this);
    }
    if (this->interactType != INTERACTION_NONE) {
#ifdef QUICKSTART
        // QUICKSTART's 3-chest lottery puzzle (game.c,
        // QuickStartSetupChestLotteryContent) reserves local flags 250-252
        // for its own 3 chests - well above any real room's own local-flag
        // usage. Only the winner is ever registered in gSmallChests; without
        // this block, opening a losing chest just falls through to
        // OpenSmallChest's generic "not found" consolation (a fairy) and
        // leaves the other two chests standing, so the player could open all
        // 3 in sequence and still walk away with the real prize - defeating
        // the "one guess, real risk" puzzle the user actually asked for.
        // Whichever of the 3 is opened first now ends the round outright:
        // the other two are deleted unopened (no second guess), and a
        // losing guess grants nothing at all, not even the fairy - only the
        // registered winner (checked the same way OpenSmallChest itself
        // resolves "found", by tile position) still calls through to it for
        // a real reward.
        if (this->type >= 250 && this->type <= 252) {
            u32 pos = COORD_TO_TILE(this);
            u32 isWinner = 0;
            s32 i;
            TileEntity* t = gSmallChests;
            for (i = 0; i < 8; i++, t++) {
                if (*(u16*)&t->tilePos == pos) {
                    isWinner = 1;
                    break;
                }
            }
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* ent = &gEntities[i].base;
                if (ent != this && ent->kind == OBJECT && ent->id == SPECIAL_CHEST && ent->type >= 250 &&
                    ent->type <= 252) {
                    DeleteEntity(ent);
                }
            }
            if (isWinner) {
                OpenSmallChest(pos, 2);
            } else {
                sub_0807B7D8(0x74, pos, 2);
                RequestPriorityDuration(NULL, 120);
                SoundReq(SFX_CHEST_OPEN);
            }
            DeleteThisEntity();
            return;
        }
#endif
        OpenSmallChest(COORD_TO_TILE(this), 2);
        DeleteThisEntity();
    }
}
