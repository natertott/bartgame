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
#if defined(QUICKSTART) || defined(MAPEXPLORE)
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
static void QuickStartSpawnShopMerchantOnce(s16, s16);
static void QuickStartClearShopObstacles(void);
static void QuickStartMaintainShop(const s16 (*)[2]);
static void QuickStartRandomizeLaddersOnce(void);
static void QuickStartProcessLadderLinks(void);
static void QuickStartSetupLadderRoomContent(s32);
static void QuickStartEnforceContainment(void);
static void QuickStartEnforceLonLonContainment(void);
static void QuickStartSpawnLonLonRanchEnemiesOnce(void);
static void QuickStartClearLonLonRanchGoron(void);
static void QuickStartSolveLonLonBoulder(void);
static void QuickStartProcessLinks(void);
static void QuickStartRoomMonitor(void);
static u8 QuickStartGetDifficulty(void);
static void QuickStartIncrementDifficulty(void);
static void QuickStartPickEnemy(u8, u8*, u8*);
static void QuickStartSpawnEnemyGroup(const s16 (*)[2], s32, s32, s32);
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

#ifdef MAPEXPLORE
// Full main-quest inventory: every sword/shield upgrade, both bomb/bow/
// boomerang variants, every non-attack item, all 4 Elements, every sword
// skill, and the wallet/bag/quiver/kinstone-bag upgrade markers. Left out
// deliberately: one-shot pickup-effect ids (ITEM_RUPEE1, ITEM_HEART,
// ITEM_KINSTONE, ...) and QUICKSTART's own ITEM_32/33/5A markers - none of
// those are meant to be permanently "owned" inventory entries.
//
// Also deliberately NOT granted: ITEM_MAP (dungeon-map pause screen isn't
// needed for overworld mapping) and ITEM_LANTERN_ON (see below).
//
// Only ITEM_LANTERN_OFF is granted, not ITEM_LANTERN_ON - matching
// QUICKSTART's own item list. Owning both simultaneously (which a real save
// never does; they're the unlit/lit states of one item) breaks
// PauseMenu_ItemMenu_Init: agbcc compiles that function's inventory-scan
// for-loop using the loop variable `item` itself as the loop counter
// register, and the ITEM_LANTERN_OFF/ITEM_LANTERN_ON special case
// overwrites `item` mid-iteration with gPauseMenuOptions.unk15 (the sprite
// variant to draw). With only one lantern item owned this is a no-op each
// time (the overwritten value equals the value it already had), but with
// both owned, reaching item==ITEM_LANTERN_ON(16) resets the loop counter
// back down to unk15==ITEM_LANTERN_OFF(15) - the next increment lands back
// on 16, and the loop cycles 15/16 forever, never reaching item==32 and
// never calling SetMenuType(1). Confirmed via the emulator: with both
// lantern items granted, opening the pause menu spins the CPU in this loop
// forever (gMain.ticks and gFadeControl frozen, screen black, hardware
// interrupts still firing normally in the background) - exactly the freeze
// the user reported. Granting only ITEM_LANTERN_OFF avoids the whole class
// of bug.
//
// File-scope (not block-scope) - agbcc doesn't resolve enum-constant
// initializers for a static array declared inside a function body.
static const u8 sMapExploreItems[] = {
    ITEM_SMITH_SWORD,       ITEM_GREEN_SWORD,      ITEM_RED_SWORD,        ITEM_BLUE_SWORD,
    ITEM_FOURSWORD,         ITEM_BOMBS,            ITEM_REMOTE_BOMBS,     ITEM_BOW,
    ITEM_LIGHT_ARROW,       ITEM_BOOMERANG,        ITEM_MAGIC_BOOMERANG,  ITEM_SHIELD,
    ITEM_MIRROR_SHIELD,     ITEM_LANTERN_OFF,      ITEM_GUST_JAR,
    ITEM_PACCI_CANE,        ITEM_MOLE_MITTS,       ITEM_ROCS_CAPE,        ITEM_PEGASUS_BOOTS,
    ITEM_FIRE_ROD,          ITEM_OCARINA,           ITEM_BOTTLE1,          ITEM_BOTTLE2,
    ITEM_BOTTLE3,           ITEM_BOTTLE4,           ITEM_SHELLS,           ITEM_EARTH_ELEMENT,
    ITEM_FIRE_ELEMENT,      ITEM_WATER_ELEMENT,     ITEM_WIND_ELEMENT,     ITEM_GRIP_RING,
    ITEM_POWER_BRACELETS,   ITEM_FLIPPERS,          ITEM_SKILL_SPIN_ATTACK,
    ITEM_SKILL_ROLL_ATTACK, ITEM_SKILL_DASH_ATTACK, ITEM_SKILL_ROCK_BREAKER, ITEM_SKILL_SWORD_BEAM,
    ITEM_SKILL_GREAT_SPIN,  ITEM_SKILL_DOWN_THRUST, ITEM_SKILL_PERIL_BEAM, ITEM_WALLET,
    ITEM_BOMBBAG,           ITEM_LARGE_QUIVER,      ITEM_KINSTONE_BAG,     ITEM_SKILL_FAST_SPIN,
    ITEM_SKILL_FAST_SPLIT,  ITEM_SKILL_LONG_SPIN,   ITEM_QST_LONLON_KEY,   ITEM_QST_GRAVEYARD_KEY,
    ITEM_QST_TINGLE_TROPHY, ITEM_QST_CARLOV_MEDAL,
};
#endif

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
    // world (36,39) to (235,174), origin (0,0). Spawn point placed directly
    // by the user (via the room-local position Lua script, Tools/Scripting
    // in mGBA) rather than this file's own emulator survey.
    gRoomTransition.player_status.start_pos_x = 135;
    gRoomTransition.player_status.start_pos_y = 0x9b;
    gRoomTransition.player_status.layer = 1;
    // Every fresh boot is meant to be its own clean round - none of last
    // round's starter/bonus/skill choice, ladder/gauntlet reward pickups, or
    // heart pieces should carry over. Global flags (gSave.flags - the
    // difficulty counter, ladder assignments, EZERO_1ST, etc.) live in a
    // separate array and are untouched by this, but ownership itself
    // (gSave.inventory, 2 bits/item) persists across DoSoftReset same as
    // everything else in gSave - left alone, QuickStartAnyPickedUp would see
    // last round's picks as already-owned and silently skip straight past
    // the choice phases with the old loadout, which is exactly what was
    // happening. Wiping it here, before any of the fixed starting gear below
    // gets (re-)granted, is simpler and more robust than re-clearing every
    // individual item/marker (ITEM_32/33/5A, all three choice categories,
    // every ladder-room reward) by hand.
    MemClear(gSave.inventory, sizeof(gSave.inventory));
    gSave.stats.heartPieces = 0;
    gSave.stats.maxHealth = 40;
    gSave.stats.health = gSave.stats.maxHealth;
    gSave.stats.equipped[SLOT_A] = ITEM_SHIELD;
    gSave.stats.equipped[SLOT_B] = ITEM_SMITH_SWORD;
    // L/Select item slots - start empty like a fresh save, same as every
    // other piece of starting gear reset just above.
    gSave.stats.equippedExtra[0] = ITEM_NONE;
    gSave.stats.equippedExtra[1] = ITEM_NONE;
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
    // Lon Lon Ranch house key, granted at boot per the user's request ("Link
    // should start the game with the Lon Lon ranch house key already in his
    // inventory"). Note this doesn't actually gate anything under
    // QUICKSTART: the only place this item is ever read is talon.c's own
    // dialogue script (whether Talon offers his "you found my key" cutscene
    // line), and Talon himself is deleted from the ranch house along with
    // every other vanilla NPC/object the moment it's repurposed as a "?
    // room" (QuickStartClearLadderRoomObstacles) - it's granted purely so
    // the save's inventory state matches what the player was told, with no
    // functional door-gating effect either way.
    SetInventoryValue(ITEM_QST_LONLON_KEY, 1);
    // Fuses the Lon Lon Ranch kinstone piece at boot. In vanilla,
    // sub_StateChange_HyruleField_LonLonRanch (roomInit.c) only loads the
    // wall-punching Goron's entity list (and draws the wall-crack tiles at
    // local (128,864)/(128,880)) while !CheckKinstoneFused(KINSTONE_29) -
    // pre-fusing it here means that never happens, so the Goron and its
    // crack are simply never there, and the cave entrance behind it (the
    // real door at local (136,852), gExitList_HyruleField_LonLonRanch[4])
    // is open from the start. See QuickStartClearLonLonRanchGoron below for
    // a defensive backstop in case any of that understanding is incomplete.
    WriteBit(&gSave.kinstones.fusedKinstones, KINSTONE_29);
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
#elif defined(MAPEXPLORE)
    // Dev-only: boot into MAPEXPLORE_AREA/MAPEXPLORE_ROOM (South Hyrule
    // Field by default, right outside Hyrule Castle Town's south gate) with
    // the entire main quest done except the Vaati fight, for walking the
    // full overworld and recording entrance/exit/enemy-spawn coordinates.
    //
    // NOT spawned directly in town itself (AREA_HYRULE_TOWN):
    // confirmed in the emulator that opening the pause menu after a direct
    // boot-spawn into Hyrule Town Main freezes with a black screen -
    // gArea.dungeon_idx reads as 243 there (computed from per-area ROM
    // metadata as `location - 23`, which underflows for any non-dungeon
    // area), and PauseMenu_Screen_5 unconditionally calls
    // DrawDungeonMapActually(), which indexes gDungeonFloorMetadatas/
    // gSave.dungeonItems by that same out-of-bounds dungeon_idx with no
    // bounds check - reading whatever happens to sit there in EWRAM (hence
    // the freeze being intermittent/build-layout-sensitive rather than
    // deterministic). Reproduced this with the existing, already-proven
    // QUICKSTART spawn-override mechanism pointed at Hyrule Town too (not
    // anything specific to this build's own item/flag setup), and confirmed
    // the pause menu opens fine from an ordinary overworld field room
    // instead. Spawning in South Hyrule Field sidesteps the whole class of
    // bug: the player just walks a few steps north through the real town
    // gate themselves, a genuine transition rather than a boot override,
    // which does not carry this problem.
    gRoomTransition.player_status.area_next = MAPEXPLORE_AREA;
    gRoomTransition.player_status.room_next = MAPEXPLORE_ROOM;
    gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
    gRoomTransition.player_status.start_pos_x = 504;
    gRoomTransition.player_status.start_pos_y = 872;
    gRoomTransition.player_status.layer = 1;

    // Max out hearts, rupees, bombs, arrows, shells, and every wallet/bag/
    // quiver upgrade.
    gSave.stats.heartPieces = 0;
    gSave.stats.maxHealth = 0xA0; // 40 hearts - script.c's own cap (min(+8, 0xA0))
    gSave.stats.health = gSave.stats.maxHealth;
    gSave.stats.walletType = 3; // gWalletSizes[3] == 999 (itemUtils.c)
    gSave.stats.rupees = 999;
    gSave.stats.bombBagType = 3; // gBombBagSizes[3] == 99
    gSave.stats.bombCount = 99;
    gSave.stats.quiverType = 3; // gQuiverSizes[3] == 99
    gSave.stats.arrowCount = 99;
    gSave.stats.shells = 9999;

    // Full main-quest inventory: see sMapExploreItems above.
    {
        s32 i;
        for (i = 0; i < ARRAY_COUNT(sMapExploreItems); i++) {
            SetInventoryValue(sMapExploreItems[i], 1);
        }
    }
    gSave.stats.bottles[0] = ITEM_BOTTLE_RED_POTION;
    gSave.stats.bottles[1] = ITEM_BOTTLE_RED_POTION;
    gSave.stats.bottles[2] = ITEM_BOTTLE_RED_POTION;
    gSave.stats.bottles[3] = ITEM_BOTTLE_RED_POTION;

    // Best-in-slot equip loadout: Four Sword + Mirror Shield on A/B, Pegasus
    // Boots + Roc's Cape on the L/Select slots (fast travel + gap-jumping -
    // the two most useful for covering ground while mapping the overworld).
    gSave.stats.equipped[SLOT_A] = ITEM_MIRROR_SHIELD;
    gSave.stats.equipped[SLOT_B] = ITEM_FOURSWORD;
    gSave.stats.equippedExtra[0] = ITEM_PEGASUS_BOOTS;
    gSave.stats.equippedExtra[1] = ITEM_ROCS_CAPE;

    // Every dungeon's small/big key count and compass/map/big-key bits, all
    // area-visit flags (skip first-visit cutscenes/triggers anywhere), and
    // the upper Windcrest-visited byte (see the field comment in save.h).
    {
        s32 i;
        for (i = 0; i < 0x10; i++) {
            gSave.dungeonKeys[i] = 9;
            gSave.dungeonItems[i] = 7; // 4:compass 2:bigkey 1:smallkey
        }
        for (i = 0; i < 8; i++) {
            gSave.areaVisitFlags[i] = 0xFFFFFFFF;
        }
    }
    gSave.windcrests |= 0xFF000000;

    // All 100 Kinstone fusions - this is what actually flips the overworld
    // into its fully-fused late-game appearance (roomInit.c gates dozens of
    // bridges/NPCs/obstacles on CheckKinstoneFused). fusedCount/didAllFusions
    // are only the Kinstone-menu "100/100" completion marker; fuserProgress/
    // fuserOffers are set to KINSTONE_FUSER_DONE so no fuser NPC still has an
    // offer pending.
    {
        s32 i;
        for (i = 1; i <= KINSTONE_64; i++) {
            WriteBit(&gSave.kinstones.fusedKinstones, i);
        }
        for (i = 0; i < 128; i++) {
            gSave.kinstones.fuserProgress[i] = KINSTONE_FUSER_DONE;
            gSave.kinstones.fuserOffers[i] = KINSTONE_FUSER_DONE;
        }
    }
    gSave.kinstones.fusedCount = 100;
    gSave.kinstones.didAllFusions = 1;
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
#elif defined(MAPEXPLORE)
    // Every dungeon-clear/boss-die flag plus the full Elemental Sanctuary
    // sequence (SEIIKI_STAINED_GLASS is what UpdateGlobalProgress reads for
    // its max value, 9 - "everything done, ready for Vaati") and the
    // handful of other main-quest story flags read elsewhere in the
    // overworld. Placed after ResetTmpFlags(), same reason QUICKSTART's own
    // LV1_CLEAR above is: that call unconditionally re-derives LV1/2/4_CLEAR
    // from real Element ownership, so setting these any earlier would get
    // clobbered (the Elements are already granted above, so this isn't
    // strictly necessary here, but matches the established pattern).
    //
    // Deliberately NOT set: ENDING ("Vaati's wrath defeated"), GAMECLEAR
    // ("watched end cutscene"), or LV6_SOTO_ENDING/LV6_CLEAR (Dark Hyrule
    // Castle has no simple "clear" flag - reaching and beating Vaati IS that
    // dungeon's completion) - the whole point of this build is stopping
    // just short of the Vaati fight itself.
    SetGlobalFlag(LV1_CLEAR);
    SetGlobalFlag(LV2_CLEAR);
    SetGlobalFlag(LV3_CLEAR);
    SetGlobalFlag(LV4_CLEAR);
    SetGlobalFlag(LV5_CLEAR);
    SetGlobalFlag(EZERO_1ST);
    SetGlobalFlag(WHITE_SWORD_END);
    SetGlobalFlag(KAKERA_COMPLETE);
    ClearGlobalFlag(ZELDA_CHASE);
    // Talked to Daltus and Smith - without this, South Hyrule Field's own
    // room-init function (sub_StateChange_HyruleField_SouthHyruleField,
    // roomInit.c) queues the pre-game BGM_FESTIVAL_APPROACH music, since it
    // still thinks we're in the "walking to the festival for the first
    // time" opening state.
    SetGlobalFlag(TABIDACHI);
    // "Zelda enters Town in South Hyrule Field" - without this, that same
    // room-init function treats this as the very first visit and loads the
    // game's actual opening-cutscene entity list (gUnk_080F70A8: Zelda and
    // the Master Smith escorting Link to the festival) on top of our spawn
    // point, and unconditionally re-clears ZELDA_CHASE right along with it.
    // That cutscene immediately pans gRoomControls.camera_target to one of
    // those NPCs and never hands it back (the scripted walk-to-the-castle
    // sequence has nowhere sensible to go from a boot-spawn instead of a
    // real new-game intro), which is what actually caused the "no Link
    // sprite" bug the user reported - Link's entity was there the whole
    // time, just permanently off-screen because the camera had latched onto
    // the intro NPC instead. Confirmed via the emulator: gRoomControls.
    // camera_target pointed at one of that entity list's NPCs, not
    // &gPlayerEntity.base, and the player's own local (room-relative)
    // position was correct the whole time. Setting this flag stops that
    // entity list (and the whole opening scene) from loading at all.
    SetLocalFlagByBank(FLAG_BANK_1, SOUGEN_01_ZELDA);
    SetLocalFlagByBank(FLAG_BANK_1, SOUGEN_08_TORITSUKI);
    SetLocalFlagByBank(FLAG_BANK_3, OUBO_KAKERA);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_ENTER);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_SWORD_1ST);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_SWORD_2ND);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_SWORD_3RD);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_BUNSHIN);
    SetLocalFlagByBank(FLAG_BANK_3, SEIIKI_STAINED_GLASS);
    SetLocalFlagByBank(FLAG_BANK_7, LV3_16_BOSSDIE);
    SetLocalFlagByBank(FLAG_BANK_8, LV4_10_BOSSDIE);
    SetLocalFlagByBank(FLAG_BANK_9, LV5_BOSSDIE);
    SetLocalFlagByBank(FLAG_BANK_9, LV5_MBOSSDIE);
    gSave.global_progress = 9;
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
// exact spot it was placed (room-local offset) - and if so, refreshes its
// own despawn timer. Used to tell "the player picked it up" apart from
// "the room got unloaded before they picked it up" for a reward drop -
// Castle Garden, Melari's Mine, and the ladder "? room" chest/mini-boss
// rewards all use this exact pattern, and all of them need the refresh:
// left untouched, the item silently vanishes on its default ~10-second
// ground-item timer, often before a real player can realistically fight
// through to it (confirmed in the emulator for Castle Garden's own
// reward, behind a 19-enemy gauntlet) - and that disappearance then reads
// as a genuine pickup the very next frame, permanently marking the
// reward collected even though nothing was ever actually handed over.
static bool32 QuickStartGroundItemAt(s16 offsetX, s16 offsetY) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM && QuickStartEntityInCurrentRoom(ent) &&
            ent->x.HALF.HI - gRoomControls.origin_x == offsetX && ent->y.HALF.HI - gRoomControls.origin_y == offsetY) {
            ((ItemOnGroundEntity*)ent)->unk_6c = 600;
            return TRUE;
        }
    }
    return FALSE;
}

// Castor Darknut Main's safe walkable box (world (36,39)-(235,174), origin
// (0,0)) is ~199x135px -> 24 32x32 squares. The original 9 hand-verified
// spots (3 from the old wave1, 4 from wave2, 2 from wave3) plus 26 more
// found the same way (a full room collision-data scan for open 3x3-tile
// neighborhoods, then an in-emulator movement check on every candidate) -
// comfortably more than the ~5 the density curve ever asks for here, with
// room to spare for variety across boots. Shared by all 3 combat waves
// since they run in the same room, never simultaneously.
#define QUICKSTART_MAIN_ROOM_SQUARES 24
static const s16 sQuickStartMainEnemyOffsets[35][2] = {
    { 0x6e, 0x87 },  { 0x96, 0x87 },  { 0xbe, 0x87 },  { 0x5a, 0x60 },  { 0x82, 0x9c },  { 0xaa, 0x60 },
    { 0xd2, 0x9c },  { 0x6e, 0x60 },  { 0xbe, 0x60 },  { 48, 51 },      { 72, 51 },      { 96, 51 },
    { 120, 51 },     { 144, 51 },     { 168, 51 },     { 192, 51 },     { 216, 51 },     { 48, 75 },
    { 72, 75 },      { 96, 75 },      { 120, 75 },     { 144, 75 },     { 168, 75 },     { 192, 75 },
    { 216, 75 },     { 48, 99 },      { 216, 99 },     { 72, 111 },     { 156, 111 },    { 48, 123 },
    { 216, 123 },    { 72, 135 },     { 48, 147 },     { 168, 147 },    { 96, 159 },
};

static void QuickStartSpawnEnemies(void) {
    QuickStartSpawnEnemyGroup(sQuickStartMainEnemyOffsets, ARRAY_COUNT(sQuickStartMainEnemyOffsets),
                               QUICKSTART_MAIN_ROOM_SQUARES, QUICKSTART_MAIN_ROOM_SQUARES);
}

// Wave 2: same room, same pool, just rolled independently - the density
// curve (not a fixed "more than wave 1" rule) decides how many show up.
static void QuickStartSpawnWave2(void) {
    QuickStartSpawnEnemyGroup(sQuickStartMainEnemyOffsets, ARRAY_COUNT(sQuickStartMainEnemyOffsets),
                               QUICKSTART_MAIN_ROOM_SQUARES, QUICKSTART_MAIN_ROOM_SQUARES);
}

// Wave 3: the climactic wave - regular enemies from the same pool, plus a
// real Darknut as a fixed mini-boss (mini-bosses sit outside the 5-level
// difficulty system entirely, per the brief - always exactly 1). This room
// is Castor Darknut Main, the Darknut's own vanilla arena (see
// object/bossDoor.c and object/cutsceneOrchestrator.c), so its sprite
// assets are already loaded here regardless of our own cutscene removal.
static void QuickStartSpawnWave3(void) {
    Entity* enemy;
    QuickStartSpawnEnemyGroup(sQuickStartMainEnemyOffsets, ARRAY_COUNT(sQuickStartMainEnemyOffsets),
                               QUICKSTART_MAIN_ROOM_SQUARES, QUICKSTART_MAIN_ROOM_SQUARES);
    enemy = CreateEnemy(DARK_NUT, 0);
    if (enemy != NULL) {
        enemy->x.HALF.HI = gRoomControls.origin_x + 0x96;
        enemy->y.HALF.HI = gRoomControls.origin_y + 0x9c;
        enemy->collisionLayer = 1;
        enemy->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(enemy);
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
// Hall's own verified-safe width is local x [70,420] at y~94 (see file
// header comment above) -> ~350x32px -> ~10 32x32 squares.
#define QUICKSTART_HALL_ROOM_SQUARES 10
#define QUICKSTART_HALL_MAX_ENEMIES 4
static void QuickStartSpawnHallEnemiesOnce(void) {
    static const s16 sQuickStartHallEnemyOffsets[4][2] = {
        { 0x96, 0x5e }, { 0xfa, 0x5e }, { 0x15e, 0x5e }, { 0x19a, 0x5e },
    };
    if (gRoomTransition.field_0x4[0] != 10) {
        return;
    }
    if (GetInventoryValue(ITEM_33) != 0) {
        return;
    }
    QuickStartSpawnEnemyGroup(sQuickStartHallEnemyOffsets, ARRAY_COUNT(sQuickStartHallEnemyOffsets),
                               QUICKSTART_HALL_ROOM_SQUARES, QUICKSTART_HALL_MAX_ENEMIES);
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
// Castle Garden is 1008x528px -> 31x16 -> 496 32x32 squares. The original
// 19 hand-verified spots plus 46 more found the same way (a full room
// collision-data scan for open 3x3-tile neighborhoods, then an in-emulator
// movement check on every candidate) - not enough to ever literally reach
// the density curve's nominal "1 per 5 squares" (496/5 = ~99), but that
// ratio was never reachable here regardless of how many spots get
// verified: MAX_ENTITIES (entity.h) caps the entire room - player,
// decorations, reward item, everything - at 72 entities total, and this
// room's own overhead (player + decorations) already used ~7 of those
// before a single enemy spawns. QUICKSTART_GARDEN_MAX_ENEMIES is that
// real, measured ceiling (with a safety margin for the reward item and
// anything else sharing the room) - the density formula's own count gets
// clamped to it, same as it's clamped to the offset pool size.
#define QUICKSTART_GARDEN_ROOM_SQUARES 496
#define QUICKSTART_GARDEN_MAX_ENEMIES 50
static const s16 sQuickStartGardenEnemyOffsets[65][2] = {
    { 0xc8, 0x96 },  { 0x15e, 0x96 },  { 0x1f4, 0x96 },  { 0x28a, 0x96 },  { 0x320, 0x96 },
    { 0xb4, 0xd2 },  { 0x186, 0xe6 },  { 0x1f4, 0xe6 },  { 0x262, 0xe6 },  { 0x320, 0xe6 },
    { 0x118, 0x10e }, { 0x15e, 0x136 }, { 0x1f4, 0x136 }, { 0x28a, 0x136 }, { 0x320, 0x136 },
    { 0x118, 0x17c }, { 0x15e, 0x17c }, { 0x1f4, 0x17c }, { 0x28a, 0x17c },
    { 232, 72 },  { 776, 72 },  { 168, 88 },  { 424, 104 }, { 456, 104 }, { 536, 104 }, { 568, 104 },
    { 168, 120 }, { 232, 136 }, { 264, 136 }, { 424, 136 }, { 456, 136 }, { 536, 136 }, { 568, 136 },
    { 728, 136 }, { 760, 136 }, { 424, 168 }, { 456, 168 }, { 520, 168 }, { 552, 168 }, { 584, 168 },
    { 488, 184 }, { 424, 200 }, { 456, 200 }, { 520, 200 }, { 552, 200 }, { 584, 200 }, { 248, 280 },
    { 520, 328 }, { 776, 328 }, { 488, 344 }, { 520, 360 }, { 488, 408 }, { 520, 408 }, { 376, 424 },
    { 616, 424 }, { 488, 440 }, { 520, 440 }, { 376, 456 }, { 616, 456 }, { 328, 488 }, { 360, 488 },
    { 392, 488 }, { 616, 488 }, { 648, 488 }, { 680, 488 },
};

static void QuickStartSpawnGardenEnemiesOnce(void) {
    if (GetInventoryValue(ITEM_32) != 0) {
        return;
    }
    if (CheckRoomFlag(0)) {
        return;
    }
    QuickStartSpawnEnemyGroup(sQuickStartGardenEnemyOffsets, ARRAY_COUNT(sQuickStartGardenEnemyOffsets),
                               QUICKSTART_GARDEN_ROOM_SQUARES, QUICKSTART_GARDEN_MAX_ENEMIES);
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
// door onward, in Lon Lon Ranch (world (392,264), verified walkable the
// same way as its enemy pool below). Picking it up ends the round. Only
// spawns once every Lon Lon Ranch enemy is dead - same "wait for a clear
// room" gate Castle Garden's own gauntlet reward uses.
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
        itemEntity->x.HALF.HI = gRoomControls.origin_x + 392;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + 159;
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
// MsgInit (message.c) isn't declared in message.h - it's only ever reached
// there through gMessageFunctions[], the per-frame message state machine's
// own dispatch table - but it's a plain non-static function, so it's still
// a real linkable symbol. Calling it directly lets this synchronously force
// the "resolve gMessage.textIndex into gTextRender.curToken" step to happen
// immediately, in the same frame as the call below that then overwrites
// curToken with this file's own custom text - rather than waiting a frame
// for the normal MessageMain() (main.c) to reach it on its own, which would
// mean a real (if numerically meaningless) vanilla string gets resolved
// into curToken and is at risk of starting to render before this file ever
// gets a chance to replace it.
extern u32 MsgInit(void);

// "You win! Difficulty\nincreased to level X." - authored directly as a
// plain C string rather than through the usual .string/charmap asset
// pipeline (data/const/text.s and friends): that pipeline only extracts
// bytes that already exist in the base ROM (assets/gfx.json-style byte
// ranges) and has never been used in this project to author brand new
// text, and doing so would also mean adding a new object file's sections
// into linker.ld by hand, which lays out this ROM's memory to match the
// original exactly. A plain string literal sidesteps both: C already
// emits standard ASCII bytes per character, which cross-checked exactly
// against this engine's own real behavior (NumberToAscii, message.c,
// builds digits as '0' | digit - i.e. real ASCII - and this file's
// existing skill-pickup message already renders real letters correctly
// via the normal TEXT_INDEX path), and \x06\x01 is this engine's own
// control code for "insert numeric variable 1 here" (charmap.txt:
// STR_VAR_1 = 06 01), substituted from gMessage.rupees at render time -
// same mechanism the shop's price prompt already uses. \n is charmap's
// '\n' = 0A, this engine's own real line-break control code. The
// terminator is C's own implicit trailing '\0', which is also this
// engine's own "end of text" byte (charmap.txt: '$' = 00).
static const u8 sQuickStartWinMessage[] = "You win! Difficulty\nincreased to level \x06\x01.";

// Room flag 1 (Lon Lon Ranch's flag 0 is already claimed by
// QuickStartSpawnLonLonRanchEnemiesOnce) tracks "message already shown"
// across the few frames it's up, the same idempotent-per-frame-check
// pattern this whole file already uses elsewhere - a plain mutable static
// local doesn't work in this build: agbcc emits it into .data, and this
// ROM's linker.ld doesn't map src/game.o's .data section at all (every
// other piece of writable per-visit state in this file already goes
// through room/global flags or gSave fields for the same underlying
// reason, not just for the reset-on-reload semantics).
static void QuickStartCheckWinCondition(void) {
    if (GetInventoryValue(ITEM_QST_GRAVEYARD_KEY) == 0) {
        ClearRoomFlag(1);
        return;
    }
    if (!CheckRoomFlag(1)) {
        QuickStartIncrementDifficulty();
        // A deliberately out-of-range category (any real one only goes up
        // to TEXT_CAFE) so MessageRequest's own resolution step - forced to
        // run immediately by MsgInit below - safely falls back to the
        // engine's own "invalid index" placeholder instead of a real
        // string with real side effects, before this file's own text
        // replaces it a few lines down.
        MessageRequest(TEXT_INDEX(0xff, 0));
        // MessageRequest above MemClears the whole gMessage struct, so
        // rupees has to be set after it, not before - confirmed in the
        // emulator: setting it first always showed "level 0" regardless of
        // the real difficulty, since MessageRequest was silently wiping it
        // back out before MsgInit ever read it.
        gMessage.rupees = QuickStartGetDifficulty();
        MsgInit();
        gTextRender.curToken.buf[0] = sQuickStartWinMessage;
        gTextRender.curToken.unk01 = 0;
        gTextRender.curToken.unk00 = 1;
        SetRoomFlag(1);
        return;
    }
    if (gMessage.state & MESSAGE_ACTIVE) {
        return;
    }
    // Cleared here, not in the branch above - clearing it the instant the
    // win message starts made GetInventoryValue(...) == 0 true again on
    // the very next frame, before the message ever finished or this
    // function ever reached DoSoftReset below: that early-returned via the
    // very first check above, wiping room flag 1's "message already
    // shown" bookkeeping and abandoning the win sequence entirely - and
    // QuickStartSpawnWinKeyOnce, seeing the same now-zeroed value, would
    // immediately drop a fresh key, which is exactly the infinite
    // pickup/message loop this was confirmed causing. Cleared here instead
    // so it only happens once, right before the save that's supposed to
    // record it, not mid-message.
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
    // AREA_12x12 -> box +6/+6), which is now retargeted (under #ifdef
    // QUICKSTART, transitions.c) to the exact same destination as this
    // link - that real door's own position is this trigger box, and it was
    // found winning the race against this link in practice (landing the
    // player in the old vanilla destination, Castor Caves, instead), so
    // both now agree regardless of which one actually fires. Landing spot
    // (120,120), well clear of the OTHER direction's own trigger box below
    // (108-126,50-62 in Melari's Mine) - (120,65), tried first, turned out
    // to still be caught by a slow passive drift toward that box (confirmed
    // in the emulator: spawning as close as (120,82) stays put for ~100
    // frames, then drifts north several px per frame with zero input,
    // eventually crossing into the box and bouncing straight back to Hall -
    // an infinite loop the user reported). (120,120) sits well outside the
    // whole drift-affected range (confirmed stable over 300+ idle frames,
    // walkable in all 4 directions).
    { AREA_CASTOR_DARKNUT, ROOM_CASTOR_DARKNUT_HALL, 0x188, 0x18e, 0x18, 0x1e, AREA_MELARIS_MINE,
      ROOM_MELARIS_MINE_MAIN, 120, 120 },
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
    // the actual walkable corner. This same real door was found winning
    // the race against this link too (landing in Crenel Minish Paths
    // instead of Hall), so it's now retargeted the same way as Hall's own
    // door above - transitions.c, gExitList_MelarisMine_Main[0].
    // Landing spot placed by the user directly (Lua position script) at
    // (119,74), facing down - confirmed open and walkable in all 4
    // directions (see the IdleSouth start_anim special-case in
    // QuickStartProcessLinks below for the facing).
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x6c, 0x7e, 0x32, 0x3e, AREA_CASTOR_DARKNUT,
      ROOM_CASTOR_DARKNUT_HALL, 119, 74 },
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
    // Melari's Mine's two remaining real doors (Minish House Interiors -
    // Southeast, East), opened for future NPCs. Each trigger box is that
    // door's own real coordinates (gExitList_MelarisMine_Main[3], [4]
    // respectively, both AREA_12x12 -> box +6/+6); each interior room's own
    // return trip uses its single real exit (a WARP_TYPE_BORDER, retargeted
    // in transitions.c) rather than a table row here, same reasoning as
    // Castle Garden's south border - it already reliably fires without
    // needing GetActTileAtTilePos. Both interior rooms are small,
    // single-screen, and confirmed reachable from Melari's Mine's existing
    // walkable network (each door's immediate approach connects back to
    // already-verified ground within a few hundred frames of walking).
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x228, 0x22e, 0x220, 0x226, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST, 0x78, 0x64 },
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x280, 0x286, 0x11c, 0x122, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST, 0x78, 0x64 },
    // Melari's Mine's former Southwest door -> the merchant's new room
    // (Dojos "Grimblade", see QuickStartSpawnShopMerchantOnce) rather
    // than the old cramped Minish House Interiors room. Same trigger box as
    // that room used (the door's own real coordinates,
    // gExitList_MelarisMine_Main[2], AREA_12x12 -> box +6/+6) - the physical
    // spot in Melari's Mine the player already knows to go to for the shop
    // doesn't change, only where it leads. Lands at (119,170), facing up,
    // per the user's own request (see the IdleNorth start_anim
    // special-case in QuickStartProcessLinks below for the facing) - this
    // real door is also retargeted the same way (transitions.c,
    // gExitList_MelarisMine_Main[2]), since it was found winning the race
    // against this link in practice.
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0xa8, 0xae, 0x220, 0x226, AREA_DOJOS, ROOM_DOJOS_GRIMBLADE, 119,
      170 },
    // Grimblade -> back to Melari's Mine. Trigger box centered on (119,185),
    // placed by the user directly (Lua position script). Lands at
    // (168,525), the exact spot this room's real (retargeted) border exit
    // used to return to before the merchant moved here - reusing it keeps
    // both paths back into Melari's Mine consistent with each other.
    { AREA_DOJOS, ROOM_DOJOS_GRIMBLADE, 103, 135, 177, 193, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 168, 525 },
    // Castle Garden's real north door (gExitList_CastleGarden_Main[0]) is a
    // WARP_TYPE_AREA door - left un-retargeted (transitions.c) for the same
    // ACT_TILE reason documented above, so this is a position box instead,
    // covering the door's own visual footprint (local (504,40), where the
    // player is actually seen walking up between the castle's entrance
    // pillars) rather than depending on it. Lands just past the entrance
    // of Lon Lon Ranch, offset south of that room's own return-trip box
    // below so arriving here doesn't immediately re-trigger it.
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 488, 520, 16, 56, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      344, 870 },
    // Lon Lon Ranch -> back to Castle Garden. Trigger box centered on
    // (315,975), placed by the user directly (Lua position script).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 287, 343, 966, 984, AREA_CASTLE_GARDEN,
      ROOM_CASTLE_GARDEN_MAIN, 504, 120 },
    // Lon Lon Ranch -> Talon and Malon's house (west room, the one with the
    // beds), front door. Trigger box centered on (345,651), placed by the
    // user directly (Lua position script) - close to the real vanilla
    // door's own position (344,632), which this file's own emulator survey
    // had previously found unreachable without shrinking.
    //
    // Landing spot moved from (104,88) to (72,120) (the room's own OLD
    // content position, before the user asked to move that content to
    // (110,92)): (104,88) turned out to be the exact same 16x16 tile as
    // the new content spot, so the reward's collision turning on (~13
    // frames after spawn) immediately contacted the still-standing player
    // and auto-collected it with no discovery moment at all - the same
    // "dropped directly on the spawn tile" failure mode already documented
    // on sQuickStartQuestionRoomPool above, just not caught here since this
    // room's content position didn't come from that pool. Confirmed via a
    // frame-by-frame emulator trace: the reward entity was disappearing
    // ~20 frames after creation even though its own despawn timer
    // (unk_6c) stayed pinned at 600 the whole time - it wasn't vanishing,
    // it was being picked up. (72,120) is well clear of (110,92) (open
    // floor per a live collision-grid dump, confirmed stable over 300
    // idle frames and walkable).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 329, 361, 643, 659, AREA_HOUSE_INTERIORS_4,
      ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST, 72, 120 },
    // Lon Lon Ranch -> Talon and Malon's house, EAST room. Trigger box
    // centered on (392,635), placed by the user directly (Lua position
    // script) - matches the real vanilla door's own position almost
    // exactly (gExitList_HyruleField_LonLonRanch[1]: local (392,632),
    // WARP_TYPE_AREA -> AREA_HOUSE_INTERIORS_4/ROOM_HOUSE_INTERIORS_4_
    // RANCH_HOUSE_EAST). A previous round of this file wrongly sent this
    // to the WEST room's own second south-wall gap instead - that gap is
    // the Minish-only crack, not a real regular-Link door, and had nothing
    // to do with the east room at all. Lands at (120,120), the same spot
    // the real (also-unreliable-under-QUICKSTART) vanilla door itself
    // targets.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 376, 408, 627, 643, AREA_HOUSE_INTERIORS_4,
      ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST, 120, 120 },
    // Ranch house West and East no longer have their own custom exit link,
    // or a custom West<->East connector - West is a "? room" (see
    // sQuickStartFixedRoomContentPos and QuickStartRoomMonitor below) and
    // East is the merchant's second shop location, but both leave the house
    // via their own real WARP_TYPE_BORDER exit (retargeted in transitions.c
    // for West) since border-type transitions - unlike the WARP_TYPE_AREA
    // entrance doors above - don't depend on the undecompiled per-tile
    // ACT_TILE check, and fire correctly under QUICKSTART with sustained
    // holding against the wall (confirmed in the emulator this session for
    // both rooms and several others). West's real border exit is
    // retargeted to (345,710) in transitions.c, clear of the front-door
    // entrance box above (landing on that box's own center used to
    // instantly bounce the player back inside); East's is left at its
    // untouched vanilla spot, already confirmed to fire correctly on its
    // own.
    //
    // Lon Lon Ranch's Goron Cave door itself (the real vanilla door the
    // wall-punching Goron used to block - see the KINSTONE_29 fuse in
    // GameTask_Transition above) is NOT wired up here - it leads to a
    // random "? room" pool draw now (ladder slot 3), same as Castle
    // Garden's two ladders, so its destination varies per save and can't be
    // a static entry in this table. See sQuickStartLadderEntrances below
    // instead, which (like QuickStartProcessLadderLinks) resolves the
    // target at the moment the trigger fires.
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

// Melari's Mine is 720x624px -> 22x19 -> 418 32x32 squares. Unlike Castle
// Garden's hedge maze, most of this room's own bounding box is solid rock
// rather than open floor with occasional obstacles - a blind grid mostly
// landed inside walls. The original 16 hand-verified spots plus 46 more
// found via a collision-data scan + in-emulator movement check (same
// method as Castle Garden's expansion) still can't literally reach the
// density curve's "1 per 5 squares" (418/5 = ~84) - same MAX_ENTITIES
// (entity.h) ceiling as Castle Garden applies here too, and this room's
// own overhead (player + decorations) measured at ~16 entities before any
// enemy spawns. QUICKSTART_MINE_MAX_ENEMIES is the real, measured ceiling
// with a safety margin, same role as Castle Garden's cap above.
#define QUICKSTART_MINE_ROOM_SQUARES 418
#define QUICKSTART_MINE_MAX_ENEMIES 40
static const s16 sQuickStartMineEnemyOffsets[62][2] = {
    { 0xfa, 0x56 },  { 0x14a, 0x56 },  { 0x19a, 0x56 },  { 0x1ea, 0x56 },  { 0x23a, 0x56 },
    { 0x96, 0x1cc }, { 0xfa, 0x1cc },  { 0x226, 0x1cc }, { 0x100, 0x100 }, { 0x193, 0x14e },
    { 0xe4, 0x137 }, { 0x15e, 0x12c }, { 0x258, 0x15e }, { 0x96, 0x15e },  { 0x17c, 0x10e },
    { 0x140, 0x17c },
    { 88, 88 },   { 120, 88 },  { 152, 88 },  { 184, 88 },  { 216, 88 },  { 360, 88 },  { 520, 88 },
    { 600, 88 },  { 632, 88 },  { 552, 104 }, { 584, 120 }, { 616, 120 }, { 568, 200 }, { 216, 232 },
    { 584, 232 }, { 584, 264 }, { 152, 280 }, { 584, 296 }, { 328, 312 }, { 376, 312 }, { 168, 328 },
    { 584, 328 }, { 152, 376 }, { 584, 376 }, { 584, 408 }, { 584, 440 }, { 120, 472 }, { 184, 472 },
    { 216, 472 }, { 584, 472 }, { 152, 488 }, { 248, 488 }, { 280, 488 }, { 312, 488 }, { 344, 488 },
    { 376, 488 }, { 408, 488 }, { 440, 488 }, { 472, 488 }, { 504, 488 }, { 536, 488 }, { 120, 504 },
    { 184, 504 }, { 216, 504 }, { 568, 504 }, { 600, 504 },
};

static void QuickStartSpawnMelarisMineEnemiesOnce(void) {
    if (GetInventoryValue(ITEM_5A) != 0) {
        return;
    }
    if (CheckRoomFlag(1)) {
        return;
    }
    QuickStartSpawnEnemyGroup(sQuickStartMineEnemyOffsets, ARRAY_COUNT(sQuickStartMineEnemyOffsets),
                               QUICKSTART_MINE_ROOM_SQUARES, QUICKSTART_MINE_MAX_ENEMIES);
    SetRoomFlag(1);
}

// Lon Lon Ranch (a single room inside AREA_HYRULE_FIELD - see
// QuickStartEnforceLonLonContainment above for why the whole area isn't
// just added to QuickStartAreaContained) is 720x960px -> 22x30 -> 660
// 32x32 squares, the biggest room this loop uses yet. Same story as
// Castle Garden/Melari's Mine: MAX_ENTITIES (entity.h) caps the entire
// room - player, the ranch's own ambient animals/decorations (measured at
// ~9 entities before any enemy spawns), everything - at 72 total, so
// QUICKSTART_LONLON_MAX_ENEMIES is the real, measured ceiling with a
// safety margin, same role as the other two rooms' caps. All 50 spots
// below were found via the same method as Castle Garden's and Melari's
// Mine's expansions (a room-wide collision-data scan for open 3x3-tile
// neighborhoods, then an in-emulator movement check on every candidate),
// with the entrance from Castle Garden and the win key's own spot (see
// QuickStartSpawnWinKeyOnce) excluded.
#define QUICKSTART_LONLON_ROOM_SQUARES 660
#define QUICKSTART_LONLON_MAX_ENEMIES 50
static const s16 sQuickStartLonLonRanchEnemyOffsets[50][2] = {
    { 88, 24 },   { 168, 24 },  { 168, 56 },  { 56, 136 },  { 392, 136 }, { 24, 152 },  { 88, 152 },
    { 424, 152 }, { 56, 168 },  { 360, 168 }, { 392, 168 }, { 88, 184 },  { 296, 184 }, { 56, 200 },
    { 88, 216 },  { 56, 232 },  { 392, 232 }, { 88, 248 },  { 56, 264 },  { 88, 280 },  { 680, 280 },
    { 56, 296 },  { 184, 296 }, { 88, 312 },  { 680, 312 }, { 56, 328 },  { 88, 344 },  { 680, 344 },
    { 56, 360 },  { 88, 376 },  { 680, 376 }, { 88, 408 },  { 680, 408 }, { 56, 424 },  { 88, 440 },
    { 120, 440 }, { 520, 440 }, { 680, 440 }, { 56, 456 },  { 632, 456 }, { 88, 472 },  { 120, 472 },
    { 152, 472 }, { 520, 472 }, { 664, 472 }, { 56, 488 },  { 632, 488 }, { 88, 504 },  { 120, 504 },
    { 152, 504 },
};

// No separate "reward earned" item marker the way Castle Garden/Melari's
// Mine have (ITEM_32/ITEM_5A) - the win key itself is the reward here, and
// QuickStartSpawnWinKeyOnce already re-checks "is the room clear" fresh
// every frame on its own, so the only bookkeeping this needs is "don't
// respawn a full wave on top of one already in progress this visit."
static void QuickStartSpawnLonLonRanchEnemiesOnce(void) {
    if (CheckRoomFlag(0)) {
        return;
    }
    QuickStartSpawnEnemyGroup(sQuickStartLonLonRanchEnemyOffsets, ARRAY_COUNT(sQuickStartLonLonRanchEnemyOffsets),
                               QUICKSTART_LONLON_ROOM_SQUARES, QUICKSTART_LONLON_MAX_ENEMIES);
    SetRoomFlag(0);
}

// Defensive backstop for the KINSTONE_29 fuse-at-boot in GameTask_Transition:
// that flag is what makes sub_StateChange_HyruleField_LonLonRanch
// (roomInit.c) skip loading the wall-punching Goron's entity list in the
// first place, so this should never actually find one - but it costs
// nothing to also delete any GORON-kind NPC that turns up here regardless,
// the same idempotent per-frame backstop QuickStartClearMelarisMineObstacles
// and QuickStartClearShopObstacles already use elsewhere in this file.
static void QuickStartClearLonLonRanchGoron(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC && gEntities[i].base.id == GORON) {
            DeleteEntity(&gEntities[i].base);
        }
    }
}

typedef struct {
    s16 srcXMin;
    s16 srcXMax;
    s16 srcYMin;
    s16 srcYMax;
    s16 destX;
    s16 destY;
    u8 oldTileX;
    u8 oldTileY;
    u8 holeTileX;
    u8 holeTileY;
} QuickStartLonLonBoulder;

// Lon Lon Ranch has three PUSHABLE_ROCK entities (object.h), each resting
// one tile from its own SURFACE_HOLE act-tile - all confirmed by dumping
// the room's full act-tile grid and cross-referencing every PUSHABLE_ROCK
// entity's live position: (488,904)/tile(30,56) next to the hole at
// tile(29,56) (right by our entrance); (184,200)/tile(11,12) next to the
// hole at tile(10,12); and (216,904)/tile(13,56) next to the hole at
// tile(14,56) (this one's hole is EAST of the rock, not west - direction
// doesn't matter, only ending up centered on the hole tile does). Normally
// the player pushes each rock onto its hole; its own vanilla code
// (object/pushableRock.c: sub_0808A644) then settles it into action 3 and
// overwrites the hole's tile with SPECIAL_TILE_21 ("Boulder in Hole", a
// walkable bridge). This can't rely on the player ever pushing them
// itself, so force that same end state directly every frame - same
// idempotent per-frame pattern as QuickStartClearCastleGuards.
static const QuickStartLonLonBoulder sQuickStartLonLonBoulders[] = {
    { 448, 528, 864, 944, 472, 904, 30, 56, 29, 56 },
    { 144, 224, 160, 240, 168, 200, 11, 12, 10, 12 },
    { 176, 256, 864, 944, 232, 904, 13, 56, 14, 56 },
};

static void QuickStartSolveLonLonBoulder(void) {
    s32 i, j;
    // Each rock's source box is tight around its own starting spot only
    // (not the other two rocks' spots), so this can't drag the wrong rock
    // onto the wrong hole.
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s32 localX;
        s32 localY;
        if (ent->kind != OBJECT || ent->id != PUSHABLE_ROCK) {
            continue;
        }
        localX = ent->x.HALF.HI - gRoomControls.origin_x;
        localY = ent->y.HALF.HI - gRoomControls.origin_y;
        for (j = 0; j < ARRAY_COUNT(sQuickStartLonLonBoulders); j++) {
            const QuickStartLonLonBoulder* b = &sQuickStartLonLonBoulders[j];
            if (localX < b->srcXMin || localX > b->srcXMax || localY < b->srcYMin || localY > b->srcYMax) {
                continue;
            }
            ent->x.HALF.HI = gRoomControls.origin_x + b->destX;
            ent->y.HALF.HI = gRoomControls.origin_y + b->destY;
            ent->action = 3;
            break;
        }
    }
    // Each rock's ORIGINAL resting tile was already marked solid by its own
    // vanilla init code (object/pushableRock.c: sub_0808A644, the non-hole
    // branch) the moment the room loaded, independent of the entity itself
    // - confirmed via a live collision-grid dump showing the first rock's
    // tile still blocked after the entity was relocated. Clear each one
    // explicitly with the same TILE_TYPE_0 "fix collision only" trick
    // already used in QuickStartClearCastleGuards above.
    for (i = 0; i < ARRAY_COUNT(sQuickStartLonLonBoulders); i++) {
        const QuickStartLonLonBoulder* b = &sQuickStartLonLonBoulders[i];
        SetTileType(TILE_TYPE_0, TILE_POS(b->oldTileX, b->oldTileY), LAYER_BOTTOM);
        SetTileType(SPECIAL_TILE_21, TILE_POS(b->holeTileX, b->holeTileY), LAYER_BOTTOM);
    }
}

// One more "? room" slot (ladder index 2 - see GF_LADDER_BASE etc. above
// and QuickStartRoomMonitor below) alongside the 20-room Castle Garden
// ladder pool and the Goron Cave Stairs door's own pool draw (ladder index
// 3, see sQuickStartLadderEntrances below - that one draws its room from
// the pool like Castle Garden's ladders do, rather than being a fixed
// room): Talon and Malon's house's west room. It's a fixed room rather than
// a random draw (the player reaches it via its own dedicated
// sQuickStartLinks entrance, not a ladder), so it gets its own
// verified-walkable content spot directly here instead of going through
// sQuickStartQuestionRoomPool/contentDX/contentDY. (110,92) per the user's
// own request - confirmed stable (no drift) and walkable in the emulator.
static const s16 sQuickStartFixedRoomContentPos[1][2] = {
    { 110, 92 },
};

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

// The Swordsman's Dojo "Grimblade" arena (AREA_DOJOS,
// ROOM_DOJOS_GRIMBLADE) as the merchant's room - relocated here from the
// original Minish House Interiors "Melari's Mines Southwest" room, which
// (per its own room header, a single non-scrolling 240x160 screen with
// only ~12 standable tiles amid the furniture) was too cramped. Grimblade
// is a real one-on-one sword-duel arena: 240x192, and per a full
// collision-grid dump in the emulator its main floor (local x=32-207,
// y=96-207, tile-aligned) is one uninterrupted 11x7-tile open rectangle -
// 77 tiles with zero obstacles, dwarfing the old room's ~12. It also has
// no real exit of its own at all (gExitLists_Dojos[ROOM_DOJOS_GRIMBLADE]
// is gExitList_NoExitList - the vanilla duel ends via cutscene, not a
// walked door), so unlike every other repurposed room in this file this
// one arrives with exactly zero pre-existing exits to fight around: the
// only way in or out is the single sQuickStartLinks pair added for it
// below, a clean match for "one room, one door."
//
// The first of several planned NPCs for this loop's shops - a merchant
// selling a small fixed catalog (see script_QuickStartMerchant), using the
// exact vanilla shop mechanism (ScriptCommand_SaleItemConfirmMessage/
// CheckShopItemPrice/BuyShopItem, the same trio Beedle and Talon's own
// shops use) rather than anything custom-built. Reuses the ZELDA entity
// kind rather than a real shopkeeper's (Stockwell/Beedle) - those kinds
// dispatch through their own action-function tables that expect a
// ScriptExecutionContext already wired up their own specific way (e.g.
// Stockwell's `this->context`, set up only by his own vanilla init code),
// incompatible with the generic StartCutscene-based script attachment
// QuickStartMakeNpcTalkable uses. ZELDA's is already proven generic and
// safe (used for the Main item-choice sign earlier in this file) - the
// merchant will look like Zelda for now, a cosmetic mismatch rather than a
// functional one.
//
// Same merchant (same catalog, same script_QuickStartMerchant, same
// gRoomVars.shopItemType-based sale) now also runs in Lon Lon Ranch's east
// house room (see QuickStartRoomMonitor below) - just called again with
// that room's own verified npcOffsetX/Y. Nothing needs to track "bought in
// one room, reflected in the other": the catalog, prices, and purchase
// mechanism all key off GetInventoryValue/gSave, which is already global
// save state, so an item bought at either location is simply owned
// game-wide from then on - the same way it would be if Beedle and Talon
// both happened to sell the same item.
static void QuickStartSpawnShopMerchantOnce(s16 npcOffsetX, s16 npcOffsetY) {
    s32 i;
    Entity* npc;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
            return;
        }
    }
    npc = CreateNPC(ZELDA, 0, 0);
    if (npc != NULL) {
        npc->x.HALF.HI = gRoomControls.origin_x + npcOffsetX;
        npc->y.HALF.HI = gRoomControls.origin_y + npcOffsetY;
        npc->collisionLayer = 1;
        UpdateSpriteForCollisionLayer(npc);
        QuickStartMakeNpcTalkable(npc, &script_QuickStartMerchant);
    }
}

// Shared by both shop rooms (Grimblade and Lon Lon Ranch's east house room)
// - each room's own pre-existing vanilla content (Grimblade's Blademaster,
// door-frame torches, and one prop; the east room's own vanilla
// NPCs/furniture-as-entities, if any) confirmed present via an emulator
// entity dump the first time each room was loaded. Cleared unconditionally
// every frame, same idempotent pattern as QuickStartClearMelarisMineObstacles,
// but scoped by id rather than a blanket kind check: both rooms host our own
// ZELDA-kind merchant NPC and SHOP_ITEM-kind pedestals, which a blanket
// "delete every NPC/OBJECT" would also delete.
static void QuickStartClearShopObstacles(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == NPC && ent->id != ZELDA) {
            DeleteEntity(ent);
        } else if (ent->kind == OBJECT && ent->id != SHOP_ITEM) {
            DeleteEntity(ent);
        }
    }
}

// The merchant's fixed catalog, displayed as liftable SHOP_ITEM pedestal
// props rather than offered through dialogue - the real vanilla shop UX
// (Stockwell, the Goron Merchant): the player lifts one, carries it to the
// merchant, and script_QuickStartMerchant completes the sale based on
// whatever's in gRoomVars.shopItemType, exactly like Beedle/Talon's own
// scripts do. Expanded from the original 3 consumables to a real stock of
// equipment upgrades, a heart piece, a bottle with a fairy in it, and a
// skill - covering "any item, powerup, or skill" at a small scale rather
// than literally every item in the game. Prices for every one of these
// (itemMetaData.c, gUnk_080FD964, #ifdef QUICKSTART) start at 100 and go
// up with the item's value - the two upgrades priced 600 in vanilla (bomb
// bag, large quiver) already clear that bar unmodified. Shared by both shop
// rooms - same wares everywhere the merchant appears.
static const u16 sQuickStartShopCatalog[] = {
    ITEM_BOMBS10,          ITEM_ARROWS10, ITEM_SHIELD,     ITEM_HEART_PIECE,
    ITEM_BOTTLE_FAIRY,     ITEM_WALLET,   ITEM_BOMBBAG,    ITEM_LARGE_QUIVER,
    ITEM_SKILL_SPIN_ATTACK,
};
// Placed by the user directly (Lua position script) - two rows across
// Grimblade's open floor.
static const s16 sQuickStartShopItemOffsets[][2] = {
    { 60, 57 }, { 90, 57 }, { 120, 57 }, { 150, 57 }, { 180, 57 },
    { 170, 85 }, { 140, 85 }, { 110, 85 }, { 80, 85 },
};
// Lon Lon Ranch east house room's own catalog layout - same 5+4 two-row
// split as Grimblade's, independently verified walkable in the emulator
// (per-spot movement check from the room's own (120,120) entrance) since
// this room's furniture layout is completely different from Grimblade's.
static const s16 sQuickStartRanchHouseEastShopOffsets[][2] = {
    { 60, 72 }, { 90, 72 }, { 120, 72 }, { 150, 72 }, { 180, 72 },
    { 170, 104 }, { 140, 104 }, { 110, 104 }, { 80, 104 },
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

// Polled every frame the player is in either shop room (alongside
// QuickStartSpawnShopMerchantOnce) so a purchased item's now-deleted
// pedestal prop gets restocked - vanilla's real pedestal shops (Goron
// Merchant etc.) have their own manager entity to do this; we don't have
// that infrastructure, so just re-check and re-spawn missing entries here
// instead. `offsets` must have exactly ARRAY_COUNT(sQuickStartShopCatalog)
// entries, one per catalog item in the same order.
static void QuickStartMaintainShop(const s16 (*offsets)[2]) {
    s32 i;
    for (i = 0; i < ARRAY_COUNT(sQuickStartShopCatalog); i++) {
        if (!QuickStartShopItemExists(sQuickStartShopCatalog[i])) {
            QuickStartSpawnShopItem(sQuickStartShopCatalog[i], offsets[i][0], offsets[i][1]);
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
// Bit +0 of each ladder's block is unused now - it used to be
// GF_LADDER_REVEALED, tracking whether the marker pot had been broken yet
// (removed along with the whole pot mechanic; the real ladder fixtures and
// the Goron Cave door are simply always live now, no reveal step needed).
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
// ladder bits above (highest in use is GF_LADDER_ROOM_BIT(3,5) = 173, the
// 4th ladder slot being the Goron Cave Stairs door's own pool draw - see
// QuickStartRandomizeLaddersOnce below).
// 4 bits -> 0..15 (only 0..QUICKSTART_MAX_DIFFICULTY are ever produced by
// QuickStartIncrementDifficulty, but the extra headroom over the previous
// 2-bit counter costs nothing and leaves room to extend the curve later).
// Save-persistent (global flags, not room flags) since it has to survive
// the DoSoftReset a win triggers - EWRAM (and gSave with it) is
// deliberately preserved across that reset (see DoSoftReset, main.c), and
// WriteSaveFile below makes sure it's actually on the save file the
// title/file-select flow reloads from, not just sitting in EWRAM.
#define GF_DIFFICULTY_BIT(b) (174 + (b)) // b = 0..3
#define QUICKSTART_MAX_DIFFICULTY 12

static u8 QuickStartGetDifficulty(void) {
    return (CheckGlobalFlag(GF_DIFFICULTY_BIT(0)) ? 1 : 0) | (CheckGlobalFlag(GF_DIFFICULTY_BIT(1)) ? 2 : 0) |
           (CheckGlobalFlag(GF_DIFFICULTY_BIT(2)) ? 4 : 0) | (CheckGlobalFlag(GF_DIFFICULTY_BIT(3)) ? 8 : 0);
}

static void QuickStartIncrementDifficulty(void) {
    u8 next = QuickStartGetDifficulty();
    s32 b;
    if (next < QUICKSTART_MAX_DIFFICULTY) {
        next++;
    }
    for (b = 0; b < 4; b++) {
        if (next & (1 << b)) {
            SetGlobalFlag(GF_DIFFICULTY_BIT(b));
        } else {
            ClearGlobalFlag(GF_DIFFICULTY_BIT(b));
        }
    }
}

// The enemy roster, grouped into 5 hand-picked difficulty levels (level 1
// easiest, level 5 hardest) per the user's own list - only enemies with a
// straightforward, crash-free CreateEnemy(id, form) spawn made the cut;
// anything with a mechanic that needs more setup (a scripted home/range, a
// room property, dungeon entrance data, etc.) was deliberately left out.
// "form" here is the same value CreateEnemy's second argument always was
// elsewhere in this file (entity->type) - for enemies with a color variant
// it selects which color; for the rest it's always 0.
typedef struct {
    u8 id;
    u8 form;
} QuickStartEnemyPick;

static const QuickStartEnemyPick sQuickStartLevel1[] = {
    { ACRO_BANDIT, 0 }, { BEETLE, 0 }, { BOBOMB, 0 }, { CROW, 0 }, { CHUCHU, 0 /* green */ },
    { KEESE, 0 },       { LEEVER, 0 /* red */ },      { OCTOROK, 0 /* red */ },
    { LIKE_LIKE, 0 },   { ROPE, 0 },
};
static const QuickStartEnemyPick sQuickStartLevel2[] = {
    { CHUCHU, 2 /* blue */ }, { LEEVER, 1 /* blue */ },     { OCTOROK, 1 /* blue */ }, { BOMBAROSSA, 0 },
    { BOW_MOBLIN, 0 },        { RUPEE_LIKE, 0 /* green */ }, { HELMASAUR, 0 },          { MOLDORM, 0 },
    { PEAHAT, 0 },            { MULLDOZER, 0 /* red */ },    { PESTO, 0 /* red */ },    { TEKTITE, 0 /* red */ },
    { SLUGGULA, 0 },
};
// Yellow and purple Keaton are the same actor with no form-based color
// variant (confirmed empirically - all 4 form values render identically),
// so Keaton only appears once here rather than duplicated into level 4.
static const QuickStartEnemyPick sQuickStartLevel3[] = {
    { MULLDOZER, 1 /* blue */ }, { PESTO, 1 /* blue */ },  { STALFOS, 1 /* blue */ }, { TEKTITE, 1 /* blue */ },
    { GHINI, 0 },                { PUFFSTOOL, 0 },         { CHUCHU, 1 /* red */ },   { RUPEE_LIKE, 2 /* red */ },
    { STALFOS, 0 /* red */ },    { WISP, 0 /* red */ },    { ROCK_CHUCHU, 0 },        { ROLLOBITE, 0 },
    { SPARK, 0 },                { SPEAR_MOBLIN, 0 },      { SPIKED_BEETLE, 0 },      { KEATON, 0 },
};
// Floormaster (Wall Master) deliberately left out - it grabs the player and
// warps them to a dungeon's scripted "entrance" point, which none of these
// QUICKSTART rooms have configured, so the actual destination would be
// undefined.
static const QuickStartEnemyPick sQuickStartLevel4[] = {
    { RUPEE_LIKE, 1 /* blue */ }, { WISP, 1 /* blue */ }, { GOBDO, 0 /* gibdo */ }, { LAKITU, 0 },
    { MOLDWORM, 0 },              { SCISSORS_BEETLE, 0 }, { SPINY_BEETLE, 0 },      { TAKKURI, 0 },
};
static const QuickStartEnemyPick sQuickStartLevel5[] = {
    { BALL_CHAIN_SOLIDER, 0 },
    { WIZZROBE_ICE, 0 },
    { WIZZROBE_FIRE, 0 },
};

static const QuickStartEnemyPick* const sQuickStartEnemyLevels[5] = {
    sQuickStartLevel1, sQuickStartLevel2, sQuickStartLevel3, sQuickStartLevel4, sQuickStartLevel5,
};
static const s32 sQuickStartEnemyLevelCounts[5] = {
    ARRAY_COUNT(sQuickStartLevel1), ARRAY_COUNT(sQuickStartLevel2), ARRAY_COUNT(sQuickStartLevel3),
    ARRAY_COUNT(sQuickStartLevel4), ARRAY_COUNT(sQuickStartLevel5),
};

// One row per difficulty step: how much of each enemy level to sample from
// (must sum to 100) and how many squares (32x32) each enemy gets - lower is
// denser. Density never goes below 5 (QUICKSTART_MIN_DENSITY) - going any
// denser than that isn't just a matter of verifying more spawn spots, the
// room's entire entity budget (MAX_ENTITIES, entity.h) is shared with the
// player, decorations, and everything else, so there's a hard ceiling on
// how many enemies can ever exist at once regardless of density - see the
// per-room QUICKSTART_*_MAX_ENEMIES caps below. A simple first pass, easy
// to retune once we see how a full run plays out.
typedef struct {
    u8 levelWeights[5];
    u8 density;
} QuickStartDifficultyTier;

#define QUICKSTART_MIN_DENSITY 5

static const QuickStartDifficultyTier sQuickStartDifficultyTiers[QUICKSTART_MAX_DIFFICULTY + 1] = {
    /*  0 */ { { 100, 0, 0, 0, 0 }, 25 },
    /*  1 */ { { 80, 20, 0, 0, 0 }, 25 },
    /*  2 */ { { 80, 20, 0, 0, 0 }, 15 },
    /*  3 */ { { 60, 40, 0, 0, 0 }, 12 },
    /*  4 */ { { 40, 60, 0, 0, 0 }, 10 },
    /*  5 */ { { 20, 80, 0, 0, 0 }, 10 },
    /*  6 */ { { 0, 60, 40, 0, 0 }, 9 },
    /*  7 */ { { 0, 40, 45, 15, 0 }, 8 },
    /*  8 */ { { 0, 20, 45, 30, 5 }, 7 },
    /*  9 */ { { 0, 10, 35, 40, 15 }, 7 },
    /* 10 */ { { 0, 0, 30, 45, 25 }, 6 },
    /* 11 */ { { 0, 0, 20, 40, 40 }, 5 },
    /* 12 */ { { 0, 0, 15, 35, 50 }, 5 }, // never 100% level 5, per the brief
};

static const QuickStartDifficultyTier* QuickStartGetDifficultyTier(u8 difficulty) {
    if (difficulty > QUICKSTART_MAX_DIFFICULTY) {
        difficulty = QUICKSTART_MAX_DIFFICULTY;
    }
    return &sQuickStartDifficultyTiers[difficulty];
}

// Rolls one fresh enemy (id + form) for the given difficulty: first picks a
// level via the tier's weights (a plain weighted die roll over whichever
// levels have nonzero weight this tier), then picks uniformly at random
// within that level's roster. Called once per enemy spawned rather than
// once per room, so - exactly per the brief - two rooms at the same
// difficulty can come out with entirely different enemy mixes.
static void QuickStartPickEnemy(u8 difficulty, u8* outId, u8* outForm) {
    const QuickStartDifficultyTier* tier = QuickStartGetDifficultyTier(difficulty);
    s32 roll = (s32)Random() % 100;
    s32 cumulative = 0;
    s32 level;
    s32 levelCount;
    const QuickStartEnemyPick* pick;
    for (level = 0; level < 5; level++) {
        cumulative += tier->levelWeights[level];
        if (roll < cumulative) {
            break;
        }
    }
    if (level >= 5) {
        // Only reachable if a tier's weights don't sum to 100 - fall back
        // to the lowest level that's actually available this tier.
        for (level = 0; level < 5 && tier->levelWeights[level] == 0; level++) {
        }
        if (level >= 5) {
            level = 0;
        }
    }
    levelCount = sQuickStartEnemyLevelCounts[level];
    pick = &sQuickStartEnemyLevels[level][(s32)Random() % levelCount];
    *outId = pick->id;
    *outForm = pick->form;
}

// Shared by every QUICKSTART enemy spawner: picks `count` distinct spots
// out of this room's own pre-verified-walkable offset pool (a partial
// Fisher-Yates shuffle, so which spots get used - not just which enemies -
// varies across boots too) and rolls a fresh enemy for each from
// QuickStartPickEnemy. `count` itself comes from the room's size in 32x32
// squares divided by this difficulty's density, clamped to at least 1, and
// to at most whichever is smaller of the offset pool's own size or
// maxEnemies (the room's hard entity-budget ceiling - see the per-room
// constants above each call site).
static void QuickStartSpawnEnemyGroup(const s16 (*offsets)[2], s32 offsetCount, s32 roomSquares, s32 maxEnemies) {
    s32 indices[72];
    s32 i, j, r, tmp, count, difficulty, density, cap;
    Entity* enemy;
    u8 id, form;

    if (offsetCount > 72) {
        offsetCount = 72;
    }
    for (i = 0; i < offsetCount; i++) {
        indices[i] = i;
    }
    for (i = 0; i < offsetCount - 1; i++) {
        r = (s32)Random() % (offsetCount - i);
        tmp = indices[i];
        indices[i] = indices[i + r];
        indices[i + r] = tmp;
    }

    difficulty = QuickStartGetDifficulty();
    density = QuickStartGetDifficultyTier(difficulty)->density;
    if (density < QUICKSTART_MIN_DENSITY) {
        density = QUICKSTART_MIN_DENSITY;
    }
    count = roomSquares / density;
    if (count < 1) {
        count = 1;
    }
    cap = (offsetCount < maxEnemies) ? offsetCount : maxEnemies;
    if (count > cap) {
        count = cap;
    }

    for (i = 0; i < count; i++) {
        j = indices[i];
        QuickStartPickEnemy(difficulty, &id, &form);
        enemy = CreateEnemy(id, form);
        if (enemy != NULL) {
            enemy->x.HALF.HI = gRoomControls.origin_x + offsets[j][0];
            enemy->y.HALF.HI = gRoomControls.origin_y + offsets[j][1];
            enemy->collisionLayer = 1;
            enemy->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(enemy);
        }
    }
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
    // Minish House Interiors rows: content placed by the user directly (Lua
    // position script) at a single shared spot, (120,80) - 40px north of
    // the (120,120) shared spawn, facing back down toward the door (see
    // QuickStartSetupLadderRoomContent's direction = IdleSouth) - rather
    // than each room's own individually-walked offset. Confirmed in the
    // emulator for the item and NPC kinds (both land exactly on (120,80),
    // direction sticks for the NPC); the miniboss enemy's own continuous
    // AI update overwrites direction on every subsequent frame regardless
    // of what's set at spawn (and nudges its landing y by a few px, same
    // class of engine-owned adjustment as the ladder pots' own +3px), so
    // "facing down" only reliably holds for the brief spawn frame there -
    // not fixable without rewriting the enemy's own AI.
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_BLUE, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GENTARI_MAIN, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GREEN, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_EXIT, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_TOWN, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_LAKE_HYLIA_OCARINA, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_MINISH_WOODS_BOMB, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_NEXT_TO_KNUCKLE, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_POT_MINISH, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_RED, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SHOE_MINISH, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SIDE_AREA, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD, 0, -40 },
    // Moved from (120,136) to (119,102) (contentDX/DY -1,-18) per the user's
    // report: the old spot put a LADDER_KIND_MINIBOSS Dark Nut right at the
    // room's own door, where it got stuck rather than fighting properly.
    // Confirmed walkable and stable (no drift) in both rooms.
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE, -1, -18 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WESTERN_WOODS_HEART_PIECE, -1, -18 },
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
// per save (GF_LADDERS_RANDOMIZED) - exactly once, each of 4 "? room" slots
// is assigned a kind, and (for chest/NPC kinds) which specific reward or
// disposition, all via Random(). Slots 0, 1, and 3 each additionally draw
// which of the 20 sQuickStartQuestionRoomPool rooms they lead to - slots 0-1
// are Castle Garden's own two real ladders, slot 3 is the Goron Cave Stairs
// door in Lon Lon Ranch (see sQuickStartLadderEntrances below), a fixed
// entrance but a random destination, same as the other two. Slot 2 (Ranch
// House West) is a fixed room end to end - own entrance, own room - so it
// only needs a kind/extra roll, no room draw. Doing this lazily on first
// room entry rather than in GameTask_Transition avoids touching the boot
// sequence at all - the persistent flags this writes make the choice stick
// for the rest of this save regardless of when it first ran.
static void QuickStartRandomizeLaddersOnce(void) {
    s32 i, j, drawCount;
    u8 usedRoom[3];
    if (CheckGlobalFlag(GF_LADDERS_RANDOMIZED)) {
        return;
    }
    drawCount = 0;
    for (i = 0; i < 4; i++) {
        u8 kind = (u8)((s32)Random() % 3);
        u8 roomIdx;
        QuickStartLadderSetKind(i, kind);
        if (kind == LADDER_KIND_CHEST) {
            QuickStartLadderSetExtra(i, (u8)((s32)Random() % QUICKSTART_LADDER_REWARD_POOL_SIZE));
        } else if (kind == LADDER_KIND_NPC) {
            QuickStartLadderSetExtra(i, (u8)((s32)Random() % 2)); // bit 0: 1 = evil, 0 = friendly
        }
        if (i == 2) {
            continue;
        }
        // Distinct room per slot - two slots sharing one physical "? room"
        // would make leaving through it ambiguous about which one's
        // content to re-arm. The pool (20) comfortably exceeds the 3 draws
        // needed, so a plain reject-and-retry loop is enough.
        for (;;) {
            roomIdx = (u8)((s32)Random() % QUICKSTART_QUESTION_ROOM_POOL_SIZE);
            for (j = 0; j < drawCount; j++) {
                if (usedRoom[j] == roomIdx) {
                    break;
                }
            }
            if (j == drawCount) {
                break;
            }
        }
        usedRoom[drawCount] = roomIdx;
        drawCount++;
        QuickStartLadderSetRoomIndex(i, roomIdx);
    }
    SetGlobalFlag(GF_LADDERS_RANDOMIZED);
}

// No pot, no "reveal" step any more - the user didn't want the pot-lift-and-
// throw mechanic at all, just Link descending the real vanilla ladder
// fixture as he would in vanilla. Castle Garden Main has exactly two real
// HIDDEN_LADDER_DOWN fixtures (object.c, id 87). Their own registered
// entity position ((104,104) and (936,376), read directly off the live
// entities in the emulator) isn't quite where the player actually ends up
// standing after descending one, though - the user walked up to each real
// ladder in-game and read back Link's own position with the Lua script
// afterward, landing on (104,110) and (936,382) instead (a few px off from
// the fixture's own registration point, presumably HiddenLadderDown's own
// undecompiled logic settling the player at a slightly different anchor).
// These trigger boxes are centered on those user-verified positions rather
// than the raw entity coordinates. The Goron Cave Stairs door (Lon Lon
// Ranch, see the KINSTONE_29 fuse in GameTask_Transition) is a third
// entrance into this same "? room" system now, ladder index 3, with its
// own real-door-adjacent trigger box (see the sQuickStartLinks comment
// above for how that corridor was traced) rather than a HIDDEN_LADDER_DOWN
// fixture. Unlike the fixed 3-room mapping this replaced, or Ranch House
// West's own single fixed room, ladder index 3's destination is a pool
// draw exactly like ladders 0-1 (QuickStartRandomizeLaddersOnce above), so
// its target has to be resolved at trigger time rather than being a static
// entry in sQuickStartLinks - hence this table (fromArea/fromRoom/trigger
// box/ladder index) and QuickStartProcessLadderLinks below, rather than
// folding it into sQuickStartLinks. Unlike ladders 0-1, though, it's
// entered from a different room than it returns to - see
// QuickStartFixupQuestionRoomReturn's own ladderIndex == 3 special case
// below for why leaving the pool room lands back in Lon Lon Ranch instead
// of Castle Garden Main.
typedef struct {
    u8 fromArea;
    u8 fromRoom;
    s16 triggerMinX;
    s16 triggerMaxX;
    s16 triggerMinY;
    s16 triggerMaxY;
    s32 ladderIndex;
} QuickStartLadderEntrance;

static const QuickStartLadderEntrance sQuickStartLadderEntrances[] = {
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 88, 120, 94, 126, 0 },
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 920, 952, 366, 398, 1 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 120, 152, 836, 868, 3 },
};

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

// Checked every frame regardless of area (called unconditionally from
// QuickStartRoomMonitor, alongside QuickStartEnforceContainment) since its
// three entrances now span two different rooms (Castle Garden Main and
// Lon Lon Ranch) - unlike the old pot-based version, there's no reveal
// state to gate on any more, the real ladder fixtures (and the Goron Cave
// door corridor) are simply always live.
static void QuickStartProcessLadderLinks(void) {
    s32 i;
    s16 localX, localY;
    if (gRoomTransition.transitioningOut) {
        return;
    }
    localX = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
    localY = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
    for (i = 0; i < ARRAY_COUNT(sQuickStartLadderEntrances); i++) {
        const QuickStartLadderEntrance* entrance = &sQuickStartLadderEntrances[i];
        if (gRoomControls.area == entrance->fromArea && gRoomControls.room == entrance->fromRoom &&
            localX >= entrance->triggerMinX && localX <= entrance->triggerMaxX && localY >= entrance->triggerMinY &&
            localY <= entrance->triggerMaxY) {
            u8 targetArea, targetRoom;
            QuickStartGetLadderTarget(entrance->ladderIndex, &targetArea, &targetRoom);
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
static Script* const sQuickStartLadderNpcScripts[2] = {
    &script_QuickStartLadderNpc0,
    &script_QuickStartLadderNpc1,
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
//
// Ladder index 2 (Ranch House West) isn't part of the random pool draw -
// it's a fixed room, so its content position is just
// sQuickStartFixedRoomContentPos directly rather than a pool lookup. Index
// 3 (Goron Cave Stairs door) IS a pool draw like 0-1, so it falls through
// to the regular lookup below.
static void QuickStartGetLadderContentOffset(s32 ladderIndex, s16* contentX, s16* contentY) {
    s32 rawIndex, poolIndex;
    if (ladderIndex == 2) {
        *contentX = sQuickStartFixedRoomContentPos[0][0];
        *contentY = sQuickStartFixedRoomContentPos[0][1];
        return;
    }
    rawIndex = QuickStartLadderGetRoomIndex(ladderIndex);
    poolIndex = rawIndex % QUICKSTART_QUESTION_ROOM_POOL_SIZE;
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
        // Room flag 3: "confirmed present at least once this visit" -
        // distinct from flag 0 ("we've spawned it"), same two-flag "did it
        // vanish for real, or was it wiped before ever really settling"
        // pattern QuickStartSpawnMelarisMineRewardOnce/
        // QuickStartSpawnGardenRewardOnce already use, kept here for the
        // same reason: without it, a chest that disappears before this
        // function ever confirms it was actually there (e.g. the entity
        // slot getting reused some other way) reads as a genuine pickup on
        // the very next frame it's checked.
        if (CheckRoomFlag(0)) {
            if (QuickStartGroundItemAt(contentX, contentY)) {
                SetRoomFlag(3);
                return;
            }
            if (CheckRoomFlag(3)) {
                SetGlobalFlag(GF_LADDER_DONE(ladderIndex));
                return;
            }
            // Never confirmed present - fall through and re-drop it.
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
                // Set after UpdateSpriteForCollisionLayer, which otherwise
                // overwrites it (confirmed in the emulator: direction read
                // back as 0xFF, not IdleSouth, when set beforehand).
                itemEntity->direction = IdleSouth;
                SetRoomFlag(0);
            }
        }
    } else if (kind == LADDER_KIND_MINIBOSS) {
        if (CheckRoomFlag(2)) {
            // Reward already dropped this visit - just watching for pickup
            // (same "did it vanish for real, or did the room just unload
            // before they grabbed it" distinction QuickStartGroundItemAt
            // exists for on the chest case above).
            if (!QuickStartGroundItemAt(contentX, contentY)) {
                SetGlobalFlag(GF_LADDER_DONE(ladderIndex));
            }
            return;
        }
        if (CheckRoomFlag(0)) {
            s32 i;
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* enemy = &gEntities[i].base;
                if (enemy->kind == ENEMY && QuickStartEntityInCurrentRoom(enemy)) {
                    // Keep it parked exactly on its spawn spot until the
                    // player gets close enough to actually engage - the
                    // same 56px "notice the player" radius its own AI
                    // (darkNut.c) already switches out of idle patrolling
                    // at. Without this, it visibly wanders off its spawn
                    // point within about half a second of the room
                    // loading, even with the player nowhere nearby to
                    // react to - confirmed by logging its position frame
                    // by frame with nobody else in the room. A heart piece
                    // dropped at this same spot never has this problem
                    // (no AI to wander with), which is the whole
                    // discrepancy this was chasing.
                    if (!PlayerInRange(enemy, 1, 56)) {
                        enemy->x.HALF.HI = gRoomControls.origin_x + contentX;
                        enemy->y.HALF.HI = gRoomControls.origin_y + contentY;
                    }
                    return;
                }
            }
            // Dead - drop the reward and start watching for pickup.
            {
                Entity* itemEntity = CreateObject(GROUND_ITEM, ITEM_HEART_PIECE, 0);
                if (itemEntity != NULL) {
                    itemEntity->x.HALF.HI = gRoomControls.origin_x + contentX;
                    itemEntity->y.HALF.HI = gRoomControls.origin_y + contentY;
                    itemEntity->collisionLayer = 1;
                    itemEntity->flags |= ENT_PERSIST;
                    UpdateSpriteForCollisionLayer(itemEntity);
                    itemEntity->direction = IdleSouth;
                    SetRoomFlag(2);
                }
            }
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
                enemy->direction = IdleSouth;
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
                npc->direction = IdleSouth;
                // % 2: ladder indices 2-3 (Ranch House) reuse the same 2
                // NPC scripts as indices 0-1 rather than needing their own -
                // the script itself doesn't reference which physical room
                // it's running in.
                QuickStartMakeNpcTalkable(npc, sQuickStartLadderNpcScripts[ladderIndex % 2]);
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

// Which ladder slot (0-3) the current room is standing in for, or -1 if it
// isn't one of them. Unlike the old fixed 3-branch dispatch this replaces,
// the pool spans several real areas (Minish House Interiors, Tree Interiors,
// Caves, Great Fairies, Royal Valley Graves) and which physical room maps to
// which ladder varies per save, so a plain area/room comparison against
// fixed constants doesn't work for slots 0, 1, or 3 (all three draw their
// room from the pool - see QuickStartRandomizeLaddersOnce) - this checks
// against each one's current runtime assignment instead. Slot 2 (Ranch
// House West) IS a fixed physical room though (no pool draw), so that one's
// a direct area/room match.
static s32 QuickStartFindLadderForCurrentRoom(void) {
    static const u8 sPoolDrawLadderIndices[3] = { 0, 1, 3 };
    s32 k, i, rawIndex, poolIndex;
    for (k = 0; k < 3; k++) {
        i = sPoolDrawLadderIndices[k];
        rawIndex = QuickStartLadderGetRoomIndex(i);
        poolIndex = rawIndex % QUICKSTART_QUESTION_ROOM_POOL_SIZE;
        if (gRoomControls.area == sQuickStartQuestionRoomPool[poolIndex].area &&
            gRoomControls.room == sQuickStartQuestionRoomPool[poolIndex].room) {
            return i;
        }
    }
    if (gRoomControls.area == AREA_HOUSE_INTERIORS_4 && gRoomControls.room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST) {
        return 2;
    }
    return -1;
}

// Where each ladder's own real exit already lands - clear of every
// ladder/entrance trigger box in this room, so returning doesn't instantly
// re-trigger whichever one it lands near. Every "? room" pool entry's
// retargeted exit (src/data/transitions.c) points at the same literal spot
// regardless of which ladder it's serving this save, since which physical
// room backs which ladder varies per save and a compile-time table can't
// encode that - QuickStartFixupQuestionRoomReturn below corrects the
// landing position to the right one of these before the transition
// completes. Ladder 1's spot is as close to landing "on the ladder
// fixture" (936,376) as this room's own hedges allow - a live collision
// dump plus walking there directly found that spot inside blocked hedge
// collision (the previous (800,370) estimate turned out to still be
// inside a different hedge, matching the user's own bug report of
// spawning "inside a shrubbery"); (935,311), well north at the same x, is
// the closest confirmed-walkable point, open in every direction except
// the hedge immediately east. Indexed directly by ladderIndex (0-3), not by
// draw order, so indices 2 and 3 are unused placeholders here: index 2
// (Ranch House West)'s own real exit never targets Castle Garden Main, and
// index 3 (Goron Cave Stairs door)'s pool room is redirected back to Lon
// Lon Ranch entirely (not just repositioned within Castle Garden) by
// QuickStartFixupQuestionRoomReturn's own ladderIndex == 3 special case
// below - both are skipped before this array is ever read with that index.
static const s16 sQuickStartLadderReturnSpots[4][2] = {
    { 105, 144 },
    { 935, 311 },
    { 0, 0 },
    { 0, 0 },
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
    if (ladderIndex == 3) {
        // Goron Cave Stairs door - entered from Lon Lon Ranch, not Castle
        // Garden (unlike ladders 0-1, which both enter and leave through
        // Castle Garden), so it should return there too, rather than to
        // the literal Castle Garden spot every pool room's own retargeted
        // exit shares. Overrides the whole destination, not just position:
        // (344,870) is the same proven-safe landing spot the Castle
        // Garden -> Lon Lon Ranch link itself uses, clear of the Goron
        // Cave door's own trigger box (120-152,836-868).
        gRoomTransition.player_status.area_next = AREA_HYRULE_FIELD;
        gRoomTransition.player_status.room_next = ROOM_HYRULE_FIELD_LON_LON_RANCH;
        gRoomTransition.player_status.start_pos_x = 344;
        gRoomTransition.player_status.start_pos_y = 870;
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
    for (i = 0; i < 2; i++) {
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
    // The merchant's room (AREA_DOJOS, ROOM_DOJOS_GRIMBLADE) isn't added to
    // QuickStartAreaContained wholesale - AREA_DOJOS holds several other
    // real dojo rooms entered from many unrelated overworld spots, same
    // "don't blanket-contain a shared area" reasoning as Minish House
    // Interiors/Tree Interiors' own ladder-target exception above. This is
    // the one specific transition sQuickStartLinks itself is about to make
    // leaving Melari's Mine, let through the same way.
    if (gRoomTransition.player_status.area_next == AREA_DOJOS && gRoomTransition.player_status.room_next == ROOM_DOJOS_GRIMBLADE) {
        return;
    }
    if (!QuickStartAreaContained(gRoomTransition.player_status.area_next)) {
        gRoomTransition.transitioningOut = 0;
    }
}

// Lon Lon Ranch is a single room inside AREA_HYRULE_FIELD, a huge overworld
// area with many entirely unrelated rooms (South Hyrule Field, Eastern
// Hills, Trilby Highlands, ...) - QuickStartAreaContained can't just add
// AREA_HYRULE_FIELD wholesale the way it does for single-purpose areas
// like Castor Darknut or Melari's Mine, that would be containing far more
// than intended. This is the same idea scoped to the one room instead of
// the whole area: leaving Lon Lon Ranch through anything except the
// sQuickStartLinks position box back to Castle Garden gets cancelled,
// which blocks the ranch's other real vanilla exits - the Veil
// Falls/Lake Hylia/Hyrule Town borders reliably fire under QUICKSTART
// (WARP_TYPE_BORDER doesn't need GetActTileAtTilePos) and need this to
// stay blocked; the two ranch house interiors, two cave entrances, and
// Goron Cave's own real door are WARP_TYPE_AREA doors that don't reliably
// fire under QUICKSTART at all (same ACT_TILE gap the Castle Garden/Lon
// Lon Ranch link itself works around), so this check is mostly a no-op
// safety net for those, not their only defense - our own sQuickStartLinks
// position box into the two ranch house rooms, and QuickStartProcessLadderLinks'
// own transition into whichever pool room ladder 3 (the Goron Cave Stairs
// door) currently resolves to, are both explicitly allowed through below.
static void QuickStartEnforceLonLonContainment(void) {
    u8 ladder3TargetArea, ladder3TargetRoom;
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomControls.area != AREA_HYRULE_FIELD || gRoomControls.room != ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        return;
    }
    if (gRoomTransition.player_status.area_next == AREA_CASTLE_GARDEN &&
        gRoomTransition.player_status.room_next == ROOM_CASTLE_GARDEN_MAIN) {
        return;
    }
    if (gRoomTransition.player_status.area_next == AREA_HYRULE_FIELD &&
        gRoomTransition.player_status.room_next == ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        return;
    }
    if (gRoomTransition.player_status.area_next == AREA_HOUSE_INTERIORS_4 &&
        (gRoomTransition.player_status.room_next == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST ||
         gRoomTransition.player_status.room_next == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST)) {
        return;
    }
    QuickStartGetLadderTarget(3, &ladder3TargetArea, &ladder3TargetRoom);
    if (gRoomTransition.player_status.area_next == ladder3TargetArea &&
        gRoomTransition.player_status.room_next == ladder3TargetRoom) {
        return;
    }
    gRoomTransition.transitioningOut = 0;
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
            // start_anim doubles as the spawn facing (gameUtils.c copies it
            // straight into the player's animationState/direction on
            // arrival) - only these two destinations need an explicit one
            // (per the user's own requests); every other link leaves it
            // alone, matching this function's prior behavior.
            if (link->toArea == AREA_CASTOR_DARKNUT && link->toRoom == ROOM_CASTOR_DARKNUT_HALL) {
                gRoomTransition.player_status.start_anim = IdleSouth;
            } else if (link->toArea == AREA_DOJOS && link->toRoom == ROOM_DOJOS_GRIMBLADE) {
                gRoomTransition.player_status.start_anim = IdleNorth;
            }
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
    QuickStartEnforceLonLonContainment();
    QuickStartFixupQuestionRoomReturn();
    // Unconditional (not folded into a specific room's branch below) since
    // its 3 entrances now span two different rooms - see
    // sQuickStartLadderEntrances and QuickStartProcessLadderLinks above.
    QuickStartProcessLadderLinks();
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
    } else if (gRoomControls.area == AREA_HYRULE_FIELD && gRoomControls.room == ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        QuickStartClearLonLonRanchGoron();
        QuickStartSolveLonLonBoulder();
        QuickStartSpawnLonLonRanchEnemiesOnce();
        QuickStartSpawnWinKeyOnce();
        QuickStartCheckWinCondition();
    } else if (gRoomControls.area == AREA_DOJOS && gRoomControls.room == ROOM_DOJOS_GRIMBLADE) {
        QuickStartClearShopObstacles();
        QuickStartSpawnShopMerchantOnce(120, 125);
        QuickStartMaintainShop(sQuickStartShopItemOffsets);
    } else if (gRoomControls.area == AREA_HOUSE_INTERIORS_4 &&
               gRoomControls.room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST) {
        // The east house room is the merchant's second location now (same
        // catalog, same script - see QuickStartSpawnShopMerchantOnce above)
        // rather than a "? room" - it no longer goes through
        // QuickStartFindLadderForCurrentRoom at all. Slot 3 (which used to
        // be this room) is now the Goron Cave Stairs door's own pool draw
        // instead - see sQuickStartLadderEntrances.
        QuickStartClearShopObstacles();
        QuickStartSpawnShopMerchantOnce(176, 56);
        QuickStartMaintainShop(sQuickStartRanchHouseEastShopOffsets);
    } else {
        // Falls through to here for Ranch House West (slot 2, a fixed
        // room) and for whichever pool room the Goron Cave Stairs door
        // (slot 3) currently resolves to - same generic dispatch as
        // Castle Garden's own two ladders (slots 0-1).
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
static const s16 sQuickStartItemOffsets[QUICKSTART_ITEM_CHOICES] = { 100, 136, 170 };

static void QuickStartSpawnItems(const QuickStartItemChoice* choices) {
    s32 i;
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        Entity* itemEntity = CreateObject(GROUND_ITEM, choices[i].itemId, 0);
        if (itemEntity != NULL) {
            itemEntity->x.HALF.HI = gRoomControls.origin_x + sQuickStartItemOffsets[i];
            itemEntity->y.HALF.HI = gRoomControls.origin_y + 105;
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
        npc->x.HALF.HI = gRoomControls.origin_x + 135;
        npc->y.HALF.HI = gRoomControls.origin_y + 70;
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
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + 135;
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
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + 135;
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
        // construction the wave 1 enemies already exist (having survived the
        // reload via ENT_PERSIST) by the time this branch is reached at all.
        // A same-frame "none found" reading here always means they've
        // genuinely all been defeated, never that they simply haven't
        // spawned yet.
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            // Checked against Main's own absolute world box (same bounds
            // used throughout this file for Main's offsets - world
            // (36,39)-(235,174)) rather than by enemy id: every wave now
            // rolls its enemies from the same shared random level pool as
            // Hall's ambient enemies (QuickStartSpawnHallEnemiesOnce), so an
            // id-based filter (this used to just check for OCTOROK, back
            // when wave 1 was always literally Octoroks) can no longer tell
            // "mine" apart from "Hall's" - only position still can.
            if (gEntities[i].base.kind == ENEMY && gEntities[i].base.x.HALF.HI >= 36 &&
                gEntities[i].base.x.HALF.HI <= 235 && gEntities[i].base.y.HALF.HI >= 39 &&
                gEntities[i].base.y.HALF.HI <= 174) {
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
