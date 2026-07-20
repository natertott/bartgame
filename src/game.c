/**
 * @file game.c
 * @ingroup Tasks
 *
 * @brief Game task
 */
#include "game.h"

#include "affine.h"
#include "area.h"
#include "asm.h"
#include "common.h"
#include "entity.h"
#include "fileselect.h"
#include "main.h"
#include "manager/diggingCaveEntranceManager.h"
#include "message.h"
#include "player.h"
#include "room.h"
#include "save.h"
#include "screen.h"
#include "sound.h"
#include "ui.h"
#include "beanstalkSubtask.h"
#include "pauseMenu.h"
#include "fade.h"
#ifdef QUICKSTART
#include "roomid.h"
#include "item.h"
#include "enemy.h"
#include "npc.h"
#include "object.h"
#include "object/itemOnGround.h"
#include "object/itemForSale.h"
#include "itemMetaData.h"
#include "script.h"
#include "kinstone.h"
#include "flags.h"
#include "tiles.h"
#include "map.h"
#endif

// Game task

typedef void(GameState)(void);
typedef void(GameMainState)(void);

static GameState GameTask_Transition;
static GameState GameTask_Init;
static GameState GameTask_Exit;
static GameState GameTask_Main;

static GameMainState GameMain_InitRoom;
static GameMainState GameMain_ChangeRoom;
static GameMainState GameMain_Update;
static GameMainState GameMain_ChangeArea;
GameMainState GameMain_MinishPortal;
static GameMainState GameMain_BarrelUpdate;
/*static GameMainState 00000000;*/
GameMainState GameMain_Subtask;

extern u8 gUpdateVisibleTiles;

extern void FinalizeSave(void);
extern void ClearArmosData(void);
extern void ClearRoomMemory(void);
extern void ClearMenuSavestate(void);
extern void ResetUI(void);
extern void sub_0806FD8C(void);
extern void sub_080300C4(void);
extern u32 sub_0805BC04(void);
extern void DeleteSleepingEntities(void);
extern bool32 UpdateLightLevel(void);
extern void sub_080185F8(void);
extern void UpdateDoorTransition(void);
extern bool32 CheckInitPortal(void);
extern void UpdateCarriedObject(void);
extern void CollisionMain(void);
extern void sub_0805BB74(s32);
extern void CreateZeldaFollower(void);
extern void LoadRoomGfx(void);
extern void RecycleEntities(void);
extern void sub_0804AF90(void);
extern void CallRoomProp6(void);
extern u32 WriteSaveFile(u32, SaveFile*);

static void UpdateWindcrests(void);
static void InitializeEntities(void);
static void sub_08051D98(void);
static void sub_08051DCC(void);
#ifdef QUICKSTART
static void QuickStartSpawnEnemies(void);
static void QuickStartMakeNpcTalkable(Entity*, Script*);
static void QuickStartSpawnStarterChoice(void);
static void QuickStartSpawnStarterChoiceOnce(void);
static void QuickStartRefreshItemTimers(void);
static void QuickStartDeleteGroundItemsAndSigns(void);
static void QuickStartSpawnChest(void);
static void QuickStartUpdateItemChoice(void);
static void QuickStartUpdate(void);
static void QuickStartSpawnHallEnemiesOnce(void);
static void QuickStartClearCastleGuards(void);
static void QuickStartSpawnGardenEnemiesOnce(void);
static void QuickStartSpawnGardenRewardOnce(void);
static void QuickStartClearMelarisMineObstacles(void);
static void QuickStartSpawnMelarisMineEnemiesOnce(void);
static void QuickStartSpawnMelarisMineRewardOnce(void);
static void QuickStartSpawnMelarisMineMerchantOnce(void);
static void QuickStartMaintainMelarisMineShop(void);
static void QuickStartRandomizeLaddersOnce(void);
static void QuickStartMaintainGardenLadders(void);
static void QuickStartProcessLadderLinks(void);
static void QuickStartSetupLadderRoomContent(s32);
static void QuickStartEnforceContainment(void);
static void QuickStartProcessLinks(void);
static void QuickStartRoomMonitor(void);
static u8 QuickStartGetDifficulty(void);
static void QuickStartIncrementDifficulty(void);
static u8 QuickStartScaleEnemyType(u8, u8);
static void QuickStartSpawnWinKeyOnce(void);
static void QuickStartCheckWinCondition(void);
#endif

void sub_08054974(u32 worldEventId, bool32 param_2);

void GameTask(void) {
    static GameState* const sStates[] = {
        GameTask_Transition,
        GameTask_Init,
        GameTask_Main,
        GameTask_Exit,
    };

    gRoomTransition.frameCount++;
    sStates[gMain.state]();
#ifdef DEMO_USA
    if (gSave.demo_timer != 0) {
        if (--gSave.demo_timer == 0) {
            SetFade(FADE_IN_OUT | FADE_BLACK_WHITE | FADE_INSTANT, 2);
            gMain.state = GAMETASK_EXIT;
        }
    }
#endif
}

static void GameTask_Transition(void) {
    // wait for file select to fade out
    if (gFadeControl.active)
        return;

    DispReset(1);
    InitSoundPlayingInfo();
    zMallocInit();
    ResetUI();
    ClearMenuSavestate();
    MemClear(&gRoomTransition, sizeof(gRoomTransition));
    ClearRoomMemory();
    ClearArmosData();

    FinalizeSave();
    // spawn in with saved status
    MemCopy(&gSave.saved_status, &gRoomTransition.player_status, sizeof(gRoomTransition.player_status));
#ifdef QUICKSTART
    // Dev-only: skip wherever the save file says to start and drop the
    // player into QUICKSTART_AREA/QUICKSTART_ROOM instead, fully equipped.
    gRoomTransition.player_status.area_next = QUICKSTART_AREA;
    gRoomTransition.player_status.room_next = QUICKSTART_ROOM;
    gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
    // Castor Darknut Main (the room one screen north of Hall, connected to
    // it, and the one that actually contains the Darknut) is a single
    // enclosed room whose safe walkable area - verified by actually walking
    // the player through it in the emulator - is roughly a 199x135 box from
    // world (36,39) to (235,174), origin (0,0). Spawn near the bottom-left,
    // clear of the room's static chest-spawner prop sitting around (136,104).
    gRoomTransition.player_status.start_pos_x = 0x46;
    gRoomTransition.player_status.start_pos_y = 0x9b;
    gRoomTransition.player_status.layer = 1;
    gSave.stats.maxHealth = 40;
    gSave.stats.health = gSave.stats.maxHealth;
    gSave.stats.equipped[SLOT_A] = ITEM_SHIELD;
    gSave.stats.equipped[SLOT_B] = ITEM_SMITH_SWORD;
    // Start with the Big Wallet (300 rupee cap) already owned. walletType is
    // the field gameplay actually reads (gWalletSizes[walletType].size, see
    // gameUtils.c/ui.c) - it's separate from the inventory-ownership bit
    // GetInventoryValue(ITEM_WALLET) tracks, which nothing here needs to
    // touch (ITEM_WALLET stays in the "? room" chest reward pool - GiveItem
    // just bumps walletType again if it's ever picked up a second time,
    // same as any other wallet upgrade).
    gSave.stats.walletType = 1;
    // Writing straight into equipped[] only plugs these into the A/B slots -
    // it never marks them as owned (that's a separate 2-bit-per-item record,
    // see GetInventoryValue/SetInventoryValue in playerUtils.c). The real
    // GiveItem() (itemUtils.c) always does both: PutItemOnSlot() to place it
    // in a slot, then SetInventoryValue(item, 1) to register ownership. We
    // skipped the second half, so the shield/sword were never "in
    // inventory" - just physically sitting in a slot. The moment the player
    // picked up a starter item and it got auto-equipped into slot A
    // (bumping the shield out), the shield had nowhere registered to fall
    // back to and was simply gone. Register ownership so both remain
    // selectable from the item menu even after being displaced.
    SetInventoryValue(ITEM_SHIELD, 1);
    SetInventoryValue(ITEM_SMITH_SWORD, 1);
    // Dev-only: also pre-grant the Fire Rod and Light Arrow (the upgraded
    // Bow ammo - there's no separate "Light Bow" item, Light Arrow is what
    // that name refers to) so they're available in the item menu for
    // testing without needing to actually find them in the world. Deliberately
    // NOT granting plain ITEM_BOW here - it's one of the three starter-item
    // choices (see sQuickStartStarterItems below), and QuickStartAnyPickedUp
    // detects a "pickup" purely via GetInventoryValue, with no way to tell a
    // genuine pickup apart from an already-owned item - pre-granting it would
    // silently auto-skip the whole starter-choice phase at boot. ItemBow
    // (item.c) handles both ITEM_BOW and ITEM_LIGHT_ARROW identically, so
    // owning just the upgraded arrow is enough to equip and use it.
    SetInventoryValue(ITEM_FIRE_ROD, 1);
    SetInventoryValue(ITEM_LIGHT_ARROW, 1);
    // InitializePlayer() (gameUtils.c) sets PL_NO_CAP on the player whenever
    // EZERO_1ST ("met Ezlo") isn't set - true for any fresh save, since we
    // skip the whole intro that would normally clear it. PL_NO_CAP is meant
    // for the brief pre-Ezlo window of the real game, where the only items
    // you can possibly have are the sword/shield - sub_08077D38 in
    // playerUtils.c (the item-use animation setup) only special-cases
    // PL_NO_CAP for those, and silently uses an uninitialized local for any
    // other item's animation index. That's what was rendering as a
    // corrupted, wrong sprite (a different garbage value per item) whenever
    // the player used the bow/boomerang/lantern/gust jar/pegasus boots -
    // this isn't a QUICKSTART-only issue, it's a real vanilla gap that's
    // simply unreachable in normal play since you can't have those items yet
    // while PL_NO_CAP is set. Mark Ezlo as met so the player is in the same
    // state a real playthrough would be by the time any of these items are
    // obtainable.
    SetGlobalFlag(EZERO_1ST);
    // Pre-grant one empty bottle so the bonus-reward phase's Red Potion
    // pickup (GiveItem's bottle-fill path in itemUtils.c only fills a slot
    // already marked empty, 0x20) has somewhere to go - without this the
    // pickup would silently do nothing.
    gSave.stats.bottles[0] = 0x20;
    SetInventoryValue(ITEM_BOTTLE1, 1);
#endif
    gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
    ResetTmpFlags();
#ifdef QUICKSTART
    // A fresh save's global_progress defaults to 1 (title.c), which is
    // specifically the "opening festival-day chase" story stage -
    // sub_unk3_HyruleTown_0 (roomInit.c) special-cases exactly that value
    // to redirect Hyrule Town Main into the AREA_FESTIVAL_TOWN variant
    // (with its own festival-day NPC set) instead of the regular town.
    // That same function recomputes global_progress from scratch via
    // UpdateGlobalProgress() (gameUtils.c) every time it runs, defaulting
    // back to 1 unless LV1_CLEAR is set (which bumps it to 2). Set the flag
    // here, AFTER ResetTmpFlags() above - that call unconditionally derives
    // LV1_CLEAR from real Earth Element possession
    // (`if (!GetInventoryValue(ITEM_EARTH_ELEMENT)) ClearGlobalFlag(LV1_CLEAR);`),
    // so setting it any earlier just gets immediately cleared again.
    SetGlobalFlag(LV1_CLEAR);
    // global_progress 1 (see above) is also specifically the "opening
    // festival-day chase" story stage, during which ZELDA_CHASE is set and
    // CreateZeldaFollower() (npc5.c, called unconditionally by
    // InitializeEntities() on every real room load) spawns a Zelda
    // companion NPC on top of the player in every single room entered -
    // this is what looked like Zelda "randomly" appearing in unrelated
    // areas. Clear it so that companion never spawns.
    ClearGlobalFlag(ZELDA_CHASE);
#endif

    gMain.state = GAMETASK_INIT;
    gMain.substate = GAMEMAIN_INITROOM;
}

static void GameTask_Init(void) {
    DispReset(1);
    gFadeControl.mask = 0xffffffff;
    MemClear(&gOAMControls, 0xB74);
    MemClear(&gUI, sizeof(gUI));
    EraseAllEntities();
    SetBGDefaults();
    ClearTileMaps();
    ResetPalettes();
    ResetPaletteTable(1);
    sub_0806FD8C();
    gRoomControls.area = gRoomTransition.player_status.area_next;
    gRoomControls.room = gRoomTransition.player_status.room_next;
    LoadGfxGroups();
    gGFXSlots.unk0 = 1;
    gMain.state = GAMETASK_MAIN;
}

static void GameTask_Main(void) {
    static GameMainState* const sStates[] = {
        GameMain_InitRoom,
        GameMain_ChangeRoom,
        GameMain_Update,
        GameMain_ChangeArea,
        GameMain_MinishPortal,
        GameMain_BarrelUpdate,
        0,
        GameMain_Subtask,
    };
    sStates[gMain.substate]();
}

static void GameMain_InitRoom(void) {
    SetInitializationPriority();
    gScreen.lcd.displayControl = DISPCNT_BG0_ON | DISPCNT_BG1_ON | DISPCNT_BG2_ON | DISPCNT_OBJ_ON | DISPCNT_OBJ_1D_MAP;
    gMain.substate = GAMEMAIN_CHANGEROOM;
    gRoomTransition.transitioningOut = 0;
    gRoomTransition.field_0x4[0] = 0;
    gRoomTransition.field_0x4[1] = 0;
    MessageInitialize();
    InitRoom();
    InitUI(FALSE);
    InitializeEntities();
#ifndef EU
    sub_0801855C();
#endif
}

#ifdef QUICKSTART
extern Script script_QuickStartChooseOne;
extern Script script_QuickStartMerchant;

typedef struct {
    u16 itemId;
} QuickStartItemChoice;

#define QUICKSTART_ITEM_CHOICES 3

static const QuickStartItemChoice sQuickStartStarterItems[QUICKSTART_ITEM_CHOICES] = {
    { ITEM_BOMBS },
    { ITEM_BOW },
    { ITEM_BOOMERANG },
};
static const QuickStartItemChoice sQuickStartBonusItems[QUICKSTART_ITEM_CHOICES] = {
    { ITEM_HEART_CONTAINER },
    { ITEM_RUPEE100 },
    { ITEM_BOTTLE_RED_POTION },
};
static const QuickStartItemChoice sQuickStartSkillItems[QUICKSTART_ITEM_CHOICES] = {
    { ITEM_SKILL_SPIN_ATTACK },
    { ITEM_SKILL_ROLL_ATTACK },
    { ITEM_SKILL_PERIL_BEAM },
};

// Whether an entity's position falls within the CURRENT room's bounds
// (gRoomControls.origin_x/y/width/height, which update per-room regardless
// of which of Main/Hall/Town is active). Several idempotency/clearance
// checks in this file scan gEntities by kind/id alone, which conflates
// separate rooms' independently-spawned enemies of the same type - e.g.
// Main's wave-in-progress Octoroks look identical to Hall's own unrelated
// ambient ones on a bare kind/id scan. Scoping by position instead of
// relying on a hardcoded room-specific threshold generalizes correctly to
// every room this file spawns enemies in.
static bool32 QuickStartEntityInCurrentRoom(Entity* entity) {
    s16 x = entity->x.HALF.HI;
    s16 y = entity->y.HALF.HI;
    return x >= gRoomControls.origin_x && x < gRoomControls.origin_x + gRoomControls.width && y >= gRoomControls.origin_y &&
           y < gRoomControls.origin_y + gRoomControls.height;
}

// Whether a ground item this file itself dropped is still sitting at the
// exact spot it was placed (room-local offset). Used to tell "the player
// picked it up" apart from "the room got unloaded before they picked it
// up" for a gauntlet reward - see QuickStartSpawnGardenRewardOnce and
// QuickStartSpawnMelarisMineRewardOnce for why that distinction matters.
static bool32 QuickStartGroundItemAt(s16 offsetX, s16 offsetY) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == OBJECT && gEntities[i].base.id == GROUND_ITEM &&
            QuickStartEntityInCurrentRoom(&gEntities[i].base) &&
            gEntities[i].base.x.HALF.HI - gRoomControls.origin_x == offsetX &&
            gEntities[i].base.y.HALF.HI - gRoomControls.origin_y == offsetY) {
            return TRUE;
        }
    }
    return FALSE;
}

static void QuickStartSpawnEnemies(void) {
    static const s16 sQuickStartEnemyOffsets[3][2] = {
        { 0x6e, 0x87 },
        { 0x96, 0x87 },
        { 0xbe, 0x87 },
    };
    u8 enemyType = QuickStartScaleEnemyType(OCTOROK, QuickStartGetDifficulty());
    s32 i;
    for (i = 0; i < 3; i++) {
        Entity* enemy = CreateEnemy(enemyType, 0);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartEnemyOffsets[i][0];
            enemy->y.HALF.HI = gRoomControls.origin_y + sQuickStartEnemyOffsets[i][1];
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
}

// Wave 2: a step up from the opening 3 Octoroks - just more of them, spread
// across the room's full safe walkable box (world (36,39)-(235,174)).
static void QuickStartSpawnWave2(void) {
    static const s16 sQuickStartWave2Offsets[4][2] = {
        { 0x5a, 0x60 },
        { 0x82, 0x9c },
        { 0xaa, 0x60 },
        { 0xd2, 0x9c },
    };
    u8 enemyType = QuickStartScaleEnemyType(OCTOROK, QuickStartGetDifficulty());
    s32 i;
    for (i = 0; i < 4; i++) {
        Entity* enemy = CreateEnemy(enemyType, 0);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartWave2Offsets[i][0];
            enemy->y.HALF.HI = gRoomControls.origin_y + sQuickStartWave2Offsets[i][1];
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
}

// Wave 3: the hardest wave - 2 Octoroks plus a real Darknut. This room is
// Castor Darknut Main, the Darknut's own vanilla arena (see
// object/bossDoor.c and object/cutsceneOrchestrator.c), so its sprite
// assets are already loaded here regardless of our own cutscene removal.
static void QuickStartSpawnWave3(void) {
    static const s16 sQuickStartWave3OctorokOffsets[2][2] = {
        { 0x6e, 0x60 },
        { 0xbe, 0x60 },
    };
    u8 difficulty = QuickStartGetDifficulty();
    u8 enemyType = QuickStartScaleEnemyType(OCTOROK, difficulty);
    s32 i;
    Entity* enemy;
    for (i = 0; i < 2; i++) {
        enemy = CreateEnemy(enemyType, 0);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartWave3OctorokOffsets[i][0];
            enemy->y.HALF.HI = gRoomControls.origin_y + sQuickStartWave3OctorokOffsets[i][1];
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
    enemy = CreateEnemy(DARK_NUT, 0);
    if (enemy != NULL) {
        enemy->x.HALF.HI = gRoomControls.origin_x + 0x96;
        enemy->y.HALF.HI = gRoomControls.origin_y + 0x9c;
        enemy->collisionLayer = 1;
        enemy->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(enemy);
    }
    // A second Darknut once the player's won a round or more - reuses one
    // of Wave2's own verified-safe spots in this same room (Wave2 and
    // Wave3 never run at the same time, so there's no collision risk
    // reusing it here).
    if (difficulty >= 2) {
        enemy = CreateEnemy(DARK_NUT, 0);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + 0x82;
            enemy->y.HALF.HI = gRoomControls.origin_y + 0x9c;
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
}

// Castor Darknut Hall - the wide corridor south of Main, reachable now that
// BossDoor is disabled for QUICKSTART (see object/bossDoor.c) - is much
// wider than Main (512px vs Main's ~200px), spanning roughly local x
// [70,420] at local y ~94 (verified by walking it in the emulator). Spread
// a few Octoroks across that width so the room isn't empty.
//
// Two bugs fixed here together:
// 1) Hall is reachable by simply wandering south out of Main, without ever
//    finishing (or even starting) the item-choice/combat/chest sequence -
//    these ambient Octoroks are only supposed to appear once that's fully
//    done, so gate on field_0x4[0] == 10 (QuickStartUpdateItemChoice's
//    "done" phase) rather than spawning unconditionally the instant the
//    player sets foot in the room.
// 2) Hall turns out to scroll gRoomControls.origin_x/y as the player walks
//    through it (it's one large room, not several), so the old "scan for
//    an Octorok already in QuickStartEntityInCurrentRoom bounds" check
//    would stop matching the first wave the moment the origin shifted
//    (their position no longer being described as within the "current"
//    equation, on the other hand) creating a second full wave at the new
//    origin - verified in the emulator: two complete sets of 3, 208px
//    apart. ITEM_33 (another bare unused Item enum slot) is a fixed,
//    scroll-independent "already spawned" marker instead.
static void QuickStartSpawnHallEnemiesOnce(void) {
    // Hall's own verified-safe width is local x [70,420] at y~94 (see file
    // header comment above) - a 4th difficulty-only spot at x=410 stays
    // comfortably inside that range without needing fresh verification.
    static const s16 sQuickStartHallEnemyOffsets[4] = { 0x96, 0xfa, 0x15e, 0x19a };
    u8 difficulty = QuickStartGetDifficulty();
    u8 enemyType = QuickStartScaleEnemyType(OCTOROK, difficulty);
    s32 count = (difficulty >= 2) ? 4 : 3;
    s32 i;
    if (gRoomTransition.field_0x4[0] != 10) {
        return;
    }
    if (GetInventoryValue(ITEM_33) != 0) {
        return;
    }
    for (i = 0; i < count; i++) {
        Entity* enemy = CreateEnemy(enemyType, 0);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartHallEnemyOffsets[i];
            enemy->y.HALF.HI = gRoomControls.origin_y + 0x5e;
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
    SetInventoryValue(ITEM_33, 1);
}

// Hyrule Castle Garden is the gauntlet - the vanilla guards standing watch
// here would otherwise stand around (and can trigger vanilla guard-chase
// scripts), so clear them out every frame. Scoped to just GUARD_1 rather
// than every NPC (unlike the earlier Village hub prototype's blanket NPC
// clear) since Castle Garden isn't being used as a calm hub - only the
// guards specifically need to go.
// Deleting the guard entities alone still left an invisible wall right
// where one of them stood: sub_StateChange_CastleGarden_Main (roomInit.c)
// always blocks tiles (24,9)/(24,10)/(38,9)/(38,10) with SPECIAL_TILE_114
// (a solid, spriteless collision tile) whenever the late-game
// SOUGEN_08_TORITSUKI flag isn't set - real vanilla content gating an
// early-game checkpoint, entirely independent of the guard entities
// themselves. Reset those tiles back to plain floor too.
static void QuickStartClearCastleGuards(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC && gEntities[i].base.id == GUARD_1) {
            DeleteEntity(&gEntities[i].base);
        }
    }
    SetTileType(TILE_TYPE_0, TILE_POS(24, 9), LAYER_BOTTOM);
    SetTileType(TILE_TYPE_0, TILE_POS(24, 10), LAYER_BOTTOM);
    SetTileType(TILE_TYPE_0, TILE_POS(38, 9), LAYER_BOTTOM);
    SetTileType(TILE_TYPE_0, TILE_POS(38, 10), LAYER_BOTTOM);
    // SetTileType above only fixes collision - confirmed in the emulator
    // that the 4 tiles still render solid black afterward. SPECIAL_TILE_114
    // is >= 0x4000 (see SetTileType's own leading comment: "tileType >=
    // 0x4000: call SetTile directly"), meaning the vanilla code this
    // replaced didn't just tag these 4 tiles with a collision type - it
    // overwrote their actual tile graphic with a dedicated "blocking" tile
    // (used elsewhere for the Library, per tiles.h's comment on
    // SPECIAL_TILE_114), which is why TILE_TYPE_0 (a real type, < 0x800)
    // swaps the collision back to normal but leaves that graphic in place.
    // mapDataOriginal (map.h) is the map's own unmodified copy of mapData,
    // taken before any tile ever gets overwritten - restoring straight from
    // it, rather than guessing at a neighboring tile's index, guarantees
    // getting back the exact grass/path art that was there originally.
    {
        MapLayer* layer = GetLayerByIndex(LAYER_BOTTOM);
        layer->mapData[TILE_POS(24, 9)] = layer->mapDataOriginal[TILE_POS(24, 9)];
        layer->mapData[TILE_POS(24, 10)] = layer->mapDataOriginal[TILE_POS(24, 10)];
        layer->mapData[TILE_POS(38, 9)] = layer->mapDataOriginal[TILE_POS(38, 9)];
        layer->mapData[TILE_POS(38, 10)] = layer->mapDataOriginal[TILE_POS(38, 10)];
    }
}

// ITEM_32 doesn't otherwise exist as a real, checked-anywhere item (a bare
// unused filler slot in the Item enum) - repurposed here as a PERMANENT
// "gauntlet already won" marker (save-persistent, never reset once set).
// The transient "wave spawned this visit" state deliberately does NOT ride
// on another inventory slot like this - it uses room flag 0
// (CheckRoomFlag/SetRoomFlag, flags.c) instead, which is part of
// gRoomVars and gets cleared by sub_08052EA0 on every room (re)load,
// including a plain leave-and-return trip. That distinction matters:
// leaving the room mid-fight wipes the actual enemies (area unloads don't
// respect ENT_PERSIST the way our own same-room reload trick does), so a
// persistent "in progress" flag would read the resulting empty room as
// "cleared" and hand out the reward for free - verified in the emulator.
// With the wave-spawned flag auto-resetting instead, returning mid-fight
// just respawns the wave, exactly as if the fight were only now starting.
// Density target: 1 enemy per 25 (32x32px) squares of the room. Castle
// Garden is 1008x528px -> 31x16 squares -> 496/25 -> 19 enemies (picking
// 32px squares rather than the engine's native 16px tiles, since the
// literal tile count - 63x33 -> 2079/25 -> 83 - would blow well past
// MAX_ENTITIES (72 total, shared with the player, every decorative
// object already in the room, and the reward item), not just this
// room's own budget). Started as an evenly-spaced 5x4 grid, but the
// room's middle section is a hedge maze, not open ground - a blind grid
// landed 5 of the 19 inside solid hedge tiles with no room to even move,
// let alone be reachable by the player. Those 5 were individually
// verified in the emulator (can the entity actually move at all from
// that exact spot) and moved to the nearest open ground; the other 14
// were already fine.
static void QuickStartSpawnGardenEnemiesOnce(void) {
    static const s16 sQuickStartGardenEnemyOffsets[19][2] = {
        { 0xc8, 0x96 },  { 0x15e, 0x96 },  { 0x1f4, 0x96 },  { 0x28a, 0x96 },  { 0x320, 0x96 },
        { 0xb4, 0xd2 },  { 0x186, 0xe6 },  { 0x1f4, 0xe6 },  { 0x262, 0xe6 },  { 0x320, 0xe6 },
        { 0x118, 0x10e }, { 0x15e, 0x136 }, { 0x1f4, 0x136 }, { 0x28a, 0x136 }, { 0x320, 0x136 },
        { 0x118, 0x17c }, { 0x15e, 0x17c }, { 0x1f4, 0x17c }, { 0x28a, 0x17c },
    };
    static const u8 sQuickStartGardenEnemyTypes[3] = { OCTOROK, ROPE, CROW };
    s32 i;
    if (GetInventoryValue(ITEM_32) != 0) {
        return;
    }
    if (CheckRoomFlag(0)) {
        return;
    }
    {
        u8 difficulty = QuickStartGetDifficulty();
        for (i = 0; i < ARRAY_COUNT(sQuickStartGardenEnemyOffsets); i++) {
            u8 enemyType = QuickStartScaleEnemyType(sQuickStartGardenEnemyTypes[(s32)Random() % 3], difficulty);
            Entity* enemy = CreateEnemy(enemyType, 0);
            if (enemy != NULL) {
                enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartGardenEnemyOffsets[i][0];
                enemy->y.HALF.HI = gRoomControls.origin_y + sQuickStartGardenEnemyOffsets[i][1];
                enemy->collisionLayer = 1;
                enemy->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(enemy);
            }
        }
    }
    SetRoomFlag(0);
}

// The pool of "not guaranteed by the earlier starter/bonus/skill choices"
// rewards the gauntlet can drop - tools, upgrades, skills, and heart
// progression. Filtered at drop time to whichever the player doesn't
// already have.
static const u16 sQuickStartGardenRewardPool[] = {
    ITEM_BOOMERANG,         ITEM_MAGIC_BOOMERANG,   ITEM_LANTERN_OFF,      ITEM_GUST_JAR,
    ITEM_PACCI_CANE,        ITEM_MOLE_MITTS,        ITEM_ROCS_CAPE,        ITEM_PEGASUS_BOOTS,
    ITEM_REMOTE_BOMBS,      ITEM_OCARINA,           ITEM_MIRROR_SHIELD,    ITEM_SKILL_SPIN_ATTACK,
    ITEM_SKILL_ROLL_ATTACK, ITEM_SKILL_ROCK_BREAKER, ITEM_SKILL_SWORD_BEAM, ITEM_SKILL_GREAT_SPIN,
    ITEM_SKILL_DOWN_THRUST, ITEM_SKILL_PERIL_BEAM,  ITEM_SKILL_DASH_ATTACK, ITEM_HEART_PIECE,
    ITEM_HEART_CONTAINER,
};
#define QUICKSTART_GARDEN_REWARD_POOL_SIZE (sizeof(sQuickStartGardenRewardPool) / sizeof(u16))

// Picks a random not-yet-owned reward and drops it at the gauntlet's fixed
// reward spot, marking ITEM_32 as "earned" (1) and room flag 1 as "now
// watching this visit's drop" - shared by both the initial grant and the
// re-drop path in QuickStartSpawnGardenRewardOnce below.
static void QuickStartSpawnGardenRewardItem(void) {
    s32 i;
    u16 available[QUICKSTART_GARDEN_REWARD_POOL_SIZE];
    s32 availableCount = 0;
    u16 chosenItem;
    Entity* itemEntity;
    for (i = 0; i < QUICKSTART_GARDEN_REWARD_POOL_SIZE; i++) {
        if (GetInventoryValue(sQuickStartGardenRewardPool[i]) == 0) {
            available[availableCount] = sQuickStartGardenRewardPool[i];
            availableCount++;
        }
    }
    // Everything in the pool is already owned (unlikely, but possible after
    // repeated testing) - fall back to a rupee pile so clearing the room
    // still has something to show for it.
    chosenItem = (availableCount != 0) ? available[(s32)Random() % availableCount] : ITEM_RUPEE100;
    itemEntity = CreateObject(GROUND_ITEM, chosenItem, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + 0x1f8;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + 0x108;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
        SetInventoryValue(ITEM_32, 1);
        SetRoomFlag(1);
    }
}

// Once every gauntlet enemy is dead, drop a random reward the player
// doesn't already have. Only fires once the wave has actually been spawned
// THIS visit (room flag 0, set by QuickStartSpawnGardenEnemiesOnce): on
// the very first frame in the room, before that, "no enemies alive" would
// otherwise look identical to "already cleared" and grant the reward
// immediately - and after leaving mid-fight and coming back, it looks
// identical to "the area-unload just wiped them", which must respawn the
// wave rather than pay out for it (see QuickStartSpawnGardenEnemiesOnce).
//
// ITEM_32 is a 3-state flag, not a boolean: 0 = not earned yet, 1 = earned
// and a ground item is (or was) dropped for it, 2 = confirmed actually
// picked up. That distinction exists because leaving the room (any of
// Castle Garden's several exits) wipes ground items same as it wipes
// enemies, regardless of ENT_PERSIST - a player who clears the gauntlet
// then wanders off before grabbing the drop would otherwise lose it
// forever (ITEM_32 already 1, nothing left to spawn it again). Room flag 1
// tracks "watching a drop THIS visit": if the item vanishes while that
// flag is still set, it was a genuine pickup (promote to 2); if the flag
// is already gone (a fresh visit) and there's no item, it was wiped before
// pickup, so re-drop it.
static void QuickStartSpawnGardenRewardOnce(void) {
    s32 i;
    if (GetInventoryValue(ITEM_32) >= 2) {
        return;
    }
    if (GetInventoryValue(ITEM_32) == 0) {
        if (!CheckRoomFlag(0)) {
            return;
        }
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                return;
            }
        }
        QuickStartSpawnGardenRewardItem();
        return;
    }
    if (QuickStartGroundItemAt(0x1f8, 0x108)) {
        SetRoomFlag(1);
        return;
    }
    if (CheckRoomFlag(1)) {
        SetInventoryValue(ITEM_32, 2);
        return;
    }
    QuickStartSpawnGardenRewardItem();
}

// Win condition: a key sitting just south of Castle Garden Main's north
// door (the real vanilla exit to Hyrule Castle - gExitList_CastleGarden_Main
// entry 0, trigger at local (0x1f8, 0x28)). Picking it up ends the round.
// ITEM_QST_GRAVEYARD_KEY is a real Item enum slot that's otherwise unused
// by anything QUICKSTART touches (it's vanilla content for the Royal
// Valley graveyard quest, never reached from this loop), so its own
// inventory flag doubles as the "already spawned/taken" latch - no new
// global flag needed for that part. It gets explicitly cleared again in
// QuickStartCheckWinCondition below so the next round (after the
// win-triggered reset) starts with the key unclaimed again.
//
// Ground items despawn on their own timer regardless of ENT_PERSIST (see
// QuickStartRefreshItemTimers, which does the same thing for the starter/
// bonus/skill choices) - left unrefreshed, the key would flicker away and
// respawn every ~10 seconds while the player's still making their way
// here, and worse, a pickup landing in the same frame as a despawn could
// race and silently drop the win entirely. Called every frame from
// QuickStartRoomMonitor, so refresh an existing key's timer every time
// through instead of only spawning once and leaving it to fend for itself.
static void QuickStartSpawnWinKeyOnce(void) {
    Entity* itemEntity;
    s32 i;
    if (GetInventoryValue(ITEM_QST_GRAVEYARD_KEY) != 0) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM && ent->type == ITEM_QST_GRAVEYARD_KEY) {
            ((ItemOnGroundEntity*)ent)->unk_6c = 600;
            return;
        }
    }
    itemEntity = CreateObject(GROUND_ITEM, ITEM_QST_GRAVEYARD_KEY, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + 0x1f8;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + 0x78;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
    }
}

// Difficulty only ever climbs here. DoSoftReset() (main.c) preserves EWRAM
// on the CPU side, but the title/file-select flow the player lands back on
// unconditionally reloads gSave from the save file (EEPROM) the moment they
// pick a slot - so without an explicit write here first, the very next
// "Continue" would load the OLD, un-incremented save right back over our
// change, and it would look like the win never registered. WriteSaveFile is
// the same plain, synchronous EEPROM write HandleSaveInProgress (save.c)
// itself calls to do the real work - it needs none of that function's
// surrounding save-menu/sound-fade state machine, so it's safe to call
// directly from mid-gameplay like this.
static void QuickStartCheckWinCondition(void) {
    if (GetInventoryValue(ITEM_QST_GRAVEYARD_KEY) == 0) {
        return;
    }
    QuickStartIncrementDifficulty();
    SetInventoryValue(ITEM_QST_GRAVEYARD_KEY, 0);
    WriteSaveFile(gSaveHeader->saveFileId, &gSave);
    DoSoftReset();
}

// General-purpose room-to-room connector: entering a rectangular trigger
// box (local coordinates, relative to gRoomControls.origin at the time)
// within a specific room fires a fade transition straight to another
// specific room/position, regardless of whether the two areas are related
// in vanilla at all. This is the generalized form of what this file used
// to have as three separate hand-written copies (Hall<->Melari's Mine,
// Melari's Mine->Castle Garden) - the same technique, but as one data
// table and one function, so linking any further pair of rooms is a new
// row here instead of a new bespoke block.
//
// Why a position box instead of reusing the real vanilla door (retargeting
// its destination in transitions.c, as Hall's own exit and Melari's Mine's
// two doors originally were)? DoApplicableTransition (scroll.c) only fires
// when the player is standing on one specific ACT_TILE-flagged tile in the
// room's own compiled map data - GetActTileAtTilePos, the function that
// looks this up, is still undecompiled ASM. Retargeting a real Transition
// entry's own destination fields (leaving its coordinates untouched) was
// tried and empirically found to never fire under QUICKSTART's direct
// room load (exhaustive grid-warp sweep, zero hits) - apparently the
// ACT_TILE/prerequisite state that pathway depends on isn't set up when a
// room is jumped into directly instead of entered via a real transition.
// A position box sidesteps that pathway entirely - it's checked every
// frame regardless of ACT_TILE state - at the cost of being an invisible
// trigger rather than a real door.
//
// "Invisible trigger" doesn't mean "wherever's convenient" though. Every
// room's real exits are already fully decompiled data in
// src/data/transitions.c (the gExitList_* / Transition tables) - each
// entry's startX/startY/shape is the pixel-exact location of a real
// door/staircase in that room, and any entry anywhere in the file whose
// destination is a given room has an endX/endY that's a proven-safe,
// already-used-by-the-real-game spawn point in that room. Reading those
// tables (see scratchpad/parse_transitions.py from this session, usage:
// `python3 parse_transitions.py AREA_X ROOM_Y` - prints both the room's
// own real exits, for trigger placement, and every real entry landing in
// that room, for spawn placement) replaces emulator trial-and-error
// entirely for finding *where* to put a box. The links below all use real
// door coordinates this way, picking a different one of a room's several
// real exits per outgoing link so the boxes don't collide with each other
// (the two Melari's Mine boxes use its "east" and "southeast" real doors
// respectively; the destination they actually send the player to is
// unrelated to whatever the real door used to lead to).
//
// Box math: a real Transition's box is [startX, startX+w] x [startY,
// startY+h], where (w,h) comes from its shape: AREA_12x12 -> (6,6),
// AREA_12x28 -> (6,14), AREA_28x12 -> (14,6), AREA_44x12 -> (22,6).
//
// Adding a new link: (1) run the parser for both the source and
// destination room to get a real exit (for the trigger box) and a real
// "lands here" entry (for the spawn position) - no emulator warping
// needed to find either coordinate. (2) A real door's coordinates are
// exact, but the data says nothing about whether that spot is reachable
// on foot from wherever the player will actually be standing - some rooms
// turn out to be a genuine maze of pockets that aren't mutually walkable
// (confirmed empirically for Melari's Mine: its "east" and "southeast"
// real doors, and the landing spot for its "Crenel Minish Paths" door,
// each sit in a small dead-end alcove that doesn't connect to the room's
// open area by walking, even though all three are real vanilla tiles).
// Always confirm reachability in the emulator after wiring up a new link,
// same as before - the parser removes the guesswork of *where the door
// is*, not the separate question of *can you walk there*.
//
// Melari's Mine's own two doors below are NOT on real door coordinates -
// they're both on the same long horizontal corridor that runs along the
// top of the room (confirmed by emulator walk test to be continuously
// walkable for roughly its whole ~550px length, unlike the maze of
// disconnected pockets further south/central in the room where its real
// doors sit - see the corridor exploration this session). Using two
// points on that same corridor as "the two main exits" - one near each
// end - means the player can actually walk the whole path between them
// (needed so the room can later be populated with NPCs along it), and
// both spawns land right next to a real archway/support-beam map feature
// instead of in the middle of open floor (which read as Link
// materializing out of nowhere - positioning next to a wall/feature this
// way is what actually fixes that, not the transition's spawn_type: real
// doors overwhelmingly use TRANSITION_TYPE_NORMAL for their
// transition_type, which DoExitTransition copies into player_status as
// spawn_type, and TRANSITION_TYPE_NORMAL and PL_SPAWN_DEFAULT are both 0 -
// i.e. ordinary vanilla doors already spawn the player with
// PL_SPAWN_DEFAULT, same as this file always has).
//
// Castor Darknut Hall's link is on real door coordinates end to end
// (confirmed reachable by walking straight up from around local x=390).
//
// Castle Garden -> Melari's Mine (leaving through the bottom) is NOT in
// this table - Castle Garden's south edge is a real WARP_TYPE_BORDER
// transition (src/data/transitions.c, gExitList_CastleGarden_Main's last
// entry), and unlike the WARP_TYPE_AREA doors discussed above,
// border-type transitions don't depend on the undecompiled
// GetActTileAtTilePos at all (IsPosInBorderTransitionRegion, scroll.c,
// only checks facing direction and which half of the room you're in) -
// confirmed empirically to still fire under QUICKSTART (walking off
// Castle Garden's south edge currently lands you in Hyrule Field). That
// entry is retargeted to Melari's Mine under #ifdef QUICKSTART instead of
// being reproduced here, since it already reliably covers the entire
// south edge - a table row using a position box would just be a strictly
// worse copy of a mechanism that already works.
typedef struct {
    u8 fromArea;
    u8 fromRoom;
    s16 triggerMinX;
    s16 triggerMaxX;
    s16 triggerMinY;
    s16 triggerMaxY;
    u8 toArea;
    u8 toRoom;
    s16 spawnX;
    s16 spawnY;
} QuickStartLink;

static const QuickStartLink sQuickStartLinks[] = {
    // Castor Darknut Hall -> Melari's Mine, arriving at the corridor's west
    // end (Door A). Trigger box is Hall's own (only) real door,
    // gExitList_CastorDarknut_Hall[0] (startX=0x188, startY=0x18,
    // AREA_12x12 -> box +6/+6), which in vanilla leads to Castor Caves -
    // confirmed reachable by walking straight up from around local x=390.
    { AREA_CASTOR_DARKNUT, ROOM_CASTOR_DARKNUT_HALL, 0x188, 0x18e, 0x18, 0x1e, AREA_MELARIS_MINE,
      ROOM_MELARIS_MINE_MAIN, 0xa0, 0x56 },
    // Melari's Mine, Door A (west end of the corridor) -> back to Castor
    // Darknut Hall. Box is centered on the real Crenel Minish Paths door's
    // own coordinates (gExitList_MelarisMine_Main[0]: startX=0x78,
    // startY=0x38, AREA_12x12 -> box +6/+6) - tightened from the much
    // larger area this used before (which fired the instant the player
    // took one step off the Hall-arrival spawn point, before ever visually
    // reaching the archway) - but widened slightly northwest of the real
    // box, to (0x6c-0x7e, 0x32-0x3e): walking directly at the real box
    // stops just short of it at local (115, 55), a few px northwest of
    // (120-126, 56-62), confirmed a hard wall (600 frames of holding
    // toward it made no further progress) rather than a slow creep like
    // Hall's own door had. The real box alone is therefore unreachable on
    // foot; this is the smallest box that both contains it and reaches
    // the actual walkable corner.
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x6c, 0x7e, 0x32, 0x3e, AREA_CASTOR_DARKNUT,
      ROOM_CASTOR_DARKNUT_HALL, 0x64, 0x5e },
    // Melari's Mine, Door B -> Castle Garden, arriving at its south end
    // ("the bottom"). Door B is NOT on the top corridor - it's near the
    // real Mt Crenel Cavern of Flames door's own coordinates
    // (gExitList_MelarisMine_Main[1]: startX=0x70, startY=0x12c,
    // AREA_12x12 -> box +6/+6) in the larger open space below the
    // corridor, on the room's far west side (that real door's own
    // facing_direction, 0x6/west, matches "exiting left"). Confirmed
    // reachable from the corridor by a specific route: down through a gap
    // around local x=580 into the lower space, then walkable most of the
    // way west, then up through a second gap around local x=140-160 that
    // lands right next to this door. That approach is also the ONLY
    // direction this spot is reachable from at all (walking down from the
    // north or up from the south dead-ends well short of it) - and the
    // real box's own tight 6x6px size meant a fast walk-left could overshoot
    // past it in a single frame before ever registering, only catching on
    // a slower second attempt. Widened well past the real box (to
    // 0x64-0x8c x, 0x128-0x136 y) in the one direction that matters (further
    // east, the approach side) so a normal walking speed can't skip over it.
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x64, 0x8c, 0x128, 0x136, AREA_CASTLE_GARDEN,
      ROOM_CASTLE_GARDEN_MAIN, 0x1f8, 0x1e0 },
    // Melari's Mine's three remaining real doors (Minish House Interiors -
    // Southwest, Southeast, East), opened for future NPCs. Each trigger box
    // is that door's own real coordinates (gExitList_MelarisMine_Main[2],
    // [3], [4] respectively, all AREA_12x12 -> box +6/+6); each interior
    // room's own return trip uses its single real exit (a WARP_TYPE_BORDER,
    // retargeted in transitions.c) rather than a table row here, same
    // reasoning as Castle Garden's south border - it already reliably
    // fires without needing GetActTileAtTilePos. All three interior rooms
    // are small, single-screen, and confirmed reachable from Melari's
    // Mine's existing walkable network (each door's immediate approach
    // connects back to already-verified ground within a few hundred
    // frames of walking).
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0xa8, 0xae, 0x220, 0x226, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST, 0x78, 0x64 },
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x228, 0x22e, 0x220, 0x226, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST, 0x78, 0x64 },
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x280, 0x286, 0x11c, 0x122, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST, 0x78, 0x64 },
};

// All of Melari's Mine's stock NPCs disabled for now, not just the ones
// directly blocking the two doors - this room is meant to get its own
// custom NPCs later, and one of the MOUNTAIN_MINISH wanderers otherwise
// stands right next to Door B guarding it, physically blocking the path
// to Castle Garden. Simplest to just clear the whole room's NPCs
// (MOUNTAIN_MINISH and Melari herself alike) unconditionally, every
// frame, the same way QuickStartClearCastleGuards clears GUARD_1.
static void QuickStartClearMelarisMineObstacles(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC) {
            DeleteEntity(&gEntities[i].base);
        }
    }
}

// Same density target as Castle Garden (1 per 32x32 square): Melari's Mine
// is 720x624px -> 22x19 squares -> 418/25 -> 16 enemies. Unlike Castle
// Garden's hedge maze, most of this room's own bounding box is solid rock
// rather than open floor with occasional obstacles - a blind grid mostly
// landed inside walls (confirmed empirically: 12 of 16 grid-spaced probes
// couldn't move in any direction at all). Every position below was
// individually verified walkable in the emulator instead, spread across
// the top corridor and the larger space below it (both Door A/B's own
// vicinities avoided, so this can't interfere with either link's box).
static const s16 sQuickStartMineEnemyOffsets[16][2] = {
    { 0xfa, 0x56 },  { 0x14a, 0x56 },  { 0x19a, 0x56 },  { 0x1ea, 0x56 },  { 0x23a, 0x56 },
    { 0x96, 0x1cc }, { 0xfa, 0x1cc },  { 0x226, 0x1cc }, { 0x100, 0x100 }, { 0x193, 0x14e },
    { 0xe4, 0x137 }, { 0x15e, 0x12c }, { 0x258, 0x15e }, { 0x96, 0x15e },  { 0x17c, 0x10e },
    { 0x140, 0x17c },
};
// All Octoroks (rather than a mixed pool) so an automated/AI test pass can
// verify the wave-clear reward drop unambiguously - one known enemy type
// throughout, instead of needing to recognize 4 different ones.
static void QuickStartSpawnMelarisMineEnemiesOnce(void) {
    s32 i;
    if (GetInventoryValue(ITEM_5A) != 0) {
        return;
    }
    if (CheckRoomFlag(1)) {
        return;
    }
    {
        u8 enemyType = QuickStartScaleEnemyType(OCTOROK, QuickStartGetDifficulty());
        for (i = 0; i < ARRAY_COUNT(sQuickStartMineEnemyOffsets); i++) {
            Entity* enemy = CreateEnemy(enemyType, 0);
            if (enemy != NULL) {
                enemy->x.HALF.HI = gRoomControls.origin_x + sQuickStartMineEnemyOffsets[i][0];
                enemy->y.HALF.HI = gRoomControls.origin_y + sQuickStartMineEnemyOffsets[i][1];
                enemy->collisionLayer = 1;
                enemy->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(enemy);
            }
        }
    }
    SetRoomFlag(1);
}

// Drops the heart piece at its fixed spot and marks ITEM_5A "earned" +
// room flag 2 "watching this visit's drop" - shared by the initial grant
// and the re-drop path in QuickStartSpawnMelarisMineRewardOnce below.
static void QuickStartSpawnMelarisMineRewardItem(void) {
    Entity* itemEntity = CreateObject(GROUND_ITEM, ITEM_HEART_PIECE, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + 0x100;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + 0x100;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
        SetInventoryValue(ITEM_5A, 1);
        SetRoomFlag(2);
    }
}

// Heart piece reward once the room's own wave is cleared - a quarter heart,
// not a full container, since this is just one of the loop's several
// gauntlets rather than a dungeon-boss-tier reward. No manual maxHealth
// bookkeeping needed here either: a GROUND_ITEM of ITEM_HEART_PIECE already
// routes through the vanilla LinkHoldingItem_Action3 pickup cutscene on its
// own (itemOnGround.c's CheckShouldPlayItemGetCutscene forces the cutscene
// path for any item with the metadata's unk3 0x2 bit set, which
// ITEM_HEART_PIECE has same as ITEM_HEART_CONTAINER), and that cutscene is
// what actually grants the permanent health increase (4 pieces = +8
// maxHealth) - the same mechanism a real overworld heart piece uses.
//
// ITEM_5A is a 3-state flag like Castle Garden's ITEM_32: 0 = not earned,
// 1 = earned and a ground item is (or was) dropped, 2 = confirmed picked
// up. Melari's Mine has five real exits within easy reach of the reward
// spot (Hall, Castle Garden, and the three house doors), all of which wipe
// ground items same as they wipe enemies - leaving before grabbing the
// drop used to lose it permanently (ITEM_5A already 1, nothing left to
// re-drop it). Room flag 2 (flag 1 is already this room's own "wave is up"
// marker) tracks "watching a drop THIS visit", same logic as Castle
// Garden's fix: vanished-while-still-watching means a genuine pickup
// (promote to 2); vanished-on-a-fresh-visit means it was wiped before
// pickup, so re-drop it.
static void QuickStartSpawnMelarisMineRewardOnce(void) {
    s32 i;
    if (GetInventoryValue(ITEM_5A) >= 2) {
        return;
    }
    if (GetInventoryValue(ITEM_5A) == 0) {
        if (!CheckRoomFlag(1)) {
            return;
        }
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                return;
            }
        }
        QuickStartSpawnMelarisMineRewardItem();
        return;
    }
    if (QuickStartGroundItemAt(0x100, 0x100)) {
        SetRoomFlag(2);
        return;
    }
    if (CheckRoomFlag(2)) {
        SetInventoryValue(ITEM_5A, 2);
        return;
    }
    QuickStartSpawnMelarisMineRewardItem();
}

// The first of several planned NPCs for Melari's Mine's newly-opened side
// rooms - a merchant selling a small fixed catalog (see
// script_QuickStartMerchant), using the exact vanilla shop mechanism
// (ScriptCommand_SaleItemConfirmMessage/CheckShopItemPrice/BuyShopItem,
// the same trio Beedle and Talon's own shops use) rather than anything
// custom-built. Reuses the ZELDA entity kind rather than a real
// shopkeeper's (Stockwell/Beedle) - those kinds dispatch through their own
// action-function tables that expect a ScriptExecutionContext already
// wired up their own specific way (e.g. Stockwell's `this->context`, set
// up only by his own vanilla init code), incompatible with the generic
// StartCutscene-based script attachment QuickStartMakeNpcTalkable uses.
// ZELDA's is already proven generic and safe (used for the Main
// item-choice sign earlier in this file) - the merchant will look like
// Zelda for now, a cosmetic mismatch rather than a functional one.
static void QuickStartSpawnMelarisMineMerchantOnce(void) {
    s32 i;
    Entity* npc;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
            return;
        }
    }
    npc = CreateNPC(ZELDA, 0, 0);
    if (npc != NULL) {
        npc->x.HALF.HI = gRoomControls.origin_x + 0xb4;
        npc->y.HALF.HI = gRoomControls.origin_y + 0x5a;
        npc->collisionLayer = 1;
        UpdateSpriteForCollisionLayer(npc);
        QuickStartMakeNpcTalkable(npc, &script_QuickStartMerchant);
    }
}

// The merchant's fixed catalog, displayed as liftable SHOP_ITEM pedestal
// props rather than offered through dialogue - the real vanilla shop UX
// (Stockwell, the Goron Merchant): the player lifts one, carries it to the
// merchant, and script_QuickStartMerchant completes the sale based on
// whatever's in gRoomVars.shopItemType, exactly like Beedle/Talon's own
// scripts do. The room (room_header for
// ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST) is a single
// non-scrolling 0xf0x0xa0 screen, so its horizontal center is local x=0x78 -
// which is also the room's own spawn point x, confirming the middle is
// walkable. Positions are a row centered on that, spaced 0x20 apart -
// originally placed further east (0x94-0xd4) clustered off to the merchant's
// side of the room, which made them hard to walk up to; recentered here.
static const u16 sQuickStartShopCatalog[] = { ITEM_BOMBS10, ITEM_ARROWS10, ITEM_SHIELD };
static const s16 sQuickStartShopItemOffsets[][2] = {
    { 0x58, 0x6e },
    { 0x78, 0x6e },
    { 0x98, 0x6e },
};

// Whether one of our own SHOP_ITEM props for the given catalog item still
// exists in the current room - false while it's off being carried, on the
// pedestal, or (per sub_080819B4 in itemForSale.c) has just been consumed
// by a completed purchase and deleted itself.
static bool32 QuickStartShopItemExists(u16 itemId) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == OBJECT && gEntities[i].base.id == SHOP_ITEM &&
            gEntities[i].base.type == itemId && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
            return TRUE;
        }
    }
    return FALSE;
}

// Spawns one catalog item as a liftable pedestal prop at a fixed room-local
// spot. timer=1 selects the more forgiving of ItemForSale's two hitbox
// shapes and (per ItemForSale_MakeInteractable) makes it interactable from
// any direction rather than one specific side. unk_80/unk_82 are the
// reset-position ItemForSale itself uses (sub_080819B4) when the item is
// dropped without being bought - CreateObject leaves them uninitialized for
// a dynamically-spawned entity (they're normally populated by the room's
// own static object data), so they're set explicitly here to the same spot
// the item is placed at, or the prop would snap to a garbage position on a
// cancelled sale.
static void QuickStartSpawnShopItem(u16 itemId, s16 offsetX, s16 offsetY) {
    ItemForSaleEntity* itemEntity = (ItemForSaleEntity*)CreateObject(SHOP_ITEM, itemId, 0);
    if (itemEntity != NULL) {
        itemEntity->base.x.HALF.HI = gRoomControls.origin_x + offsetX;
        itemEntity->base.y.HALF.HI = gRoomControls.origin_y + offsetY;
        itemEntity->base.collisionLayer = 1;
        itemEntity->base.timer = 1;
        itemEntity->unk_80 = offsetX;
        itemEntity->unk_82 = offsetY;
        UpdateSpriteForCollisionLayer(&itemEntity->base);
    }
}

// Polled every frame the player is in the shop room (alongside
// QuickStartSpawnMelarisMineMerchantOnce) so a purchased item's now-deleted
// pedestal prop gets restocked - vanilla's real pedestal shops (Goron
// Merchant etc.) have their own manager entity to do this; we don't have
// that infrastructure, so just re-check and re-spawn missing entries here
// instead.
static void QuickStartMaintainMelarisMineShop(void) {
    s32 i;
    for (i = 0; i < ARRAY_COUNT(sQuickStartShopCatalog); i++) {
        if (!QuickStartShopItemExists(sQuickStartShopCatalog[i])) {
            QuickStartSpawnShopItem(sQuickStartShopCatalog[i], sQuickStartShopItemOffsets[i][0],
                                     sQuickStartShopItemOffsets[i][1]);
        }
    }
}

// --- Castle Garden hidden ladders -----------------------------------------
//
// Three grass patches in Castle Garden (stand-ins for real grass: dynamically
// spawned POT objects, broken by a sword swing the same as any other
// breakable prop, single health point. BUSH was tried first since it reads
// more like grass, but its idle state runs down a gustJarTolerance counter
// every single frame regardless of whether it's actually being gusted -
// confirmed empirically to self-delete after ~32 frames with zero player
// interaction, making it useless as a "sits there until cut" stand-in)
// each hide a ladder down to a single-room "mini dungeon", assigned exactly
// once per save - a chest reward, a mini-boss fight, or an NPC who either
// gives or takes 100 rupees - chosen randomly the first time the player
// ever sets foot in Castle Garden Main and permanently remembered from then
// on. Room flags/inventory slots (used everywhere else in this file for
// "reset on leave" and "gauntlet-once" bookkeeping respectively) can't do
// that: room flags reset on every reload, and every unused Item enum slot
// (ITEM_32/33/5A) is already spoken for by other QUICKSTART features. Global
// flags are the one primitive that's both save-persistent AND has room to
// spare - the named Flag enum (flags.h) only goes up to END=0x65, leaving
// 0x65-0xFF (155 bits) completely unclaimed in FLAG_BANK_0.
#define GF_LADDERS_RANDOMIZED 0x65
#define GF_LADDER_BASE(i) (0x66 + (i) * 18)
#define GF_LADDER_REVEALED(i) (GF_LADDER_BASE(i) + 0)
#define GF_LADDER_KIND_BIT(i, b) (GF_LADDER_BASE(i) + 1 + (b))  // b = 0,1
#define GF_LADDER_EXTRA_BIT(i, b) (GF_LADDER_BASE(i) + 3 + (b)) // b = 0..7
#define GF_LADDER_DONE(i) (GF_LADDER_BASE(i) + 11)
// Which of the 20 "? room" pool entries (sQuickStartQuestionRoomPool below)
// backs this ladder this save - a second independent Random() draw from
// the kind/extra above, so the physical room and the reward/challenge it
// holds vary separately. 6 bits covers indices 0-31, comfortably more than
// the pool's 20 entries.
#define GF_LADDER_ROOM_BIT(i, b) (GF_LADDER_BASE(i) + 12 + (b)) // b = 0..5

// Difficulty counter for the win/reset loop below - well clear of the
// ladder bits above (highest in use is GF_LADDER_ROOM_BIT(2,5) = 155).
// 2 bits -> 0..3, one step harder each time the player wins a round.
// Save-persistent (global flags, not room flags) since it has to survive
// the DoSoftReset a win triggers - EWRAM (and gSave with it) is
// deliberately preserved across that reset (see DoSoftReset, main.c).
#define GF_DIFFICULTY_BIT(b) (174 + (b)) // b = 0,1
#define QUICKSTART_MAX_DIFFICULTY 3

static u8 QuickStartGetDifficulty(void) {
    return (CheckGlobalFlag(GF_DIFFICULTY_BIT(0)) ? 1 : 0) | (CheckGlobalFlag(GF_DIFFICULTY_BIT(1)) ? 2 : 0);
}

static void QuickStartIncrementDifficulty(void) {
    u8 next = QuickStartGetDifficulty();
    if (next < QUICKSTART_MAX_DIFFICULTY) {
        next++;
    }
    if (next & 1) {
        SetGlobalFlag(GF_DIFFICULTY_BIT(0));
    } else {
        ClearGlobalFlag(GF_DIFFICULTY_BIT(0));
    }
    if (next & 2) {
        SetGlobalFlag(GF_DIFFICULTY_BIT(1));
    } else {
        ClearGlobalFlag(GF_DIFFICULTY_BIT(1));
    }
}

// Single shared escalation rule so every wave gets harder the same way
// instead of each spawner inventing its own - a deliberately simple
// "swap the common enemy for a tougher relative once the counter is high
// enough" rule, easy to retune once we see how it plays.
static u8 QuickStartScaleEnemyType(u8 baseType, u8 difficulty) {
    // Golden enemy variants deliberately left out of the rotation for now -
    // not part of the difficulty progression yet.
    if (difficulty >= 1) {
        if (baseType == OCTOROK) {
            return SPEAR_MOBLIN;
        }
    }
    return baseType;
}

enum { LADDER_KIND_CHEST, LADDER_KIND_MINIBOSS, LADDER_KIND_NPC };

static u8 QuickStartLadderGetKind(s32 ladderIndex) {
    return (CheckGlobalFlag(GF_LADDER_KIND_BIT(ladderIndex, 0)) ? 1 : 0) |
           (CheckGlobalFlag(GF_LADDER_KIND_BIT(ladderIndex, 1)) ? 2 : 0);
}

static void QuickStartLadderSetKind(s32 ladderIndex, u8 kind) {
    if (kind & 1) {
        SetGlobalFlag(GF_LADDER_KIND_BIT(ladderIndex, 0));
    }
    if (kind & 2) {
        SetGlobalFlag(GF_LADDER_KIND_BIT(ladderIndex, 1));
    }
}

// Generic 8-bit scratch value per ladder, packed as 8 global flag bits -
// which specific meaning it holds depends on that ladder's kind: a reward
// pool index (chest), or bit 0 alone as a friendly/evil boolean (NPC).
static u8 QuickStartLadderGetExtra(s32 ladderIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 8; b++) {
        if (CheckGlobalFlag(GF_LADDER_EXTRA_BIT(ladderIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartLadderSetExtra(s32 ladderIndex, u8 value) {
    s32 b;
    for (b = 0; b < 8; b++) {
        if (value & (1 << b)) {
            SetGlobalFlag(GF_LADDER_EXTRA_BIT(ladderIndex, b));
        }
    }
}

static u8 QuickStartLadderGetRoomIndex(s32 ladderIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 6; b++) {
        if (CheckGlobalFlag(GF_LADDER_ROOM_BIT(ladderIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartLadderSetRoomIndex(s32 ladderIndex, u8 value) {
    s32 b;
    for (b = 0; b < 6; b++) {
        if (value & (1 << b)) {
            SetGlobalFlag(GF_LADDER_ROOM_BIT(ladderIndex, b));
        }
    }
}

// The "? room" pool: every candidate real, single-exit room found by a
// full scan of every area's exit-transition table (excluding the main
// story dungeons and Hyrule Castle Town's named NPC houses), then further
// narrowed to the 20 confirmed walkable at their default landing spot -
// several other candidates turned out to spawn the player wedged solid in
// every direction (background floor art, not a clearable entity - the
// same class of bug ROOM_TREE_INTERIORS_1c hit below) and were dropped
// rather than shipped un-verified. Each entry's own real exit is
// retargeted under #ifdef QUICKSTART (src/data/transitions.c) to the same
// shared Castle Garden landing spot regardless of which ladder ends up
// using it - unlike the fixed 3-room mapping this replaces, a given
// physical room can be assigned to any of the 3 ladders depending on the
// save, so a per-room-specific return position isn't something a static
// compile-time table can encode any more.
// contentDX/contentDY: how far the reward/enemy/NPC sits from the shared
// (0x78,0x78) spawn point, walked out by hand in the emulator per room -
// most of these turned out to be small single-purpose alcoves built around
// one original vanilla object, not roomy enough for a real "opposite side
// of the room" placement. Where a direction was confirmed to hold up over
// a longer walk (not just a step or two before hitting a wall or sliding
// into a real transition into whatever real content neighbors it), this
// pushes the spawn a bit further that way so it isn't sitting right on
// the door; where every direction beyond a couple pixels turned out
// blocked or led straight out of the room, it's left at (0,0) - there's
// nowhere else confirmed safe to put it.
typedef struct {
    u8 area;
    u8 room;
    s16 contentDX;
    s16 contentDY;
} QuickStartQuestionRoomEntry;

static const QuickStartQuestionRoomEntry sQuickStartQuestionRoomPool[] = {
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_BLUE, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GENTARI_MAIN, 0, 0 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GREEN, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_EXIT, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_TOWN, 0, 0 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_LAKE_HYLIA_OCARINA, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_MINISH_WOODS_BOMB, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_NEXT_TO_KNUCKLE, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_POT_MINISH, 0, 0 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_RED, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SHOE_MINISH, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SIDE_AREA, 0, 16 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD, 0, 16 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE, 0, 16 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WESTERN_WOODS_HEART_PIECE, 0, 16 },
    { AREA_CAVES, ROOM_CAVES_LON_LON_RANCH_WALLET, 0, 0 },
    { AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN, -20, 0 },
    { AREA_CAVES, ROOM_CAVES_TRILBY_RUPEE, -16, 0 },
    { AREA_GREAT_FAIRIES, ROOM_GREAT_FAIRIES_MINISH_WOODS, 0, -16 },
    { AREA_ROYAL_VALLEY_GRAVES, ROOM_ROYAL_VALLEY_GRAVES_GINA, 0, -20 },
};
// Literal, matching this file's other pool-size constants (see
// QUICKSTART_LADDER_REWARD_POOL_SIZE below) rather than a sizeof-derived
// expression, for the same __umodsi3 reason.
#define QUICKSTART_QUESTION_ROOM_POOL_SIZE 20

// Every pool room's retargeted exit (src/data/transitions.c) lands here -
// south of ladder 0's own real HIDDEN_LADDER_DOWN pot (104,104), clear of
// its +/-16 trigger box and far from ladders 1 and 2's boxes too (936,376
// and 650,310) - the exact spot gExitList_TreeInteriors_14 already used
// before this pool existed. Kept here only as documentation of what
// transitions.c's literal 0x68,0x90 means - nothing in this file needs to
// read it back.
#define QUICKSTART_QUESTION_ROOM_RETURN_X 0x68
#define QUICKSTART_QUESTION_ROOM_RETURN_Y 0x90

// Chest rewards deliberately skip the shop's consumables (Bombs10/Arrows10)
// and lean toward upgrades/heart progress, so a ladder chest never feels
// like a smaller version of what Melari's Mine's merchant already sells.
static const u16 sQuickStartLadderRewardPool[] = {
    ITEM_HEART_PIECE, ITEM_BOMBBAG, ITEM_LARGE_QUIVER, ITEM_RUPEE200, ITEM_WALLET, ITEM_KINSTONE_BAG,
};
// A plain literal (matching this file's other enemy/reward pool modulos,
// e.g. "% 3"/"% 4" above) rather than a sizeof-based macro - agbcc emits an
// unsigned modulo helper (__umodsi3, not provided by its runtime lib) for
// the sizeof-derived expression even when cast to (s32) on both sides.
#define QUICKSTART_LADDER_REWARD_POOL_SIZE 6

// Runs every frame in Castle Garden Main but only ever does anything once
// per save (GF_LADDERS_RANDOMIZED) - exactly once, each of the 3 ladders is
// assigned a kind, and (for chest/NPC kinds) which specific reward or
// disposition, all via Random(). Doing this lazily on first room entry
// rather than in GameTask_Transition avoids touching the boot sequence at
// all - the persistent flags this writes make the choice stick for the
// rest of this save regardless of when it first ran.
static void QuickStartRandomizeLaddersOnce(void) {
    s32 i, j;
    u8 usedRoom[3];
    if (CheckGlobalFlag(GF_LADDERS_RANDOMIZED)) {
        return;
    }
    for (i = 0; i < 3; i++) {
        u8 kind = (u8)((s32)Random() % 3);
        u8 roomIdx;
        QuickStartLadderSetKind(i, kind);
        if (kind == LADDER_KIND_CHEST) {
            QuickStartLadderSetExtra(i, (u8)((s32)Random() % QUICKSTART_LADDER_REWARD_POOL_SIZE));
        } else if (kind == LADDER_KIND_NPC) {
            QuickStartLadderSetExtra(i, (u8)((s32)Random() % 2)); // bit 0: 1 = evil, 0 = friendly
        }
        // Distinct room per ladder - two ladders sharing one physical "?
        // room" would make leaving through it ambiguous about which
        // ladder's content to re-arm. The pool (20) comfortably exceeds
        // the 3 draws needed, so a plain reject-and-retry loop is enough.
        for (;;) {
            roomIdx = (u8)((s32)Random() % QUICKSTART_QUESTION_ROOM_POOL_SIZE);
            for (j = 0; j < i; j++) {
                if (usedRoom[j] == roomIdx) {
                    break;
                }
            }
            if (j == i) {
                break;
            }
        }
        usedRoom[i] = roomIdx;
        QuickStartLadderSetRoomIndex(i, roomIdx);
    }
    SetGlobalFlag(GF_LADDERS_RANDOMIZED);
}

// Ladders 0 and 1 sit exactly on top of Castle Garden Main's own real,
// vanilla HIDDEN_LADDER_DOWN fixtures (object.c: HiddenLadderDown, id 87) -
// the game already ships two of these stone dais spots in this room,
// invisible until their own reveal condition fires; confirmed present at
// these two local coordinates by scanning gEntities for id 87 while walking
// the whole room. They stay permanently un-revealed on their own (nothing
// in this file ever satisfies their internal tile-type check), so they
// just sit there harmlessly while our own pot supplies the "cut this to
// open it" interaction at the same visual spot - this is what makes our
// entrances line up with the actual ladder-shaped fixtures already in the
// garden instead of arbitrary grass. Only two such real fixtures exist
// anywhere in this room (verified by an exhaustive room-wide scan), so
// ladder 2 falls back to the previous hand-picked, verified-walkable
// enemy-grid spot (see sQuickStartGardenEnemyOffsets above).
static const s16 sQuickStartLadderPotOffsets[3][2] = {
    { 104, 104 },
    { 936, 376 },
    { 0x28a, 0x136 },
};

// Ladder index is encoded in type2, NOT type - super->type looked like a
// free field to stash it in (0/1/2, distinguishing the 3 pots), but
// BreakPot's own drop-on-death handler (sub_0808288C in pot.c) reads that
// exact same field back as the "form" of a real GROUND_ITEM to spawn on
// death - form 0 and 0xff both mean "drop nothing", but form 1 or 2 (ladder
// 1's or 2's "index") is any OTHER real in-game item, which is exactly why
// one ladder's pot was observed re-dropping what looked like a smith's
// sword: ladder 1's pot had type=1, and BreakPot took that as "drop item
// form 1" instead of "this is ladder 1's pot". type must stay fixed at
// 0xff (drop nothing) for all 3 pots, so the ladder index is tagged via
// type2 instead, offset by 10 to dodge type2==1 specifically (Pot_Init and
// BreakPot both give type2==1 a second, unrelated meaning: an
// already-broken/don't-respawn check through this->flag, a field this
// code never initializes) - 10/11/12 are read by no other pot.c logic.
#define QUICKSTART_LADDER_POT_TYPE2(ladderIndex) (10 + (ladderIndex))

// Existence anywhere in the room, NOT exact position - a real vanilla pot
// can be picked up and carried (playerUtils.c's RegisterCarryEntity path,
// same as any other liftable object), which relocates the entity without
// destroying it. An earlier version of this check compared against the
// pot's exact spawn position (with a small tolerance for Pot_Init's own
// +3px y-nudge on spawn): the moment the player picked a pot up and walked
// it even slightly off that spot, the position check would report it
// "gone", and since the room-flag "watching" state from the prior frame
// was still set, that read as "it was here, now it's missing - must have
// been broken" - incorrectly revealing the ladder just from being carried,
// with no need to ever actually break it. Checking existence instead (is a
// POT tagged with this ladder's type2 marker present ANYWHERE in the room)
// only reports "gone" once the entity is genuinely deleted - which only
// happens via BreakPot (a real sword hit, or a thrown pot shattering on
// impact), not from merely being relocated in the player's hands.
static bool32 QuickStartPotExists(s32 ladderIndex) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == OBJECT && gEntities[i].base.id == POT &&
            gEntities[i].base.type2 == QUICKSTART_LADDER_POT_TYPE2(ladderIndex) &&
            QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
            return TRUE;
        }
    }
    return FALSE;
}

// type = 0xff (drop nothing - see QUICKSTART_LADDER_POT_TYPE2 above) for
// every ladder's pot, regardless of index; type2 = 10 + ladderIndex is what
// actually distinguishes them for QuickStartPotExists.
static void QuickStartSpawnLadderPot(s32 ladderIndex) {
    Entity* pot = CreateObject(POT, 0xff, QUICKSTART_LADDER_POT_TYPE2(ladderIndex));
    if (pot != NULL) {
        pot->x.HALF.HI = gRoomControls.origin_x + sQuickStartLadderPotOffsets[ladderIndex][0];
        pot->y.HALF.HI = gRoomControls.origin_y + sQuickStartLadderPotOffsets[ladderIndex][1];
        pot->collisionLayer = 1;
        pot->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(pot);
    }
}

// Room flags 5, 6, 7 - Castle Garden Main's own gauntlet already claims 0
// and 1 (QuickStartSpawnGardenEnemiesOnce/QuickStartSpawnGardenRewardOnce).
// Same "was it here and is it now gone THIS visit" pattern as
// QuickStartGroundItemAt's callers: a pot wiped by leaving before it's
// broken re-spawns intact on return, rather than being silently
// un-discoverable forever.
static void QuickStartMaintainGardenLadders(void) {
    s32 i;
    for (i = 0; i < 3; i++) {
        s32 watchFlag = 5 + i;
        if (CheckGlobalFlag(GF_LADDER_REVEALED(i))) {
            continue;
        }
        if (QuickStartPotExists(i)) {
            SetRoomFlag(watchFlag);
            continue;
        }
        if (CheckRoomFlag(watchFlag)) {
            SetGlobalFlag(GF_LADDER_REVEALED(i));
            continue;
        }
        QuickStartSpawnLadderPot(i);
    }
}

// Which "? room" pool entry backs a given ladder this save, and where the
// player lands inside it - every pool room was verified walkable at the
// same default (0x78,0x78) spawn (see the pool comment above), so unlike
// the old fixed 3-room mapping this doesn't need a per-ladder spawn
// override.
static void QuickStartGetLadderTarget(s32 ladderIndex, u8* area, u8* room) {
    s32 rawIndex = QuickStartLadderGetRoomIndex(ladderIndex);
    s32 poolIndex = rawIndex % QUICKSTART_QUESTION_ROOM_POOL_SIZE;
    *area = sQuickStartQuestionRoomPool[poolIndex].area;
    *room = sQuickStartQuestionRoomPool[poolIndex].room;
}

// Separate from QuickStartProcessLinks/sQuickStartLinks (which fire
// unconditionally whenever the player's local position falls in their box)
// because these three must additionally be gated on GF_LADDER_REVEALED -
// otherwise the player could fall into a mini dungeon before ever cutting
// the grass that's supposed to reveal it.
static void QuickStartProcessLadderLinks(void) {
    s32 i;
    s16 localX, localY;
    if (gRoomTransition.transitioningOut) {
        return;
    }
    localX = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
    localY = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
    for (i = 0; i < 3; i++) {
        s16 offsetX = sQuickStartLadderPotOffsets[i][0];
        s16 offsetY = sQuickStartLadderPotOffsets[i][1];
        if (!CheckGlobalFlag(GF_LADDER_REVEALED(i))) {
            continue;
        }
        if (localX >= offsetX - 16 && localX <= offsetX + 16 && localY >= offsetY - 16 && localY <= offsetY + 16) {
            u8 targetArea, targetRoom;
            QuickStartGetLadderTarget(i, &targetArea, &targetRoom);
            gRoomTransition.player_status.area_next = targetArea;
            gRoomTransition.player_status.room_next = targetRoom;
            gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
            gRoomTransition.player_status.start_pos_x = 0x78;
            gRoomTransition.player_status.start_pos_y = 0x78;
            gRoomTransition.player_status.layer = 1;
            gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
            gRoomTransition.transitioningOut = 1;
            return;
        }
    }
}

extern Script script_QuickStartLadderNpc0;
extern Script script_QuickStartLadderNpc1;
extern Script script_QuickStartLadderNpc2;
static Script* const sQuickStartLadderNpcScripts[3] = {
    &script_QuickStartLadderNpc0,
    &script_QuickStartLadderNpc1,
    &script_QuickStartLadderNpc2,
};

// These "orphaned" rooms were never actually emptied - they still carry
// their own original static object data (the exact bug report: a room
// packed full of real pre-existing chests, furniture etc., on top of
// whatever we add, left no open floor at all and trapped the player
// between them). Room flag 1 ("obstacles cleared this visit", distinct
// from flag 0's "our own content spawned this visit" below) gates a
// one-time sweep deleting every pre-existing OBJECT/ENEMY/NPC in the room
// before any of our own content goes in, so each mini-dungeon is a genuine
// blank single-room canvas regardless of what its original vanilla data
// happened to contain.
static void QuickStartClearLadderRoomObstacles(void) {
    s32 i;
    if (CheckRoomFlag(1)) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        if ((gEntities[i].base.kind == OBJECT || gEntities[i].base.kind == ENEMY || gEntities[i].base.kind == NPC) &&
            &gEntities[i].base != gRoomControls.camera_target && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
            DeleteEntity(&gEntities[i].base);
        }
    }
    SetRoomFlag(1);
}

// Every "? room" pool entry was confirmed walkable at the shared spawn
// point (0x78,0x78) after QuickStartClearLadderRoomObstacles runs - unlike
// the fixed 3-room mapping this replaced (one of which,
// ROOM_TREE_INTERIORS_1c, turned out to have a dense cross of chest
// sprites baked into its background art, completely boxing in that exact
// spot - entity-clearing alone can't touch background tiles), no
// per-room override was needed there since every surviving pool candidate
// was screened for exactly that failure mode before being added. Content
// still needs its own per-room nudge though (see contentDX/contentDY on
// the pool entries above): dropped directly on the spawn tile, a chest
// reward was observed picking itself up automatically the instant the
// room loads, with no discovery moment at all.
static void QuickStartGetLadderContentOffset(s32 ladderIndex, s16* contentX, s16* contentY) {
    s32 rawIndex = QuickStartLadderGetRoomIndex(ladderIndex);
    s32 poolIndex = rawIndex % QUICKSTART_QUESTION_ROOM_POOL_SIZE;
    *contentX = 0x78 + sQuickStartQuestionRoomPool[poolIndex].contentDX;
    *contentY = 0x78 + sQuickStartQuestionRoomPool[poolIndex].contentDY;
}

// Called every frame the player is in whichever pool room is currently
// assigned to a ladder, keyed by that ladder's index. GF_LADDER_DONE
// permanently stops any further spawning once the chest is looted / the
// mini-boss is dead / the NPC's one-time rupee exchange has happened -
// matching the single-exit design, a plain room flag (reset on every
// reload) is enough to track "spawned this visit" without needing the
// more involved leave-before-resolving recovery the multi-exit rooms
// elsewhere in this file need (there's only the one way in or out here).
static void QuickStartSetupLadderRoomContent(s32 ladderIndex) {
    u8 kind;
    s16 contentX, contentY;
    QuickStartGetLadderContentOffset(ladderIndex, &contentX, &contentY);
    QuickStartClearLadderRoomObstacles();
    if (CheckGlobalFlag(GF_LADDER_DONE(ladderIndex))) {
        return;
    }
    kind = QuickStartLadderGetKind(ladderIndex);
    if (kind == LADDER_KIND_CHEST) {
        if (CheckRoomFlag(0)) {
            if (!QuickStartGroundItemAt(contentX, contentY)) {
                SetGlobalFlag(GF_LADDER_DONE(ladderIndex));
            }
            return;
        }
        {
            s32 extra = QuickStartLadderGetExtra(ladderIndex);
            u16 rewardItem = sQuickStartLadderRewardPool[extra % QUICKSTART_LADDER_REWARD_POOL_SIZE];
            Entity* itemEntity = CreateObject(GROUND_ITEM, rewardItem, 0);
            if (itemEntity != NULL) {
                itemEntity->x.HALF.HI = gRoomControls.origin_x + contentX;
                itemEntity->y.HALF.HI = gRoomControls.origin_y + contentY;
                itemEntity->collisionLayer = 1;
                itemEntity->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(itemEntity);
                SetRoomFlag(0);
            }
        }
    } else if (kind == LADDER_KIND_MINIBOSS) {
        if (CheckRoomFlag(0)) {
            s32 i;
            for (i = 0; i < MAX_ENTITIES; i++) {
                if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                    return;
                }
            }
            SetGlobalFlag(GF_LADDER_DONE(ladderIndex));
            return;
        }
        {
            Entity* enemy = CreateEnemy(DARK_NUT, 0);
            if (enemy != NULL) {
                enemy->x.HALF.HI = gRoomControls.origin_x + contentX;
                enemy->y.HALF.HI = gRoomControls.origin_y + contentY;
                enemy->collisionLayer = 1;
                enemy->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(enemy);
                SetRoomFlag(0);
            }
        }
    } else {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
                return;
            }
        }
        {
            Entity* npc = CreateNPC(ZELDA, 0, 0);
            if (npc != NULL) {
                npc->x.HALF.HI = gRoomControls.origin_x + contentX;
                npc->y.HALF.HI = gRoomControls.origin_y + contentY;
                npc->collisionLayer = 1;
                UpdateSpriteForCollisionLayer(npc);
                QuickStartMakeNpcTalkable(npc, sQuickStartLadderNpcScripts[ladderIndex]);
            }
        }
    }
}

// "Fully contained" per the user's request: once inside Castor Darknut
// (Hall or Main), Melari's Mine, Castle Garden, or the Minish House
// Interiors rooms opened off Melari's Mine, no transition - real or our
// own - is allowed to land anywhere else. This is a blanket safety net on
// top of the specific links above, not a replacement for them: it catches
// every OTHER real exit these rooms have (Castle Garden alone has 5 more
// WARP_TYPE_AREA doors and a WARP_TYPE_BORDER one to Hyrule Field; Hall's
// only other content is the one real door already repurposed above)
// regardless of whether a given one currently fires under QUICKSTART -
// checked every frame, right after UpdateDoorTransition and UpdateScroll
// (see the call site in QuickStartRoomMonitor, itself called after both of
// those every frame) so a same-frame cancel always lands before the fade
// actually starts. AREA_TREE_INTERIORS is included too, since
// QuickStartProcessLadderLinks' own transition into it would otherwise get
// cancelled by this same function the instant it fires - it's listed here
// as a whole area (rather than per-room) because Minish House Interiors
// already needed to be, for Melari's Mine. The "? room" pool's other areas
// (Caves, Great Fairies, Royal Valley Graves) deliberately AREN'T added
// here: each pool room was selected specifically for having exactly one
// real exit (see sQuickStartQuestionRoomPool above), so there's no "every
// OTHER real exit" left for a blanket area-wide net to catch - the one
// real exit each has is already individually retargeted in
// transitions.c, same mechanism as Tree Interiors' ladder rooms below.
static bool32 QuickStartAreaContained(u8 area) {
    return area == AREA_CASTOR_DARKNUT || area == AREA_MELARIS_MINE || area == AREA_CASTLE_GARDEN ||
           area == AREA_MINISH_HOUSE_INTERIORS || area == AREA_TREE_INTERIORS;
}

// Which ladder (0-2) the current room is standing in for, or -1 if it
// isn't one of the 3 currently-assigned "? room" pool rooms. Unlike the
// old fixed 3-branch dispatch this replaces, the pool spans several real
// areas (Minish House Interiors, Tree Interiors, Caves, Great Fairies,
// Royal Valley Graves) and which physical room maps to which ladder
// varies per save, so a plain area/room comparison against 3 fixed
// constants no longer works - this checks against each ladder's current
// runtime assignment instead.
static s32 QuickStartFindLadderForCurrentRoom(void) {
    s32 i;
    for (i = 0; i < 3; i++) {
        s32 rawIndex = QuickStartLadderGetRoomIndex(i);
        s32 poolIndex = rawIndex % QUICKSTART_QUESTION_ROOM_POOL_SIZE;
        if (gRoomControls.area == sQuickStartQuestionRoomPool[poolIndex].area &&
            gRoomControls.room == sQuickStartQuestionRoomPool[poolIndex].room) {
            return i;
        }
    }
    return -1;
}

// Where each ladder's own real exit already lands (gExitList_TreeInteriors_14/
// _1c/_UnusedHeartContainer, back when those 3 specific rooms were each
// permanently tied to one ladder) - south of that ladder's own pot, clear
// of its +/-16 trigger box. Every "? room" pool entry's retargeted exit
// (src/data/transitions.c) points at the same literal spot regardless of
// which ladder it's serving this save, since which physical room backs
// which ladder varies per save and a compile-time table can't encode
// that - QuickStartFixupQuestionRoomReturn below corrects the landing
// position to the right one of these 3 before the transition completes.
// Ladder 1's spot was originally (936,416) - 40px south of its pot at
// (936,376) - which the emulator showed lands the player inside the
// castle's solid outer wall. A closer offset directly south (936,396)
// turned out to be no better - that whole crop-field patch is planted
// solid, and the player is locked in place there too, unable to move in
// any of the 4 directions at all (confirmed by comparing screenshots
// before/after holding each direction - the player's sprite doesn't move
// a single pixel relative to the background in any of them). (800,396),
// on the paved path between the hedge rows west of the crops, is
// confirmed free to walk in all 4 directions the same way.
static const s16 sQuickStartLadderReturnSpots[3][2] = {
    { 0x68, 0x90 },
    { 0x320, 0x18c },
    { 0x28a, 0x15e },
};

// Runs every frame regardless of area (like QuickStartEnforceContainment,
// called alongside it below) so it catches the outgoing transition while
// still standing in the "? room" itself, the same frame the real engine
// populates player_status from transitions.c's static table. Every pool
// room's retargeted exit resolves to the same literal Castle Garden spot
// (ladder 0's), so without this fixup the player would always reappear at
// ladder 0's spot no matter which ladder's room they actually left
// through.
static void QuickStartFixupQuestionRoomReturn(void) {
    s32 ladderIndex;
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomTransition.player_status.area_next != AREA_CASTLE_GARDEN ||
        gRoomTransition.player_status.room_next != ROOM_CASTLE_GARDEN_MAIN) {
        return;
    }
    ladderIndex = QuickStartFindLadderForCurrentRoom();
    if (ladderIndex < 0) {
        return;
    }
    gRoomTransition.player_status.start_pos_x = sQuickStartLadderReturnSpots[ladderIndex][0];
    gRoomTransition.player_status.start_pos_y = sQuickStartLadderReturnSpots[ladderIndex][1];
}

// "? room" pool entries outside Minish House Interiors/Tree Interiors
// (Caves, Great Fairies, Royal Valley Graves) deliberately aren't added
// wholesale to QuickStartAreaContained's area list - those areas are used
// all over the real game from many unrelated vanilla entrances, and
// blanket-containing them would block every one of THOSE rooms' own real
// exits back to the ordinary overworld, a regression far bigger than this
// feature. Instead, this checks the one specific transition
// QuickStartProcessLadderLinks itself is about to make - into whichever
// pool room the ladder the player just stepped into currently resolves
// to - and lets that one through regardless of which area it's in, same
// as the fixed-area escape hatch does for Tree Interiors/Minish House
// Interiors.
static bool32 QuickStartIsCurrentLadderTarget(u8 area, u8 room) {
    s32 i;
    for (i = 0; i < 3; i++) {
        u8 targetArea, targetRoom;
        QuickStartGetLadderTarget(i, &targetArea, &targetRoom);
        if (area == targetArea && room == targetRoom) {
            return TRUE;
        }
    }
    return FALSE;
}

static void QuickStartEnforceContainment(void) {
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (!QuickStartAreaContained(gRoomControls.area)) {
        return;
    }
    if (QuickStartIsCurrentLadderTarget(gRoomTransition.player_status.area_next, gRoomTransition.player_status.room_next)) {
        return;
    }
    if (!QuickStartAreaContained(gRoomTransition.player_status.area_next)) {
        gRoomTransition.transitioningOut = 0;
    }
}

static void QuickStartProcessLinks(void) {
    s32 i;
    s16 localX, localY;
    if (gRoomTransition.transitioningOut) {
        return;
    }
    localX = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
    localY = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
    for (i = 0; i < ARRAY_COUNT(sQuickStartLinks); i++) {
        const QuickStartLink* link = &sQuickStartLinks[i];
        if (gRoomControls.area == link->fromArea && gRoomControls.room == link->fromRoom && localX >= link->triggerMinX &&
            localX <= link->triggerMaxX && localY >= link->triggerMinY && localY <= link->triggerMaxY) {
            gRoomTransition.player_status.area_next = link->toArea;
            gRoomTransition.player_status.room_next = link->toRoom;
            gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
            gRoomTransition.player_status.start_pos_x = link->spawnX;
            gRoomTransition.player_status.start_pos_y = link->spawnY;
            gRoomTransition.player_status.layer = 1;
            gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
            gRoomTransition.transitioningOut = 1;
            return;
        }
    }
}

// Polled every frame regardless of item-choice phase (unlike
// QuickStartUpdateItemChoice, which is specific to Castor Darknut Main) so
// that leaving the starting room still gets QUICKSTART treatment.
static void QuickStartRoomMonitor(void) {
    QuickStartEnforceContainment();
    QuickStartFixupQuestionRoomReturn();
    if (gRoomControls.area == AREA_CASTOR_DARKNUT && gRoomControls.room == ROOM_CASTOR_DARKNUT_HALL) {
        QuickStartSpawnHallEnemiesOnce();
    } else if (gRoomControls.area == AREA_MELARIS_MINE && gRoomControls.room == ROOM_MELARIS_MINE_MAIN) {
        QuickStartClearMelarisMineObstacles();
        QuickStartSpawnMelarisMineRewardOnce();
        QuickStartSpawnMelarisMineEnemiesOnce();
    } else if (gRoomControls.area == AREA_CASTLE_GARDEN && gRoomControls.room == ROOM_CASTLE_GARDEN_MAIN) {
        QuickStartClearCastleGuards();
        QuickStartSpawnGardenRewardOnce();
        QuickStartSpawnGardenEnemiesOnce();
        // Ground-item pickup alone sets a skill's ITEM_SKILL_* inventory
        // flag but (outside of a full player (re)init) doesn't itself
        // refresh gPlayerState.skills - same gap already hit and fixed for
        // the earlier Woods-gauntlet prototype's boss-skill reward. Cheap
        // and idempotent to just keep it in sync every frame here instead
        // of needing an exact "on pickup" hook.
        UpdatePlayerSkills();
        QuickStartRandomizeLaddersOnce();
        QuickStartMaintainGardenLadders();
        QuickStartProcessLadderLinks();
        QuickStartSpawnWinKeyOnce();
        QuickStartCheckWinCondition();
    } else if (gRoomControls.area == AREA_MINISH_HOUSE_INTERIORS &&
               gRoomControls.room == ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST) {
        QuickStartSpawnMelarisMineMerchantOnce();
        QuickStartMaintainMelarisMineShop();
    } else {
        s32 ladderIndex = QuickStartFindLadderForCurrentRoom();
        if (ladderIndex >= 0) {
            QuickStartSetupLadderRoomContent(ladderIndex);
        }
    }
    QuickStartProcessLinks();
}

// A freshly created NPC otherwise keeps whatever stale facing/interactable/
// action state was left in that entity slot by its previous occupant. The
// Zelda entity kind (see npc/zelda.c: Zelda()) dispatches on ->action through
// a 2-entry function pointer table where only action==0 runs the proper
// first-tick setup (entity list ordering, PRIO_MESSAGE, InitScriptForNPC) -
// reset it explicitly, along with facing and interactability.
//
// sub_0807DD80 (used by static room NPCs) assumes ->cutsceneBeh already
// points at a valid, pre-existing ScriptExecutionContext and just
// re-initializes it in place - for a freshly CreateNPC'd entity that
// pointer is stale garbage, so that dereference was writing the script
// through a garbage pointer instead of ever actually attaching it (this is
// why dialogue never rendered: the NPC's script was never really running).
// StartCutscene is the generic, self-contained version that allocates its
// own context from the pool and wires cutsceneBeh to point at it - the
// correct call for an entity with no pre-existing script context.
// The engine's default NPC interact hitbox (gHitbox_2, used by ZELDA via
// GetNPCDefinition) is only 8x8px, checked against a point offset from the
// player by a small facing-dependent vector - in practice a very unforgiving
// window that requires near pixel-perfect positioning to trigger, which is
// fine for precisely-scripted test input but not for normal player movement.
// Give our sign NPCs a much larger interact zone instead.
static const Rect sQuickStartNpcInteractHitbox = { 0, 0, 20, 20 };

static void QuickStartMakeNpcTalkable(Entity* npc, Script* script) {
    s32 index;

    npc->action = 0;
    npc->animationState = IdleSouth;
    StartCutscene(npc, script);
    index = AddInteractableObject(npc, INTERACTION_TALK, KINSTONE_NONE);
    if (index >= 0) {
        // AddInteractableObject only fills in entity/type/kinstoneId - it
        // reuses whatever candidate slot GetInteractableObjectIndex(0) hands
        // back without clearing the rest, so interactDirections (lower 4
        // bits: which facing directions Link is allowed to interact from,
        // 0 = any) can still hold a restrictive leftover value from
        // whatever this room's own entities registered there before we
        // deleted them. Force it open from every direction.
        gPossibleInteraction.candidates[index].interactDirections = 0;
        gPossibleInteraction.candidates[index].customHitbox = &sQuickStartNpcInteractHitbox;
    }
}

// Castor Darknut Main's safe walkable area - verified by actually walking
// the player through it in the emulator - is roughly a 199x135 box from
// world (36,39) to (235,174), origin (0,0). Every choice phase reuses this
// same 3-slot item row; the single instructive sign sits in its own row
// well above it (75px vertical separation), so browsing never risks an
// accidental pickup.
static const s16 sQuickStartItemOffsets[QUICKSTART_ITEM_CHOICES] = { 0x6e, 0x96, 0xbe };

static void QuickStartSpawnItems(const QuickStartItemChoice* choices) {
    s32 i;
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        Entity* itemEntity = CreateObject(GROUND_ITEM, choices[i].itemId, 0);
        if (itemEntity != NULL) {
            itemEntity->x.HALF.HI = gRoomControls.origin_x + sQuickStartItemOffsets[i];
            itemEntity->y.HALF.HI = gRoomControls.origin_y + 0x87;
            itemEntity->collisionLayer = 1;
            itemEntity->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(itemEntity);
        }
    }
}

static bool32 QuickStartAnyPickedUp(const QuickStartItemChoice* choices) {
    s32 i;
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        if (GetInventoryValue(choices[i].itemId) != 0) {
            return TRUE;
        }
    }
    return FALSE;
}

static void QuickStartSpawnStarterChoice(void) {
    Entity* npc;

    QuickStartSpawnItems(sQuickStartStarterItems);

    npc = CreateNPC(ZELDA, 0, 0);
    if (npc != NULL) {
        npc->x.HALF.HI = gRoomControls.origin_x + 0x46;
        npc->y.HALF.HI = gRoomControls.origin_y + 0x3c;
        npc->collisionLayer = 1;
        npc->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(npc);
        QuickStartMakeNpcTalkable(npc, &script_QuickStartChooseOne);
    }
}

// Scan rather than a flag, since this needs to survive repeated calls
// during the fade-in with no new persistent storage.
static void QuickStartSpawnStarterChoiceOnce(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
            return;
        }
    }
    QuickStartSpawnStarterChoice();
}

// ItemOnGround has a built-in ~10-second despawn timer meant for enemy
// drops (see itemOnGround.c: unk_6c counts down and deletes the entity at
// 0). Our pedestal items need to sit until chosen, so keep resetting it
// every frame for as long as we're still in a choosing phase.
static void QuickStartRefreshItemTimers(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM) {
            ((ItemOnGroundEntity*)ent)->unk_6c = 600;
        }
    }
}

static void QuickStartDeleteGroundItemsAndSigns(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if ((ent->kind == OBJECT && ent->id == GROUND_ITEM) || (ent->kind == NPC && ent->id == ZELDA)) {
            DeleteEntity(ent);
        }
    }
}

static void QuickStartSpawnChest(void) {
    // Not a literal treasure-chest sprite/tile (the room was never authored
    // with one, and the real chest objects - ChestSpawner/SpecialChest -
    // resolve their contents through room-authored tile data we don't have),
    // just the same reliable ground-item pickup used everywhere else in this
    // room, placed at the room's center. ITEM_HEART_PIECE is the actual
    // vanilla "quarter of a heart container" item - object/linkHoldingItem.c
    // (LinkHoldingItem_Action3) already handles it correctly on its own
    // (increments gSave.stats.heartPieces, only turning into a permanent
    // +1 max heart once 4 have been collected), so no extra bookkeeping is
    // needed here.
    Entity* itemEntity = CreateObject(GROUND_ITEM, ITEM_HEART_PIECE, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + 0x87;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + 0x6a;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
    }
}

// Phase progression for gRoomTransition.field_0x4[0]:
//   0 - choosing starting weapon (bombs/bow/boomerang)
//   1 - pending starting weapon pickup cutscene
//   2 - choosing bonus reward (heart container/100 rupees/red potion)
//   3 - pending bonus reward pickup cutscene
//   4 - choosing tiger scroll (spin attack/roll attack/peril beam)
//   5 - pending tiger scroll pickup cutscene
//   6 - combat wave 1: 3 Octoroks are up
//   7 - combat wave 2: 4 Octoroks are up
//   8 - combat wave 3: 2 Octoroks + a Darknut are up
//   9 - reward chest is up, waiting to be collected
//   10 - done
static void QuickStartUpdateItemChoice(void) {
    u8 phase = gRoomTransition.field_0x4[0];

    // This whole state machine (item choices, then all 3 combat waves, then
    // the chest) is scoped to Castor Darknut Main alone. Without this guard,
    // once BossDoor stopped blocking the south exit, wandering into Hall
    // (or beyond) right as the current wave's last enemy died would spawn
    // the next wave wherever the player currently stood (using whatever
    // room's gRoomControls.origin_x/y happened to be active at that
    // moment), instead of back in Main where it belongs. Simply pausing
    // everything outside Main - no spawning, no phase advancement - until
    // the player returns keeps every wave anchored to the right room.
    if (gRoomControls.area != QUICKSTART_AREA || gRoomControls.room != QUICKSTART_ROOM) {
        return;
    }

    if (phase == 1 || phase == 3 || phase == 5) {
        // NOTE: field_0x4[1] (the other byte in this array) is the vanilla
        // game-over trigger flag - CheckGameOver() in src/gameUtils.c treats
        // any nonzero value there as "start the death sequence". Never use
        // it for anything else; a prior attempt to repurpose it as a delay
        // counter here silently forced the game into TASK_GAMEOVER.
        if (gPlayerEntity.base.action != PLAYER_NORMAL) {
            return;
        }
        // Phase 5 additionally waits on the skill-get message triggered
        // above (phase 4's handler) actually being dismissed - unlike the
        // starter/bonus rows' vanilla pickup cutscene, showing this message
        // doesn't itself change gPlayerEntity.base.action away from
        // PLAYER_NORMAL, so without this the very next frame's check above
        // would already pass and spawn wave 1 (RELOAD_ALL and all) out from
        // under a message the player hasn't even had a chance to read yet -
        // confirmed in the emulator before this check was added.
        if (phase == 5 && (gMessage.state & MESSAGE_ACTIVE)) {
            return;
        }
        // These were spawned with ENT_PERSIST so an incidental reload
        // elsewhere (e.g. a menu-triggered one) can't wipe them out before
        // the player has chosen - which also means they won't get cleared
        // by the reload we trigger going into combat. Tear them down
        // explicitly so each new phase (and the combat room) starts clean.
        QuickStartDeleteGroundItemsAndSigns();
        // RELOAD_ALL (unlike a full room init) never calls
        // ResetPossibleInteraction(), so gPossibleInteraction/
        // gInteractableObjects would otherwise keep dangling references to
        // the entities just deleted above. Clear it out before anything
        // reuses those slots.
        ResetPossibleInteraction();
        if (phase == 1) {
            // The bonus item row spawns at the exact same coordinates as the
            // starter item row, and the player is still standing on/next to
            // whichever starter item they just picked up - without moving
            // them away first, the new items would spawn on top of the
            // player and get auto-picked-up instantly, cascading straight
            // through this phase (and the next) unintended. Send the player
            // back to the room's spawn point, which is clear of every
            // item-row x-offset, before spawning the next set of items.
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + 0x46;
            gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + 0x9b;
            QuickStartSpawnItems(sQuickStartBonusItems);
            gRoomTransition.field_0x4[0] = 2;
        } else if (phase == 3) {
            // ITEM_HEART_CONTAINER's own metadata has no GiveItem-switch
            // effect (unk1 == 0) - it's normally a special boss-reward
            // object (object/heartContainer.c) that spawns its own cutscene
            // entity outside the generic pickup flow. Grant the actual
            // effect ourselves: a full heart is 8 health units in this
            // engine (see ui.c: gHUD.maxHealth = gSave.stats.maxHealth >> 1,
            // with gHUD.maxHealth itself in quarter-heart units).
            if (GetInventoryValue(ITEM_HEART_CONTAINER) != 0) {
                gSave.stats.maxHealth += 8;
                gSave.stats.health = gSave.stats.maxHealth;
            }
            // Same reasoning as phase 1 above: reposition before the skill
            // item row spawns at the same reused coordinates.
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + 0x46;
            gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + 0x9b;
            QuickStartSpawnItems(sQuickStartSkillItems);
            gRoomTransition.field_0x4[0] = 4;
        } else {
            // UpdatePlayerSkills (playerUtils.c) is what actually turns the
            // ITEM_SKILL_* inventory flag into a usable gPlayerState.skills
            // bit - it normally only runs once per full player (re)init,
            // which this mid-game reload doesn't trigger (the player entity
            // persists across RELOAD_ALL, unlike a real area transition).
            UpdatePlayerSkills();
            // Spawn wave 1 directly here, edge-triggered exactly like waves
            // 2 and 3 - NOT via a "spawn during this reload's fade-in"
            // idempotent poll (as this used to work). That indirection meant
            // ANY later reload while still on phase 6 - including simply
            // walking back into Main after leaving before wave 1 was fully
            // cleared - would find zero Octoroks alive and spawn a fresh
            // set, resurrecting enemies the player had already defeated.
            // These have ENT_PERSIST, so they survive the RELOAD_ALL below
            // just fine without needing to be (re)created during it.
            QuickStartSpawnEnemies();
            gRoomTransition.field_0x4[0] = 6;
            // reload_flags alone is not self-executing: it's only consumed by
            // UpdateScroll's Scroll0/Scroll2 handlers (see scroll.c), which are
            // what actually clear it back to 0 and let GameMain_ChangeRoom hand
            // control back to GameMain_Update. The vanilla door-transition path
            // (sub_0807BD14 in playerUtils.c) always pairs reload_flags = 1 with
            // scrollAction = 2 for exactly this reason. scrollAction's steady-
            // state value during normal play is 1 (Scroll1, plain camera
            // follow), which never touches reload_flags at all - so setting
            // reload_flags without also resetting scrollAction here left it
            // permanently stuck at 1 with the room transition never completing:
            // a real, silent soft-lock (substate parked on GAMEMAIN_CHANGEROOM
            // forever), not a crash - this is what looked like "the game
            // freezes" during real play. Scroll0 is the handler that clears
            // reload_flags and hands substate back, so force that path.
            gRoomControls.scrollAction = 0;
            gRoomControls.reload_flags = RELOAD_ALL;
        }
        return;
    }

    if (phase == 0 || phase == 2 || phase == 4) {
        const QuickStartItemChoice* choices =
            (phase == 0) ? sQuickStartStarterItems : (phase == 2) ? sQuickStartBonusItems : sQuickStartSkillItems;
        QuickStartRefreshItemTimers();
        if (QuickStartAnyPickedUp(choices)) {
            // Bombs/bow/boomerang and the heart/rupee/potion row both show a
            // proper "You got/swapped for the X!" message on pickup for
            // free, via the vanilla ItemOnGround -> GiveItem cutscene path
            // (itemOnGround.c: sub_08081420/CheckShouldPlayItemGetCutscene).
            // The skill scroll row doesn't - confirmed in the emulator: the
            // very next frame after picking one up already shows Octoroks
            // for wave 1, with no message ever having appeared, unlike the
            // two earlier rows which visibly hold the textbox open and
            // block movement for a couple of seconds. ITEM_SKILL_* is the
            // one Item kind with no physical form (nothing to actually hold
            // overhead), which is almost certainly why that cutscene's
            // gRoomTransition.field_0x4[0]) waits on it - is only long
            // enough for this to be a coincidence for skills specifically.
            // Firing the message explicitly here, rather than trying to
            // coax the vanilla cutscene into cooperating, means this
            // doesn't depend on figuring out exactly why it skips itself.
            if (phase == 4) {
                s32 i;
                for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
                    u16 skillItem = sQuickStartSkillItems[i].itemId;
                    if (GetInventoryValue(skillItem) != 0) {
                        MessageRequest(TEXT_INDEX(TEXT_ITEM_GET, gItemMetaData[skillItem].textId));
                        break;
                    }
                }
            }
            gRoomTransition.field_0x4[0] = phase + 1;
        }
        return;
    }

    if (phase == 6) {
        // Wave 1 was already spawned synchronously by the phase 5 handler,
        // before it even set phase to 6 and triggered the reload - so by
        // construction the Octoroks already exist (having survived the
        // reload via ENT_PERSIST) by the time this branch is reached at all.
        // A same-frame "0 Octoroks" reading here always means they've
        // genuinely all been defeated, never that they simply haven't
        // spawned yet.
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            // Scoped to Main's own bounds (see QuickStartEntityInCurrentRoom)
            // - this function only runs while we're in Main (guard above),
            // so gRoomControls.origin/width/height already reflect Main's own
            // dimensions here. Without this, Hall's entirely unrelated
            // ambient Octoroks (QuickStartSpawnHallEnemiesOnce) would show up
            // on a bare kind/id scan and permanently block wave 1 from ever
            // reading as "cleared", even after Main's own are long dead.
            if (gEntities[i].base.kind == ENEMY && gEntities[i].base.id == OCTOROK &&
                QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                return;
            }
        }
        QuickStartSpawnWave2();
        gRoomTransition.field_0x4[0] = 7;
        return;
    }

    // Phases 7 and 8 don't go through a room reload like phase 6 did coming
    // from phase 5 - there's no player reposition or entity persistence
    // concern here, the previous wave's enemies are already gone (defeated),
    // so we can spawn the next wave directly the moment this phase is
    // reached, no idempotent "Once" gating required.
    if (phase == 7) {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            // Same Main-only bounds check as phase 6 above.
            if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                return;
            }
        }
        QuickStartSpawnWave3();
        gRoomTransition.field_0x4[0] = 8;
        return;
    }

    if (phase == 8) {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            // Same Main-only bounds check as phase 6 above.
            if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
                return;
            }
        }
        QuickStartSpawnChest();
        gRoomTransition.field_0x4[0] = 9;
        return;
    }

    if (phase == 9) {
        if (GetInventoryValue(ITEM_HEART_PIECE) != 0) {
            gRoomTransition.field_0x4[0] = 10;
        }
        return;
    }
}

static void QuickStartUpdate(void) {
    // Called every frame of GameMain_ChangeRoom - the fade-in/room-entry
    // transition, entered right as a room loads and left only once
    // gMain.substate advances to GAMEMAIN_UPDATE. QuickStartRoomMonitor
    // below is what actually deletes each custom room's pre-existing
    // vanilla entities (guards, ambient NPCs, whatever the room's own
    // static data happened to include), but until this call was added it
    // only ever ran from GameMain_Update - i.e. only once the transition
    // had already finished and at least one full frame had already been
    // drawn (DrawEntities() runs here in GameMain_ChangeRoom too) with
    // those entities still in place. That's the flash: every custom room,
    // not just Main, briefly showed its real vanilla sprites before this
    // file got a chance to clear them. Calling the same idempotent
    // monitor here too closes that window.
    QuickStartRoomMonitor();
    // Same reasoning as the guard in QuickStartUpdateItemChoice: this runs
    // during every room-entry reload, not just ones in Castor Darknut Main.
    if (gRoomControls.area != QUICKSTART_AREA || gRoomControls.room != QUICKSTART_ROOM) {
        return;
    }
    // Wave 1 used to be (re)spawned here, once per reload - moved to a
    // direct one-time call in the phase 5 handler instead (see
    // QuickStartUpdateItemChoice), so it can no longer come back to life
    // just because some later reload finds the room empty (e.g. simply
    // walking back into Main after already defeating wave 1).
    if (gRoomTransition.field_0x4[0] == 0) {
        QuickStartSpawnStarterChoiceOnce();
    }
    QuickStartUpdateItemChoice();
}
#endif

static void GameMain_ChangeRoom(void) {
    UpdateEntities();
    if (!UpdateLightLevel())
        UpdateScroll();
    UpdateBgAnimations();
    UpdateScrollVram();
    DrawUI();
    UpdateManagers();
#ifdef QUICKSTART
    QuickStartUpdate();
#endif
    FlushSprites();
    DrawUIElements();
    UpdateCarriedObject();
    DrawEntities();
    CopyOAM();

    if (gFadeControl.active || gRoomControls.reload_flags != 0)
        return;

    UpdateFakeScroll();
    if (gArea.bgm != gArea.queued_bgm) {
        gArea.bgm = gArea.queued_bgm;
        SoundReq(gArea.queued_bgm | SONG_PLAY_VOL_RESET);
    }

    DeleteSleepingEntities();

    if (sub_0805BC04())
        return;

    UpdatePlayerMapCoords();
    ClearEventPriority();
    UpdateWindcrests();
    sub_080300C4();
    gMain.substate = GAMEMAIN_UPDATE;
    SetPlayerControl(0);
    gPauseMenuOptions.disabled = 0;
#if defined(USA) || defined(DEMO_USA)
    if (gArea.unk28.textBaseIndex != 0xff) {
        sub_0801855C();
    }
    CreateMiscManager();
    CheckAreaDiscovery();
#elif defined(EU)
    CheckAreaDiscovery();
    sub_0801855C();
#elif defined(JP)
    CheckAreaDiscovery();
    if (gArea.unk28.textBaseIndex != 0xff) {
        sub_0801855C();
    }
#elif defined(DEMO_JP)
    if (gRoomTransition.field31)
        CheckAreaDiscovery();
    if (gArea.unk28.textBaseIndex != 0xff) {
        sub_0801855C();
    }
    CreateMiscManager();
#endif
    if (!gRoomVars.didEnterScrolling) {
        RequestPriorityDuration(NULL, 1);
    }
}

static void GameMain_Update(void) {
    if (CheckInitPauseMenu() || CheckInitPortal()) {
        return;
    }
    UpdateTimerCallbacks();

    // leave early if player is now entering a portal
    if (gMain.substate != GAMEMAIN_UPDATE) {
        return;
    }

    if ((gMessage.state & MESSAGE_ACTIVE) || gPriorityHandler.priority_timer != 0)
        PausePlayer();

    FlushSprites();
    UpdateEntities();
    UpdateDoorTransition();
    CollisionMain();
    UpdateScroll();
    UpdateBgAnimations();
    UpdateScrollVram();
    DecreasePortalTimer();
    DrawUI();
    UpdateManagers();
#ifdef QUICKSTART
    // GameMain_ChangeRoom's QuickStartUpdate only runs briefly during the
    // room-entry transition, before substate advances to GAMEMAIN_UPDATE -
    // long before the player would actually reach and pick up an item,
    // finish an item-get cutscene, clear combat, or open the reward chest.
    // Poll here instead, every frame during normal gameplay in this room,
    // until everything (phase 10) is done.
    if (gRoomTransition.field_0x4[0] != 10) {
        QuickStartUpdateItemChoice();
    }
    QuickStartRoomMonitor();
#endif
    DrawUIElements();
    UpdateCarriedObject();
    DrawEntities();
    CheckRoomExit();
    UpdatePlayerMapCoords();
    CheckGameOver();
    sub_080185F8();
    CopyOAM();
    switch (gRoomControls.reload_flags) {
        case RELOAD_ALL:
            gPlayerState.queued_action = PLAYER_ROOMTRANSITION;
            gMain.substate = GAMEMAIN_CHANGEROOM;
            SetRoomReloadPriority();
            sub_08051D98();
            break;
        case RELOAD_ENTITIES:
            gPlayerState.queued_action = PLAYER_ROOMTRANSITION;
            gMain.substate = GAMEMAIN_CHANGEROOM;
            SetRoomReloadPriority();
            sub_08051DCC();
            break;
    }
}

static void GameMain_BarrelUpdate(void) {
    if (CheckInitPauseMenu())
        return;

    UpdateEntities();
    CollisionMain();
    DrawUI();
    UpdateManagers();
    FlushSprites();
    DrawUIElements();
    UpdateCarriedObject();
    DrawEntities();
    CheckRoomExit();
    CheckGameOver();
    CopyOAM();
    if (!gFadeControl.active)
        ClearEventPriority();
}

static void GameMain_ChangeArea(void) {
    FlushSprites();
    DrawUIElements();
    DrawEntities();
    gMain.pad = 1;
    CopyOAM();
    if (!gFadeControl.active) {
        DispReset(1);
        gMain.state = GAMETASK_INIT;
        gMain.substate = GAMEMAIN_INITROOM;
        gRoomTransition.transitioningOut = 1;
    }
}

static void GameTask_Exit(void) {
#ifdef DEMO_USA
    if (!gFadeControl.active)
        DoSoftReset();
#else
    SetFade(FADE_IN_OUT | FADE_BLACK_WHITE | FADE_INSTANT, 8);
    SetTask(TASK_GAMEOVER);
#endif
}

// TODO End of GameTask?

static void InitializeEntities(void) {
    sub_08052EA0();
    sub_0804AF90();
    CallRoomProp6();
    InitializePlayer();
    gDiggingCaveEntranceTransition.entrance = NULL;
    InitializeCamera();
    gUpdateVisibleTiles = 1;
    LoadRoomBgm();
    SetColor(0, 0);
    LoadRoom();
    CreateZeldaFollower();
    CallRoomProp5And7();
    sub_0805329C();
    UpdateScrollVram();
    sub_0805BB74(-1);
    UpdatePlayerRoomStatus();
}

static void sub_08051D98(void) {
    sub_08052EA0();
    gRoomVars.didEnterScrolling = TRUE;

    // remove old entities, unless persistent
    RecycleEntities();

    sub_0804AF90();
    CallRoomProp6();
    LoadRoomGfx();
    LoadRoomBgm();
    LoadRoom();
    CallRoomProp5And7();
    SetPlayerControl(1);
}

static void sub_08051DCC(void) {
    gRoomControls.area = gRoomTransition.player_status.area_next;
    gRoomControls.room = gRoomTransition.player_status.room_next;
    RoomExitCallback();
    gRoomTransition.type = TRANSITION_3;
    InitRoom();
    sub_08052EA0();
    RecycleEntities();
    sub_0804AF90();
    CallRoomProp6();
    LoadRoomBgm();
}

static void UpdateWindcrests(void) {
    if (AreaIsOverworld()) {
        const OverworldLocation* location;
        u32 hi_x, hi_y;
        s32 x, y;

        x = gPlayerEntity.base.x.HALF.HI;
        if (x < 0)
            x += 0xf;
        hi_x = x >> 4;

        y = gPlayerEntity.base.y.HALF.HI;
        if (y < 0)
            y += 0xf;
        hi_y = y >> 4;

        for (location = gOverworldLocations; location->minX != 0xFF; location++) {
            if (location->minX <= hi_x && location->maxX >= hi_x && location->minY <= hi_y && location->maxY >= hi_y) {
                gSave.windcrests |= 1 << location->windcrestId;
                break;
            }
        }
    }
}
