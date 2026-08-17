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
#include "effects.h"
#include "item.h"
#include "enemy.h"
#include "npc.h"
#include "object.h"
#include "object/itemOnGround.h"
#include "script.h"
#include "object/itemForSale.h"
#include "itemMetaData.h"
#include "script.h"
#include "kinstone.h"
#include "flags.h"
#include "tiles.h"
#include "map.h"
#include "vram.h"
// Not declared in ui.h (see QuickStartDrawDifficultyHUD's own comment) -
// plain non-static function, same as WriteSaveFile/MsgInit below.
void RenderDigits(u32, u32, u32, u32);
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
// --- QUICKSTART's own flag storage -----------------------------------------
//
// gSave.flags is 0x200 bytes = 4096 bits, carved into 13 "banks". A bank is
// just a base offset into that bit array (see enum LocalFlagOffsets,
// flags.h); CheckLocalFlagByBank(bank, n) reads absolute bit bank+n. Every
// AREA is assigned a bank in gAreaMetadata, and CheckLocalFlag/SetLocalFlag
// implicitly use whichever bank the CURRENT area was assigned - that's how
// vanilla lets many areas reuse small flag numbers without colliding.
//
// CheckGlobalFlag/SetGlobalFlag are simply "bank 0" - and bank 0 ends at
// bit 255, because FLAG_BANK_1 begins at 0x100. That matters a great deal
// here: QUICKSTART had been allocating its own state as "global" flags
// climbing from 101 upward and had reached 305, i.e. 50 bits PAST the end of
// bank 0 and directly on top of FLAG_BANK_1 - which gAreaMetadata assigns to
// 15 areas including AREA_HYRULE_FIELD, the overworld this entire mode is
// played in. Vanilla Hyrule Field local flags and QUICKSTART state were
// aliasing each other.
//
// So QUICKSTART's flags move out of bank 0 into a private window inside
// FLAG_BANK_12. Bank 12 is by far the largest (0xA80..0xFFF = 1408 bits).
// ORIGIN 700 puts the window at raw offsets 700-1407 (708 bits) for the
// flag numbers below, which run 101-707.
//
// The flag NUMBERS in that window are deliberately unchanged - only the
// accessor moved - so every GF_* definition, comment and bit-packing layout
// keeps its existing meaning. Vanilla progress flags (LV1_CLEAR, TABIDACHI,
// ZELDA_CHASE, ...) still go through the real CheckGlobalFlag/SetGlobalFlag
// and stay in bank 0, where the rest of the engine expects to find them.
//
// --- The whole of FLAG_BANK_12, one map ----------------------------------
//
// This bank is effectively QUICKSTART's: gAreaMetadata hands LOCAL_BANK_12
// to nothing but the eight Royal Crypt areas, a side dungeon this mode
// never enters (no region, pool room or content site names it - the
// invariant checker's "flags" tier asserts that, so it stays true).
//
//   raw 0            unusable - SetLocalFlagByBank drops offset 0 in every
//                    bank (flags.c reserves it as "no flag").
//   raw 1    - 793   the room-keyed content sites (GF_CONTENT_SITE_BASE),
//                    13 bits each, room for 61 sites. Raw-addressed, NOT
//                    through QsCheckFlag - see its own comment below.
//   raw 794  - 800   spare (the tail of the site block's ceiling).
//   raw 801  - 1407  the QUICKSTART window, i.e. QsCheckFlag offsets
//                    101-707. Everything else in this file lives here.
//
// Raw 0-585 used to hold GF_DOOR_*, 15 synthetic door entrances at 19 bits
// each that were all retired without their storage being reclaimed. That
// dead block is what the site block now occupies. Before that reclaim the
// sites lived at QsCheckFlag offsets 266-655, wedged between the region
// chain below them and the bridge/shop/Melari flags above, with room for
// exactly ONE more site - which is why adding the 31st was impossible until
// this move. Their old range, offsets 266-655, is free now.
//
// The rule this layout exists to enforce: no two blocks may overlap, and
// none may run past raw 1407. invariant_check.py's "flags" tier parses
// every GF_* define out of this file and asserts both, so the next person
// to grow a block finds out at check time instead of in play. (The last
// time this went wrong it was silent and nasty: at 25 sites, site 24's
// block started at exactly GF_NHF_BRIDGE_JOINED, so joining North Hyrule
// Field's bridge also marked the smithy site "already randomized" with an
// all-zero roll, and entering the smithy permanently joined the bridge.)
// Where the player stands in the hub's third-floor hall. Used by the initial
// spawn and by the two inter-phase repositions, which have to agree with it -
// they exist to move the player OFF the item row before the next row spawns,
// so a stale copy of this number would put them straight back on it.
#define QUICKSTART_HUB_SPAWN_X 120
#define QUICKSTART_HUB_SPAWN_Y 120

#define QUICKSTART_FLAG_ORIGIN 700

static bool32 QsCheckFlag(u32 flag) {
    return CheckLocalFlagByBank(FLAG_BANK_12, QUICKSTART_FLAG_ORIGIN + flag);
}

static void QsSetFlag(u32 flag) {
    SetLocalFlagByBank(FLAG_BANK_12, QUICKSTART_FLAG_ORIGIN + flag);
}

static void QsClearFlag(u32 flag) {
    ClearLocalFlagByBank(FLAG_BANK_12, QUICKSTART_FLAG_ORIGIN + flag);
}

// A little-endian run of `bits` flags starting at `base`, read and written as
// one number. Most of this file's multi-bit state (a pool index, a 3-bit
// price roll) open-codes this loop at its own site; the shop's prices are
// nine bits wide and there are eight of them, which is where open-coding
// stops being readable.
static s32 QsReadField(u32 base, s32 bits) {
    s32 b, value = 0;
    for (b = 0; b < bits; b++) {
        if (QsCheckFlag(base + b)) {
            value |= 1 << b;
        }
    }
    return value;
}

static void QsWriteField(u32 base, s32 bits, s32 value) {
    s32 b;
    for (b = 0; b < bits; b++) {
        if (value & (1 << b)) {
            QsSetFlag(base + b);
        } else {
            QsClearFlag(base + b);
        }
    }
}

// The content sites' own block sits BELOW the QUICKSTART window rather than
// inside it (see the bank map above), so it needs its own accessor - passing
// its offsets to QsCheckFlag would add ORIGIN 700 and land somewhere else
// entirely. Same bank, raw addressing.
//
// Origin 1, not 0: SetLocalFlagByBank (flags.c) is `if (flag != 0)
// WriteBit(...)`, i.e. vanilla reserves offset 0 in every bank as "no
// flag". A block based at 0 loses its first bit silently - measured, with
// the site block briefly based at 0: site 0's kind and extra bits wrote
// fine and its RANDOMIZED latch never stuck, so North Hyrule Field's fairy
// fountain re-rolled its contents on every single entry.
#define QUICKSTART_SITE_FLAG_ORIGIN 1

static bool32 QsCheckSiteFlag(u32 flag) {
    return CheckLocalFlagByBank(FLAG_BANK_12, QUICKSTART_SITE_FLAG_ORIGIN + flag);
}

static void QsSetSiteFlag(u32 flag) {
    SetLocalFlagByBank(FLAG_BANK_12, QUICKSTART_SITE_FLAG_ORIGIN + flag);
}

// A3's pin. Set it and the next run reuses gSave.run_seed verbatim instead
// of deriving a fresh seed, which makes a run reproducible turn for turn:
// same region chain, same shop, same "? room" contents, same fuser scatter.
//
// FLAG_BANK_11 offset 174, which is in that bank's uncleared tail alongside
// nothing else - deliberately, for the same reason GF_DIFFICULTY_BIT sits
// outside the run-start wipes. A pin that a new run cleared would pin
// nothing, since the pin's whole job is to survive into the next run.
// Declared up here rather than with the other GF_* blocks because
// GameTask_Transition, the only thing that reads it, is compiled above them.
#define GF_SEED_PINNED 174

// gRoomVars.flags is shared with whatever vanilla room logic runs in the
// room, and vanilla uses the low bits. That is not a theoretical hazard: in
// Dark Hyrule Castle's Triple Darknut room - a 2-door pool member - vanilla
// clears room flag 0 while the player is standing there, which wiped the
// "already spawned this visit" latch every kind of "? room" content relies
// on. The result was one fresh spawn per frame until the entity table
// saturated: 63 stacked reward items on the arrival tile (the player could
// not stop picking them up), 21 minibosses, 61 fairies. Reported by the
// user; reproduced by forcing the 2-door draw to that room, and confirmed
// with a counter showing CheckRoomFlag(0) reading false on 36 of 51 calls
// that had already set it.
//
// So QUICKSTART's own per-visit flags live in a private window instead,
// exactly like its global flags do (QUICKSTART_FLAG_ORIGIN above). Offsets
// used inside the window run 0..107 (the content sites' 64 + slot*8 windows,
// then the puzzle switches' 104..107 toggle bits - QS_SWITCH_HIT_FLAG), and
// gRoomVars.flags holds 416 bits, so an origin of 256 clears every plausible
// vanilla flag while leaving the top of the range unused.
#define QUICKSTART_ROOM_FLAG_ORIGIN 256

static u32 QsCheckRoomFlag(u32 flag) {
    return CheckRoomFlag(QUICKSTART_ROOM_FLAG_ORIGIN + flag);
}

static void QsSetRoomFlag(u32 flag) {
    SetRoomFlag(QUICKSTART_ROOM_FLAG_ORIGIN + flag);
}

static void QsClearRoomFlag(u32 flag) {
    ClearRoomFlag(QUICKSTART_ROOM_FLAG_ORIGIN + flag);
}

// Is the current room fully loaded and coherent - id, origin, room vars all
// describing the same room? Every QUICKSTART per-frame spawner/monitor that
// mixes gRoomControls.room, gRoomControls.origin_* and room flags must gate
// on this, because transitions tear those apart for a few frames:
//
//  - seam SCROLLS flip room id and origin mid-frame while scrollAction sits
//    at 2 and reload_flags at 1 (measured for the dojo dispatcher bug) -
//    the first two clauses catch those;
//  - border WALKS (including the town bridges) flip gRoomControls.room a
//    frame or two BEFORE the engine's room reset runs, while scrollAction
//    still reads the OLD room's settled 1 - measured on the Trilby -> Lon
//    Lon bridge, where the region monitor saw Lon Lon's room id with
//    Trilby's origin and Trilby's room flags and dropped the region reward
//    at wrong-origin coordinates on arrival. The tracker-pointer clause
//    catches that window exactly: sub_08052EA0 (the room reset that also
//    wipes gRoomVars) is what re-points gArea.pCurrentRoomInfo at the new
//    room's info via UpdateRoomTracker, so until it has run the pointer
//    still names the OLD room. Once it matches, the flags are known fresh
//    and the origin check below confirms the origin was refreshed too
//    (sub_0807BFA8 copies it from this very info record).
static bool32 QuickStartRoomSettled(void) {
    if (gRoomControls.reload_flags != 0 || gRoomControls.scrollAction != 1) {
        return FALSE;
    }
    if (gArea.pCurrentRoomInfo != &gArea.roomResInfos[gRoomControls.room]) {
        return FALSE;
    }
    if (gRoomControls.origin_x != gArea.pCurrentRoomInfo->map_x ||
        gRoomControls.origin_y != gArea.pCurrentRoomInfo->map_y) {
        return FALSE;
    }
    return TRUE;
}

static void QuickStartMakeNpcTalkable(Entity*, Script*);
static void QuickStartSpawnRegionFusers(void);
static void QuickStartTinglePayout(void);
static void QuickStartReloadRoomAfterFusion(void);
static void QuickStartSpawnStarterChoice(void);
static void QuickStartSpawnStarterChoiceOnce(void);
static void QuickStartRefreshItemTimers(void);
static void QuickStartRefreshPlacedItemTimers(void);
static void QuickStartDeleteGroundItemsAndSigns(void);
static void QuickStartUpdateItemChoice(void);
static void QuickStartUpdate(void);
static void QuickStartClearCastleGuards(void);
static void QuickStartShowRegionIntroHintOnce(void);
static void QuickStartClearMelarisMineObstacles(void);
static void QuickStartSpawnMelarisMineEnemiesOnce(void);
static void QuickStartSpawnMelarisMineRewardOnce(void);
static void QuickStartSpawnShopMerchantOnce(s16, s16);
static void QuickStartMaintainShop(const s16 (*)[2]);
static void QuickStartRandomizeMelariEastOnce(void);
static void QuickStartSetupMelariEastRoomContent(void);
static void QuickStartRandomizeMelariSoutheastOnce(void);
static void QuickStartSetupMelariSoutheastRoomContent(void);
static void QuickStartRandomizeSlotsOnce(void);
static void QuickStartSetupSlotRoomContent(s32);
static void QuickStart2DoorClearRoomObstacles(u8, u8);
static bool32 QuickStartIsBoomerangTree(u8, u8);
static void QuickStartEnforceContainment(void);
static void QuickStartEnforceLonLonContainment(void);
static void QuickStartEnforceFieldRegionContainment(void);
static void QuickStartClearLonLonRanchAnimals(void);
static void QuickStartProcessLinks(void);
static void QuickStartRollElementRegionOnce(void);
static s32 QuickStartCurrentRegionPoolIndex(void);
static s32 QuickStartElementRegionIndex(void);
static void QuickStartRegionMonitor(s32 position);
static void QuickStartRoomMonitor(void);
static bool32 QuickStartQuestSwapActive(void);
static bool32 QuickStartFindOpenTileNear(s32, s32, s32, s16*, s16*);
static bool32 QuickStartLeverAtTile(s32, s32);
void QuickStartMarkCatalogItem(u32);
static bool32 QuickStartPositionAllowed(s16, s16);
static bool32 QuickStartGfxBudgetForSpawn(void);
static s32 QuickStartFreeGfxSlots(void);
static s32 QuickStartReclaimableGfxSlots(void);
static void QuickStartApplyFoodEffects(void);
u32 QuickStartFoodMask(void);
static s32 QuickStart2DoorExitSide(void);
static bool32 QuickStart2DoorDoorSpot(s32, s16*, s16*);
static s32 QuickStartFindSiteAt(s32, s32);
static bool32 QuickStartTileBelongsToSite(s32, s32, s32);
static void QuickStartSiteContentSpot(s32, s16*, s16*);
static u8 QuickStartSiteRewardTier(s32);
static void QuickStartPotRoomGenerate(s32, s32, s32, s32);
static u8 QuickStartGetDifficulty(void);
static void QuickStartIncrementDifficulty(void);
static void QuickStartDrawDifficultyHUD(void);
static void QuickStart2DoorRandomizeOnce(void);
static void QuickStart2DoorSetupRoomContent(void);
static void QuickStartFixupCaveConnectorReturn(void);
static bool32 QuickStart2DoorIsCurrentRoom(void);
static void QuickStartRandomizeRiverBridgeOnce(void);
static void QuickStartSetupRiverBridgeRoomContent(void);
static void QuickStartProcessRiverBridgeLink(void);
static void QuickStartFixupRiverBridgeReturn(void);
static bool32 QuickStartRiverBridgeIsCurrentRoom(void);
static void QuickStartRandomizeCaveOnce(void);
static void QuickStartSetupCaveRoomContent(void);
static bool32 QuickStartCaveIsCurrentRoom(void);
static void QuickStartPickEnemy(u8, u8*, u8*);
static void QuickStartSpawnEnemyGroup(const s16 (*)[2], s32, s32, s32);
static void QuickStartSpawnEnemyGroupAtDifficulty(const s16 (*)[2], s32, s32, s32, u8);
static void QuickStartSpawnWinKeyOnce(s16, s16);
static void QuickStartCheckWinCondition(void);
static s32 QuickStartCountItemsHeld(void);
static u32 QuickStartComputeScore(void);
#endif

// The engine's RNG state (src/main.c). Reseeded per run in
// GameTask_Transition below - see the comment there for why that is
// necessary rather than cosmetic.
extern u32 gRand;

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
    // The hub's third floor - Home of the Wind Tribe. Measured, not guessed
    // (docs/QUICKSTART_HUB.md sec 2): the floor is 240x336 and its open hall
    // is rows 3-7 by columns 2-12, i.e. the pixel box (32,48)-(207,127).
    // Everything the item-selection phase places lives in that hall, stacked
    // vertically with 32px between rows so nothing is picked up by accident:
    //
    //     y=40    the sign NPC   (QuickStartSpawnStarterChoice)
    //     y=72    the item row   (sQuickStartItemOffsets)
    //     y=120   the player     (here)
    //
    // The item row moved up a tile and its three slots moved a tile closer
    // together (user's call, for how it reads on screen); the sign moved up
    // with it so it still stands clear of the middle item rather than
    // directly on top of it.
    //
    // The floor below the hall (rows 8-12) is the stair column alone, so
    // there is nowhere further south to stand - this is the bottom row.
    gRoomTransition.player_status.start_pos_x = QUICKSTART_HUB_SPAWN_X;
    gRoomTransition.player_status.start_pos_y = QUICKSTART_HUB_SPAWN_Y;
    gRoomTransition.player_status.layer = 1;
    // Every fresh boot is meant to be its own clean round - none of last
    // round's starter/bonus/skill choice, ladder/gauntlet reward pickups, or
    // heart pieces should carry over. Global flags (gSave.flags - the
    // difficulty counter, ladder assignments, EZERO_1ST, etc.) live in a
    // separate array and are untouched by this, but ownership itself
    // (gSave.inventory, 2 bits/item) persists across DoSoftReset same as
    // everything else in gSave. Left alone, last run's picks stay owned,
    // and `QuickStartTierEntryUsable` refuses any non-repeatable item the
    // player already has - so the three selection rounds would draw from a
    // pool that shrinks every run and eventually cannot fill a row, on top
    // of handing the player a loadout they never chose. Wiping it here, before any of the fixed starting gear below
    // gets (re-)granted, is simpler and more robust than re-clearing every
    // individual item/marker (ITEM_32/33/5A, all three choice categories,
    // every ladder-room reward) by hand.
    MemClear(gSave.inventory, sizeof(gSave.inventory));
    // The ladder pool's assignments (GF_SLOTS_RANDOMIZED=101 through the
    // last ladder's own block, 173) and the 2-door cave connector's own
    // draw (GF_2DOOR_RANDOMIZED=184 through GF_2DOOR_DONE=201) need to be
    // re-rolled every fresh boot too, same "no carry-over between rounds"
    // policy as everything else in this block - left alone (as the comment
    // above says gSave.flags generally is), both stayed pinned to whatever
    // they first rolled on the very first-ever QUICKSTART boot, unchanged
    // by any later DoSoftReset (reported by the user as the cave connector
    // "locked as a single room"). GF_DIFFICULTY_BIT (174-177), in the
    // middle of this same range, is deliberately skipped - it's the one
    // genuinely persistent meta-progression counter here, incremented by
    // QuickStartIncrementDifficulty on every win, not reset per round.
    {
        s32 bit;
        for (bit = 101; bit <= 173; bit++) {
            QsClearFlag(bit);
        }
        for (bit = 184; bit <= 201; bit++) {
            QsClearFlag(bit);
        }
        // 202-206: GF_SLOT_KIND_BIT2(0..3)/GF_2DOOR_KIND_BIT2, the 3rd kind
        // bit added for QS_EVENT_POT_LOTTERY/CHEST_LOTTERY/FAIRY, stored
        // outside the two contiguous blocks above since inserting it inline
        // would have shifted every bit after it (colliding with
        // GF_DIFFICULTY_BIT below). 207: GF_REGION_INTRO_HINT_SHOWN, same
        // "own the tail end of the free range" reasoning. 208-228: the
        // region chain's own randomized-once flag, pool-index-per-slot, and
        // reward-state-per-slot ranges - same "re-roll every fresh boot"
        // policy as the ladder/2door pools above. 229: GF_REGION_FINAL_HINT_SHOWN,
        // same one-per-run reasoning as GF_REGION_INTRO_HINT_SHOWN. 230-234:
        // Melari's Mine East room's own randomized-once/kind/extra bits.
        // 235: free (was GF_HEART_CONTAINER_BONUS_APPLIED). 241-265: the river
        // bridge and cave connector draws. 266-655: free (this is where the
        // room-keyed content sites used to live, before they moved down to
        // their own raw block at the bottom of the bank - see the bank map
        // at the top of this file; they are cleared separately below).
        // 656: the North Hyrule Field bridge. 657-689: the shop's own door
        // draw and price rolls. 692-698: which fusion this run has already
        // re-loaded its room for. 699-703: where this run scatters the
        // Kinstone fusers. 690-691: Melari's Mine's two rooms' collected
        // latches - re-rolled every fresh boot like everything else here, so a
        // new run gets the shop somewhere else at different prices.
        for (bit = 202; bit <= 703; bit++) {
            QsClearFlag(bit);
        }
        // Wipe every per-area LOCAL flag, so each run gets a fresh world.
        //
        // gSave.flags is one 4096-bit array carved into banks (flags.h,
        // gLocalFlagBanks). Bank 0 is the global flags - story progress, the
        // items and entrances this mode forces open at boot - and stays.
        // Everything from FLAG_BANK_1 (bit 0x100) up to the start of
        // QUICKSTART's own block is per-area state, and that is where the
        // world records what the player did to it: bombed walls, smashed
        // destructible tiles, opened chests, revealed portals, and (once they
        // are back) kinstone fusions. Vanilla wants those permanent. A
        // roguelite does not - a wall the previous run blew open should be
        // whole again, so the bombs still matter.
        //
        // Upper bound is exclusive of QUICKSTART's range: its flag n lives at
        // FLAG_BANK_12 (0xA80) + QUICKSTART_FLAG_ORIGIN (700) + n, i.e. bit
        // 3388 onward, and the loop above owns that.
        for (bit = FLAG_BANK_1; bit < FLAG_BANK_12 + QUICKSTART_FLAG_ORIGIN; bit++) {
            ClearGlobalFlag(bit); // bank 0 == raw bit index into gSave.flags
        }
        // The room-keyed content sites, whose block is FLAG_BANK_12 raw
        // 1..793 (GF_CONTENT_SITE_BASE - it is raw-addressed, below the
        // QUICKSTART window rather than inside it). They re-roll every
        // fresh boot for the same reason everything above does.
        //
        // The loop above ALMOST covers them - it sweeps absolute bits
        // 0x100..3387, and this block is absolute 2688..3480 - but it stops
        // at the start of the QUICKSTART window, which cuts the block off
        // at raw 699. The top ~7 sites would carry over. So clear the whole
        // block explicitly, sized to its ceiling (1 + 61 sites * 13 bits) and
        // not to the current count, so adding a site row stays a one-line
        // change. Literal rather than QUICKSTART_CONTENT_SITE_MAX * ...
        // because, like every other number in this block, the defines live
        // further down the file than GameTask_Transition does.
        for (bit = 0; bit < 794; bit++) {
            ClearLocalFlagByBank(FLAG_BANK_12, bit);
        }
        // (The old bank-11 142-173 wave-counter clear is gone with the
        // counters themselves - per-region wave state lives in the QS
        // window now, inside the 202-703 wipe above.)
        // Charms are run-long now (see QuickStartCharmMask), which means
        // nothing expires them - so the run boundary has to. Both the vanilla
        // single-charm byte, used for Link's palette tint, and our own
        // "which charms are owned" bits.
        gSave.stats.charm = 0;
        gSave.stats.charmTimer = 0;
        // Literal 32-42 rather than GF_QUEST_*/QUICKSTART_CHARM_BIT: like
        // every other number in this block, the defines live further down
        // the file than GameTask_Transition does.
        //
        // 32-39 is the pot quest (GF_QUEST_ROLLED through GF_QUEST_DONE),
        // which its own comment calls "one draw per run" but which nothing
        // was actually clearing - the old bank 11 wipes covered 0-31 and
        // 40-141 and stepped straight over it. So the quest was pinned to
        // whatever it rolled on the first-ever run, and once GF_QUEST_DONE
        // latched it stayed latched: the quest disappeared from every run
        // after the one that completed it. Found by the invariant checker's
        // flags tier, which now asserts every per-run bit in this bank is
        // covered by one of these loops.
        for (bit = 32; bit <= 42; bit++) {
            ClearLocalFlagByBank(FLAG_BANK_11, bit);
        }
        // Bits 43-58: the live wave-gauntlet record (GF_SEAM_GAUNTLET_*).
        // A run that ends mid-gauntlet must not leave the next one thinking
        // some room already has a fight in progress in it.
        // Bits 59-73: the handicap record (GF_HANDICAP_*).
        // Bits 74-84: the hunt quest (GF_HUNT_*), which is one attempt per
        // run, so a new run has to get its attempt back.
        // Bits 85-88: the hub item-selection phase mirror (GF_HUB_PHASE_BIT).
        // Stale bits here would tell the next run it had already picked its
        // item and skip the whole selection.
        // Bits 89-96: the roof wave's state (GF_ROOF_STATE_BIT) and the seed
        // its reward is drawn from (GF_ROOF_SEED_BIT), so each run gets its
        // own rooftop fight and its own reward.
        // Bits 97-141: the shop's drawn stock, five bits per shelf slot
        // (GF_SHOP_SLOT_BIT). Cleared with the rest so a new run redraws -
        // GF_SHOP_RANDOMIZED, the latch that decides whether to redraw at all,
        // lives in the QUICKSTART flag window and is cleared by the 202-703
        // loop further up.
        for (bit = 43; bit <= 141; bit++) {
            ClearLocalFlagByBank(FLAG_BANK_11, bit);
        }
        // The hunt clock and the handicap snapshot. Clearing the ACTIVE bit
        // above is what actually ends a handicap, but leaving a stale
        // snapshot behind would hand the next run a pile of free items the
        // first time anything called QuickStartHandicapRestore.
        gSave.timer4 = 0;
        gSave.timer5 = 0;
        gSave.timer6 = 0;
    }
    // --- Reseed the RNG for this run ------------------------------------
    //
    // THE reason two runs looked identical. gRand is set to the literal
    // 0x1234567 in AgbMain (src/main.c) and never touched again, and
    // DoSoftReset - which is how a won run starts the next one - goes back
    // through AgbMain, so every run began from the same RNG state. Every
    // per-run draw then compounds it: they are all rolled unconditionally
    // from QuickStartRoomMonitor, which first runs on frame ONE, before the
    // player has pressed anything, so QuickStartStirRandom (one extra
    // Random() per input frame) has had nothing to stir. Same region chain,
    // same shop, same prices, same "? room" contents, every single run.
    // Reported by the user about the shop specifically; the shop was just
    // the most visible instance.
    //
    // Mixed from state that survives a soft reset and genuinely differs run
    // to run: a persistent 6-bit run counter, plus the previous run's length
    // and kill counts (read here, before the resets below zero them). The
    // very first run on a brand-new save is still fixed - nothing has
    // happened yet to vary - which is fine, and arguably good for a first
    // impression. Every run after it differs.
    //
    // Bits 178-183 are the counter. They sit in the gap between
    // GF_DIFFICULTY_BIT (174-177) and the 184-201 clear loop, so no run-start
    // clear touches them, which is exactly the property needed.
    //
    // A3, the fixed-seed playtest switch. Whatever this block decides, the
    // seed it settles on is written to gSave.run_seed - so every run is
    // identifiable after the fact, from a save file alone, without anyone
    // having had to turn anything on first. That is the half that makes a
    // user's bug report reproducible: they send the .sav, the seed is in it.
    //
    // And if FLAG_BANK_11 bit 174 (GF_SEED_PINNED) is set, the derivation is
    // skipped entirely and run_seed is used as-is. Both halves therefore run
    // through one field: it records the seed normally, and dictates it when
    // pinned. The pin bit lives in bank 11's uncleared tail, beside the
    // difficulty counter's own reasoning - a pin that a new run wiped would
    // pin nothing.
    //
    // The record happens AFTER the stirring below, not before, so the value
    // stored is exactly the gRand the run actually starts from and the
    // pinned path can restore it with no further mixing. Storing the
    // pre-stir value would make the two paths diverge by eight turns of the
    // generator, which is the kind of thing that looks like it works.
    if (CheckLocalFlagByBank(FLAG_BANK_11, GF_SEED_PINNED)) {
        gRand = gSave.run_seed;
    } else {
        u32 counter = 0;
        s32 b;
        for (b = 0; b < 6; b++) {
            if (QsCheckFlag(178 + b)) {
                counter |= (1u << b);
            }
        }
        counter++;
        for (b = 0; b < 6; b++) {
            if (counter & (1u << b)) {
                QsSetFlag(178 + b);
            } else {
                QsClearFlag(178 + b);
            }
        }
        // Knuth's multiplicative constant, then a few turns of the engine's
        // own generator so the low bits - which is all most draws look at,
        // via `% n` on a small n - are properly mixed rather than tracking
        // the counter.
        gRand ^= counter * 2654435761u;
        gRand += gSave.run_frames + gSave.enemies_killed * 7 + gSave.miniboss_kills * 131 +
                 gSave.boss_kills * 1009;
        for (b = 0; b < 8; b++) {
            Random();
        }
        gSave.run_seed = gRand;
        // And commit the counter, because otherwise it does not survive.
        // gSave lives in EWRAM but InitSaveData reloads it from SRAM on every
        // boot - including the soft reset a won run ends with - so a counter
        // that is only incremented in RAM is thrown away the moment the run
        // ends. Measured: without this, three soft resets in a row produced
        // three identical runs. The win path already calls WriteSaveFile at
        // exactly this level (QuickStartCheckWinCondition), so the cost is one
        // more save write per run, on a mode whose runs last minutes.
    }
    // Outside the if: the pinned path writes no counter but still wants the
    // save flushed, and the unpinned path's run_seed is only useful if it
    // reaches SRAM.
    WriteSaveFile(gSaveHeader->saveFileId, &gSave);
    gSave.stats.heartPieces = 0;
    // Unlike maxHealth/health/inventory just below, rupees was never reset
    // here - confirmed via emulator testing (dirty rupees to a known value,
    // play through a full win, check after DoSoftReset) that it carries
    // over from the previous run otherwise. Every run starts broke.
    gSave.stats.rupees = 0;
    // 2 hearts to start, per the user's own request (was 3) - a full heart
    // is 8 health units in this engine (see the ITEM_HEART_CONTAINER comment
    // on phase 3's bonus-reward handling below, and DrawHearts/ui.c:
    // gHUD.maxHealth = gSave.stats.maxHealth/2, itself in quarter-heart
    // units).
    gSave.stats.maxHealth = 16;
    gSave.stats.health = gSave.stats.maxHealth;
    // Run-scoped scoring counters (see docs/QUICKSTART_ROADMAP.md) - all
    // reset to 0 here so each run's score reflects only that run. meta_xp
    // and runs_completed are the one exception: they're the persistent
    // meta-progression currency the score feeds into at each win
    // (QuickStartCheckWinCondition), and must NOT be touched here.
    gSave.run_frames = 0;
    // Must be reset alongside run_frames: the stuck-wave failsafe compares
    // the two, and a stale value left over from the previous run would make
    // that difference enormous the moment run_frames restarts at 0.
    gSave.final_wave_frame = 0;
    gSave.enemies_killed = 0;
    gSave.miniboss_kills = 0;
    gSave.boss_kills = 0;
    // Bomb bag/quiver capacity and current ammo count - like the equip
    // slots just below, these are never touched by the inventory-ownership
    // MemClear above (they're separate Stats fields, not inventory bits),
    // so a Large Quiver/Bomb Bag upgrade found on one run silently carried
    // its capacity (and whatever ammo count) into the next. Zeroed here so
    // ammo capacity/count only ever comes from what's actually picked up
    // this run, same as the starting Bombs/Bow/Boomerang choice already
    // grants via the real GiveItem path.
    gSave.stats.bombBagType = 0;
    gSave.stats.bombCount = 0;
    gSave.stats.quiverType = 0;
    gSave.stats.arrowCount = 0;
    gSave.stats.equipped[SLOT_A] = ITEM_SHIELD;
    // Level 1 on purpose. Upgrading to ITEM_RED_SWORD does make
    // SurfaceAction_CloneTile hand out one clone (player.c switches on the
    // equipped sword: Smith's and Green give zero, Red one, Blue two, Four
    // Sword three), but the sword is only half of it - the duplication
    // technique also needs the spin-attack skill scroll, which this mode
    // does not grant either. Giving the sword alone bought nothing, so the
    // clone-block puzzles stay unsolvable for now and the whole mechanic is
    // parked on the roadmap rather than half-wired here.
    gSave.stats.equipped[SLOT_B] = ITEM_SMITH_SWORD;
    // L item slot starts empty. It used to hold the Bow, back when the Bow
    // was free gear; now that bow, arrows and bombs are all things the run
    // has to find, there is nothing to put here at boot.
    gSave.stats.equippedExtra[0] = ITEM_NONE;
    // Start with every wallet upgrade already owned (walletType 3 ==
    // gWalletSizes[3] == 999 rupee cap, itemUtils.c). walletType is the
    // field gameplay actually reads (gWalletSizes[walletType].size, see
    // gameUtils.c/ui.c) - it's separate from the inventory-ownership bit
    // GetInventoryValue(ITEM_WALLET) tracks, which nothing here needs to
    // touch (ITEM_WALLET stays in the "? room" chest reward pool - GiveItem
    // just bumps walletType again if it's ever picked up a second time,
    // same as any other wallet upgrade, capped at 3 either way).
    gSave.stats.walletType = 3;
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
    // The Fire Rod and Light Arrow used to be pre-granted here for testing.
    // Both are droppable now (WEAPON/TOOL, see docs/QUICKSTART_ITEM_TIERS.md),
    // so handing them out at boot would defeat the point.
    //
    // Note for whoever adds the Fire Rod to a drop table: it shares
    // MENU_SLOT_CANE with the Cane of Pacci (itemMetaData.c). That is our own
    // doing, not vanilla's - the rod ships with menuSlot 0x63, the "not on
    // the grid" sentinel, and was given the cane's cell precisely because the
    // cane was never granted. The item grid has twelve cells and all twelve
    // are spoken for, so the fix is not a new cell: it is making the two
    // mutually exclusive in the roll.
    // The Bow and its arrows are no longer free. They are WEAPON/TOOL drops
    // and shop stock now, so a run that wants a ranged option has to find or
    // buy one.
    // ITEM_FLIPPERS is no longer a free grant - it's one of the round-1
    // key-item choices now (QS_CAT_KEY in the tier table), and the point of
    // that round is that owning it (or not) actually changes which region
    // the run's chain routes through (QuickStartRandomizeRegionChainOnce).
    // Bombs are no longer free either, same reasoning as the Bow above.
    // The Gust Jar used to be granted here, because peeling CHUCHU_BOSS was
    // the one thing nothing else could do and that boss rolls into every
    // region's wave loop. It is an uncommon WEAPON/TOOL drop now like
    // everything else - conventional weapons peel the jelly too, see
    // sub_08027AA4 in chuchuBoss.c.
    // The hub's own windcrest, revealed from the start so the player can warp
    // home from anywhere. gUnk_08128024 (src/menu/kinstoneMenu.c) is the
    // eight-row fast-travel table and gSave.windcrests bits 24-31 are its
    // availability flags, one per row in order; Cloud Tops is row 2, so bit
    // 26. Its destination in that table is (0x1e8,0x1a8) = (488,424), which
    // is exactly where the WINDCREST object stands in the room - so the warp
    // lands on the crest itself with no new data needed.
    gSave.windcrests |= 1 << 26;
    // North Hyrule Field's boomerang cave: the ladder in the middle of the
    // four tree entrances is vanilla's own four-torch puzzle - light one torch
    // in each of the four Boomerang tree rooms and the ladder appears
    // (sub_StateChange_Caves_Boomerang, roomInit.c, keyed on
    // SOUGEN_06_HASHIGO). A RARE drop sits at the bottom of it.
    //
    // That flag is a BANK-0 global, and the per-run wipe below starts at
    // FLAG_BANK_1 - deliberately, because bank 0 is where the meta layer and
    // this file's own boot grants live. So the ladder stayed open for every
    // later run: light the torches once, and the rare drop is a free walk down
    // a hole from then on. Reported by the user.
    //
    // Cleared here so the puzzle has to be solved again each run. The torches
    // themselves need nothing - they are ordinary room-local flags in Tree
    // Interiors' own bank, which the FLAG_BANK_1..12 wipe already resets.
    ClearGlobalFlag(SOUGEN_06_HASHIGO);
    // The Ocarina of Wind, granted at boot per the user's request, so the
    // hub's shop, inn and roof are reachable from anywhere in the run rather
    // than only on the way out. It does NOT need removing from the tier table:
    // QuickStartTierEntryUsable already refuses any non-repeatable item the
    // player already owns, and the ocarina's row is non-repeatable, so it
    // simply stops being drawable - including by round 1 of the opening
    // selection, which draws the whole QS_CAT_KEY category and so would
    // otherwise offer a "choice" the player already holds.
    //
    // Where it takes the player is fixed - see Subtask_FastTravel_0
    // (src/subtask/subtaskFastTravel.c), which skips the crest-picking map
    // entirely under QUICKSTART.
    SetInventoryValue(ITEM_OCARINA, 1);
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
    // Kinstone bag, granted at boot per the user's request - without it
    // owned, NPCs offering a fusion simply can't be interacted with
    // (kinstone.c gates the fusion prompt on GetInventoryValue(ITEM_KINSTONE_BAG)),
    // so any "? room" NPC/kinstone-fusion content would otherwise be
    // silently unusable from the very first run.
    SetInventoryValue(ITEM_KINSTONE_BAG, 1);
    // Nine gates used to be force-fused right here, as a stopgap so their
    // doors stood open with no way for the player to open them. The fusion
    // economy replaces that: they are earned back through a placed fuser
    // now (sQuickStartFusers / QuickStartSpawnRegionFusers).
    //
    // Nothing else was ever pre-fused in this mode. The blanket "fuse all
    // 100" pass lives in the MAPEXPLORE branch below - it is a dev mode for
    // walking a finished world - so with those nine gone, a QUICKSTART save
    // starts with the entire fusion table clear on its own.
    //
    // Except across runs. gSave.kinstones is not part of gSave.flags, so the
    // per-run world reset above does not touch it: fuse a gate in run 1 and
    // it would still be open in run 2, and the pieces would still be in the
    // bag. Wipe the whole block per run, same "no carry-over between rounds"
    // policy as rupees, hearts and the inventory.
    //
    // (tools/quickstart/kinstone_audit.py enumerates which fusions actually
    // change a room this mode visits - 29 of the 91 that have a world event
    // at all, of which the 18 that open a gate or place a chest have fusers.)
    MemClear(&gSave.kinstones, sizeof(gSave.kinstones));
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
    // "Met Zelda" - the flag the whole opening sequence hangs off. Without
    // it the game still believes the run is in its first five minutes, which
    // is what made Link's House unusable: the entrance and the smithy each
    // load a cutscene-only entity list (roomInit.c,
    // sub_StateChange_HouseInteriors2_LinksHouseEntrance/Smith), and the
    // bedroom runs script_PlayerIntro outright, which is why the stairs
    // appeared to dump the player back downstairs. One flag fixes all three.
    SetGlobalFlag(START);
    // Pre-grant one empty bottle. GiveItem's bottle-fill path (itemUtils.c)
    // only fills a slot already marked empty (0x20) and silently does
    // nothing otherwise, so anything that arrives bottled needs this to
    // exist first. Originally it was here for the fixed Red Potion the
    // second selection round used to offer; now that round draws the rare
    // REWARD/STAT band, and this one bottle is what makes four of its six
    // entries - the bottled fairy and the three charms - drawable at all.
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
    // (584, 264): the actual "arrive from Town's south gate" landing point
    // for this room, taken from its WARP_TYPE_AREA transition entry
    // (screenTransitions.c). The previous (504, 872) was well past this
    // room's own bounds (width 1008, height 688 - see gRoomControls at
    // runtime), placing Link 184px south of the room's bottom edge, which is
    // why the camera clamped at the room's southern edge and never centered
    // on him: the "target" itself is outside the room the clamp is built for.
    gRoomTransition.player_status.start_pos_x = 584;
    gRoomTransition.player_status.start_pos_y = 264;
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
    // Boots on the L slot (fastest way to cover ground while mapping the
    // overworld).
    gSave.stats.equipped[SLOT_A] = ITEM_MIRROR_SHIELD;
    gSave.stats.equipped[SLOT_B] = ITEM_FOURSWORD;
    gSave.stats.equippedExtra[0] = ITEM_PEGASUS_BOOTS;

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
    // NOT didAllFusions, despite the 100 above. That field is not just a
    // menu counter: itemUtils.c's drop roll applies DROPTABLE_NO_KINSTONES
    // whenever it is set, which suppresses kinstone drops from every enemy
    // in the game. It was set here as part of the "pretend the save is
    // complete" block, and it is why enemies dropped no pieces at all -
    // measured: six waves killed in South Hyrule Field produced zero
    // kinstone drops and an empty bag.
    //
    // The fusion economy needs the supply side working, so it stays clear.
    // The 100 fused bits above are kept: they are what holds the overworld
    // in its post-fusion shape (roomInit.c gates dozens of bridges, NPCs
    // and obstacles on CheckKinstoneFused), and MAPEXPLORE is a dev mode for
    // walking a finished world, not for playing the fusion economy - that
    // lives in the QUICKSTART branch above.
    gSave.kinstones.didAllFusions = 0;
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
    // Now that the region pool includes real overworld Hyrule Field rooms
    // (not just Castle Garden/Lon Lon Ranch), the same early-game state that
    // ZELDA_CHASE covers above also affects those rooms directly:
    // sub_StateChange_HyruleField_SouthHyruleField (roomInit.c) still loads
    // the opening Zelda/Smith escort cutscene entity list and does an
    // instant black/white fade without SOUGEN_01_ZELDA, and other Hyrule
    // Field rooms gate their own decorations on gSave.global_progress. Set
    // global_progress to 9 (the same "everything done" value MAPEXPLORE
    // uses, see below) and SOUGEN_01_ZELDA so every field region loads in
    // its ordinary state instead of the festival-day intro state.
    //
    // Deliberately NOT setting TABIDACHI ("Talked to Daltus and Smith"),
    // unlike MAPEXPLORE: it only buys correct BGM in South Hyrule Field (a
    // cosmetic wrong-music-cue issue), but CheckGlobalFlag(TABIDACHI) also
    // gates sub_StateChange_HyruleField_LonLonRanch's own
    // LoadRoomEntityList(&gUnk_080F7810) call - confirmed in the emulator
    // that setting TABIDACHI adds 10 extra native entities to Lon Lon
    // Ranch's room (kind=ENEMY, counted by QuickStartRegionWaveCleared),
    // pushing its already-verified wave count from 26 to 36. Not worth
    // breaking an existing, working region over a music cue.
    gSave.global_progress = 9;
    SetLocalFlagByBank(FLAG_BANK_1, SOUGEN_01_ZELDA);
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
extern Script script_QuickStartHunt;
extern Script script_QuickStartScav;

// Per-run (not per-visit, not permanent) - "has the region-intro Ezlo hint
// already been shown this run". Only the run's first overworld region ever
// sets this (see QuickStartShowRegionIntroHintOnce) - re-entering that same
// region, or any later region, must not re-trigger it, but a fresh run
// should see it again. Global flag rather than a room flag since Castle
// Garden Main can be freely left and re-entered many times in one run.
// Declared up here (rather than alongside the rest of this file's GF_*
// flag constants, much further down) purely so QuickStartShowRegionIntroHintOnce
// below - itself placed early, next to the Castle Garden functions it
// belongs with - can see it; picks up right after GF_2DOOR_KIND_BIT2 (206),
// the highest bit allocated down there, and is cleared every run in
// GameTask_Transition alongside the ladder/2door ranges.
#define GF_REGION_INTRO_HINT_SHOWN 207

// RETIRED: the ordered region chain (QUICKSTART_REGION_CHAIN_MAX,
// GF_REGION_CHAIN_RANDOMIZED 208, POOL_BIT 209-220, REWARD_STATE 221-228 -
// all free now). The run is a free-roam hunt instead: every pool region is
// live every run, and ONE of them, drawn per run, hides the Earth Element -
// see GF_ELEMENT_REGION_* further down with the per-region state block.

typedef struct QuickStartRegion_ {
    u8 area;
    u8 room;
    // Landing spot when warped in via the region-chain portal (see
    // QuickStartProcessRegionChainLinks) - not necessarily either real
    // door's own vanilla landing point, just a confirmed-safe spot in this
    // room.
    s16 entranceX;
    s16 entranceY;
    // This region's own "onward" trigger box (local coordinates) - reused
    // verbatim from whichever real door/box already continues the fixed
    // Castle Garden -> Lon Lon Ranch sequence today; only the box's
    // destination becomes dynamic (whichever region is next in this save's
    // chain), not its position.
    //
    // The box MUST lie inside the room's own pixel bounds
    // (gRoomControls.width/height), and it must beat the room's real border
    // transition to the punch, which means not sharing the outermost pixel
    // row. Lon Lon Ranch's box was (287-343, 966-984) in a 720x960 room -
    // entirely past the bottom edge, so no amount of walking could put the
    // player inside it, and it only ever fired on the frames a border
    // transition carried his coordinates past the edge. Measured bounds:
    // Castle Garden 1008x528, Lon Lon Ranch 720x960, South Hyrule Field
    // 1008x688, North Hyrule Field 1008x800, Trilby Highlands 480x960.
    s16 exitMinX;
    s16 exitMaxX;
    s16 exitMinY;
    s16 exitMaxY;
    const s16 (*enemyOffsets)[2];
    s32 enemyOffsetCount;
    s32 roomSquares;
    s32 maxEnemies;
    // Reward pool for whenever this region ISN'T the chain's last slot -
    // the last slot drops an Earth Element and triggers the win condition
    // instead (see QuickStartSpawnRegionRewardOnce), same as Lon Lon Ranch
    // always has today. Also where the Chuchu Boss (one of the possible
    // endless-wave rolls, QuickStartSpawnRegionWave) and each wave's
    // enemy group both spawn/center.
    s16 rewardX;
    s16 rewardY;
    // Optional per-region "quirk" logic that doesn't fit the generic shape
    // (Lon Lon Ranch's boulder puzzle + Goron/animal removal, Castle
    // Garden's guard removal) - called unconditionally every frame this
    // region is current, same as those functions already run today.
    void (*quirkHook)(void);
} QuickStartRegion;

typedef struct {
    u16 itemId;
} QuickStartItemChoice;

#define QUICKSTART_ITEM_CHOICES 3

// RETIRED: three hardcoded 3-to-5 entry arrays (sQuickStartKeyItems,
// sQuickStartBonusItems, sQuickStartSkillItems). Every hub round now draws
// from the one tier table further down this file - see
// QuickStartSpawnChoiceRow, and the three QUICKSTART_CHOICE_ROW_* masks
// beside it that say what each round may offer. The old arrays had drifted
// out of sync with that table (the key-item array listed 5 of its 9
// QS_CAT_KEY entries, so the Cane of Pacci, the Grip Ring and the Power
// Bracelets could never open a run) and rounds 2 and 3 were not randomized
// at all: the same heart container / 100 rupees / red potion and the same
// three skills, every single run.

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
// Same idea as QuickStartGroundItemAt below, but matched on the item's form
// rather than its position.
//
// The pot room needs this because it cannot name a position. Its layout is
// generated from the room's own collision map, and a pot WRITES collision
// while it stands - so re-running the generator on a later frame to find out
// where the winning pot went counts a completely different set of open cells
// and lands somewhere else. Matching the prize by form sidesteps the whole
// problem: the room's plain pots are form 0xFF (they drop nothing) and its
// trap pots spawn bombs rather than ground items, so the only GROUND_ITEM
// wearing a reward-pool form is the prize. Safe against enemy drops too -
// The tier table's REWARD rows are heart pieces, rupees and bottles, and
// ITEM_RUPEE200, none of which a bob-omb ever leaves behind.
static bool32 QuickStartGroundItemOfForm(u16 form) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM && ent->type == form &&
            QuickStartEntityInCurrentRoom(ent)) {
            ((ItemOnGroundEntity*)ent)->unk_6c = 600;
            return TRUE;
        }
    }
    return FALSE;
}

// Is the player standing close enough to a room-local spot to have just
// picked something up off it? A tile and a half either way - generous enough
// that the pickup animation's own drift cannot fail the test, tight enough
// that a player across the room cannot pass it.
#define QUICKSTART_PICKUP_RADIUS 24
static bool32 QuickStartPlayerNearSpot(s16 offsetX, s16 offsetY) {
    s32 dx = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) - offsetX;
    s32 dy = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) - offsetY;
    if (dx < 0) {
        dx = -dx;
    }
    if (dy < 0) {
        dy = -dy;
    }
    return dx <= QUICKSTART_PICKUP_RADIUS && dy <= QUICKSTART_PICKUP_RADIUS;
}

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

// RETIRED: Castor Darknut Main's and Hall's enemy waves.
//
// Main was the item-selection room and Hall the one-wave gate south of it,
// back when the run started in Castor Darknut. The hub moved to Home of the
// Wind Tribe and, per the user, "after item selection, no enemies spawn" -
// so the three Main waves (QuickStartSpawnEnemies/Wave2/Wave3, a fixed
// Darknut mini-boss among them), Hall's ambient Octoroks, and the 35-spot
// offset table they all shared are gone. Nothing routes into either room any
// more; the roof wave is what replaces them in the hub design.


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

// Called every frame in whichever room is the run's first overworld region
// (today, always Castle Garden Main) - fires exactly once per run, the
// first frame the player is ever in that room. GF_REGION_INTRO_HINT_SHOWN
// is a per-run (not per-visit) global flag: unlike the room-flag-gated
// hints elsewhere in this file, this must not repeat on every re-entry into
// the same region, only once each run, however many times the player
// wanders in and out. When regions are generalized/randomized
// (docs/QUICKSTART_ROADMAP.md secs 3.1/3.2), this same call just needs to move
// to wherever "region position 1 this run" resolves to - it's independent
// of which physical region that turns out to be.
static void QuickStartShowRegionIntroHintOnce(void) {
    if (QsCheckFlag(GF_REGION_INTRO_HINT_SHOWN)) {
        return;
    }
    QsSetFlag(GF_REGION_INTRO_HINT_SHOWN);
    CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 10), 0);
}

// Same one-per-run shape as QuickStartShowRegionIntroHintOnce above, but
// fired on first entry to the chain's LAST slot instead of its first -
// per the user's own feedback ("I haven't seen [the Earth Element] in
// other areas, even after defeating full waves of enemies"): the actual
// mechanic is simple and deterministic (the Earth Element always drops the
// moment the FIRST wave in this one specific region - the chain's last
// slot - is cleared, no RNG, no boss requirement), but nothing in-game
// ever said so, and every other region a player might grind endless waves
// in in the meantime (this session's own new infinite-wave system) will
// never drop it no matter how long they stay. This hint directly names
// the trigger the moment the player reaches the region where it's real.
#define GF_REGION_FINAL_HINT_SHOWN 229
static void QuickStartShowRegionFinalHintOnce(void) {
    if (QsCheckFlag(GF_REGION_FINAL_HINT_SHOWN)) {
        return;
    }
    QsSetFlag(GF_REGION_FINAL_HINT_SHOWN);
    CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 12), 0);
}

// Melari's Mine's other 2 real doors (Southeast/East - see
// gExitList_MelarisMine_Main, transitions.c) were sitting completely
// unused under QUICKSTART until now - per the user's own request, each
// gets a random "?" room event assigned once per run, with no pool-draw
// indirection needed (the real door already leads there for real). Both
// rooms use the same shape: a genuine random pick between the two
// simplest existing "?" room kinds (chest / talking NPC) - the other
// kinds (miniboss/waves/fairy/lotteries) either need more room than these
// small interiors have (this session's own "combat needs big rooms"
// rule) or the slotIndex-keyed state these standalone rooms don't have.
// Southeast was originally hardcoded to always be a guaranteed Shop, but
// the user later pointed out Melari's Mine already has a real shop (Door
// 3, retargeted to Dojos Grimblade) - a second, forced one here was
// redundant, so Southeast was changed to this same randomized-kind
// pattern East already used.
#define GF_MELARI_EAST_RANDOMIZED 230
#define GF_MELARI_EAST_KIND_BIT 231 // 0 = chest, 1 = NPC
#define GF_MELARI_EAST_EXTRA_BIT(b) (232 + (b)) // b = 0..2, chest reward index or NPC script index
// 235 is free: it used to be GF_HEART_CONTAINER_BONUS_APPLIED, the latch
// for a manual Heart Container maxHealth grant that turned out to be
// double-counting vanilla's own (see QuickStartUpdateItemChoice's phase 3).
#define GF_MELARI_SOUTHEAST_RANDOMIZED 236
#define GF_MELARI_SOUTHEAST_KIND_BIT 237 // 0 = chest, 1 = NPC
#define GF_MELARI_SOUTHEAST_EXTRA_BIT(b) (238 + (b)) // b = 0..2, chest reward index or NPC script index

// North Hyrule Field's river-crossing 2-door bridge - a SEPARATE draw from
// the ladder pool from Lon Lon Ranch's own 2-door connector (GF_2DOOR_*
// above), reusing the same sQuickStart2DoorSmallRoomPool/LargeRoomPool room
// list but with its own room-index draw (excluded from colliding with
// whichever room Lon Lon Ranch's own connector already claimed - see
// QuickStartRandomizeRiverBridgeOnce). Unlike Lon Lon Ranch's connector
// (effectively one-sided - see QuickStartFixupCaveConnectorReturn's own
// comment), this one is a genuine two-sided bridge: two distinct real
// ladders (280,238) and (120,238), the user's own walked/found positions on
// either bank of the river cutting through the room, both wired to the
// SAME pool room. GF_RIVER_ENTERED_FROM_B is the one piece of state that
// can't be a room flag (it has to survive the load into the pool room
// itself, whose own room flags don't exist until that room is current) -
// set right when either entrance trigger fires, read back by
// QuickStartFixupRiverBridgeReturn to send the player out the side they
// DIDN'T enter from, regardless of which of the room's 2 real doors they
// physically use to leave.
#define GF_RIVER_RANDOMIZED 241
#define GF_RIVER_POOL_BIT 242
#define GF_RIVER_ROOM_BIT(b) (243 + (b)) // b = 0..4
#define GF_RIVER_KIND_BIT 248 // 0 = chest, 1 = NPC
#define GF_RIVER_EXTRA_BIT(b) (249 + (b)) // b = 0..2
#define GF_RIVER_DONE 252
#define GF_RIVER_ENTERED_FROM_B 253

// North Hyrule Field's other new entrance - a real cave mouth at (264,304),
// one-sided like Lon Lon Ranch's own cave connector (no second physical
// side given for this one, so no GF_CAVE_ENTERED_FROM_B-style tracking
// needed): walking up to it draws a third independent room from the same
// 2-door pool (excluded from whichever rooms the connector above and the
// river bridge already claimed), and leaving via that room's own real
// door(s) always lands back at the same fixed, walkable spot just south of
// the cave mouth (264,344) - confirmed in the emulator: open ground in
// every direction, walking back north re-enters the cave's own trigger box.
// Where that mouth actually leads. See QuickStartCaveGetTarget for why this
// is a fixed room now rather than a pool draw.
#define QUICKSTART_CAVE_AREA AREA_CAVES
#define QUICKSTART_CAVE_ROOM ROOM_CAVES_TO_GRAVEYARD

#define GF_CAVE_RANDOMIZED 254
#define GF_CAVE_POOL_BIT 255
#define GF_CAVE_ROOM_BIT(b) (256 + (b)) // b = 0..4
#define GF_CAVE_KIND_BIT 261 // 0 = chest, 1 = NPC
#define GF_CAVE_EXTRA_BIT(b) (262 + (b)) // b = 0..2
#define GF_CAVE_DONE 265

// --- PILOT: room-keyed "? room" content sites ------------------------------
//
// The generalization of what Melari's Mine East/Southeast already do by
// hand, and the core of the vanilla-doors-with-randomized-contents model:
// instead of rerouting a door to a randomly drawn room, the door is left
// exactly as vanilla built it and the ROOM it leads to gets a randomized
// event spawned inside it. Keyed by (area, room) rather than by an
// entrance index, so a room's content is a property of the room itself -
// which is what makes the door count and the room count independent.
//
// 13 bits per site: 1 randomized latch + 3 kind bits + 8 extra bits + 1
// done latch, laid out contiguously so adding a site is +13 bits and one
// table row.
//
// This started out as 8 bits (1 kind bit, 3 extra bits) because the pilot
// only ever rolled chest-or-NPC. It has to carry the full roll now: with
// the last 5 synthetic entrances retired, content sites are the ONLY way a
// single-door "? room" gets its contents, so they need the same 7-kind
// vocabulary the retired ladder/door slots had (QS_EVENT_*: chest,
// miniboss, npc, waves, pot lottery, chest lottery, fairy) - 3 kind bits -
// and the same 8-bit extra, which the pot lottery needs in full (it packs
// a 0-8 winner slot plus a prize index, see QuickStartPickPotRoomExtra).
// Anything narrower would have silently deleted the lottery/fairy/miniboss/
// wave room types from the game as the last doors were converted.
//
// These are QsCheckSiteFlag/QsSetSiteFlag offsets - RAW FLAG_BANK_12
// offsets from 0, not the +700 QUICKSTART window every other GF_* in this
// file uses. That is the whole point of the block: it sits below the
// window, in the 586 bits the retired GF_DOOR_* entrances used to squat on,
// so it can grow without shoving anything else along in front of it.
//
// Ceiling is QUICKSTART_CONTENT_SITE_MAX = 61 sites (61 * 13 = 793 bits,
// raw 1..793), short of raw 801 where the QUICKSTART window itself begins. Adding a site is now one table row and nothing else - no constant
// below it moves, because there is nothing below it. The compile-time
// assertion under the count is what makes that promise enforceable: blow
// past 61 and the build stops instead of quietly aliasing the window.
//
// They also have to be cleared per run explicitly - see the site-block
// clear in GameTask_Transition, and its comment on why the bank-wide wipe
// there does not reach the top of this block on its own.
#define QUICKSTART_CONTENT_SITE_COUNT 44
#define QUICKSTART_CONTENT_SITE_BITS 13
#define QUICKSTART_CONTENT_SITE_MAX 61
#define GF_CONTENT_SITE_BASE(i) ((i) * QUICKSTART_CONTENT_SITE_BITS)
#define GF_CONTENT_SITE_RANDOMIZED(i) (GF_CONTENT_SITE_BASE(i) + 0)
#define GF_CONTENT_SITE_KIND_BIT(i, b) (GF_CONTENT_SITE_BASE(i) + 1 + (b))    // b = 0..2
#define GF_CONTENT_SITE_EXTRA_BIT(i, b) (GF_CONTENT_SITE_BASE(i) + 4 + (b))   // b = 0..7
#define GF_CONTENT_SITE_DONE(i) (GF_CONTENT_SITE_BASE(i) + 12)
// Build breaks here if the site table outgrows the space between raw 0 and
// the start of the QUICKSTART window. C89 has no static_assert; a negative
// array dimension is the portable stand-in agbcc accepts.
typedef char QuickStartContentSiteBlockFits[(QUICKSTART_CONTENT_SITE_COUNT <= QUICKSTART_CONTENT_SITE_MAX) ? 1 : -1];
typedef char QuickStartContentSiteBlockClearsWindow[(QUICKSTART_SITE_FLAG_ORIGIN +
                                                         QUICKSTART_CONTENT_SITE_MAX * QUICKSTART_CONTENT_SITE_BITS <=
                                                     QUICKSTART_FLAG_ORIGIN + 101)
                                                        ? 1
                                                        : -1];
// --- The shop, as a randomly-placed "? room" -------------------------------
//
// Which overworld door leads to the shop this run (5 bits, an index into
// the retired shop-door draw), plus a per-catalog-item price roll (3 bits each).
// Both are rolled once per run and then fixed, so the player can go back to
// the shop as often as they like and find it in the same place at the same
// prices.
//
// Melari's Mine's two hand-written "? rooms" never had a persistent "this
// has been collected" latch - only a room flag, which resets on every room
// load. Re-entering respawned the reward, so either room could be farmed
// indefinitely by walking out and back in. These are that latch. Every
// other "? room" already had one: the generic content sites carry
// GF_CONTENT_SITE_DONE.
#define GF_MELARI_EAST_DONE 690
#define GF_MELARI_SOUTHEAST_DONE 691

// Which Kinstone fusion this run has already re-loaded its room for, stored
// as a 7-bit id (kinstone ids run 1..100) rather than a flag per fuser -
// there are 18 fusers and only 16 free offsets left below 707.
//
// The problem it solves: vanilla applies a fusion's world event to the LIVE
// room only on room load (sub_080186EC, room.c). The fusion cutscene itself
// runs against an auxiliary copy of the room (sub_08054974 ->
// LoadAuxiliaryRoom), so the player watches the staircase appear and then
// returns to a room where it still is not there - the change only lands the
// next time they walk in. Re-applying the event by hand does not fix the
// whole class either: the "blocked" state of a type 4 or type 7 gate is
// tiles PAINTED OVER the room at load time while un-fused, and nothing in
// vanilla erases them, because a room load simply does not paint them.
// Reloading the room is the one operation that covers every gate type, and
// it is exactly what the player is doing manually today by stepping into a
// house and back out.
#define GF_FUSION_RELOADED_ID_BIT(b) (692 + (b)) // b = 0..6

// Where the fusers stand this run. One roll, four bits, shared by every
// region - see QuickStartFuserSpot for how one number moves eighteen sprites
// to different places without a flag each.
#define GF_FUSER_SCATTER_ROLLED 699
#define GF_FUSER_SCATTER_BIT(b) (700 + (b)) // b = 0..3

// Switch-operated bridges (QuickStartUpdateSwitchBridges). Sits immediately
// above the content sites' last block, which ends at 655.
#define GF_NHF_BRIDGE_JOINED 656

#define GF_SHOP_RANDOMIZED 657
// 658-689: the retired shop-door draw (658-662) and the retired 9-slot
// 3-bit price roll (663-689). Both free; see QUICKSTART_SHOP_AREA and the
// shop price block below.

// --- Shop prices and purchase state ---------------------------------------
//
// Prices are absolute rupee amounts rolled per run, not a scale factor on the
// vanilla table any more, so they need real width. These live in the range
// the retired content-site block left free (QsCheckFlag offsets 266-655; see
// the FLAG_BANK_12 map at the top of this file), which is cleared per run
// along with the rest of 202-703.
//
//   refill price   7 bits x 3 slots   value 0-99  -> 1-100 rupees
//   one-off price  9 bits x 4 slots   value 0-499 -> 1-500 rupees
//   heart pieces   5 bits             purchases so far this run
//   sold           1 bit  x 4 slots   a drawn slot that has been bought
#define GF_SHOP_REFILL_PRICE_BIT(i, b) (266 + (i) * 7 + (b)) // i = 0..2, b = 0..6 -> 266-286
#define GF_SHOP_ONEOFF_PRICE_BIT(i, b) (287 + (i) * 9 + (b)) // i = 0..3, b = 0..8 -> 287-322
#define GF_SHOP_HEART_PIECE_BUYS_BIT(b) (323 + (b))          // b = 0..4      -> 323-327
#define GF_SHOP_SLOT_SOLD_BIT(i) (328 + (i))                 // i = 0..3      -> 328-331
#define QUICKSTART_SHOP_REFILL_PRICE_BITS 7
#define QUICKSTART_SHOP_ONEOFF_PRICE_BITS 9
#define QUICKSTART_SHOP_REFILL_PRICE_MAX 100
#define QUICKSTART_SHOP_ONEOFF_PRICE_MAX 500
// The heart piece: 50 rupees the first time in every run, +25 for each one
// bought since. The counter is 5 bits and saturates rather than wrapping - at
// 31 purchases the price is already 825, well past what a run can carry.
#define QUICKSTART_SHOP_HEART_PIECE_BASE 50
#define QUICKSTART_SHOP_HEART_PIECE_STEP 25
#define QUICKSTART_SHOP_HEART_PIECE_BUYS_MAX 31

// Room-local coordinates, walked/confirmed walkable in the emulator (4-way
// movement check from each point, no wall/water immediately blocking any
// direction). Side A is the user's own given ladder position; Side B was
// found by tracing the river west from there to a matching dock structure
// on the far bank. Each side's "arrival" spot is offset from its own entry
// trigger so returning to it doesn't immediately re-satisfy that same
// trigger box next frame (same reasoning as sQuickStartDoorReturnSpots'
// own "+40, clear of the box" comment).
#define QUICKSTART_RIVER_SIDE_A_X 280
#define QUICKSTART_RIVER_SIDE_A_Y 238
#define QUICKSTART_RIVER_SIDE_A_ARRIVAL_X 320
#define QUICKSTART_RIVER_SIDE_A_ARRIVAL_Y 238
#define QUICKSTART_RIVER_SIDE_B_X 120
#define QUICKSTART_RIVER_SIDE_B_Y 238
#define QUICKSTART_RIVER_SIDE_B_ARRIVAL_X 120
#define QUICKSTART_RIVER_SIDE_B_ARRIVAL_Y 278


// Win condition: an Earth Element dropped at whichever region ends up last
// in this save's region chain (see QuickStartSpawnRegionRewardOnce) - at
// rewardX/rewardY, that region's own normal-loot reward spot. Picking it up
// ends the round. Only spawns once that region's own wave (and boss, if it
// has one) is fully cleared - same "wait for a clear room" gate every other
// region's own normal-loot reward uses.
// ITEM_EARTH_ELEMENT is a real Item enum slot that's otherwise unused by
// anything QUICKSTART touches on this loop (the actual main-quest Earth
// Element, never granted anywhere in this file), so its own inventory flag
// doubles as the "already spawned/taken" latch - no new global flag needed
// for that part. It gets explicitly cleared again in
// QuickStartCheckWinCondition below so the next round (after the
// win-triggered reset) starts with the Element unclaimed again.
//
// Ground items despawn on their own timer regardless of ENT_PERSIST (see
// QuickStartRefreshItemTimers, which does the same thing for the starter/
// bonus/skill choices) - left unrefreshed, the Element would flicker away and
// respawn every ~10 seconds while the player's still making their way
// here, and worse, a pickup landing in the same frame as a despawn could
// race and silently drop the win entirely. Called every frame from
// QuickStartRoomMonitor, so refresh an existing Element's timer every time
// through instead of only spawning once and leaving it to fend for itself.
static void QuickStartSpawnWinKeyOnce(s16 rewardX, s16 rewardY) {
    Entity* itemEntity;
    s32 i;
    if (GetInventoryValue(ITEM_EARTH_ELEMENT) != 0) {
        return;
    }
    // Refresh the existing Element's despawn timer FIRST, every frame,
    // regardless of room flag 43 below - this used to be checked only
    // inside the "not flagged yet" branch, so it only ever ran on the one
    // frame the item was first created; every frame after that hit flag
    // 403's early return before ever reaching this scan, leaving the
    // ground item's own ~10-second despawn timer (unk_6c, itemOnGround.c)
    // completely unrefreshed. The Element would then vanish exactly 10
    // seconds after spawning regardless of whether the player had actually
    // fought through the room's enemy wave to reach it yet (reported by
    // the user after real playtesting) - the same "reward silently expires
    // before a real player can get there" failure QuickStartGroundItemAt's
    // own comment documents for Castle Garden/Melari's Mine/the ladder
    // pool, just missed here since this reward doesn't go through that
    // shared helper.
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM && ent->type == ITEM_EARTH_ELEMENT) {
            ((ItemOnGroundEntity*)ent)->unk_6c = 600;
            return;
        }
    }
    // Room flag 43: "already created one this round" - GiveItem (the real
    // vanilla pickup path, LinkHoldingItem_Action1 in
    // object/linkHoldingItem.c) isn't called until the pickup cutscene's own
    // held-item entity reaches a specific animation frame, several frames
    // after the original ItemOnGround entity here is already deleted (see
    // ItemOnGround_Action4/sub_08081420) - so GetInventoryValue above still
    // reads 0 for a real window after the item is physically gone. Without
    // this flag, the entity scan above finds nothing during that window
    // (the cutscene's own entity isn't a GROUND_ITEM) and concludes none
    // exists yet, spawning a second Earth Element at the same spot - which
    // the player then immediately stands on and picks up again the moment
    // they regain control, replaying the whole cutscene a second time
    // (reported by the user, reasoned from a full read of the real
    // ItemOnGround -> LinkHoldingItem call chain rather than reproduced via
    // emulator, since forcing this exact multi-entity timing window is
    // impractical to script). No manual clearing needed elsewhere: like
    // every other room flag in this file, it resets on its own the moment
    // the room reloads for a genuinely new round.
    if (QsCheckRoomFlag(43)) {
        return;
    }
    itemEntity = CreateObject(GROUND_ITEM, ITEM_EARTH_ELEMENT, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + rewardX;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + rewardY;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
        QsSetRoomFlag(43);
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

// Genuine custom dialogue - see TEXT_CUSTOM/gCustomStrings (message.h,
// text.c): sub_0805EEB4 resolves TEXT_INDEX(TEXT_CUSTOM, n) straight to
// gCustomStrings[n] instead of the real, compiled-asset translation tables
// (which have no source and can't have new lines authored into them - the
// whole reason the QUICKSTART ladder-NPC scripts used to borrow real,
// unrelated vanilla dialogue lines instead, see data/scripts/quickstart/
// script_QuickStartLadderNpc0.inc's own comment on that). Works from
// anywhere a normal TEXT_INDEX does: MessageNoOverlap/EzloMessage in a
// script, or CreateEzloHint/MessageRequest directly from C, like the win
// message below.
//
// Authored as plain C strings rather than through the usual .string/
// charmap asset pipeline (data/const/text.s and friends): that pipeline
// only extracts bytes that already exist in the base ROM (assets/gfx.json-
// style byte ranges), and using it to author brand new text would also
// mean adding a new object file's sections into linker.ld by hand, which
// lays out this ROM's memory to match the original exactly. A plain string
// literal sidesteps both: C already emits standard ASCII bytes per
// character, which cross-checked exactly against this engine's own real
// behavior (NumberToAscii, message.c, builds digits as '0' | digit - i.e.
// real ASCII - and this file's existing skill-pickup message already
// renders real letters correctly via the normal TEXT_INDEX path), and
// \x06\x01 is this engine's own control code for "insert numeric variable 1
// here" (charmap.txt: STR_VAR_1 = 06 01), substituted from gMessage.rupees
// at render time - same mechanism the shop's price prompt already uses. \n
// is charmap's '\n' = 0A, this engine's own real line-break control code.
// The terminator is C's own implicit trailing '\0', which is also this
// engine's own "end of text" byte (charmap.txt: '$' = 00).
const u8* const gCustomStrings[] = {
    [0] = (const u8*)"You win! Difficulty\nincreased to level \x06\x01.",
    // Castle Garden ladder mini-dungeon reward NPCs (data/scripts/quickstart/
    // script_QuickStartLadderNpc0/1/2.inc) - all 3 ladders share the same
    // pair of outcomes and, before this existed, the same borrowed TEXT_ANJU/
    // TEXT_HAPPY_HEARTH real dialogue lines. ModRupees's amount is a fixed
    // 100 in every script that uses these, so it's written directly into
    // the text instead of needing the ScriptCommand_SetMessageValue/
    // BeginBlock dance those real lines required for their own {rupees}
    // template slot.
    [1] = (const u8*)"Thanks for stopping by!\nHave 100 Rupees.",
    [2] = (const u8*)"It's a trap!\nYou lost 100 Rupees!",
    [3] = (const u8*)"There's nothing left\nfor you here.",
    // Item-choice sign NPC (data/scripts/quickstart/script_QuickStartChooseOne.inc,
    // shared by all 3 choice rows). Used to show TEXT_BURLOV,30 - a real,
    // unrelated mid-sentence Carlov/Burlov dialogue fragment ("Now, when
    // you're...") that happened to be reachable, not actual instructions.
    [4] = (const u8*)"Choose one of these\nitems!",
    // Ezlo's one-time round-start greeting (see the phase==0 branch of
    // QuickStartUpdateItemChoice below) - CreateEzloHint funnels through the
    // same sub_0805EEB4 resolver as every other TEXT_INDEX use, so
    // TEXT_CUSTOM works here too. Reworded for the F1b dialogue pass: the
    // old "your item picks your path" described the retired region-chain
    // routing and had become a false promise under free-roam; what the
    // player actually needs to know is that there are THREE rounds and
    // each gives exactly one pick.
    [5] = (const u8*)"Ezlo: Choose wisely!\nTake one gift per round.",
    // Shop merchant (data/scripts/quickstart/script_QuickStartMerchant.inc) -
    // shared by both shop rooms (Dojos Grimblade and Lon Lon Ranch's east
    // house room, see QuickStartSpawnShopMerchantOnce). Used to show
    // TEXT_BURLOV,30 (the same borrowed, unrelated Carlov/Burlov fragment as
    // the item-choice sign above) for the greeting, and TEXT_PICOLYTE,0x09
    // (a real Picolyte-shop line, equally out of context here) for the
    // "can't afford it" case.
    [6] = (const u8*)"Welcome! Carry an item\nhere to buy it.",
    [7] = (const u8*)"Sorry, you can't afford\nthat right now!",
    // Shown right after the difficulty message on a win, see
    // QuickStartCheckWinCondition below - same \x06\x01/gMessage.rupees
    // mechanism, just a second message rather than a second number packed
    // into the first (this engine only exposes one live numeric slot to
    // substitute per message).
    [8] = (const u8*)"Run score: \x06\x01\nKeep it up!",
    // Shown once, the moment a "? room" ladder resolves to the new
    // QS_EVENT_WAVES content (QuickStartSetupWaveRoomContent) - the
    // player's only warning that this room wants 3 waves cleared before it
    // drops a reward, since nothing else about the room looks different
    // from a single-miniboss room until the first wave spawns.
    [9] = (const u8*)"Ezlo: Get ready! Defeat\nthree waves of enemies!",
    // Shown once per run, the moment the player first sets foot in the
    // run's first overworld region (see QuickStartShowRegionIntroHintOnce) -
    // the game's actual goal statement. Under free-roam that statement is
    // "it is hidden in ONE of the areas, go search", which is a real
    // instruction; the old "seek it out there" told a new player nothing
    // about HOW.
    [10] = (const u8*)"Ezlo: The Earth Element\nhides in ONE area. Search!",
    // Shown when a NON-element region's first wave clear drops its reward
    // (QuickStartSpawnRegionRewardOnce's state-0 branch; the element
    // region's clear goes through the separate win-key path and never
    // shows this). Reworded for the F1b pass: "press on to the next area"
    // was chain-era phrasing - free-roam has no next area - and the one
    // genuinely useful fact this moment can teach is that THIS region is
    // not the element's hiding place, so cross it off.
    [11] = (const u8*)"Ezlo: A prize! But the\nElement is elsewhere...",
    // Shown once per run, the moment the player first sets foot in the
    // chain's LAST region (see QuickStartShowRegionFinalHintOnce) - directly
    // names the actual trigger (clearing this region's first wave, nothing
    // more) per the user's own request for a hint about what causes the
    // Earth Element to drop.
    [12] = (const u8*)"Ezlo: The Earth Element\nis here! Clear the foes!",
    // The rare miniboss Red Sword grant (see the QS_EVENT_MINIBOSS
    // reward drop). Delivered via GiveItem, which is silent on its own, so
    // this message is the whole pickup moment.
    [13] = (const u8*)"You won the Red Sword!\nEquip it from the menu.",
    // The hidden-item quest's completion line (QuickStartSetupRegionQuest).
    [14] = (const u8*)"You found what was\nhidden here!",
    // The hunt quest (QuickStartHunt*, below). One giver NPC per run, in
    // one region. 15 is the offer, 16 the handicap offer, 17 the win, 18
    // the loss, 19 what the NPC says once the run has burned its one
    // attempt. Reworded for the F1b pass so a first-timer learns the rules
    // from the text alone: the offer names the task and the exact time
    // limit (the countdown also shows in the HUD's key slot - DrawKeys,
    // ui.c - but a number the player has already read is easier to
    // recognize there); the handicap offer says the kit COMES BACK, which
    // the old line left terrifyingly open; the loss line says the attempt
    // is spent for the run, so "why won't he talk to me" never needs
    // asking. Keep the "30" literal in sync with QUICKSTART_HUNT_SECONDS.
    [15] = (const u8*)"My quarry! Slay ALL of\nthem in 30 seconds. Go!",
    [16] = (const u8*)"One weapon, no kit -\nall returned after. Deal?",
    [17] = (const u8*)"Cleared, and with time\nto spare! This is yours.",
    [18] = (const u8*)"Too slow - they fled.\nThat was my only hunt.",
    [19] = (const u8*)"You had your chance at\nthem. Maybe next time.",
    // The hub's hint sprites (sQuickStartHubHints below). Six Wind Tribe
    // wanderers scattered through the parts of the hub that are not doing a
    // job of their own - the tower entrance, Floor 2, and the clifftop by the
    // wind crest. Deliberately NOT in the spawn room, the shop or the roof,
    // per the user: those three rooms already have something to say.
    //
    // Between them they cover the six things a new run has no other way to
    // learn: kinstone fusion, what the run is actually for, that doors and
    // holes are worth trying, that winning raises the stakes, that some rooms
    // fight back in waves, and that clearing an area pays.
    [20] = (const u8*)"Fuse Kinstones with the\nwanderers you meet!",
    // 21 reworded for the F1b pass: "waits in the final area" was the
    // chain era's geography and is simply false under free-roam.
    [21] = (const u8*)"The Element hides in a\ndifferent area each run.",
    [22] = (const u8*)"Doors and holes hide\nsurprises. Try them all!",
    [23] = (const u8*)"Each win raises the\ndifficulty and the loot.",
    [24] = (const u8*)"Some rooms send waves.\nClear each wave for loot.",
    [25] = (const u8*)"Clear an area of foes\nand a reward will drop.",
    // The pot quest's own give line (see QuickStartSetupRegionQuest and
    // GF_QUEST_HINT_SHOWN): before the F1b pass this quest had NO intro at
    // all - pots simply appeared in one region and the completion line
    // ([14]) was the first the player ever heard of it.
    [26] = (const u8*)"Ezlo: One pot in this\narea hides a prize!",
    // The scavenger hunt (QuickStartScav*, below). 27 the offer - names
    // the target, the task and the exact time limit, per the F1b bar
    // (keep the "25" in sync with QUICKSTART_SCAV_SECONDS); 28 the win -
    // says where the prize is, since it drops at the giver rather than
    // where the Keaton died; 29 the loss - says the attempt is spent; 30
    // the spent line for later visits.
    [27] = (const u8*)"A Keaton stole my prize!\nSlay it! 25 seconds!",
    [28] = (const u8*)"My prize is back - and\nnow it's yours. Take it!",
    [29] = (const u8*)"The Keaton got away...\nThat was my only chance.",
    [30] = (const u8*)"The chase is done for\nthis run. Travel safe!",
    // The closing gate's one-shot room hint (QS_EVENT_GATE).
    [31] = (const u8*)"Ezlo: Strike the switch,\nthen RUN for the prize!",
    // The decoy levers' hint (QS_EVENT_GATE, decoy variant). States the
    // whole contract in one breath - three levers, one opens, one
    // punishes - because the room itself gives no tell by design.
    [32] = (const u8*)"Ezlo: Three switches!\nOne frees it, one BITES...",
    // Food charm/curse receipts (QuickStartNoteFoodItem). One line per
    // item, shown as an Ezlo bubble the moment the food is picked up, per
    // the F1b bar: name the item AND the effect, so the player learns the
    // vocabulary. 33-35 the charms, 36-38 the curses.
    [33] = (const u8*)"The Brioche! Your sword\nsends foes FLYING now.",
    [34] = (const u8*)"The Croissant! Your\nfeet feel feather-light.",
    [35] = (const u8*)"The Cake! No blow can\nmove you now. Stand firm!",
    [36] = (const u8*)"Humble Pie... a curse!\nBlows send YOU flying.",
    [37] = (const u8*)"Dog Food?! A curse! The\nenemies quicken...",
    [38] = (const u8*)"Odd Mushroom... a curse!\nFoes fire twice as fast.",
    // Batch two of the receipts: the tomes, the trinkets, the pity sword.
    [39] = (const u8*)"A scorched tome! Flame\ncannot burn you now.",
    [40] = (const u8*)"A frosted tome! Ice\ncannot freeze you now.",
    [41] = (const u8*)"A crackling tome! No\nspark can shock you now.",
    [42] = (const u8*)"Tingle's trophy! Foes\nwill spill more rupees.",
    [43] = (const u8*)"The Jabber Nut! Foes\nwill drop more kinstones.",
    [44] = (const u8*)"Carlov's medal! Foes\nwill drop more hearts.",
    [45] = (const u8*)"A broken sword... shops\npity you: 50 rupee cap!",
    // The inn (Wind Tribe Tower Floor 2): the three beds' offers, the
    // refusal, and the wake-up line. Prices repeated in the text on
    // purpose - the offer IS the price tag.
    [46] = (const u8*)"A comfy bed.\nOne night: 50 Rupees.\nPress R again to sleep.",
    [47] = (const u8*)"A plush bed.\nOne night: 200 Rupees.\nPress R again to sleep.",
    [48] = (const u8*)"A royal bed.\nOne night: 500 Rupees.\nPress R again to sleep.",
    [49] = (const u8*)"You can't afford\nthis bed.",
    [50] = (const u8*)"You wake up\nfeeling rested!",
    // F10: the MAP and COMPASS receipts. The compass names the Element's
    // REGION - never the spot - so [52]-[58] follow the ring enum order
    // (QS_RING_CG..QS_RING_WW, see QuickStartRingRegionOfPoolIndex).
    [51] = (const u8*)"The world map!\nPress START to see\nwhere you stand.",
    [52] = (const u8*)"The compass hums...\nthe Element waits in\nthe Castle Garden!",
    [53] = (const u8*)"The compass hums...\nthe Element waits in\nNorth Hyrule Field!",
    [54] = (const u8*)"The compass hums...\nthe Element waits in\nSouth Hyrule Field!",
    [55] = (const u8*)"The compass hums...\nthe Element waits in\nthe Eastern Hills!",
    [56] = (const u8*)"The compass hums...\nthe Element waits in\nLon Lon Ranch!",
    [57] = (const u8*)"The compass hums...\nthe Element waits in\nTrilby Highlands!",
    [58] = (const u8*)"The compass hums...\nthe Element waits in\nthe Western Wood!",
    // Charm 14, the luck charm (ITEM_SHELLS). It does NOT sit at 33 + n
    // like the other thirteen: that run ends at 45 and 46 is already the
    // inn's first bed offer, so the announcement special-cases this one
    // (see QuickStartNoteFoodItem).
    [59] = (const u8*)"Lucky shells! Fortune\nfavors you - rarer finds\nfrom here on.",
    // ===================== The trophy case catalog ======================
    //
    // 60 is the placeholder every not-yet-found row shows; 61 onward are
    // the entry NAMES, one per sQuickStartCatalog row in table order; the
    // DESCRIPTIONS follow immediately after the last name. Both blocks are
    // indexed arithmetically (QUICKSTART_CATALOG_NAME_BASE /
    // _DESC_BASE), so a row added to the catalog table must have a name
    // AND a description inserted at the matching position in BOTH blocks -
    // there is a compile-time check that the pair fits under 256, but
    // nothing can check that they line up. Keep all three lists in the
    // same order and adding an entry stays a three-line edit.
    //
    // Names are short by necessity: the list draws five at a time in a
    // narrow column. Descriptions have a scrolling panel and should say
    // what the thing DOES, not what it is - "Spin Attack" is already on
    // screen next to it.
    [60] = (const u8*)"- - - - -",
    // -- the goal
    [61] = (const u8*)"Earth Element",
    // -- ordinary pickups
    [62] = (const u8*)"Heart",
    [63] = (const u8*)"Green Rupee",
    [64] = (const u8*)"Blue Rupee",
    [65] = (const u8*)"Red Rupee",
    // "Bomb Refill" rather than "Bombs": row 25 is the BOMBS weapon and
    // the two would otherwise read identically five rows apart.
    [66] = (const u8*)"Bomb Refill",
    [67] = (const u8*)"Arrow Refill",
    [68] = (const u8*)"Kinstone Piece",
    [69] = (const u8*)"Fairy",
    // -- rewards
    [70] = (const u8*)"Big Green Rupee",
    [71] = (const u8*)"Big Red Rupee",
    [72] = (const u8*)"Big Silver Rupee",
    [73] = (const u8*)"Piece of Heart",
    [74] = (const u8*)"Heart Container",
    [75] = (const u8*)"Empty Bottle",
    [76] = (const u8*)"Blue Potion",
    [77] = (const u8*)"Red Potion",
    [78] = (const u8*)"Bottled Fairy",
    // -- weapons and tools
    [79] = (const u8*)"Smith's Sword",
    [80] = (const u8*)"White Sword",
    [81] = (const u8*)"Shield",
    [82] = (const u8*)"Mirror Shield",
    [83] = (const u8*)"Bow",
    [84] = (const u8*)"Large Quiver",
    [85] = (const u8*)"Bombs",
    [86] = (const u8*)"Remote Bombs",
    [87] = (const u8*)"Bomb Bag",
    [88] = (const u8*)"Boomerang",
    [89] = (const u8*)"Magic Boomerang",
    [90] = (const u8*)"Gust Jar",
    [91] = (const u8*)"Fire Rod",
    [92] = (const u8*)"Map",
    [93] = (const u8*)"Compass",
    // -- key items
    [94] = (const u8*)"Pegasus Boots",
    [95] = (const u8*)"Roc's Cape",
    [96] = (const u8*)"Mole Mitts",
    [97] = (const u8*)"Flippers",
    [98] = (const u8*)"Lantern",
    [99] = (const u8*)"Ocarina",
    [100] = (const u8*)"Cane of Pacci",
    [101] = (const u8*)"Grip Ring",
    [102] = (const u8*)"Power Bracelets",
    // -- sword skills
    [103] = (const u8*)"Spin Attack",
    [104] = (const u8*)"Great Spin",
    [105] = (const u8*)"Rock Breaker",
    [106] = (const u8*)"Roll Attack",
    [107] = (const u8*)"Dash Attack",
    [108] = (const u8*)"Down Thrust",
    [109] = (const u8*)"Sword Beam",
    [110] = (const u8*)"Peril Beam",
    // -- stat upgrades
    [111] = (const u8*)"Arrow Butterfly",
    [112] = (const u8*)"Dig Butterfly",
    [113] = (const u8*)"Swim Butterfly",
    [114] = (const u8*)"Charm of Nayru",
    [115] = (const u8*)"Charm of Farore",
    [116] = (const u8*)"Charm of Din",
    // -- charms and curses
    [117] = (const u8*)"Brioche",
    [118] = (const u8*)"Croissant",
    [119] = (const u8*)"Cake",
    [120] = (const u8*)"Red Book",
    [121] = (const u8*)"Green Book",
    [122] = (const u8*)"Blue Book",
    [123] = (const u8*)"Tingle Trophy",
    [124] = (const u8*)"Jabber Nut",
    [125] = (const u8*)"Carlov's Medal",
    [126] = (const u8*)"Broken Sword",
    [127] = (const u8*)"Lucky Shells",
    [128] = (const u8*)"Humble Pie",
    [129] = (const u8*)"Dog Food",
    [130] = (const u8*)"Strange Mushroom",
    // ---- descriptions, same order --------------------------------------
    [131] = (const u8*)"The run's goal. It waits\nin one area each run -\ntake it and you win.",
    [132] = (const u8*)"Restores one heart.\nFalls from cut grass,\npots and slain foes.",
    [133] = (const u8*)"One rupee. The shop and\nthe inn both take them,\nso nothing is wasted.",
    [134] = (const u8*)"Five rupees.",
    [135] = (const u8*)"Twenty rupees.",
    [136] = (const u8*)"Refills five bombs, up\nto whatever your bag\nwill hold.",
    [137] = (const u8*)"Refills five arrows, up\nto whatever your quiver\nwill hold.",
    [138] = (const u8*)"Fuse a piece at a gated\ndoor to open a new room\nfor the rest of the run.",
    [139] = (const u8*)"Refills your hearts on\nthe spot. Catch one in\na bottle to save it.",
    [140] = (const u8*)"Fifty rupees. A common\narea-clear reward.",
    [141] = (const u8*)"One hundred rupees.",
    [142] = (const u8*)"Two hundred rupees. The\nrichest single reward\nthis mode drops.",
    [143] = (const u8*)"Four pieces make one\nwhole Heart Container.",
    [144] = (const u8*)"One more heart on your\nlife bar, permanently\nfor this run.",
    [145] = (const u8*)"Holds one potion, fairy\nor charm. More bottles\nmeans more can be held.",
    [146] = (const u8*)"Refills your hearts when\ndrunk. Keep it for the\nfight you did not expect.",
    [147] = (const u8*)"Refills hearts AND cures\nwhatever ails you.",
    [148] = (const u8*)"Revives you where you\nfall - an extra life in\na bottle.",
    [149] = (const u8*)"Your starting blade. Its\nspin and beam skills are\nlearned separately.",
    [150] = (const u8*)"A stronger blade. Every\nsword blow you land does\nmore damage.",
    [151] = (const u8*)"Blocks blows from ahead\nand bounces some shots\nstraight back.",
    [152] = (const u8*)"Blocks what a shield\nblocks, and reflects\nmagic besides.",
    [153] = (const u8*)"Strikes at range. Some\nfoes a sword cannot kill\nfall to an arrow.",
    [154] = (const u8*)"Carry far more arrows\nbefore you run dry.",
    [155] = (const u8*)"Blows open cracked walls\nand kills whatever is\nstanding too close.",
    [156] = (const u8*)"Bombs you set off when\nYOU choose, not on a\nfuse.",
    [157] = (const u8*)"Carry far more bombs\nbefore you run dry.",
    [158] = (const u8*)"Stuns at range and grabs\ndistant items. Kills\nsome flyers outright.",
    [159] = (const u8*)"A boomerang you steer in\nflight. Reaches what the\nplain one cannot.",
    [160] = (const u8*)"Sucks in foes, pulls off\nshields, and hauls light\nthings across gaps.",
    [161] = (const u8*)"Sets fire to what it\ntouches. Lights dark\nrooms as it goes.",
    [162] = (const u8*)"Shows the whole world on\nthe pause screen, and\nwhere you stand on it.",
    [163] = (const u8*)"Names the area holding\nthis run's Earth\nElement.",
    [164] = (const u8*)"Hold the button to run.\nCrash into things and\nthey give way.",
    [165] = (const u8*)"Jump gaps and ledges,\nand glide a little on\nthe way down.",
    [166] = (const u8*)"Dig through soft ground\nfor buried things and\nburied ways through.",
    [167] = (const u8*)"Swim deep water instead\nof being turned back at\nthe shore.",
    [168] = (const u8*)"Lights dark rooms and\nsets fire to what needs\nburning.",
    [169] = (const u8*)"Plays the songs that\ncarry you across the\nworld in one step.",
    [170] = (const u8*)"Flips heavy things over\nand fires you up out of\nholes.",
    [171] = (const u8*)"Grip and pull without\nbeing shaken loose or\nburned.",
    [172] = (const u8*)"Shove the heavy rocks\nthat block the ways\nnothing else opens.",
    [173] = (const u8*)"Hold B to charge, then\nrelease for a sweep that\nhits all around you.",
    [174] = (const u8*)"A longer, wider spin\nthat keeps turning. Needs\nthe Spin Attack first.",
    [175] = (const u8*)"Your sword breaks rocks\nthat used to need bombs\nor bracelets.",
    [176] = (const u8*)"Roll into a foe and come\nup swinging, in one\nmotion.",
    [177] = (const u8*)"Dash with the boots and\nthe sword leads, striking\nwhat you run down.",
    [178] = (const u8*)"Fall from a jump with\nthe blade below you and\nland it point first.",
    [179] = (const u8*)"At full health your\nsword throws a beam at\nwhatever you face.",
    [180] = (const u8*)"At ONE heart your sword\nthrows beams - desperate,\nand strongest.",
    [181] = (const u8*)"You nock and loose\narrows faster than you\ndid before.",
    [182] = (const u8*)"You dig faster than you\ndid before.",
    [183] = (const u8*)"You swim faster than you\ndid before.",
    [184] = (const u8*)"Nayru: you take a\nQUARTER of the damage\nyou otherwise would.",
    [185] = (const u8*)"Farore: you take half\ndamage AND deal half\nagain as much.",
    [186] = (const u8*)"Din: your blows do\nDOUBLE damage. Drink it\nand hit things.",
    [187] = (const u8*)"Charm: your sword knocks\nfoes twice as far as it\nused to.",
    [188] = (const u8*)"Charm: you walk half\nagain as fast for the\nrest of the run.",
    [189] = (const u8*)"Charm: nothing can knock\nyou back. You stand\nwhere you stand.",
    [190] = (const u8*)"Charm: fire cannot burn\nyou - no flames, no\ncontact damage.",
    [191] = (const u8*)"Charm: ice cannot freeze\nyou. Walk through what\nused to stop you.",
    [192] = (const u8*)"Charm: sparks cannot\nshock you.",
    [193] = (const u8*)"Charm: slain foes spill\nrupees far more often.",
    [194] = (const u8*)"Charm: slain foes drop\nKinstone pieces far more\noften.",
    [195] = (const u8*)"Charm: slain foes drop\nhearts far more often.",
    [196] = (const u8*)"Charm: the shop caps\nevery price at 50 rupees\n- the heart piece aside.",
    [197] = (const u8*)"Charm: rare finds come\nup roughly twice as\noften.",
    [198] = (const u8*)"CURSE: blows knock YOU\ntwice as far. Humble\npie, indeed.",
    [199] = (const u8*)"CURSE: every foe moves\nhalf again as fast for\nthe rest of the run.",
    [200] = (const u8*)"CURSE: foes that shoot\nfire about half again as\noften.",
    // Tingle's payout (QuickStartTinglePayout).
    [201] = (const u8*)"Tingle, Tingle! A Heart\nContainer for a fine\nfusion!",
};
const u32 gCustomStringCount = ARRAY_COUNT(gCustomStrings);

// Room flag 40 (in QUICKSTART's private room-flag window, see QsSetRoomFlag)
// tracks "message already shown" across the few frames it's
// up, the same idempotent-per-frame-check pattern this whole file already
// uses elsewhere - a plain mutable static local doesn't work in this build:
// agbcc emits it into .data, and this ROM's linker.ld doesn't map
// src/game.o's .data section at all (every other piece of writable per-visit
// state in this file already goes through room/global flags or gSave fields
// for the same underlying reason, not just for the reset-on-reload
// semantics).
//
// A flag of its own rather than reusing flag 1 as this used to: a shared bit
// would read true before the win message ever actually showed, silently
// skipping straight to "already shown, waiting for dismissal" and hanging
// forever. Collision with VANILLA's own room flags - the original reason
// this one was pushed up into the 400s - is no longer a consideration for
// any flag in this file: they all go through QsSetRoomFlag's private window
// now (see QUICKSTART_ROOM_FLAG_ORIGIN).
// Counts distinct items currently owned (GetInventoryValue != 0) across the
// real item id range (ITEM_NONE=0 excluded; ids from 0xfc on are drop-table
// markers, not real inventory slots - see item.h - so the loop stops well
// short of those). Used by QuickStartComputeScore's item-variety bonus
// below; nothing here needs a persistent counter of its own since ownership
// is already tracked (gSave.inventory) and reset per run by the same
// MemClear(gSave.inventory, ...) GameTask_Transition already does for every
// other piece of starting-gear bookkeeping.
static s32 QuickStartCountItemsHeld(void) {
    s32 i;
    s32 count = 0;
    for (i = 1; i < ITEM_KINSTONE_RED; i++) {
        if (GetInventoryValue(i) != 0) {
            count++;
        }
    }
    return count;
}

// First-cut scoring formula for the run just finished - see
// docs/QUICKSTART_ROADMAP.md for the full design and rationale. Deliberately
// simple and easy to retune once we see real playthroughs: regular/miniboss/
// boss kills each score linearly (boss_kills is always 0 today - no region
// yet spawns one - kept in the formula so it's a pure config change, not a
// code change, once regions add bosses), plus four flat bonuses matching
// the user's brief (finish quickly, hold a lot of rupees, gain hearts,
// collect a variety of items). All four bonus thresholds are placeholders
// pending real playtest data.
#define QUICKSTART_SCORE_TIME_BONUS_FRAMES (10 * 60 * 60) // finish within 10 in-game minutes
#define QUICKSTART_SCORE_TIME_BONUS 500
#define QUICKSTART_SCORE_RUPEE_BONUS_THRESHOLD 200
#define QUICKSTART_SCORE_RUPEE_BONUS 200
#define QUICKSTART_SCORE_HEART_BONUS_PER_HEART 50
#define QUICKSTART_SCORE_ITEM_BONUS_PER_ITEM 20
static u32 QuickStartComputeScore(void) {
    u32 score = gSave.enemies_killed * 10 + gSave.miniboss_kills * 100 + gSave.boss_kills * 500;
    s32 heartsGained = ((s32)gSave.stats.maxHealth - 24) / 8;

    if (gSave.run_frames <= QUICKSTART_SCORE_TIME_BONUS_FRAMES) {
        score += QUICKSTART_SCORE_TIME_BONUS;
    }
    if (gSave.stats.rupees >= QUICKSTART_SCORE_RUPEE_BONUS_THRESHOLD) {
        score += QUICKSTART_SCORE_RUPEE_BONUS;
    }
    if (heartsGained > 0) {
        score += heartsGained * QUICKSTART_SCORE_HEART_BONUS_PER_HEART;
    }
    score += QuickStartCountItemsHeld() * QUICKSTART_SCORE_ITEM_BONUS_PER_ITEM;
    return score;
}

static void QuickStartCheckWinCondition(void) {
    if (GetInventoryValue(ITEM_EARTH_ELEMENT) == 0) {
        QsClearRoomFlag(40);
        QsClearRoomFlag(42);
        QsClearRoomFlag(44);
        return;
    }
    // Room flag 44: "vanilla's own Earth Element get-message has started".
    //
    // The "is a message up right now?" test below is necessary but not
    // sufficient on its own. GiveItem flips this item's inventory value a
    // few frames BEFORE the pickup cutscene actually posts its own text -
    // measured at 6 frames in the emulator (walk-up pickup, gMessage.state
    // and .textIndex sampled every frame): our custom message went up on
    // frame 27 and vanilla's text index 0x540 replaced it on frame 33, so
    // the "You win!" line was on screen for a tenth of a second and then
    // silently overwritten. Waiting for a message to have appeared first,
    // and only then for it to finish, closes that window.
    //
    // Only required on the visit that actually dropped the Element (room
    // flag 43): if the player picked it up and came back later, inventory
    // already reads nonzero with no cutscene pending, and waiting for a
    // message that will never arrive would hang the win outright.
    if (QsCheckRoomFlag(43) && !QsCheckRoomFlag(44)) {
        if (gMessage.state & MESSAGE_ACTIVE) {
            QsSetRoomFlag(44);
        }
        return;
    }
    if (!QsCheckRoomFlag(40)) {
        // Wait for the real vanilla "You got the Earth Element" pickup
        // cutscene to finish and be dismissed before starting our own
        // message - GetInventoryValue(ITEM_EARTH_ELEMENT) above already
        // reads nonzero the instant the item is touched, well before that
        // cutscene's own multi-page text is done with gMessage, and
        // MessageRequest below does an unconditional MemClear(&gMessage,
        // ...): firing it immediately here was confirmed in the emulator
        // (via a real walk-up pickup, not a memory poke - see
        // scratchpad/vidframes this session) to silently clobber the real
        // cutscene's state and race straight through to DoSoftReset within
        // a couple of frames, so neither this message nor the score message
        // below ever actually got shown to the player.
        if (gMessage.state & MESSAGE_ACTIVE) {
            return;
        }
        QuickStartIncrementDifficulty();
        MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 0));
        // MessageRequest above MemClears the whole gMessage struct, so
        // rupees has to be set after it, not before - confirmed in the
        // emulator: setting it first always showed "level 0" regardless of
        // the real difficulty, since MessageRequest was silently wiping it
        // back out before MsgInit ever read it.
        gMessage.rupees = QuickStartGetDifficulty();
        // Forces the resolution step (normally the next MessageMain() tick,
        // see message.c) to happen immediately instead of a frame later -
        // this function isn't itself part of the script/message system's
        // own per-frame timing, so nothing else would otherwise drive it
        // forward the moment MessageRequest above sets state=1.
        MsgInit();
        QsSetRoomFlag(40);
        return;
    }
    if (gMessage.state & MESSAGE_ACTIVE) {
        return;
    }
    // Second message: this run's score, shown once the difficulty message
    // above has been dismissed. Same room-flag-gated one-shot pattern as
    // flag 40 itself. meta_xp is banked here, exactly once, right as the
    // score it's derived from is computed and shown, so the number on
    // screen is the number saved. It's safe this early because nothing
    // meta_xp gates (kind unlocks) can roll while the message holds the
    // player in place. runs_completed is NOT incremented here - see the
    // save/reset branch below.
    if (!QsCheckRoomFlag(42)) {
        u32 score = QuickStartComputeScore();
        gSave.meta_xp += score;
        MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 8));
        gMessage.rupees = score;
        MsgInit();
        QsSetRoomFlag(42);
        return;
    }
    if (gMessage.state & MESSAGE_ACTIVE) {
        return;
    }
    // Cleared here, not in the branch above - clearing it the instant the
    // win message starts made GetInventoryValue(...) == 0 true again on
    // the very next frame, before the message ever finished or this
    // function ever reached DoSoftReset below: that early-returned via the
    // very first check above, wiping room flag 40's "message already
    // shown" bookkeeping and abandoning the win sequence entirely - and
    // QuickStartSpawnWinKeyOnce, seeing the same now-zeroed value, would
    // immediately drop a fresh Element, which is exactly the infinite
    // pickup/message loop this was confirmed causing. Cleared here instead
    // so it only happens once, right before the save that's supposed to
    // record it, not mid-message.
    SetInventoryValue(ITEM_EARTH_ELEMENT, 0);
    // Incremented on the same frame as the save and the reset, NOT up in
    // the score-message branch with meta_xp: QuickStartRegionChainLength()
    // reads runs_completed every frame, so a win count that ticks over
    // while the score message is still up shifts which chain slot counts
    // as "last" mid-win-sequence (the region monitor keeps running under
    // the message) and the real last region briefly stops testing as last
    // - stray normal-reward drop, stalled failsafe clock. Here the new
    // value is visible for zero gameplay frames: the very next thing that
    // happens is the reset that rebuilds the run around it.
    gSave.runs_completed++;
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
    // RETIRED: the two Castor Darknut Hall <-> Melari's Mine rows. Hall was
    // the gate between the old start room and the old hub, and both ends are
    // off the route now.
    //
    // Melari's Mine's own Door B (near the real Mt Crenel Cavern of Flames
    // door) is retired too. It was the hub's way into region slot 0 - first
    // as a static row here, then as a dynamic box in
    // QuickStartProcessRegionChainLinks - and the pit in Cloud Tops does that
    // job now.
    //
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
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0xa8, 0xae, 0x220, 0x226, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST, 0x78, 0x64 },
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x228, 0x22e, 0x220, 0x226, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST, 0x78, 0x64 },
    { AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 0x280, 0x286, 0x11c, 0x122, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST, 0x78, 0x64 },
    // The Southwest door (the first of the three rows above) spent a
    // session pointing at the shop in the Grimblade dojo instead of at its
    // own vanilla room, both here and in transitions.c. The shop has moved
    // out - first to a randomly drawn overworld door, now to the hub - and
    // the dojo became a plain "? room" entered the way vanilla always
    // intended - down Castle Garden's southeast ladder, through the ante
    // room, north into the arena - but this door kept its old destination,
    // which stranded anyone who walked into it: the dojo's own exit chain
    // runs back out to Castle Garden's southeast ladder, into a Castle
    // Garden that never went through the region chain's setup. Both ends
    // are back on vanilla now, and the room it leads to is a content site
    // like Melari's other two side rooms.
    // Castle Garden's real north door (gExitList_CastleGarden_Main[0], a
    // WARP_TYPE_AREA door left un-retargeted for the same ACT_TILE reason
    // documented above - local (504,40), the castle's own entrance
    // pillars) and Lon Lon Ranch's own return box (287-343,966-984,
    // centered on (315,975)) both used to be static rows here, leading to
    // each other. Now dynamic instead, same reasoning as Melari's Mine's
    // Door B above - each region's own "onward" exit box
    // (sQuickStartRegionPool's exitMinX/MaxX/MinY/MaxY) leads to whichever
    // region is next in this save's chain, resolved at trigger time by
    // QuickStartProcessRegionChainLinks below rather than a fixed
    // destination here.
    // Talon and Malon's house (both west and east rooms) is fully reset to
    // vanilla per the user's own request - repeated rounds of custom content
    // there (a "? room" reward in the west room, a second shop location in
    // the east room) kept turning up new bugs (a large un-clearable black
    // obstruction in the west room, a real internal west/east connecting
    // door bleeding through past our own custom systems, shop item
    // density concerns) on top of each other. No custom entrance trigger
    // boxes for either room here anymore - both real vanilla
    // WARP_TYPE_AREA doors (gExitList_HyruleField_LonLonRanch) are left
    // exactly as-is, same "unreliable under QUICKSTART, same as every
    // other un-retargeted WARP_TYPE_AREA door" situation as Castle Garden's
    // own north door above, not something this file tries to work around
    // for this house anymore. See QuickStartEnforceLonLonContainment's own
    // exception below for both rooms (letting the real doors through
    // without canceling them, but adding nothing on top), and
    // transitions.c/QuickStartRoomMonitor for the rest of the reset (no
    // ifdef divergence, no ladder/shop content dispatch).
    //
    // Lon Lon Ranch's Goron Cave door itself (the real vanilla door the
    // wall-punching Goron blocks until KINSTONE_29 is fused at its fuser)
    // is NOT wired up here - it leads to a
    // random "? room" pool draw now (ladder slot 3), same as Castle
    // Garden's two ladders, so its destination varies per save and can't be
    // a static entry in this table. That mechanism is gone;
    // the room-keyed content sites resolve the
    // target at the moment the trigger fires.
    //
    // Lon Lon Ranch's cave connector used to live here as a fixed
    // GENTARI_EXIT entry (a single real door made bidirectional). Removed
    // entirely per the user's own request - the connector now draws a
    // random physical room from a real 2-door pool every save instead (see
    // sQuickStart2DoorSmallRoomPool/LargeRoomPool, QuickStart2DoorRandomizeOnce,
    // and the retired cave-connector trigger, which resolves this same real
    // vanilla cave-mouth box - gExitList_HyruleField_LonLonRanch:
    // startX=0xe8, startY=0x1b4, AREA_12x12 -> box +6/+6 - at trigger time
    // instead of a static table entry here, the same reason ladder 3's own
    // entrance isn't in this table either).
    //
    // The four Boomerang tree hollows' ladders DOWN into the chamber. Their
    // real WARP_TYPE_AREA rows (gExitList_TreeInteriors_Boomerang*) never
    // fire in play: the ladder tile at (120,84) is armed with a door
    // actTile (QuickStartOpenBoomerangChamber), but the vanilla collision
    // under the ladder art is solid, so a player walking up presses against
    // its lip at y~95 and never actually stands ON the tile the door check
    // reads. Measured directly - 300 frames of holding up, position pinned
    // at (120,95), no transition. This is the one leg of the chamber's five
    // round trips that stayed broken (all four ladders/staircase UP out of
    // the chamber fire fine - they're approached over open floor).
    //
    // So the down legs are position boxes instead, the same mechanism as
    // every other row here: the box is exactly where the blocked player
    // ends up pressing (x 112-128, y 84-98), and each destination is its
    // own vanilla row's arrival corner in the chamber. The chamber's four
    // up-rows' arrival spot is moved from (120,56) to (120,104) in
    // transitions.c to sit just SOUTH of this box - at the vanilla spot the
    // arriving player materialized inside the box's walk-through path and
    // bounced straight back down.
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST, 112, 128, 84, 98,
      AREA_CAVES, ROOM_CAVES_BOOMERANG, 0x48, 0x88 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST, 112, 128, 84, 98,
      AREA_CAVES, ROOM_CAVES_BOOMERANG, 0x108, 0x88 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST, 112, 128, 84, 98,
      AREA_CAVES, ROOM_CAVES_BOOMERANG, 0x48, 0xf8 },
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST, 112, 128, 84, 98,
      AREA_CAVES, ROOM_CAVES_BOOMERANG, 0x108, 0xf8 },
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
    if (QsCheckRoomFlag(1)) {
        return;
    }
    QuickStartSpawnEnemyGroup(sQuickStartMineEnemyOffsets, ARRAY_COUNT(sQuickStartMineEnemyOffsets),
                               QUICKSTART_MINE_ROOM_SQUARES, QUICKSTART_MINE_MAX_ENEMIES);
    QsSetRoomFlag(1);
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

// Deletes the ranch's ambient animals (COW, CUCCO, CUCCO_CHICK) per the
// user's own explicit request ("the cows are back... but they should be
// gone").
//
// It used to delete the wall-punching GORON too, and that was the reason the
// Goron cave could not be entered from the overworld. Vanilla's
// sub_StateChange_HyruleField_LonLonRanch (roomInit.c) does this on every
// room load:
//
//     if (!CheckKinstoneFused(KINSTONE_29)) {
//         LoadRoomEntityList(&gUnk_080F7860);            // the Goron
//         SetTile(SPECIAL_TILE_114, TILE_POS(8, 54), LAYER_BOTTOM);
//         SetTile(SPECIAL_TILE_150, TILE_POS(8, 55), LAYER_BOTTOM);
//     }
//
// The Goron and the two blocking tiles are ONE gate, and the fusion is what
// lifts both. Deleting only the NPC left the tiles painted over the cave
// mouth - a barrier with nothing standing in front of it, which is exactly
// how the user found it: "there is still an invisible barrier where the
// Goron stood".
//
// The deletion made sense when this file also fused KINSTONE_29 at boot, so
// the gate was meant to be open from the start and any Goron that appeared
// was a leftover. That boot-time fuse is gone - it was removed when
// KINSTONE_29 became a real fuser in the kinstone economy (sQuickStartFusers)
// - and only the deletion and a few comments describing it survived. Three
// of those comments have been corrected with this change.
//
// So the Goron stays. It stands at the wall as vanilla intends, visibly
// explaining why the cave is shut, and fusing KINSTONE_29 at its fuser plays
// the punch-through cutscene and opens it - which the user confirmed already
// works in play.
static void QuickStartClearLonLonRanchAnimals(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == NPC &&
            (gEntities[i].base.id == COW || gEntities[i].base.id == CUCCO ||
             gEntities[i].base.id == CUCCO_CHICK)) {
            DeleteEntity(&gEntities[i].base);
        }
    }
}

// Eastern Hills ships vanilla story NPCs (the farmers and their visitors)
// whose spawn is keyed on story/fusion flags a run can end up setting, and
// whose scripted spots sit ON the walkway - the user's screenshot has a
// pair of them standing in the stair gap by the farmhouse, walling off the
// descent. This mode's ? regions are supposed to be swept of vanilla
// population anyway, so: every frame, any NPC that is not one of ours goes.
// ZELDA is the entity id every QUICKSTART NPC borrows (fusers, hunt/scav
// givers, signs, the merchant), same protection rule as
// QuickStartClearHubRoom's sweep.
static void QuickStartClearEasternHillsNpcs(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent == gRoomControls.camera_target) {
            continue;
        }
        if (ent->kind == NPC && ent->id != ZELDA) {
            DeleteEntity(ent);
        }
    }
}

// Trilby Highlands' southwest field - the 10x10-tile pocket at tiles
// (1,35)-(10,44) that the solved boulder crossing and the restored
// through-cave opened up (flood-verified open, and ringed by solid tiles
// on every side; the only ways in are the cave mouth and ledge hops, which
// enemies don't take). Per the user it hosts wave spawns now and is the
// region's boss arena, "so long as they are contained to just that part of
// the map" - the solid ring already does that for tile-collision movement,
// and this clamp is the hard guarantee on top of it: any boss piece that
// somehow ends up outside (knockback through a seam frame, a future
// movement change) is pulled back to the pocket's edge. Idempotent, cheap,
// runs only while a boss exists.
#define QUICKSTART_TRILBY_POCKET_MIN_X 32
#define QUICKSTART_TRILBY_POCKET_MAX_X 160
#define QUICKSTART_TRILBY_POCKET_MIN_Y 576
#define QUICKSTART_TRILBY_POCKET_MAX_Y 704

static void QuickStartTrilbyQuirkHook(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s32 lx, ly;
        if (ent->kind != ENEMY || ent->id != CHUCHU_BOSS) {
            continue;
        }
        lx = ent->x.HALF.HI - gRoomControls.origin_x;
        ly = ent->y.HALF.HI - gRoomControls.origin_y;
        if (lx < QUICKSTART_TRILBY_POCKET_MIN_X) {
            lx = QUICKSTART_TRILBY_POCKET_MIN_X;
        }
        if (lx > QUICKSTART_TRILBY_POCKET_MAX_X) {
            lx = QUICKSTART_TRILBY_POCKET_MAX_X;
        }
        if (ly < QUICKSTART_TRILBY_POCKET_MIN_Y) {
            ly = QUICKSTART_TRILBY_POCKET_MIN_Y;
        }
        if (ly > QUICKSTART_TRILBY_POCKET_MAX_Y) {
            ly = QUICKSTART_TRILBY_POCKET_MAX_Y;
        }
        ent->x.HALF.HI = gRoomControls.origin_x + lx;
        ent->y.HALF.HI = gRoomControls.origin_y + ly;
    }
}

// RETIRED: QuickStartSolveLonLonBoulder + sQuickStartLonLonBoulders, the
// hand-measured teleport-and-stamp solver for Lon Lon Ranch's three
// boulder-hole crossings. It forced the end state directly - rock moved,
// action=3, SPECIAL_TILE_21 written over the hole with SetTileType - and
// writing that tile-type constant is exactly what left the ugly black
// square over each filled hole the user reported (foreign artwork, the
// same failure mode the Boomerang chamber hit; see
// QuickStartUpdateSwitchBridges' donor-tile comment). Trilby's
// QuickStartFillBoulderHoles does the same job by driving vanilla's own
// PushableRock settle path, which lays the correct art - so that function
// now covers every ring region (Lon Lon's three rocks included) and this
// solver is gone.

// ---- The overworld regions (free-roam) ----
// One data table (sQuickStartRegionPool below) plus one generic set of
// dispatch functions. Every region in the pool is live every run: endless
// escalating waves, a one-time reward on its first wave clear, quests. One
// region, drawn per run (QuickStartRollElementRegionOnce), drops the Earth
// Element in place of its normal reward - "the Element is SOMEWHERE, go
// find it" - and ends the run (QuickStartSpawnWinKeyOnce/
// QuickStartCheckWinCondition above, both region-agnostic). Travel between
// regions is real walking across the ring (see QuickStartIsRingRegionRoom);
// nothing warps.

// --- Per-region run state (the free-roam structure) ------------------------
//
// The run is "the Earth Element is SOMEWHERE - go find it": every region in
// the pool is live every run (waves, a one-time reward, quests), and one
// region, drawn per run, drops the Element in place of its normal reward
// when its first wave clears. Everything below is indexed by POOL INDEX,
// which - unlike the retired chain slots - is stable per physical region.
//
// Storage sits in the QS window's free range (the retired content-site
// span, after the shop's block which ends at 331), sized for 12 regions so
// the three still-unintegrated ring rooms and future growth fit without
// another move. All of it is cleared by the run-start 202-703 wipe.
#define QUICKSTART_REGION_STATE_MAX 12
#define GF_ELEMENT_REGION_ROLLED 332
#define GF_ELEMENT_REGION_BIT(b) (333 + (b))                             // b = 0..3 -> 333-336
// 337 spare (was going to be a separate element-hint latch; the hint
// reuses GF_REGION_FINAL_HINT_SHOWN instead).
#define GF_REGION_REWARD_STATE_BIT(i, b) (338 + (i) * 2 + (b))           // i = 0..11 -> 338-361
#define GF_REGION_WAVE_BIT(i, b) (362 + (i) * 8 + (b))                   // i = 0..11 -> 362-457
#define GF_REGION_QUEST_HOST_BIT(b) (458 + (b))                               // b = 0..3 -> 458-461
#define GF_REGION_HUNT_HOST_BIT(b) (462 + (b))                                // b = 0..3 -> 462-465
#define GF_DROP_REGION_ROLLED 466
#define GF_DROP_REGION_BIT(b) (467 + (b))                                     // b = 0..3 -> 467-470
// The pot quest's one-per-run give line (custom string 26, fired by
// QuickStartSetupRegionQuest). Lives here rather than with the quest's own
// bank-11 block because that block's neighbours (QUICKSTART_CHARM_BIT at
// 40-42) left it no room to grow.
#define GF_REGION_QUEST_HINT 471
// The roof's two fairy pots, one life each per run (the user's report:
// vanilla respawns them every room load, which was a free fairy top-up
// per hub visit). See QuickStartRoofFairyPotsOnce.
#define GF_FAIRY_POT_BIT(b) (472 + (b))                                  // b = 0..1 -> 472-473
// The scavenger hunt (F1, QuickStartScav* below): one giver per run, in a
// drawn region that is never the hunt quest's own - the two share the HUD
// clock (gSave.timer4), so they must never run at once.
#define GF_SCAV_ROLLED 474
#define GF_SCAV_HOST_BIT(b) (475 + (b))                                  // b = 0..3 -> 475-478
#define GF_SCAV_SPOT_BIT(b) (479 + (b))                                  // b = 0..4 -> 479-483
#define GF_SCAV_STATE_BIT(b) (484 + (b))                                 // b = 0..1 -> 484-485
// State values + clock, up here rather than with the quest's own code
// because the hunt quest's guards (defined earlier in the file) read them.
// 25, down from the original 60 (the user, Aug 2026: "the timer needs to
// be about half or less"). A Keaton bolts on sight and the chase crosses
// the region, so a minute made the clock decorative - the player caught it
// with time to spare and the swarm never mattered. At 25 the chase is the
// quest: you have to cut the Keaton off rather than out-walk it, and the
// pack's positioning tax finally costs something.
#define QUICKSTART_SCAV_SECONDS 25
#define QUICKSTART_SCAV_FRAMES (QUICKSTART_SCAV_SECONDS * 60)
#define QUICKSTART_SCAV_OFFERED 0
#define QUICKSTART_SCAV_RUNNING 1
#define QUICKSTART_SCAV_WON 2
#define QUICKSTART_SCAV_FAILED 3
static s32 QuickStartScavState(void);
// The closing gate's countdown, in frames (QS_EVENT_GATE - see the branch
// in QuickStartSetupEventContent). Global bits rather than room state
// because room flags are bits and this needs a number; only one gate room
// can be live at a time (the player is standing in it), and the branch
// zeroes it on every fresh visit, so sharing one field is safe. 10 bits =
// 17 seconds max, twice the widest window.
#define GF_GATE_TIMER_BIT(b) (486 + (b))                                 // b = 0..9 -> 486-495
// The window is priced in TILES OF TRAVEL rather than as a flat number of
// seconds (the user, Aug 2026: "it's trivial to get the prize right now").
// The old 8-seconds-falling-to-4 window was flat, so a switch dealt three
// tiles from the cage gave the player five idle seconds and a switch dealt
// across the room gave them the same five - the timer never described the
// run it was timing. Measured on open ground (walkspeed.py): Link walks
// 1.20 px/frame, i.e. ~14 frames per tile, and diagonals cost the same as
// their long axis, so Chebyshev distance IS the walk. The window is that
// distance times a per-tile allowance that tightens with difficulty:
//   difficulty 0  -> 22 frames/tile, ~1.6x a straight walk
//   difficulty 12 -> 15 frames/tile, ~1.07x - a clean line, no hesitation
// Pegasus Boots and a dash buy back the margin, which is the point: the
// kit the player found is what turns a sprint back into a walk.
#define QUICKSTART_GATE_FRAMES_PER_TILE 14
#define QUICKSTART_GATE_SLACK_BASE 22
#define QUICKSTART_GATE_SLACK_MIN (QUICKSTART_GATE_FRAMES_PER_TILE + 1)
// Floor and ceiling. The floor keeps a degenerate short deal (a room too
// cramped to separate switch and cage) from being unwinnable - three tiles
// of walking, which is more than the two-tile minimum such a deal leaves;
// the ceiling is the 10-bit field.
#define QUICKSTART_GATE_WINDOW_MIN (QUICKSTART_GATE_FRAMES_PER_TILE * 3)
#define QUICKSTART_GATE_WINDOW_MAX 1000
// How far the switch must be dealt from the cage, in tiles. This is the
// other half of the same report: a switch dealt ON the cage made any
// window generous, and since the cage ring spawns after the switch, a ring
// pot could also land on top of the switch - "the levers/switches are
// often under the pots". Five tiles is ~70 frames of walking, so the
// window has something to price even at the minimum.
#define QUICKSTART_GATE_LEVER_MIN_TILES 5
// The decoy-switch variant of the switch-puzzle site (the per-visit coin
// flip in the QS_EVENT_GATE branch). Switch roles live in the switch
// ENTITY (a scratch byte at 0x76, see QS_SWITCH_ROLE), not
// in flags: the switches are per-visit objects anyway, and the site's
// 8-bit room-flag window has only 3 bits free - not enough for a role
// permutation plus per-lever resolved state.
#define QUICKSTART_LEVER_ROLE_PRIZE 0
#define QUICKSTART_LEVER_ROLE_TRAP 1
#define QUICKSTART_LEVER_ROLE_DUD 2
#define QUICKSTART_LEVER_ROLE_DONE 0x80

// --- Food charms and curses (F4) ------------------------------------------
// The six unused pastry/food items, repurposed as run-long status effects:
// eat one (it arrives as an ordinary uncommon ? event / quest drop) and the
// effect sticks for the rest of the run, announced by an Ezlo line. Three
// bless, three bite - and the item names telegraph which is which only
// loosely (Humble Pie), which is the fun.
//   bit 0  BRIOCHE   charm: sword blows knock enemies twice as far
//   bit 1  CROISSANT charm: Link walks half again as fast
//   bit 2  CAKE      charm: Link cannot be knocked back at all
//   bit 3  PIE       curse: blows knock Link twice as far ("humble pie")
//   bit 4  DOGFOOD   curse: enemies move half again as fast
//   bit 5  MUSHROOM  curse: shooter enemies fire ~1.5x as often
// Batch two, on the rest of the unused quest items (all charms):
//   bit 6  BOOK1         fire cannot burn you (no ignite, no contact damage)
//   bit 7  BOOK2         ice cannot freeze you
//   bit 8  BOOK3         sparks cannot shock you
//   bit 9  TINGLE_TROPHY enemies spill more rupees
//   bit 10 JABBERNUT     enemies drop more kinstones
//   bit 11 CARLOV_MEDAL  enemies drop more hearts
//   bit 12 BROKEN_SWORD  cheap shop: everything capped at 50 rupees
//                        (except the heart piece, whose price still climbs)
// Persistent for the run in the QS window (per-run bits, cleared with the
// rest of the window at run start). CAKE beats PIE when both are held -
// the immunity check runs last.
// Moved out of 496-508 when the fourteenth charm arrived: the block sat
// directly below GF_REGION_ALIVE_BIT (509+), so one more entry would have
// walked into the D2 alive counts. 581 is the head of the next free run
// (581-655), which leaves room for a good many more before this has to
// move again. Per-run flags, all inside the run wipe's 202-703, so nothing
// carries over from a save written before the move.
#define GF_FOOD_BIT(n) (581 + (n)) // n = 0..13 -> 581-594
// Tingle's fusion has paid out (see sQuickStartTingles). One bit per row,
// per run - the heart container is a once-per-run prize, and the run wipe
// covers 202-703 so a new run puts Tingle back with his fusion unspent.
#define GF_TINGLE_PAID_BIT(i) (595 + (i)) // i = 0..3 -> 595-598
#define QUICKSTART_FOOD_SWORD_KNOCKBACK (1 << 0)
#define QUICKSTART_FOOD_WALK_SPEED (1 << 1)
#define QUICKSTART_FOOD_STEADFAST (1 << 2)
#define QUICKSTART_FOOD_CURSE_KNOCKBACK (1 << 3)
#define QUICKSTART_FOOD_CURSE_ENEMY_SPEED (1 << 4)
#define QUICKSTART_FOOD_CURSE_FIRE_RATE (1 << 5)
#define QUICKSTART_FOOD_IMMUNE_FIRE (1 << 6)
#define QUICKSTART_FOOD_IMMUNE_ICE (1 << 7)
#define QUICKSTART_FOOD_IMMUNE_SHOCK (1 << 8)
#define QUICKSTART_FOOD_DROP_RUPEES (1 << 9)
#define QUICKSTART_FOOD_DROP_KINSTONES (1 << 10)
#define QUICKSTART_FOOD_DROP_HEARTS (1 << 11)
#define QUICKSTART_FOOD_CHEAP_SHOP (1 << 12)
// The last idea from the original F4 wish list: rarer loot, run-long.
// Read once, in QuickStartDrawItem's tier roll.
#define QUICKSTART_FOOD_RARE_LUCK (1 << 13)
#define QUICKSTART_FOOD_COUNT 14
#define QUICKSTART_CHEAP_SHOP_PRICE 50

// D2: the persistent living-enemy count. Six bits per pool region (wave
// caps are 50, so 63 fits) recording how many of the region's CURRENT
// wave are still alive, so a round trip into a ? room, a cave, a fusion's
// room-reload, or any other pocket within the region RESUMES the fight -
// only the remainder respawns - instead of putting the whole wave back.
// Cleared (forcing a full fresh wave) in exactly two cases, per the user:
// the wave is genuinely cleared, or the player is seen settled in a
// DIFFERENT region (or the hub) - leaving the region is the reset;
// everything within it persists. 63 doubles as the "just spawned, count
// unknown" sentinel: the wave watcher min-updates it to the true live
// count on the next settled frame and on every kill after. In the run
// wipe's 202-703 range, so a new run starts clean.
#define GF_REGION_ALIVE_BIT(i, b) (509 + (i) * 6 + (b)) // i = 0..11 -> 509-580
#define QUICKSTART_ALIVE_UNKNOWN 63

// 3-state like the old ITEM_32/ITEM_5A markers this replaces: 0 = not
// earned yet, 1 = earned and a ground item is (or was) dropped, 2 =
// confirmed actually picked up.
static u8 QuickStartGetRegionRewardState(s32 poolIndex) {
    return (QsCheckFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 0)) ? 1 : 0) |
           (QsCheckFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 1)) ? 2 : 0);
}

static void QuickStartSetRegionRewardState(s32 poolIndex, u8 value) {
    if (value & 1) {
        QsSetFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 0));
    } else {
        QsClearFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 0));
    }
    if (value & 2) {
        QsSetFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 1));
    } else {
        QsClearFlag(GF_REGION_REWARD_STATE_BIT(poolIndex, 1));
    }
}

// Lon Lon Ranch's own quirks (Goron/animal removal; its boulder-hole
// crossings are handled by the generalized QuickStartFillBoulderHoles now).
static void QuickStartLonLonRanchQuirkHook(void) {
    QuickStartClearLonLonRanchAnimals();
}

// North Hyrule Field has one native BUSINESS_SCRUB_PROLOGUE (a one-time
// vanilla prologue NPC) that spawns as kind ENEMY, not NPC - confirmed in
// the emulator that it's present at boot with no player action needed. Left
// alive it would permanently block QuickStartRegionWaveCleared (which
// requires zero ENEMY-kind entities in the room), so it needs the same
// "delete on sight" treatment as Castle Garden's guards/Lon Lon's Goron.
static void QuickStartClearNorthFieldScrub(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == ENEMY && gEntities[i].base.id == BUSINESS_SCRUB_PROLOGUE) {
            DeleteEntity(&gEntities[i].base);
        }
    }
}

// South Hyrule Field, North Hyrule Field, and Trilby Highlands - the first
// 3 of the 5 additional regions from docs/QUICKSTART_ROADMAP.md sec 2.1's
// table, surveyed one pass after Castle Garden/Lon Lon Ranch's own
// generalization. Entrance/exit/enemy-grid data below comes from a
// collision-data scan (gMapBottom.collisionData/actTiles read directly via
// mgba, filtering out both real wall collision and water/lilypad act-tiles)
// for open 3x3-tile neighborhoods, the same method the original two
// regions' own grids used, plus spot-checks in the emulator (screenshots
// confirming dry land, not a lake). Exit boxes are one of each room's own
// user-surveyed real transition edges (given several pixels of thickness
// perpendicular to the edge for a workable trigger box) - which real
// neighbor it used to lead to doesn't matter now that the chain always
// portals to whichever region comes next (see QuickStartProcessRegionChainLinks).
// Reward spot reused from Castle Garden's; the reward itself is a tier draw,
// same as Lon Lon Ranch. No boss hook for any of the three yet, per the
// "boss-less for now" plan - only Castle Garden has one so far.
static const s16 sQuickStartSouthFieldEnemyOffsets[][2] = {
    { 504, 24 },  { 504, 72 },  { 744, 72 },  { 840, 72 },  { 72, 120 },  { 120, 120}, { 456, 120},
    { 504, 120}, { 552, 120}, { 696, 120}, { 744, 120}, { 792, 120}, { 840, 120}, { 888, 120},
    { 936, 120}, { 984, 120}, { 504, 168}, { 888, 168}, { 504, 216}, { 888, 216}, { 504, 264},
    { 552, 264}, { 840, 264}, { 888, 264}, { 456, 312}, { 504, 312}, { 792, 312}, { 840, 312},
    { 888, 312}, { 456, 360}, { 504, 360}, { 840, 360}, { 888, 360}, { 456, 408}, { 504, 408},
    { 840, 408}, { 888, 408}, { 456, 456}, { 504, 456}, { 600, 456}, { 888, 456}, { 504, 504},
    { 504, 552}, { 552, 552}, { 600, 552}, { 648, 552}, { 840, 552}, { 72, 600},
};
#define QUICKSTART_SOUTHFIELD_ROOM_SQUARES 651
#define QUICKSTART_SOUTHFIELD_MAX_ENEMIES 50

static const s16 sQuickStartNorthFieldEnemyOffsets[][2] = {
    { 504, 120}, { 936, 120}, { 984, 120}, { 504, 168}, { 72, 216},  { 504, 216}, { 72, 264},
    { 504, 264}, { 648, 264}, { 696, 264}, { 840, 264}, { 72, 312},  { 120, 312}, { 504, 312},
    { 648, 312}, { 696, 312}, { 840, 312}, { 72, 360},  { 120, 360}, { 504, 360}, { 648, 360},
    { 696, 360}, { 744, 360}, { 504, 408}, { 648, 408}, { 408, 456}, { 456, 456}, { 504, 456},
    { 552, 456}, { 600, 456}, { 744, 504}, { 504, 552}, { 552, 552}, { 600, 552}, { 24, 600},
    { 72, 600},  { 504, 600}, { 552, 600}, { 264, 648}, { 312, 648}, { 360, 648}, { 504, 648},
    { 840, 648}, { 888, 648}, { 984, 648}, { 264, 696}, { 312, 696}, { 360, 696}, { 408, 696},
    { 456, 696}, { 504, 696}, { 552, 696}, { 600, 696}, { 648, 696}, { 696, 696}, { 744, 696},
    { 792, 696}, { 840, 696}, { 888, 696}, { 264, 744}, { 312, 744}, { 360, 744}, { 408, 744},
    { 456, 744}, { 504, 744}, { 552, 744}, { 600, 744}, { 648, 744}, { 696, 744}, { 744, 744},
    { 792, 744}, { 840, 744},
};
#define QUICKSTART_NORTHFIELD_ROOM_SQUARES 775
#define QUICKSTART_NORTHFIELD_MAX_ENEMIES 50

static const s16 sQuickStartTrilbyEnemyOffsets[][2] = {
    { 120, 24 },  { 360, 120}, { 408, 120}, { 456, 120}, { 360, 168}, { 312, 360}, { 360, 360},
    { 24, 408 },  { 360, 408}, { 360, 456}, { 312, 504}, { 360, 504}, { 408, 504}, { 360, 552},
    { 408, 552}, { 456, 552}, { 360, 840}, { 312, 888}, { 360, 888}, { 360, 936},
    // The southwest pocket, tiles (1,35)-(10,44) - opened by the solved
    // boulder crossing + restored through-cave, flood-verified open (see
    // QuickStartTrilbyQuirkHook). Eight spots spread across it per the
    // user's request that the field host spawns.
    { 40, 584 },  { 120, 584}, { 24, 632 }, { 104, 632}, { 40, 664 },  { 120, 664}, { 56, 696 },
    { 136, 696},
};
#define QUICKSTART_TRILBY_ROOM_SQUARES 450
#define QUICKSTART_TRILBY_MAX_ENEMIES 50

// Castle Garden and Lon Lon Ranch (the original two, refactored per
// docs/QUICKSTART_ROADMAP.md sec 3.1's own "become the first two rows in
// that table" plan) plus South Hyrule Field, North Hyrule Field, and
// Trilby Highlands (the first 3 of the roadmap's 5 additional regions,
// surveyed this pass - see the block comment above their data). Castor
// Wilds and Eastern Hills (the latter split across 3 real rooms - South/
// Center/North - needing its own separate look) are still not in the pool
// yet and get appended in a later pass.
// --- Eastern Hills and Western Wood: the overworld expansion's six rooms --
// Surveyed the same way as the three field regions above: the live
// collision grid read in the emulator, flooded from a seam the ring tests
// proved walkable, offsets farthest-point sampled over open 3x3
// neighbourhoods so they spread across the reachable component instead of
// clustering. Entrance and reward share the central open tile - nothing
// warps a player to a region entrance any more, so the field only anchors
// tooling, the wave centre and the rescue failsafe.
//
// Eastern Hills North is TWO components: a small southwest pocket (the SHF
// seam) and the main body (the LLR gap and everything east). The grid uses
// the main body only - an enemy in the pocket would be unreachable from
// the region's own through-routes.
static const s16 sQuickStartEasternHillsSouthEnemyOffsets[][2] = {
    { 72, 168 },  { 168, 24 },  { 408, 168 }, { 152, 152 }, { 328, 24 },
    { 344, 152 }, { 376, 120 }, { 120, 136 }, { 360, 88 },
};
static const s16 sQuickStartEasternHillsCenterEnemyOffsets[][2] = {
    { 72, 216 },  { 328, 232 }, { 104, 56 },  { 200, 200 }, { 168, 88 },
    { 264, 24 },  { 280, 184 }, { 56, 88 },   { 120, 184 }, { 216, 56 },
    { 152, 216 }, { 120, 88 },  { 152, 56 },  { 232, 184 }, { 312, 200 },
};
static const s16 sQuickStartEasternHillsNorthEnemyOffsets[][2] = {
    { 328, 24 },  { 40, 216 },  { 344, 456 }, { 168, 104 }, { 120, 328 },
    { 424, 248 }, { 152, 232 }, { 280, 120 }, { 312, 344 }, { 184, 296 },
    { 328, 232 }, { 264, 56 },  { 104, 216 }, { 120, 264 }, { 200, 216 },
    { 280, 216 }, { 296, 296 }, { 312, 72 },  { 312, 408 }, { 360, 264 },
};
static const s16 sQuickStartWesternWoodsSouthEnemyOffsets[][2] = {
    { 424, 24 },  { 40, 56 },   { 328, 152 }, { 296, 40 },  { 72, 152 },
    { 360, 72 },  { 168, 152 }, { 40, 120 },  { 72, 88 },   { 312, 88 },
    { 184, 72 },  { 328, 56 },  { 392, 56 },  { 424, 72 },
};
static const s16 sQuickStartWesternWoodsCenterEnemyOffsets[][2] = {
    { 424, 24 },  { 376, 120 }, { 296, 24 },  { 296, 136 }, { 328, 72 },
    { 392, 72 },  { 424, 104 }, { 248, 120 }, { 264, 40 },  { 312, 104 },
    { 360, 88 },
};
static const s16 sQuickStartWesternWoodsNorthEnemyOffsets[][2] = {
    { 72, 88 },   { 40, 552 },  { 408, 136 }, { 296, 616 }, { 40, 296 },
    { 200, 520 }, { 360, 280 }, { 104, 440 }, { 184, 152 }, { 344, 24 },
    { 312, 456 }, { 72, 200 },  { 136, 568 }, { 312, 104 }, { 328, 200 },
    { 344, 376 }, { 40, 392 },  { 200, 408 }, { 248, 568 }, { 408, 232 },
    { 40, 472 },  { 88, 504 },  { 104, 152 }, { 232, 456 },
};

static const QuickStartRegion sQuickStartRegionPool[] = {
    // Castle Garden - entrance/exit reused from the old static
    // sQuickStartLinks rows (Melari's Mine Door B's destination, and the
    // real north door's own trigger box), enemy grid/reward pool/spot
    // unchanged from the old QuickStartSpawnGarden*/sQuickStartGarden*
    // functions/data above.
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 0x1f8, 0x1e0, 488, 520, 16, 56, sQuickStartGardenEnemyOffsets,
      ARRAY_COUNT(sQuickStartGardenEnemyOffsets), QUICKSTART_GARDEN_ROOM_SQUARES, QUICKSTART_GARDEN_MAX_ENEMIES,
      0x1f8, 0x108,
      QuickStartClearCastleGuards },
    // Lon Lon Ranch - entrance/exit reused from the old static
    // sQuickStartLinks rows (Castle Garden's own north-door destination,
    // and Lon Lon's own return box), enemy grid unchanged from
    // sQuickStartLonLonRanchEnemyOffsets above. Reward pool reused
    // from the shared tier table (QuickStartDrawItem) - this region
    // never actually draws from it while it's the chain's last slot (the
    // Earth Element/win path takes over instead, see
    // QuickStartSpawnRegionRewardOnce below), only if a future, bigger
    // chain ever puts it somewhere other than last.
    //
    // Reward spot moved from (392,159) to (264,712). The old spot sits
    // inside the Cane of Pacci ledge the user walked and fenced off in
    // sQuickStartGatedZones ({228..475, 0..167}), so when Lon Lon Ranch
    // came up as the chain's last slot the Earth Element - the run's whole
    // objective - dropped somewhere a player without the Cane could not
    // stand, and the Chuchu Boss and the normal loot drop landed there too.
    // The new spot is on the open field north of the region's own entrance,
    // walked in the emulator from (344,870) straight up to (344,711) and
    // then west through (264,711), so it is provably in the same connected
    // component as the point the player arrives at.
    //
    // Exit box moved from (287-343, 966-984) to (288-336, 928-956). The old
    // box was OUTSIDE the room: Lon Lon Ranch is 720x960, so y 966-984 is
    // past the bottom edge and no amount of walking could ever put the player
    // inside it. That is a leftover from the hardwired Castle Garden -> Lon
    // Lon ordering, when this region was always the chain's last slot and its
    // onward box was never exercised. It only ever fired on the frames a
    // border transition carried the player's coordinates past the edge, which
    // is why the user saw "no exits work except the south one, and coming
    // back UP into the ranch teleports me to the next region".
    //
    // The new box is the funnel into the same southern gap, measured off the
    // room's own act tiles: the bottom row (y 944) is solid except tiles
    // 18-21, i.e. x 288-336, and the corridor above it is open from x 240 to
    // x 448. Sitting at y 928-956 it is 58px below the (344,870) arrival
    // spot and 8px west of it, so arriving does not trip it but deliberately
    // walking down the gap does - and it now fires before vanilla's own
    // border transition rather than after.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 344, 870, 288, 336, 928, 956,
      sQuickStartLonLonRanchEnemyOffsets, ARRAY_COUNT(sQuickStartLonLonRanchEnemyOffsets), QUICKSTART_LONLON_ROOM_SQUARES,
      QUICKSTART_LONLON_MAX_ENEMIES, 264, 712,
      QuickStartLonLonRanchQuirkHook },
    // South Hyrule Field - entrance (504,264) and reward spot (648,552) are
    // both verified-open, non-water tiles from the collision scan. Exit box
    // is the user-surveyed top edge (467,10)-(539,10) padded to a 0-30 y
    // band (a workable trigger thickness; that edge's real vanilla
    // destination doesn't matter, see the block comment above).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, 504, 264, 460, 546, 0, 30,
      sQuickStartSouthFieldEnemyOffsets, ARRAY_COUNT(sQuickStartSouthFieldEnemyOffsets), QUICKSTART_SOUTHFIELD_ROOM_SQUARES,
      QUICKSTART_SOUTHFIELD_MAX_ENEMIES, 648, 552,
      NULL },
    // North Hyrule Field - entrance (504,456) and reward spot (744,504) are
    // verified-open. Exit box is the user-surveyed bottom edge
    // (484,797)-(524,797) padded to a 770-800 y band. Needs
    // QuickStartClearNorthFieldScrub (see above) for the native
    // BUSINESS_SCRUB_PROLOGUE that otherwise blocks wave-clear detection.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 504, 456, 478, 530, 770, 800,
      sQuickStartNorthFieldEnemyOffsets, ARRAY_COUNT(sQuickStartNorthFieldEnemyOffsets), QUICKSTART_NORTHFIELD_ROOM_SQUARES,
      QUICKSTART_NORTHFIELD_MAX_ENEMIES, 744, 504,
      QuickStartClearNorthFieldScrub },
    // Trilby Highlands - entrance (360,360) and reward spot (360,504) are
    // both spot-checked with screenshots (dry land next to the room's
    // lake/waterfall, not in the water itself). Exit box is the
    // user-surveyed right edge (472,535)-(472,590) padded to a 465-480 x
    // band (room width is only 480px, so this sits right at the edge).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, 360, 360, 465, 480, 525, 600,
      sQuickStartTrilbyEnemyOffsets, ARRAY_COUNT(sQuickStartTrilbyEnemyOffsets), QUICKSTART_TRILBY_ROOM_SQUARES,
      QUICKSTART_TRILBY_MAX_ENEMIES, 360, 504,
      QuickStartTrilbyQuirkHook },
    // The six overworld-expansion rooms. Exit boxes are dead fields (the
    // warp mechanic is retired) and zeroed. No quirk hooks: the outdoor
    // entity dumps found only OBJECT-kind scenery, no enemy-kind blockers.
    // Squares/max from the flood: reachable tiles, cap ~ squares/13.
    // All three Eastern Hills rooms run the vanilla-NPC sweep: story/fusion
    // flags can conjure the farm's scripted population onto the walkways
    // (the user's screenshot had a pair walling off the stair gap by the
    // farmhouse), and a ? region owes the player a swept room.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH, 328, 104, 0, 0, 0, 0,
      sQuickStartEasternHillsSouthEnemyOffsets, ARRAY_COUNT(sQuickStartEasternHillsSouthEnemyOffsets), 265, 20,
      328, 104, QuickStartClearEasternHillsNpcs },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER, 248, 104, 0, 0, 0, 0,
      sQuickStartEasternHillsCenterEnemyOffsets, ARRAY_COUNT(sQuickStartEasternHillsCenterEnemyOffsets), 285, 21,
      248, 104, QuickStartClearEasternHillsNpcs },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH, 264, 264, 0, 0, 0, 0,
      sQuickStartEasternHillsNorthEnemyOffsets, ARRAY_COUNT(sQuickStartEasternHillsNorthEnemyOffsets), 458, 35,
      264, 264, QuickStartClearEasternHillsNpcs },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH, 200, 104, 0, 0, 0, 0,
      sQuickStartWesternWoodsSouthEnemyOffsets, ARRAY_COUNT(sQuickStartWesternWoodsSouthEnemyOffsets), 217, 16,
      200, 104, NULL },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER, 264, 88, 0, 0, 0, 0,
      sQuickStartWesternWoodsCenterEnemyOffsets, ARRAY_COUNT(sQuickStartWesternWoodsCenterEnemyOffsets), 121, 9,
      264, 88, NULL },
    // Max 24, not the squares/13 = 46 the survey formula suggests. This
    // room carries the ring's heaviest fixed sheet load - five fusers plus
    // its own vanilla object clutter - and the gfx tier measured the wave's
    // one-frame spawn burst dipping to 1 free sprite slot at difficulty 8
    // against the checker's floor of 2 (the burst reads a stale free count,
    // and the reaper only settles it a few dozen frames later). 24 keeps
    // the burst small enough that the worst frame stays above the floor.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, 248, 360, 0, 0, 0, 0,
      sQuickStartWesternWoodsNorthEnemyOffsets, ARRAY_COUNT(sQuickStartWesternWoodsNorthEnemyOffsets), 607, 24,
      248, 360, NULL },
};
#define QUICKSTART_REGION_POOL_SIZE (s32)(sizeof(sQuickStartRegionPool) / sizeof(QuickStartRegion))
// (QUICKSTART_TRILBY_POOL_INDEX / QUICKSTART_LONLON_POOL_INDEX retired with
// the chain draw and the region unlock rules - nothing special-cases either
// region any more.)

// --- The meta-progression unlock registry (roadmap B1) ---------------------
// One table every randomized draw consults, so "what this save has earned"
// lives in exactly one place. Two currencies, both persistent u32s in gSave
// (see save.h): meta_xp (each win's score, ~800-2000 per win, added at the
// win screen) and runs_completed (wins). A rule is satisfied once its
// counter reaches its threshold - unlocks never re-lock, since neither
// counter ever decreases.
//
// Content this save has NOT earned yet must never be drawn - the pick
// functions fall back to an always-unlocked kind, and the region chain
// draw rejects locked pool rows. The draw math that makes the rejection
// loop safe: at 0 wins the chain is 2 and 3 regions are unlocked (Castle
// Garden/South Field/North Field); 1 win -> chain 3, Lon Lon joins (4);
// 2 wins -> chain 4, exactly the 4 non-Trilby regions, with Trilby only
// ever entering via the forced-last Flippers path. Unlocked count >= chain
// length at every step.
// The two REGION unlock rules (Lon Lon at 1 win, Trilby at 2) are retired:
// with the overworld a freely walkable ring, a region cannot be "locked" -
// the player can walk into it. Only content-kind unlocks remain.
enum {
    QUICKSTART_UNLOCK_KIND_POT_LOTTERY,
    QUICKSTART_UNLOCK_KIND_CHEST_LOTTERY,
    QUICKSTART_UNLOCK_KIND_FAIRY,
    QUICKSTART_UNLOCK_COUNT,
};

typedef struct {
    u8 byWins;     // 1: threshold counts runs_completed; 0: counts meta_xp
    u16 threshold;
} QuickStartUnlockRule;

// Thresholds calibrated against the measured score range (~800-2000 per
// winning run): the pot lottery arrives with the first decent score, the
// chest lottery a win or two later, everything else is win-gated.
static const QuickStartUnlockRule sQuickStartUnlockRules[QUICKSTART_UNLOCK_COUNT] = {
    { 0, 500 },  // QUICKSTART_UNLOCK_KIND_POT_LOTTERY
    { 0, 1500 }, // QUICKSTART_UNLOCK_KIND_CHEST_LOTTERY
    { 1, 1 },    // QUICKSTART_UNLOCK_KIND_FAIRY
};

// Master switch for the progression gate. Off (0) per the user, Aug 2026:
// "turn off the unlocking system - all items/rooms/features should be
// available random options at all levels."
//
// Everything the registry describes stays intact - the rules table, the
// score and win counters it reads, the call sites that ask - so turning it
// back on is this one line. That matters because the meta loop is still
// the design's centre; what is being switched off is the gating, not the
// idea, and the thresholds were never tuned against real play anyway
// (Decision 2 in section 5 of the roadmap).
#define QUICKSTART_UNLOCKS_ENABLED 0

static bool32 QuickStartIsUnlocked(u32 unlockId) {
#if QUICKSTART_UNLOCKS_ENABLED
    const QuickStartUnlockRule* rule = &sQuickStartUnlockRules[unlockId];
    if (rule->byWins) {
        return gSave.runs_completed >= rule->threshold;
    }
    return gSave.meta_xp >= rule->threshold;
#else
    return TRUE;
#endif
}

// Which pool row the current room belongs to, or -1 if it isn't a pool
// region at all. Every region is live every run now, so this is a plain
// table scan - no per-save chain indirection left.
static s32 QuickStartCurrentRegionPoolIndex(void) {
    s32 i;
    for (i = 0; i < QUICKSTART_REGION_POOL_SIZE; i++) {
        const QuickStartRegion* region = &sQuickStartRegionPool[i];
        if (gRoomControls.area == region->area && gRoomControls.room == region->room) {
            return i;
        }
    }
    return -1;
}

// Which pool region hides the Earth Element this run.
static s32 QuickStartElementRegionIndex(void) {
    s32 b, value = 0;
    for (b = 0; b < 4; b++) {
        if (QsCheckFlag(GF_ELEMENT_REGION_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value % QUICKSTART_REGION_POOL_SIZE;
}

// Which pool region the hub's pit drops the player into this run - drawn
// once per run, so every fall within a run lands in the same place, and a
// new run lands somewhere new (per the user, bringing the randomness back
// after the fixed-Castle-Garden interim).
static s32 QuickStartDropRegionIndex(void) {
    s32 b, value = 0;
    for (b = 0; b < 4; b++) {
        if (QsCheckFlag(GF_DROP_REGION_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value % QUICKSTART_REGION_POOL_SIZE;
}

// --- The NAMED regions and their map adjacency -----------------------------
//
// The pool is 11 rooms but the ring is SEVEN named regions (Eastern Hills
// and Western Wood are three rooms each), and the element-distance rule
// below is stated in named regions. Adjacency is the vanilla MAP's - two
// regions sharing an edge, plus the two town bridges - which is exactly the
// metric the user's own example uses ("if the player lands in Hyrule Castle
// Garden, the element could be in HCG (0), NHF (1), Lon Lon Ranch (2), SHF
// (2) or Trilby Highlands (2)"): NHF touches LLR and Trilby on the map even
// though those particular seams are cliff-walled in play, so walking
// distance can exceed map distance. That is fine - the rule shapes where
// the element may HIDE, not a route.
enum {
    QS_RING_CG,
    QS_RING_NHF,
    QS_RING_SHF,
    QS_RING_EH,
    QS_RING_LLR,
    QS_RING_TRIL,
    QS_RING_WW,
    QS_RING_COUNT
};

static const u8 sQuickStartRingAdjacency[QS_RING_COUNT] = {
    /* CG   */ (1 << QS_RING_NHF),
    /* NHF  */ (1 << QS_RING_CG) | (1 << QS_RING_SHF) | (1 << QS_RING_LLR) | (1 << QS_RING_TRIL),
    /* SHF  */ (1 << QS_RING_NHF) | (1 << QS_RING_EH) | (1 << QS_RING_WW),
    /* EH   */ (1 << QS_RING_SHF) | (1 << QS_RING_LLR),
    /* LLR  */ (1 << QS_RING_EH) | (1 << QS_RING_NHF) | (1 << QS_RING_TRIL),
    /* TRIL */ (1 << QS_RING_LLR) | (1 << QS_RING_NHF) | (1 << QS_RING_WW),
    /* WW   */ (1 << QS_RING_TRIL) | (1 << QS_RING_SHF),
};

// Which named region a pool row belongs to. By position: the pool's row
// order is CG, LLR, SHF, NHF, TRIL, then EH South/Center/North, then WW
// South/Center/North.
static u8 QuickStartRingRegionOfPoolIndex(s32 poolIndex) {
    static const u8 byPool[] = {
        QS_RING_CG, QS_RING_LLR, QS_RING_SHF, QS_RING_NHF, QS_RING_TRIL,
        QS_RING_EH, QS_RING_EH, QS_RING_EH,
        QS_RING_WW, QS_RING_WW, QS_RING_WW,
    };
    return byPool[poolIndex % QUICKSTART_REGION_POOL_SIZE];
}

// Every named region within two map steps of `ring`, as a bitmask
// (including itself).
static u32 QuickStartRingWithinTwo(u8 ring) {
    u32 one = (1u << ring) | sQuickStartRingAdjacency[ring];
    u32 two = one;
    s32 r;
    for (r = 0; r < QS_RING_COUNT; r++) {
        if (one & (1u << r)) {
            two |= sQuickStartRingAdjacency[r];
        }
    }
    return two;
}

// Two draws per run, and they are COUPLED - this is the chain's return in
// its new form, per the user.
//
// First the pit's DROP region: uniform over the whole pool, so a run can
// begin anywhere in the ring. Then the ELEMENT region: uniform over the
// pool rows whose named region is within TWO map steps of the drop's
// (QuickStartRingWithinTwo) - close enough that finding it is a hunt, not
// a tour. The rejection loop terminates because the drop's own region is
// always within its own two steps.
//
// Rolled unconditionally from QuickStartRoomMonitor, same "roll it well
// before the player can reach it" reasoning every other per-run draw uses.
// The old chain draw's Zora Flippers special case (force Trilby last)
// stays retired: no key item re-routes the run.
static void QuickStartRollElementRegionOnce(void) {
    s32 drop, elem, b;
    u32 allowed;
    if (QsCheckFlag(GF_ELEMENT_REGION_ROLLED)) {
        return;
    }
    drop = (s32)Random() % QUICKSTART_REGION_POOL_SIZE;
    for (b = 0; b < 4; b++) {
        if (drop & (1 << b)) {
            QsSetFlag(GF_DROP_REGION_BIT(b));
        }
    }
    QsSetFlag(GF_DROP_REGION_ROLLED);
    allowed = QuickStartRingWithinTwo(QuickStartRingRegionOfPoolIndex(drop));
    for (;;) {
        elem = (s32)Random() % QUICKSTART_REGION_POOL_SIZE;
        if (allowed & (1u << QuickStartRingRegionOfPoolIndex(elem))) {
            break;
        }
    }
    for (b = 0; b < 4; b++) {
        if (elem & (1 << b)) {
            QsSetFlag(GF_ELEMENT_REGION_BIT(b));
        }
    }
    QsSetFlag(GF_ELEMENT_REGION_ROLLED);
}

// Moved up from next to QuickStartGetDifficulty/QuickStartIncrementDifficulty
// further down this file (still the canonical home for the rest of that
// comment) - needed here first, by QuickStartSpawnRegionWave's own
// escalating-difficulty clamp below.
#define QUICKSTART_MAX_DIFFICULTY 12

// Same "is any ENEMY-kind entity still in this room" check every kind of
// wave-clear detection in this file already uses. Only ever consulted for
// wave 0 (see QuickStartSpawnRegionRewardOnce - the reward/Earth Element
// only ever cares about the first wave), and wave 0 is always a plain
// tiered group, never a Chuchu Boss (QuickStartSpawnRegionWave below), so
// there's no separate "boss has actually appeared yet" race to guard
// against here the way the old Castle-Garden-only boss hook needed to.
static bool32 QuickStartRegionWaveCleared(void) {
    s32 i;
    if (!QsCheckRoomFlag(0)) {
        return FALSE;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (gEntities[i].base.kind == ENEMY && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
            return FALSE;
        }
    }
    return TRUE;
}

// Endless-wave state - persistent (FLAG_BANK_11, completely unclaimed
// RETIRED: GF_REGION_WAVE_COUNT_BIT, the chain-slot-keyed wave counters at
// FLAG_BANK_11 142-173 (free now). Wave counters are per POOL INDEX in the
// QS window instead (GF_REGION_WAVE_BIT, with the rest of the free-roam
// per-region state) - a chain slot stopped existing, and pool-index keying
// is what lets a counter follow its physical region. They still persist
// across leaving/re-entering a region within a run (that requirement is
// unchanged) and still reset per run via the 202-703 wipe.
// Out of 100 - the chance any wave AFTER the first (wave 0 is always a
// plain group, see QuickStartSpawnRegionWave) rolls as a solo Chuchu Boss
// encounter instead. Never concurrent with a normal wave's own enemies -
// only ever rolled once the room is already fully clear - so this doesn't
// reopen the GFX-slot budget question that capped the old Castle-Garden-
// only pairing to "boss alone" in the first place (docs/QUICKSTART_ROADMAP.md
// sec 3.3, this session's scratchpad/test_gfx_boss_cost.py).
// 20 -> 10 per the user, alongside the second charm batch: with the ring
// fully populated and every region's wave loop rolling this, one in five
// was making bosses routine rather than an event.
#define QUICKSTART_REGION_BOSS_WAVE_CHANCE 10
// GFX slots (free-or-evictable - QuickStartReclaimableGfxSlots, since
// the loader reclaims unreferenced sheets on demand) a room must offer
// before the boss roll may fire. The family + start particles cost 14
// slots (measured in a quiet dojo: 21 free -> 7 after a full 5-piece
// spawn). Below the cost, pieces fail to spawn - a PARTIAL family whose
// survivors deref dangling parent/child pointers - which is the "boss
// started spawning and never finished" half of the user's NHF report.
// 16 = cost + margin. Below the gate, the wave loop deals a normal wave.
#define QUICKSTART_BOSS_SPAWN_MIN_GFX 16

static u8 QuickStartRegionGetWaveCount(s32 poolIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 8; b++) {
        if (QsCheckFlag(GF_REGION_WAVE_BIT(poolIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartRegionSetWaveCount(s32 poolIndex, u8 value) {
    s32 b;
    for (b = 0; b < 8; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_REGION_WAVE_BIT(poolIndex, b));
        } else {
            QsClearFlag(GF_REGION_WAVE_BIT(poolIndex, b));
        }
    }
}

static u8 QuickStartRegionGetAliveCount(s32 poolIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 6; b++) {
        if (QsCheckFlag(GF_REGION_ALIVE_BIT(poolIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartRegionSetAliveCount(s32 poolIndex, u8 value) {
    s32 b;
    if (value > QUICKSTART_ALIVE_UNKNOWN) {
        value = QUICKSTART_ALIVE_UNKNOWN;
    }
    for (b = 0; b < 6; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_REGION_ALIVE_BIT(poolIndex, b));
        } else {
            QsClearFlag(GF_REGION_ALIVE_BIT(poolIndex, b));
        }
    }
}

// The live in-room ENEMY headcount the alive-counter records, plus whether
// any of them is a boss piece - boss waves are setpieces and are never
// resumed (a "remainder" of jelly pieces respawned through the plain group
// spawner would come back as ordinary enemies).
static s32 QuickStartCountRegionEnemies(bool32* hasBoss) {
    s32 i, count = 0;
    *hasBoss = FALSE;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY && QuickStartEntityInCurrentRoom(ent)) {
            count++;
            if (ent->id == CHUCHU_BOSS) {
                *hasBoss = TRUE;
            }
        }
    }
    return count;
}

// Rolls and spawns wave `wave` (0-indexed) for this region. Difficulty
// escalates with wave count on top of the run's own persistent difficulty
// counter (QuickStartGetDifficulty) - reusing the exact same tier table
// (sQuickStartDifficultyTiers/QuickStartSpawnEnemyGroupAtDifficulty) a
// normal wave already draws from, just at a higher tier the deeper into
// one sitting the player gets.
// Whether a region may roll the Chuchu Boss wave at all. Per the user, only
// the three rooms where the boss has been SEEN working: Castle Garden,
// North Hyrule Field and South Hyrule Field. The small rooms cannot host it
// - the boss locked the whole game up in Eastern Hills South (the seam
// scroll into a 480x208 room mid-spawn) - and the rest of the ring is
// paused, not vetted, so the list is an allowlist rather than a blocklist:
// a new region gets bosses when someone has watched one work there.
static bool32 QuickStartRegionAllowsBoss(const QuickStartRegion* region) {
    if (region->area == AREA_CASTLE_GARDEN && region->room == ROOM_CASTLE_GARDEN_MAIN) {
        return TRUE;
    }
    if (region->area != AREA_HYRULE_FIELD) {
        return FALSE;
    }
    // Trilby joined the list per the user, with its own arena: the boss
    // spawns in the enclosed southwest pocket instead of at the reward spot
    // (see the spawn override in QuickStartSpawnRegionWave and the
    // containment clamp in QuickStartTrilbyQuirkHook).
    return region->room == ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD ||
           region->room == ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD ||
           region->room == ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS;
}

// "The boss wave rolled but the room can't pay for it YET" - per-visit
// latch for the deferred spawn below. Numbered beside the other wave-loop
// flags (0 = wave up, 4 = clear hint shown).
#define QUICKSTART_BOSS_OWED_FLAG 8
// How long a deferred boss waits for the gfx table to recover before the
// loop gives up and deals a normal wave instead. Ten seconds: kill drops
// (the usual pressure - measured, a cleared wave's uncollected drops hold
// reclaimable at 8 of the 16 the boss needs) despawn in ~8.5s, so a room
// that is going to recover has recovered by then, and a room under fixed
// sheet pressure (WW North's fusers) doesn't sit empty forever.
#define QUICKSTART_BOSS_OWED_TIMEOUT (10 * 60)

// --- The escalation clock ------------------------------------------------
//
// In-region difficulty used to be runDifficulty + waveCount, one step per
// cleared wave regardless of how big that wave was. But wave size comes
// from ROOM size, so small rooms handed out difficulty far faster per unit
// of actual play - the user's report that Eastern Hills "goes up very
// rapidly" because its rooms hold few enemies and clear quickly.
//
// Measured on the live tables before this change: Eastern Hills South
// spawns NINE enemies per wave at every difficulty (its verified-spot pool
// only has nine entries, so neither density nor difficulty can raise it)
// and walked from wave 0 to maximum difficulty in 117 kills, against North
// Hyrule Field's 362 - a 3.1x faster climb per kill, with Western Wood
// Center at 3.4x. Worse, Eastern Hills is three region slots with three
// independent counters, so "spending a while in Eastern Hills" is really
// three fast clocks at once.
//
// The fix prices a difficulty step in KILLS instead of in waves. A
// region's base wave size is already implied by its table row, so this
// needs no new saved state: it is pure arithmetic over constants, which
// also means it recomputes identically on every frame of a visit.
#define QUICKSTART_ESCALATION_KILLS 30
#define QUICKSTART_BASE_DENSITY 25

static s32 QuickStartRegionBaseWave(const QuickStartRegion* region) {
    s32 base = region->roomSquares / QUICKSTART_BASE_DENSITY;
    if (base > region->enemyOffsetCount) {
        base = region->enemyOffsetCount;
    }
    if (base > region->maxEnemies) {
        base = region->maxEnemies;
    }
    if (base < 1) {
        base = 1;
    }
    return base;
}

// How many difficulty steps this region's wave counter has actually earned.
static s32 QuickStartEscalationSteps(const QuickStartRegion* region, u8 wave) {
    return ((s32)wave * QuickStartRegionBaseWave(region)) / QUICKSTART_ESCALATION_KILLS;
}

static s32 QuickStartEscalatedDifficulty(const QuickStartRegion* region, u8 wave) {
    s32 escalated = (s32)QuickStartGetDifficulty() + QuickStartEscalationSteps(region, wave);
    if (escalated > QUICKSTART_MAX_DIFFICULTY) {
        escalated = QUICKSTART_MAX_DIFFICULTY;
    }
    return escalated;
}

// Returns TRUE if a wave (or the boss) actually spawned; FALSE while a
// rolled boss is deferred waiting for gfx. The caller only marks the room
// "wave up" on TRUE.
static bool32 QuickStartSpawnRegionWave(const QuickStartRegion* region, u8 wave) {
    s32 escalated;
    // A boss the room owes from an earlier frame's roll. Measured on the
    // live game (scratchpad/gate_measure.py): at the instant a cleared
    // wave respawns, the just-killed wave's uncollected drops still hold
    // sheet slots, so QuickStartReclaimableGfxSlots reads 8-15 against the
    // gate's 16 and the old "fall through to a normal wave" behaviour
    // meant the boss NEVER actually appeared mid-region - the only bosses
    // players ever saw came out of the region-entry bug this batch also
    // fixes. Deferring the owed spawn until the table recovers (drops
    // despawn or get picked up within seconds) is what makes the 10% roll
    // real. The room simply stays quiet for those few seconds.
    if (QsCheckRoomFlag(QUICKSTART_BOSS_OWED_FLAG)) {
        if (QuickStartReclaimableGfxSlots() >= QUICKSTART_BOSS_SPAWN_MIN_GFX) {
            Entity* boss = CreateEnemy(CHUCHU_BOSS, ((s32)Random() & 1) ? 4 : 0);
            QsClearRoomFlag(QUICKSTART_BOSS_OWED_FLAG);
            if (boss != NULL) {
                s16 bossX = region->rewardX;
                s16 bossY = region->rewardY;
                if (region->area == AREA_HYRULE_FIELD && region->room == ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS) {
                    bossX = 88;
                    bossY = 600;
                }
                boss->x.HALF.HI = gRoomControls.origin_x + bossX;
                boss->y.HALF.HI = gRoomControls.origin_y + bossY;
                boss->collisionLayer = 1;
                UpdateSpriteForCollisionLayer(boss);
                return TRUE;
            }
            // CreateEnemy itself failed - fall through to a normal wave
            // rather than leaving the room empty.
        } else if (gSave.run_frames - gSave.final_wave_frame < QUICKSTART_BOSS_OWED_TIMEOUT) {
            return FALSE;
        } else {
            // The table never recovered (fixed sheet pressure) - stop
            // waiting, keep the loop alive with an ordinary wave.
            QsClearRoomFlag(QUICKSTART_BOSS_OWED_FLAG);
        }
    } else
    // This boss rolls in every region's wave loop, not just Castle Garden as
    // an earlier comment here claimed - so it needs no Gust Jar interlock but
    // it would need one if it were still jar-only. It isn't: sub_08027AA4
    // (chuchuBoss.c) now lets a sword, arrow, boomerang, thrown object, Fire
    // Rod blast or Pacci Cane shot peel the jelly, and the bare core already
    // took ordinary damage in vanilla. Suck-and-slam is untouched and still
    // the cleanest way through.
    //
    // The Random() consume stays unconditional so the RNG stream does not
    // depend on WHICH region the player happens to be standing in.
    //
    // The GFX gate is the user's NHF bug (see docs/QUICKSTART_ROADMAP.md,
    // boss camera/freeze entry): the boss family plus its spawn particles
    // cost ~6 sheets, and rolling it into a room that cannot pay left the
    // table below the reserve - which used to hand the boss straight to
    // the reserve trimmer (one piece eaten per pass, measured 5->0 in 320
    // frames, camera_target left dangling on a cleared slot). The trimmer
    // now refuses boss pieces outright, but a short table no longer
    // downgrades the roll to a normal wave - it DEFERS the spawn (the
    // owed branch above), because measurement showed the downgrade fired
    // every single time. 6 measured (2 fit a 12-free cleared room, budget
    // doc finding 4) + the reserve of 4 the spawn must not eat.
    if (wave > 0 && (s32)Random() % 100 < QUICKSTART_REGION_BOSS_WAVE_CHANCE && QuickStartRegionAllowsBoss(region)) {
        if (QuickStartReclaimableGfxSlots() >= QUICKSTART_BOSS_SPAWN_MIN_GFX) {
            // F3: the boss is Green OR Electric (blue), an even coin flip
            // per spawn. Both forms are one chuchuBoss.c state machine
            // selected by the spawn type: type 0 records type2=0 (green
            // palette 0x2b), type 4 records type2=4 (blue palette 0x2c,
            // the electric attack set). The weapon-peel widening
            // (sub_08027AA4) keys on contact flags, not type2, so it
            // covers both forms - and it even passes type2 to the splash
            // particle so the effects match the palette.
            Entity* boss = CreateEnemy(CHUCHU_BOSS, ((s32)Random() & 1) ? 4 : 0);
            if (boss != NULL) {
                s16 bossX = region->rewardX;
                s16 bossY = region->rewardY;
                // Trilby's arena is the enclosed southwest pocket, not the
                // reward spot - centered in its widest open band (tile
                // (5,37)) so the whole family fits inside the pocket's
                // solid ring. The clamp in QuickStartTrilbyQuirkHook keeps
                // it there.
                if (region->area == AREA_HYRULE_FIELD && region->room == ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS) {
                    bossX = 88;
                    bossY = 600;
                }
                boss->x.HALF.HI = gRoomControls.origin_x + bossX;
                boss->y.HALF.HI = gRoomControls.origin_y + bossY;
                boss->collisionLayer = 1;
                UpdateSpriteForCollisionLayer(boss);
                return TRUE;
            }
        } else {
            // Rolled a boss the room can't pay for THIS frame. Latch it and
            // wait (see the owed branch above). final_wave_frame doubles as
            // the wait's deadline anchor - the room is empty right now, so
            // the stuck-wave rescue that also reads it has nothing to do,
            // and the spawn that eventually lands restarts it anyway.
            QsSetRoomFlag(QUICKSTART_BOSS_OWED_FLAG);
            gSave.final_wave_frame = gSave.run_frames;
            return FALSE;
        }
    }
    escalated = QuickStartEscalatedDifficulty(region, wave);
    QuickStartSpawnEnemyGroupAtDifficulty(region->enemyOffsets, region->enemyOffsetCount, region->roomSquares,
                                          region->maxEnemies, (u8)escalated);
    return TRUE;
}

// Replaces the old "spawn exactly one wave, ever" gate: once a wave goes
// fully clear, queues the next one (harder than the last), forever - on
// every visit, regardless of whether this region's one-time reward has
// already been earned. That reward (QuickStartSpawnRegionRewardOnce) still
// only ever comes from wave 0's own clear, via its own once-only reward-
// state gate, completely untouched by this loop continuing past it.
// How long the chain's last region will wait for its Element-gating wave to
// be finished before pulling any survivor to the reward spot - see
// QuickStartRescueStuckFinalWave.
#define QUICKSTART_STUCK_WAVE_FRAMES (90 * 60)

// The win depends on one specific room going completely enemy-free, so a
// single enemy the player cannot get at ends the run then and there. The
// spawn tables cannot rule that out on their own: they were built from a
// collision scan for open 3x3 neighbourhoods, which says a tile is standable
// but nothing about whether it is connected to where the player comes in,
// and even a perfectly connected spawn point is no guarantee once enemies
// start moving - a Crow or a Peahat can drift somewhere with no route back.
// sQuickStartGatedZones handles the cases that have been walked and written
// down; this handles the rest, without needing any of them enumerated.
//
// If the wave that gates the Element has been up for
// QUICKSTART_STUCK_WAVE_FRAMES and is still not clear, every surviving enemy
// is moved to the reward spot, where the player necessarily can reach them.
// The timer then restarts, so an enemy that somehow wanders off again gets
// pulled back rather than stranding the run on the second attempt.
//
// Runs in EVERY region, not just the chain's last.
//
// It was scoped to the last slot on the reasoning that elsewhere a stranded
// enemy only costs a loot drop. That was wrong about how the mode plays: a
// region's wave gates its reward AND its onward exit, so an enemy the player
// cannot reach stalls the whole run, not one item. Lon Lon Ranch is where the
// user hit it - its waves could not be cleared at all, because some spawn
// ground there is not connected to where the player walks in.
//
// The last slot keeps its own separate clock (gSave.final_wave_frame, started
// when the Element-gating wave spawns) because the win depends on that exact
// room going empty; every other region shares the run-scoped one below.
static void QuickStartRescueStuckFinalWave(const QuickStartRegion* region) {
    s32 i;
    if (gSave.run_frames - gSave.final_wave_frame < QUICKSTART_STUCK_WAVE_FRAMES) {
        return;
    }
    gSave.final_wave_frame = gSave.run_frames;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s16 spotX, spotY;
        if (ent->kind != ENEMY || !QuickStartEntityInCurrentRoom(ent)) {
            continue;
        }
        // Spread them, don't stack them. Every survivor used to be dropped on
        // the reward spot itself - the same single tile - so a rescue of five
        // stranded enemies produced five sprites occupying one square, which
        // is unreadable and unfightable. QuickStartFindOpenTileNear spirals
        // out from the reward spot and refuses any tile with another enemy
        // within two, so they land spaced across the open ground around it.
        if (!QuickStartFindOpenTileNear(region->rewardX, region->rewardY, 2, &spotX, &spotY)) {
            spotX = region->rewardX;
            spotY = region->rewardY;
        }
        ent->x.HALF.HI = gRoomControls.origin_x + spotX;
        ent->y.HALF.HI = gRoomControls.origin_y + spotY;
        ent->collisionLayer = 1;
        UpdateSpriteForCollisionLayer(ent);
    }
}

// gSave.final_wave_frame is the stuck-wave clock, and one is enough for all
// the regions: only one is ever loaded, so the last slot's use of it and every
// other region's cannot overlap.
static void QuickStartSpawnRegionEnemiesOnce(const QuickStartRegion* region, s32 slot) {
    u8 wave = QuickStartRegionGetWaveCount(slot);
    if (QsCheckRoomFlag(0)) {
        if (!QuickStartRegionWaveCleared()) {
            // D2: keep the persistent alive-count current while the wave is
            // up. Min-update only - the count never grows mid-wave, so a
            // stray extra entity can't inflate the remainder. Boss waves
            // zero it instead (setpieces re-roll fresh on re-entry rather
            // than resuming), and quest swap windows record nothing.
            if (!QuickStartQuestSwapActive()) {
                bool32 hasBoss;
                s32 live = QuickStartCountRegionEnemies(&hasBoss);
                u8 alive = QuickStartRegionGetAliveCount(slot);
                if (hasBoss) {
                    if (alive != 0) {
                        QuickStartRegionSetAliveCount(slot, 0);
                    }
                } else if (live < alive) {
                    QuickStartRegionSetAliveCount(slot, (u8)live);
                }
            }
            // A wave that will not clear stalls the region's reward AND its
            // onward exit, so pull stranded enemies back to the reward spot
            // wherever it happens - this used to run only in the chain's last
            // region. See QuickStartRescueStuckFinalWave.
            QuickStartRescueStuckFinalWave(region);
            return;
        }
        if (wave < 255) {
            QuickStartRegionSetWaveCount(slot, wave + 1);
        }
        // A genuine clear is one of the two resets: the next spawn is a
        // full fresh wave.
        QuickStartRegionSetAliveCount(slot, 0);
        QsClearRoomFlag(0);
        return;
    }
    {
        // D2: a nonzero remainder means the CURRENT wave was interrupted by
        // a within-region excursion (? room, cave, fusion reload - anything
        // that reloads the room without the player settling in another
        // region, which is what resets it). Resume it: respawn only the
        // remainder, at the same escalated difficulty this wave was dealt
        // at, with no wave-counter movement and no boss roll - clearing the
        // remainder finishes the wave through the branch above exactly as
        // if the player had never left.
        u8 remainder = QuickStartRegionGetAliveCount(slot);
        if (remainder > 0) {
            s32 escalated = QuickStartEscalatedDifficulty(region, wave);
            QuickStartSpawnEnemyGroupAtDifficulty(region->enemyOffsets, region->enemyOffsetCount,
                                                  region->roomSquares, remainder, (u8)escalated);
            // Leave the stored remainder as-is: the watcher above min-updates
            // it to whatever actually spawned on the next settled frame.
            QsSetRoomFlag(0);
            if (slot != QuickStartElementRegionIndex() || !QsCheckRoomFlag(43)) {
                gSave.final_wave_frame = gSave.run_frames;
            }
            return;
        }
    }
    // FALSE means a rolled boss is deferred waiting for gfx (see
    // QuickStartSpawnRegionWave) - the room stays "no wave up" and this
    // runs again next frame until the owed spawn lands or times out.
    if (!QuickStartSpawnRegionWave(region, wave)) {
        return;
    }
    // Fresh full wave: arm the alive-counter at the "count unknown"
    // sentinel; the watcher records the true spawned count next frame.
    QuickStartRegionSetAliveCount(slot, QUICKSTART_ALIVE_UNKNOWN);
    QsSetRoomFlag(0);
    // Start (or restart) the stuck-wave clock for the wave just spawned. Room
    // flag 43 is "an Element has already been dropped this visit"; once it is
    // set the last region has nothing left for the failsafe to protect, but
    // every other region still wants its clock running for the next wave.
    if (slot != QuickStartElementRegionIndex() || !QsCheckRoomFlag(43)) {
        gSave.final_wave_frame = gSave.run_frames;
    }
}

// ======================= The item tier system ==========================
//
// Every drop in the mode comes through here. It replaces three unrelated flat
// pools (a 4-then-8 entry "ladder" pool, a 4-entry rare pool, and a 23-entry
// region pool) that had no tiers at all, so an item's rarity used to be an
// accident of which pool it happened to sit in and how big that pool was.
//
// A draw is two steps: roll a TIER, then pick uniformly among the entries of
// that tier that the run can actually use. Category is a mask so a caller can
// say "anything but key items" (the ? rooms) or "anything at all" (a region
// clear reward).
#define QS_CAT_KEY (1 << 0)
#define QS_CAT_REWARD (1 << 1)
#define QS_CAT_WEAPON (1 << 2)
#define QS_CAT_SKILL (1 << 3)
#define QS_CAT_STAT (1 << 4)
// CHARMS/CURSES: the repurposed pastry/food items (see GF_FOOD_BIT). All
// uncommon, all run-long status effects, half of them traps - which is
// why they get their own category rather than riding QS_CAT_STAT: a
// future caller can ask for "drops but no gambles" by masking it out.
#define QS_CAT_CHARM (1 << 5)
// What a "? room" may pay: everything except key items, per the user's rule
// that those come from the opening selection and the shop.
#define QS_CAT_DROP (QS_CAT_REWARD | QS_CAT_WEAPON | QS_CAT_SKILL | QS_CAT_STAT | QS_CAT_CHARM)
#define QS_CAT_ALL (QS_CAT_DROP | QS_CAT_KEY)

#define QS_TIER_COMMON 0
#define QS_TIER_UNCOMMON 1
#define QS_TIER_RARE 2

// A set of tiers, for callers that pick from a band rather than rolling the
// 60/30/10 curve - today the hub's three selection rounds
// (QuickStartSpawnChoiceRow), which are a deliberate choice between three
// visible items, not a random drop.
#define QS_TIER_BIT(t) (1 << (t))
#define QS_TIER_ANY (QS_TIER_BIT(QS_TIER_COMMON) | QS_TIER_BIT(QS_TIER_UNCOMMON) | QS_TIER_BIT(QS_TIER_RARE))
#define QS_TIER_NOT_RARE (QS_TIER_BIT(QS_TIER_COMMON) | QS_TIER_BIT(QS_TIER_UNCOMMON))

// What a content site's kill/pickup pays, when the row wants to override
// its kind's usual payout (QuickStartContentSite.rewardTier, defined with
// the site table much further down - these live up here beside the tiers
// they name because the miniboss reward drop is compiled above that table).
// DEFAULT keeps the old behaviour exactly - a miniboss pays a heart piece,
// or a heart container if the site is elite - so every row that omits the
// field is unchanged. The others are QS_TIER_* + 1.
#define QS_SITE_REWARD_DEFAULT 0
#define QS_SITE_REWARD_COMMON 1
#define QS_SITE_REWARD_UNCOMMON 2
#define QS_SITE_REWARD_RARE 3

// 60 / 30 / 10, expressed as buckets out of ten. This is the one place the
// mode's rarity curve is written down.
#define QS_TIER_BUCKETS 10
#define QS_TIER_COMMON_BUCKETS 6
#define QS_TIER_UNCOMMON_BUCKETS 3 // rare is the remaining bucket

// How wide a seed an event stores to describe its prize. Six bits, because a
// content site's `extra` is eight and the top two carry flags (bit 7 = this
// site always pays rare, bit 6 = this wave gauntlet is the stripped-kit
// variant). Sixty-four values is far more than the tier table needs and
// costs nothing.
#define QUICKSTART_DRAW_SEED_RANGE 64

// Why an item might not be drawable yet. Checked at DRAW time, not at roll
// time, so a prize decided on the first visit still resolves correctly when
// the player comes back holding different things.
enum {
    QS_REQ_NONE,
    QS_REQ_BOW,          // a quiver or an arrow butterfly is nothing without it
    QS_REQ_BOMBS,        // ditto the bomb bag and remote bombs
    QS_REQ_BOOMERANG,    // the magical one is an upgrade, not a replacement
    QS_REQ_MOLE_MITTS,   // the dig butterfly only speeds up digging
    QS_REQ_FLIPPERS,     // the swim butterfly only speeds up swimming
    QS_REQ_SPIN_ATTACK,  // Great Spin is an upgrade to it
    QS_REQ_ROCS_CAPE,    // Down Thrust needs something to come down from
    QS_REQ_EMPTY_BOTTLE, // potions, fairies and charms all FILL a bottle
    QS_REQ_BOTTLE_ROOM,  // a new empty bottle needs a free bottle slot
    QS_REQ_NO_PACCI,     // the Fire Rod shares the Cane's inventory cell
    QS_REQ_NO_FIRE_ROD,  // ...and vice versa
};

typedef struct {
    u16 item;
    u8 cat;
    u8 tier;
    u8 req;
    u8 repeatable; // may drop again when already owned (rupees, hearts, fills)
} QuickStartTierEntry;

// The tier table. Ordering is irrelevant - unlike the flat pools it replaces,
// nothing indexes this positionally, so rows can be added or moved freely.
//
// Ordering is irrelevant to CORRECTNESS but not to reach: see
// QuickStartDrawPick for why a tier's later entries used to be unreachable
// and how the pick now spreads over the whole list.
//
// Deliberately absent:
//   ITEM_LIGHT_ARROW  - unverified; it can join the direct-grant list
//                       (QuickStartItemNeedsDirectGrant) and come straight
//                       in whenever someone wants it.
//   two loose fairies - that is the FAIRY room kind, not an item.
//
// ITEM_RED_SWORD used to be listed here as impossible, on a claim that has
// since been disproved (see QuickStartItemNeedsDirectGrant). It is now an
// ordinary uncommon row, delivered by grant rather than by drop.
static const QuickStartTierEntry sQuickStartTiers[] = {
    // --- REWARDS ---------------------------------------------------------
    { ITEM_RUPEE50, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_NONE, 1 },
    { ITEM_HEART_PIECE, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_NONE, 1 },
    { ITEM_BOTTLE_BLUE_POTION, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_EMPTY_BOTTLE, 1 },
    { ITEM_BOTTLE1, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_BOTTLE_ROOM, 1 },
    { ITEM_RUPEE100, QS_CAT_REWARD, QS_TIER_UNCOMMON, QS_REQ_NONE, 1 },
    { ITEM_BOTTLE_RED_POTION, QS_CAT_REWARD, QS_TIER_UNCOMMON, QS_REQ_EMPTY_BOTTLE, 1 },
    { ITEM_RUPEE200, QS_CAT_REWARD, QS_TIER_RARE, QS_REQ_NONE, 1 },
    { ITEM_HEART_CONTAINER, QS_CAT_REWARD, QS_TIER_RARE, QS_REQ_NONE, 1 },
    { ITEM_BOTTLE_FAIRY, QS_CAT_REWARD, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    // --- WEAPONS / TOOLS -------------------------------------------------
    { ITEM_BOW, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_BOMBS, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_BOOMERANG, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    // Bag and quiver stack to type 3, so they stay drawable once owned.
    { ITEM_BOMBBAG, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOMBS, 1 },
    { ITEM_LARGE_QUIVER, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOW, 1 },
    { ITEM_REMOTE_BOMBS, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOMBS, 0 },
    { ITEM_BOTTLE1, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOTTLE_ROOM, 1 },
    { ITEM_GUST_JAR, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_FIRE_ROD, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_NO_PACCI, 0 },
    // The level-2 sword, per the user. It has no ground-item form, so it
    // reaches the player through QuickStartSpawnRewardEntity's direct-grant
    // path rather than as something lying on the floor - which is exactly
    // what lets it sit in the draw at all, having been excluded until now.
    // It remains a miniboss payout too; not repeatable, so a run cannot
    // stack two.
    { ITEM_RED_SWORD, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_MAGIC_BOOMERANG, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_BOOMERANG, 0 },
    { ITEM_MIRROR_SHIELD, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_NONE, 0 },
    // --- SKILL UPGRADES --------------------------------------------------
    { ITEM_SKILL_SPIN_ATTACK, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_ROCK_BREAKER, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_ROLL_ATTACK, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_DASH_ATTACK, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_PERIL_BEAM, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_SWORD_BEAM, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_DOWN_THRUST, QS_CAT_SKILL, QS_TIER_RARE, QS_REQ_ROCS_CAPE, 0 },
    { ITEM_SKILL_GREAT_SPIN, QS_CAT_SKILL, QS_TIER_RARE, QS_REQ_SPIN_ATTACK, 0 },
    // --- STAT UPGRADES ---------------------------------------------------
    // No common tier, per the design. The butterflies each speed up exactly
    // one thing (arrows/digging/swimming) and are read straight off the
    // inventory bit by itemBow.c, itemMoleMitts.c and playerUtils.c, so they
    // need no new code - only the item they upgrade.
    { ITEM_ARROW_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_BOW, 0 },
    { ITEM_DIG_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_MOLE_MITTS, 0 },
    { ITEM_SWIM_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_FLIPPERS, 0 },
    // Charms arrive bottled and become permanent when drunk
    // (QuickStartNoteCharm -> QUICKSTART_CHARM_BIT -> CalculateDamage). That
    // framework has been live and unreachable since it was built: nothing
    // granted a charm, and almost nothing granted a bottle to put one in.
    { BOTTLE_CHARM_NAYRU, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    { BOTTLE_CHARM_FARORE, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    { BOTTLE_CHARM_DIN, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    // --- CHARMS / CURSES -------------------------------------------------
    // The repurposed food items (F4): eating one applies a run-long status
    // effect the moment GiveItem runs (QuickStartNoteFoodItem), announced
    // by an Ezlo line. Three bless, three bite, and nothing but the names
    // hints which is which. All uncommon per the user's spec; not
    // repeatable, so each can headline at most one ? event per run.
    { ITEM_BRIOCHE, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },      // charm: sword knockback up
    { ITEM_CROISSANT, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },    // charm: walk speed up
    { ITEM_CAKE, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },         // charm: knockback immunity
    { ITEM_PIE, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },          // curse: Link knocked further
    { ITEM_QST_DOGFOOD, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },  // curse: enemies faster
    { ITEM_QST_MUSHROOM, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 }, // curse: foes fire faster
    // Batch two - all charms, on the rest of the unused quest items.
    { ITEM_QST_BOOK1, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },        // charm: fire immunity
    { ITEM_QST_BOOK2, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },        // charm: ice immunity
    { ITEM_QST_BOOK3, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },        // charm: shock immunity
    { ITEM_QST_TINGLE_TROPHY, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },// charm: rupee drops up
    { ITEM_JABBERNUT, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },        // charm: kinstone drops up
    { ITEM_QST_CARLOV_MEDAL, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 }, // charm: heart drops up
    { ITEM_QST_BROKEN_SWORD, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 }, // charm: cheap shop
    // The last item from the original F4 wish list. Uncommon like its
    // siblings, so a run that finds it early gets a noticeably richer rest
    // of the run - which is the point of a luck charm.
    { ITEM_SHELLS, QS_CAT_CHARM, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 }, // charm: rarer rewards
    // F10: the two findable tools. The MAP activates the START-screen map
    // (the pause menu already gates that screen on GetInventoryValue(ITEM_MAP)
    // - see pauseMenu.c PauseMenu_Variant2); the COMPASS turns on the map's
    // unfused-fusion markers and names the Element's region (see
    // pauseMenuScreen6.c's QUICKSTART block + QuickStartNoteFoodItem).
    { ITEM_MAP, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_NONE, 0 },
    { ITEM_COMPASS, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_NONE, 0 },
    // --- KEY ITEMS -------------------------------------------------------
    // Never drawn by a ? room (QS_CAT_DROP excludes them); reachable from the
    // opening selection and from a region clear reward.
    { ITEM_PEGASUS_BOOTS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_ROCS_CAPE, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_MOLE_MITTS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_FLIPPERS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_LANTERN_OFF, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_OCARINA, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_PACCI_CANE, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NO_FIRE_ROD, 0 },
    { ITEM_GRIP_RING, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NONE, 0 },
    { ITEM_POWER_BRACELETS, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NONE, 0 },
};
#define QUICKSTART_TIER_COUNT (s32)(sizeof(sQuickStartTiers) / sizeof(QuickStartTierEntry))

// Is there a bottle standing empty? Charms, potions and bottled fairies all
// go through GiveItem case 4, which looks for a bottle whose contents are
// 0x20 (empty) and silently does NOTHING if it finds none - so without this
// check a rare charm drop would be a pickup that vanishes and gives nothing.
static bool32 QuickStartHasEmptyBottle(void) {
    s32 i;
    for (i = 0; i < 4; i++) {
        if (gSave.stats.bottles[i] == 0x20) {
            return TRUE;
        }
    }
    return FALSE;
}

// Room for one more bottle? GiveItem case 3 walks ITEM_BOTTLE1..4 for the
// first one not yet owned, and returns without doing anything if all four
// are taken.
static bool32 QuickStartHasBottleRoom(void) {
    s32 i;
    for (i = 0; i < 4; i++) {
        if (GetInventoryValue(ITEM_BOTTLE1 + i) == 0) {
            return TRUE;
        }
    }
    return FALSE;
}

// Items that arrive by GiveItem rather than as something lying on the
// floor.
//
// A correction to the record, because this file asserted the opposite for
// a long time: the tier table used to exclude ITEM_RED_SWORD on the
// grounds that CreateObject(GROUND_ITEM, ITEM_RED_SWORD) "never creates an
// entity at all". A clean-room probe (empty the room of ground items,
// verify zero, spawn one, count again, with a heart piece run identically
// as control) shows it DOES create one, and a screenshot shows the sword
// sprite on the floor. So the impossibility claim was wrong.
//
// The swords stay on the direct-grant path anyway, for two better reasons
// than impossibility. It is what this file ALREADY does for the Red Sword
// on the miniboss payout (GiveItem + a message), so both routes now feel
// the same; and GiveItem is the unambiguous way to make an equipment
// UPGRADE actually apply, which a floor pickup only does by going through
// the same call in the end.
//
// The helper exists regardless of which items are on this list: it
// replaced ten copies of the same eight-line drop block, so a reward
// spawner is now one call that cannot forget ENT_PERSIST or the
// direction fixup.
static bool32 QuickStartItemNeedsDirectGrant(u16 item) {
    switch (item) {
        case ITEM_GREEN_SWORD:
        case ITEM_RED_SWORD:
        case ITEM_BLUE_SWORD:
        case ITEM_FOURSWORD:
            return TRUE;
        default:
            return FALSE;
    }
}

// Put `item` in front of the player at a room-local spot: normally as a
// ground item, but through GiveItem for the equipment that has no floor
// form. Returns the entity when there is one, and NULL when the item was
// granted outright - so a caller that only wants "did this pay out" should
// test the bool32 sibling below instead.
static Entity* QuickStartSpawnRewardEntity(u16 item, s16 localX, s16 localY) {
    Entity* itemEntity;
    if (QuickStartItemNeedsDirectGrant(item)) {
        if (GetInventoryValue(item) == 0) {
            GiveItem(item, 0);
            MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 13));
            MsgInit();
        }
        return NULL;
    }
    itemEntity = CreateObject(GROUND_ITEM, item, 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + localX;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + localY;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
        // Set after UpdateSpriteForCollisionLayer, which otherwise
        // overwrites it.
        itemEntity->direction = IdleSouth;
    }
    return itemEntity;
}

// "Did this reward actually reach the player?" - TRUE for a ground item
// that exists AND for a direct grant that has already happened.
static bool32 QuickStartRewardDelivered(u16 item, s16 localX, s16 localY) {
    if (QuickStartItemNeedsDirectGrant(item)) {
        QuickStartSpawnRewardEntity(item, localX, localY);
        return TRUE;
    }
    return QuickStartSpawnRewardEntity(item, localX, localY) != NULL;
}

static bool32 QuickStartTierEntryUsable(const QuickStartTierEntry* e) {
    if (!e->repeatable && GetInventoryValue(e->item) != 0) {
        return FALSE;
    }
    switch (e->req) {
        case QS_REQ_BOW:
            return GetInventoryValue(ITEM_BOW) != 0;
        case QS_REQ_BOMBS:
            return GetInventoryValue(ITEM_BOMBS) != 0;
        case QS_REQ_BOOMERANG:
            return GetInventoryValue(ITEM_BOOMERANG) != 0;
        case QS_REQ_MOLE_MITTS:
            return GetInventoryValue(ITEM_MOLE_MITTS) != 0;
        case QS_REQ_FLIPPERS:
            return GetInventoryValue(ITEM_FLIPPERS) != 0;
        case QS_REQ_SPIN_ATTACK:
            return GetInventoryValue(ITEM_SKILL_SPIN_ATTACK) != 0;
        case QS_REQ_ROCS_CAPE:
            return GetInventoryValue(ITEM_ROCS_CAPE) != 0;
        case QS_REQ_EMPTY_BOTTLE:
            return QuickStartHasEmptyBottle();
        case QS_REQ_BOTTLE_ROOM:
            return QuickStartHasBottleRoom();
        // itemMetaData.c gives ITEM_FIRE_ROD and ITEM_PACCI_CANE the same
        // MENU_SLOT_CANE, because the 4x3 item grid has no free cell. Rather
        // than fight the menu art, the two are made mutually exclusive in the
        // draw: whichever the run finds first locks the other out.
        case QS_REQ_NO_PACCI:
            return GetInventoryValue(ITEM_PACCI_CANE) == 0;
        case QS_REQ_NO_FIRE_ROD:
            return GetInventoryValue(ITEM_FIRE_ROD) == 0;
        default:
            return TRUE;
    }
}

// Pick the `pick`-th usable entry of (catMask, tier), or ITEM_NONE if the run
// has exhausted that tier. No modulo: `pick` is reduced by subtraction
// because the count is a runtime value, and agbcc emits __umodsi3 (which its
// runtime lib does not provide) for a division by anything but a constant.
static u16 QuickStartTierPick(u8 catMask, u8 tier, s32 pick) {
    s32 i, count = 0;
    for (i = 0; i < QUICKSTART_TIER_COUNT; i++) {
        const QuickStartTierEntry* e = &sQuickStartTiers[i];
        if ((e->cat & catMask) && e->tier == tier && QuickStartTierEntryUsable(e)) {
            count++;
        }
    }
    if (count == 0) {
        return ITEM_NONE;
    }
    if (pick < 0) {
        pick = -pick;
    }
    while (pick >= count) {
        pick -= count;
    }
    for (i = 0; i < QUICKSTART_TIER_COUNT; i++) {
        const QuickStartTierEntry* e = &sQuickStartTiers[i];
        if ((e->cat & catMask) && e->tier == tier && QuickStartTierEntryUsable(e)) {
            if (pick == 0) {
                return e->item;
            }
            pick--;
        }
    }
    return ITEM_NONE;
}

// Draw at a FORCED tier, stepping down if that tier is exhausted and finally
// falling back to a heart piece - which is always usable, so a draw can never
// come back empty and leave a "? room" with nothing in it.
// Spread a 6-bit draw seed across a tier's WHOLE usable list.
//
// The raw `seed / QS_TIER_BUCKETS` this replaces could only ever produce
// 0..6, and QuickStartTierPick reduces a pick by subtraction, so every
// entry past the seventh usable one in a tier was unreachable for every
// seed - the reason the thirteen charms had never once been seen. Within a
// tier band the low digit barely varies while the quotient does, so
// scaling the digit up and adding the quotient turns a band's 18 seeds
// into 18 distinct picks. Still a pure function of the seed, which is what
// keeps a prize stable across leaving and re-entering a room.
static s32 QuickStartDrawPick(s32 seed) {
    if (seed < 0) {
        seed = -seed;
    }
    return (seed % QS_TIER_BUCKETS) * 7 + seed / QS_TIER_BUCKETS;
}

static u16 QuickStartDrawAtTier(s32 pick, u8 catMask, s32 tier) {
    s32 t;
    for (t = tier; t >= 0; t--) {
        u16 item = QuickStartTierPick(catMask, (u8)t, pick);
        if (item != ITEM_NONE) {
            return item;
        }
    }
    for (t = tier + 1; t <= QS_TIER_RARE; t++) {
        u16 item = QuickStartTierPick(catMask, (u8)t, pick);
        if (item != ITEM_NONE) {
            return item;
        }
    }
    return ITEM_HEART_PIECE;
}

// The ordinary draw: roll a tier 60/30/10, then pick within it.
//
// `seed` is whatever the caller had stored for this event (a content site's
// `extra`, a lottery's prize field). Deriving both the tier and the pick from
// it - rather than calling Random() at drop time - is what makes a prize
// stable across leaving the room and coming back, which every "? room" here
// depends on.
static u16 QuickStartDrawItem(s32 seed, u8 catMask) {
    s32 roll = seed;
    s32 tier;
    if (roll < 0) {
        roll = -roll;
    }
    // TEN buckets, not a percentage out of 100. The seed is only six bits
    // (QUICKSTART_DRAW_SEED_RANGE), so "roll % 100 < 60" would have made rare
    // literally unreachable and uncommon a 4-in-64 accident - a seed of 0-63
    // never lands in the 90-99 band at all. Ten buckets divide exactly into
    // the 60/30/10 curve and work at any seed width.
    roll = roll % QS_TIER_BUCKETS;
    if (QuickStartFoodMask() & QUICKSTART_FOOD_RARE_LUCK) {
        // The luck charm (F4's last idea): the same ten buckets, re-cut
        // 40/40/20 instead of 60/30/10. Rare doubles and the common band
        // gives up the difference, which is a real change in what a run
        // FEELS like without touching any table or any other draw.
        if (roll < 4) {
            tier = QS_TIER_COMMON;
        } else if (roll < 8) {
            tier = QS_TIER_UNCOMMON;
        } else {
            tier = QS_TIER_RARE;
        }
    } else if (roll < QS_TIER_COMMON_BUCKETS) {
        tier = QS_TIER_COMMON;
    } else if (roll < QS_TIER_COMMON_BUCKETS + QS_TIER_UNCOMMON_BUCKETS) {
        tier = QS_TIER_UNCOMMON;
    } else {
        tier = QS_TIER_RARE;
    }
    // The pick used to be plain `seed / QS_TIER_BUCKETS`, and that was a
    // real bug, not a rounding detail: the seed is six bits, so seed/10
    // only ever produces 0..6. QuickStartTierPick reduces the pick by
    // subtraction while it is >= the usable count, so with more than about
    // seven usable entries in a tier, everything after the seventh was
    // UNREACHABLE - permanently, for every seed, in every room.
    //
    // The user reported never once receiving a pastry/status item. That is
    // exactly this: the thirteen charms sit at the end of the uncommon
    // list, so simulated over the real table they were reachable 0 times
    // out of 13 both early (19 usable uncommon entries, 6 reachable) and
    // mid-run (25 usable, still 6 reachable). Both the F10 tools and the
    // late skill upgrades were losing the same way in the rare tier.
    //
    // The fix keeps the pick a pure function of the seed - prize stability
    // across leaving and re-entering a room depends on that - but spreads
    // it over the whole list instead of clustering at the front. Within a
    // tier band the low digit is nearly constant while seed/10 varies, so
    // multiplying the digit up and adding the quotient turns the 18 seeds
    // of a band into 18 DISTINCT picks (measured: full coverage of every
    // tier at every plausible count, and 11 of the 13 charm slots).
    return QuickStartDrawAtTier(QuickStartDrawPick(seed), catMask, tier);
}

// Draws this region's clear reward and drops it at the reward spot, marking
// this chain slot "earned" (1) and room flag 1 "now watching this visit's
// drop" - shared by both the initial grant and the re-drop path in
// QuickStartSpawnRegionRewardOnce below.
static void QuickStartSpawnRegionRewardItem(const QuickStartRegion* region, s32 slot) {
    u16 chosenItem;
    // The region reward is the one draw that includes KEY items, because it
    // is where the Cane of Pacci, the Ocarina and the two key items the
    // opening selection did not offer have always come from. Rolled fresh
    // (not seeded) - unlike a "? room" prize this is placed once and never
    // re-derived, so it has nothing to stay consistent with.
    //
    chosenItem = QuickStartDrawItem((s32)Random() & 0x3f, QS_CAT_ALL);
    // "Delivered", not "an entity exists". A direct-grant item (the
    // level-2 sword) is handed straight over, and without this the region
    // would draw one, place nothing, and never mark its reward earned -
    // the clear would silently pay out nothing at all.
    if (QuickStartRewardDelivered(chosenItem, region->rewardX, region->rewardY)) {
        QuickStartSetRegionRewardState(slot, 1);
        QsSetRoomFlag(1);
    }
}

// Generalizes QuickStartSpawnGardenRewardOnce - same 3-state
// earned/dropped/confirmed shape (now chain-slot-indexed instead of an
// Item enum marker), except the chain's LAST slot drops an Earth Element
// and feeds the win condition instead of a normal loot item (see
// QuickStartSpawnWinKeyOnce/QuickStartCheckWinCondition above - both
// already region-agnostic, so nothing about them needed to change).
static void QuickStartSpawnRegionRewardOnce(const QuickStartRegion* region, s32 slot) {
    u8 state;
    if (slot == QuickStartElementRegionIndex()) {
        // The wave-cleared test only gates the FIRST drop. Everything after
        // it has to keep running every frame, cleared room or not.
        //
        // This used to early-return on !QuickStartRegionWaveCleared() for
        // all three steps, which quietly broke the whole win the moment the
        // endless-wave loop landed: on the frame the first wave goes clear
        // the Element drops here, and then QuickStartSpawnRegionEnemiesOnce
        // - called immediately after this in QuickStartRegionMonitor -
        // clears room flag 0 and spawns the next wave. From the very next
        // frame QuickStartRegionWaveCleared() reads false again, so this
        // function returned before ever reaching QuickStartCheckWinCondition
        // again. Two things then went wrong at once: the Element's despawn
        // timer stopped being refreshed (QuickStartSpawnWinKeyOnce is what
        // refreshes it), so it evaporated ~10 seconds after the wave clear
        // and room flag 43 stopped it ever coming back; and even if the
        // player did grab it in time, the win sequence could not start
        // until they also fully cleared the NEXT, harder wave. Room flag
        // 403 ("an Element was created this round") is the right gate for
        // the two follow-up steps, since it is set exactly when the drop
        // happens and cleared on a genuinely new room load.
        if (QuickStartRegionWaveCleared() || QsCheckRoomFlag(43)) {
            QuickStartSpawnWinKeyOnce(region->rewardX, region->rewardY);
        } else {
            QuickStartRescueStuckFinalWave(region);
        }
        QuickStartCheckWinCondition();
        return;
    }
    state = QuickStartGetRegionRewardState(slot);
    if (state >= 2) {
        return;
    }
    if (state == 0) {
        if (!QuickStartRegionWaveCleared()) {
            return;
        }
        // Room flag 4: "region-cleared hint already shown this visit" -
        // same one-shot-per-visit shape as the WAVES room hint elsewhere in
        // this file; enough on its own since by the time this slot's
        // reward state leaves 0, this branch never runs again regardless.
        if (!QsCheckRoomFlag(4)) {
            QsSetRoomFlag(4);
            CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 11), 0);
        }
        QuickStartSpawnRegionRewardItem(region, slot);
        return;
    }
    if (QuickStartGroundItemAt(region->rewardX, region->rewardY)) {
        QsSetRoomFlag(1);
        return;
    }
    if (QsCheckRoomFlag(1)) {
        QuickStartSetRegionRewardState(slot, 2);
        return;
    }
    QuickStartSpawnRegionRewardItem(region, slot);
}

// Dispatch for whichever region the current room resolves to in this
// save's chain - called every frame from QuickStartRoomMonitor once
// QuickStartGetCurrentRegionChainPosition confirms the current room is
// part of it. Reward before enemies, matching this file's own established
// convention elsewhere (Melari's Mine/Castle Garden already call their
// reward spawner before their enemy spawner, so a full room doesn't cost
// the reward its entity slot).
// --- Overworld side-quests: the hidden-item quest -------------------------
//
// The first of the quest kinds, and deliberately the cheapest one, chosen
// to prove the framework rather than to show off (see
// docs/QUICKSTART_QUEST_RESEARCH.md): scattered pots across one region,
// exactly one of which hides a real reward. Search them to find it.
//
// It costs essentially nothing in the currency that actually binds. Pots
// share a single sprite sheet - measured repeatedly, 40+ of them render
// fine anywhere - and the reward is a GROUND_ITEM whose sheet is resident
// in every region already, so the quest adds ~0 to the GFX table that
// South and North Hyrule Field were saturating. That is the whole reason
// this one goes first.
//
// State lives in FLAG_BANK_11, which has 160 free bits (we use 32 for the
// region wave counters). QUICKSTART's own flag window is down to 42 free
// offsets, so quests are deliberately housed away from it.
#define GF_QUEST_ROLLED 32
// (33-34 free - the old 2-bit quest chain-slot field; the quest's host
// region is the 4-bit QS-window GF_REGION_QUEST_HOST_BIT field now.)
#define GF_QUEST_HIDE_BIT(b) (35 + (b)) // b = 0..3, which pot holds the prize
#define GF_QUEST_DONE 39

// Which charms this run owns. FLAG_BANK_11 again (bits 40-42), for the same
// reason the quest state is here: QUICKSTART's own flag window is nearly
// full and this bank has 150+ bits untouched.
//
// Vanilla stores exactly one charm, in gSave.stats.charm, because a charm is
// a 60-second drink - a second one replacing the first is the intended
// behaviour there. Ours are rare permanent pickups, and a rare pickup that
// deletes the last rare pickup is a bad trade, so ownership is tracked
// separately and CalculateDamage applies every charm held. The vanilla byte
// is still set, purely so GetPlayerPalette keeps tinting Link.
#define QUICKSTART_CHARM_BIT(n) (40 + (n)) // n = 0..2: Nayru, Farore, Din

#define QUICKSTART_QUEST_POTS 8
#define QUICKSTART_QUEST_REWARD ITEM_HEART_PIECE

static bool32 QuickStartQuestFlag(s32 bit) {
    return CheckLocalFlagByBank(FLAG_BANK_11, bit) != 0;
}

static void QuickStartQuestSetFlag(s32 bit) {
    SetLocalFlagByBank(FLAG_BANK_11, bit);
}

// One draw per run, rolled unconditionally from the room monitor like every
// other per-run draw (the hub is bypassed, so nothing may depend on a
// particular room being entered).
static void QuickStartRandomizeQuestOnce(void) {
    s32 slot, hide, b;
    if (QuickStartQuestFlag(GF_QUEST_ROLLED)) {
        return;
    }
    // A POOL index now, not a chain slot - the quest can land in any of the
    // pool's regions. Stored in the QS window's 4-bit GF_REGION_QUEST_HOST_BIT
    // field rather than the old 2-bit bank-11 slot field, which cannot
    // count past 3.
    slot = (s32)Random() % QUICKSTART_REGION_POOL_SIZE;
    hide = (s32)Random() % QUICKSTART_QUEST_POTS;
    for (b = 0; b < 4; b++) {
        if (slot & (1 << b)) {
            QsSetFlag(GF_REGION_QUEST_HOST_BIT(b));
        }
    }
    for (b = 0; b < 4; b++) {
        if (hide & (1 << b)) {
            QuickStartQuestSetFlag(GF_QUEST_HIDE_BIT(b));
        }
    }
    QuickStartQuestSetFlag(GF_QUEST_ROLLED);
}

static s32 QuickStartQuestSlot(void) {
    s32 b, value = 0;
    for (b = 0; b < 4; b++) {
        if (QsCheckFlag(GF_REGION_QUEST_HOST_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static s32 QuickStartQuestHiddenIndex(void) {
    s32 b, value = 0;
    for (b = 0; b < 4; b++) {
        if (QuickStartQuestFlag(GF_QUEST_HIDE_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

// Pots go on the region's OWN enemy-offset table rather than anywhere
// derived: every entry in it is a pre-verified walkable spot in that room,
// which is exactly the property a searchable pot needs, and it is already
// filtered for item-gated zones by QuickStartPositionAllowed. Spread by
// striding through the table so the search covers the region instead of
// clustering in one corner.
static void QuickStartSpawnQuestPots(const QuickStartRegion* region) {
    s32 i, placed = 0, stride, hidden;
    if (region->enemyOffsetCount <= 0) {
        return;
    }
    hidden = QuickStartQuestHiddenIndex() % QUICKSTART_QUEST_POTS;
    stride = region->enemyOffsetCount / QUICKSTART_QUEST_POTS;
    if (stride < 1) {
        stride = 1;
    }
    for (i = 0; i < region->enemyOffsetCount && placed < QUICKSTART_QUEST_POTS; i += stride) {
        s16 x = region->enemyOffsets[i][0];
        s16 y = region->enemyOffsets[i][1];
        Entity* pot;
        if (!QuickStartPositionAllowed(x, y)) {
            continue;
        }
        // Honour the same reserve every other spawner does, even though pots
        // are cheap - the point of the reserve is that nothing gets to be
        // the exception.
        if (!QuickStartGfxBudgetForSpawn()) {
            return;
        }
        // Form 0xFF is an ordinary empty pot; the hidden one carries the
        // reward, which is exactly how the pot lottery already hides its
        // prize (QuickStartPotRoomFill).
        pot = CreateObject(POT, (placed == hidden) ? QUICKSTART_QUEST_REWARD : (u32)0xFF, 0);
        if (pot != NULL) {
            pot->x.HALF.HI = gRoomControls.origin_x + x;
            pot->y.HALF.HI = gRoomControls.origin_y + y;
            pot->collisionLayer = 1;
            pot->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(pot);
        }
        placed++;
    }
}

// Room flag 53: pots laid out this visit. Room flag 54: the prize has been
// seen on the floor, so its disappearance means "picked up" rather than
// "never spawned" - the same distinction QuickStartGroundItemAt exists for
// everywhere else in this file.
static void QuickStartSetupRegionQuest(const QuickStartRegion* region, s32 slot) {
    if (QuickStartQuestFlag(GF_QUEST_DONE) || slot != QuickStartQuestSlot()) {
        return;
    }
    // The give line (custom string 26), once per run, the first time the
    // player stands in the host region while the quest is live - before
    // this the pots just appeared unannounced and the completion line was
    // the quest's first words (the F1b dialogue pass).
    if (!QsCheckFlag(GF_REGION_QUEST_HINT)) {
        QsSetFlag(GF_REGION_QUEST_HINT);
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 26), 0);
    }
    if (!QsCheckRoomFlag(53)) {
        QsSetRoomFlag(53);
        QuickStartSpawnQuestPots(region);
        return;
    }
    if (QuickStartGroundItemOfForm(QUICKSTART_QUEST_REWARD)) {
        QsSetRoomFlag(54);
    } else if (QsCheckRoomFlag(54)) {
        QuickStartQuestSetFlag(GF_QUEST_DONE);
        MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 14));
        MsgInit();
    }
}

// Defined further down, next to the wave/gauntlet code they share their
// enemy placer and flag bank with.
static void QuickStartHuntMonitor(const QuickStartRegion* region, s32 slot);
static void QuickStartScavMonitor(const QuickStartRegion* region, s32 slot);
static void QuickStartHandicapMonitor(void);

static void QuickStartRegionMonitor(s32 poolIndex) {
    const QuickStartRegion* region = &sQuickStartRegionPool[poolIndex];
    // Settled-room guard (QuickStartRoomSettled). Running in a transition's
    // torn window is exactly the user's "prize drops the moment I enter,
    // then the wave spawns" report, reproduced walking the Trilby -> Lon
    // Lon town bridge: the previous region's "wave spawned" flag + zero
    // enemies counted in the new room reads as a wave clear, so the reward
    // and its Ezlo line fire on arrival (at OLD-origin coordinates, so the
    // item also lands off the reward spot and the state machine re-drops a
    // second one), and the spurious wave-counter increment makes the first
    // wave dealt here wave 1+, which is what let the boss roll fire right
    // behind the phantom prize.
    if (!QuickStartRoomSettled()) {
        return;
    }
    if (region->quirkHook != NULL) {
        region->quirkHook();
    }
    // The intro hint fires once per run in whichever region the player
    // reaches first (the once-latch does the scoping); the "the Earth
    // Element is here!" hint fires the moment they set foot in the drawn
    // element region, wherever in the ring that is.
    QuickStartShowRegionIntroHintOnce();
    if (poolIndex == QuickStartElementRegionIndex()) {
        QuickStartShowRegionFinalHintOnce();
    }
    QuickStartSetupRegionQuest(region, poolIndex);
    QuickStartHuntMonitor(region, poolIndex);
    QuickStartScavMonitor(region, poolIndex);
    QuickStartSpawnRegionRewardOnce(region, poolIndex);
    QuickStartSpawnRegionEnemiesOnce(region, poolIndex);
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
        QsSetRoomFlag(2);
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
        if (!QsCheckRoomFlag(1)) {
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
        QsSetRoomFlag(2);
        return;
    }
    if (QsCheckRoomFlag(2)) {
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
//
// Two slots changed hands once the starting loadout became "sword and shield
// only": ITEM_SHIELD and ITEM_WALLET are both boot grants now, so both were
// dead stock - money spent on something already owned. They are the Bow and
// Bombs instead, which is where the shelf next to them was pointing all
// along: the shop already sold arrows, bombs-by-the-ten, a bomb bag and a
// large quiver, and not one of those four does anything for a run that never
// found the weapon.
// --- What the shop stocks -------------------------------------------------
//
// It used to be a hardcoded nine-item list, identical every run - only the
// PRICES were rolled. The user noticed ("it seems like they are the same items
// every time right now") and asked for the stock to be drawn from the item
// categories instead. This is that pool.
//
// It is a separate table from sQuickStartTiers because the two answer
// different questions. The tier table says what a run may FIND; this says
// what the merchant may SELL, and selling has requirements finding does not:
// an item needs a confirm-purchase message id in gItemMetaData or the sale
// script has nothing to say and the purchase cannot complete. Every row below
// has been given one (src/itemMetaData.c, TEXT_STOCKWELL 0x02 as the generic
// borrow).
//
// It also lets the shop leave out things the tier table is right to include.
// Rupees are the clear case: paying rupees for rupees is not a choice, and at
// a low price roll a 200-rupee bundle is just free money. The heart piece is
// left out too - it has its own permanent slot below, on its own escalating
// price - and so is the Ocarina of Wind, which the boot grant already hands
// out. Everything else in QS_CAT_KEY / WEAPON / REWARD / SKILL / STAT is
// here, at every tier, per the user: "the items should be randomly chosen at
// the start of each run and can come from any of the rarity tiers".
//
// Reusing QuickStartTierEntry rather than inventing a struct: the fields line
// up exactly, and it means QuickStartTierEntryUsable - which already knows
// about ammo without its weapon, potions without a bottle, and the Fire Rod /
// Pacci Cane inventory-cell clash - is the shop's eligibility test for free.
// `tier` is unused here; the slot table below decides the shape of the stock.
static const QuickStartTierEntry sQuickStartShopPool[] = {
    // --- KEY ITEMS (8) ---------------------------------------------------
    { ITEM_PEGASUS_BOOTS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_ROCS_CAPE, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_MOLE_MITTS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_FLIPPERS, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_LANTERN_OFF, QS_CAT_KEY, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_PACCI_CANE, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NO_FIRE_ROD, 0 },
    { ITEM_GRIP_RING, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NONE, 0 },
    { ITEM_POWER_BRACELETS, QS_CAT_KEY, QS_TIER_RARE, QS_REQ_NONE, 0 },
    // --- WEAPONS / TOOLS (10) --------------------------------------------
    { ITEM_BOW, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_BOMBS, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_BOOMERANG, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_GUST_JAR, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_FIRE_ROD, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_NO_PACCI, 0 },
    { ITEM_BOMBBAG, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOMBS, 0 },
    { ITEM_LARGE_QUIVER, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOW, 0 },
    { ITEM_REMOTE_BOMBS, QS_CAT_WEAPON, QS_TIER_UNCOMMON, QS_REQ_BOMBS, 0 },
    { ITEM_MAGIC_BOOMERANG, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_BOOMERANG, 0 },
    { ITEM_MIRROR_SHIELD, QS_CAT_WEAPON, QS_TIER_RARE, QS_REQ_NONE, 0 },
    // --- REWARDS (5) -----------------------------------------------------
    // No rupees (see above) and no heart piece (its own slot).
    { ITEM_BOTTLE1, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_BOTTLE_ROOM, 1 },
    { ITEM_BOTTLE_BLUE_POTION, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_EMPTY_BOTTLE, 1 },
    { ITEM_BOTTLE_RED_POTION, QS_CAT_REWARD, QS_TIER_UNCOMMON, QS_REQ_EMPTY_BOTTLE, 1 },
    { ITEM_HEART_CONTAINER, QS_CAT_REWARD, QS_TIER_RARE, QS_REQ_NONE, 1 },
    { ITEM_BOTTLE_FAIRY, QS_CAT_REWARD, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    // --- SKILL UPGRADES (8) ----------------------------------------------
    { ITEM_SKILL_SPIN_ATTACK, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_ROCK_BREAKER, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_ROLL_ATTACK, QS_CAT_SKILL, QS_TIER_COMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_DASH_ATTACK, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_PERIL_BEAM, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_SWORD_BEAM, QS_CAT_SKILL, QS_TIER_UNCOMMON, QS_REQ_NONE, 0 },
    { ITEM_SKILL_DOWN_THRUST, QS_CAT_SKILL, QS_TIER_RARE, QS_REQ_ROCS_CAPE, 0 },
    { ITEM_SKILL_GREAT_SPIN, QS_CAT_SKILL, QS_TIER_RARE, QS_REQ_SPIN_ATTACK, 0 },
    // --- STAT UPGRADES (6) -----------------------------------------------
    { ITEM_ARROW_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_BOW, 0 },
    { ITEM_DIG_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_MOLE_MITTS, 0 },
    { ITEM_SWIM_BUTTERFLY, QS_CAT_STAT, QS_TIER_UNCOMMON, QS_REQ_FLIPPERS, 0 },
    { BOTTLE_CHARM_NAYRU, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    { BOTTLE_CHARM_FARORE, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
    { BOTTLE_CHARM_DIN, QS_CAT_STAT, QS_TIER_RARE, QS_REQ_EMPTY_BOTTLE, 1 },
};
#define QUICKSTART_SHOP_POOL_SIZE ((s32)ARRAY_COUNT(sQuickStartShopPool))

// --- The shape of the stock, per the user's spec --------------------------
//
// Eight shelf slots, in two kinds.
//
// FOUR are permanent and repeatable - the player can come back and buy them
// all run, as long as the rupees hold out:
//
//   a recovery heart, ten arrows, ten bombs   fixed price, rolled once per
//                                             run in [1, 100]
//   a heart piece                             50 rupees, +25 per purchase
//                                             within the run
//
// The two ammo rows carry their weapon requirement (QS_REQ_BOW /
// QS_REQ_BOMBS), which is the user's "if the player hasn't received the bomb
// bag or the bow/quiver yet, then they can't get these items": the slot sits
// bare until the run finds the weapon, then stocks itself.
//
// FOUR are drawn from the pool above and can be bought exactly ONCE - one
// KEY ITEM, one WEAPON/TOOL, one REWARD, and one that is either a SKILL or a
// STAT upgrade. Their prices are rolled per run in [1, 500]. Once bought, the
// slot stays empty for the rest of the run: nothing restocks it. That is what
// GF_SHOP_SLOT_SOLD_BIT is for - the "is it still sellable" test alone cannot
// express it, because several of these (potions, a bottled charm) are
// repeatable items that stay usable after the first purchase.
#define QUICKSTART_SHOP_FIXED_SLOTS 4
#define QUICKSTART_SHOP_DRAWN_SLOTS 4
#define QUICKSTART_SHOP_SLOTS (QUICKSTART_SHOP_FIXED_SLOTS + QUICKSTART_SHOP_DRAWN_SLOTS)

static const QuickStartTierEntry sQuickStartShopFixed[QUICKSTART_SHOP_FIXED_SLOTS] = {
    { ITEM_HEART, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_NONE, 1 },
    { ITEM_ARROWS10, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_BOW, 1 },
    { ITEM_BOMBS10, QS_CAT_WEAPON, QS_TIER_COMMON, QS_REQ_BOMBS, 1 },
    { ITEM_HEART_PIECE, QS_CAT_REWARD, QS_TIER_COMMON, QS_REQ_NONE, 1 },
};

// What each drawn slot may hold. The last one is deliberately two categories
// at once - "one SKILL upgrade OR STAT upgrade" - so it is not predictable
// which of the two a run will offer.
static const u8 sQuickStartShopSlotCategories[QUICKSTART_SHOP_DRAWN_SLOTS] = {
    QS_CAT_KEY,
    QS_CAT_WEAPON,
    QS_CAT_REWARD,
    QS_CAT_SKILL | QS_CAT_STAT,
};

// Six bits per drawn slot, four slots: bank 11 offsets 97-120. Six because
// the pool is 37 rows now and five bits stopped covering it - the old nine
// 5-bit slots ran to 141, so this shrinks the block rather than growing it.
// QUICKSTART_SHOP_POOL_SIZE is asserted against 64 by the invariant checker
// rather than here, since a static assert would need a header this file does
// not include.
#define GF_SHOP_SLOT_BIT(i, b) (97 + (i) * 6 + (b)) // i = 0..3, b = 0..5
#define QUICKSTART_SHOP_SLOT_EMPTY 63

static s32 QuickStartShopSlotEntry(s32 slot) {
    s32 b, index = 0;
    for (b = 0; b < 6; b++) {
        if (CheckLocalFlagByBank(FLAG_BANK_11, GF_SHOP_SLOT_BIT(slot, b))) {
            index |= (1 << b);
        }
    }
    return index;
}

static void QuickStartShopSetSlotEntry(s32 slot, s32 index) {
    s32 b;
    for (b = 0; b < 6; b++) {
        if (index & (1 << b)) {
            SetLocalFlagByBank(FLAG_BANK_11, GF_SHOP_SLOT_BIT(slot, b));
        } else {
            ClearLocalFlagByBank(FLAG_BANK_11, GF_SHOP_SLOT_BIT(slot, b));
        }
    }
}

// Has this drawn slot already been bought this run? Distinct from "is the
// item still usable": several of the drawn items are repeatable (potions, a
// bottled charm), so usability alone would happily restock them.
static bool32 QuickStartShopSlotSold(s32 drawn) {
    return QsCheckFlag(GF_SHOP_SLOT_SOLD_BIT(drawn));
}

// The item on a given shelf right now, or ITEM_NONE for a shelf that should
// stand bare. Re-derived rather than cached, which is what makes the shelf
// keep itself honest: a slot goes quiet the moment its item stops being
// sellable, instead of restocking something the player cannot use or has
// already bought.
//
// Three ways a shelf comes up empty:
//   - a drawn slot whose item has been bought (GF_SHOP_SLOT_SOLD_BIT);
//   - a drawn slot whose draw came up empty (its category was exhausted);
//   - either kind whose item is not currently usable - arrows with no bow, a
//     potion with no empty bottle, a key item the run has since found
//     elsewhere.
static u16 QuickStartShopSlotItem(s32 slot) {
    const QuickStartTierEntry* e;
    if (slot < QUICKSTART_SHOP_FIXED_SLOTS) {
        e = &sQuickStartShopFixed[slot];
    } else {
        s32 drawn = slot - QUICKSTART_SHOP_FIXED_SLOTS;
        s32 index = QuickStartShopSlotEntry(drawn);
        if (index >= QUICKSTART_SHOP_POOL_SIZE || QuickStartShopSlotSold(drawn)) {
            return ITEM_NONE;
        }
        e = &sQuickStartShopPool[index];
    }
    if (!QuickStartTierEntryUsable(e)) {
        return ITEM_NONE;
    }
    return e->item;
}
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
// instead. `offsets` must have exactly QUICKSTART_SHOP_SLOTS entries, one per
// shelf slot in the same order.
//
// A slot whose item is ITEM_NONE is simply left bare: either its draw came up
// empty, or the item is no longer sellable (bought, or gated on something the
// player lacks). That is the intended read - the shelf empties as the player
// clears it out.
static void QuickStartMaintainShop(const s16 (*offsets)[2]) {
    s32 i;
    for (i = 0; i < QUICKSTART_SHOP_SLOTS; i++) {
        u16 item = QuickStartShopSlotItem(i);
        if (item != ITEM_NONE && !QuickStartShopItemExists(item)) {
            QuickStartSpawnShopItem(item, offsets[i][0], offsets[i][1]);
        }
    }
}

// --- The shop's own room ---------------------------------------------------
//
// The shop is a fixture of the hub now: Floor 1 of Home of the Wind Tribe,
// one flight up from the entrance and three below the item selection, walked
// to like any other room in the tower.
//
// It used to be a "? room". First it lived in the Grimblade dojo behind a
// fixed link from Melari's Mine; then, when the mine stopped being the hub,
// it moved into Stockwell's own store and was reached through ONE randomly
// drawn overworld door per run, whose real transition was caught mid-flight
// and redirected (sQuickStartShopDoors, QuickStartProcessDoorRedirects) with
// a matching return fixup on the way out. All of that is retired. A hub with
// a shop in it does not need the shop hidden somewhere in the overworld, and
// the old arrangement carried two standing bugs with it - the drawn door's
// usual "? room" event was displaced for that run, and Stockwell's upper-right
// shelf sat in a sealed pocket that took three attempts to lay out around.
//
// What survives unchanged: the catalog, the per-run price roll
// (QuickStartGetShopPrice), the merchant NPC and script_QuickStartMerchant,
// and vanilla's own lift-and-carry pedestal sale.
//
// GF_SHOP_DOOR_BIT's five flag bits (658-662) are free now, as is the whole
// of the retired 3-bit price roll (663-689).
#define QUICKSTART_SHOP_AREA AREA_WIND_TRIBE_TOWER
#define QUICKSTART_SHOP_ROOM ROOM_WIND_TRIBE_TOWER_FLOOR_1

// A rupee price in [1, limit], drawn uniformly.
//
// Rejection rather than a modulo, for the reason QuickStartTierPick
// documents: `limit` is a compile-time constant at every call site today, but
// agbcc emits a call to __umodsi3 for a division by a non-constant and its
// runtime library does not provide one, so the whole file keeps to masks and
// rejection. The mask is the smallest power of two above the limit, so at
// worst (limit 100, mask 127) a draw is accepted 78% of the time; sixteen
// tries makes a fallthrough vanishingly unlikely, and the fallthrough itself
// is still a valid price rather than a wrong one.
static s32 QuickStartRollShopPrice(s32 limit, s32 mask) {
    s32 attempt, roll = 0;
    for (attempt = 0; attempt < 16; attempt++) {
        roll = (s32)Random() & mask;
        if (roll < limit) {
            return roll + 1;
        }
    }
    return (roll & (limit - 1)) + 1;
}

// Rolled once per run: what the four drawn shelves hold, and what everything
// costs.
//
// Each drawn slot takes its own category (sQuickStartShopSlotCategories) by
// rejection so no item appears twice: pick a usable pool row of the right
// category, reject it if an earlier slot already took it, try again. Bounded
// rather than looped forever - if a category is exhausted (a run that already
// owns every key item, say) the slot is left empty, which the shelf shows as
// bare floor.
//
// "Usable" is QuickStartTierEntryUsable, the same test every other draw in
// this file uses, so ammo is never stocked without its weapon and a potion is
// never stocked without a bottle to put it in. Note what that means for the
// draw specifically: a category is filtered by what the player holds AT RUN
// START, which is right after the three selection rounds - so the shop will
// not offer back the key item they just chose.
//
// The four permanent slots need no draw, only prices. The heart piece needs
// not even that: its price is a function of how many have been bought this
// run, and the counter starts every run at zero with the rest of the QS
// window.
static void QuickStartRandomizeShopOnce(void) {
    s32 i, j, attempt;
    if (QsCheckFlag(GF_SHOP_RANDOMIZED)) {
        return;
    }
    for (i = 0; i < QUICKSTART_SHOP_DRAWN_SLOTS; i++) {
        s32 chosen = QUICKSTART_SHOP_SLOT_EMPTY;
        for (attempt = 0; attempt < 64; attempt++) {
            s32 pick = (s32)Random() % QUICKSTART_SHOP_POOL_SIZE;
            const QuickStartTierEntry* e = &sQuickStartShopPool[pick];
            if (!(e->cat & sQuickStartShopSlotCategories[i])) {
                continue;
            }
            if (!QuickStartTierEntryUsable(e)) {
                continue;
            }
            for (j = 0; j < i; j++) {
                if (QuickStartShopSlotEntry(j) == pick) {
                    break;
                }
            }
            if (j < i) {
                continue;
            }
            chosen = pick;
            break;
        }
        QuickStartShopSetSlotEntry(i, chosen);
        // The price roll is per SLOT, not per item, so it stays valid however
        // the draw came out.
        QsWriteField(GF_SHOP_ONEOFF_PRICE_BIT(i, 0), QUICKSTART_SHOP_ONEOFF_PRICE_BITS,
                     QuickStartRollShopPrice(QUICKSTART_SHOP_ONEOFF_PRICE_MAX, 0x1ff) - 1);
    }
    for (i = 0; i < QUICKSTART_SHOP_FIXED_SLOTS - 1; i++) {
        QsWriteField(GF_SHOP_REFILL_PRICE_BIT(i, 0), QUICKSTART_SHOP_REFILL_PRICE_BITS,
                     QuickStartRollShopPrice(QUICKSTART_SHOP_REFILL_PRICE_MAX, 0x7f) - 1);
    }
    QsSetFlag(GF_SHOP_RANDOMIZED);
}

// Records a completed sale. Called from ScriptCommand_BuyShopItem (script.c),
// which is the one place a purchase actually goes through - the confirm
// message and the affordability check both run before it and can still be
// declined.
//
// Two things follow from a sale: a heart piece pushes the NEXT heart piece 25
// rupees higher, and one of the four drawn slots empties for good. Neither
// can be inferred from the shelf itself. The prop deleting itself is not the
// signal - a prop is also deleted when the room unloads, and
// QuickStartMaintainShop respawns it either way, which is exactly what makes
// the four permanent slots work.
void QuickStartNoteShopPurchase(u32 item) {
    s32 i;
    if (!QsCheckFlag(GF_SHOP_RANDOMIZED)) {
        return;
    }
    if (item == ITEM_HEART_PIECE) {
        s32 buys = QsReadField(GF_SHOP_HEART_PIECE_BUYS_BIT(0), 5);
        if (buys < QUICKSTART_SHOP_HEART_PIECE_BUYS_MAX) {
            QsWriteField(GF_SHOP_HEART_PIECE_BUYS_BIT(0), 5, buys + 1);
        }
        return;
    }
    for (i = 0; i < QUICKSTART_SHOP_DRAWN_SLOTS; i++) {
        s32 index = QuickStartShopSlotEntry(i);
        if (index < QUICKSTART_SHOP_POOL_SIZE && sQuickStartShopPool[index].item == item) {
            QsSetFlag(GF_SHOP_SLOT_SOLD_BIT(i));
            return;
        }
    }
}


// This run's price for one of the shop's own wares, or a negative value for
// anything the run isn't pricing itself.
//
// These are ABSOLUTE amounts now, not a scale factor on the vanilla table.
// That was the only way to honour the user's spec ("a fixed price between 1
// and 100 rupees", "randomly assigned between 1 and 500") - a multiplier on
// whatever gUnk_080FD964 happened to list cannot hit a stated range, and half
// this shelf (the recovery heart, the butterflies, the charms) has a vanilla
// price of zero to scale in the first place. The old 3-bit (4+roll)/8 roll is
// retired with it.
//
// `basePrice` is now unused for the same reason: it was the thing being
// scaled, and it was also the fast reject - a zero-priced item was assumed
// not to be shop stock. It is exactly the recovery heart, so the reject is
// GF_SHOP_RANDOMIZED plus the slot scan instead. The parameter stays in the
// signature because GetItemPrice (itemUtils.c) has it to hand and a future
// price rule may want it again.
//
// Called from GetItemPrice for EVERY item lookup in the game, so it has to be
// cheap and has to say "not mine" quickly. Vanilla shops elsewhere keep their
// own prices untouched.
//
// Reads the slot's drawn pool row directly rather than through
// QuickStartShopSlotItem: that one also applies the usability and sold tests,
// and an item being priced is not the same question as it being stocked - the
// price has to keep answering while the sale completes, which is exactly when
// the slot is being marked sold and the player is about to own it.
s32 QuickStartGetShopPrice(u32 item, s32 basePrice) {
    s32 i;
    if (!QsCheckFlag(GF_SHOP_RANDOMIZED)) {
        return -1;
    }
    // The heart piece: 50 rupees, then 25 more for each one already bought
    // this run. Derived on every lookup rather than stored, so the displayed
    // price and the charged price cannot drift apart across a purchase.
    // Deliberately ABOVE the Broken Sword cap below, per the user: the
    // heart piece's climbing price is the one thing the pity discount
    // does not touch.
    if (item == ITEM_HEART_PIECE) {
        return QUICKSTART_SHOP_HEART_PIECE_BASE +
               QUICKSTART_SHOP_HEART_PIECE_STEP * QsReadField(GF_SHOP_HEART_PIECE_BUYS_BIT(0), 5);
    }
    for (i = 0; i < QUICKSTART_SHOP_FIXED_SLOTS - 1; i++) {
        if (sQuickStartShopFixed[i].item == item) {
            s32 price = QsReadField(GF_SHOP_REFILL_PRICE_BIT(i, 0), QUICKSTART_SHOP_REFILL_PRICE_BITS) + 1;
            // The Broken Sword charm: merchants take pity - nothing costs
            // more than 50. A CAP, not an assignment, so a lucky cheap
            // roll stays cheap.
            if ((QuickStartFoodMask() & QUICKSTART_FOOD_CHEAP_SHOP) && price > QUICKSTART_CHEAP_SHOP_PRICE) {
                price = QUICKSTART_CHEAP_SHOP_PRICE;
            }
            return price;
        }
    }
    for (i = 0; i < QUICKSTART_SHOP_DRAWN_SLOTS; i++) {
        s32 index = QuickStartShopSlotEntry(i);
        s32 price;
        if (index >= QUICKSTART_SHOP_POOL_SIZE || sQuickStartShopPool[index].item != item) {
            continue;
        }
        price = QsReadField(GF_SHOP_ONEOFF_PRICE_BIT(i, 0), QUICKSTART_SHOP_ONEOFF_PRICE_BITS) + 1;
        if ((QuickStartFoodMask() & QUICKSTART_FOOD_CHEAP_SHOP) && price > QUICKSTART_CHEAP_SHOP_PRICE) {
            price = QUICKSTART_CHEAP_SHOP_PRICE;
        }
        return price;
    }
    return -1;
}

// Where the merchant stands and where the catalog is laid out, on Floor 1 of
// the tower. Measured (a live collision dump, tools/quickstart/emu.py): the
// floor is 240x336 and splits into two blocks joined by the stair column at
// tile column 3 -
//
//   upper hall  rows 5-7   (y 80-127), columns 2-12 (x 32-207), fully open
//   lower block rows 15-18 (y 240-303), columns 2-12, plus rows 13-14 at
//               columns 2-4
//
// and the two blocks really are one connected component: walked it in the
// emulator, (56,112) down the column to (56,302) and (56,216) back up to
// (56,87).
//
// The catalog goes in the UPPER hall, all eight of it, because the lower
// block is where the traffic is: arriving from the Entrance lands the player
// at (184,248) and arriving from Floor 2 at (136,248), and stock strewn
// across the arrival tiles is exactly the complaint the Stockwell layout drew
// ("all the items are on the first tiles when you enter").
//
// Two rows with a walkway between them, so every item is approached from open
// floor rather than over a counter - the thing that made Stockwell's shelves
// take four attempts to lay out:
//
//   y=88    the four one-off items   (row 5, slots 4-7)
//   y=104   the walkway              (row 6) - and the merchant, east end
//   y=120   the four permanent ones  (row 7, slots 0-3)
//
// Slot order is display order, and the split is deliberate: the four
// permanent slots (heart, arrows, bombs, heart piece) are the ones a player
// comes back to over and over, so they sit on the near row, and the run's
// four one-off wares sit behind them where they read as the special stock.
//
// The x offsets are the SAME ones the nine-slot layout used - the near row is
// its old front row unchanged, the far row its old back row with the last
// entry dropped. Re-spacing the eight evenly across the hall was tried first
// and the checker caught it: at (176,120) the heart piece spawned fine and
// then would not lift from the walkway tile in front of it. These eight are
// each emulator-verified liftable, so they are what the layout keeps.
//
// Nothing here is on a shelf, in an alcove, or in a separate collision
// component, which is the whole reason for moving the shop into the hub.
#define QUICKSTART_SHOP_MERCHANT_X 192
#define QUICKSTART_SHOP_MERCHANT_Y 104
static const s16 sQuickStartShopRoomItemOffsets[][2] = {
    { 64, 120 }, { 96, 120 }, { 128, 120 }, { 160, 120 }, // near row, the permanent four
    { 48, 88 },  { 80, 88 },  { 112, 88 },  { 144, 88 },  // far row, the one-off four
};

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
#define GF_SLOTS_RANDOMIZED 0x65
#define GF_SLOT_BASE(i) (0x66 + (i) * 18)
// Bit +0 of each ladder's block used to be unused - it was GF_LADDER_REVEALED,
// tracking whether the marker pot had been broken yet (removed along with
// the whole pot mechanic). Repurposed now as GF_SLOT_POOL_BIT: which of
// the two size-restricted room pools (sQuickStartSmallRoomPool/
// sQuickStartMediumRoomPool below) this ladder drew from, so its kind roll
// and room draw both stay inside that pool's own rules (see
// QuickStartRandomizeSlotsOnce).
#define GF_SLOT_POOL_BIT(i) (GF_SLOT_BASE(i) + 0)
#define GF_SLOT_KIND_BIT(i, b) (GF_SLOT_BASE(i) + 1 + (b))  // b = 0,1
// 3rd kind bit, added for QS_EVENT_POT_LOTTERY/CHEST_LOTTERY/FAIRY - see
// GameTask_Transition's own comment on why this lives outside the
// contiguous per-ladder block instead of widening it in place.
#define GF_SLOT_KIND_BIT2(i) (202 + (i))
#define GF_SLOT_EXTRA_BIT(i, b) (GF_SLOT_BASE(i) + 3 + (b)) // b = 0..7
#define GF_SLOT_DONE(i) (GF_SLOT_BASE(i) + 11)
// Which pool entry backs this ladder this save - a second independent
// Random() draw from the kind/extra above, so the physical room and the
// reward/challenge it holds vary separately. 6 bits covers indices 0-31,
// comfortably more than either pool's size.
#define GF_SLOT_ROOM_BIT(i, b) (GF_SLOT_BASE(i) + 12 + (b)) // b = 0..5

// There used to be a second, parallel copy of this whole slot shape here:
// GF_DOOR_*, 15 synthetic door entrances at 19 bits each, living at
// FLAG_BANK_12 raw offsets 300-585. Every one of those 15 entrances was
// retired when the single-door "? rooms" moved to the room-keyed content
// site table below - QuickStartRandomizeDoorsOnce skipped all 15, and
// QuickStartFindSlotForCurrentRoom skipped slots 1-18 - so the block was
// written by nothing and read by nothing, but it still SAT on 286 bits in
// the middle of the one bank this mode has room to grow in. Deleting it is
// what makes the content site block below able to expand; see the flag map
// there. The accessors below lost their "is this a door slot?" branch with
// it, because slotIndex can only ever be 0-3 now.
#define QUICKSTART_LEGACY_LADDER_SLOTS 4

static u8 QuickStartSlotGetPool(s32 slotIndex) {
    return QsCheckFlag(GF_SLOT_POOL_BIT(slotIndex)) ? 1 : 0;
}

static void QuickStartSlotSetPool(s32 slotIndex, u8 pool) {
    if (pool) {
        QsSetFlag(GF_SLOT_POOL_BIT(slotIndex));
    } else {
        QsClearFlag(GF_SLOT_POOL_BIT(slotIndex));
    }
}

// Check/set wrapper for GF_SLOT_DONE(slotIndex), widened the same way as
// the accessors above - every call site that used to do
// QsCheckFlag(GF_SLOT_DONE(slotIndex))/QsSetFlag(GF_SLOT_DONE(slotIndex))
// directly now goes through these instead, so door-slot "done" state lands
// in FLAG_BANK_12 too.
static u32 QuickStartLadderCheckDone(s32 slotIndex) {
    return QsCheckFlag(GF_SLOT_DONE(slotIndex));
}

static void QuickStartSlotSetDone(s32 slotIndex) {
    QsSetFlag(GF_SLOT_DONE(slotIndex));
}

// Difficulty counter for the win/reset loop below - well clear of the
// ladder bits above (highest in use is GF_SLOT_ROOM_BIT(3,5) = 173, the
// 4th ladder slot being the Goron Cave Stairs door's own pool draw - see
// QuickStartRandomizeSlotsOnce below).
// 4 bits -> 0..15 (only 0..QUICKSTART_MAX_DIFFICULTY are ever produced by
// QuickStartIncrementDifficulty, but the extra headroom over the previous
// 2-bit counter costs nothing and leaves room to extend the curve later).
// Save-persistent (global flags, not room flags) since it has to survive
// the DoSoftReset a win triggers - EWRAM (and gSave with it) is
// deliberately preserved across that reset (see DoSoftReset, main.c), and
// WriteSaveFile below makes sure it's actually on the save file the
// title/file-select flow reloads from, not just sitting in EWRAM.
#define GF_DIFFICULTY_BIT(b) (174 + (b)) // b = 0..3

// Exposed (non-static) for src/itemUtils.c's drop-table hook, which needs
// the run's difficulty to scale kinstone weights. Kept as a function rather
// than a shared variable: game.c must not add .bss/.data.
u8 QuickStartDifficultyForDrops(void) {
    return QuickStartGetDifficulty();
}

static u8 QuickStartGetDifficulty(void) {
    return (QsCheckFlag(GF_DIFFICULTY_BIT(0)) ? 1 : 0) | (QsCheckFlag(GF_DIFFICULTY_BIT(1)) ? 2 : 0) |
           (QsCheckFlag(GF_DIFFICULTY_BIT(2)) ? 4 : 0) | (QsCheckFlag(GF_DIFFICULTY_BIT(3)) ? 8 : 0);
}

static void QuickStartIncrementDifficulty(void) {
    u8 next = QuickStartGetDifficulty();
    s32 b;
    if (next < QUICKSTART_MAX_DIFFICULTY) {
        next++;
    }
    for (b = 0; b < 4; b++) {
        if (next & (1 << b)) {
            QsSetFlag(GF_DIFFICULTY_BIT(b));
        } else {
            QsClearFlag(GF_DIFFICULTY_BIT(b));
        }
    }
}

// Persistent HUD readout of the current run's difficulty (the user asked
// "is there a way to display the current difficulty... a counter on the
// HUD"). Uses the exact same BG0-tilemap digit mechanism DrawRupees/
// DrawKeys already use (RenderDigits, ui.c): reading RenderDigits' own
// addressing (src/ui.c) shows iconVramIndex is a starting VRAM tile index
// and each decimal digit consumes 2 consecutive tiles for its 8x16 glyph
// (top half/bottom half) - rupees (3 digits) claims 0x70-0x75, keys (2
// digits) claims 0x76-0x79 right after, so 0x7A is the first tile past
// both. Confirmed safe empirically (screenshot after wiring this up shows
// nothing else on screen affected).
//
// Placed at the bottom-left corner of the screen (gBG0Buffer row 18, col
// 0-1 - row 18 is the same row DrawRupees uses on the opposite/right side
// of the screen) since every screenshot taken this session shows that
// corner is otherwise always empty.
//
// Redrawn unconditionally every frame rather than latched "once per run" -
// a first attempt used a one-shot global-flag latch (matching the "draw
// once" instinct: difficulty never changes mid-run), but that only ever
// showed up for a single frame before vanishing again, confirmed via
// memory inspection in the emulator: every real room transition reloads
// the WHOLE BG0 tilemap and character data fresh from the new room's own
// map data, wiping both the tilemap entries and the tile graphics
// RenderDigits had written, and the latch then prevented ever redrawing
// either. DrawRupees/DrawKeys (ui.c) already solve exactly this the same
// way - reasserting their own tiles/digits every single frame rather than
// once - so this does the same instead of trying to be cleverer about it.
// The actual cost (a handful of u16 writes plus RenderDigits' own small
// DMA copies) is trivial on GBA hardware and no different in kind from
// what those two already do far more often (every frame rupees/keys are
// on screen at all).
//
// VRAM tile 0x7A (this constant's first value) turned out NOT to be free -
// missed on the first pass because only ui.c's own RenderDigits call sites
// (rupees at 0x70, keys at 0x76) were checked. message.c's own textbox
// border tiles (MSG_BORDER_CORNER = 0x7B, running through 0x7F) sit right
// past those, and the real message-text glyph rendering claims a further
// stretch beyond that (MSG_TEXT_LINE1TOP=0x82 through MSG_TEXT_LINE2BOTTOM=
// 0xB7 and whatever ring of tiles follows it) - overlapping this HUD
// element's 4 tiles (0x7A-0x7D) corrupted the textbox border into a
// garbled tooth/comb pattern the instant any message showed on screen
// (reported by the user, reproduced by inspecting message.c after the
// report rather than guessing blind).
//
// 0x1E0 (the value this moved to next) turned out to be a second, worse
// instance of the exact same mistake: RenderDigits' iconVramIndex is a
// *character* tile index into BG0's own charbase (charbase 3, i.e.
// VRAM+0xC000), but charbase 3 is also where the screenbases (tilemaps) for
// ALL FOUR backgrounds live on this build - gScreen.bg0/bg1/bg2/bg3.control
// put their screenbases at 31/29/28/30 respectively, and screenbase N
// occupies VRAM+N*0x800, which for N=28..31 falls at VRAM+0xE000-0xFFFF -
// i.e. charbase-3 *character* tile indices 0x100-0x1FF are not free tile
// graphics at all, they ARE the live tilemaps. 0x1E0 sits squarely inside
// BG0's own screenbase (31, tiles 0x1C0-0x1FF), so every single redraw of
// this HUD element DMA'd digit-glyph pixel data directly over 4 tiles' worth
// of BG0's real tilemap (rows 16-17, spanning both columns since RenderDigits
// writes a contiguous run) - two of those overwritten cells happened to
// decode as an opaque, solid-black pixel (BG0 is priority 0, i.e. always on
// top, and screen-locked, i.e. it doesn't scroll with the room camera), so
// the corruption showed up as two small solid-black rectangles fixed at the
// same screen position in every room, reappearing every frame this runs.
// Root-caused via mGBA memory/VRAM introspection + single-step tracing back
// to the exact RenderDigits DMA call that overwrites screenbase 31.
//
// The only tile range in charbase 3 that is actually just character
// graphics (not doubling as one of the four screenbases) is 0x000-0x0FF, and
// of that, everything up through message text (0x82-0xB7, see message.c) is
// already claimed. 0xF0 sits in the gap between the message system's last
// known tile and the start of the screenbase region (0x100) with a
// comfortable margin on both sides, confirmed empirically with a message box
// open on screen and after multiple room transitions (the failure mode this
// bug depended on).
#define QUICKSTART_DIFFICULTY_VRAM_TILE 0xF0
static void QuickStartDrawDifficultyHUD(void) {
    u16* row1 = &gBG0Buffer[0x240];
    u16* row2 = &gBG0Buffer[0x260];
    u16 temp = 0xf000 | QUICKSTART_DIFFICULTY_VRAM_TILE;
    row1[0] = temp;
    row2[0] = temp + 1;
    row1[1] = temp + 2;
    row2[1] = temp + 3;
    gScreen.bg0.updated = 1;
    RenderDigits(QUICKSTART_DIFFICULTY_VRAM_TILE, QuickStartGetDifficulty(), 0, 2);
}

// The enemy roster, grouped into 5 hand-picked difficulty levels (level 1
// easiest, level 5 hardest) per the user's own list - only enemies with a
// straightforward, crash-free CreateEnemy(id, form) spawn made the cut;
// anything with a mechanic that needs more setup (a scripted home/range, a
// room property, dungeon entrance data, etc.) was deliberately left out.
// "form" here is the same value CreateEnemy's second argument always was
// elsewhere in this file (entity->type) - for enemies with a color variant
// it selects which color; for the rest it's always 0.
// Two fields beyond the id/form pair the roster started as, both feeding
// the composition builder below (roadmap: the Wave Composition Study).
//
// `roles` is what this enemy IS, as a bitmask, so an archetype can ask for
// "something that shoots" or "something that swarms" instead of naming
// kinds. `cost` is what its sprite SHEET costs the GFX table, in slots,
// read out of gEnemyDefinitions/gFixedTypeGfxData (a slot is 0x200 bytes;
// see LoadFixedGFX and the fixed_gfx macro). Cost is the honest currency
// for wave variety: kinds range 1..8 slots, so counting kinds - which is
// what QUICKSTART_MAX_ENEMY_KINDS used to do - both over-permits three
// expensive ones (Puffstool + Bow Moblin + Ghini is 21 slots) and
// over-forbids six cheap ones (six 1-slot kinds is 6). The budget below
// spends slots instead, which is what the table actually runs out of.
#define QS_R_CHAFF 0x01  /* dies fast; safe to field in numbers */
#define QS_R_HEAVY 0x02  /* elite: high hp or armored - the rationed stuff */
#define QS_R_RANGED 0x04 /* attacks from a distance */
#define QS_R_FLYER 0x08  /* ignores ground obstacles */
#define QS_R_AMBUSH 0x10 /* hides, burrows or waits */
#define QS_R_FAST 0x20   /* speed >= 256 */
#define QS_R_SLOW 0x40   /* speed <= 96; a wall, not a threat */
#define QS_R_THIEF 0x80  /* takes items/rupees rather than health */

// `requires` is an item the player must own before this enemy may be drawn
// into a wave, or 0 for "always eligible". It exists because wave clear
// demands an empty room, so an enemy the player has no way to kill stalls
// the region for the rest of the run.
//
// Two are known, both found by reading their collision handlers rather
// than by guessing (contact ids are in include/collision.h):
//   SPARK   dies only to (contactFlags & 0x7f) == 0x14 = COL_BOOMERANG.
//           This is the user's own example - "certain enemies who won't
//           die by the sword will die by the bow & arrow or boomerang...
//           the shock sprites".
//   LAKITU  dies only to COL_PACCI (0x1d), the Cane of Pacci.
// Both stay in the roster - they are good enemies - but they now only
// appear once the player is carrying the answer to them.
typedef struct {
    u8 id;
    u8 form;
    u8 roles;
    u8 cost;
    u16 requires;
} QuickStartEnemyPick;

// The roster is sorted by what actually makes an enemy dangerous, in this
// order: HEALTH (the one true scalar in gEnemyDefinitions), then whether
// it threatens the player's THINGS rather than their hearts (shield and
// rupee theft compound worse than damage), then reach and mobility, then
// whether it needs a specific answer.
//
// A note on "damage dealt": the definition table's damageType is NOT a
// number of hearts. It is a type id handed to whatever it touches, and the
// receiver's own handler decides what it means (see intr.s, where hitType
// is written into the victim's contactFlags). So damage ranking here is
// qualitative - armored, ranged, status-inflicting - rather than numeric,
// and health carries the ordering.

// Level 1 - chaff. Health 1-4, no theft, no armor, nothing that needs an
// answer. This is the whole roster a player meets before difficulty 4.
static const QuickStartEnemyPick sQuickStartLevel1[] = {
    { BEETLE, 0, QS_R_CHAFF | QS_R_FAST, 1, 0 },
    { KEESE, 0, QS_R_CHAFF | QS_R_FLYER | QS_R_FAST, 1, 0 },
    { SMALL_PESTO, 0, QS_R_CHAFF | QS_R_FLYER | QS_R_SLOW, 1, 0 },
    { TEKTITE, 0 /* red */, QS_R_CHAFF | QS_R_FAST, 1, 0 },
    { CROW, 0, QS_R_CHAFF | QS_R_FLYER | QS_R_FAST, 2, 0 },
    { MINI_SLIME, 0, QS_R_CHAFF | QS_R_SLOW, 2, 0 },
    { GYORG_CHILD, 0, QS_R_CHAFF | QS_R_FLYER, 2, 0 },
    { OCTOROK, 0 /* red */, QS_R_CHAFF | QS_R_RANGED | QS_R_SLOW, 3, 0 },
    { PEAHAT, 0, QS_R_CHAFF | QS_R_FLYER, 2, 0 },
    { CHUCHU, 0 /* green */, QS_R_CHAFF | QS_R_SLOW, 4, 0 },
    { ROPE, 0, QS_R_CHAFF | QS_R_AMBUSH, 4, 0 },
};
// Level 2 - light. Health 4-8, or a mechanic (burrowing, exploding,
// stationary fire) that asks for a little more than walking up and
// swinging.
static const QuickStartEnemyPick sQuickStartLevel2[] = {
    { SLUGGULA, 0, QS_R_CHAFF | QS_R_RANGED | QS_R_SLOW, 2, 0 },
    { OCTOROK2, 0, QS_R_CHAFF | QS_R_RANGED | QS_R_SLOW, 3, 0 },
    { OCTOROK, 1 /* blue */, QS_R_RANGED | QS_R_SLOW, 3, 0 },
    { SLIME, 0, QS_R_CHAFF | QS_R_SLOW, 2, 0 },
    { STALFOS, 0 /* red */, QS_R_CHAFF | QS_R_FAST, 2, 0 },
    { STALFOS, 1 /* blue */, QS_R_CHAFF | QS_R_FAST, 2, 0 },
    { KEATON, 0, QS_R_CHAFF | QS_R_FAST, 1, 0 },
    { HELMASAUR, 0, QS_R_FAST, 4, 0 },
    { PESTO, 0 /* red */, QS_R_CHAFF | QS_R_FLYER | QS_R_SLOW, 3, 0 },
    { CHUCHU, 2 /* blue */, QS_R_CHAFF | QS_R_SLOW, 4, 0 },
    { BOBOMB, 0, QS_R_SLOW, 2, 0 },
    { BOMBAROSSA, 0, QS_R_RANGED | QS_R_FAST, 1, 0 },
    { LEEVER, 0 /* red */, QS_R_CHAFF | QS_R_AMBUSH, 2, 0 },
    { MULLDOZER, 0 /* red */, QS_R_SLOW, 4, 0 },
    { TEKTITE, 1 /* blue */, QS_R_FAST, 1, 0 },
    { LEEVER, 1 /* blue */, QS_R_AMBUSH, 2, 0 },
};
// Yellow and purple Keaton are the same actor with no form-based color
// variant (confirmed empirically - all 4 form values render identically),
// so Keaton only appears once here rather than duplicated into level 4.
// Level 3 - mid. Health 8-10, armored shells, splitters, spore clouds and
// the first stationary artillery. Nothing here steals and nothing here
// needs a specific item.
static const QuickStartEnemyPick sQuickStartLevel3[] = {
    { MOLDORM, 0, QS_R_FAST, 2, 0 },
    { GHINI, 0, QS_R_FLYER | QS_R_FAST, 5, 0 },
    { ARMOS, 0, QS_R_AMBUSH | QS_R_SLOW, 5, 0 },
    { EYEGORE, 0, QS_R_RANGED | QS_R_SLOW, 6, 0 },
    { MULLDOZER, 1 /* blue */, QS_R_SLOW, 4, 0 },
    { PESTO, 1 /* blue */, QS_R_CHAFF | QS_R_FLYER | QS_R_SLOW, 3, 0 },
    { CHUCHU, 1 /* red */, QS_R_CHAFF | QS_R_SLOW, 4, 0 },
    { ROCK_CHUCHU, 0, QS_R_SLOW, 2, 0 },
    { SPINY_CHUCHU, 0, QS_R_SLOW, 6, 0 },
    { SPIKED_BEETLE, 0, QS_R_AMBUSH | QS_R_SLOW, 5, 0 },
    { PUFFSTOOL, 0, QS_R_CHAFF | QS_R_SLOW, 8, 0 },
    { FIREBALL_GUY, 0, QS_R_RANGED, 4, 0 },
    { MINI_FIREBALL_GUY, 0, QS_R_CHAFF | QS_R_RANGED, 4, 0 },
    { BOMB_PEAHAT, 0, QS_R_FLYER, 2, 0 },
    { CLOUD_PIRANHA, 0, QS_R_AMBUSH, 4, 0 },
    { SPINY_BEETLE, 0, QS_R_FAST, 2, 0 },
    { ENEMY_50, 0, QS_R_FAST, 5, 0 },
};
// Floormaster (Wall Master) deliberately left out - it grabs the player and
// warps them to a dungeon's scripted "entrance" point, which none of these
// QUICKSTART rooms have configured, so the actual destination would be
// undefined.
// Darknut (the vanilla game's own recurring miniboss, e.g. Palace of Winds'
// "Darknut Miniboss" room and the Castor Wilds encounter this file's own
// fixed-room setup already spawns) is already a proven, crash-free
// CreateEnemy(DARK_NUT, form) call elsewhere in this file (see the Castor
// Darknut room setup and the ladder-room QS_EVENT_MINIBOSS spawn code
// below) - gEnemyDefinition_5 (enemy.c) gives it 4 forms with increasing
// health (12/12/20/26), so the two weaker forms are grouped here with the
// rest of level 4 and the two tougher ones go in level 5 below.
// Level 4 - heavy. Health 16-20, or a thief. Theft sits at this level
// regardless of health: losing a shield or a purse compounds across a run
// in a way that taking a heart does not.
static const QuickStartEnemyPick sQuickStartLevel4[] = {
    { LIKE_LIKE, 0, QS_R_HEAVY | QS_R_SLOW | QS_R_THIEF, 2, 0 },
    { RUPEE_LIKE, 0 /* green */, QS_R_HEAVY | QS_R_THIEF, 4, 0 },
    { RUPEE_LIKE, 2 /* red */, QS_R_HEAVY | QS_R_THIEF, 4, 0 },
    { RUPEE_LIKE, 1 /* blue */, QS_R_HEAVY | QS_R_THIEF, 4, 0 },
    { TAKKURI, 0, QS_R_FAST | QS_R_FLYER | QS_R_THIEF, 2, 0 },
    { GOBDO, 0 /* gibdo */, QS_R_HEAVY | QS_R_SLOW, 2, 0 },
    { SCISSORS_BEETLE, 0, QS_R_HEAVY, 1, 0 },
    { MOLDWORM, 0, QS_R_HEAVY, 6, 0 },
    { ENEMY_4D, 0, QS_R_HEAVY, 1, 0 },
    { BOW_MOBLIN, 0, QS_R_RANGED | QS_R_FAST, 8, 0 },
    { SPEAR_MOBLIN, 0, QS_R_FAST, 8, 0 },
    { ACRO_BANDIT, 0, QS_R_CHAFF, 7, 0 },
};
// Since QuickStartPickEnemy is rolled independently per enemy (see its own
// comment above), a high-difficulty wave that leans heavily on level 5 can
// already come up with more than one Darknut/Ball and Chain Soldier/Wizzrobe
// in the same room purely by chance - no separate "spawn N minibosses"
// mechanism needed for that.
// Level 5 - specialists. Not the toughest (that is the Elites below) but
// the ones that change HOW you fight: casters that teleport and inflict an
// element, the 64hp golden trio that soaks a whole magazine, the hazards
// that ignore a sword entirely and need the right tool in hand.
static const QuickStartEnemyPick sQuickStartLevel5[] = {
    { WIZZROBE_FIRE, 0, QS_R_RANGED | QS_R_FAST, 4, 0 },
    { WIZZROBE_ICE, 0, QS_R_RANGED | QS_R_FAST, 5, 0 },
    { WIZZROBE_WIND, 0, QS_R_RANGED | QS_R_FAST, 3, 0 },
    { TEKTITE_GOLDEN, 0, QS_R_HEAVY | QS_R_FAST, 1, 0 },
    { OCTOROK_GOLDEN, 0, QS_R_HEAVY | QS_R_RANGED | QS_R_SLOW, 3, 0 },
    { ROPE_GOLDEN, 0, QS_R_HEAVY | QS_R_AMBUSH, 4, 0 },
    { ROLLOBITE, 0, QS_R_FAST, 6, 0 },
    { WISP, 0 /* red */, QS_R_FLYER, 3, 0 },
    { WISP, 1 /* blue */, QS_R_FLYER | QS_R_FAST, 3, 0 },
    // Weapon-gated (see the `requires` note on QuickStartEnemyPick): these
    // two shrug off a sword, so they only join once their answer is in the
    // bag. Drawn like anything else once it is.
    { SPARK, 0, QS_R_FAST, 1, ITEM_BOOMERANG },
    { LAKITU, 0, QS_R_RANGED | QS_R_FLYER, 1, ITEM_PACCI_CANE },
};

// Level 6 - ELITES, per the user: "a tier beyond tier 5 called Elites that
// includes Darknuts, all mini bosses, and 3x ball-and-chain enemies at one
// time". Everything here is armored, high-health, or both, and everything
// here is rationed by sQuickStartLiveCaps rather than by rarity alone -
// the caps are what stop this tier from becoming the Darknut pile the
// whole rework exists to prevent.
//
// This doubles as the miniboss pool the ? room content draws from
// (QUICKSTART_MINIBOSS_POOL_SIZE), which is what makes "all minibosses are
// Elites" true by construction instead of by two lists agreeing.
//
// Madderpillar earns its place on health (32) but is the priciest entry in
// entity terms: probed, one placement is about seven live entities because
// it is a segmented chain, so its live cap is 2.
static const QuickStartEnemyPick sQuickStartElites[] = {
    { DARK_NUT, 0, QS_R_HEAVY | QS_R_SLOW, 2, 0 },
    { DARK_NUT, 1, QS_R_HEAVY | QS_R_SLOW, 2, 0 },
    { DARK_NUT, 2 /* blue, 20hp */, QS_R_HEAVY | QS_R_SLOW, 2, 0 },
    { DARK_NUT, 3 /* red, 26hp */, QS_R_HEAVY | QS_R_SLOW, 2, 0 },
    { BALL_CHAIN_SOLIDER, 0, QS_R_HEAVY, 1, 0 },
    { ENEMY_64, 0, QS_R_HEAVY | QS_R_SLOW, 4, 0 },
    { MADDERPILLAR, 0, QS_R_HEAVY, 5, 0 },
};

#define QUICKSTART_ENEMY_LEVELS 6

static const QuickStartEnemyPick* const sQuickStartEnemyLevels[QUICKSTART_ENEMY_LEVELS] = {
    sQuickStartLevel1, sQuickStartLevel2, sQuickStartLevel3,
    sQuickStartLevel4, sQuickStartLevel5, sQuickStartElites,
};
static const s32 sQuickStartEnemyLevelCounts[QUICKSTART_ENEMY_LEVELS] = {
    ARRAY_COUNT(sQuickStartLevel1), ARRAY_COUNT(sQuickStartLevel2), ARRAY_COUNT(sQuickStartLevel3),
    ARRAY_COUNT(sQuickStartLevel4), ARRAY_COUNT(sQuickStartLevel5), ARRAY_COUNT(sQuickStartElites),
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
    u8 levelWeights[QUICKSTART_ENEMY_LEVELS];
    u8 density;
} QuickStartDifficultyTier;

#define QUICKSTART_MIN_DENSITY 5

// Retuned per the user's brief on difficulty pacing: "Levels 1, 2, and 3
// should scale in difficulty noticeably but fairly. Once we have set a
// baseline difficulty at 3, we should then seek to explore the variety of
// enemy combinations more so than just pure difficulty."
//
// So steps 0-3 are the POWER ramp: all level-1 chaff, then a 1/2 blend,
// then level 2 with a taste of 3, with the density climbing alongside. A
// player meets no elite at all before step 4.
//
// Steps 4-12 are the VARIETY ramp. The weights deliberately STOP marching
// toward level 5 and settle into a level-2/3/4 band that barely moves;
// what actually changes with difficulty above the baseline is the
// composition (sQuickStartArchetypes below), the density, and a slowly
// widening elite allowance (sQuickStartLiveCaps). Level 5 tops out at 7%
// weight rather than the old 50%.
//
// The old curve is why high difficulty read as "Darknuts again": at step
// 12 it drew level 5 half the time, and two of that level's five entries
// are Darknut forms, so 61% of waves loaded a Darknut kind and the
// uniform-thirds fill then made about five of them. Weight alone was not
// the whole fix - the live caps and the composition builder are the rest -
// but a top tier that dominates the draw made everything else moot.
// Six columns now: levels 1-5 plus the Elites. The Elite weight is
// deliberately tiny and late - it is a spice, and the live caps mean even
// a lucky roll cannot field more than three of them.
static const QuickStartDifficultyTier sQuickStartDifficultyTiers[QUICKSTART_MAX_DIFFICULTY + 1] = {
    /*  0 */ { { 100, 0, 0, 0, 0, 0 }, 25 },
    /*  1 */ { { 75, 25, 0, 0, 0, 0 }, 22 },
    /*  2 */ { { 50, 45, 5, 0, 0, 0 }, 17 },
    /*  3 */ { { 30, 50, 20, 0, 0, 0 }, 13 }, // baseline established here
    /*  4 */ { { 25, 45, 27, 3, 0, 0 }, 12 },
    /*  5 */ { { 22, 43, 30, 5, 0, 0 }, 11 },
    /*  6 */ { { 20, 40, 32, 7, 1, 0 }, 10 },
    /*  7 */ { { 18, 38, 32, 9, 2, 1 }, 10 },
    /*  8 */ { { 16, 35, 33, 11, 3, 2 }, 9 },
    /*  9 */ { { 14, 33, 33, 13, 4, 3 }, 8 },
    /* 10 */ { { 12, 31, 33, 15, 5, 4 }, 7 },
    /* 11 */ { { 10, 29, 33, 17, 6, 5 }, 6 },
    /* 12 */ { { 10, 27, 32, 18, 7, 6 }, 6 },
};

static const QuickStartDifficultyTier* QuickStartGetDifficultyTier(u8 difficulty) {
    if (difficulty > QUICKSTART_MAX_DIFFICULTY) {
        difficulty = QUICKSTART_MAX_DIFFICULTY;
    }
    return &sQuickStartDifficultyTiers[difficulty];
}

// Roll one of the five roster levels using this tier's weights (a plain
// weighted die over whichever levels have nonzero weight).
static s32 QuickStartRollEnemyLevel(const QuickStartDifficultyTier* tier) {
    s32 roll = (s32)Random() % 100;
    s32 cumulative = 0;
    s32 level;
    for (level = 0; level < QUICKSTART_ENEMY_LEVELS; level++) {
        cumulative += tier->levelWeights[level];
        if (roll < cumulative) {
            return level;
        }
    }
    // Only reachable if a tier's weights don't sum to 100 - fall back to
    // the lowest level that's actually available this tier.
    for (level = 0; level < QUICKSTART_ENEMY_LEVELS && tier->levelWeights[level] == 0; level++) {
    }
    return (level >= QUICKSTART_ENEMY_LEVELS) ? 0 : level;
}

// Draw a roster entry for a ROLE (a QS_R_* bit), at this difficulty. The
// level is rolled from the tier weights exactly as an untyped draw would,
// so a role never smuggles in power the tier has not unlocked; within the
// level, only entries carrying the role are eligible. Reservoir sampling
// over the matching entries keeps it one pass and no scratch array.
//
// Roles are a preference, not a guarantee: a level that has no entry with
// the asked-for role (level 1 has no QS_R_HEAVY at all, deliberately)
// falls back to a plain uniform draw from that level, which is exactly the
// old behaviour. An archetype therefore degrades into an ordinary mixed
// wave rather than failing to fill.
// `budget` is the sheet allowance still unspent, and entries dearer than
// it are never returned: a slot that cannot be afforded should come back
// with a CHEAPER kind, not with nothing. That distinction is what makes
// the five-slot menagerie actually field five kinds - measured, drawing
// blind and skipping the unaffordable ones left waves averaging two kinds,
// because level 1's roster averages 2.8 slots and five blind draws want
// ~14 against a budget of 12.
//
// Returns NULL only when nothing in the rolled level is affordable at all,
// which the caller treats as "this slot sits out".
static bool32 QuickStartKindAlreadyCast(const QuickStartEnemyPick* pick, const u8* takenIds, const u8* takenForms,
                                        s32 takenCount) {
    s32 i;
    for (i = 0; i < takenCount; i++) {
        if (takenIds[i] == pick->id && takenForms[i] == pick->form) {
            return TRUE;
        }
    }
    return FALSE;
}

// May this entry be drawn at all right now? A weapon-gated enemy (see the
// `requires` note on QuickStartEnemyPick) waits until the player is
// carrying the thing that kills it - otherwise it would sit in a room the
// wave-clear objective needs emptied, forever.
static bool32 QuickStartEnemyEligible(const QuickStartEnemyPick* pick) {
    if (pick->requires == 0) {
        return TRUE;
    }
    return GetInventoryValue(pick->requires) != 0;
}

static const QuickStartEnemyPick* QuickStartDrawRole(u8 difficulty, u8 role, s32 budget, const u8* takenIds,
                                                    const u8* takenForms, s32 takenCount, u8 forceLevel) {
    const QuickStartDifficultyTier* tier = QuickStartGetDifficultyTier(difficulty);
    s32 level = (forceLevel != 0) ? (s32)(forceLevel - 1) : QuickStartRollEnemyLevel(tier);
    s32 count = sQuickStartEnemyLevelCounts[level];
    const QuickStartEnemyPick* level0 = sQuickStartEnemyLevels[level];
    const QuickStartEnemyPick* chosen = NULL;
    s32 seen = 0;
    s32 i;
    // First choice: affordable, unused, and carries the role.
    if (role != 0) {
        for (i = 0; i < count; i++) {
            if ((level0[i].roles & role) && level0[i].cost <= budget && QuickStartEnemyEligible(&level0[i]) &&
                !QuickStartKindAlreadyCast(&level0[i], takenIds, takenForms, takenCount)) {
                seen++;
                if ((s32)Random() % seen == 0) {
                    chosen = &level0[i];
                }
            }
        }
        if (chosen != NULL) {
            return chosen;
        }
    }
    // Second choice: affordable and unused, any role. A shape degrades
    // into an ordinary mixed wave rather than failing to fill.
    //
    // Excluding what the wave already holds is what makes a five-slot
    // menagerie field five DIFFERENT things: measured without it, waves
    // averaged two kinds even with five slots, because the role bits
    // overlap heavily in the small early rosters (a Keese answers chaff,
    // fast AND flyer) and every collision folded a slot away.
    seen = 0;
    for (i = 0; i < count; i++) {
        if (level0[i].cost <= budget && QuickStartEnemyEligible(&level0[i]) &&
            !QuickStartKindAlreadyCast(&level0[i], takenIds, takenForms, takenCount)) {
            seen++;
            if ((s32)Random() % seen == 0) {
                chosen = &level0[i];
            }
        }
    }
    return chosen;
}

// Rolls one fresh enemy (id + form) for the given difficulty, ignoring
// roles. Still used by the single-kind spawners (the ? room wave content,
// the quest packs); the region wave builder goes through the composition
// path instead.
static void QuickStartPickEnemy(u8 difficulty, u8* outId, u8* outForm) {
    const QuickStartDifficultyTier* tier = QuickStartGetDifficultyTier(difficulty);
    s32 level = QuickStartRollEnemyLevel(tier);
    s32 levelCount;
    const QuickStartEnemyPick* pick;
    levelCount = sQuickStartEnemyLevelCounts[level];
    pick = &sQuickStartEnemyLevels[level][(s32)Random() % levelCount];
    *outId = pick->id;
    *outForm = pick->form;
}

// --- Live caps: how many of one family may exist at once -----------------
//
// Generalized from the Acro Bandit rule, which proved the mechanism. A
// wave that wants a capped kind it already has its fill of is given a kind
// it has already paid the sheet for instead, so the wave keeps its density
// and only its COMPOSITION changes.
//
// The cap is interpolated between base and top across the difficulty
// range: cap = base + ((top - base) * difficulty) / QUICKSTART_MAX_
// DIFFICULTY, integer division. For the Darknuts that means a flat 2 all
// the way up and 3 only at difficulty 12 exactly - the user's call, "at
// the absolute highest difficulty we should spawn in maximum 3 elites".
//
// Wizzrobes are deliberately NOT rationed like the melee elites, also per
// the user: they are fun in numbers because they fight by vanishing, so
// any one of them is absent half the time. Their limit is the entity
// budget (each carries a projectile child of its own), not taste.
typedef struct {
    u8 id;
    u8 baseCap;
    u8 topCap;
} QuickStartLiveCap;

static const QuickStartLiveCap sQuickStartLiveCaps[] = {
    // Armored chasers. The whole point of this table: five of these in one
    // room was the user's report, and it was the modal outcome at the top
    // of the old curve, not bad luck.
    { DARK_NUT, 2, 3 },
    // Three at once is the user's own spec for the Elite tier ("3x
    // ball-and-chain enemies at one time"), so this is a flat 3 rather
    // than a ramp - the swing is area denial, but three of them reads as
    // a deliberate set piece rather than a pile.
    { BALL_CHAIN_SOLIDER, 3, 3 },
    // The other two Elites. Enemy 64 is a 36hp bruiser.
    { ENEMY_64, 2, 3 },
    // Madderpillar is a SEGMENTED chain: one placement is about seven
    // live entities sharing this id (measured), so this cap of 1 reads as
    // "one chain in the room", not "one body". Counting segments is
    // exactly what we want here - the entity table is the scarce thing,
    // and a second chain would be a seventh of it. Same shape of rule as
    // the Acro Bandit gang, where one placement is six.
    { MADDERPILLAR, 1, 1 },
    // The only enemy class measured to cost real frame time (F9): each
    // placement bursts into six. Unchanged.
    { ACRO_BANDIT, 2, 2 },
    // Item theft compounds unfairly - losing a shield twice is a story,
    // five times is the run.
    { RUPEE_LIKE, 3, 3 },
    { LIKE_LIKE, 3, 3 },
    { TAKKURI, 3, 3 },
    // Wizzrobes: generous by design (see above). One family across all
    // three elements, so a wave cannot field six of each.
    { WIZZROBE_FIRE, 6, 8 },
};

// Wizzrobes are three separate ids but one family for capping purposes;
// everything else caps by its own id, which already covers colour forms
// (all four Darknuts share id DARK_NUT).
static bool32 QuickStartEnemyIsWizzrobe(u8 id);

static u8 QuickStartEnemyFamily(u8 id) {
    if (QuickStartEnemyIsWizzrobe(id)) {
        return WIZZROBE_FIRE;
    }
    return id;
}

// 0 = uncapped.
static s32 QuickStartLiveCapFor(u8 id, u8 difficulty) {
    u8 family = QuickStartEnemyFamily(id);
    s32 i;
    if (difficulty > QUICKSTART_MAX_DIFFICULTY) {
        difficulty = QUICKSTART_MAX_DIFFICULTY;
    }
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartLiveCaps); i++) {
        if (sQuickStartLiveCaps[i].id == family) {
            s32 base = sQuickStartLiveCaps[i].baseCap;
            s32 top = sQuickStartLiveCaps[i].topCap;
            return base + (((top - base) * (s32)difficulty) / QUICKSTART_MAX_DIFFICULTY);
        }
    }
    return 0;
}

static bool32 QuickStartKindAtLiveCap(u8 id, u8 difficulty) {
    s32 cap = QuickStartLiveCapFor(id, difficulty);
    u8 family;
    s32 i, count = 0;
    if (cap == 0) {
        return FALSE;
    }
    family = QuickStartEnemyFamily(id);
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY && QuickStartEnemyFamily(ent->id) == family) {
            count++;
            if (count >= cap) {
                return TRUE;
            }
        }
    }
    return FALSE;
}

// --- Composition archetypes ----------------------------------------------
//
// A wave used to be three kinds in uniform thirds, which is a pile rather
// than a composition: nothing in the builder knew a Darknut was different
// in kind from a Keese, so both got a third of the room. An archetype is a
// SHAPE - which roles are present and in what proportion - and its cast is
// drawn fresh every time. Two waves of the same archetype at the same
// difficulty share a structure and share no faces, which is the variety
// the brief asks for without leaning on raw power.
//
// `roles` names what each slot wants; `shares` is that slot's relative
// portion of the wave (they need not sum to anything in particular - the
// builder normalizes). `countPercent` scales the whole wave: a swarm is
// bigger than usual, a duel is much smaller. `minDiff` keeps the
// elite-bearing shapes out of the early game, where the brief wants a
// clean power ramp and no elites at all.
#define QUICKSTART_ARCHETYPE_SLOTS 5

// forceLevel pins the roster level a shape draws from, as level+1, or 0 to
// let the tier weights roll it as usual. Only the Elite trio uses it: an
// encounter that is ABOUT its elites cannot be left to the tier weights,
// which give the Elite level a few percent at best.
typedef struct {
    u8 minDiff;
    u8 weight;
    u8 slotCount;
    u8 countPercent;
    u8 forceLevel;
    u8 roles[QUICKSTART_ARCHETYPE_SLOTS];
    u8 shares[QUICKSTART_ARCHETYPE_SLOTS];
} QuickStartArchetype;

static const QuickStartArchetype sQuickStartArchetypes[] = {
    // The plain mixed wave: no shape at all, three untyped draws. Kept as
    // the single most likely outcome so the game still reads as the game -
    // archetypes are seasoning, not a replacement.
    { 0, 30, 3, 100, 0, {0, 0, 0, 0, 0 }, { 34, 33, 33, 0, 0 } },
    // SWARM: one cheap kind, more of it than usual. Sixteen Keese costs
    // one sheet slot - the cheapest spectacle in the game.
    { 0, 12, 1, 150, 0, {QS_R_CHAFF, 0, 0, 0, 0 }, { 100, 0, 0, 0, 0 } },
    // MENAGERIE: the user's "5 types of enemies coming at you all at
    // once". The roles are picked to lean cheap (chaff, fast, flyer,
    // ambush and ranged are where the 1-2 slot kinds live), because five
    // kinds only fit the sheet budget if they are cheap ones - which is
    // exactly the trade the budget exists to expose.
    { 2, 14, 5, 100, 0, {QS_R_CHAFF, QS_R_FAST, QS_R_FLYER, QS_R_AMBUSH, QS_R_RANGED },
      { 20, 20, 20, 20, 20 } },
    // PINCER: a fast flyer and a slow ground kind arrive as two separate
    // problems out of one spawn - a 12x speed gap does that for free.
    { 2, 10, 2, 100, 0, {QS_R_FLYER | QS_R_FAST, QS_R_SLOW, 0, 0, 0 }, { 60, 40, 0, 0, 0 } },
    // AMBUSH: burrowers and hiders, with something fast to herd you onto
    // them.
    { 3, 10, 2, 100, 0, {QS_R_AMBUSH, QS_R_FAST, 0, 0, 0 }, { 65, 35, 0, 0, 0 } },
    // CROSSFIRE: two ranged kinds plus a chaser, so standing still is
    // punished and closing is contested.
    { 4, 10, 3, 90, 0, {QS_R_RANGED, QS_R_RANGED, QS_R_FAST, 0, 0 }, { 35, 35, 30, 0, 0 } },
    // ELITE GUARD: one heavy in an escort of chaff - the user's own
    // example, "a single strong enemy surrounded by smaller enemies".
    // The heavy's share is small and the live cap trims it further.
    { 4, 8, 3, 100, 0, {QS_R_HEAVY, QS_R_CHAFF, QS_R_CHAFF, 0, 0 }, { 15, 45, 40, 0, 0 } },
    // THIEVES: fast and after your things rather than your hearts. A wave
    // whose threat is economic.
    { 5, 6, 2, 100, 0, {QS_R_THIEF, QS_R_FAST, 0, 0, 0 }, { 50, 50, 0, 0, 0 } },
    // DUEL: two heavies and nothing else, at a third of the usual count.
    // Variety includes quiet: a generator that is always maximally busy
    // stops reading as varied.
    { 6, 6, 2, 35, 0, {QS_R_HEAVY, QS_R_HEAVY, 0, 0, 0 }, { 50, 50, 0, 0, 0 } },
    // ARTILLERY: shooters behind a wall of slow bodies, so the player has
    // to choose an order to kill things in.
    { 6, 8, 2, 100, 0, {QS_R_RANGED, QS_R_SLOW, 0, 0, 0 }, { 40, 60, 0, 0, 0 } },
    // ELITE TRIO: one Elite kind, three of it, and nothing else. This is
    // the user's "3x ball-and-chain enemies at one time" as a designed
    // encounter rather than a lucky roll - forceLevel pins the draw to the
    // Elite roster, which the tier weights alone would reach only a few
    // percent of the time (measured: Ball and Chain appeared in 0 of 60
    // sampled waves before this row existed).
    //
    // The head count asks for a quarter of a normal wave - about 4 at high
    // difficulty - and the live caps trim it to 3 Ball and Chain, 3
    // Darknuts at difficulty 12 (2 below it), or 2 Madderpillars. So the
    // shape says "a few of something serious" and the caps decide exactly
    // how few, which is the same division of labour every other shape uses.
    { 8, 7, 1, 25, QUICKSTART_ENEMY_LEVELS, {QS_R_HEAVY, 0, 0, 0, 0 }, { 100, 0, 0, 0, 0 } },
};

static const QuickStartArchetype* QuickStartRollArchetype(u8 difficulty) {
    s32 total = 0;
    s32 i, roll, cumulative;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartArchetypes); i++) {
        if (sQuickStartArchetypes[i].minDiff <= difficulty) {
            total += sQuickStartArchetypes[i].weight;
        }
    }
    if (total <= 0) {
        return &sQuickStartArchetypes[0];
    }
    roll = (s32)Random() % total;
    cumulative = 0;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartArchetypes); i++) {
        if (sQuickStartArchetypes[i].minDiff > difficulty) {
            continue;
        }
        cumulative += sQuickStartArchetypes[i].weight;
        if (roll < cumulative) {
            return &sQuickStartArchetypes[i];
        }
    }
    return &sQuickStartArchetypes[0];
}

// GBA OBJ VRAM is carved into 44 gfx slots (MAX_GFX_SLOTS, vram.h), 4
// permanently reserved for palettes (ResetPalettes) - leaving 40 for every
// sprite on screen at once (player, items, effects, room objects, enemies
// alike). A single enemy kind costs 1-8 of them (Bow/Spear Moblin and
// Puffstool are 8 each). Rolling a fresh kind per enemy, as this used to
// (restored earlier this session per the user's own request), asks for
// ~20 different kinds in one 50-enemy Lon Lon Ranch wave, which cannot
// fit: LoadFixedGFX/LoadSwapGFX then fail, and (with the CleanUpGFXSlots
// fix in vram.c) EnemyUpdate correctly deletes whichever enemy couldn't be
// fitted rather than corrupting an unrelated entity - but that still means
// the room ends up with noticeably fewer enemies than the density curve
// asks for. Capping kinds keeps the density curve intact instead: each
// kind is paid for once, so the remaining budget goes to more enemies
// rather than more sprite sheets. Cross-room/round variety (the actual
// point of the original brief) is unchanged - kinds are still rolled
// fresh per room and per visit; only the within-one-room variety is
// bounded. Measured in the emulator: without this cap, a 50-enemy Lon Lon
// Ranch wave at difficulty 8 held only 31 live enemies (GFX slots ran out
// partway through); with it, 33 - and at difficulty 12, 29 vs 36.
// --- The GFX-slot budget -------------------------------------------------
//
// MAX_GFX_SLOTS is 44 for the whole game, and it - not MAX_ENTITIES - is
// what the overworld actually runs out of. Measured with
// tools/quickstart/measure_budget.py on the build before this change:
// South Hyrule Field and North Hyrule Field both reach 44/44 by difficulty
// 8-12, i.e. ZERO free slots, and North Hyrule Field at difficulty 12
// spawns FEWER enemies (27) than at difficulty 4 (50) because allocation
// starts failing partway through the wave.
//
// The kind cap below bounds how many sprite SHEETS a wave asks for, which
// helped, but it is not sufficient on its own: a slot dump at difficulty 12
// showed 4 palette slots, 6 shared sheets, and ELEVEN per-instance
// allocations (refCount 1 each) that scale with the enemies themselves
// rather than with the number of kinds. So the sheet count alone cannot
// guarantee headroom - only looking at the live table can.
//
// Hence a runtime reserve, per the user's own call: never occupy the last
// slots, because a full table both drops sprites and costs frame time.
//
// Two mechanisms, because one is not enough. The spawn-time checks below
// are necessary but NOT sufficient: CreateEnemy only allocates the entity,
// and each enemy loads its own sheet later from its own Init, so during a
// burst spawn the table still reads empty and every check passes. Measured
// - adding the spawn-time guard alone changed the curve by exactly nothing.
// QuickStartEnforceGfxReserve below is what actually holds the invariant,
// by checking every frame after the cost has been paid.
#define QUICKSTART_GFX_RESERVE 4
#define QUICKSTART_GFX_HARD_FLOOR 2

static s32 QuickStartFreeGfxSlots(void) {
    s32 i, freeSlots = 0;
    for (i = 0; i < MAX_GFX_SLOTS; i++) {
        if (gGFXSlots.slots[i].status == GFX_SLOT_FREE) {
            freeSlots++;
        }
    }
    return freeSlots;
}

// The strict counter above undercounts what a spawn can actually claim:
// GFX_SLOT_UNLOADED/GFX_SLOT_STATUS2 slots hold sheets nothing references
// any more, and the loader evicts them on demand. For "can this big spawn
// fit at all" questions that is the honest number (measured: a full boss
// family landed fine in North Hyrule Field with only ~8 strictly-free
// slots, because cleared-wave sheets were evictable).
static s32 QuickStartReclaimableGfxSlots(void) {
    s32 i, freeSlots = 0;
    for (i = 0; i < MAX_GFX_SLOTS; i++) {
        if (gGFXSlots.slots[i].status <= GFX_SLOT_STATUS2) {
            freeSlots++;
        }
    }
    return freeSlots;
}

// Is there room to load a sprite sheet we have not already paid for?
static bool32 QuickStartGfxBudgetForNewKind(void) {
    return QuickStartFreeGfxSlots() > QUICKSTART_GFX_RESERVE;
}

// Is there room to put ANY further entity on screen?
static bool32 QuickStartGfxBudgetForSpawn(void) {
    return QuickStartFreeGfxSlots() > QUICKSTART_GFX_HARD_FLOOR;
}

// Spawn-count ceiling as a function of difficulty, in service of the GFX
// reserve (see QUICKSTART_GFX_RESERVE). Tuned by measurement, not theory:
// the numbers below are the first set that kept every region above the
// hard floor on every frame at difficulties 0/4/8/12, while leaving the
// low-difficulty counts (where sprites are cheap) untouched.
#define QUICKSTART_GFX_SPAWN_CAP_BASE 64
// Raised from 4 to 5 when the Kinstone fusers arrived. Every region now
// carries a permanent extra sprite sheet (the fusers all share one, but one
// is still one), and South Hyrule Field - which was already the tightest
// region at difficulty 8 - went one slot under the hard floor because of it.
// Steepening the slope pays for the fusers out of the high-difficulty wave
// count, where sprites are most expensive, and leaves the low-difficulty
// counts alone.
//
// Raised again, 5 to 6, when the overworld expansion's regions arrived:
// Western Wood North carries the ring's heaviest fixed sheet load (five
// fusers plus its own vanilla object clutter) and measured 1 free slot at
// difficulty 8 with the slope at 5 - the wave's high-tier kinds pass the
// stale-count spawn gates during the burst and their projectile sheets
// load ungated once they start shooting. Same lever, same reasoning as the
// first bump: pay for the new fixed load out of the difficulty-8+ wave
// count (24 -> 16 enemies at difficulty 8), where each enemy costs the
// most sprite table, and leave difficulty 0-4 untouched.
#define QUICKSTART_GFX_SPAWN_CAP_SLOPE 6
#define QUICKSTART_GFX_SPAWN_CAP_MIN 16

// How many distinct kinds one wave may hold, and what their sprite sheets
// may cost between them. The COST is the real limit; the count is just the
// array bound the archetypes need (no shape asks for more than 4, and the
// duplicate-fold path can leave slots unused).
//
// This replaces a flat cap of 3 kinds, which was a proxy for sheet cost
// and a bad one, because kinds range 1..8 slots: the old rule permitted
// Puffstool + Bow Moblin + Ghini (21 slots for three kinds) while
// forbidding six 1-slot kinds (6 slots for six). Spending the slots
// directly makes the expensive kinds self-limiting and lets a wave of
// cheap kinds be genuinely varied - which is the whole point of the
// composition work.
//
// 12 is chosen against the measured budget: the tightest rooms at
// difficulty 12 (Lon Lon 5 free, Trilby 6, EH-North/WW-North 7 - see
// docs/QUICKSTART_BUDGET.md) still have to fit their fixed load, and the
// per-frame reserve enforcement plus QuickStartGfxBudgetForNewKind remain
// in force underneath this as the runtime backstop.
#define QUICKSTART_MAX_ENEMY_KINDS 6
#define QUICKSTART_WAVE_SHEET_BUDGET 12

// Shared by every QUICKSTART enemy spawner: picks `count` distinct spots
// out of this room's own pre-verified-walkable offset pool (a partial
// Fisher-Yates shuffle, so which spots get used - not just which enemies -
// varies across boots too) and rolls a fresh enemy for each from
// QuickStartPickEnemy. `count` itself comes from the room's size in 32x32
// squares divided by this difficulty's density, clamped to at least 1, and
// to at most whichever is smaller of the offset pool's own size or
// maxEnemies (the room's hard entity-budget ceiling - see the per-room
// constants above each call site). Difficulty is an explicit parameter
// (rather than always reading QuickStartGetDifficulty() itself) so the
// region-chain's endless-wave loop (QuickStartSpawnRegionWave) can escalate
// past the run's own persistent difficulty counter as waves stack up,
// while every other call site keeps using the plain wrapper below.
// Parts of the overworld that are walled off behind an item. The wave-clear
// objective is the reason these matter: an enemy that spawns somewhere the
// player cannot reach makes the wave, and so the run, unwinnable. That was
// happening in practice.
//
// Each row is a box in room-local coordinates, hand-walked in game rather
// than derived from collision data - the emulator walk-simulation used
// elsewhere in this file has been wrong often enough in this codebase that
// walked ground truth is the more trustworthy source.
//
// requiredItem is what unlocks the box. Hold it and the zone behaves like
// any other ground: events may happen there. Lack it and nothing is placed
// inside. requiredItem of 0 means "never", for pockets that cannot be
// reached at all from this region however well equipped.
//
// This is deliberately a general position filter rather than an enemy-only
// one, so the same table can gate whatever else ends up wanting a spot -
// Kinstone fusions, item drops, side quests.
typedef struct {
    u8 area;
    u8 room;
    s16 minX;
    s16 maxX;
    s16 minY;
    s16 maxY;
    u16 requiredItem;
} QuickStartGatedZone;

static const QuickStartGatedZone sQuickStartGatedZones[] = {
    // South Hyrule Field's northeast shelf, reachable only by Cane of
    // Pacci. Box walked by the user: (898,189) to (971,399).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, 898, 971, 189, 399, ITEM_PACCI_CANE },
    // Trilby Highlands' northwest ledge, box walked by the user:
    // (220,55) to (314,119). Reached only through a dirt-filled cave, so
    // the gate is the Mole Mitts - that is an inference from "dirt-filled",
    // not something confirmed by finding the cave itself, and it is a
    // one-word change here if it turns out to be another item.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, 220, 314, 55, 119, ITEM_MOLE_MITTS },

    // --- North Hyrule Field -------------------------------------------
    // The whole western section. Reaching it needs bombs AND a trip through
    // the 2-door "? room" that joins the two ladders, so bombs are the
    // gating item - without them the route does not open at all.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 0, 172, 0, 1023, ITEM_BOMBS },
    // The northeast pocket, above (884,156) and right of (876,103). Bombs
    // again.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 876, 1023, 0, 156, ITEM_BOMBS },

    // --- Lon Lon Ranch ------------------------------------------------
    // Three Cane of Pacci ledges, walked by the user. The first two were
    // given as lines with everything above them out of reach, so they run
    // from the top of the room down to the line.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 38, 138, 0, 127, ITEM_PACCI_CANE },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 228, 475, 0, 167, ITEM_PACCI_CANE },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 267, 660, 222, 396, ITEM_PACCI_CANE },
    // The southeast corner. Gated on Roc's Cape alone, deliberately, even
    // though the Zora's Flippers also get the player across: the user
    // reports that crossing is ONE WAY - swim over and you cannot swim
    // back. Treating flippers as sufficient would put wave enemies somewhere
    // a flippers-only player can reach but not leave, turning a stranded
    // enemy into a stranded player.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 596, 683, 591, 782, ITEM_ROCS_CAPE },
};

// Whether something may be placed at this room-local spot in the current
// room. TRUE for anywhere not inside a gated box, and for a gated box whose
// item the player is carrying.
static bool32 QuickStartPositionAllowed(s16 localX, s16 localY) {
    s32 i;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartGatedZones); i++) {
        const QuickStartGatedZone* zone = &sQuickStartGatedZones[i];
        if (gRoomControls.area != zone->area || gRoomControls.room != zone->room) {
            continue;
        }
        if (localX < zone->minX || localX > zone->maxX || localY < zone->minY || localY > zone->maxY) {
            continue;
        }
        if (zone->requiredItem == 0) {
            return FALSE;
        }
        return GetInventoryValue(zone->requiredItem) != 0;
    }
    return TRUE;
}

// F9 (docs/QUICKSTART_ROADMAP.md): ACRO_BANDIT is not one enemy, it is a
// GANG. The placed leader bursts into five more of itself the moment its
// pop-up animation finishes (acroBandits.c, Type0Action5), so every
// placement is eventually SIX live entities of one of the heavier per-frame
// AIs - which is why the user sees the frame rate fall over at 3-4 on
// screen. The cap: a new placement is allowed only while fewer than two
// ACRO_BANDITs are live. That passes exactly two fresh leaders (0 live,
// then 1) and blocks everything after (one burst gang alone reads 6 live).
// Only OUR spawners consult this - the gang's own follower spawns are
// vanilla behaviour and stay untouched, since capping a gang mid-burst
// would leave a half-formed formation.
// The cap itself now lives in sQuickStartLiveCaps with the rest of the
// rationed kinds; this stays as the name the single-kind spawners call, so
// there is one implementation of "how many of these may be alive" rather
// than two that can drift apart.
static bool32 QuickStartAcroBanditCapReached(void) {
    return QuickStartKindAtLiveCap(ACRO_BANDIT, QuickStartGetDifficulty());
}

static void QuickStartSpawnEnemyGroupAtDifficulty(const s16 (*offsets)[2], s32 offsetCount, s32 roomSquares,
                                                   s32 maxEnemies, u8 difficulty) {
    s32 indices[72];
    s32 i, j, r, tmp, count, density, cap, allowed, gfxCap;
    Entity* enemy;
    u8 id, form;
    u8 kindIds[QUICKSTART_MAX_ENEMY_KINDS];
    u8 kindForms[QUICKSTART_MAX_ENEMY_KINDS];
    s32 kindQuota[QUICKSTART_MAX_ENEMY_KINDS];
    s32 kindCount = 0;
    s32 sheetBudget = QUICKSTART_WAVE_SHEET_BUDGET;
    const QuickStartArchetype* shape;
    s32 shareTotal = 0;

    if (offsetCount > 72) {
        offsetCount = 72;
    }
    // Drop every spot the player can't currently get to before anything is
    // shuffled or counted, so a gated zone costs the wave nothing: the same
    // number of enemies still spawn, just all of them somewhere reachable.
    allowed = 0;
    for (i = 0; i < offsetCount; i++) {
        if (QuickStartPositionAllowed(offsets[i][0], offsets[i][1])) {
            indices[allowed++] = i;
        }
    }
    offsetCount = allowed;
    if (offsetCount == 0) {
        return;
    }
    for (i = 0; i < offsetCount - 1; i++) {
        r = (s32)Random() % (offsetCount - i);
        tmp = indices[i];
        indices[i] = indices[i + r];
        indices[i + r] = tmp;
    }

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
    // A second cap, this one paid in GFX rather than in floor space. The
    // level-4/5 roster costs far more sprite table per enemy than the
    // level-1/2 one (a slot dump at difficulty 12 showed eleven
    // per-instance allocations that simply do not exist at difficulty 0),
    // so the SAME enemy count gets more expensive as difficulty climbs.
    //
    // This has to be a spawn-time cap rather than left to
    // QuickStartEnforceGfxReserve, because that runs after the fact: for
    // the frames between a burst spawn and the reserve's next pass the
    // table really is full, and anything trying to load a sheet in that
    // window - a quest sprite, a reward, a fuser - silently gets nothing.
    // The invariant checker's gfx tier samples every frame and catches
    // exactly that transient.
    gfxCap = QUICKSTART_GFX_SPAWN_CAP_BASE - difficulty * QUICKSTART_GFX_SPAWN_CAP_SLOPE;
    if (gfxCap < QUICKSTART_GFX_SPAWN_CAP_MIN) {
        gfxCap = QUICKSTART_GFX_SPAWN_CAP_MIN;
    }
    if (count > gfxCap) {
        count = gfxCap;
    }

    // --- Cast the composition ------------------------------------------
    // The shape is rolled once per wave; each of its role slots is cast
    // from the tier's own roster, and a slot that cannot be afforded (or
    // that the shape has no room for) simply does not join - the wave then
    // spreads over the kinds it did get, so density never depends on the
    // draw succeeding. countPercent scales the whole wave AFTER every
    // other clamp, so a swarm cannot climb back over the GFX ceiling.
    shape = QuickStartRollArchetype(difficulty);
    for (i = 0; i < shape->slotCount && kindCount < QUICKSTART_MAX_ENEMY_KINDS; i++) {
        const QuickStartEnemyPick* pick =
            QuickStartDrawRole(difficulty, shape->roles[i], sheetBudget, kindIds, kindForms, kindCount,
                               shape->forceLevel);
        if (pick == NULL) {
            // Nothing affordable and unused left in the rolled level.
            // The slot sits out and its share goes unclaimed, so the wave
            // simply spreads over the kinds it did get.
            continue;
        }
        kindIds[kindCount] = pick->id;
        kindForms[kindCount] = pick->form;
        kindQuota[kindCount] = shape->shares[i];
        shareTotal += shape->shares[i];
        sheetBudget -= pick->cost;
        kindCount++;
    }
    if (kindCount == 0) {
        // Nothing affordable at all (a shape of expensive roles against a
        // spent budget). Fall back to one untyped draw so the room is
        // never silently empty.
        QuickStartPickEnemy(difficulty, &id, &form);
        kindIds[0] = id;
        kindForms[0] = form;
        kindQuota[0] = 1;
        kindCount = 1;
        shareTotal = 1;
    }
    if (shape->countPercent != 100) {
        count = (count * shape->countPercent) / 100;
        if (count < 1) {
            count = 1;
        }
        // Re-clamp, because a shape that scales UP (the swarm's 150%) can
        // otherwise push past the very limits the count was just fitted
        // to. Two of the three are correctness, not taste: `cap` is the
        // size of the shuffled index array, so overrunning it reads
        // uninitialized stack and places enemies at whatever offset that
        // garbage indexes; gfxCap is the sprite-table ceiling the burst
        // must not exceed.
        if (count > cap) {
            count = cap;
        }
        if (count > gfxCap) {
            count = gfxCap;
        }
    }
    // Turn relative shares into actual head counts. Rounding leftovers go
    // to the largest share, which is the one the shape is "about".
    {
        s32 assigned = 0;
        s32 biggest = 0;
        for (i = 0; i < kindCount; i++) {
            s32 want = (count * kindQuota[i]) / shareTotal;
            kindQuota[i] = want;
            assigned += want;
            if (want > kindQuota[biggest]) {
                biggest = i;
            }
        }
        kindQuota[biggest] += count - assigned;
    }

    for (i = 0; i < count; i++) {
        s32 chosen = -1;
        j = indices[i];
        // Stop entirely rather than spend the last slots (see
        // QUICKSTART_GFX_RESERVE): a full table drops sprites and costs
        // frame time.
        if (!QuickStartGfxBudgetForSpawn()) {
            break;
        }
        // Take from whichever kind still owes head count. Walking from a
        // random start keeps the placement order mixed - otherwise every
        // wave would spawn all of kind 0 on the first offsets and all of
        // kind 2 on the last, which reads as three separate groups rather
        // than one composition.
        r = (s32)Random() % kindCount;
        for (tmp = 0; tmp < kindCount; tmp++) {
            s32 k = (r + tmp) % kindCount;
            if (kindQuota[k] > 0) {
                chosen = k;
                break;
            }
        }
        if (chosen < 0) {
            break;
        }
        id = kindIds[chosen];
        form = kindForms[chosen];
        // A kind at its live cap (sQuickStartLiveCaps) is swapped for one
        // this wave has already paid the sheet for, so the wave keeps its
        // density and only its composition changes. If every loaded kind
        // is capped, the placement is skipped instead.
        //
        // The capped kind's own quota is deliberately NOT spent here: the
        // redirect must not cost the wave a body, or a shape that leads
        // with a heavy would thin the whole room out every time the cap
        // bites. Its quota simply keeps getting redirected.
        if (QuickStartKindAtLiveCap(id, difficulty)) {
            s32 alt = -1;
            for (tmp = 0; tmp < kindCount; tmp++) {
                s32 k = (r + tmp) % kindCount;
                if (kindIds[k] != id && !QuickStartKindAtLiveCap(kindIds[k], difficulty)) {
                    alt = k;
                    break;
                }
            }
            if (alt < 0) {
                continue;
            }
            chosen = alt;
            id = kindIds[chosen];
            form = kindForms[chosen];
        }
        kindQuota[chosen]--;
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

static void QuickStartSpawnEnemyGroup(const s16 (*offsets)[2], s32 offsetCount, s32 roomSquares, s32 maxEnemies) {
    QuickStartSpawnEnemyGroupAtDifficulty(offsets, offsetCount, roomSquares, maxEnemies, QuickStartGetDifficulty());
}

// QS_EVENT_WAVES (see QuickStartSetupWaveRoomContent) is new - a 3-wave
// combat room, single enemy type per wave, only ever assigned to a
// medium/large pool room (QuickStartRandomizeSlotsOnce) alongside
// QS_EVENT_MINIBOSS, per the user's own room-size split: chest/NPC
// content stays in the small pool, miniboss/waves (and puzzles, later) stay
// in the medium/large one.
// POT_LOTTERY/CHEST_LOTTERY/FAIRY added this session, alongside pot-lottery
// and chest-lottery puzzle rooms and free-heal fairy rooms - see
// QuickStartPickSmallKind/QuickStartPickLargeKind below for which pool
// draws which subset. Needed a 3rd kind bit (GF_SLOT_KIND_BIT2/
// GF_2DOOR_KIND_BIT2) since the original 2-bit field's 4 raw values were
// already fully spoken for once you count both pools sharing one field
// (small: CHEST/NPC, large: MINIBOSS/WAVES).
enum {
    QS_EVENT_ITEM_DROP,
    QS_EVENT_MINIBOSS,
    QS_EVENT_NPC,
    QS_EVENT_WAVES,
    QS_EVENT_POT_LOTTERY,
    QS_EVENT_CHEST_LOTTERY,
    QS_EVENT_FAIRY,
    // The switch-puzzle site (Phase D): a caged prize plus switches.
    // Value 7 fills the kind field's 3-bit range exactly, so the two
    // puzzles share it and a per-visit coin flip picks which one this
    // stay gets: the CLOSING GATE (#1 - one switch, opens the cage for a
    // shrinking timed window) or the DECOY SWITCHES (#2 - three identical
    // switches dealt prize/trap/dud blind; per the user, NO tell - a pure
    // gamble). Sword-only by design either way (switches answer any hit),
    // so it needs no unlock and no kit check.
    QS_EVENT_GATE,
};

// B1: which kinds this save has earned (see sQuickStartUnlockRules). Lives
// here, next to the enum, and is consulted as a FALLBACK inside the three
// pick functions below rather than by reweighting their draws - every
// caller (ladder, door, and 2-door randomizers all call these) inherits
// the gating automatically, and a locked draw degrades to the pool's
// bread-and-butter kind instead of rerolling (no termination concerns, no
// skew among the still-locked kinds to reason about).
static bool32 QuickStartKindUnlocked(u8 kind) {
    switch (kind) {
        case QS_EVENT_POT_LOTTERY:
            return QuickStartIsUnlocked(QUICKSTART_UNLOCK_KIND_POT_LOTTERY);
        case QS_EVENT_CHEST_LOTTERY:
            return QuickStartIsUnlocked(QUICKSTART_UNLOCK_KIND_CHEST_LOTTERY);
        case QS_EVENT_FAIRY:
            return QuickStartIsUnlocked(QUICKSTART_UNLOCK_KIND_FAIRY);
        default:
            return TRUE;
    }
}

// Small pool: puzzle/dialogue content, no combat needed - CHEST/NPC (the
// original two) plus the two new lottery puzzles.
static u8 QuickStartPickSmallKind(void) {
    u8 kind;
    switch ((s32)Random() % 4) {
        case 0:
            kind = QS_EVENT_ITEM_DROP;
            break;
        case 1:
            kind = QS_EVENT_NPC;
            break;
        case 2:
            kind = QS_EVENT_POT_LOTTERY;
            break;
        default:
            kind = QS_EVENT_CHEST_LOTTERY;
            break;
    }
    if (!QuickStartKindUnlocked(kind)) {
        kind = QS_EVENT_ITEM_DROP;
    }
    return kind;
}

// Large pool: combat-capable rooms - MINIBOSS/WAVES (the original two) plus
// FAIRY as an occasional pure-reward breather between the combat-heavy
// draws, since these rooms have the floor space for a couple of fairies to
// wander without clutter.
// Rooms with no restrictions at all - big, open, and free of anything the
// event has to work around, so every kind is fair game. Distinct from the
// large pool, which is combat-and-fairies only: a room being big is not a
// reason to stop it rolling a pot lottery.
static u8 QuickStartPickAnyKind(void) {
    u8 kind;
    switch ((s32)Random() % 8) {
        case 0:
            kind = QS_EVENT_ITEM_DROP;
            break;
        case 1:
            kind = QS_EVENT_MINIBOSS;
            break;
        case 2:
            kind = QS_EVENT_NPC;
            break;
        case 3:
            kind = QS_EVENT_WAVES;
            break;
        case 4:
            kind = QS_EVENT_POT_LOTTERY;
            break;
        case 5:
            kind = QS_EVENT_CHEST_LOTTERY;
            break;
        case 6:
            kind = QS_EVENT_GATE;
            break;
        default:
            kind = QS_EVENT_FAIRY;
            break;
    }
    if (!QuickStartKindUnlocked(kind)) {
        kind = QS_EVENT_ITEM_DROP;
    }
    return kind;
}

static u8 QuickStartPickLargeKind(void) {
    u8 kind;
    switch ((s32)Random() % 4) {
        case 0:
            kind = QS_EVENT_MINIBOSS;
            break;
        case 1:
            kind = QS_EVENT_WAVES;
            break;
        case 2:
            kind = QS_EVENT_GATE;
            break;
        default:
            kind = QS_EVENT_FAIRY;
            break;
    }
    if (!QuickStartKindUnlocked(kind)) {
        // The large pool's rooms are combat rooms first - WAVES is the one
        // kind of its three that's always unlocked.
        kind = QS_EVENT_WAVES;
    }
    return kind;
}

static u8 QuickStartSlotGetKind(s32 slotIndex) {
    return (QsCheckFlag(GF_SLOT_KIND_BIT(slotIndex, 0)) ? 1 : 0) |
           (QsCheckFlag(GF_SLOT_KIND_BIT(slotIndex, 1)) ? 2 : 0) |
           (QsCheckFlag(GF_SLOT_KIND_BIT2(slotIndex)) ? 4 : 0);
}

static void QuickStartSlotSetKind(s32 slotIndex, u8 kind) {
    if (kind & 1) {
        QsSetFlag(GF_SLOT_KIND_BIT(slotIndex, 0));
    }
    if (kind & 2) {
        QsSetFlag(GF_SLOT_KIND_BIT(slotIndex, 1));
    }
    if (kind & 4) {
        QsSetFlag(GF_SLOT_KIND_BIT2(slotIndex));
    }
}

// Generic 8-bit scratch value per ladder, packed as 8 global flag bits -
// which specific meaning it holds depends on that ladder's kind: a reward
// pool index (chest), or bit 0 alone as a friendly/evil boolean (NPC).
static u8 QuickStartSlotGetExtra(s32 slotIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 8; b++) {
        if (QsCheckFlag(GF_SLOT_EXTRA_BIT(slotIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartSlotSetExtra(s32 slotIndex, u8 value) {
    s32 b;
    for (b = 0; b < 8; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_SLOT_EXTRA_BIT(slotIndex, b));
        }
    }
}

static u8 QuickStartSlotGetRoomIndex(s32 slotIndex) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 6; b++) {
        if (QsCheckFlag(GF_SLOT_ROOM_BIT(slotIndex, b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartSlotSetRoomIndex(s32 slotIndex, u8 value) {
    s32 b;
    for (b = 0; b < 6; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_SLOT_ROOM_BIT(slotIndex, b));
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

// Same shape as QuickStartQuestionRoomEntry above, plus entranceX/entranceY
// - the 2-door pool's synthetic entrance (see the retired cave-connector trigger
// below) has to land the player somewhere sensible inside whichever real
// room got drawn, unlike the 1-door pool's rooms which all share one
// generic template's (0x78,0x78) convention.
typedef struct {
    u8 area;
    u8 room;
    s16 entranceX;
    s16 entranceY;
    s16 contentDX;
    s16 contentDY;
} QuickStart2DoorRoomEntry;

// Split into two pools per the user's own room-size survey: small rooms get
// item/sprite-event content only (chest/NPC); medium/large rooms get
// combat/puzzle content only (miniboss/waves, and puzzles later). See
// QuickStartRandomizeSlotsOnce for how a ladder picks a pool and a kind
// together, and QuickStartSlotGetPool/SetPool for the per-ladder bit that
// remembers which pool it drew from.
//
// Small pool: content placed by the user directly (Lua position script) at
// a single shared spot, (120,80) - 40px north of the (120,120) shared
// spawn, facing back down toward the door (see
// QuickStartSetupSlotRoomContent's direction = IdleSouth) - rather than
// each room's own individually-walked offset. Confirmed in the emulator for
// the item and NPC kinds (both land exactly on (120,80), direction sticks
// for the NPC).
static const QuickStartQuestionRoomEntry sQuickStartSmallRoomPool[] = {
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_BLUE, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GENTARI_MAIN, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GREEN, 0, -40 },
    // (HYRULE_FIELD_EXIT and HYRULE_FIELD_SOUTHWEST left this pool for the
    // overworld expansion: their real doors in Eastern Hills South and
    // Western Wood South are open now, so each is a dedicated content site
    // - see sQuickStartRoomContentSites.)
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_TOWN, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_LAKE_HYLIA_OCARINA, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_LIBRARI, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_MINISH_WOODS_BOMB, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_NEXT_TO_KNUCKLE, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_RED, 0, -40 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SHOE_MINISH, 0, -40 },
    // Back in the pool - freed up once the cave connector moved off this
    // room (first to GENTARI_EXIT, since removed entirely - see
    // sQuickStart2DoorSmallRoomPool/LargeRoomPool), per the user's own
    // explicit request.
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SIDE_AREA, 0, -40 },
    // ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD used to sit here. It is
    // a content site now, entered by shrinking at South Hyrule Field's Minish
    // portal and walking through the tiny door at (72,456), with its own
    // vanilla INSTANT_MINISH exit restored (transitions.c). Leaving it in
    // this pool as well would be a trap: a ladder draw puts a NORMAL-size
    // player in there, and an INSTANT_MINISH border only fires for a minish
    // one, so there would be no way back out.
    // Not the shared Minish House Interiors template room, so not verified
    // against the same (120,120)/(120,80) convention - the user's own
    // testing harness (this file's synthetic-warp technique) can't reach
    // AREA_VEIL_FALLS_CAVES directly either (QuickStartEnforceContainment/
    // QuickStartEnforceLonLonContainment block any raw warp there from every
    // reachable starting room), so this offset is a conservative guess
    // pending real in-game playtesting, not an emulator-confirmed spot like
    // every other entry in this pool. The user's own note: reaching this
    // room in a real playthrough needs Zora's Flippers or Roc's Cape
    // already found elsewhere this run.
    { AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_HEART_PIECE, 0, -16 },
};
// One less than the array holds, and always has been: draws are taken modulo
// this, so the Veil Falls row above stays out of circulation until its
// guessed content offset has been walked for real. Dropped from 14 to 13
// along with South Hyrule Field's Minish house leaving the pool, precisely so
// that removal doesn't promote Veil Falls into the draw as a side effect.
#define QUICKSTART_SMALL_ROOM_POOL_SIZE 13

// Medium/large pool: miniboss and (once built) puzzle/wave content needs
// more room to work with than the small pool's shared generic template
// rooms.
//
// ROOM_MINISH_HOUSE_INTERIORS_POT_MINISH deliberately left OUT: verified in
// the emulator that QS_EVENT_WAVES there spawns entities with correct
// positions/sprite indices (confirmed via direct memory reads) but they
// never actually render on screen - a real bug, not a placement issue (the
// exact same enemy type/position combo rendered fine in the Gina room
// below). POT_MINISH has its own distinctive water/swirl tile reskin,
// which likely eats into the same VRAM/GFX-slot budget
// QUICKSTART_WAVE_TYPE_CAP was built to protect earlier this session -
// needs its own dedicated investigation before hosting multi-enemy content
// again (a single MINIBOSS enemy worked here before this split, so the
// problem seems specific to spawning several at once, not the room in
// general).
//
// Of the 7 named Dojo rooms (AREA_DOJOS), only 3 have their own single real
// door and are simple additions here: ROOM_DOJOS_GRAYBLADE, SWIFTBLADE_I,
// and WAVEBLADE (all WARP_TYPE_BORDER_SOUTH, retargeted in transitions.c
// the same way as every other pool room here). ROOM_DOJOS_GRIMBLADE is
// already this mode's shop room, not a pool candidate. The remaining 3
// (SPLITBLADE, GREATBLADE, SCARBLADE) have NO real door of their own -
// gExitLists_Dojos maps them to gExitList_NoExitList; they're reached via
// a scroll-seam from a separate "TO_X" hallway room instead (ROOM_DOJOS_TO_
// SPLITBLADE/GREATBLADE/SCARBLADE, which hold the real doors) - the same
// class of adjacency problem as Gentari's Room/Main (still unresolved),
// left out per the user's own explicit choice rather than solved here.
//
// The 3 added rooms share an identical vanilla layout (confirmed via a
// dedicated content survey): a BLADE_BROTHERS dojo-master NPC (dialogue/
// technique-demo script, not a fight - script_BladeBrothers.inc), an
// ARCHWAY decoration, 6 FURNITURE pillars, and one more OBJECT-kind
// fixture (a per-dojo technique-scroll reward, not a decompiled chest
// type) - no ENEMY-kind entities and no per-room roomInit.c logic to
// special-case (unlike Grimblade's darkness/torch handling). All of this
// is OBJECT/NPC kind, so QuickStartClearLadderRoomObstacles' existing
// generic sweep handles every one of them the same way it already does for
// Gina's own leftover content below - no manual removal needed.
static const QuickStartQuestionRoomEntry sQuickStartMediumRoomPool[] = {
    // Chest/Gina-ghost cleanup still pending (the user asked for the room's
    // own treasure chest to be removed/replaced and possibly the Gina
    // sprite removed). Verified in the emulator: a full 3-wave
    // QS_EVENT_WAVES encounter here renders correctly end to end (hint,
    // 4/6/8-enemy waves, reward drop).
    { AREA_ROYAL_VALLEY_GRAVES, ROOM_ROYAL_VALLEY_GRAVES_GINA, 0, -20 },
    // All 3 Dojo rooms share the exact same tilemap/layout (confirmed via
    // screenshot comparison at the shared (0x78,0x78) spawn point), so the
    // same modest content offset works for all of them - matching Gina's
    // own (0,-20), clear of the vanilla BLADE_BROTHERS NPC's own spot
    // (0x78,0x28) and the symmetric furniture pillars.
    { AREA_DOJOS, ROOM_DOJOS_GRAYBLADE, 0, -20 },
    { AREA_DOJOS, ROOM_DOJOS_SWIFTBLADE_I, 0, -20 },
    { AREA_DOJOS, ROOM_DOJOS_WAVEBLADE, 0, -20 },
};
#define QUICKSTART_MEDIUM_ROOM_POOL_SIZE 4

// ---- 2-door "? room" pool ----
// Rooms with two REAL doors, for wherever an overworld region needs a
// through-cave shortcut (walk in one point, come out another) instead of
// the 1-door pool's dead-end pockets. GENTARI_EXIT (the Lon Lon Ranch cave
// connector's original implementation - a single real door made
// bidirectional via a duplicated sQuickStartLinks entry) is retired
// entirely per the user's own request, now that a real pool of genuine
// 2-door rooms has been surveyed. Only Lon Lon Ranch needs one of these
// today; more overworld regions will draw from this same pool later.
//
// entranceX/entranceY: the synthetic entrance's landing spot inside this
// room (not necessarily either real door's own vanilla landing point -
// this is a fresh teleport, so any confirmed-open spot works). Reused
// verbatim from this session's screenshot survey (each room's own
// gRoomControls-local (100,100), the position used to capture every
// candidate's reference screenshot) except where that spot looked
// occupied/unclear in the screenshot - flagged individually below. None of
// these have had a full emulator walkability survey the way Castle
// Garden/Melari's Mine/Lon Lon Ranch's own content spots did; treat every
// entranceX/Y and contentDX/DY here as a reasonable starting guess pending
// real playtesting, same status the Veil Falls heart-piece hallway
// shipped with earlier this session.
// contentDX/contentDY: offset from entranceX/Y for the reward/enemy/NPC -
// a modest fixed nudge (0,-24), matching this file's other pools'
// convention of a small generic offset rather than a per-room walked one.
static const QuickStart2DoorRoomEntry sQuickStart2DoorSmallRoomPool[] = {
    { AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_DARKNUT, 100, 100, 0, -24 },
    // ROOM_CAVES_HEART_PIECE_HALLWAY used to sit here, kept fully vanilla
    // per the user's own request ("we can keep this as it is in vanilla,
    // with a heart piece inside"). It's gone from this pool: it is North
    // Hyrule Field's Heart Piece Hallway cave on the vanilla-door model
    // now, entered through its own real cave mouth and holding its own
    // randomized event (sQuickStartRoomContentSites). Leaving it here as
    // well would have let the 2-door connector draw a room that another
    // system already owns.
    { AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BRIDGE_SWITCH, 100, 100, 0, -24 },
    { AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST, 100, 100, 0, -24 },
    { AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY, 100, 100, 0, -24 },
    { AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER, 100, 100, 0, -24 },
    // Vanilla pots removed by the same generic obstacle clear every other
    // pool room gets (they're plain OBJECT-kind entities). The user also
    // asked to keep a secret bombable wall in this room leading to another
    // ? room - that mechanic isn't in any decompiled source this repo has
    // (confirmed via a dedicated search: no Bombable/CrackedWall object
    // type exists, and the room's own collision/tilemap data is still raw
    // binary) - left completely untouched rather than guessed at.
    { AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_EXIT, 100, 100, 0, -24 },
    { AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE, 100, 100, 0, -24 },
};
#define QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE 7

// Large pool: miniboss/wave content, EXCEPT the 3 rooms flagged below
// (QuickStart2DoorWantsOverworldEnemies), which always get the same
// overworld-density enemy fill Castle Garden/Melari's Mine/Lon Lon Ranch
// use (QuickStartSpawnEnemyGroup) instead of a chest/miniboss/npc/waves
// roll, per the user's own explicit request - contentDX/DY is unused for
// those 3 (0,0 placeholder), see sQuickStart2Door*EnemyOffsets instead.
static const QuickStart2DoorRoomEntry sQuickStart2DoorLargeRoomPool[] = {
    { AREA_CRENEL_MINISH_PATHS, ROOM_CRENEL_MINISH_PATHS_MELARI, 100, 100, 0, 0 },
    { AREA_CRENEL_MINISH_PATHS, ROOM_CRENEL_MINISH_PATHS_RAIN, 100, 100, 0, 0 },
    // Entrance (144,112). The screenshot survey's (100,100) shot didn't
    // clearly show Link here, and the guess that replaced it - (80,110) -
    // turned out to be the exact spot one of this hallway's HUGE_ACORN
    // props stands on, at (80,112). Spawning inside it left Link invisible
    // and unable to move in any direction (reported by the user, then
    // reproduced: an entity dump at the entrance shows four overlapping
    // HUGE_ACORN entities there, and holding each direction for 15 frames
    // moves the player 0px). (144,112) is the same height, 64px clear of
    // that acorn, and confirmed standable and walkable in all four
    // directions.
    { AREA_MINISH_PATHS, ROOM_MINISH_PATHS_MINISH_VILLAGE, 144, 112, 0, 0 },
    // Entrance measured, not the shared (100,100) default: this room is a
    // 240x320 hallway with THREE 4x5 water pools in a zigzag (collision
    // 0x30), and (100,100) is tile (6,6) - dead centre of the top-left one.
    // The player materialised in the water and could not get out; the
    // content spot 24px above it was in the same pool. (104,200) is tile
    // (6,12), the open corridor that runs between the pools, and the
    // content spot lands on (6,11), also open.
    { AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH, 104, 200, 0, -24 },
    { AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_EAST_2F, 100, 100, 0, -24 },
    { AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_1F, 100, 100, 0, -24 },
    { AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_2F, 100, 100, 0, -24 },
    { AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST, 100, 100, 0, -24 },
    // Festari's own NPC sprite is deleted by the generic obstacle clear
    // like any other pool room's leftover NPCs; his back door (into
    // AREA_MINISH_WOODS) is forced open every visit regardless
    // (roomInit.c: sub_StateChange_MinishHouseInteriors_Festari now sets
    // M_PRIEST_MOVE under #ifdef QUICKSTART, the same flag his own script
    // checks to step aside).
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_FESTARI, 100, 100, 0, -24 },
    { AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT, 100, 100, 0, -24 },
    // (0,-24) originally put content at local (100,76), directly on top of
    // one of this room's own decorative torch pillars (confirmed via
    // screenshot survey after the user reported spawning inside one) -
    // this bridge corridor has pillar rows repeating roughly every ~12-24px,
    // and 76 lands right on one. (0,-48) instead confirmed clean in the
    // gap between pillar rows.
    // Also measured. The bridge is a 3-tile walkway (tiles 7-9, x 112-159)
    // running down a void of 0x21 tiles, and the shared (100,100) default
    // is tile (6,6) - one tile off its west edge, i.e. the "spawns in
    // midair" report. (136,152) is the middle of the walkway; the content
    // spot 48px above it stays on it.
    { AREA_DARK_HYRULE_CASTLE_BRIDGE, ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN, 136, 152, 0, -48 },
    // Vanilla's own locked-door precondition (ITEM_GREEN_SWORD +
    // NAKANIWA_00_EZERO) is forced open every visit (roomInit.c:
    // sub_StateChange_SanctuaryEntrance_Main, under #ifdef QUICKSTART).
    { AREA_SANCTUARY_ENTRANCE, ROOM_SANCTUARY_ENTRANCE_MAIN, 100, 100, 0, -24 },
    // (0,-24) originally put content at local (100,76), inside the rocky
    // cave-mouth archway just north of the entrance spot (unwalkable) -
    // confirmed via screenshot survey after the user reported both the
    // Darknut and its drop spawning inside it. This room's own walkable
    // path runs south from the entrance, not north; (0,+24) instead
    // confirmed clean, still on the open path.
    // Retired from the draw (the size constant below excludes this last
    // row). The full-room survey measured it at 10 open tiles in a 15x15
    // room - a sliver of corridor in an area literally named NULL. A LARGE
    // pool draw puts wave gauntlets and minibosses in here, and ten tiles
    // cannot host either. Row kept so nothing renumbers.
    // Retired from the draw (QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE stops one
    // short of this row) but measured anyway so the row is not a trap if it
    // is ever re-enabled: the room is a 240x240 pool of water with a single
    // one-tile causeway at tile x=7. (120,168) is on the causeway and the
    // content spot 24px below it stays on it.
    { AREA_NULL_61, ROOM_NULL_61_0, 120, 168, 0, 24 },
};
#define QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE 12

// Same flag-bank convention as GF_LADDER_*/GF_DIFFICULTY_BIT above - picks
// up right after GF_CAVE_CONNECTOR_DONE (183), the highest bit previously
// allocated (now free, GENTARI_EXIT's whole mechanism is gone). Only one
// connector slot exists today, so unlike GF_SLOT_BASE(i) this doesn't
// need a per-index base - a single flat set of bits is enough.
#define GF_2DOOR_RANDOMIZED 184
#define GF_2DOOR_POOL_BIT 185
#define GF_2DOOR_ROOM_BIT(b) (186 + (b)) // b = 0..4, up to 32 rooms/pool
#define GF_2DOOR_KIND_BIT(b) (191 + (b)) // b = 0,1
#define GF_2DOOR_KIND_BIT2 206 // 3rd kind bit - see GF_SLOT_KIND_BIT2(i)
#define GF_2DOOR_EXTRA_BIT(b) (193 + (b)) // b = 0..7
#define GF_2DOOR_DONE 201

static u8 QuickStart2DoorGetPool(void) {
    return QsCheckFlag(GF_2DOOR_POOL_BIT) ? 1 : 0;
}

static void QuickStart2DoorSetPool(u8 pool) {
    if (pool) {
        QsSetFlag(GF_2DOOR_POOL_BIT);
    }
}

static u8 QuickStart2DoorGetKind(void) {
    return (QsCheckFlag(GF_2DOOR_KIND_BIT(0)) ? 1 : 0) | (QsCheckFlag(GF_2DOOR_KIND_BIT(1)) ? 2 : 0) |
           (QsCheckFlag(GF_2DOOR_KIND_BIT2) ? 4 : 0);
}

static void QuickStart2DoorSetKind(u8 kind) {
    if (kind & 1) {
        QsSetFlag(GF_2DOOR_KIND_BIT(0));
    }
    if (kind & 2) {
        QsSetFlag(GF_2DOOR_KIND_BIT(1));
    }
    if (kind & 4) {
        QsSetFlag(GF_2DOOR_KIND_BIT2);
    }
}

static u8 QuickStart2DoorGetExtra(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 8; b++) {
        if (QsCheckFlag(GF_2DOOR_EXTRA_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStart2DoorSetExtra(u8 value) {
    s32 b;
    for (b = 0; b < 8; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_2DOOR_EXTRA_BIT(b));
        }
    }
}

static u8 QuickStart2DoorGetRoomIndex(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 5; b++) {
        if (QsCheckFlag(GF_2DOOR_ROOM_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStart2DoorSetRoomIndex(u8 value) {
    s32 b;
    for (b = 0; b < 5; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_2DOOR_ROOM_BIT(b));
        }
    }
}

static void QuickStart2DoorGetTarget(u8* area, u8* room) {
    // (s32) cast before % - a plain u8 %= (this file's established
    // convention, e.g. QuickStartGetSlotTarget's rawIndex % poolSize)
    // pulls in __umodsi3 (unsigned modulo), which this build doesn't link.
    s32 poolIndex = QuickStart2DoorGetRoomIndex();
    if (QuickStart2DoorGetPool() == 0) {
        poolIndex %= QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE;
        *area = sQuickStart2DoorSmallRoomPool[poolIndex].area;
        *room = sQuickStart2DoorSmallRoomPool[poolIndex].room;
    } else {
        poolIndex %= QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
        *area = sQuickStart2DoorLargeRoomPool[poolIndex].area;
        *room = sQuickStart2DoorLargeRoomPool[poolIndex].room;
    }
}

static void QuickStart2DoorGetSpawnInfo(s16* entranceX, s16* entranceY, s16* contentDX, s16* contentDY) {
    s32 poolIndex = QuickStart2DoorGetRoomIndex();
    if (QuickStart2DoorGetPool() == 0) {
        poolIndex %= QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE;
        *entranceX = sQuickStart2DoorSmallRoomPool[poolIndex].entranceX;
        *entranceY = sQuickStart2DoorSmallRoomPool[poolIndex].entranceY;
        *contentDX = sQuickStart2DoorSmallRoomPool[poolIndex].contentDX;
        *contentDY = sQuickStart2DoorSmallRoomPool[poolIndex].contentDY;
    } else {
        poolIndex %= QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
        *entranceX = sQuickStart2DoorLargeRoomPool[poolIndex].entranceX;
        *entranceY = sQuickStart2DoorLargeRoomPool[poolIndex].entranceY;
        *contentDX = sQuickStart2DoorLargeRoomPool[poolIndex].contentDX;
        *contentDY = sQuickStart2DoorLargeRoomPool[poolIndex].contentDY;
    }
}

static bool32 QuickStart2DoorIsCurrentRoom(void) {
    u8 area, room;
    if (!QsCheckFlag(GF_2DOOR_RANDOMIZED)) {
        return FALSE;
    }
    QuickStart2DoorGetTarget(&area, &room);
    return gRoomControls.area == area && gRoomControls.room == room;
}

// No room in either 2-door pool is kept vanilla any more - the one that
// was (ROOM_CAVES_HEART_PIECE_HALLWAY) left the pool entirely when it
// became a content site. Kept as a hook because the pools are still
// hand-curated and the next room the user wants left alone belongs here.
static bool32 QuickStart2DoorIsKeptVanilla(u8 area, u8 room) {
    return FALSE;
}

static bool32 QuickStart2DoorWantsOverworldEnemies(u8 area, u8 room) {
    return (area == AREA_CRENEL_MINISH_PATHS && room == ROOM_CRENEL_MINISH_PATHS_MELARI) ||
           (area == AREA_CRENEL_MINISH_PATHS && room == ROOM_CRENEL_MINISH_PATHS_RAIN) ||
           (area == AREA_MINISH_PATHS && room == ROOM_MINISH_PATHS_MINISH_VILLAGE);
}

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
// ITEM_WALLET and ITEM_KINSTONE_BAG removed - both are granted for free at
// boot now (GameTask_Transition), so either one dropping here would just be
// a dead pick that does nothing.
// The Bow and Bombs lead the list for two reasons. They are COMMON
// WEAPON/TOOL items per docs/QUICKSTART_ITEM_TIERS.md and were reachable
// NOWHERE in the mode - not in a pool, not in the shop, not in a starter
// choice - ever since they stopped being boot grants; the comments claiming
// they were "drops and shop stock now" described an intention, not code.
// And the lottery kinds only get a 2-bit slice of `extra` to name a prize
// with (QuickStartPickLotteryExtra), so they can only reach the first four
// entries - which makes the first four the right place for things that are
// always worth finding, and pushes the two capacity upgrades past it.
//
// Eight entries, not six, and the count has to STAY a power of two: agbcc
// turns "% 8" into a mask but emits __umodsi3 for "% 6", and its runtime lib
// does not provide one. Going to eight is not padding either - it is what
// finally makes this the common WEAPON/TOOL tier plus common REWARDS,
// instead of two capacity upgrades and two consolation prizes.



// Miniboss variety: QS_EVENT_MINIBOSS/QuickStart2Door's own miniboss case
// used to always spawn a plain CreateEnemy(DARK_NUT, 0). It now draws from
// sQuickStartElites, the level-6 roster - which is what makes the user's
// "Elites includes Darknuts, all mini bosses" true by construction: the
// miniboss pool and the Elite tier are the same table, so neither can
// drift from the other.
#define QUICKSTART_MINIBOSS_POOL_SIZE ((s32)ARRAY_COUNT(sQuickStartElites))

// Lottery prizes are drawn from their own small fixed table rather than the
// tier system, and that is deliberate. A lottery decides its prize on the
// first visit and then has to recognise that exact item on the floor when the
// player comes back (QuickStartGroundItemOfForm), but a tier draw filters on
// what the run currently owns - so the answer could change between placing
// the prize and checking for it, and the room would never register as solved.
//
// These eight rows have no prerequisites and are all repeatable, so the draw
// is a pure function of the stored seed. Weighted 5/2/1 = 62.5 / 25 / 12.5,
// the closest an eight-entry table gets to the mode's 60/30/10 curve.
static const u16 sQuickStartLotteryPrizes[8] = {
    ITEM_RUPEE50,  ITEM_HEART_PIECE, ITEM_RUPEE50,  ITEM_HEART_PIECE, // common
    ITEM_RUPEE50,                                                     // common
    ITEM_RUPEE100, ITEM_RUPEE100,                                     // uncommon
    ITEM_HEART_CONTAINER,                                             // rare
};
#define QUICKSTART_LOTTERY_PRIZE_COUNT 8

// --- The lottery "extra" byte -------------------------------------------
//
// Both lottery kinds pack their whole state into the single 8-bit `extra`
// value every kind gets, because that is what survives leaving the room and
// coming back (GF_CONTENT_SITE_EXTRA_BIT / GF_2DOOR_EXTRA_BIT, 8 bits each).
//
// The prize field is THREE bits, and the mask below is the only place that
// number is written down. It used to be two, which was correct while
// the shared reward pool had four entries and silently wrong the moment it
// grew to eight: the writer emitted a 3-bit index into a 2-bit slot, so
// indices 4-7 folded onto 0-3 and, in the pot room, the spilled bit landed in
// the winner field and perturbed which pot held the prize.
//
// Tie the mask to the pool size and neither can drift again.
#define QUICKSTART_LOTTERY_PRIZE_SHIFT 2
#define QUICKSTART_LOTTERY_PRIZE_MASK (QUICKSTART_LOTTERY_PRIZE_COUNT - 1)

static s32 QuickStartLotteryPrizeIndex(s32 extra) {
    return (extra >> QUICKSTART_LOTTERY_PRIZE_SHIFT) & QUICKSTART_LOTTERY_PRIZE_MASK;
}

// Chest lottery: winner slot in bits 0-1 (0-2, three chests), prize in bits
// 2-4. Bits 5-7 are unused and always were.
static u8 QuickStartPickLotteryExtra(void) {
    u8 winnerSlot = (u8)((s32)Random() % 3);
    u8 prizeIndex = (u8)((s32)Random() % QUICKSTART_LOTTERY_PRIZE_COUNT);
    return (u8)(winnerSlot | ((prizeIndex & QUICKSTART_LOTTERY_PRIZE_MASK) << QUICKSTART_LOTTERY_PRIZE_SHIFT));
}

// Pot lottery only: 9 pots instead of chests' 3, so winnerSlot needs 4 bits
// (0-8) instead of the 2 bits QuickStartPickLotteryExtra above packs for the
// 3-chest case - still fits the same 8-bit "extra" scratch value every other
// kind gets (4 bits winner + 2 bits prize = 6 of 8 bits used).
#define QUICKSTART_POT_ROOM_PRESET_COUNT 3

// The pot room's whole layout is derived from this one byte (see
// QuickStartSetupPotRoomContent), so it has to carry everything that must
// survive leaving the room and coming back:
//
//   bits 0-1  density preset: packed / mixed / sparse
//   bits 2-4  prize index into sQuickStartLotteryPrizes
//   bits 5-7  where in the fill order the winning pot sits
//
// Nothing here is re-rolled on re-entry, and that is the point. The layout
// used to come straight from Random() at spawn time, which meant walking
// out and back in reshuffled which pot held the prize - the room was a slot
// machine you could re-pull instead of a puzzle you had to dig through.
//
// The winner field gave up a bit to the widened prize field, going from 16
// buckets to 8. It is not a slot index, it is a position along the far half
// of the fill order (see the winnerIndex arithmetic in
// QuickStartPotRoomGenerate), and that half is only ~10-22 pots deep - so
// eight buckets still land the prize somewhere different nearly every time,
// while four bits were finer than the thing being addressed.
#define QUICKSTART_POT_WINNER_SHIFT 5
#define QUICKSTART_POT_WINNER_BUCKETS 8
static u8 QuickStartPickPotRoomExtra(void) {
    u8 preset = (u8)((s32)Random() % QUICKSTART_POT_ROOM_PRESET_COUNT);
    u8 prizeIndex = (u8)((s32)Random() % QUICKSTART_LOTTERY_PRIZE_COUNT);
    u8 winnerBucket = (u8)((s32)Random() % QUICKSTART_POT_WINNER_BUCKETS);
    return (u8)(preset | ((prizeIndex & QUICKSTART_LOTTERY_PRIZE_MASK) << QUICKSTART_LOTTERY_PRIZE_SHIFT) |
                (winnerBucket << QUICKSTART_POT_WINNER_SHIFT));
}

// Runs every frame in Castle Garden Main but only ever does anything once
// per save (GF_SLOTS_RANDOMIZED) - exactly once, each of 4 "? room" slots
// is assigned a pool (small vs medium/large, per the user's own room-size
// split), a kind restricted to whatever that pool allows, and (for
// chest/NPC kinds) which specific reward or disposition, all via Random().
// Slots 0, 1, and 3 each additionally draw which room within that pool they
// lead to - slots 0-1 are Castle Garden's own two real ladders, slot 3 is
// the Goron Cave Stairs door in Lon Lon Ranch (see the retired ladder-entrance table
// below), a fixed entrance but a random destination, same as the other two.
// Slot 2 (Ranch House West) predates the Ranch House's full vanilla reset
// earlier this session - it still rolls a kind/extra for save-flag-layout
// stability, but nothing reads it any more (Ranch House West has no
// QUICKSTART content left), so it's left exactly as it always was rather
// than folded into the new pool system. Doing this lazily on first room
// entry rather than in GameTask_Transition avoids touching the boot
// sequence at all - the persistent flags this writes make the choice stick
// for the rest of this save regardless of when it first ran.
static void QuickStartRandomizeSlotsOnce(void) {
    s32 i, j, drawCount;
    u8 usedPool[3];
    u8 usedRoom[3];
    if (QsCheckFlag(GF_SLOTS_RANDOMIZED)) {
        return;
    }
    drawCount = 0;
    for (i = 0; i < 4; i++) {
        u8 pool, kind, roomIdx, poolSize;
        if (i == 2) {
            kind = (u8)((s32)Random() % 3);
            QuickStartSlotSetKind(i, kind);
            if (kind == QS_EVENT_ITEM_DROP) {
                QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE));
            } else if (kind == QS_EVENT_NPC) {
                QuickStartSlotSetExtra(i, (u8)((s32)Random() % 2));
            }
            continue;
        }
        pool = (u8)((s32)Random() % 2);
        QuickStartSlotSetPool(i, pool);
        if (pool == 0) {
            kind = QuickStartPickSmallKind();
        } else {
            kind = QuickStartPickLargeKind();
        }
        QuickStartSlotSetKind(i, kind);
        if (kind == QS_EVENT_ITEM_DROP) {
            QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE));
        } else if (kind == QS_EVENT_NPC) {
            QuickStartSlotSetExtra(i, (u8)((s32)Random() % 2)); // bit 0: 1 = evil, 0 = friendly
        } else if (kind == QS_EVENT_WAVES) {
            // Reuses the ladder chest reward pool for the wave room's own
            // 3-waves-cleared drop, same reward variety a chest room gets
            // instead of a single fixed item.
            QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE));
        } else if (kind == QS_EVENT_MINIBOSS) {
            QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_MINIBOSS_POOL_SIZE));
        } else if (kind == QS_EVENT_POT_LOTTERY) {
            QuickStartSlotSetExtra(i, QuickStartPickPotRoomExtra());
        } else if (kind == QS_EVENT_CHEST_LOTTERY) {
            QuickStartSlotSetExtra(i, QuickStartPickLotteryExtra());
        }
        poolSize = (pool == 0) ? QUICKSTART_SMALL_ROOM_POOL_SIZE : QUICKSTART_MEDIUM_ROOM_POOL_SIZE;
        // Distinct room per slot - two slots sharing one physical "? room"
        // makes leaving through it genuinely ambiguous about which slot's
        // content/return-path applies. This used to fall back to a
        // duplicate once the rolled pool was exhausted (accepting the
        // ambiguity to avoid an infinite retry loop) - confirmed by the
        // user's own bug report to actually manifest: back when the medium
        // pool held only Gina's room (QUICKSTART_MEDIUM_ROOM_POOL_SIZE==1),
        // any 2 of the 3 slots rolling "medium" (a 50/50 coin flip each,
        // ~50% chance overall) were forced to share that one room, and
        // leaving through it via whichever slot iterates later in
        // QuickStartFindSlotForCurrentRoom's fixed {0,1,3} order got
        // misattributed to the earlier slot instead - reported as leaving
        // the Goron Cave Stairs door's (slot 3) room landing back at slot
        // 1's own Castle Garden spot instead of Lon Lon Ranch. The medium
        // pool has more rooms now (the 3 Dojo rooms above), which lowers
        // the odds, but this fallback stays regardless - it's a real fix,
        // not just odds-reduction. Falls back to the OTHER pool instead
        // now - total capacity (14+4=18) always comfortably covers 3
        // slots, so this never needs to loop forever, and kind/extra are
        // re-rolled to match whichever pool actually ends up backing this
        // slot.
        {
            s32 usedInThisPool = 0;
            for (j = 0; j < drawCount; j++) {
                if (usedPool[j] == pool) {
                    usedInThisPool++;
                }
            }
            if (usedInThisPool >= poolSize) {
                pool = 1 - pool;
                QuickStartSlotSetPool(i, pool);
                if (pool == 0) {
                    kind = QuickStartPickSmallKind();
                } else {
                    kind = QuickStartPickLargeKind();
                }
                QuickStartSlotSetKind(i, kind);
                if (kind == QS_EVENT_ITEM_DROP || kind == QS_EVENT_WAVES) {
                    QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE));
                } else if (kind == QS_EVENT_NPC) {
                    QuickStartSlotSetExtra(i, (u8)((s32)Random() % 2));
                } else if (kind == QS_EVENT_MINIBOSS) {
                    QuickStartSlotSetExtra(i, (u8)((s32)Random() % QUICKSTART_MINIBOSS_POOL_SIZE));
                } else if (kind == QS_EVENT_POT_LOTTERY) {
                    QuickStartSlotSetExtra(i, QuickStartPickPotRoomExtra());
                } else if (kind == QS_EVENT_CHEST_LOTTERY) {
                    QuickStartSlotSetExtra(i, QuickStartPickLotteryExtra());
                }
                poolSize = (pool == 0) ? QUICKSTART_SMALL_ROOM_POOL_SIZE : QUICKSTART_MEDIUM_ROOM_POOL_SIZE;
            }
            for (;;) {
                roomIdx = (u8)((s32)Random() % poolSize);
                for (j = 0; j < drawCount; j++) {
                    if (usedPool[j] == pool && usedRoom[j] == roomIdx) {
                        break;
                    }
                }
                if (j == drawCount) {
                    break;
                }
            }
        }
        usedPool[drawCount] = pool;
        usedRoom[drawCount] = roomIdx;
        drawCount++;
        QuickStartSlotSetRoomIndex(i, roomIdx);
    }
    QsSetFlag(GF_SLOTS_RANDOMIZED);
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
// Ranch, shut behind the KINSTONE_29 fusion) is a third
// entrance into this same "? room" system now, ladder index 3, with its
// own real-door-adjacent trigger box (see the sQuickStartLinks comment
// above for how that corridor was traced) rather than a HIDDEN_LADDER_DOWN
// fixture. Unlike the fixed 3-room mapping this replaced, or Ranch House
// West's own single fixed room, ladder index 3's destination is a pool
// draw exactly like ladders 0-1 (QuickStartRandomizeSlotsOnce above), so
// its target has to be resolved at trigger time rather than being a static
// entry in sQuickStartLinks - hence this table (fromArea/fromRoom/trigger
// box/ladder index) and the retired ladder-link trigger, rather than
// folding it into sQuickStartLinks. Unlike ladders 0-1, though, it's
// entered from a different room than it returns to - see
// QuickStartFixupQuestionRoomReturn's own slotIndex == 3 special case
// below for why leaving the pool room lands back in Lon Lon Ranch instead
// of Castle Garden Main.

// EMPTY. Every synthetic "walk into an invisible box and get teleported to
// a randomly drawn pool room" entrance has been retired in favour of the
// real vanilla door that was always there, with a randomized event spawned
// inside the room it really leads to (sQuickStartRoomContentSites below).
//
// The last five to go were Castle Garden's two ladders (the Great Fairy
// cellar and Grimblade's dojo entrance), Lon Lon Ranch's Goron Cave door,
// Link's House, and North Hyrule Field's Heart Piece Hallway cave. Those
// four had been held back on the grounds that they open onto more than a
// single dead-end room; the user's own call was to convert them anyway,
// "regardless of if they are single door rooms or two-door rooms". Each
// pocket turned out to be closed in vanilla already, except the Heart
// Piece Hallway's onward door to ROOM_CAVES_TO_GRAVEYARD, which is
// neutralized in transitions.c instead.
//
// The sentinel row exists only because C has no zero-length arrays. Area
// 0xff is not a real area, so the three loops that still walk this table
// (the retired ladder-link trigger and
// QuickStartEnforceFieldRegionContainment) iterate once and match
// nothing. The rest of the synthetic machinery - the two room pools, the
// per-slot flag blocks, QuickStartSetupSlotRoomContent - is left intact
// and still referenced, so the retired system reads as a coherent whole
// rather than a half-deleted one; nothing reaches it in play.

// Which "? room" pool entry backs a given ladder this save, and where the
// player lands inside it - every pool room was verified walkable at the
// same default (0x78,0x78) spawn (see the pool comment above), so unlike
// the old fixed 3-room mapping this doesn't need a per-ladder spawn
// override.
static void QuickStartGetSlotTarget(s32 slotIndex, u8* area, u8* room) {
    s32 rawIndex = QuickStartSlotGetRoomIndex(slotIndex);
    if (QuickStartSlotGetPool(slotIndex) == 0) {
        s32 poolIndex = rawIndex % QUICKSTART_SMALL_ROOM_POOL_SIZE;
        *area = sQuickStartSmallRoomPool[poolIndex].area;
        *room = sQuickStartSmallRoomPool[poolIndex].room;
    } else {
        s32 poolIndex = rawIndex % QUICKSTART_MEDIUM_ROOM_POOL_SIZE;
        *area = sQuickStartMediumRoomPool[poolIndex].area;
        *room = sQuickStartMediumRoomPool[poolIndex].room;
    }
}


extern Script script_QuickStartLadderNpc0;
extern Script script_QuickStartLadderNpc1;
static Script* const sQuickStartEventNpcScripts[2] = {
    &script_QuickStartLadderNpc0,
    &script_QuickStartLadderNpc1,
};

// The NPC event's one-time gate and friendly/evil split both live INSIDE
// the .inc script, on raw bank-0 global flags - script files cannot see C
// state, so flags are the only channel. Bank 0 is deliberately exempt from
// the per-run world reset (real story flags live there), which is exactly
// how these used to leak: resolve any NPC event once and the "resolved"
// bit stayed set in the save forever, so every NPC event in every later
// run - and any second NPC event in the same run sharing the script -
// greeted the player with "There's nothing left for you here" (confirmed,
// exactly as the user suspected). Meanwhile nothing ever SET the evil bit,
// so the rupee-stealing variant could never fire at all.
//
// Only one NPC event can be live at a time (one ZELDA per room, one room
// loaded), so the pair is a per-event SCRATCH REGISTER now: loaded from
// the event's own rolled extra when its NPC spawns, and the script's own
// "SetGlobalFlag resolved" is folded back into the event's DONE latch by
// whoever owns one. Scripts 1/2's flag pairs (0x75/0x7d, 0x81/0x89) are
// retired along with the multi-script indexing - script 0 serves every
// event, since the flags are what vary now, not the script.
#define QUICKSTART_NPC_EVIL_FLAG 0x69
#define QUICKSTART_NPC_RESOLVED_FLAG 0x71

static void QuickStartLoadNpcScratchFlags(u8 extra) {
    if (extra & 1) {
        SetGlobalFlag(QUICKSTART_NPC_EVIL_FLAG);
    } else {
        ClearGlobalFlag(QUICKSTART_NPC_EVIL_FLAG);
    }
    ClearGlobalFlag(QUICKSTART_NPC_RESOLVED_FLAG);
}

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
    if (QsCheckRoomFlag(1)) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        if ((gEntities[i].base.kind == OBJECT || gEntities[i].base.kind == ENEMY || gEntities[i].base.kind == NPC) &&
            &gEntities[i].base != gRoomControls.camera_target && QuickStartEntityInCurrentRoom(&gEntities[i].base)) {
            DeleteEntity(&gEntities[i].base);
        }
    }
    QsSetRoomFlag(1);
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
static void QuickStartGetLadderContentOffset(s32 slotIndex, s16* contentX, s16* contentY) {
    s32 rawIndex, poolIndex;
    rawIndex = QuickStartSlotGetRoomIndex(slotIndex);
    if (QuickStartSlotGetPool(slotIndex) == 0) {
        poolIndex = rawIndex % QUICKSTART_SMALL_ROOM_POOL_SIZE;
        *contentX = 0x78 + sQuickStartSmallRoomPool[poolIndex].contentDX;
        *contentY = 0x78 + sQuickStartSmallRoomPool[poolIndex].contentDY;
    } else {
        poolIndex = rawIndex % QUICKSTART_MEDIUM_ROOM_POOL_SIZE;
        *contentX = 0x78 + sQuickStartMediumRoomPool[poolIndex].contentDX;
        *contentY = 0x78 + sQuickStartMediumRoomPool[poolIndex].contentDY;
    }
}

// QS_EVENT_WAVES: a 3-wave gauntlet (one enemy type per wave, per the
// user's own brief), an Ezlo hint the first time a ladder resolves to this
// kind, and a tier draw once all 3 are
// cleared. Room flags used, all distinct from the other kinds' own (they
// never run in the same room at once, so there's no collision reusing low
// numbers): flag 0 = the current wave's enemies have been spawned and at
// least one is still alive; flag 2 = all 3 waves cleared, reward dropped,
// watching for pickup (same flag/meaning QS_EVENT_MINIBOSS uses for its
// own reward-drop state); flag 4 = the one-time hint has been shown; flags
// 5-6 = which wave is in progress, 0-2 (wave 1/2/3).
#define QUICKSTART_WAVE_ROOM_HINT_SHOWN_FLAG 4
#define QUICKSTART_WAVE_ROOM_WAVE_BIT(b) (5 + (b)) // b = 0,1

static u8 QuickStartWaveRoomGetWave(u32 flagBase) {
    return (QsCheckRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(0)) ? 1 : 0) |
           (QsCheckRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(1)) ? 2 : 0);
}

static void QuickStartWaveRoomSetWave(u32 flagBase, u8 wave) {
    if (wave & 1) {
        QsSetRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(0));
    } else {
        QsClearRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(0));
    }
    if (wave & 2) {
        QsSetRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(1));
    } else {
        QsClearRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_WAVE_BIT(1));
    }
}

// Generic surrounding-grid placement, centered on the room's own single
// verified content spot. This file's other multi-enemy spawners
// (QuickStartSpawnEnemyGroup) all use a per-room, individually-walked
// offset table found via a dedicated collision survey instead - the "?
// room" pool's medium/large rooms (POT_MINISH, the Gina room, and the 3
// Dojo rooms) have never had that kind of survey done for a MULTI-enemy
// encounter, only ever a single point for the miniboss/chest/
// NPC kinds above. This is a deliberately conservative placeholder (tight
// to the verified point, not a full room-spanning grid) pending real
// playtesting, and also stands in for the user's own "no more than 1 enemy
// per 4 tiles" density cap until these rooms get their own measured
// squares the way Castle Garden/Melari's Mine/Lon Lon Ranch did earlier.
// Caps how many enemies one wave can ask for. The fixed offset table this
// replaced is gone: it placed enemies at hand-picked pixel offsets with no
// idea what was under them, which is what put a Darknut inside Link's House's
// wall and stacked three of them into adjacent tiles in Grimblade's dojo.
// QuickStartSpawnEnemiesOnOpenTiles finds the ground instead.
#define QUICKSTART_WAVE_ROOM_OFFSET_COUNT 12
// No room in the pool is anywhere near this many tiles across; it only
// bounds the outward scan so a walled-in anchor cannot spin.
#define QUICKSTART_SPAWN_MAX_RING 40

// Is this one of the enemies THIS file spawned, and still alive?
//
// The position test alone is not enough, and the failure is not theoretical:
// traced in Grimblade's dojo, a Wizzrobe's vanish phase teleports it to
// (216,216) in a room that is 240x192 - outside the room's own bounds. Every
// "is the fight over?" check then read it as dead and dropped the reward at
// frame 127 with nobody having touched it, which is the "the wizzrobe
// disappears and the item drops" report exactly.
//
// ENT_PERSIST is the reliable marker: every enemy this file spawns gets it,
// and no vanilla enemy sets it. Position stays as a fallback so anything
// spawned by some other path still counts while it is in the room.
// A Wizzrobe fights by vanishing, so it needs company and it needs to be
// left alone. One on its own spends most of the encounter invisible, which
// is dead time; a group keeps pressure on while any individual is away.
static bool32 QuickStartEnemyIsWizzrobe(u8 id) {
    return id == WIZZROBE_WIND || id == WIZZROBE_FIRE || id == WIZZROBE_ICE;
}

// How many of this miniboss to put in the room. SIX Wizzrobes minimum on
// the user's second call on this ("in the ? room that has wizzrobes, we
// need way more than the 3 we have right now - maybe 6 or more, however
// many the rooms can handle"), climbing with the difficulty counter to ten.
//
// The ceiling is entity budget, not taste. MAX_ENTITIES is 72 for the whole
// game and each Wizzrobe carries a projectile child of its own from Init
// (wizzrobeFire.c) plus another while it is firing, so ten of them is
// around 30 slots - affordable because a miniboss ? room is otherwise an
// empty room (no wave, no props), which is exactly what "however many the
// room can handle" comes out to. Sheet cost stays flat however many spawn:
// they are one kind, and a kind is paid for once. Anything else stays a
// solo fight.
#define QUICKSTART_WIZZROBE_MIN 6
#define QUICKSTART_WIZZROBE_MAX 10
static s32 QuickStartMinibossCount(u8 id) {
    s32 count;
    if (!QuickStartEnemyIsWizzrobe(id)) {
        return 1;
    }
    count = QUICKSTART_WIZZROBE_MIN + QuickStartGetDifficulty() / 2;
    if (count > QUICKSTART_WIZZROBE_MAX) {
        count = QUICKSTART_WIZZROBE_MAX;
    }
    return count;
}

static bool32 QuickStartEnemyIsOurs(Entity* ent) {
    if (ent->kind != ENEMY) {
        return FALSE;
    }
    // The chuchu boss's invisible hitbox-proxy piece (the type-8 spawn)
    // survives the boss's own death sequence parked at health 0 - its
    // delete condition is part of the vanilla arena flow that never runs
    // here. Counting it kept the room reading "enemies present" after
    // every boss kill, which froze the wave loop until the player left
    // and re-entered (measured: core + jelly gone 180 frames after the
    // kill, proxy still there at +900). A dead boss piece is not an
    // enemy for any purpose this predicate serves.
    if (ent->id == CHUCHU_BOSS && ent->health == 0) {
        return FALSE;
    }
    return (ent->flags & ENT_PERSIST) || QuickStartEntityInCurrentRoom(ent);
}

// Holds the GFX reserve after the fact, which is the only point at which
// the true cost is visible (see the QUICKSTART_GFX_RESERVE comment). Run
// every frame from the room monitor: while the table is below the reserve,
// delete our own surplus enemies, FARTHEST FROM THE PLAYER first, so the
// thing that disappears is off-screen rather than the one being fought.
//
// Two safeties. It only ever touches enemies WE spawned
// (QuickStartEnemyIsOurs), never vanilla room content and never the
// player. And it refuses to act at all below a floor of live enemies, so a
// miniboss pack, a wave-room fight or a quest group - all small, all
// deliberately placed - can never be eaten by it; only the big overworld
// density fills are ever trimmed.
//
// One per pass, one pass every 64 frames: deleting an entity does not
// release its slot immediately (the gfx table is reference-counted and
// cleaned up later), so trimming greedily would delete far more than the
// reserve actually needs.
#define QUICKSTART_GFX_REAP_FLOOR 10

// --- Measurement mailbox (F8, docs/QUICKSTART_BUDGET.md) -------------------
//
// A fixed EWRAM mailbox the emulator harness writes, to stage measurement
// scenarios that normal play cannot be steered into on demand: a specific
// boss + escort combination, an uncapped acro pile for the CPU knee.
// 0x0203FF00 sits far above everything the linker places (the last data
// symbol ends at 0x02033A90 and the 4K zMalloc heap at 0x02036540) and is
// guarded by a magic word besides, so in normal play these twelve bytes
// are one inert compare per frame. Layout:
//   +0 u32 magic 0x51534D42 - command pending; cleared when serviced
//   +4 u32 arg0  enemy id | form << 8 | count << 16
//   +8 u32 arg1  x | y << 16 (room-local pixels; 0 = at the player)
// Spawns are raw CreateEnemy calls - deliberately NOT routed through the
// wave spawners, their kind caps or the GFX reserve gates, because the
// whole point of a measurement spawn is to see what those guards would
// have prevented.
#define QUICKSTART_MEASURE_MAILBOX 0x0203FF00
#define QUICKSTART_MEASURE_MAGIC 0x51534D42

static void QuickStartMeasureMailbox(void) {
    vu32* box = (vu32*)QUICKSTART_MEASURE_MAILBOX;
    u32 arg, pos;
    s32 i, count, bx, by;
    if (box[0] != QUICKSTART_MEASURE_MAGIC) {
        return;
    }
    arg = box[1];
    pos = box[2];
    count = (arg >> 16) & 0xFF;
    bx = (pos & 0xFFFF) ? (s32)(pos & 0xFFFF) : (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x);
    by = (pos >> 16) ? (s32)(pos >> 16) : (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y);
    // Command variant: low byte 0xFE spawns a GROUND_ITEM whose item id is
    // the form byte, instead of an enemy - the item-pickup analogue of the
    // raw enemy spawn (added for the food charm/curse probes; usable for
    // any "what does item X do on pickup" measurement).
    if ((arg & 0xFF) == 0xFE) {
        Entity* e = CreateObject(GROUND_ITEM, (arg >> 8) & 0xFF, 0);
        if (e != NULL) {
            e->x.HALF.HI = gRoomControls.origin_x + bx;
            e->y.HALF.HI = gRoomControls.origin_y + by;
            e->collisionLayer = 1;
            e->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(e);
            e->direction = IdleSouth;
        }
        box[0] = 0;
        return;
    }
    for (i = 0; i < count; i++) {
        Entity* e = CreateEnemy(arg & 0xFF, (arg >> 8) & 0xFF);
        if (e != NULL) {
            // A loose grid around the anchor so a pile does not stack on
            // one pixel - overlap changes both AI and collision cost.
            e->x.HALF.HI = gRoomControls.origin_x + bx + ((i & 3) * 24) - 36;
            e->y.HALF.HI = gRoomControls.origin_y + by + ((i >> 2) * 24) - 24;
            e->collisionLayer = 1;
            e->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(e);
        }
    }
    box[0] = 0;
}

static void QuickStartEnforceGfxReserve(void) {
    s32 reaped;
    // Only act on one frame in 64. A deleted entity does not release its
    // gfx slot on the same frame, so an unthrottled reaper keeps reading
    // "still below the reserve" and trims all the way to the floor -
    // measured: North Hyrule Field at difficulty 8 fell from 63 live
    // enemies to 10. Spacing the passes out lets the table settle between
    // them, so it removes what the reserve needs and then stops. 16 frames
    // was still too eager at difficulty 12; 64 leaves the count intact
    // wherever the reserve is already satisfied.
    if ((gRoomTransition.frameCount & 63) != 0) {
        return;
    }
    for (reaped = 0; reaped < 1; reaped++) {
        s32 i, worst = -1, worstDist = -1, ours = 0;
        if (QuickStartFreeGfxSlots() >= QUICKSTART_GFX_RESERVE) {
            return;
        }
        for (i = 0; i < MAX_ENTITIES; i++) {
            Entity* enemy = &gEntities[i].base;
            s32 dx, dy, dist;
            if (!QuickStartEnemyIsOurs(enemy)) {
                continue;
            }
            ours++;
            // Never a live boss piece, never the camera's current target.
            // The boss spawns at the region reward spot - far from
            // wherever the player walked in, i.e. exactly the FARTHEST
            // enemy this loop hunts - and with a live fill pushing 'ours'
            // over the floor, this trimmer ate the whole family one piece
            // per pass, mid-intro (measured: 5 pieces to 0 in 320 frames,
            // the user's NHF report). A deleted intro core also strands
            // gRoomControls.camera_target on a cleared slot at (0,0),
            // which is the black screen half of that report. Setpieces
            // are not density fill; only the fill is ever surplus.
            if (enemy->id == CHUCHU_BOSS || enemy == gRoomControls.camera_target) {
                continue;
            }
            dx = enemy->x.HALF.HI - gPlayerEntity.base.x.HALF.HI;
            dy = enemy->y.HALF.HI - gPlayerEntity.base.y.HALF.HI;
            if (dx < 0) {
                dx = -dx;
            }
            if (dy < 0) {
                dy = -dy;
            }
            dist = dx + dy;
            if (dist > worstDist) {
                worstDist = dist;
                worst = i;
            }
        }
        if (worst < 0 || ours <= QUICKSTART_GFX_REAP_FLOOR) {
            return;
        }
        DeleteEntity(&gEntities[worst].base);
    }
}

// Armor for every camera seizure in the game: if whatever entity the
// camera was following is GONE (its slot cleared - kind 0 marks a freed
// slot), hand the camera back to the player and restore the normal
// scroll speed. A vanilla cutscene always returns the camera itself, but
// anything that deletes the followed entity out from under it - a room
// unload mid-cutscene, a sweep, the (now boss-proof) reserve trimmer -
// left camera_target dangling; measured after the trimmer ate a boss
// core mid-intro, the camera sat aimed at a cleared slot reading
// position (0,0), i.e. panning into the void off the room's corner.
static void QuickStartRescueDanglingCamera(void) {
    Entity* target = gRoomControls.camera_target;
    if (target == NULL || target == &gPlayerEntity.base) {
        return;
    }
    if (target >= &gEntities[0].base && target <= &gEntities[MAX_ENTITIES - 1].base && target->kind != 0) {
        return;
    }
    gRoomControls.camera_target = &gPlayerEntity.base;
    gRoomControls.scrollSpeed = 4;
}

static s32 QuickStartCountRoomEnemies(void) {
    s32 i, count;
    count = 0;
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (QuickStartEnemyIsOurs(&gEntities[i].base)) {
            count++;
        }
    }
    return count;
}

// One enemy TYPE per wave (a single QuickStartPickEnemy roll, not one per
// enemy), scaled up per wave and by the overall difficulty counter, capped
// to this room's own offset-grid size.
// --- Spawning on ground that actually exists ---------------------------
//
// Every enemy spawner in this file used to place entities at fixed pixel
// offsets from a hand-picked spot and hope. That produced exactly the two
// failures the user reported in the Dojos and Link's House: measured in the
// emulator, a 4-enemy wave in Link's House entrance put one of them INSIDE
// the wall block (which reads in play as "trapped in the door"), and in
// Grimblade's dojo it stacked three into adjacent tiles, where they shove
// each other every frame and read as stuttering and glitching around.
//
// A tile is open when its collisionData is 0 - all four quadrants free.
// That is the same test the pot room uses, and it is the portable one:
// actTiles only tracks solidity by luck outside the overworld rooms.
static bool32 QuickStartTileIsOpen(s32 tx, s32 ty) {
    if (tx < 0 || ty < 0 || tx >= (s32)(gRoomControls.width >> 4) || ty >= (s32)(gRoomControls.height >> 4)) {
        return FALSE;
    }
    return GetCollisionDataAtTilePos(TILE_POS(tx, ty), 1) == 0;
}

static s32 QuickStartCountOpenTiles(void) {
    s32 tx, ty, count = 0;
    for (ty = 0; ty < (s32)(gRoomControls.height >> 4); ty++) {
        for (tx = 0; tx < (s32)(gRoomControls.width >> 4); tx++) {
            if (QuickStartTileIsOpen(tx, ty)) {
                count++;
            }
        }
    }
    return count;
}

// Open, and open on all four sides. A Darknut is a full tile wide and walks
// and charges; dropped into a one-tile alcove it spends the fight grinding
// against the walls. Preferred for combat spawns, relaxed only if the room
// cannot supply enough such tiles.
static bool32 QuickStartTileHasElbowRoom(s32 tx, s32 ty) {
    return QuickStartTileIsOpen(tx, ty) && QuickStartTileIsOpen(tx - 1, ty) && QuickStartTileIsOpen(tx + 1, ty) &&
           QuickStartTileIsOpen(tx, ty - 1) && QuickStartTileIsOpen(tx, ty + 1);
}

// Is some other enemy already within `dist` tiles? Doubles as the spacing
// rule and as dedup between the two placement passes, which is why the
// placer needs no record of where it has already put things - the entities
// themselves are the record.
static bool32 QuickStartEnemyNearTile(s32 tx, s32 ty, s32 dist) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s32 ex, ey;
        if (ent->kind != ENEMY || !QuickStartEntityInCurrentRoom(ent)) {
            continue;
        }
        ex = ((ent->x.HALF.HI - gRoomControls.origin_x) >> 4) - tx;
        ey = ((ent->y.HALF.HI - gRoomControls.origin_y) >> 4) - ty;
        if (ex < 0) {
            ex = -ex;
        }
        if (ey < 0) {
            ey = -ey;
        }
        if (ex <= dist && ey <= dist) {
            return TRUE;
        }
    }
    return FALSE;
}

// Nearest open tile to a room-local spot, returned as a tile centre. Same
// ring scan as the placer, without creating anything.
static bool32 QuickStartFindOpenTileNear(s32 anchorX, s32 anchorY, s32 spacing, s16* outX, s16* outY) {
    s32 anchorTX = anchorX >> 4;
    s32 anchorTY = anchorY >> 4;
    s32 ring;
    for (ring = 0; ring < QUICKSTART_SPAWN_MAX_RING; ring++) {
        s32 dx, dy;
        for (dy = -ring; dy <= ring; dy++) {
            for (dx = -ring; dx <= ring; dx++) {
                if (dx != -ring && dx != ring && dy != -ring && dy != ring) {
                    continue;
                }
                if (QuickStartTileIsOpen(anchorTX + dx, anchorTY + dy) &&
                    !QuickStartEnemyNearTile(anchorTX + dx, anchorTY + dy, spacing)) {
                    *outX = (s16)((anchorTX + dx) * 16 + 8);
                    *outY = (s16)((anchorTY + dy) * 16 + 8);
                    return TRUE;
                }
            }
        }
    }
    return FALSE;
}

// The synthetic entrance every 2-door pool room shares is the literal
// constant (100,100), which was never measured against any of them - it just
// happens to be floor in most. In Dark Hyrule Castle's bridge room it is
// not: that room is a 3-tile-wide walkway running down the middle of a void,
// and (100,100) is tile (6,6), collision 0x0f, one tile off the west edge.
// The player and the room's content both materialised in the gap beside the
// bridge, which is the "spawns in midair with no ground beneath them"
// report.
//
// Rather than measure an entrance for each of the twenty pool rooms and get
// it wrong again, arrival is corrected against the room's own collision:
// anything standing on a solid tile is moved to the nearest open one. Once
// per room entry, and never mid-transition.
#define QUICKSTART_PLAYER_RESCUED_FLAG 51
static void QuickStartRescuePlayerOntoGround(void) {
    s16 localX, localY, safeX, safeY;
    if (gRoomTransition.transitioningOut || QsCheckRoomFlag(QUICKSTART_PLAYER_RESCUED_FLAG)) {
        return;
    }
    localX = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
    localY = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
    QsSetRoomFlag(QUICKSTART_PLAYER_RESCUED_FLAG);
    if (QuickStartTileIsOpen(localX >> 4, localY >> 4)) {
        return;
    }
    if (QuickStartFindOpenTileNear(localX, localY, 1, &safeX, &safeY)) {
        gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + safeX;
        gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + safeY;
    }
}

// Places up to `count` enemies on distinct, open, spaced-out tiles, scanning
// outward in Chebyshev rings from the requested spot so they cluster around
// where the event wanted them without ever landing in a wall.
//
// Two passes: the first insists on elbow room and two tiles of separation,
// the second (only reached if the room is too cramped to supply that) takes
// any open tile one clear of its neighbours. Small rooms therefore still
// fill, they just fill tighter. Returns how many actually went down.
// The ring search is deliberately wide - QUICKSTART_SPAWN_MAX_RING is 40,
// larger than any room - because several hand-placed content spots are
// simply wrong and this is what rescues them.
//
// That is exactly wrong in a room that holds more than one site. The
// relax==0 pass scans all 40 rings looking for elbow room before relax==1
// tries anything, so a strict tile thirty rings away beats a merely-open
// tile next to the anchor. In Goron Cave, whose four chambers are stacked
// in one 15x45 shaft, that put all four stages' minibosses in the top
// chamber on a single tile - measured: four separate entities, each
// carrying its own site's roll, all at the last row's spot.
//
// `ownerSite` fixes it with the rule the pot lottery already uses: a tile
// belongs to whichever site in this room is nearest to it, so the search
// can range as far as it likes and still never cross into another site's
// half of the room. Pass -1 to opt out (the wave, quest and 2-door
// spawners, none of which belong to a site). In a single-site room the test
// is always true, so nothing about the old behaviour changes.
static s32 QuickStartSpawnEnemiesOnOpenTiles(u8 id, u8 form, s32 anchorX, s32 anchorY, s32 count, s32 ownerSite) {
    s32 anchorTX = anchorX >> 4;
    s32 anchorTY = anchorY >> 4;
    s32 relax, ring, placed = 0;
    for (relax = 0; relax < 2 && placed < count; relax++) {
        for (ring = 0; ring < QUICKSTART_SPAWN_MAX_RING && placed < count; ring++) {
            s32 dx, dy;
            for (dy = -ring; dy <= ring; dy++) {
                for (dx = -ring; dx <= ring; dx++) {
                    s32 tx, ty;
                    Entity* enemy;
                    if (dx != -ring && dx != ring && dy != -ring && dy != ring) {
                        continue;
                    }
                    if (placed >= count) {
                        return placed;
                    }
                    tx = anchorTX + dx;
                    ty = anchorTY + dy;
                    if (relax == 0 ? !QuickStartTileHasElbowRoom(tx, ty) : !QuickStartTileIsOpen(tx, ty)) {
                        continue;
                    }
                    if (!QuickStartTileBelongsToSite(tx, ty, ownerSite)) {
                        continue;
                    }
                    if (QuickStartEnemyNearTile(tx, ty, relax == 0 ? 2 : 1)) {
                        continue;
                    }
                    // Same GFX reserve every other spawner honours - a
                    // miniboss pack or a quest group must not be what
                    // fills the last slots.
                    if (!QuickStartGfxBudgetForSpawn()) {
                        return placed;
                    }
                    // The gang cap (QuickStartAcroBanditCapReached). This
                    // placer is single-kind, so there is nothing to swap
                    // to - a capped acro group just stops here, and the
                    // two gangs it did place are 12 entities once burst,
                    // a full-sized fight already.
                    if (id == ACRO_BANDIT && QuickStartAcroBanditCapReached()) {
                        return placed;
                    }
                    enemy = CreateEnemy(id, form);
                    if (enemy == NULL) {
                        return placed;
                    }
                    enemy->x.HALF.HI = gRoomControls.origin_x + tx * 16 + 8;
                    enemy->y.HALF.HI = gRoomControls.origin_y + ty * 16 + 8;
                    enemy->collisionLayer = 1;
                    enemy->flags |= ENT_PERSIST;
                    UpdateSpriteForCollisionLayer(enemy);
                    placed++;
                }
            }
        }
    }
    return placed;
}

static void QuickStartSpawnWave(s32 contentX, s32 contentY, u8 wave, u8 difficulty) {
    u8 id, form;
    s32 i, count;
    QuickStartPickEnemy(difficulty, &id, &form);
    // Single-kind spawn + the gang cap = a capped acro pick would place
    // nothing and the empty wave would read as instantly cleared. Trade
    // the pick for a beetle instead of consuming another Random() so the
    // RNG stream stays put.
    if (id == ACRO_BANDIT && QuickStartAcroBanditCapReached()) {
        id = BEETLE;
        form = 0;
    }
    count = 4 + difficulty / 2 + wave * 2;
    if (count > QUICKSTART_WAVE_ROOM_OFFSET_COUNT) {
        count = QUICKSTART_WAVE_ROOM_OFFSET_COUNT;
    }
    QuickStartSpawnEnemiesOnOpenTiles(id, form, contentX, contentY, count, -1);
}

// --- Why a wave gauntlet in the Grimblade dojo could never be finished ---
//
// Rooms inside one area share a pixel grid, and two rooms whose rectangles
// touch along an edge are joined by a SCROLL SEAM: the player crosses by
// walking, with no door and no fade. The engine wipes gRoomVars.flags on the
// way across - and gRoomVars.flags is where every "? room" event keeps its
// per-visit state.
//
// Measured live: ROOM_DOJOS_GRIMBLADE is 240x192 at (1280,0) and its ante
// room (ROOM_DOJOS_TO_GRIMBLADE, where the ladder from Castle Garden comes
// up) is 240x160 directly below it at (1280,192). Walking south from the
// arena floor crosses in 43 frames, and a room flag set before the crossing
// reads back as 0 both in the ante room and on returning.
//
// For a wave gauntlet that is fatal. Back up 24px during a fight and come
// forward again and the "this wave is already spawned" latch AND the wave
// counter are both gone, so the room spawns a fresh wave 1 on top of every
// enemy still alive. Do it a few times and the arena fills with more enemies
// than can be cleared - the user's "impossible to kill all of the enemies".
//
// tools/quickstart/seam_audit.py enumerates this from gAreaRoomHeaders:
// five QUICKSTART rooms have a seam, and Grimblade is the only one that
// hosts combat, which is why only it was reported.
//
// The fix keeps the gauntlet's own state outside the room flags, in
// FLAG_BANK_11, tagged with the room it belongs to. Only one gauntlet can be
// in progress at a time, so one record is enough. A seam crossing no longer
// resets anything: the fight simply carries on.
#define GF_SEAM_GAUNTLET_LIVE 43
#define GF_SEAM_GAUNTLET_AREA_BIT(b) (44 + (b)) // b = 0..6
#define GF_SEAM_GAUNTLET_ROOM_BIT(b) (51 + (b)) // b = 0..4
#define GF_SEAM_GAUNTLET_WAVE_BIT(b) (56 + (b)) // b = 0..1
// Separate from LIVE on purpose. LIVE means "a gauntlet is running in the
// recorded room"; SPAWNED means "the wave it is on has had its enemies
// created". Between clearing a wave and spawning the next there is one frame
// where the gauntlet is live but nothing is out - folding the two together
// would lose the wave counter in exactly that frame if the player happened
// to cross the seam during it.
#define GF_SEAM_GAUNTLET_SPAWNED 58

static void QuickStartGauntletWriteBits(s32 base, s32 count, u32 value) {
    s32 b;
    for (b = 0; b < count; b++) {
        if (value & (1 << b)) {
            SetLocalFlagByBank(FLAG_BANK_11, base + b);
        } else {
            ClearLocalFlagByBank(FLAG_BANK_11, base + b);
        }
    }
}

static u32 QuickStartGauntletReadBits(s32 base, s32 count) {
    s32 b;
    u32 value = 0;
    for (b = 0; b < count; b++) {
        if (CheckLocalFlagByBank(FLAG_BANK_11, base + b)) {
            value |= (1 << b);
        }
    }
    return value;
}

// Is the live gauntlet record this room's? Room ids only reach 15 in the
// areas that host events, so five bits is ample.
static bool32 QuickStartGauntletIsHere(void) {
    return CheckLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_LIVE) != 0 &&
           QuickStartGauntletReadBits(GF_SEAM_GAUNTLET_AREA_BIT(0), 7) == gRoomControls.area &&
           QuickStartGauntletReadBits(GF_SEAM_GAUNTLET_ROOM_BIT(0), 5) == gRoomControls.room;
}

static void QuickStartGauntletRemember(u8 wave, bool32 spawned) {
    SetLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_LIVE);
    QuickStartGauntletWriteBits(GF_SEAM_GAUNTLET_AREA_BIT(0), 7, gRoomControls.area);
    QuickStartGauntletWriteBits(GF_SEAM_GAUNTLET_ROOM_BIT(0), 5, gRoomControls.room);
    QuickStartGauntletWriteBits(GF_SEAM_GAUNTLET_WAVE_BIT(0), 2, wave);
    if (spawned) {
        SetLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_SPAWNED);
    } else {
        ClearLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_SPAWNED);
    }
}

static void QuickStartGauntletForget(void) {
    ClearLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_LIVE);
    ClearLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_SPAWNED);
}

// The other half of the seam problem: enemies chase, and the seam is open,
// so a wave walks itself out of the arena and camps the ante room. They
// still COUNT (QuickStartEnemyIsOurs matches on ENT_PERSIST, not on room
// bounds), so the gauntlet stalls with nothing visible left to kill.
//
// Same leash the miniboss kind already puts on a Wizzrobe that teleports
// out of bounds, generalized: anything of ours that is outside the room gets
// snapped back to open ground near the event. Only ever called while the
// monitor is on the event's own room, so "outside the room" cannot mean
// "the player walked away and the enemy is legitimately elsewhere".
static void QuickStartLeashStrayEnemies(s32 contentX, s32 contentY) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* enemy = &gEntities[i].base;
        s16 backX, backY;
        if (!QuickStartEnemyIsOurs(enemy) || QuickStartEntityInCurrentRoom(enemy)) {
            continue;
        }
        if (QuickStartFindOpenTileNear(contentX, contentY, 1, &backX, &backY)) {
            enemy->x.HALF.HI = gRoomControls.origin_x + backX;
            enemy->y.HALF.HI = gRoomControls.origin_y + backY;
        }
    }
}

// Defined just below, with the rest of the handicap; declared here because
// the stripped-kit gauntlet variant is applied and undone from inside the
// wave state machine.
static u8 QuickStartHandicapApply(void);
static void QuickStartHandicapRestore(void);
// Defined at the bottom of the file, next to the charm pickup hook that
// collision.c also reaches through.
u8 QuickStartCharmMask(void);

// Returns TRUE once the room's payoff has been collected, i.e. "this event
// is finished, never spawn it again" - the caller owns the actual done
// latch, because the two callers store it in different places (a retired
// ladder/door slot vs. a content site's own GF_CONTENT_SITE_DONE bit).
static bool32 QuickStartSetupWaveRoomContent(s32 extra, s32 contentX, s32 contentY, u32 flagBase) {
    u8 wave, difficulty;
    if (QsCheckRoomFlag(flagBase + 2)) {
        // All 3 waves cleared, reward already dropped - watch for the
        // pickup. Same "gone is not the same as taken" rule as the item-drop
        // kind above: if the player is not standing where it was, the item
        // was removed rather than collected, so put it back.
        if (QuickStartGroundItemAt(contentX, contentY)) {
            return FALSE;
        }
        if (QuickStartPlayerNearSpot(contentX, contentY)) {
            return TRUE;
        }
        QsClearRoomFlag(flagBase + 2);
        return FALSE;
    }
    if (!QsCheckRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_HINT_SHOWN_FLAG)) {
        QsSetRoomFlag(flagBase + QUICKSTART_WAVE_ROOM_HINT_SHOWN_FLAG);
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 9), 0);
    }
    difficulty = QuickStartGetDifficulty();
    // The seam record outranks the room flags, because the room flags are
    // exactly what a seam crossing destroys. When it is this room's, it is
    // both the wave counter AND the "already spawned" latch; the room flags
    // are still written below so a room without a seam behaves identically
    // whether or not the record survives.
    if (QuickStartGauntletIsHere()) {
        wave = (u8)QuickStartGauntletReadBits(GF_SEAM_GAUNTLET_WAVE_BIT(0), 2);
        QuickStartWaveRoomSetWave(flagBase, wave);
        if (CheckLocalFlagByBank(FLAG_BANK_11, GF_SEAM_GAUNTLET_SPAWNED)) {
            QsSetRoomFlag(flagBase + 0);
        } else {
            QsClearRoomFlag(flagBase + 0);
        }
    } else {
        wave = QuickStartWaveRoomGetWave(flagBase);
    }
    if (QsCheckRoomFlag(flagBase + 0)) {
        // This wave's enemies are still out there somewhere - possibly
        // literally, if they chased the player over a seam, so haul them
        // back before deciding the wave is clear.
        QuickStartLeashStrayEnemies(contentX, contentY);
        if (QuickStartCountRoomEnemies() > 0) {
            return FALSE;
        }
        // Cleared.
        if (wave >= 2) {
            // That was wave 3 - drop the reward and start watching for
            // pickup (same reward pool a chest room draws from, so a wave
            // room's payoff has the same variety instead of a single fixed
            // item).
            u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) never become a floor
            // entity, so the test is "was it delivered", not "does an
            // entity exist" - see QuickStartSpawnRewardEntity.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(flagBase + 2);
                QuickStartGauntletForget();
                // Kit back before the reward is picked up, so a stripped-kit
                // gauntlet's payout lands in a full inventory.
                QuickStartHandicapRestore();
            }
            return FALSE;
        }
        // Advance to the next wave - QsClearRoomFlag(flagBase + 0) lets the fallthrough
        // below spawn it on the next frame.
        QuickStartWaveRoomSetWave(flagBase, wave + 1);
        QsClearRoomFlag(flagBase + 0);
        QuickStartGauntletRemember(wave + 1, FALSE);
        return FALSE;
    }
    // Extra bit 6 makes this a stripped-kit gauntlet. Applied on the way into
    // wave 1 only - QuickStartHandicapApply is idempotent, but taking the
    // snapshot once is what makes "give it all back" mean the right thing.
    // The kit comes back when the reward drops (above) or the moment the
    // player leaves the room (QuickStartHandicapMonitor), so there is no way
    // to end up permanently stripped.
    if ((extra & 0x40) && wave == 0) {
        QuickStartHandicapApply();
    }
    QuickStartSpawnWave(contentX, contentY, wave, difficulty);
    QsSetRoomFlag(flagBase + 0);
    QuickStartGauntletRemember(wave, TRUE);
    return FALSE;
}

// ======================= The handicap ==================================
//
// "Take away all of the player's items, buffs and upgrades and leave them
// with ONE weapon" - used by the hunt quest below and, as a rarer variant,
// by the ? room wave gauntlet. Everything comes back afterwards whether the
// challenge is won or lost.
//
// WHERE THE SNAPSHOT LIVES. game.o gets no .bss or .data (linker.ld is an
// absolute NOLOAD layout), so there is nowhere in this file to put one. It
// goes in gSave instead, in the three u32s the engine itself documents as
// unused - "timer4", "timer5", "timer6" (save.h). They are already saved,
// restored and zeroed with everything else, which is exactly the lifetime a
// snapshot needs, and nothing anywhere in the tree reads them.
//
//   timer5 - one bit per entry of sQuickStartHandicapItems that was owned
//            and has been taken. That is why the list is capped at 32.
//   timer6 - equipped[0] | equipped[1] << 8 | equippedExtra[0] << 16 |
//            charm mask << 24. The three equip slots have to be saved
//            because taking the item out from under them leaves the HUD
//            pointing at something the player no longer has.
//   timer4 - the hunt's own countdown, in frames. Not part of the snapshot.
//
// WHAT IS NOT TAKEN: bomb and arrow COUNTS. Zeroing the item is already
// enough to make a weapon unusable, so the counts can be left alone, which
// saves two bytes of snapshot and one class of bug. The kept weapon is
// topped up to a working supply instead - see QuickStartHandicapApply.
#define QUICKSTART_HANDICAP_AMMO 30

// Which room the handicap belongs to, so that walking out of it gives the
// player their kit back rather than stranding them stripped for the run.
// FLAG_BANK_11 again, straight after the seam-gauntlet record.
#define GF_HANDICAP_ACTIVE 59
#define GF_HANDICAP_AREA_BIT(b) (60 + (b)) // b = 0..6
#define GF_HANDICAP_ROOM_BIT(b) (67 + (b)) // b = 0..4

// The kit. Everything here is either a weapon, a tool, a movement upgrade or
// a learned sword skill - i.e. everything the player has EARNED this run.
// Deliberately absent: the Kinstone Bag and Wallet (bookkeeping, taking them
// would strand rupees and pieces), bottles (a bottled fairy is a life, and
// taking lives away is a different and much crueller mechanic than taking
// weapons away), and the Lon Lon key.
//
// Order matters only in that it is the bit order of the timer5 snapshot, so
// rows must never be reordered or removed without clearing that word - which
// GameTask_Transition does at every run boundary anyway.
static const u8 sQuickStartHandicapItems[] = {
    ITEM_SMITH_SWORD,       ITEM_RED_SWORD,         ITEM_BOMBS,            ITEM_REMOTE_BOMBS,
    ITEM_BOW,               ITEM_LIGHT_ARROW,       ITEM_BOOMERANG,        ITEM_MAGIC_BOOMERANG,
    ITEM_SHIELD,            ITEM_MIRROR_SHIELD,     ITEM_LANTERN_OFF,      ITEM_GUST_JAR,
    ITEM_PACCI_CANE,        ITEM_MOLE_MITTS,        ITEM_ROCS_CAPE,        ITEM_PEGASUS_BOOTS,
    ITEM_FIRE_ROD,          ITEM_OCARINA,           ITEM_GRIP_RING,        ITEM_POWER_BRACELETS,
    ITEM_FLIPPERS,          ITEM_SKILL_SPIN_ATTACK, ITEM_SKILL_ROLL_ATTACK, ITEM_SKILL_DASH_ATTACK,
    ITEM_SKILL_ROCK_BREAKER, ITEM_SKILL_SWORD_BEAM, ITEM_SKILL_GREAT_SPIN, ITEM_SKILL_DOWN_THRUST,
    ITEM_SKILL_PERIL_BEAM,  ITEM_BOMBBAG,           ITEM_LARGE_QUIVER,
};
#define QUICKSTART_HANDICAP_ITEM_COUNT 31

// The four weapons a handicap may leave you with, in the order the roll
// indexes them.
static const u8 sQuickStartHandicapWeapons[] = {
    ITEM_SMITH_SWORD,
    ITEM_BOMBS,
    ITEM_BOW,
    ITEM_FIRE_ROD,
};

static bool32 QuickStartHandicapActive(void) {
    return CheckLocalFlagByBank(FLAG_BANK_11, GF_HANDICAP_ACTIVE) != 0;
}

// Which weapon this run's handicap challenges leave behind. Rolled fresh at
// the moment the handicap is applied rather than at run start, because it
// has to be something the player actually owns - a "bombs only" challenge
// handed to a run that never found bombs is not hard, it is unplayable.
// Falls back to the sword, which every run has.
static u8 QuickStartHandicapPickWeapon(void) {
    s32 i;
    s32 roll = (s32)Random() % 4;
    for (i = 0; i < 4; i++) {
        u8 item = sQuickStartHandicapWeapons[(roll + i) % 4];
        if (GetInventoryValue(item) != 0) {
            return item;
        }
    }
    return ITEM_SMITH_SWORD;
}

static u8 QuickStartHandicapApply(void) {
    u8 kept = QuickStartHandicapPickWeapon();
    u32 taken = 0;
    s32 i;
    if (QuickStartHandicapActive()) {
        return kept; // already stripped; never snapshot on top of a snapshot
    }
    gSave.timer6 = (u32)gSave.stats.equipped[0] | ((u32)gSave.stats.equipped[1] << 8) |
                   ((u32)gSave.stats.equippedExtra[0] << 16) | ((u32)QuickStartCharmMask() << 24);
    for (i = 0; i < QUICKSTART_HANDICAP_ITEM_COUNT; i++) {
        u8 item = sQuickStartHandicapItems[i];
        if (item == kept) {
            continue;
        }
        if (GetInventoryValue(item) != 0) {
            taken |= (1u << i);
            SetInventoryValue(item, 0);
        }
    }
    gSave.timer5 = taken;
    // Charms are ours, not vanilla's, so they are suspended by clearing our
    // own ownership bits (CalculateDamage reads QuickStartCharmMask) and the
    // vanilla byte GetPlayerPalette tints from.
    for (i = 0; i < 3; i++) {
        ClearLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(i));
    }
    gSave.stats.charm = 0;
    // Put the one weapon where the player's hands already are. A stripped
    // kit with nothing on A or B reads as a bug, not as a challenge.
    gSave.stats.equipped[0] = kept;
    gSave.stats.equipped[1] = kept;
    gSave.stats.equippedExtra[0] = ITEM_NONE;
    // Ammo, for the two weapons that need it. Not clawed back afterwards:
    // that would need two more bytes of snapshot to know what to claw back
    // to, and leaving the player a few spare bombs is a fair trade for
    // having taken everything else.
    if (kept == ITEM_BOMBS && gSave.stats.bombCount < QUICKSTART_HANDICAP_AMMO) {
        ModBombs(QUICKSTART_HANDICAP_AMMO - gSave.stats.bombCount);
    }
    if (kept == ITEM_BOW && gSave.stats.arrowCount < QUICKSTART_HANDICAP_AMMO) {
        ModArrows(QUICKSTART_HANDICAP_AMMO - gSave.stats.arrowCount);
    }
    SetLocalFlagByBank(FLAG_BANK_11, GF_HANDICAP_ACTIVE);
    QuickStartGauntletWriteBits(GF_HANDICAP_AREA_BIT(0), 7, gRoomControls.area);
    QuickStartGauntletWriteBits(GF_HANDICAP_ROOM_BIT(0), 5, gRoomControls.room);
    return kept;
}

static void QuickStartHandicapRestore(void) {
    u32 taken = gSave.timer5;
    u32 slots = gSave.timer6;
    s32 i;
    if (!QuickStartHandicapActive()) {
        return;
    }
    for (i = 0; i < QUICKSTART_HANDICAP_ITEM_COUNT; i++) {
        if (taken & (1u << i)) {
            SetInventoryValue(sQuickStartHandicapItems[i], 1);
        }
    }
    for (i = 0; i < 3; i++) {
        if ((slots >> 24) & (1u << i)) {
            SetLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(i));
            // Any one of them will do for the tint; the real effect comes
            // from the mask, and vanilla only has room for one.
            gSave.stats.charm = BOTTLE_CHARM_NAYRU + i;
        }
    }
    gSave.stats.equipped[0] = (u8)(slots & 0xff);
    gSave.stats.equipped[1] = (u8)((slots >> 8) & 0xff);
    gSave.stats.equippedExtra[0] = (u8)((slots >> 16) & 0xff);
    gSave.timer5 = 0;
    gSave.timer6 = 0;
    ClearLocalFlagByBank(FLAG_BANK_11, GF_HANDICAP_ACTIVE);
}

// Run every frame from the room monitor. The one job is the safety net:
// a handicap belongs to the room that applied it, so leaving that room -
// by any route, including dying - hands the kit straight back. Without it a
// player who walks out of a stripped-kit fight spends the rest of the run
// with one weapon and no way to get the rest back.
static void QuickStartHandicapMonitor(void) {
    if (!QuickStartHandicapActive()) {
        return;
    }
    if (QuickStartGauntletReadBits(GF_HANDICAP_AREA_BIT(0), 7) != gRoomControls.area ||
        QuickStartGauntletReadBits(GF_HANDICAP_ROOM_BIT(0), 5) != gRoomControls.room) {
        QuickStartHandicapRestore();
    }
}

// ======================= The hunt quest ================================
//
// One giver per run, standing in one region of the chain. Talk to it and a
// pack of enemies appears with a clock; kill them all before it runs out and
// it pays. Miss and the giver leaves for good - one attempt per run, per the
// user's brief.
//
// The clock is drawn in the HUD's key slot (DrawKeys, ui.c): QUICKSTART has
// no dungeons and therefore never any small keys, so that counter, its BG0
// cells and its digit tiles are all sitting idle and already wired.
//
// Telling hunt enemies apart from the region's own endless waves matters,
// because both are in the same room at the same time. They are marked with
// enemyFlags bit 7, the one bit of that field vanilla never defines (enemy.h
// stops at EM_FLAG_MONITORED, 1 << 6).
#define QUICKSTART_EM_FLAG_HUNT (1 << 7)
// Two digits is what the key counter draws, so the limit has to stay under
// 100 seconds. 45 is enough to cross most of a region and fight, and short
// enough that dawdling loses.
#define QUICKSTART_HUNT_SECONDS 30
#define QUICKSTART_HUNT_FRAMES (QUICKSTART_HUNT_SECONDS * 60)
// Pack size, rebalanced with the clock (the user, Aug 2026: "we need both
// a shorter timer and more enemies"). 4-8 in 45 seconds was ~7 seconds per
// kill, which no wave enemy survives - the clock never ran out. 7-13 in 30
// seconds is ~4 seconds per kill at the low end and ~2.3 at the high, so
// the pack has to be fought efficiently rather than picked apart. The
// ceiling stays inside the entity budget: the pack is ONE kind (one GFX
// sheet, the measured-cheap many-instances shape) and shares the room with
// whatever the region's own wave left standing, and MAX_ENTITIES is 72.
// 7 + difficulty/2 walks the range and lands exactly on the ceiling at
// QUICKSTART_MAX_DIFFICULTY, so the clamp below is a guard, not the curve.
#define QUICKSTART_HUNT_MIN_ENEMIES 7
#define QUICKSTART_HUNT_MAX_ENEMIES 13

#define GF_HUNT_ROLLED 74
// (75-76 free - the old 2-bit hunt chain-slot field. The hunt's host region
// is the 4-bit QS-window GF_REGION_HUNT_HOST_BIT field now.)
#define GF_HUNT_SPOT_BIT(b) (77 + (b))  // b = 0..4, index into the region's own offsets
#define GF_HUNT_HANDICAP 82             // this run's hunt is the stripped-kit variant
#define GF_HUNT_STATE_BIT(b) (83 + (b)) // b = 0..1
#define QUICKSTART_HUNT_OFFERED 0
#define QUICKSTART_HUNT_RUNNING 1
#define QUICKSTART_HUNT_WON 2
#define QUICKSTART_HUNT_FAILED 3

static s32 QuickStartHuntState(void) {
    return (s32)QuickStartGauntletReadBits(GF_HUNT_STATE_BIT(0), 2);
}

static void QuickStartHuntSetState(s32 state) {
    QuickStartGauntletWriteBits(GF_HUNT_STATE_BIT(0), 2, (u32)state);
}

// One draw per run, from the region monitor like every other per-run draw.
// One in three hunts is the handicap variant - uncommon enough to be a
// surprise, common enough to be worth building.
static void QuickStartHuntRollOnce(void) {
    if (CheckLocalFlagByBank(FLAG_BANK_11, GF_HUNT_ROLLED)) {
        return;
    }
    {
        // Pool index, 4-bit QS-window field - same widening as the pot
        // quest's region draw above.
        s32 huntRegion = (s32)Random() % QUICKSTART_REGION_POOL_SIZE;
        s32 b;
        for (b = 0; b < 4; b++) {
            if (huntRegion & (1 << b)) {
                QsSetFlag(GF_REGION_HUNT_HOST_BIT(b));
            }
        }
    }
    QuickStartGauntletWriteBits(GF_HUNT_SPOT_BIT(0), 5, (u32)((s32)Random() % 32));
    if ((s32)Random() % 3 == 0) {
        SetLocalFlagByBank(FLAG_BANK_11, GF_HUNT_HANDICAP);
    }
    QuickStartHuntSetState(QUICKSTART_HUNT_OFFERED);
    SetLocalFlagByBank(FLAG_BANK_11, GF_HUNT_ROLLED);
}

// Where the giver stands. The region's own enemy-offset table is used for
// the same reason the pot quest uses it: every entry is a pre-verified
// walkable spot in that room, already filtered for item-gated zones by
// QuickStartPositionAllowed. Walks forward from the rolled index so a
// blocked spot falls through to the next rather than dropping the quest.
static bool32 QuickStartHuntSpot(const QuickStartRegion* region, s16* outX, s16* outY) {
    s32 i;
    s32 start;
    if (region->enemyOffsetCount <= 0) {
        return FALSE;
    }
    start = (s32)QuickStartGauntletReadBits(GF_HUNT_SPOT_BIT(0), 5) % region->enemyOffsetCount;
    for (i = 0; i < region->enemyOffsetCount; i++) {
        s32 idx = (start + i) % region->enemyOffsetCount;
        s16 x = region->enemyOffsets[idx][0];
        s16 y = region->enemyOffsets[idx][1];
        if (QuickStartPositionAllowed(x, y)) {
            *outX = x;
            *outY = y;
            return TRUE;
        }
    }
    return FALSE;
}

static s32 QuickStartCountHuntEnemies(void) {
    s32 i, count = 0;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY && (((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
            count++;
        }
    }
    return count;
}

static void QuickStartHuntClearPack(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY && (((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
            DeleteEntity(ent);
        }
    }
}

// The pack. One enemy type, at the run's difficulty plus a tier - a hunt is
// meant to be a step up from the wave the player is already fighting - and
// placed through the normal open-tile placer around the giver, so the fight
// starts where the conversation did rather than somewhere across the map.
static void QuickStartHuntSpawnPack(s16 spotX, s16 spotY) {
    u8 id, form;
    s32 count, i;
    QuickStartPickEnemy(QuickStartGetDifficulty() + 2, &id, &form);
    // Same capped-acro substitution as QuickStartSpawnWave: an empty pack
    // would hand the hunt an instant win.
    if (id == ACRO_BANDIT && QuickStartAcroBanditCapReached()) {
        id = BEETLE;
        form = 0;
    }
    count = QUICKSTART_HUNT_MIN_ENEMIES + QuickStartGetDifficulty() / 2;
    if (count > QUICKSTART_HUNT_MAX_ENEMIES) {
        count = QUICKSTART_HUNT_MAX_ENEMIES;
    }
    // Marked after the fact rather than by the placer, which has no idea what
    // it is placing for. Anything unmarked in the room at this instant is a
    // wave enemy and stays that way, so the two sets never mix.
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY) {
            ((Enemy*)ent)->enemyFlags &= ~QUICKSTART_EM_FLAG_HUNT;
        }
    }
    QuickStartSpawnEnemiesOnOpenTiles(id, form, spotX, spotY, count, -1);
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY && ent->id == id && ent->type == form &&
            !(((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
            ((Enemy*)ent)->enemyFlags |= QUICKSTART_EM_FLAG_HUNT;
        }
    }
}

// Seconds left, or -1 when no hunt is running. ui.c's DrawKeys reads this
// every frame to decide whether the key slot shows a clock.
s32 QuickStartHuntSecondsLeft(void) {
    // The scavenger hunt shares the clock, so the key slot shows it for
    // whichever of the two timed quests is running.
    if ((QuickStartHuntState() != QUICKSTART_HUNT_RUNNING && QuickStartScavState() != QUICKSTART_SCAV_RUNNING) ||
        gSave.timer4 == 0) {
        return -1;
    }
    // Round up, so the last second is shown as 1 rather than 0. Signed on
    // purpose: agbcc turns a division by a signed constant into shifts, but
    // emits __udivsi3 - which its runtime lib does not provide - for the
    // unsigned form, and gSave.timer4 is a u32.
    return ((s32)gSave.timer4 + 59) / 60;
}

// --- The three script hooks (data/scripts/quickstart/script_QuickStartHunt.inc)
//
// ScriptCommand_Call invokes its target as (Entity*, ScriptExecutionContext*)
// and the target answers a JumpIf by writing context->condition, which is why
// these take the pair rather than returning a value.
void QuickStartHuntCanStart(Entity* entity, ScriptExecutionContext* context) {
    // The scavenger hunt shares the HUD clock (gSave.timer4) and the enemy
    // mark bit, so neither quest may start while the other is running.
    context->condition =
        (QuickStartHuntState() == QUICKSTART_HUNT_OFFERED) && (QuickStartScavState() != QUICKSTART_SCAV_RUNNING);
}

void QuickStartHuntIsHandicap(Entity* entity, ScriptExecutionContext* context) {
    context->condition = CheckLocalFlagByBank(FLAG_BANK_11, GF_HUNT_HANDICAP) != 0;
}

void QuickStartHuntBegin(Entity* entity, ScriptExecutionContext* context) {
    if (QuickStartHuntState() != QUICKSTART_HUNT_OFFERED) {
        return;
    }
    if (CheckLocalFlagByBank(FLAG_BANK_11, GF_HUNT_HANDICAP)) {
        QuickStartHandicapApply();
    }
    QuickStartHuntSpawnPack(entity->x.HALF.HI - gRoomControls.origin_x, entity->y.HALF.HI - gRoomControls.origin_y);
    gSave.timer4 = QUICKSTART_HUNT_FRAMES;
    QuickStartHuntSetState(QUICKSTART_HUNT_RUNNING);
    SoundReq(SFX_SECRET);
}

// Called every frame from QuickStartRegionMonitor for the hosting slot.
static void QuickStartHuntMonitor(const QuickStartRegion* region, s32 slot) {
    s32 state;
    s16 spotX, spotY;
    QuickStartHuntRollOnce();
    {
        s32 b, huntRegion = 0;
        for (b = 0; b < 4; b++) {
            if (QsCheckFlag(GF_REGION_HUNT_HOST_BIT(b))) {
                huntRegion |= (1 << b);
            }
        }
        if (slot != huntRegion) {
            return;
        }
    }
    state = QuickStartHuntState();
    if (state == QUICKSTART_HUNT_RUNNING) {
        if (QuickStartCountHuntEnemies() == 0) {
            // Won. The handicap comes off first, so the reward lands in a
            // full kit rather than being picked up by a stripped one.
            QuickStartHandicapRestore();
            QuickStartHuntSetState(QUICKSTART_HUNT_WON);
            gSave.timer4 = 0;
            if (QuickStartHuntSpot(region, &spotX, &spotY)) {
                QuickStartSpawnRewardEntity(
                    CheckLocalFlagByBank(FLAG_BANK_11, GF_HUNT_HANDICAP)
                        ? QuickStartDrawAtTier(QuickStartDrawPick((s32)Random() & 0x3f), QS_CAT_DROP, QS_TIER_RARE)
                        : QuickStartDrawItem((s32)Random() & 0x3f, QS_CAT_DROP),
                    spotX, spotY);
            }
            MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 17));
            MsgInit();
            return;
        }
        if (gSave.timer4 != 0) {
            gSave.timer4--;
        }
        if (gSave.timer4 == 0) {
            // Out of time. The pack goes, the kit comes back, and the giver
            // is done with this run.
            QuickStartHuntClearPack();
            QuickStartHandicapRestore();
            QuickStartHuntSetState(QUICKSTART_HUNT_FAILED);
            MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 18));
            MsgInit();
        }
        return;
    }
    if (state != QUICKSTART_HUNT_OFFERED) {
        // Won or failed: the giver has nothing left to offer, and a failed
        // one has walked off, so neither gets re-spawned.
        return;
    }
    if (!QuickStartHuntSpot(region, &spotX, &spotY)) {
        return;
    }
    {
        // Position is the identity check, exactly as it is for the kinstone
        // fusers: it survives the entity list being rebuilt on every room
        // load, which a "did I spawn yet" flag would not.
        s32 worldX = gRoomControls.origin_x + spotX;
        s32 worldY = gRoomControls.origin_y + spotY;
        s32 e;
        Entity* npc;
        for (e = 0; e < MAX_ENTITIES; e++) {
            if (gEntities[e].base.kind == NPC && gEntities[e].base.id == ZELDA &&
                gEntities[e].base.x.HALF.HI == worldX && gEntities[e].base.y.HALF.HI == worldY) {
                return;
            }
        }
        if (!QuickStartGfxBudgetForSpawn()) {
            return;
        }
        npc = CreateNPC(ZELDA, 0, 0);
        if (npc == NULL) {
            return;
        }
        npc->x.HALF.HI = worldX;
        npc->y.HALF.HI = worldY;
        npc->collisionLayer = 1;
        UpdateSpriteForCollisionLayer(npc);
        npc->direction = IdleSouth;
        QuickStartMakeNpcTalkable(npc, &script_QuickStartHunt);
    }
}

// ======================= The scavenger hunt (F1) ========================
//
// The third quest sibling, and the first with the F1 "timed find-the-item"
// shape: a giver NPC's prize has been STOLEN by a Keaton, which is loose
// somewhere in the region - it is released at the region's reward spot,
// across the map from the giver, so the chase crosses the whole region.
// Starting the chase despawns the region's wave and releases a swarm whose
// only job is slowing the player down (many instances, few kinds - the
// measured-cheap shape, docs/QUICKSTART_BUDGET.md): beetles for bodies,
// sparks for a positioning tax, one wizzrobe kind for ranged pressure.
// Kill the Keaton inside the clock and the prize drops back at the giver's
// spot as a RARE draw; run out and the pack scatters - one attempt per
// run, like the hunt.
//
// The clock is gSave.timer4 in the HUD's key slot, SHARED with the hunt
// quest - which is why the two guard against each other's RUNNING state
// (QuickStartScavCanStart / QuickStartHuntCanStart) and why the scavenger
// roll never picks the hunt's own host region. The pack is marked with the
// same QUICKSTART_EM_FLAG_HUNT bit (bit 7 is the only enemyFlags bit
// vanilla leaves free); mutual exclusion is what keeps the two quests'
// marked sets from ever coexisting.
//
// Leaving the region mid-chase unloads the pack with the room; room flag 7
// ("the pack is out this visit") is what tells that apart from a kill -
// a fresh visit with the chase RUNNING re-releases the pack instead of
// counting an empty room as a win. The clock only ticks inside the host
// region, so stepping out pauses the chase rather than silently losing it.
//
// The buried and under-bush hide modes from the F1 brief are follow-ups:
// both need per-region tile surveys (diggable spots, cuttable bushes)
// before they can be drawn safely - see the roadmap. (State values and
// the clock length live with the flag block above - the hunt's guards
// read them.)

static u32 QuickStartScavReadBits(s32 first, s32 count) {
    u32 v = 0;
    s32 b;
    for (b = 0; b < count; b++) {
        if (QsCheckFlag(first + b)) {
            v |= 1u << b;
        }
    }
    return v;
}

static void QuickStartScavWriteBits(s32 first, s32 count, u32 v) {
    s32 b;
    for (b = 0; b < count; b++) {
        if (v & (1u << b)) {
            QsSetFlag(first + b);
        } else {
            QsClearFlag(first + b);
        }
    }
}

static s32 QuickStartScavState(void) {
    return (s32)QuickStartScavReadBits(GF_SCAV_STATE_BIT(0), 2);
}

static void QuickStartScavSetState(s32 state) {
    QuickStartScavWriteBits(GF_SCAV_STATE_BIT(0), 2, (u32)state);
}

// Is either quest currently swapping the region's population (the hunt's
// pack, the scavenger chase)? While one runs, the room's live headcount
// describes the QUEST's enemies, not the wave's, so the persistent
// alive-counter must not record it - the pre-quest remainder stays put,
// which is exactly the "quests don't reset the count" rule.
static bool32 QuickStartQuestSwapActive(void) {
    return QuickStartHuntState() == QUICKSTART_HUNT_RUNNING || QuickStartScavState() == QUICKSTART_SCAV_RUNNING;
}

static void QuickStartScavRollOnce(void) {
    s32 scavRegion, huntRegion;
    if (QsCheckFlag(GF_SCAV_ROLLED)) {
        return;
    }
    // The hunt's own roll has to land first so this draw can avoid its
    // host - the two givers must never share a region (shared clock,
    // shared enemy mark).
    QuickStartHuntRollOnce();
    huntRegion = 0;
    {
        s32 b;
        for (b = 0; b < 4; b++) {
            if (QsCheckFlag(GF_REGION_HUNT_HOST_BIT(b))) {
                huntRegion |= (1 << b);
            }
        }
    }
    scavRegion = (s32)Random() % QUICKSTART_REGION_POOL_SIZE;
    if (scavRegion == huntRegion) {
        scavRegion = (scavRegion + 1) % QUICKSTART_REGION_POOL_SIZE;
    }
    QuickStartScavWriteBits(GF_SCAV_HOST_BIT(0), 4, (u32)scavRegion);
    QuickStartScavWriteBits(GF_SCAV_SPOT_BIT(0), 5, (u32)((s32)Random() % 32));
    QuickStartScavSetState(QUICKSTART_SCAV_OFFERED);
    QsSetFlag(GF_SCAV_ROLLED);
}

// Same walkable-spot walk as the hunt giver's, from this quest's own roll.
static bool32 QuickStartScavSpot(const QuickStartRegion* region, s16* outX, s16* outY) {
    s32 i, start;
    if (region->enemyOffsetCount <= 0) {
        return FALSE;
    }
    start = (s32)QuickStartScavReadBits(GF_SCAV_SPOT_BIT(0), 5) % region->enemyOffsetCount;
    for (i = 0; i < region->enemyOffsetCount; i++) {
        s32 idx = (start + i) % region->enemyOffsetCount;
        s16 x = region->enemyOffsets[idx][0];
        s16 y = region->enemyOffsets[idx][1];
        if (QuickStartPositionAllowed(x, y)) {
            *outX = x;
            *outY = y;
            return TRUE;
        }
    }
    return FALSE;
}

static s32 QuickStartCountMarked(u8 id) {
    s32 i, count = 0;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        // No health filter, deliberately - same as the hunt's own counter.
        // A just-created enemy's health is 0 until its own init tick has
        // run, so filtering on health here reads a freshly released Keaton
        // as already dead and hands out an instant win (measured). A dying
        // one keeps counting through its death animation instead, which
        // only delays the win by those few frames.
        if (ent->kind == ENEMY && ent->id == id && (((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
            count++;
        }
    }
    return count;
}

// Release (or re-release, after a room reload) the thief and its swarm.
// The wave is despawned first per the F1 brief - which also pays for the
// pack: measured, a cleared room affords far more than a live wave does.
static void QuickStartScavReleasePack(const QuickStartRegion* region, s16 giverX, s16 giverY) {
    s32 i, beetles;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (QuickStartEnemyIsOurs(ent)) {
            DeleteEntity(ent);
        } else if (ent->kind == ENEMY) {
            ((Enemy*)ent)->enemyFlags &= ~QUICKSTART_EM_FLAG_HUNT;
        }
    }
    // The thief, across the region at the reward spot.
    QuickStartSpawnEnemiesOnOpenTiles(KEATON, 0, region->rewardX, region->rewardY, 1, -1);
    // The swarm, around the conversation: bodies, a positioning tax, and
    // one ranged kind - instance-heavy, kind-light on purpose.
    beetles = 6 + QuickStartGetDifficulty() / 2;
    if (beetles > 10) {
        beetles = 10;
    }
    QuickStartSpawnEnemiesOnOpenTiles(BEETLE, 0, giverX, giverY, beetles, -1);
    QuickStartSpawnEnemiesOnOpenTiles(SPARK, 0, giverX, giverY, 3, -1);
    QuickStartSpawnEnemiesOnOpenTiles(WIZZROBE_ICE, 0, giverX, giverY, 2, -1);
    // Everything standing after a despawn is the pack: mark it all.
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == ENEMY) {
            ((Enemy*)ent)->enemyFlags |= QUICKSTART_EM_FLAG_HUNT;
        }
    }
    QsSetRoomFlag(7);
}

// --- Script hooks (data/scripts/quickstart/script_QuickStartScav.inc) ---

void QuickStartScavCanStart(Entity* entity, ScriptExecutionContext* context) {
    context->condition =
        (QuickStartScavState() == QUICKSTART_SCAV_OFFERED) && (QuickStartHuntState() != QUICKSTART_HUNT_RUNNING);
}

void QuickStartScavBegin(Entity* entity, ScriptExecutionContext* context) {
    const QuickStartRegion* region;
    s32 slot = (s32)QuickStartScavReadBits(GF_SCAV_HOST_BIT(0), 4) % QUICKSTART_REGION_POOL_SIZE;
    if (QuickStartScavState() != QUICKSTART_SCAV_OFFERED || QuickStartHuntState() == QUICKSTART_HUNT_RUNNING) {
        return;
    }
    region = &sQuickStartRegionPool[slot];
    QuickStartScavReleasePack(region, entity->x.HALF.HI - gRoomControls.origin_x,
                              entity->y.HALF.HI - gRoomControls.origin_y);
    gSave.timer4 = QUICKSTART_SCAV_FRAMES;
    QuickStartScavSetState(QUICKSTART_SCAV_RUNNING);
    SoundReq(SFX_SECRET);
}

// Called every frame from QuickStartRegionMonitor for the hosting slot.
static void QuickStartScavMonitor(const QuickStartRegion* region, s32 slot) {
    s32 state;
    s16 spotX, spotY;
    QuickStartScavRollOnce();
    if (slot != (s32)QuickStartScavReadBits(GF_SCAV_HOST_BIT(0), 4) % QUICKSTART_REGION_POOL_SIZE) {
        return;
    }
    state = QuickStartScavState();
    if (state == QUICKSTART_SCAV_RUNNING) {
        if (!QsCheckRoomFlag(7)) {
            // Fresh visit mid-chase: the room reload unloaded the pack.
            // Re-release it rather than reading the empty room as a kill.
            if (QuickStartScavSpot(region, &spotX, &spotY)) {
                QuickStartScavReleasePack(region, spotX, spotY);
            }
            return;
        }
        if (QuickStartCountMarked(KEATON) == 0) {
            // The thief is down - the prize returns to the giver's spot.
            s32 i;
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* ent = &gEntities[i].base;
                if (ent->kind == ENEMY && (((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
                    DeleteEntity(ent);
                }
            }
            QuickStartScavSetState(QUICKSTART_SCAV_WON);
            gSave.timer4 = 0;
            if (QuickStartScavSpot(region, &spotX, &spotY)) {
                QuickStartSpawnRewardEntity(
                    QuickStartDrawAtTier(QuickStartDrawPick((s32)Random() & 0x3f), QS_CAT_DROP, QS_TIER_RARE),
                    spotX, spotY);
            }
            MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 28));
            MsgInit();
            return;
        }
        if (gSave.timer4 != 0) {
            gSave.timer4--;
        }
        if (gSave.timer4 == 0) {
            s32 i;
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* ent = &gEntities[i].base;
                if (ent->kind == ENEMY && (((Enemy*)ent)->enemyFlags & QUICKSTART_EM_FLAG_HUNT)) {
                    DeleteEntity(ent);
                }
            }
            QuickStartScavSetState(QUICKSTART_SCAV_FAILED);
            MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 29));
            MsgInit();
        }
        return;
    }
    if (state != QUICKSTART_SCAV_OFFERED) {
        return;
    }
    if (!QuickStartScavSpot(region, &spotX, &spotY)) {
        return;
    }
    {
        s32 worldX = gRoomControls.origin_x + spotX;
        s32 worldY = gRoomControls.origin_y + spotY;
        s32 e;
        Entity* npc;
        for (e = 0; e < MAX_ENTITIES; e++) {
            if (gEntities[e].base.kind == NPC && gEntities[e].base.id == ZELDA &&
                gEntities[e].base.x.HALF.HI == worldX && gEntities[e].base.y.HALF.HI == worldY) {
                return;
            }
        }
        if (!QuickStartGfxBudgetForSpawn()) {
            return;
        }
        npc = CreateNPC(ZELDA, 0, 0);
        if (npc == NULL) {
            return;
        }
        npc->x.HALF.HI = worldX;
        npc->y.HALF.HI = worldY;
        npc->collisionLayer = 1;
        UpdateSpriteForCollisionLayer(npc);
        npc->direction = IdleSouth;
        QuickStartMakeNpcTalkable(npc, &script_QuickStartScav);
    }
}

// The pot room.
//
// This replaced a fixed 3x3 grid of 9 pots centred on the site's own
// contentX/contentY. That shape could not fit the rooms it had to live in:
// measured live, the fully-open floor of a hosting room runs from 18 cells
// (the Minish house off South Hyrule Field) to 220 (the Hyrule Castle
// cellar), so one hand-placed offset was either swallowed by a wall or lost
// in the middle of a field.
//
// What it builds instead: pots over most of the room's own walkable floor,
// with a clear apron at the entrance. One holds the prize, some are plain,
// some are QUICKSTART's trap form (QUICKSTART_POT_TRAP_FORM, pot.c's
// sub_0808288C - a primed bomb rather than an empty crack). The point is
// the cramping: with the floor packed there is nowhere safe to throw, so
// clearing a path risks lobbing a live one into your own feet.
//
// Three things decide the shape, and each is forced by something real:
//
// 1. WALKABILITY comes from collisionData, not actTiles. A pot fills a
//    whole tile, and collisionData == 0 means all four quadrants are free,
//    which is exactly the question. actTiles only tracks solidity by luck
//    in the overworld rooms - inside the Minish house it reads 0x00 nearly
//    everywhere and claims 2 open cells against a true 18.
//
// 2. THE FILL STREAMS IN RINGS outward from the player, one pass per
//    Chebyshev ring, instead of collecting candidate cells and sorting them
//    by distance. game.o gets no .bss/.data (linker.ld is an absolute
//    NOLOAD layout), so there is nowhere to put a candidate array, and a
//    few hundred bytes of stack for one is not worth the risk on a GBA.
//    Ring order earns its keep anyway: it puts the density where the player
//    is standing, so a 220-cell room gets a dense plug to dig through
//    rather than 30 pots sprinkled uselessly across it.
//
// 3. THE BUDGET IS TIGHT. MAX_ENTITIES is 72 for the whole game, and a
//    trap pot spawns a real PLAYER_ITEM_BOMB when it breaks - so a chain
//    reaction through a dense trap field can put a dozen live bombs in the
//    room on top of every pot still standing, plus their explosion FX. The
//    caps below leave room for that cascade, because the cascade is the
//    entire appeal.
//
// The anchor is the player's own position when the room is set up, which is
// where he arrived through the door. That is what retires the awkward
// per-room offsets: no table, and the apron is always at the way in.
#define QUICKSTART_POT_TRAP_FORM 0xFE
// Pots and traps are capped separately, because they cost different things.
// A pot is one entity. A TRAP pot is one entity now plus a live
// PLAYER_ITEM_BOMB the moment it breaks - and in a packed field one blast
// breaks its neighbours, so the traps are what can actually run the table
// out. Splitting the caps is what lets the pot count go high enough to
// cover almost the whole floor (which is the point of the room) while the
// cascade stays bounded: 44 pots + at most 12 simultaneous bombs still
// leaves ~16 slots for explosion FX, the prize and the player.
#define QUICKSTART_POT_ROOM_MAX_POTS 44
#define QUICKSTART_POT_ROOM_MAX_TRAPS 12
#define QUICKSTART_POT_ROOM_MAX_ENEMIES 4
// No room in the pool is anywhere near this wide in tiles; it only bounds
// the ring loop so a malformed room can't spin.
#define QUICKSTART_POT_ROOM_MAX_RING 40

// Density preset: what fraction of the open floor gets a pot, how many of
// those are live, and how many bob-ombs wander the gaps. 256 = every cell.
typedef struct {
    u8 fill;    // of 256
    u8 trap;    // of 256
    u8 enemies;
} QuickStartPotRoomPreset;

static const QuickStartPotRoomPreset sQuickStartPotRoomPresets[QUICKSTART_POT_ROOM_PRESET_COUNT] = {
    { 243, 96, 0 },  // packed  - ~95% of the floor, no room to breathe, no enemies needed
    { 179, 128, 2 }, // mixed   - ~70%, half of them live, a couple of bob-ombs in the gaps
    { 115, 160, 4 }, // sparse  - ~45%, mostly live, and the gaps are patrolled
};

// Bob-omb walks up and detonates; Bombarossa lobs from a distance. Both
// chosen over the tidier nuisances (ropes, leevers, sparks) on the user's
// call - they are thematically right for a room already full of bombs, and
// they are also the reason QUICKSTART_POT_ROOM_MAX_ENEMIES is only 4.
static const u8 sQuickStartPotRoomEnemies[] = { BOBOMB, BOMBAROSSA };

// xorshift32, seeded from the site's stored extra byte and the room's own
// identity. Deliberately NOT Random(): the layout has to come out identical
// every time the room is entered, or walking out and back in reshuffles
// which pot holds the prize.
static u32 QuickStartPotRoomRand(u32* state) {
    u32 x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

static u32 QuickStartPotRoomSeed(s32 extra) {
    // The | 1 matters: xorshift is stuck at zero forever if it ever seeds
    // there, and extra is legitimately 0 for one preset/prize combination.
    return (u32)((extra * 2654435761u) ^ ((u32)gRoomControls.area << 16) ^ ((u32)gRoomControls.room << 8) ^
                 0x9E3779B9u) |
           1u;
}


// The entrance apron: the clear ground the player is standing on when the
// room builds itself. A full 3x3 costs 9 cells, which is half the floor of
// the smallest hosting room, so below that size it degrades to a plus - the
// player's own tile and its four cardinal neighbours. What it must never do
// is degrade to nothing: sealing the player in on all four sides means he
// has to break a pot before he can move at all, and if that one happens to
// be live he eats the blast at point-blank with nowhere to retreat to.
// Does this tile belong to the event we are building, or to a neighbouring
// one?
//
// Most rooms hold a single content site and this always answers yes. The
// Boomerang chamber holds five - one per tree ladder - in a single connected
// cave, and the pot room's flood does not care about walls it cannot see: it
// spread straight out of its own alcove and across the other four, which is
// the user's report that the pot puzzle "expanded across several of the
// sub-areas".
//
// The division is a plain nearest-site test against the sites' own content
// spots. No new table and no per-room boxes: a tile is ours only if our
// site is the closest one to it, which carves the shared room into one
// region per event exactly where the events themselves sit.
static bool32 QuickStartPotRoomInApron(s32 dx, s32 dy, s32 apron) {
    s32 ax = (dx < 0) ? -dx : dx;
    s32 ay = (dy < 0) ? -dy : dy;
    if (apron > 0) {
        return ax <= apron && ay <= apron;
    }
    return (ax + ay) <= 1;
}

// One fill pass. Returns how many pots it placed (or would have placed, with
// spawn == FALSE). winnerIndex < 0 means "no prize this pass".
//
// It runs twice, and it has to. The number of pots that actually go down is
// not the target: the apron, the room's walls and the per-cell skip roll all
// eat into it, so a winnerIndex picked against the target can land past the
// end and the prize never spawns at all - the room becomes unwinnable, which
// is exactly what the first version did in the Minish house. So pass one
// counts with spawning off, the index is chosen against that real count, and
// pass two re-seeds and lays the room down for real. Both passes run before
// a single pot exists, which matters: a pot WRITES collision, so a pass run
// after any of them are standing would see a different map.
// --- Pot placement reachability ------------------------------------------
//
// "Open" is not the same as "the player can get there". The Lon Lon Ranch
// through-cave is the case that proved it: a 15x16 room split by a solid
// wall across row 8, with the arrival chamber above it and a second chamber
// below. Both halves are open floor, both fall inside the fill's rings, so
// the generator happily laid pots in the lower half - which the player
// cannot reach from where they come in. The reported symptom was pots
// "spawning outside the walkable space".
//
// So the fill is restricted to the anchor's own connected component. The
// set is computed ONCE, before any pot exists, which matters: a pot writes
// collision onto its own tile as it spawns, so a set computed later would
// see the fill walling itself off and shrink as it went.
//
// Flood fill by repeated sweeps rather than a queue: a queue big enough for
// the worst-case room is far more stack than this is worth, while the
// bitmap is 512 bytes and the rooms that host pot lotteries are small. It
// runs once per room entry, not per frame.
#define QUICKSTART_REACH_BYTES (64 * 64 / 8)
#define QUICKSTART_REACH_GET(bits, x, y) ((bits)[(((y) << 6) | (x)) >> 3] & (1 << ((((y) << 6) | (x)) & 7)))
#define QUICKSTART_REACH_SET(bits, x, y) ((bits)[(((y) << 6) | (x)) >> 3] |= (1 << ((((y) << 6) | (x)) & 7)))

static void QuickStartMarkReachableTiles(u8* bits, s32 anchorTX, s32 anchorTY) {
    s32 w = (s32)(gRoomControls.width >> 4);
    s32 h = (s32)(gRoomControls.height >> 4);
    s32 x, y, i, changed;
    for (i = 0; i < QUICKSTART_REACH_BYTES; i++) {
        bits[i] = 0;
    }
    if (w > 64) {
        w = 64;
    }
    if (h > 64) {
        h = 64;
    }
    if (anchorTX < 0 || anchorTY < 0 || anchorTX >= w || anchorTY >= h || !QuickStartTileIsOpen(anchorTX, anchorTY)) {
        return; // no seed - caller treats an empty set as "no restriction"
    }
    QUICKSTART_REACH_SET(bits, anchorTX, anchorTY);
    do {
        changed = 0;
        for (y = 0; y < h; y++) {
            for (x = 0; x < w; x++) {
                if (QUICKSTART_REACH_GET(bits, x, y) || !QuickStartTileIsOpen(x, y)) {
                    continue;
                }
                if ((x > 0 && QUICKSTART_REACH_GET(bits, x - 1, y)) ||
                    (y > 0 && QUICKSTART_REACH_GET(bits, x, y - 1)) ||
                    (x + 1 < w && QUICKSTART_REACH_GET(bits, x + 1, y)) ||
                    (y + 1 < h && QUICKSTART_REACH_GET(bits, x, y + 1))) {
                    QUICKSTART_REACH_SET(bits, x, y);
                    changed = 1;
                }
            }
        }
    } while (changed);
}

// An empty set means the seed was unusable, in which case the old
// unrestricted behaviour is better than placing nothing at all.
static bool32 QuickStartReachAllows(const u8* bits, s32 tx, s32 ty) {
    s32 i;
    if (tx < 0 || ty < 0 || tx >= 64 || ty >= 64) {
        return FALSE;
    }
    if (QUICKSTART_REACH_GET(bits, tx, ty)) {
        return TRUE;
    }
    for (i = 0; i < QUICKSTART_REACH_BYTES; i++) {
        if (bits[i] != 0) {
            return FALSE;
        }
    }
    return TRUE;
}

static s32 QuickStartPotRoomFill(const QuickStartPotRoomPreset* preset, u32 seed, s32 anchorTX, s32 anchorTY,
                                 s32 apron, s32 target, s32 winnerIndex, s32 prizeIndex, s32 ownerSite,
                                 bool32 spawn, const u8* reach) {
    u32 state = seed;
    s32 ring, placed = 0, traps = 0, enemiesLeft = spawn ? preset->enemies : 0;

    if (enemiesLeft > QUICKSTART_POT_ROOM_MAX_ENEMIES) {
        enemiesLeft = QUICKSTART_POT_ROOM_MAX_ENEMIES;
    }
    for (ring = 0; ring < QUICKSTART_POT_ROOM_MAX_RING && placed < target; ring++) {
        s32 dx, dy;
        for (dy = -ring; dy <= ring; dy++) {
            for (dx = -ring; dx <= ring; dx++) {
                s32 tx, ty;
                u32 roll;
                // Ring, not disc: only the cells exactly `ring` away, so
                // each cell is visited once across the whole loop.
                if (dx != -ring && dx != ring && dy != -ring && dy != ring) {
                    continue;
                }
                tx = anchorTX + dx;
                ty = anchorTY + dy;
                // Per CELL, not just per ring. The ring loop's own `placed <
                // target` only stops it starting a new ring, and a single
                // ring of a big room holds far more cells than the whole
                // budget - the Fairy Fountain laid 43 pots against a cap of
                // 30 before this was here.
                if (placed >= target) {
                    return placed;
                }
                if (QuickStartPotRoomInApron(dx, dy, apron) || !QuickStartTileIsOpen(tx, ty) ||
                    !QuickStartReachAllows(reach, tx, ty) ||
                    !QuickStartTileBelongsToSite(tx, ty, ownerSite)) {
                    continue;
                }
                roll = QuickStartPotRoomRand(&state);
                if ((roll & 0xFF) >= preset->fill) {
                    // A gap. Some of them get something unpleasant standing
                    // in them.
                    if (enemiesLeft > 0 && ((roll >> 8) & 3) == 0) {
                        Entity* enemy = CreateEnemy(
                            sQuickStartPotRoomEnemies[(roll >> 16) % ARRAY_COUNT(sQuickStartPotRoomEnemies)], 0);
                        if (enemy != NULL) {
                            enemy->x.HALF.HI = gRoomControls.origin_x + tx * 16 + 8;
                            enemy->y.HALF.HI = gRoomControls.origin_y + ty * 16 + 8;
                            enemy->collisionLayer = 1;
                            UpdateSpriteForCollisionLayer(enemy);
                            enemiesLeft--;
                        }
                    }
                    continue;
                }
                {
                    // Decided in both passes, not just the spawning one, so
                    // the two passes stay in lockstep.
                    bool32 isTrap = (roll >> 24) < preset->trap && traps < QUICKSTART_POT_ROOM_MAX_TRAPS;
                    if (isTrap) {
                        traps++;
                    }
                    if (spawn) {
                        u32 form = (placed == winnerIndex)
                                       ? sQuickStartLotteryPrizes[prizeIndex]
                                       : (isTrap ? QUICKSTART_POT_TRAP_FORM : (u32)0xFF);
                        Entity* pot = CreateObject(POT, form, 0);
                        if (pot != NULL) {
                            pot->x.HALF.HI = gRoomControls.origin_x + tx * 16 + 8;
                            pot->y.HALF.HI = gRoomControls.origin_y + ty * 16 + 8;
                            pot->collisionLayer = 1;
                            pot->flags |= ENT_PERSIST;
                            UpdateSpriteForCollisionLayer(pot);
                        }
                    }
                }
                placed++;
            }
        }
    }
    return placed;
}

static void QuickStartPotRoomGenerate(s32 extra, s32 anchorTX, s32 anchorTY, s32 ownerSite) {
    const QuickStartPotRoomPreset* preset = &sQuickStartPotRoomPresets[(extra & 3) % QUICKSTART_POT_ROOM_PRESET_COUNT];
    s32 prizeIndex = QuickStartLotteryPrizeIndex(extra);
    s32 winnerBucket = (extra >> QUICKSTART_POT_WINNER_SHIFT) & (QUICKSTART_POT_WINNER_BUCKETS - 1);
    u32 seed = QuickStartPotRoomSeed(extra);
    s32 open = QuickStartCountOpenTiles();
    s32 target = (open * preset->fill) >> 8;
    s32 apron, actual, winnerIndex;
    u8 reach[QUICKSTART_REACH_BYTES];

    if (target > QUICKSTART_POT_ROOM_MAX_POTS) {
        target = QUICKSTART_POT_ROOM_MAX_POTS;
    }
    // Cap by real entity headroom, minus a margin for the trap pots' bombs
    // and their FX. Without this the counting pass and the spawning pass
    // disagree the moment CreateObject starts returning NULL - the room
    // survey measured the Boomerang chamber at just 28 free slots (five
    // events' worth of content lives there), and a winner index past the
    // last pot that actually spawned is an unwinnable room: the prize
    // simply never exists.
    {
        s32 slots = (s32)(MAX_ENTITIES - gEntCount) - 12;
        if (slots < 1) {
            slots = 1;
        }
        if (target > slots) {
            target = slots;
        }
    }
    // A 3x3 apron costs 9 cells, which is half the floor of the smallest
    // hosting room, so below that size QuickStartPotRoomInApron falls back to
    // a plus shape instead.
    apron = (open >= 24) ? 1 : 0;

    // Computed here, once, and shared by both passes - and deliberately
    // before a single pot exists, since pots write their own collision.
    QuickStartMarkReachableTiles(reach, anchorTX, anchorTY);

    actual = QuickStartPotRoomFill(preset, seed, anchorTX, anchorTY, apron, target, -1, prizeIndex, ownerSite,
                                   FALSE, reach);
    if (actual <= 0 && ownerSite >= 0) {
        // The player arrived outside this site's own region - re-anchor on
        // the site itself rather than giving up, so the room still gets its
        // event and still keeps it local.
        {
            s16 siteX, siteY;
            QuickStartSiteContentSpot(ownerSite, &siteX, &siteY);
            anchorTX = siteX >> 4;
            anchorTY = siteY >> 4;
        }
        // Re-anchoring moves the component too, so the set is rebuilt.
        QuickStartMarkReachableTiles(reach, anchorTX, anchorTY);
        actual = QuickStartPotRoomFill(preset, seed, anchorTX, anchorTY, apron, target, -1, prizeIndex, ownerSite,
                                       FALSE, reach);
    }
    if (actual <= 0) {
        return;
    }
    // Keep the winner in the far half of the fill order, so it sits deep in
    // the field rather than in the first ring the player can reach.
    winnerIndex = (actual / 2) + ((winnerBucket * (actual / 2)) >> 3);
    if (winnerIndex >= actual) {
        winnerIndex = actual - 1;
    }
    QuickStartPotRoomFill(preset, seed, anchorTX, anchorTY, apron, target, winnerIndex, prizeIndex, ownerSite,
                          TRUE, reach);
}

// Pots are OBJECT-kind, so QuickStartClearVanillaRoomContent never sweeps
// them mid-visit - the same "spawn once, then just watch for the drop"
// two-flag shape QS_EVENT_ITEM_DROP uses (room flag 0 = spawned, 3 =
// confirmed present at least once) is enough on its own to stop a reload
// re-rolling or duplicating the prize.
static bool32 QuickStartSetupPotRoomContent(s32 extra, s32 contentX, s32 contentY, u32 flagBase) {
    s32 anchorTX, anchorTY;
    if (QsCheckRoomFlag(flagBase + 0)) {
        if (QuickStartGroundItemOfForm(sQuickStartLotteryPrizes[QuickStartLotteryPrizeIndex(extra)])) {
            QsSetRoomFlag(flagBase + 3);
            return FALSE;
        }
        return QsCheckRoomFlag(flagBase + 3);
    }
    // The player's own arrival spot anchors the layout. contentX/contentY -
    // the site's hand-placed content offset - is deliberately ignored here;
    // retiring it is the whole point of this rewrite.
    anchorTX = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) >> 4;
    anchorTY = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) >> 4;
    QuickStartPotRoomGenerate(extra, anchorTX, anchorTY, QuickStartFindSiteAt(contentX, contentY));
    QsSetRoomFlag(flagBase + 0);
    return FALSE;
}

// Each of the 3 chests' own "already opened" local flag (SpecialChest_Init:
// CheckLocalFlag(this->type), specialChest.c) is drawn from this fixed,
// high, QUICKSTART-reserved range rather than anything meaningful to the
// room's own vanilla data - chosen well above any real room's own local
// flag usage. Cleared explicitly right before every spawn (not just in
// GameTask_Transition, which only knows about global flags) so a flag left
// set by a previous save's playthrough of this same physical room can never
// make a chest insta-delete itself on a fresh save.
#define QUICKSTART_CHEST_LOTTERY_FLAG(i) (250 + (i))

// Same winnerSlot/prizeIndex shape as the pot lottery above, but via
// SPECIAL_CHEST + a manually-injected gSmallChests entry (see room.c's
// LoadSmallChestTile/playerItemUtils.c's OpenSmallChest) instead of POT's
// form parameter - the other two chests are left unregistered, so opening
// them falls through to OpenSmallChest's own "not found" consolation prize
// (a fairy). Tracks done via the winner's own local flag going from clear
// to set (OpenSmallChest sets it on a successful, registered open) - no
// ground-item polling needed here since that flag is itself an
// unambiguous, persistent "was this actually opened" signal.
static bool32 QuickStartSetupChestLotteryContent(s32 extra, s32 contentX, s32 contentY, u32 flagBase) {
    static const s16 offsets[3] = { -16, 0, 16 };
    s32 winnerSlot, prizeIndex;
    winnerSlot = extra & 3;
    // Same guard as the pot lottery's: only 0-2 are ever rolled, but the
    // stored bits are cheap to sanity-check and the table is only 3 long.
    if (winnerSlot > 2) {
        winnerSlot = 2;
    }
    prizeIndex = QuickStartLotteryPrizeIndex(extra);
    if (QsCheckRoomFlag(flagBase + 0)) {
        return CheckLocalFlag(QUICKSTART_CHEST_LOTTERY_FLAG(winnerSlot)) ? TRUE : FALSE;
    }
    {
        s32 i;
        for (i = 0; i < 3; i++) {
            ClearLocalFlag(QUICKSTART_CHEST_LOTTERY_FLAG(i));
        }
        for (i = 0; i < 3; i++) {
            s32 localX = contentX + offsets[i];
            Entity* chest = CreateObject(SPECIAL_CHEST, QUICKSTART_CHEST_LOTTERY_FLAG(i), 0);
            if (chest != NULL) {
                chest->x.HALF.HI = gRoomControls.origin_x + localX;
                chest->y.HALF.HI = gRoomControls.origin_y + contentY;
                chest->collisionLayer = 1;
                chest->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(chest);
            }
            if (i == winnerSlot) {
                s32 j;
                TileEntity* slot = NULL;
                for (j = 0; j < 8; j++) {
                    if (gSmallChests[j].tilePos == 0) {
                        slot = &gSmallChests[j];
                        break;
                    }
                }
                if (slot != NULL) {
                    slot->type = SMALL_CHEST;
                    slot->localFlag = (u8)QUICKSTART_CHEST_LOTTERY_FLAG(i);
                    slot->_2 = (u8)sQuickStartLotteryPrizes[prizeIndex];
                    slot->_3 = 0;
                    slot->tilePos = (u16)(((localX >> 4) & 0x3F) | (((contentY >> 4) & 0x3F) << 6));
                    slot->_6 = 1;
                    slot->_7 = 0;
                }
            }
        }
        QsSetRoomFlag(flagBase + 0);
    }
    return FALSE;
}

// Two Fairy objects (fairy.c) at fixed offsets - the exact object an
// ITEM_FAIRY ground item already turns itself into on its own (see
// itemOnGround.c's ITEM_FAIRY special case: CreateObject(FAIRY, 0x60, 0)),
// reused directly here instead of going through a ground-item middleman.
// type2=0 gives the default "pop up, wander, heal on contact, vanish after
// ~10s if ignored" behavior, identical to any fairy found in the wild -
// unlike the lottery kinds above, there's no lasting reward here to guard
// against re-farming, so this doesn't bother with GF_SLOT_DONE at all.
static void QuickStartSetupFairyRoomContent(s32 contentX, s32 contentY, u32 flagBase) {
    static const s16 offsets[2] = { -16, 16 };
    s32 i;
    if (QsCheckRoomFlag(flagBase + 0)) {
        return;
    }
    for (i = 0; i < 2; i++) {
        Entity* fairy = CreateObject(FAIRY, 0x60, 0);
        if (fairy != NULL) {
            fairy->x.HALF.HI = gRoomControls.origin_x + contentX + offsets[i];
            fairy->y.HALF.HI = gRoomControls.origin_y + contentY;
            fairy->collisionLayer = 1;
            UpdateSpriteForCollisionLayer(fairy);
        }
    }
    QsSetRoomFlag(flagBase + 0);
}

// The single-door "? room" event itself, independent of who owns it.
// Called every frame the player is standing in the room; returns TRUE the
// moment the event is fully resolved (chest looted / mini-boss dead and its
// drop taken / lottery decided), which is the caller's cue to set whatever
// "done" latch it keeps so nothing ever spawns here again.
//
// Split out of QuickStartSetupSlotRoomContent so the room-keyed content
// sites (QuickStartSetupContentSite) can run the exact same seven event
// kinds. Those sites are the only live caller now - every synthetic ladder
// and door entrance has been retired in favour of real vanilla doors - but
// keeping the two entry points separate costs nothing and keeps the
// retired path honest rather than half-deleted.
//
// A plain room flag (reset on every reload) is enough to track "spawned
// this visit": these are all single-entrance dead ends, so there is no
// leave-before-resolving recovery to do the way the multi-exit rooms
// elsewhere in this file need.
// --- The closing gate (QS_EVENT_GATE) helpers -----------------------------

static u32 QuickStartGateReadTimer(void) {
    u32 v = 0;
    s32 b;
    for (b = 0; b < 10; b++) {
        if (QsCheckFlag(GF_GATE_TIMER_BIT(b))) {
            v |= 1u << b;
        }
    }
    return v;
}

static void QuickStartGateWriteTimer(u32 v) {
    s32 b;
    for (b = 0; b < 10; b++) {
        if (v & (1u << b)) {
            QsSetFlag(GF_GATE_TIMER_BIT(b));
        } else {
            QsClearFlag(GF_GATE_TIMER_BIT(b));
        }
    }
}

// The cage is a ring of PRIMED TRAP POTS (QUICKSTART_POT_TRAP_FORM, the
// pot lottery's bomb form). The first cut painted tiles instead, with the
// bridge's proven donor discipline - and the collision flipped while the
// ART did not: in interior rooms the walls' visible art lives on another
// background layer, so the sampled 'solid' type draws nothing, and the
// result was an invisible fence (screenshotted; the exact artifact class
// the user has reported before). Pots carry their own sprite, so they are
// visible in every room by construction - and a trap-pot cage is BETTER
// roguelite besides: a player may force entry by lifting a primed pot and
// eating the blast, paying in health for what the lever gives free.
static s32 QuickStartGateRingPots(s32 ptx, s32 pty, Entity** firstOut) {
    s32 i, count = 0;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s32 tx, ty;
        if (ent->kind != OBJECT || ent->id != POT) {
            continue;
        }
        tx = (ent->x.HALF.HI - gRoomControls.origin_x) >> 4;
        ty = (ent->y.HALF.HI - gRoomControls.origin_y) >> 4;
        if (tx >= ptx - 1 && tx <= ptx + 1 && ty >= pty - 1 && ty <= pty + 1 && !(tx == ptx && ty == pty)) {
            if (firstOut != NULL && count == 0) {
                *firstOut = ent;
            }
            count++;
        }
    }
    return count;
}

// playerClearance is a Chebyshev radius (in tiles) around the player that
// the ring must leave empty. 0 is the old behaviour - only the tile under
// their feet is spared, which is what the trap close (aimed AT the player)
// and the timed re-close (the pressure the puzzle IS) need. The initial
// deal passes 2: the player is standing on the doorstep they just walked
// in through, so tiles near them ARE the doorway, and a deal that walls
// the door is the user-reported failure. A cage dealt with a gap is the
// safe failure either way - the prize just comes cheaper.
static void QuickStartGateClose(s32 ptx, s32 pty, s32 playerClearance) {
    s32 dx, dy;
    s32 playerTX = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) >> 4;
    s32 playerTY = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) >> 4;
    for (dy = -1; dy <= 1; dy++) {
        for (dx = -1; dx <= 1; dx++) {
            s32 tx = ptx + dx;
            s32 ty = pty + dy;
            Entity* pot;
            s32 e;
            bool32 taken = FALSE;
            if (dx == 0 && dy == 0) {
                continue;
            }
            // Never near the player, never on solid ground, never doubled -
            // and never in the room's outer THREE tile rows/columns. Doors,
            // seams and ladder mouths live in the outer walls, and their
            // one-tile approach corridors sit directly inboard of them: the
            // dojo lockout was a cage row landing on the seam-approach tile
            // at row 9 of 12, which an outer-2 band would not have caught.
            // In a room too small to give the ring 3 tiles of clearance the
            // cage comes out with a gap - a free prize is the safe failure;
            // a walled-off entrance is the one the user got locked out by.
            if (tx >= playerTX - playerClearance && tx <= playerTX + playerClearance &&
                ty >= playerTY - playerClearance && ty <= playerTY + playerClearance) {
                continue;
            }
            if (tx < 3 || ty < 3 || tx >= (s32)(gRoomControls.width >> 4) - 3 ||
                ty >= (s32)(gRoomControls.height >> 4) - 3) {
                continue;
            }
            // Never on top of a switch. The cage is dealt AFTER the
            // switches, and a pot's tile is not "open" once it is there,
            // so a ring pot landing on a switch buried it - the player saw
            // a pot where the puzzle's one interactive object should be
            // ("the levers/switches are often under the pots"). The
            // switch-side minimum distance normally keeps the ring clear
            // of them anyway; this is the guard for the cramped rooms
            // where that minimum has to be relaxed.
            if (QuickStartLeverAtTile(tx, ty)) {
                continue;
            }
            if (!QuickStartTileIsOpen(tx, ty)) {
                continue;
            }
            for (e = 0; e < MAX_ENTITIES; e++) {
                Entity* ent = &gEntities[e].base;
                if (ent->kind == OBJECT && ent->id == POT &&
                    (ent->x.HALF.HI - gRoomControls.origin_x) >> 4 == tx &&
                    (ent->y.HALF.HI - gRoomControls.origin_y) >> 4 == ty) {
                    taken = TRUE;
                    break;
                }
            }
            if (taken) {
                continue;
            }
            pot = CreateObject(POT, QUICKSTART_POT_TRAP_FORM, 0);
            if (pot != NULL) {
                pot->x.HALF.HI = gRoomControls.origin_x + tx * 16 + 8;
                pot->y.HALF.HI = gRoomControls.origin_y + ty * 16 + 8;
                pot->collisionLayer = 1;
                pot->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(pot);
            }
        }
    }
}

static void QuickStartGateOpen(s32 ptx, s32 pty) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        s32 tx, ty;
        if (ent->kind != OBJECT || ent->id != POT) {
            continue;
        }
        tx = (ent->x.HALF.HI - gRoomControls.origin_x) >> 4;
        ty = (ent->y.HALF.HI - gRoomControls.origin_y) >> 4;
        if (tx >= ptx - 1 && tx <= ptx + 1 && ty >= pty - 1 && ty <= pty + 1 && !(tx == ptx && ty == pty)) {
            // A pot stamps SPECIAL_TILE_0 over its tile at init and saves
            // the original index at entity offset 0x70 (pot.c, unk_70),
            // restoring it only through its own lift/break paths. A bare
            // DeleteEntity skips that restore and leaves phantom map
            // collision behind - measured: the ring read solid forever and
            // the re-close skipped every "occupied" tile, spawning nothing.
            SetTile(*(u16*)((u8*)ent + 0x70), TILE_POS(tx, ty), ent->collisionLayer);
            DeleteEntity(ent);
        }
    }
}

// --- The decoy switches (QS_EVENT_GATE, room flag +1 set) -----------------
// All six deals of {prize, trap, dud} (the QUICKSTART_LEVER_ROLE_*
// values 0/1/2) across the three switches. One row is drawn per visit and
// stamped switch-by-switch into a scratch byte on the entity (see
// QS_SWITCH_ROLE); QUICKSTART_LEVER_ROLE_DONE marks a switch whose pull
// has been resolved, so flipping a spent switch back and forth does
// nothing further.
static const u8 sQuickStartLeverRoles[6][3] = {
    { 0, 1, 2 }, { 0, 2, 1 }, { 1, 0, 2 },
    { 1, 2, 0 }, { 2, 0, 1 }, { 2, 1, 0 },
};

// The puzzle's switches are LIGHTABLE_SWITCH objects, not HITTABLE_LEVER.
// A lever has NO sprite of its own - its gObjectDefinitions row reads gfx
// 0 / sprite 0, and its whole visual is HittableLever_UpdateTile painting
// meta-tiles 0x377/0x378 into the room's tilemap. Only dungeon tilesets
// carry lever art at those indices, so in the overworld ? rooms the lever
// rendered as whatever garbage the local tileset kept there ("some kind
// of broken element", per the user - the same tileset-locality lesson as
// the invisible painted shutter). The lightable switch instead carries
// fixed gfx 19 / sprite 475 through LoadFixedGFX - the "entity sprites
// render everywhere" rule the trap pots already rely on - and its Type0
// is a free-running toggle: every hit flips the flag named by its flag2
// field (entity offset 0x86) and frameIndex mirrors that flag, 0 off / 1
// on (lightableSwitch.c). Three consequences shape the plumbing:
//  - flag2 must name a REAL flag, or the toggle never latches
//    (SetFlag(0) is a no-op). Each switch gets its own bit in the private
//    room-flag window - offsets 104..107, directly above the content
//    sites' 64 + slot*8 windows - encoded as a type-2 (room) flag id.
//  - type2 selects its optional rail-movement mode, so the decoy roles
//    that used to ride in the lever's unused type2 move to a scratch
//    byte at entity offset 0x76, inside LightableSwitchEntity's unused
//    padding.
//  - "pulled" is read from frameIndex, not from a flipping type bit.
#define QS_SWITCH_HIT_FLAG(n) (0x8000 + QUICKSTART_ROOM_FLAG_ORIGIN + 104 + (n))
#define QS_SWITCH_ROLE(ent) (((u8*)(ent))[0x76])
#define QS_SWITCH_FLAG2(ent) (*(u16*)((u8*)(ent) + 0x86))

static Entity* QuickStartSpawnPuzzleSwitch(s32 lx, s32 ly, u32 flagIndex) {
    Entity* sw = CreateObject(LIGHTABLE_SWITCH, 0, 0);
    if (sw != NULL) {
        sw->x.HALF.HI = gRoomControls.origin_x + lx;
        sw->y.HALF.HI = gRoomControls.origin_y + ly;
        sw->collisionLayer = 1;
        QS_SWITCH_FLAG2(sw) = QS_SWITCH_HIT_FLAG(flagIndex);
        // Deal every switch OFF. The bit lives in gRoomVars, which the
        // room reset wipes anyway; this covers a redeal inside one visit.
        ClearFlag(QS_SWITCH_HIT_FLAG(flagIndex));
        QS_SWITCH_ROLE(sw) = 0;
        UpdateSpriteForCollisionLayer(sw);
    }
    return sw;
}

// Pull a room-local pixel anchor at least 5 tiles inboard of every wall.
// Switches spawn "near the player", and at a seam or door the player IS
// the entrance corridor: measured in the dojo, the decoy deal put its
// middle switch on the corridor's own column at the seam mouth, and a
// puzzle switch is a solid, collidable fixture - the room was walled shut
// exactly the way the mis-placed cage had walled it (user-reported
// class). Anchoring the search inboard keeps every switch off the
// doorstep; the player walked in, so a spot a few tiles ahead of them is
// always reachable. The CAGE anchors through this too (the site content
// spots were chosen for reward drops, and several sit on the door's
// approach line - "the puzzle is placed right in front of the ? room
// door", per the user), which is why the margin is 5 tiles rather than
// the original 3.5: the cage ring reaches one tile beyond its anchor, and
// a ring tile four tiles from the wall still leaves the outer-3 door band
// plus a one-tile walking gap in front of it.
#define QUICKSTART_INBOARD_MARGIN 0x58
static void QuickStartClampInboard(s32* x, s32* y) {
    s32 maxX = (s32)gRoomControls.width - QUICKSTART_INBOARD_MARGIN;
    s32 maxY = (s32)gRoomControls.height - QUICKSTART_INBOARD_MARGIN;
    if (*x < QUICKSTART_INBOARD_MARGIN) {
        *x = QUICKSTART_INBOARD_MARGIN;
    } else if (*x > maxX) {
        *x = maxX;
    }
    if (*y < QUICKSTART_INBOARD_MARGIN) {
        *y = QUICKSTART_INBOARD_MARGIN;
    } else if (*y > maxY) {
        *y = maxY;
    }
}

static bool32 QuickStartLeverAtTile(s32 tx, s32 ty) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == LIGHTABLE_SWITCH &&
            (ent->x.HALF.HI - gRoomControls.origin_x) >> 4 == tx &&
            (ent->y.HALF.HI - gRoomControls.origin_y) >> 4 == ty) {
            return TRUE;
        }
    }
    return FALSE;
}

// Where a puzzle switch may be dealt: open ground, inboard of the door
// band, not on another switch, and at least minTiles from the cage anchor
// (ptx, pty) so the window below has a walk to price. The anchor is the
// player's own position - they just walked in, so a tile near them is
// always reachable - and when that neighbourhood is too close to the cage
// the search pushes the anchor four tiles out and tries again, in the
// eight compass directions, rather than giving up and dealing on top of
// the prize.
//
// Returns FALSE when nothing satisfies minTiles; the callers walk the
// distance down rather than skipping the switch, because a puzzle with no
// switch at all is worse than a short one (the cage is liftable, so a
// switchless deal is simply a free prize).
// Clamp to the outer-THREE band rather than to QuickStartClampInboard's
// 5.5-tile margin. That margin is sized for the CAGE, whose ring reaches a
// tile beyond its anchor; a switch is a single tile, and the outer-3 test
// below is already the rule that keeps it off doors, seams and their
// approach corridors. The difference matters in the small caves: a 15x10
// room clamps to a band five tiles wide under the cage's margin, which is
// why every deal there used to land on the 2-tile floor.
static void QuickStartClampToBand(s32* x, s32* y) {
    s32 lo = 3 * 16 + 8;
    s32 maxX = ((s32)(gRoomControls.width >> 4) - 4) * 16 + 8;
    s32 maxY = ((s32)(gRoomControls.height >> 4) - 4) * 16 + 8;
    if (*x > maxX) {
        *x = maxX;
    }
    if (*x < lo) {
        *x = lo;
    }
    if (*y > maxY) {
        *y = maxY;
    }
    if (*y < lo) {
        *y = lo;
    }
}

static bool32 QuickStartGateSwitchTile(s32 anchorX, s32 anchorY, s32 ptx, s32 pty, s32 minTiles, s16* outX,
                                       s16* outY) {
    // The player's own anchor first (they just walked in, so a tile near
    // them is both reachable and obvious), then anchors pushed four tiles
    // out, then the four corners of the band - the last resort for a room
    // too small for any push to buy separation.
    static const s16 sPush[9][2] = {
        { 0, 0 },    { -64, 0 },  { 64, 0 },   { 0, -64 },  { 0, 64 },
        { -64, -64 }, { 64, 64 }, { 64, -64 }, { -64, 64 },
    };
    s32 attempt;
    for (attempt = 0; attempt < 13; attempt++) {
        s32 ax, ay;
        s16 lx, ly;
        s32 tx, ty, dx, dy, dist;
        if (attempt < 9) {
            ax = anchorX + sPush[attempt][0];
            ay = anchorY + sPush[attempt][1];
        } else {
            ax = (attempt & 1) ? (3 * 16 + 8) : (((s32)(gRoomControls.width >> 4) - 4) * 16 + 8);
            ay = (attempt & 2) ? (3 * 16 + 8) : (((s32)(gRoomControls.height >> 4) - 4) * 16 + 8);
        }
        QuickStartClampToBand(&ax, &ay);
        if (!QuickStartFindOpenTileNear(ax, ay, 1, &lx, &ly)) {
            continue;
        }
        tx = lx >> 4;
        ty = ly >> 4;
        if (QuickStartLeverAtTile(tx, ty)) {
            continue;
        }
        // The outer band is doors, seams and their approach corridors - a
        // switch there is a switch in a wall (see QuickStartClampInboard).
        if (tx < 3 || ty < 3 || tx >= (s32)(gRoomControls.width >> 4) - 3 ||
            ty >= (s32)(gRoomControls.height >> 4) - 3) {
            continue;
        }
        dx = tx - ptx;
        if (dx < 0) {
            dx = -dx;
        }
        dy = ty - pty;
        if (dy < 0) {
            dy = -dy;
        }
        dist = (dx > dy) ? dx : dy;
        if (dist < minTiles) {
            continue;
        }
        *outX = lx;
        *outY = ly;
        return TRUE;
    }
    return FALSE;
}

// The same search, relaxing the separation until something fits. 2 is the
// hard floor: it puts the switch outside the cage ring's own footprint,
// which is what stops a ring pot from burying it.
static bool32 QuickStartGateSwitchSpot(s32 anchorX, s32 anchorY, s32 ptx, s32 pty, s16* outX, s16* outY) {
    s32 want;
    for (want = QUICKSTART_GATE_LEVER_MIN_TILES; want >= 2; want--) {
        if (QuickStartGateSwitchTile(anchorX, anchorY, ptx, pty, want, outX, outY)) {
            return TRUE;
        }
    }
    return FALSE;
}

// The window a pull earns, priced off how far the switch that was pulled
// sits from the cage. See the constants for the measurement behind it.
static s32 QuickStartGateWindowFor(s32 switchTX, s32 switchTY, s32 ptx, s32 pty) {
    s32 dx = switchTX - ptx;
    s32 dy = switchTY - pty;
    s32 dist, perTile, window;
    if (dx < 0) {
        dx = -dx;
    }
    if (dy < 0) {
        dy = -dy;
    }
    dist = (dx > dy) ? dx : dy;
    perTile = QUICKSTART_GATE_SLACK_BASE - QuickStartGetDifficulty();
    if (perTile < QUICKSTART_GATE_SLACK_MIN) {
        perTile = QUICKSTART_GATE_SLACK_MIN;
    }
    window = dist * perTile;
    if (window < QUICKSTART_GATE_WINDOW_MIN) {
        window = QUICKSTART_GATE_WINDOW_MIN;
    }
    if (window > QUICKSTART_GATE_WINDOW_MAX) {
        window = QUICKSTART_GATE_WINDOW_MAX;
    }
    return window;
}

static bool32 QuickStartSetupEventContent(u8 kind, s32 extra, s16 contentX, s16 contentY, u32 flagBase) {
    // One correction for every kind: if the table's content spot is solid
    // or out of bounds, snap it to the nearest open tile before anything is
    // placed. Miniboss, waves and the pot room already derive their own
    // ground; chest, NPC and fairy used the spot raw, so a single bad table
    // row (the class of error behind Lon Lon's exit box and the 2-door
    // entrances) silently broke those kinds.
    {
        s16 fixedX, fixedY;
        if (!QuickStartTileIsOpen(contentX >> 4, contentY >> 4) &&
            QuickStartFindOpenTileNear(contentX, contentY, 1, &fixedX, &fixedY)) {
            contentX = fixedX;
            contentY = fixedY;
        }
    }

    if (kind == QS_EVENT_ITEM_DROP) {
        // Room flag 3: "confirmed present at least once this visit" -
        // distinct from flag 0 ("we've spawned it"), same two-flag "did it
        // vanish for real, or was it wiped before ever really settling"
        // pattern QuickStartSpawnMelarisMineRewardOnce/
        // QuickStartSpawnGardenRewardOnce already use, kept here for the
        // same reason: without it, a chest that disappears before this
        // function ever confirms it was actually there (e.g. the entity
        // slot getting reused some other way) reads as a genuine pickup on
        // the very next frame it's checked.
        if (QsCheckRoomFlag(flagBase + 0)) {
            if (QuickStartGroundItemAt(contentX, contentY)) {
                QsSetRoomFlag(flagBase + 3);
                return FALSE;
            }
            // The item is gone. That used to be taken as proof the player
            // took it, and it is not: a ground item can also be deleted out
            // from under this room, and when it was, the site latched DONE
            // having shown the player nothing. Probing all 26 content-site
            // rooms found EVERY item-drop site in that state - which is why
            // "? rooms" so often turned out empty, since the item-drop kind
            // is 61% of sites on a fresh save.
            //
            // A pickup means the player was standing on the thing. If they
            // are not within a tile and a half of where it was, this was not
            // a pickup: forget the whole attempt and place it again.
            if (QsCheckRoomFlag(flagBase + 3) && QuickStartPlayerNearSpot(contentX, contentY)) {
                return TRUE;
            }
            QsClearRoomFlag(flagBase + 0);
            QsClearRoomFlag(flagBase + 3);
            // Fall through and re-drop it.
        }
        if (QuickStartGroundItemAt(contentX, contentY)) {
            // Same persistent-leftover adoption as the switch-puzzle kind:
            // ENT_PERSIST outlives a scroll-seam re-entry, room flags don't.
            QsSetRoomFlag(flagBase + 0);
            QsSetRoomFlag(flagBase + 3);
        } else {
            // Extra bit 7 marks a RARE site (QUICKSTART_KINDS_RARE). The
            // ordinary chest roll only ever fills bits 0-1, so the top bit is
            // free to say which pool to draw from - the same trick the miniboss
            // kind already uses for its elite and Red Sword bits.
            // The rare-site pick goes through the same spread the ordinary
            // draw uses (see QuickStartDrawItem) - raw seed/10 could only
            // ever reach the first seven usable entries of the tier.
            u16 rewardItem =
                (extra & 0x80)
                    ? QuickStartDrawAtTier(QuickStartDrawPick(extra & 0x3f), QS_CAT_DROP, QS_TIER_RARE)
                    : QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) pay out without ever
            // being a floor entity, so "delivered" is the test, not "an
            // entity exists" - otherwise the site would latch nothing and
            // re-roll forever.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(flagBase + 0);
            }
        }
    } else if (kind == QS_EVENT_GATE) {
        // ---- The switch-puzzle site: closing gate OR decoy switches ----
        // Room-flag windows (per visit): +0 initialized, +1 variant (set
        // = decoy switches, clear = closing gate), +3 prize seen, +4 the
        // gate switch's last-seen on bit, +5 hint shown, +6 cage open.
        s32 ptx;
        s32 pty;
        Entity* lever = NULL;
        s32 i;
        u32 t;
        // The cage anchors on the site's content spot, and content spots
        // (picked as reward-drop tiles) often sit on the door's approach
        // line - the user kept meeting the puzzle "right in front of the
        // ? room door". Pull the anchor through the same inboard clamp
        // the switches use before anything keys off it, then re-snap to
        // open ground. Pure arithmetic over the room's fixed dimensions,
        // so every frame of the visit recomputes the same spot (the
        // pickup watch below must keep looking where the prize was put).
        {
            s32 ax = contentX;
            s32 ay = contentY;
            QuickStartClampInboard(&ax, &ay);
            if (ax != contentX || ay != contentY) {
                s16 fixedX, fixedY;
                contentX = (s16)ax;
                contentY = (s16)ay;
                if (!QuickStartTileIsOpen(contentX >> 4, contentY >> 4) &&
                    QuickStartFindOpenTileNear(contentX, contentY, 1, &fixedX, &fixedY)) {
                    contentX = fixedX;
                    contentY = fixedY;
                }
            }
        }
        ptx = contentX >> 4;
        pty = contentY >> 4;
        for (i = 0; i < MAX_ENTITIES; i++) {
            Entity* ent = &gEntities[i].base;
            if (ent->kind == OBJECT && ent->id == LIGHTABLE_SWITCH && QuickStartEntityInCurrentRoom(ent)) {
                lever = ent;
                break;
            }
        }
        if (!QsCheckRoomFlag(flagBase + 0)) {
            // First frame of a visit: prize into the cage spot, lever(s)
            // near where the player is standing (they just walked in, so
            // "near the player" IS "near the entrance"), cage shut, clock
            // zero. The variant is a fresh coin flip every visit: the
            // whole room state (levers, cage, unclaimed prize) rebuilds
            // per visit anyway, so re-entering may deal a different
            // puzzle, which suits a gamble room.
            bool32 decoy;
            // A prize from a previous visit can still be sitting on the
            // spot: the item carries ENT_PERSIST, scroll-seam re-entries
            // do not clear persistent entities, and the per-visit room
            // flags (which say "drop one") DO reset. Adopt it rather than
            // stacking a second prize on top.
            if (!QuickStartGroundItemAt(contentX, contentY)) {
                u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
                // A direct-grant prize (the level-2 sword) is handed over
                // rather than caged, so the cage below has nothing to hold
                // and the puzzle is already paid. Bail before dealing it.
                if (QuickStartItemNeedsDirectGrant(rewardItem)) {
                    QuickStartSpawnRewardEntity(rewardItem, contentX, contentY);
                    QsSetRoomFlag(flagBase + 0);
                    QsSetRoomFlag(flagBase + 3);
                    return TRUE;
                }
                if (QuickStartSpawnRewardEntity(rewardItem, contentX, contentY) == NULL) {
                    return FALSE;
                }
            }
            decoy = ((s32)Random() & 1) != 0;
            if (decoy) {
                QsSetRoomFlag(flagBase + 1);
            } else {
                QsClearRoomFlag(flagBase + 1);
            }
            if (!decoy && lever == NULL) {
                s16 lx, ly;
                s32 ax = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
                s32 ay = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
                // Separated from the cage on purpose: the window is priced
                // off this distance, so a switch dealt beside the prize
                // used to hand it over for free.
                if (QuickStartGateSwitchSpot(ax, ay, ptx, pty, &lx, &ly)) {
                    lever = QuickStartSpawnPuzzleSwitch(lx, ly, 0);
                }
            } else if (decoy) {
                // Three switches dealt blind: one frees the prize, one
                // springs the trap, one is a dud - and nothing in the
                // room distinguishes them (per the user: a total gamble,
                // no eye-switch tell). Anchors fan out 2 tiles left/right
                // of the player so the row reads as one obvious cluster.
                const u8* roles = sQuickStartLeverRoles[(s32)Random() % 6];
                s32 px = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
                s32 py = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
                s32 k;
                QuickStartClampInboard(&px, &py);
                for (k = 0; k < 3; k++) {
                    s16 lx, ly;
                    Entity* newLever;
                    // One search per switch, from that switch's own anchor.
                    // It enforces everything the hand-rolled loop here used
                    // to (open ground, no double-deal, off the cage, inboard
                    // of the door band) plus the separation the window is
                    // priced from; when a neighbour's search funnels into a
                    // claimed tile the helper's own pushed anchors find the
                    // next one. Degenerate geometry still just deals fewer
                    // switches - a short deal is survivable because a
                    // trap-pot cage is always liftable.
                    if (!QuickStartGateSwitchSpot(px + (k - 1) * 32, py, ptx, pty, &lx, &ly)) {
                        continue;
                    }
                    newLever = QuickStartSpawnPuzzleSwitch(lx, ly, (u32)(1 + k));
                    if (newLever == NULL) {
                        continue;
                    }
                    QS_SWITCH_ROLE(newLever) = roles[k];
                }
            }
            QuickStartGateWriteTimer(0);
            // Clearance 2: at deal time the player is standing in the
            // doorway they entered through (see QuickStartGateClose).
            QuickStartGateClose(ptx, pty, 2);
            QsClearRoomFlag(flagBase + 6);
            if (!decoy && lever != NULL && lever->frameIndex != 0) {
                QsSetRoomFlag(flagBase + 4);
            }
            if (!QsCheckRoomFlag(flagBase + 5)) {
                QsSetRoomFlag(flagBase + 5);
                if (decoy) {
                    CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 32), 0);
                } else {
                    CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 31), 0);
                }
            }
            QsSetRoomFlag(flagBase + 0);
            return FALSE;
        }
        // Pickup watch - same earned/vanished semantics as the item drop.
        if (QuickStartGroundItemAt(contentX, contentY)) {
            QsSetRoomFlag(flagBase + 3);
        } else if (QsCheckRoomFlag(flagBase + 3)) {
            if (QuickStartPlayerNearSpot(contentX, contentY)) {
                return TRUE;
            }
            // Despawned unclaimed (the cage held the player off past the
            // ground-item timer) - put it back and keep playing.
            QsClearRoomFlag(flagBase + 3);
            {
                u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
                QuickStartSpawnRewardEntity(rewardItem, contentX, contentY);
            }
        }
        if (QsCheckRoomFlag(flagBase + 1)) {
            // ---- Decoy switches, per frame: resolve fresh pulls ----
            // A switch's frameIndex mirrors its flag2 flag, flipping
            // 0<->1 on every hit; a fresh deal starts every switch OFF,
            // so "on and not yet DONE" is exactly "pulled for the first
            // time". The roll happened at the deal - resolving here just
            // reads the stamped role.
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* ent = &gEntities[i].base;
                if (ent->kind != OBJECT || ent->id != LIGHTABLE_SWITCH || !QuickStartEntityInCurrentRoom(ent)) {
                    continue;
                }
                if (QS_SWITCH_ROLE(ent) & QUICKSTART_LEVER_ROLE_DONE) {
                    continue;
                }
                if (ent->frameIndex == 0) {
                    continue;
                }
                QS_SWITCH_ROLE(ent) |= QUICKSTART_LEVER_ROLE_DONE;
                switch (QS_SWITCH_ROLE(ent) & 3) {
                    case QUICKSTART_LEVER_ROLE_PRIZE:
                        // The right guess opens the cage on a clock too -
                        // it used to stay open for the rest of the visit,
                        // which made the win half of a gamble room a free
                        // walk. DOUBLE the closing gate's window, because
                        // this variant's pull is one-shot: the switch is
                        // marked DONE, so a lapse here cannot be re-pulled
                        // the way the gate's single switch can, and the
                        // player has already paid the 1-in-3 gamble. A
                        // lapsed cage is still liftable at the price of a
                        // primed pot, so it is a cost, not a lockout.
                        if (!QsCheckRoomFlag(flagBase + 6)) {
                            s32 window = QuickStartGateWindowFor((ent->x.HALF.HI - gRoomControls.origin_x) >> 4,
                                                                 (ent->y.HALF.HI - gRoomControls.origin_y) >> 4, ptx,
                                                                 pty);
                            window += window;
                            if (window > QUICKSTART_GATE_WINDOW_MAX) {
                                window = QUICKSTART_GATE_WINDOW_MAX;
                            }
                            QuickStartGateWriteTimer((u32)window);
                            QuickStartGateOpen(ptx, pty);
                            QsSetRoomFlag(flagBase + 6);
                        }
                        SoundReq(SFX_SECRET);
                        break;
                    case QUICKSTART_LEVER_ROLE_TRAP: {
                        // The bite: the cage machinery aimed at the
                        // PLAYER. GateClose skips the tile under their
                        // feet and only fills open tiles, so this rings
                        // them in primed pots - lift one and eat the
                        // blast, or hope the room left a gap.
                        s32 playerTX = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) >> 4;
                        s32 playerTY = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) >> 4;
                        QuickStartGateClose(playerTX, playerTY, 0);
                        SoundReq(SFX_MENU_ERROR);
                        break;
                    }
                    default:
                        // The dud: the switch's own click (lightableSwitch's
                        // SFX_110) is all the feedback there is.
                        break;
                }
            }
            // Falls through to the shared clock below rather than
            // returning: both variants run on the same countdown now.
        } else if (lever != NULL) {
            // Any flip of the switch (either direction) restarts the window.
            u32 lt = (lever->frameIndex != 0) ? 1 : 0;
            u32 seen = QsCheckRoomFlag(flagBase + 4) ? 1 : 0;
            if (lt != seen) {
                s32 window;
                if (lt) {
                    QsSetRoomFlag(flagBase + 4);
                } else {
                    QsClearRoomFlag(flagBase + 4);
                }
                window = QuickStartGateWindowFor((lever->x.HALF.HI - gRoomControls.origin_x) >> 4,
                                                 (lever->y.HALF.HI - gRoomControls.origin_y) >> 4, ptx, pty);
                QuickStartGateWriteTimer((u32)window);
                if (!QsCheckRoomFlag(flagBase + 6)) {
                    QuickStartGateOpen(ptx, pty);
                    QsSetRoomFlag(flagBase + 6);
                }
                SoundReq(SFX_SECRET);
            }
        }
        t = QuickStartGateReadTimer();
        if (t > 0) {
            QuickStartGateWriteTimer(t - 1);
        } else if (QsCheckRoomFlag(flagBase + 6)) {
            // Clock ran out: shut it again. Per-tile the close skips the
            // player's own tile, and a trap-pot cage is liftable from the
            // inside anyway (at the price of the primed pot), so it can
            // never become a jail. Clearance 0 on purpose: sparing a
            // 2-tile halo here would let the player park beside the cage
            // and cancel the re-close - the timer IS this variant.
            QuickStartGateClose(ptx, pty, 0);
            QsClearRoomFlag(flagBase + 6);
        }
        return FALSE;
    } else if (kind == QS_EVENT_MINIBOSS) {
        if (QsCheckRoomFlag(flagBase + 2)) {
            // Reward already dropped this visit - just watching for pickup
            // (same "did it vanish for real, or did the room just unload
            // before they grabbed it" distinction QuickStartGroundItemAt
            // exists for on the chest case above).
            return !QuickStartGroundItemAt(contentX, contentY);
        }
        if (QsCheckRoomFlag(flagBase + 0)) {
            const QuickStartEnemyPick* pick = &sQuickStartElites[(extra & 0x7f) % QUICKSTART_MINIBOSS_POOL_SIZE];
            // Which of this room's sites owns an enemy, for both the
            // headcount and the leash below. In a room with a single site
            // this is every enemy, so nothing changes; in Goron Cave, whose
            // four chambers are four sites in one room, it is what stops
            // each site speaking for all four fights.
            //
            // Both halves were wrong without it, and badly. The headcount
            // is how a site decides its miniboss is dead, so with four
            // sites sharing it NO stage paid out until every stage's fight
            // was over, and then all four paid at once. The leash below
            // snaps a not-yet-engaged miniboss back to contentX/contentY,
            // and ran against every enemy in the room, so each frame all
            // four sites yanked all four fights to their own spot in turn -
            // last writer won, and the whole cave's worth of minibosses
            // ended up stacked on the last chamber's tile. Measured
            // frame-by-frame: they spawn correctly at four distinct anchors
            // and are collapsed onto one the very next frame.
            s32 ownerSite = QuickStartFindSiteAt(contentX, contentY);
            s32 i, alive = 0;
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* enemy = &gEntities[i].base;
                if (QuickStartEnemyIsOurs(enemy) &&
                    QuickStartTileBelongsToSite((enemy->x.HALF.HI - gRoomControls.origin_x) >> 4,
                                                (enemy->y.HALF.HI - gRoomControls.origin_y) >> 4, ownerSite)) {
                    alive++;
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
                    //
                    // Never for a Wizzrobe. Vanishing and reappearing
                    // somewhere else IS its behaviour, so parking it fights
                    // its own AI every frame - and with a whole coven of
                    // them it would stack the lot onto one tile.
                    if (QuickStartEnemyIsWizzrobe(pick->id)) {
                        // What a Wizzrobe DOES need is a leash. Traced in
                        // Grimblade's dojo, its reappear step happily picks
                        // spots like (264,504) in a room that is 240x192 -
                        // so it vanishes and simply never comes back, which
                        // is the other half of "it appears once and is
                        // gone". Snapping it to open ground inside the room
                        // while it is away keeps it in the fight without
                        // pinning it anywhere.
                        if (!QuickStartEntityInCurrentRoom(enemy)) {
                            s16 backX, backY;
                            if (QuickStartFindOpenTileNear(contentX, contentY, 1, &backX, &backY)) {
                                enemy->x.HALF.HI = gRoomControls.origin_x + backX;
                                enemy->y.HALF.HI = gRoomControls.origin_y + backY;
                            }
                        }
                    } else if (!PlayerInRange(enemy, 1, 56)) {
                        enemy->x.HALF.HI = gRoomControls.origin_x + contentX;
                        enemy->y.HALF.HI = gRoomControls.origin_y + contentY;
                    }
                }
            }
            // Every one of them, not just the first. This used to return
            // from inside the loop, which was harmless while a miniboss was
            // always a single enemy and silently left the other Wizzrobes
            // unleashed the moment there were three.
            if (alive > 0) {
                return FALSE;
            }
            // Dead - drop the reward and start watching for pickup.
            // A non-elite miniboss rolled with extra bit 6 pays the Red
            // Sword - once: if the sword is already owned the kill falls
            // through to the ordinary heart piece, so repeat encounters
            // stay worth fighting without stacking dead swords. The sword
            // CANNOT be a floor item: CreateObject(GROUND_ITEM,
            // ITEM_RED_SWORD) never creates an entity at all (traced
            // frame-by-frame in the emulator - equipment has no
            // ground-item form in vanilla; it only ever arrives through
            // chests and scripts). So it goes through the real GiveItem
            // path (inventory + item slot + sfx) with an explicit message,
            // the same shape the skill-scroll pickup already uses. Setting
            // room flag +2 with no item on the floor is correct: the
            // pickup-watch above reads "no ground item left" as collected
            // and latches DONE.
            if (!(extra & 0x80) && (extra & 0x40) && GetInventoryValue(ITEM_RED_SWORD) == 0) {
                GiveItem(ITEM_RED_SWORD, 0);
                MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 13));
                MsgInit();
                QsSetRoomFlag(flagBase + 2);
                gSave.miniboss_kills++;
                return FALSE;
            }
            {
                // Elite sites (extra bit 7, see QuickStartRandomizeContentSiteOnce)
                // pay a full Heart Container; everything else the ordinary
                // heart piece.
                //
                // Unless the site's own row names a reward tier, which the
                // Goron cave's chain uses to make each chamber pay better
                // than the last. The tier is a static property of the row,
                // not of the roll, so it is read from the table here rather
                // than packed into `extra` - there is no bit left in that
                // byte anyway (0-5 roster index, 6 Red Sword, 7 elite).
                // Which item WITHIN the tier still varies per run: the pick
                // is the same roll that chose the miniboss.
                s32 ownerSite = QuickStartFindSiteAt(contentX, contentY);
                u8 tier = (ownerSite >= 0) ? QuickStartSiteRewardTier(ownerSite) : QS_SITE_REWARD_DEFAULT;
                u16 payout = (extra & 0x80) ? ITEM_HEART_CONTAINER : ITEM_HEART_PIECE;
                if (tier != QS_SITE_REWARD_DEFAULT) {
                    // Spread the pick, as every other draw does - a raw
                    // seed could only reach a tier's first few entries.
                    payout = QuickStartDrawAtTier(QuickStartDrawPick(extra & 0x3f), QS_CAT_DROP, tier - 1);
                }
                // "Delivered", not "an entity exists": a direct-grant
                // payout (the level-2 sword) is handed over without ever
                // lying on the floor.
                if (QuickStartRewardDelivered(payout, contentX, contentY)) {
                    QsSetRoomFlag(flagBase + 2);
                    // Tied to the same QsSetRoomFlag(flagBase + 2) success path so this
                    // only ever counts once per miniboss, even if the spawn
                    // fails and this branch legitimately retries on a later
                    // frame (see QuickStartComputeScore,
                    // docs/QUICKSTART_ROADMAP.md).
                    gSave.miniboss_kills++;
                }
            }
            return FALSE;
        }
        {
            // Through the placer, not straight onto contentX/contentY. A
            // site's content spot is hand-picked and several are simply
            // wrong (Hyrule Castle Cellar's is 184px below its own floor),
            // and even a good one can be a tile a Darknut cannot turn
            // around in.
            const QuickStartEnemyPick* pick = &sQuickStartElites[(extra & 0x7f) % QUICKSTART_MINIBOSS_POOL_SIZE];
            // Owned by this site, so a room with several of them - Goron
            // Cave's four chambers, the Boomerang chamber's five quadrants -
            // keeps each fight where it belongs.
            if (QuickStartSpawnEnemiesOnOpenTiles(pick->id, pick->form, contentX, contentY,
                                                  QuickStartMinibossCount(pick->id),
                                                  QuickStartFindSiteAt(contentX, contentY)) > 0) {
                QsSetRoomFlag(flagBase + 0);
            }
        }
    } else if (kind == QS_EVENT_WAVES) {
        return QuickStartSetupWaveRoomContent(extra, contentX, contentY, flagBase);
    } else if (kind == QS_EVENT_POT_LOTTERY) {
        return QuickStartSetupPotRoomContent(extra, contentX, contentY, flagBase);
    } else if (kind == QS_EVENT_CHEST_LOTTERY) {
        return QuickStartSetupChestLotteryContent(extra, contentX, contentY, flagBase);
    } else if (kind == QS_EVENT_FAIRY) {
        QuickStartSetupFairyRoomContent(contentX, contentY, flagBase);
    } else {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
                // The NPC is live - watch for the script's own "resolved"
                // write and fold it back into the caller's DONE latch, so
                // the event stays resolved for the run but rolls fresh next
                // run (see QUICKSTART_NPC_RESOLVED_FLAG's comment).
                //
                // Only if this Zelda is THIS event's own, though: rooms
                // with several sites (the Boomerang chamber) can roll NPC
                // for more than one of them, and the one-Zelda-per-room
                // rule means only the first spawns - without the distance
                // scope, resolving that one would falsely latch every
                // other NPC site in the room DONE too.
                s32 dx = gEntities[i].base.x.HALF.HI - (gRoomControls.origin_x + contentX);
                s32 dy = gEntities[i].base.y.HALF.HI - (gRoomControls.origin_y + contentY);
                if (dx >= -64 && dx <= 64 && dy >= -64 && dy <= 64) {
                    return CheckGlobalFlag(QUICKSTART_NPC_RESOLVED_FLAG) != 0;
                }
                return FALSE;
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
                // Bit 0 of extra is the friendly/evil roll, delivered to
                // the (single, shared) script via the scratch flags.
                QuickStartLoadNpcScratchFlags((u8)extra);
                QuickStartMakeNpcTalkable(npc, sQuickStartEventNpcScripts[0]);
            }
        }
    }
    return FALSE;
}

// The retired synthetic-entrance path's own wrapper. Every ladder and door
// entrance is gone now (the retired ladder-entrance table is empty and
// QuickStartFindSlotForCurrentRoom always returns -1), so this is
// unreachable in play - it is kept, and still called from the dispatcher,
// so the retired system stays a coherent whole rather than a half-removed
// one.
static void QuickStartSetupSlotRoomContent(s32 slotIndex) {
    s16 contentX, contentY;
    QuickStartGetLadderContentOffset(slotIndex, &contentX, &contentY);
    QuickStartClearLadderRoomObstacles();
    if (QuickStartLadderCheckDone(slotIndex)) {
        return;
    }
    if (QuickStartSetupEventContent(QuickStartSlotGetKind(slotIndex), QuickStartSlotGetExtra(slotIndex),
                                    contentX, contentY, 0)) {
        QuickStartSlotSetDone(slotIndex);
    }
}

// --- Melari's Mine's other 2 real doors (Southeast/East) --------------------
//
// See gExitList_MelarisMine_Main (transitions.c) - both real vanilla doors
// still lead exactly where they always did, untouched; the room a player
// lands in via either one IS the "?" room content directly, no synthetic
// warp/pool-room indirection needed (unlike the ladder/2-door systems
// above - which is what every single-door "? room" does now).
// East ("the one with all the beds in it"): the user walked its own
// walkable floor space directly and gave its bounding box in room-local
// coordinates - (88,65) to (184,94) - rather than this session's earlier,
// unsurveyed guess of the shared (120,120) ladder-room convention. Content
// sits at that box's center.
#define QUICKSTART_MELARI_EAST_CONTENT_X 136
#define QUICKSTART_MELARI_EAST_CONTENT_Y 80
// Southeast: content point given directly by the user.
#define QUICKSTART_MELARI_SOUTHEAST_CONTENT_X 152
#define QUICKSTART_MELARI_SOUTHEAST_CONTENT_Y 83

static u8 QuickStartMelariEastGetKind(void) {
    return QsCheckFlag(GF_MELARI_EAST_KIND_BIT) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
}

static u8 QuickStartMelariEastGetExtra(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 3; b++) {
        if (QsCheckFlag(GF_MELARI_EAST_EXTRA_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static u8 QuickStartMelariSoutheastGetKind(void) {
    return QsCheckFlag(GF_MELARI_SOUTHEAST_KIND_BIT) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
}

static u8 QuickStartMelariSoutheastGetExtra(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 3; b++) {
        if (QsCheckFlag(GF_MELARI_SOUTHEAST_EXTRA_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

// Called from Melari's Mine Main's own hub dispatch, same "roll it before
// the player can possibly reach it" timing as the ladder/2-door/region
// chain draws there already use.
static void QuickStartRandomizeMelariEastOnce(void) {
    u8 kind, extra;
    s32 b;
    if (QsCheckFlag(GF_MELARI_EAST_RANDOMIZED)) {
        return;
    }
    kind = ((s32)Random() % 2) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
    if (kind == QS_EVENT_NPC) {
        QsSetFlag(GF_MELARI_EAST_KIND_BIT);
        extra = (u8)((s32)Random() % 2);
    } else {
        extra = (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE);
    }
    for (b = 0; b < 3; b++) {
        if (extra & (1 << b)) {
            QsSetFlag(GF_MELARI_EAST_EXTRA_BIT(b));
        }
    }
    QsSetFlag(GF_MELARI_EAST_RANDOMIZED);
}

// Southeast's own copy of the above - separate flags/room-state, same
// random chest/NPC shape.
static void QuickStartRandomizeMelariSoutheastOnce(void) {
    u8 kind, extra;
    s32 b;
    if (QsCheckFlag(GF_MELARI_SOUTHEAST_RANDOMIZED)) {
        return;
    }
    kind = ((s32)Random() % 2) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
    if (kind == QS_EVENT_NPC) {
        QsSetFlag(GF_MELARI_SOUTHEAST_KIND_BIT);
        extra = (u8)((s32)Random() % 2);
    } else {
        extra = (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE);
    }
    for (b = 0; b < 3; b++) {
        if (extra & (1 << b)) {
            QsSetFlag(GF_MELARI_SOUTHEAST_EXTRA_BIT(b));
        }
    }
    QsSetFlag(GF_MELARI_SOUTHEAST_RANDOMIZED);
}

// Shared by both rooms - each one's own pre-existing vanilla decorations
// (the statues/shrine props confirmed present via an emulator entity dump
// the first time each room was loaded, OBJECT-kind but not our own
// GROUND_ITEM/SHOP_ITEM/ZELDA, so left alone) stay untouched; only real
// obstacles (vanilla NPCs, enemies) get cleared, same idempotent
// per-frame pattern
// QuickStartClearMelarisMineObstacles already use elsewhere in this file.
static void QuickStartClearMelariRoomObstacles(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == NPC && ent->id != ZELDA) {
            DeleteEntity(ent);
        } else if (ent->kind == ENEMY) {
            DeleteEntity(ent);
        }
    }
}

// East room's own content dispatch - a plain chest (one reward off the
// same tier draw the ladder/2-door chests already use
// from) or a talking NPC (same 2 canned scripts sQuickStartEventNpcScripts
// already uses), whichever QuickStartRandomizeMelariEastOnce rolled.
// Simpler double-flag-free version of the ladder system's own chest/NPC
// handling above: this room doesn't need a slotIndex, so there's no
// generic accessor plumbing to reuse, just a direct room-flag check.
static void QuickStartSetupMelariEastRoomContent(void) {
    QuickStartClearMelariRoomObstacles();
    if (QsCheckFlag(GF_MELARI_EAST_DONE)) {
        return;
    }
    // Routed through the shared event path instead of the inlined copy of
    // the chest/NPC handling this used to carry. That copy was the bug: it
    // gated respawning on a bare room flag, and room flags reset on every
    // room load, so leaving and re-entering dropped a fresh reward every
    // time. The shared path carries the two-flag "spawned" / "confirmed
    // present" pair that tells a real pickup apart from a room that merely
    // unloaded, and reports back once the reward is genuinely gone - which
    // is what the latch above records, permanently.
    if (QuickStartSetupEventContent(QuickStartMelariEastGetKind(), QuickStartMelariEastGetExtra(),
                                    QUICKSTART_MELARI_EAST_CONTENT_X, QUICKSTART_MELARI_EAST_CONTENT_Y, 0)) {
        QsSetFlag(GF_MELARI_EAST_DONE);
    }
}

// Southeast's own copy of the above - separate flags/room-state/content
// point, same random chest/NPC shape. No longer the forced Shop (see the
// GF_MELARI_SOUTHEAST_* comment above for why).
static void QuickStartSetupMelariSoutheastRoomContent(void) {
    QuickStartClearMelariRoomObstacles();
    if (QsCheckFlag(GF_MELARI_SOUTHEAST_DONE)) {
        return;
    }
    // Same fix as the East room above, same reasoning.
    if (QuickStartSetupEventContent(QuickStartMelariSoutheastGetKind(), QuickStartMelariSoutheastGetExtra(),
                                    QUICKSTART_MELARI_SOUTHEAST_CONTENT_X, QUICKSTART_MELARI_SOUTHEAST_CONTENT_Y,
                                    0)) {
        QsSetFlag(GF_MELARI_SOUTHEAST_DONE);
    }
}

// --- PILOT: room-keyed "? room" content ------------------------------------
//
// See the GF_CONTENT_SITE_* comment for the model. Each row is a real
// vanilla room reached through its own real vanilla door, plus the spot
// inside it where the randomized event goes.
//
// The 5 rows below are North Hyrule Field's tree interiors. Content sits at
// (0x78,0x60) - just north of the (0x78,0x78) spot every one of these
// rooms' own real return transitions lands the player at (confirmed from
// gExitList_HyruleField_NorthHyruleField's endX/endY for each door), so the
// reward/NPC is visible on arrival without being close enough to collide
// with the player as they spawn in.
//
// The Boomerang trees each list a real WARP_TYPE_AREA down into the shared
// ROOM_CAVES_BOOMERANG hub, left fully vanilla - but probing the live
// actTile table shows those inner doors are not armed (0x00), so they do
// not fire and the trees behave as plain one-room ? rooms. The hub row
// below is therefore currently unreachable in play; it is kept because it
// costs one table row and would start working the moment that inner door
// is made to fire, not because it is reachable today.
// The four Boomerang tree hollows are deliberately NOT in this table. Each
// is a landing with a ladder down into the shared chamber, and the chamber
// already carries one event per tree in the corner that tree arrives at -
// so the events live down there rather than on top of the ladders.
//
// large: which of the two size-restricted kind pools this site rolls from,
// the same split the retired ladder/door slots used (QuickStartPickSmallKind
// vs QuickStartPickLargeKind). Small rooms get puzzle/dialogue content
// (chest, NPC, pot lottery, chest lottery); only rooms with real floor
// space get combat (miniboss, 3-wave gauntlet) or a fairy pair. Almost
// everything here is a cramped tree hollow or cave nook, so `large` is the
// exception, not the rule.
// Which set of event kinds a site may roll.
enum {
    QUICKSTART_KINDS_SMALL, // puzzle/dialogue only - cramped tree hollows, cave nooks
    QUICKSTART_KINDS_LARGE, // combat and fairies - rooms with real floor space
    QUICKSTART_KINDS_ANY,   // everything, for rooms big and clear enough to host anything
    // High-risk, high-reward, for sites the player pays to reach (item
    // gates, Minish routes): no roll at all - ALWAYS a miniboss from the
    // level-5 roster, and its kill drops a HEART CONTAINER instead of the
    // normal heart piece (the elite bit rides in the extra byte's top bit;
    // see QuickStartRandomizeContentSiteOnce and the miniboss reward drop).
    QUICKSTART_KINDS_ELITE,
    // No roll either: always a plain item drop, always off the RARE pool
    // (QS_TIER_RARE). For sites that are meant to be worth
    // finding in themselves rather than worth fighting - the Boomerang
    // chamber's central staircase is the one that has it today.
    QUICKSTART_KINDS_RARE,
    // Always a miniboss, with no elite upgrade and no Red Sword roll. Only
    // useful paired with a row's rewardTier, which then decides what the
    // kill pays - that pairing is what builds the Goron cave's escalating
    // chain (common, then uncommon, then rare) out of one kind.
    QUICKSTART_KINDS_MINIBOSS,
};


typedef struct {
    u8 area;
    u8 room;
    u8 kinds;
    s16 contentX;
    s16 contentY;
    // Both optional, and deliberately last: C zero-fills the fields a short
    // initializer omits, so every row that predates them keeps its exact
    // meaning without being touched.
    //
    // gateKinstone: this site does not exist until that kinstone fusion is
    // done. 0 = always present. Only the Goron cave uses it, to keep each
    // stage of its chain sealed behind the wall the fusion punches open.
    u8 gateKinstone;
    // rewardTier: QS_SITE_REWARD_*, overriding the kind's usual payout.
    u8 rewardTier;
} QuickStartContentSite;

static const QuickStartContentSite sQuickStartRoomContentSites[QUICKSTART_CONTENT_SITE_COUNT] = {
    // The event for this tree lives one floor DOWN, in the fairy fountain
    // cave its staircase leads to, not in the tree hollow itself - the
    // hollow is a landing with a staircase in it, and the event was sitting
    // on top of that staircase. The tree is a pass-through now; its
    // staircase tile reads ACT_TILE_40, so it opens on touch like any other
    // vanilla door.
    { AREA_CAVES, ROOM_CAVES_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },
    // South Hyrule Field's 3 converted doors. Unlike the Boomerang trees
    // these are true dead ends - one room each, single border exit back to
    // the field - so they're the simplest possible shape for this model.
    // Content sits just north of each room's own (0x78,0x78) arrival spot,
    // same convention as the tree rooms above.
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE, QUICKSTART_KINDS_ANY, 0x78, 0x60 },
    { AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN, QUICKSTART_KINDS_ANY, 0x78, 0x60 },
    { AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_RUPEE, QUICKSTART_KINDS_ANY, 0x78, 0x60 },
    // The Boomerang cave hub. Currently UNREACHABLE in play (see above and
    // the CORRECTION comment on its door in transitions.c): neither its own
    // mouth, nor the trees' doors down into it, nor its exit back to the
    // field are armed with door actTiles. Content is defined anyway so the
    // room is ready if that changes; it costs one row and one flag slot.
    // The Boomerang chamber. FIVE events live here, not one: all four
    // trees' ladders come down into this same room at its four corners, and
    // the staircase between the trees comes down into its middle, so per the
    // user's own call each of those five entrances gets its own event in the
    // corner it arrives at. Whoever comes down any one ladder can reach all
    // five - that concentration is deliberate.
    //
    // The middle one replaces the vanilla Magical Boomerang chest, which is
    // deleted on entry (QuickStartClearBoomerangChest).
    //
    // Spots are each entrance's own arrival point nudged onto open floor,
    // read off a live actTile dump of the room rather than guessed: the
    // chamber is a ring, and its middle band (y 152-216) and the two side
    // columns are the only walkable parts.
    // Spots are the centres of boxes the user walked inside the chamber,
    // replacing the earlier guesses derived from each entrance's arrival
    // point. Walked ground truth beats derived coordinates here for the
    // same reason it has everywhere else in this file.
    { AREA_CAVES, ROOM_CAVES_BOOMERANG, QUICKSTART_KINDS_SMALL, 72, 78 },    // northwest tree,  box (56,60)-(88,97)
    { AREA_CAVES, ROOM_CAVES_BOOMERANG, QUICKSTART_KINDS_SMALL, 266, 58 },   // northeast tree,  box (249,38)-(283,78)
    { AREA_CAVES, ROOM_CAVES_BOOMERANG, QUICKSTART_KINDS_SMALL, 72, 285 },   // southwest tree,  box (53,268)-(92,303)
    // The southeast box came through as (246,183) (281,183) (281,229)
    // (246,289) - three corners agree on y=229 and the fourth reads 289, so
    // this takes the rectangle the three agree on. Easy to nudge if 289 was
    // the intended one.
    { AREA_CAVES, ROOM_CAVES_BOOMERANG, QUICKSTART_KINDS_SMALL, 263, 206 },  // southeast tree,  box (246,183)-(281,229)
    // The staircase in the middle of the chamber - the one entrance that is
    // NOT the bottom of a Boomerang tree, and the only way in that costs a
    // deliberate trip rather than a tree the player was passing anyway. Per
    // the user, it always pays a RARE drop instead of rolling with the rest.
    { AREA_CAVES, ROOM_CAVES_BOOMERANG, QUICKSTART_KINDS_RARE, 170, 158 },   // the staircase,   box (153,143)-(188,173)
    // Trilby Highlands' 4 converted doors - all true dead ends, same shape
    // as South Hyrule Field's. The Keese Chest and Fairy Fountain caves are
    // the two reached by bombing a wall open.
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },
    { AREA_CAVES, ROOM_CAVES_TRILBY_KEESE_CHEST, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },
    { AREA_CAVES, ROOM_CAVES_TRILBY_RUPEE, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },
    { AREA_CAVES, ROOM_CAVES_TRILBY_FAIRY_FOUNTAIN, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },
    // Trilby's through-cave - the room behind the two exposed ladders at
    // (0x98,0x284) and (0x118,0x284). Deferred at the pilot as a "future
    // 2-door candidate" and then never wired, which left its two vanilla
    // ladder transitions being cancelled by containment (nothing blessed
    // the destination) - the user's "connections seem to have been cut
    // off" report. The collision survey says the name lies: the room is
    // TWO separate dead-end chambers that happen to share one room id
    // (left, tiles 2-9; right, tiles 12-23; the ornate doorframe between
    // them is walled off on this layer), so each ladder gets its own
    // site, the same multi-site-per-room shape as Goron Cave's chambers.
    { AREA_CAVES, ROOM_CAVES_TRILBY_HIGHLANDS, QUICKSTART_KINDS_SMALL, 0x58, 0x48 },   // left chamber
    { AREA_CAVES, ROOM_CAVES_TRILBY_HIGHLANDS, QUICKSTART_KINDS_SMALL, 0x118, 0x48 },  // right chamber
    // --- The last 5 synthetic entrances, converted -------------------------
    //
    // Castle Garden's two ladders, Lon Lon Ranch's Goron Cave door, Link's
    // House, and North Hyrule Field's Heart Piece Hallway cave. These were
    // the four rooms held back from the earlier region conversions on the
    // grounds that they lead into "sprawling interiors" rather than dead
    // ends; the user's own call was to convert them anyway, "regardless of
    // if they are single door rooms or two-door rooms". Each pocket turns
    // out to be genuinely closed once its one escape route is dealt with,
    // so nothing here needs a synthetic teleport to stay contained:
    //
    //  - Great Fairy cellar and Grimblade's dojo entrance: single rooms
    //    whose only exit is back to Castle Garden Main. Nothing to do.
    //  - Goron Cave: Stairs + Main, and Main's only exit is back to the
    //    Stairs. Both rooms get their own event.
    //  - Link's House: Entrance + Bedroom, and the Bedroom's only exit is
    //    back to the Entrance. Both rooms get their own event.
    //  - Heart Piece Hallway: vanilla also runs it onward into
    //    ROOM_CAVES_TO_GRAVEYARD, which reaches Royal Valley and escapes
    //    the run. That one door is neutralized in transitions.c
    //    (gExitList_Caves_HeartPieceHallway) rather than here.
    //
    // Content coordinates are each room's own vanilla arrival spot (the
    // endX/endY of the door that leads there, transitions.c) nudged 24px
    // clear of it, the same convention as every row above - north where
    // there's room north, south where the arrival spot is already at the
    // top of the room.
    // The cellar and the dojo both keep a vanilla LADDER_UP fixture on the
    // spot the player arrives at, and a ladder occupies a full 3x3 block of
    // tiles. A pot lottery centred on the arrival point loses its whole
    // middle column to it - confirmed in the emulator, 3 of the 9 pots
    // shattered into smoke the frame they spawned. Both content points are
    // moved clear of their ladder's block rather than sitting the usual
    // 24px off the arrival spot: further up the cellar, and off to one side
    // in the dojo (which is too short to go further up).
    // Lon Lon Ranch's shallow-water cave - the one a Kinstone fusion reveals
    // the staircase down into. Its exit is back on vanilla (transitions.c), so
    // the stairs now lead somewhere instead of dumping the player in Castle
    // Garden. Measured: 240x160, one chamber of 59 tiles reachable from the
    // (120,120) arrival, and the site's own sweep takes care of the vanilla
    // big-wallet chest sitting at (120,40).
    //
    // This row REPLACES the Hyrule Castle Cellar site rather than adding a
    // 31st. The site block is 13 flag bits each from offset 266, and the
    // constants stacked above it now run to 703 against a bank ceiling of 707
    // - a 31st site would need all of them shifted 13 higher, which does not
    // fit. (The comment on QUICKSTART_CONTENT_SITE_COUNT still says there is
    // one site of headroom; that was true when it was written, before
    // GF_FUSION_RELOADED_ID_BIT and GF_FUSER_SCATTER_ROLLED took 692-703.)
    //
    // The cellar slot was dead twice over and is no loss: its room is
    // unreachable, shadowed by the Castle Garden northwest ladder's redirect
    // to a drawn pool room, and its content spot was y=376 in a room only 192
    // tall - outside its own room, so it could never have worked even if the
    // room were reachable. Both facts are in the roadmap's open-bugs list;
    // this closes them by reclaiming the bits for a room that does work.
    { AREA_CAVES, ROOM_CAVES_LON_LON_RANCH_WALLET, QUICKSTART_KINDS_SMALL, 120, 72 },
    // Castle Garden's southeast ladder leads to this dojo's ante room, and
    // the ante room scroll-seams north into the dojo proper. The event goes
    // in the DOJO, not the ante room - the ante room is a corridor, and the
    // dojo is a 240x192 arena with 77 unobstructed floor tiles. It rolls
    // from the large pool accordingly, so this is a place a miniboss or a
    // 3-wave gauntlet can actually be fought. Its vanilla content (the
    // dojo-master NPC and its props) is swept first; see
    // QuickStartSetupDojoRoom in the monitor.
    //
    // This room was the shop until now. The shop has moved out entirely
    // (retired; the shop is a fixed hub room now) and the Melari's Mine link
    // that used to reach it is gone with it.
    // Arena CENTER (row 5 of the 2-9 arena band), not the old (0x78,0x88):
    // that spot sat two tiles from the seam mouth at the room's south edge,
    // and the closing gate's 3x3 pot cage around it walled the entrance
    // shut - the player could not reach the room, let alone the lever
    // (user-reported; measured 0px of northward progress from the seam).
    { AREA_DOJOS, ROOM_DOJOS_GRIMBLADE, QUICKSTART_KINDS_LARGE, 0x78, 0x58 },
    { AREA_GORON_CAVE, ROOM_GORON_CAVE_STAIRS, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },                  // arrives (0x78,0x78)
    // --- Goron Cave's main chamber: a four-stage kinstone progression ----
    //
    // The one room in this file that is a dungeon rather than a single
    // event. It is a 240x720 vertical shaft, and vanilla cuts it into
    // chambers with sub_StateChange_GoronCave_Main (roomInit.c): five
    // kinstone fusions, three of which also paint a wall open. Measured
    // reachable tiles from the (0x78,0x278) arrival spot, per state:
    //
    //   no fusions   36 tiles, rows 34-41   the entry chamber
    //   KINSTONE_25  +51 tiles, rows 23-33
    //   KINSTONE_2A  +0                     adds a Goron, opens no wall
    //   KINSTONE_26  +89 tiles, rows 13-22
    //   KINSTONE_2B  +0                     adds a Goron, opens no wall
    //   KINSTONE_2F  +60 tiles, rows 3-12   the top chamber
    //
    // So the room supports FOUR sealed chambers, not the eight stages the
    // chain was first sketched as - 2A and 2B buy no floor. Per the user's
    // own call the chain is four stages, strictly one per chamber:
    // a free "? room" roll to open, then three minibosses paying an
    // escalating tier. Each row is gated on the fusion that opens its own
    // chamber, so nothing is visible or reachable before its wall is.
    //
    // Content spots are the central column of each chamber, taken from the
    // per-state reachable sets rather than guessed: every one is reachable
    // from the arrival spot in its own state and has all eight neighbours
    // open, which is what a miniboss needs to turn around in.
    //
    // REACHABLE. This was written as "unreachable, waiting on a position
    // box" and that was wrong twice over; both errors were mine, not the
    // game's.
    //
    // The first was the overworld gate. Vanilla's
    // sub_StateChange_HyruleField_LonLonRanch paints two blocking tiles over
    // the cave mouth AND spawns the wall-punching Goron in front of them,
    // both only while KINSTONE_29 is unfused - one gate, lifted by one
    // fusion. This file deleted the Goron NPC but could not delete the
    // tiles, so the barrier stayed with nothing standing in front of it.
    // The user found it in play: "there is still an invisible barrier where
    // the Goron stood". The Goron is left alone now, and the fusion opens
    // the cave exactly as vanilla intends.
    //
    // The second was the stairs room's own door up (0x78,0x38), reported
    // here as sitting on a solid tile and never firing. It fires. The
    // trigger is at the FOOT of the staircase fixture, around (120,72) -
    // measured: standing anywhere in (112-128, 72-80) opens the main
    // chamber immediately. Two bad probes hid it. Walking up the middle
    // column stalls at y=101 because that is where this room's own content
    // site drops its reward, and picking it up opens a message box that
    // blocks all input - the same trap this file has already been caught by
    // twice. Walking up a side column instead overshoots to the top row and
    // passes above the trigger entirely. Mash through the pickup and the
    // walk continues into the chamber.
    //
    // So the whole route is walkable: ranch -> fuse KINSTONE_29 -> cave
    // stairs -> main chamber, verified end to end with real input.
    { AREA_GORON_CAVE, ROOM_GORON_CAVE_MAIN, QUICKSTART_KINDS_LARGE, 120, 600, 0, QS_SITE_REWARD_DEFAULT },
    { AREA_GORON_CAVE, ROOM_GORON_CAVE_MAIN, QUICKSTART_KINDS_MINIBOSS, 120, 440, KINSTONE_25,
      QS_SITE_REWARD_COMMON },
    { AREA_GORON_CAVE, ROOM_GORON_CAVE_MAIN, QUICKSTART_KINDS_MINIBOSS, 152, 280, KINSTONE_26,
      QS_SITE_REWARD_UNCOMMON },
    { AREA_GORON_CAVE, ROOM_GORON_CAVE_MAIN, QUICKSTART_KINDS_MINIBOSS, 120, 72, KINSTONE_2F,
      QS_SITE_REWARD_RARE },
    { AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE, QUICKSTART_KINDS_ANY, 0x78, 0x60 },
    // The smithy, Link's House's right-hand room. Reachable and ordinary
    // now that the global START flag is set - it used to load the opening
    // cutscene's entity list (Link's father, Zelda, the orchestrator)
    // instead of its own furniture. Content at (120,104), clear of the
    // workbench row along the top wall and the anvil at (152,88).
    { AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH, QUICKSTART_KINDS_ANY, 120, 104 },
    // Link's House upstairs, reached by the stairs from the entrance. It was
    // unreachable for a while because it ran script_PlayerIntro and dumped
    // the player into South Hyrule Field within a second - a symptom of the
    // global START flag never being set, which GameTask_Transition now does.
    // The stairs point here again (transitions.c). Left on the SMALL pool on
    // purpose: it is a cramped bedroom with a bed and a table, not an arena.
    { AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM, QUICKSTART_KINDS_SMALL, 0x58,
      0x40 },  // arrives (0x58,0x28)
    { AREA_CAVES, ROOM_CAVES_HEART_PIECE_HALLWAY, QUICKSTART_KINDS_SMALL, 0x78, 0xb0 },               // arrives (0x78,0xc8)
    // Lon Lon Ranch's house, both rooms. Unreachable until now: the west
    // door is a scripted HOUSE_DOOR_EXT running vanilla's key gate, which
    // nothing in this run satisfies, and the east room's route onward is
    // barred by the interior door. Both are unlocked in game.c
    // (QuickStartUnlockRanchHouseDoors and the HOUSE_DOOR_INT unk7d clear),
    // so each room is a normal one-door "? room" now, entered by its own
    // front door and left the same way.
    { AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST, QUICKSTART_KINDS_SMALL, 0x68, 0x60 },  // arrives (0x68,0x78)
    { AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST, QUICKSTART_KINDS_SMALL, 0x78, 0x60 },  // arrives (0x78,0x78)
    // Lon Lon Ranch's through-cave, back on its own vanilla doors now that
    // the synthetic connector that used to swallow them is retired. Still
    // gated by vanilla's Mole Mitts dirt on the way in, which is the point -
    // it reads as a real secret rather than an ordinary cave mouth.
    //
    // The event sits at (120,88), on the open upper floor. That is
    // deliberately well clear of the diggable dirt block in the room's
    // lower left (x 24-104, y 168-248, read off a live actTile dump) rather
    // than clearing that dirt away: nothing here modifies tile data. Writing
    // foreign tile types into a room's tileset is exactly what produced the
    // graphical artifacts and invisible walls in the Boomerang chamber, and
    // placing the event on floor that is already open makes the question
    // moot.
    { AREA_CAVES, ROOM_CAVES_LON_LON_RANCH, QUICKSTART_KINDS_SMALL, 0x78, 0x58 },
    // Melari's Mine's southwest side room. Its two siblings (East and
    // Southeast) have had bespoke content dispatchers since before this
    // table existed; this one went the other way, because its door was
    // pointed at the shop instead. With the door back on vanilla (see
    // sQuickStartLinks and transitions.c) the room needs an event of its
    // own, and the table is the right home for a new one rather than a
    // third copy of the bespoke pair. Content at (152,83), the same spot
    // its structurally identical Southeast sibling already uses.
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST, QUICKSTART_KINDS_SMALL, 152, 83 },
    // The two Minish-gated rooms. These are the only destinations in the
    // whole five-region pool that a normal-sized Link cannot reach, and both
    // hang off South Hyrule Field: its exit list has always carried them
    // (transitions.c, gExitList_HyruleField_SouthHyruleField), they were just
    // unreachable because nothing in this mode ever shrank the player. The
    // field's Minish portal opens the route - hidden under its tree stump
    // until a Pegasus Boots dash reveals it (vanilla's own PLAYER_BOUNCE
    // path; the old force-reveal is gone per the user's call), so these two
    // rooms are part of what a boots run buys. Once shrunk, they are
    // ordinary "? rooms" entered by their own real vanilla doors.
    //
    // The cave at (376,216) in the field; a wide open Minish-scale cavern,
    // and its vanilla exit is a plain INSTANT_MINISH border straight back to
    // the field, so it is a clean dead end. Content 40px north of its
    // (0x78,0xb8) arrival spot.
    { AREA_MINISH_CAVES, ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE, QUICKSTART_KINDS_ANY, 0x78, 0x50 },
    // The tiny door at (72,456) in the field. One of the shared Minish House
    // Interiors template rooms, so it takes the same (0x78,0x78) arrival and
    // 40px-north content convention the rest of that family uses - and stays
    // on the SMALL pool for the same reason they do: it is a one-screen
    // mushroom interior, not an arena.
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD, QUICKSTART_KINDS_SMALL, 0x78, 0x50 },
    // Castle Garden's northeast wall hole - the third Minish-gated site, and
    // the most expensive route in the game so far: it takes the Pegasus
    // Boots (dash the stump tree open), the Minish portal (shrink), and then
    // the hole in the garden's north wall at x~776. Inside is the East
    // wall-passage room: a small walled chamber over an entry strip, joined
    // by a climbable column at tile x=8 (collision-scanned live; the room's
    // one vanilla exit is an INSTANT_MINISH south border straight back to
    // the garden, so it is a clean dead end). Priced accordingly: ELITE -
    // always a level-5 miniboss, and the kill pays a Heart Container.
    // Content spot (136,104) is the chamber's centre tile (8,6), open with
    // all four neighbours open.
    //
    { AREA_CASTLE_GARDEN_MINISH_HOLES, ROOM_CASTLE_GARDEN_MINISH_HOLES_0, QUICKSTART_KINDS_ELITE, 136, 104 },
    // Its West twin, the hole at x~232 above the west fountain. Physically
    // identical to East - measured, both are 240x240 with the same 11x9
    // open rectangle (local 48-176 x 48-176) and the same single pillar at
    // tile (7,5), 80 reachable tiles from the (120,184) arrival - so it
    // takes the same content spot. NOT elite: one guaranteed miniboss per
    // region reads as special, two reads as a farm, so this one gets the
    // full roll instead. ANY rather than SMALL because East proves the
    // footprint hosts a level-5 miniboss comfortably.
    //
    // This row is also what makes the west hole ENTERABLE, which is the
    // actual bug the user reported ("its door does not fire"). Both holes
    // are driven by the same mechanism - SpecialWarpManager (manager
    // subtype 6, room property 8) walks Castle Garden Main's three exit
    // regions and calls DoExitTransition when a MINISH-sized player stands
    // in one - and the two are byte-for-byte symmetric in the room data.
    // What differed was us: containment consults this table
    // (QuickStartIsPocketInteriorRoom), so East was blessed and West was
    // cancelled the frame its transition fired. Wiring content and opening
    // the door are the same act here.
    { AREA_CASTLE_GARDEN_MINISH_HOLES, ROOM_CASTLE_GARDEN_MINISH_HOLES_1, QUICKSTART_KINDS_ANY, 136, 104 },
    // The third of Castle Garden's Minish-only rooms: the crack behind the
    // shrubs at (936,72), the garden's own exit region index 9 (the holes
    // are 0xa and 0xb). Same containment story as the West hole above - the
    // warp fired and was cancelled - so this row both opens it and fills it.
    //
    // Much smaller and more broken up than the holes: 240x160, and only 31
    // tiles are reachable from the (152,48) arrival, in a Y of three narrow
    // passages. SMALL accordingly - the pot lottery already scales its fill
    // to QuickStartCountOpenTiles and drops to a plus-shaped apron under 24
    // tiles, so it degrades rather than failing here.
    //
    // Content at (152,104), tile (9,6): reachable, all four neighbours
    // open, 56px south of the arrival spot so it is visible on entry
    // without standing on the player, and clear of the four FURNITURE props
    // the room keeps (tiles (9,2), (7,2), (2,5), (12,3) - scenery, not
    // swept). The vanilla Minish NPC at (168,88) IS swept, like every other
    // site room's vanilla occupants.
    { AREA_MINISH_CRACKS, ROOM_MINISH_CRACKS_HYRULE_CASTLE_GARDEN, QUICKSTART_KINDS_SMALL, 152, 104 },
    // Castle Garden's two fountain chambers, behind the north-end
    // staircases. These are the rooms the KINSTONE_18 / KINSTONE_35 fusions
    // open - the staircases read as water until fused - and they are what
    // makes those two fusers worth walking to. Being content sites also
    // blesses them past containment automatically
    // (QuickStartIsPocketInteriorRoom scans this table), which is what the
    // "still blocked by containment" note on their doors in transitions.c
    // used to describe.
    //
    // Measured: both are a single 240x160 screen whose entire floor is one
    // 11x6-tile open rectangle, local (32,32)-(207,127), with the player
    // arriving at (120,120). 66 clear tiles is small-pool territory - room
    // for a puzzle or a conversation, not for a wave.
    { AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_EAST, QUICKSTART_KINDS_SMALL, 120, 80 },
    { AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_WEST, QUICKSTART_KINDS_SMALL, 120, 80 },
    // --- The overworld expansion's six new door interiors -----------------
    // One per real door in Eastern Hills and Western Wood, surveyed the
    // same way as everything above (collision grid read live in the
    // emulator; content spot is the open-3x3 tile nearest each room's
    // centre). Being rows here is also what OPENS the doors:
    // QuickStartIsPocketInteriorRoom scans this table, so the containment
    // that walls untracked interiors admits these the moment they land.
    //
    // Eastern Hills South's Minish house (Hyrule Field Exit) and Western
    // Wood South's Minish house came OUT of the drawn small-room pool for
    // this - a room reachable through its own real door must not also be a
    // pool draw's teleport target, or its retargeted exit strands whoever
    // walked in (the Boomerang-cave lesson).
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_EXIT, QUICKSTART_KINDS_SMALL, 120, 88 },
    { AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_SOUTHWEST, QUICKSTART_KINDS_SMALL, 120, 88 },
    // Eastern Hills Center's cave. 23 open-3x3 tiles, and vanilla's own
    // Keese ambush + chest are swept like every other site's occupants.
    { AREA_CAVES, ROOM_CAVES_HILLS_KEESE_CHEST, QUICKSTART_KINDS_SMALL, 120, 72 },
    // The Eastern Hills farm house. Furniture-heavy (4 open-3x3 tiles), so
    // the spot sits west of centre where the floor is actually clear.
    { AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_FARM_HOUSE, QUICKSTART_KINDS_SMALL, 88, 72 },
    // Western Wood North's heart-piece tree.
    { AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WESTERN_WOODS_HEART_PIECE, QUICKSTART_KINDS_SMALL, 120, 72 },
    // Percy's house in Western Wood Center.
    { AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_PERCY, QUICKSTART_KINDS_SMALL, 120, 104 },
    // --- The Mole Mitts dig caves ----------------------------------------
    //
    // The first of them, and the pattern for the rest (the user, Aug 2026:
    // "we need to convert this mole mitts cave to a ? event... a general
    // way of implementing ? events in mole mitt caves as we add more
    // overworld regions"). A dig cave is an ORDINARY content site - one
    // table row, nothing new - once two things are known about it, and both
    // have to be measured rather than read off the map data:
    //
    //  1. Its REACHABLE interior. AREA_DIG_CAVES is one 480x960 map shared
    //     by four rooms, so a raw collision dump spans rooms the player
    //     cannot walk to. Flood from the arrival tile instead: this one
    //     came back 27 tiles, tx 7-18 by ty 3-8 against a room origin of
    //     (0,640), a winding corridor with ZERO tiles of full 3x3 elbow
    //     room. That is why it is KINDS_SMALL - a 3x3 pot cage or a wave
    //     has nowhere to stand in here.
    //  2. Whether its overworld mouth sits in a one-way pocket. Trilby's
    //     does, which is what made the ladder a trap; the cave's exit is
    //     now the way back down (see gExitList_DigCaves1_TrilbyHighlands).
    //
    // Spot (184,104) is tile (11,6), three tiles along the corridor the
    // (0x88,0x68) arrival opens into. The far end of the cave - tile
    // (17,6), which is where a "put it as deep as possible" rule lands -
    // is on the OTHER side of a wall segment at tx 13-15 and only joins up
    // via the ty=5 passage; the invariant checker's entrance flood does
    // not cross it, and it was right to reject the spot. In a 27-tile
    // corridor "deep" is three tiles, and the entrance's own run is the
    // only segment guaranteed reachable the moment the player walks in.
    { AREA_DIG_CAVES, ROOM_DIG_CAVES_TRILBY_HIGHLANDS, QUICKSTART_KINDS_SMALL, 184, 104 },
};
// What this site's kill pays, if its row overrides the default. Same
// wrapping reason as QuickStartSiteContentSpot below: the miniboss reward
// drop is compiled above the table.
static u8 QuickStartSiteRewardTier(s32 site) {
    return sQuickStartRoomContentSites[site].rewardTier;
}

// Where a content site wants its event. Wrapped so the pot room, which is
// compiled above the table, can ask without reaching into it directly.
static void QuickStartSiteContentSpot(s32 site, s16* x, s16* y) {
    *x = sQuickStartRoomContentSites[site].contentX;
    *y = sQuickStartRoomContentSites[site].contentY;
}

// Which content site this contentX/contentY belongs to, or -1 if the caller
// is not a content site at all (the 2-door pools pass their own coordinates
// and want no restriction).
static s32 QuickStartFindSiteAt(s32 contentX, s32 contentY) {
    s32 i;
    for (i = 0; i < QUICKSTART_CONTENT_SITE_COUNT; i++) {
        if (sQuickStartRoomContentSites[i].area == gRoomControls.area &&
            sQuickStartRoomContentSites[i].room == gRoomControls.room &&
            sQuickStartRoomContentSites[i].contentX == contentX && sQuickStartRoomContentSites[i].contentY == contentY) {
            return i;
        }
    }
    return -1;
}

static bool32 QuickStartTileBelongsToSite(s32 tx, s32 ty, s32 ownerSite) {
    s32 i, ownerDist, px, py;
    if (ownerSite < 0) {
        return TRUE;
    }
    px = tx * 16 + 8 - sQuickStartRoomContentSites[ownerSite].contentX;
    py = ty * 16 + 8 - sQuickStartRoomContentSites[ownerSite].contentY;
    ownerDist = px * px + py * py;
    for (i = 0; i < QUICKSTART_CONTENT_SITE_COUNT; i++) {
        s32 dist;
        if (i == ownerSite || sQuickStartRoomContentSites[i].area != gRoomControls.area ||
            sQuickStartRoomContentSites[i].room != gRoomControls.room) {
            continue;
        }
        px = tx * 16 + 8 - sQuickStartRoomContentSites[i].contentX;
        py = ty * 16 + 8 - sQuickStartRoomContentSites[i].contentY;
        dist = px * px + py * py;
        if (dist < ownerDist) {
            return FALSE;
        }
    }
    return TRUE;
}



// Whether a content site wants its FURNITURE gone as well as its payouts -
// i.e. every OBJECT in the room, not just the reward-shaped ones
// QuickStartClearVanillaRoomContent takes out of all of them. Only rooms
// whose props actually get in the way of the event: the dojo ships with a
// dojo-master NPC and six pillars filling the arena a miniboss needs, and
// the ranch house rooms are packed tightly enough that a 9-pot lottery
// loses pots to the furniture.
static bool32 QuickStartContentSiteWantsClear(u8 area, u8 room) {
    if (area == AREA_DOJOS && room == ROOM_DOJOS_GRIMBLADE) {
        return TRUE;
    }
    // The smithy ships with a workbench row, an anvil, pots and a chest
    // filling most of its floor, and it is an ANY-kind site now, so it has
    // to be able to host a miniboss or a 3-wave gauntlet.
    if (area == AREA_HOUSE_INTERIORS_2 && room == ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH) {
        return TRUE;
    }
    return area == AREA_HOUSE_INTERIORS_4 &&
           (room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST || room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST);
}

// Deletes a room's own vanilla payout - the reward it shipped with, before
// it was repurposed as a "? room".
//
// Converting these rooms back onto their real vanilla doors brought their
// real vanilla contents back with them, and nothing was taking those away:
// the user reported tree interiors handing out a heart piece AND a random
// event, fairy fountains with both their fairies and an event, and so on.
// The event is meant to BE the room's reward, not a bonus on top of one.
//
// Deliberately narrower than "delete every OBJECT" (which is what
// QuickStartContentSiteWantsClear asks for, and which is fine in the three
// rooms that ask for it): most of these rooms keep their exit as a real
// object - a LADDER_UP, a HOUSE_DOOR_INT, an ARCHWAY - and a blanket sweep
// would take those with it. This list is the payout-shaped ids only, so a
// room can lose its chest without losing its way out.
//
// Vanilla ENEMY and NPC entities go too: an NPC in one of these rooms is
// vanilla's own reward-giver for it (Percy in his treehouse, say), which is
// the same duplication as a leftover chest, and a vanilla enemy in a room
// that is about to roll a miniboss just muddies the encounter.
// Room flag 63 rather than one of the low ones: 0-6 are already spoken for
// by the event content itself and by QuickStart2DoorClearRoomObstacles, and
// 64 upward is where the per-site event flag windows start.
#define QUICKSTART_VANILLA_CONTENT_CLEARED_FLAG 63

static void QuickStartClearVanillaRoomContent(void) {
    s32 i;
    if (QsCheckRoomFlag(QUICKSTART_VANILLA_CONTENT_CLEARED_FLAG)) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (!QuickStartEntityInCurrentRoom(ent) || ent == gRoomControls.camera_target) {
            continue;
        }
        if (ent->kind == ENEMY || ent->kind == NPC) {
            DeleteEntity(ent);
            continue;
        }
        if (ent->kind != OBJECT) {
            continue;
        }
        switch (ent->id) {
            case GROUND_ITEM:
            case CHEST_SPAWNER:
            case SPECIAL_CHEST:
            case HEART_CONTAINER:
            case FAIRY:
            case GREAT_FAIRY:
                DeleteEntity(ent);
                break;
        }
    }
    QsSetRoomFlag(QUICKSTART_VANILLA_CONTENT_CLEARED_FLAG);
}

// -1 if the current room isn't a content site.
static s32 QuickStartFindContentSiteForCurrentRoom(void) {
    s32 i;
    for (i = 0; i < QUICKSTART_CONTENT_SITE_COUNT; i++) {
        if (gRoomControls.area == sQuickStartRoomContentSites[i].area &&
            gRoomControls.room == sQuickStartRoomContentSites[i].room) {
            return i;
        }
    }
    return -1;
}

// The two halves of the "? room pocket": the interiors that hold randomized
// events, and the overworld rooms whose real vanilla doors lead into them.
// Containment consults these to allow real vanilla travel WITHIN the pocket
// while still cancelling anything leading out of the run.
//
// This is the part of the model that genuinely differs from the old one.
// The synthetic-teleport system only ever had to bless one destination per
// entrance, because it controlled both ends of every jump. Restoring real
// doors means blessing a small connected graph instead - every room the
// vanilla data can reach from here, or the first real door the player opens
// gets cancelled out from under them (which, per the transitions.c comment,
// is very likely what made real doors look like they "never fire" when this
// was first attempted).
//
// Kept as two separate sets rather than one flat "is this a pocket room"
// test, which is what this started as. A flat set would have had to include
// Castle Garden Main and Lon Lon Ranch once their own ladders were
// converted - and then "both ends are pocket rooms, allow it" would also
// have blessed North Hyrule Field -> Castle Garden Main, a real vanilla
// border between two region rooms, letting the player walk straight past
// the region chain's own gating.
static bool32 QuickStartIsPocketInteriorRoom(u8 area, u8 room) {
    s32 i;
    // The four Boomerang tree hollows. No longer content sites (their
    // events moved down into the chamber), but still the rooms the player
    // walks into from the field, so they need blessing here or the doors
    // into them get cancelled.
    if (QuickStartIsBoomerangTree(area, room)) {
        return TRUE;
    }
    // The dojo ante room and the dojo proper. Only the dojo is a content
    // site, but the ante room is the room the ladder actually lands in and
    // the two are joined by a scroll seam, so both have to be blessed or
    // the ladder itself gets cancelled.
    if (area == AREA_DOJOS && (room == ROOM_DOJOS_TO_GRIMBLADE || room == ROOM_DOJOS_GRIMBLADE)) {
        return TRUE;
    }
    // The shop. Reached by redirecting one real overworld door per run
    // (QuickStartProcessDoorRedirects), so containment has to let it
    // through from whichever region that door lives in.
    if (area == QUICKSTART_SHOP_AREA && room == QUICKSTART_SHOP_ROOM) {
        return TRUE;
    }
    // North Hyrule Field's through-cave and the Heart Piece Hallway it opens
    // into. The cave is not a content site (its event comes from the cave
    // connector's own kind/extra roll, see QuickStartSetupCaveRoomContent),
    // so unlike the hallway it does not get blessed by the table scan below
    // and needs naming here - otherwise its three field mouths and the door
    // between the two caves all get cancelled the frame they fire.
    if (area == QUICKSTART_CAVE_AREA && room == QUICKSTART_CAVE_ROOM) {
        return TRUE;
    }
    // The North Hyrule Field fairy fountain tree. It is no longer a content
    // site itself - its event moved down the staircase into the cave, which
    // IS a site and so gets blessed by the table scan below - but the tree
    // is still the room the player walks into from the field, so it has to
    // be blessed here or the door into it gets cancelled.
    if (area == AREA_TREE_INTERIORS && room == ROOM_TREE_INTERIORS_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN) {
        return TRUE;
    }
    for (i = 0; i < QUICKSTART_CONTENT_SITE_COUNT; i++) {
        if (area == sQuickStartRoomContentSites[i].area && room == sQuickStartRoomContentSites[i].room) {
            return TRUE;
        }
    }
    return FALSE;
}

// The overworld rooms that own those interiors - i.e. every room a pocket
// interior's own real exit can legitimately put the player back in.
static bool32 QuickStartIsRingRegionRoom(u8 area, u8 room);

static bool32 QuickStartIsPocketOverworldRoom(u8 area, u8 room) {
    // Every ring room owns pocket doors now - the overworld expansion put
    // content sites in all seven named regions - so the owning-overworld
    // set IS the ring. This was a hardcoded five-room list from before the
    // expansion, which silently cancelled walking OUT of any site whose
    // door lives in Eastern Hills or Western Wood; the failure stayed
    // invisible as long as those sites' exits were still mis-retargeted at
    // Castle Garden (a destination the old list allowed), and surfaced the
    // moment the retargets were fixed back to their vanilla fields.
    return QuickStartIsRingRegionRoom(area, room);
}

// Is this transition a legitimate move inside the pocket? Two shapes are
// allowed and nothing else: walking INTO an interior (from anywhere - every
// real door into one of these rooms comes from its own owning overworld
// room, so there's no third party to guard against), and walking back OUT
// of one into an owning overworld room. Interior-to-interior is covered by
// the first case, which is what lets Goron Cave's two rooms and Link's
// House's two rooms be explored normally.
static bool32 QuickStartIsPocketTransition(u8 fromArea, u8 fromRoom, u8 toArea, u8 toRoom) {
    if (QuickStartIsPocketInteriorRoom(toArea, toRoom)) {
        return TRUE;
    }
    return QuickStartIsPocketInteriorRoom(fromArea, fromRoom) && QuickStartIsPocketOverworldRoom(toArea, toRoom);
}

// Rolled lazily on first entry to the site itself rather than up front at
// the hub - unlike the old pool draws, nothing about a site's content
// depends on what any other site drew (there's no shared room pool left to
// deconflict), so there's no reason to force it earlier.
//
// Rolls the full 7-kind vocabulary now, split by the site's own `large`
// flag exactly the way the retired ladder/door slots split by which room
// pool they had drawn from. Before the last entrances were converted, a
// site only ever rolled chest-or-NPC and the richer kinds reached the
// player through the synthetic pool instead; with that pool gone, rolling
// narrowly here would have quietly removed the pot lottery, chest lottery,
// fairy rooms, minibosses and wave gauntlets from the game.
static void QuickStartRandomizeContentSiteOnce(s32 site) {
    u8 kind, extra;
    s32 b;
    if (QsCheckSiteFlag(GF_CONTENT_SITE_RANDOMIZED(site))) {
        return;
    }
    switch (sQuickStartRoomContentSites[site].kinds) {
        case QUICKSTART_KINDS_ANY:
            kind = QuickStartPickAnyKind();
            break;
        case QUICKSTART_KINDS_LARGE:
            kind = QuickStartPickLargeKind();
            break;
        case QUICKSTART_KINDS_ELITE:
            // No roll and no unlock fallback: an elite site is always a
            // miniboss fight, and its (item-gated) door is the gate.
            kind = QS_EVENT_MINIBOSS;
            break;
        case QUICKSTART_KINDS_RARE:
            // Always the plain item drop; the rare pool is selected below
            // by forcing extra bit 7.
            kind = QS_EVENT_ITEM_DROP;
            break;
        case QUICKSTART_KINDS_MINIBOSS:
            // Always a fight, but an ordinary one - no elite bit. What the
            // kill pays comes from the row's rewardTier instead.
            kind = QS_EVENT_MINIBOSS;
            break;
        default:
            kind = QuickStartPickSmallKind();
            break;
    }
    if (kind == QS_EVENT_ITEM_DROP || kind == QS_EVENT_WAVES) {
        // A draw seed, not an index: QuickStartDrawItem derives both the tier
        // and the pick from it, and storing it (rather than calling Random()
        // at drop time) is what keeps a prize the same after leaving the room
        // and coming back.
        extra = (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE);
        // Bit 6 on a WAVES site: the stripped-kit variant (see
        // QuickStartHandicapApply). One gauntlet in four, which lands it
        // between "uncommon" and "rare" once you account for WAVES itself
        // being one roll among several - the user asked for that band.
        // Chest sites never read bit 6, so sharing the field is free.
        if (kind == QS_EVENT_WAVES && (s32)Random() % 4 == 0) {
            extra |= 0x40;
        }
        if (sQuickStartRoomContentSites[site].kinds == QUICKSTART_KINDS_RARE) {
            // Bit 7 = force the drop to the RARE tier.
            // Rolled into the stored extra rather than checked at drop time
            // so the whole treatment survives leaving and re-entering the
            // room, exactly like the miniboss kind's elite bit.
            extra = (u8)(((s32)Random() % QUICKSTART_DRAW_SEED_RANGE) | 0x80);
        }
    } else if (kind == QS_EVENT_NPC) {
        extra = (u8)((s32)Random() % 2); // bit 0: 1 = evil, 0 = friendly
    } else if (kind == QS_EVENT_MINIBOSS) {
        extra = (u8)((s32)Random() % QUICKSTART_MINIBOSS_POOL_SIZE);
        // The elite bit rides in the extra byte's top bit, well clear of
        // the 0-4 roster index: the spawn reads the index with & 0x7f, and
        // the reward drop upgrades on & 0x80. Packing it here means the
        // whole elite treatment survives leaving and re-entering the room
        // for free, exactly like every other kind parameter.
        if (sQuickStartRoomContentSites[site].kinds == QUICKSTART_KINDS_ELITE) {
            extra |= 0x80;
        } else if (sQuickStartRoomContentSites[site].rewardTier != QS_SITE_REWARD_DEFAULT) {
            // A site that promises a tier must actually pay it. The Red
            // Sword branch of the reward drop returns before the item drop
            // ever happens, so letting bit 6 roll here would silently swap
            // the promised reward for a sword the player may already own.
        } else if ((s32)Random() % 4 == 0) {
            // Bit 6: this (non-elite) miniboss carries the Red Sword - the
            // blade player.c's SurfaceAction_CloneTile hands one clone out
            // for, i.e. the user's "level two sword", rare on purpose:
            // roughly 1 in 4 miniboss sites, and miniboss is itself one
            // roll among several. The drop only materializes if the sword
            // isn't owned yet (see the reward drop), so it can't pile up.
            extra |= 0x40;
        }
    } else if (kind == QS_EVENT_POT_LOTTERY) {
        extra = QuickStartPickPotRoomExtra();
    } else if (kind == QS_EVENT_CHEST_LOTTERY) {
        extra = QuickStartPickLotteryExtra();
    } else {
        extra = 0; // QS_EVENT_FAIRY takes no parameter.
    }
    for (b = 0; b < 3; b++) {
        if (kind & (1 << b)) {
            QsSetSiteFlag(GF_CONTENT_SITE_KIND_BIT(site, b));
        }
    }
    for (b = 0; b < 8; b++) {
        if (extra & (1 << b)) {
            QsSetSiteFlag(GF_CONTENT_SITE_EXTRA_BIT(site, b));
        }
    }
    QsSetSiteFlag(GF_CONTENT_SITE_RANDOMIZED(site));
}

// How many other sites share this site's room and come before it - i.e.
// which event this is within the room, 0 for the only one.
static s32 QuickStartContentSiteSlotInRoom(s32 site) {
    s32 i, slot = 0;
    for (i = 0; i < site; i++) {
        if (sQuickStartRoomContentSites[i].area == sQuickStartRoomContentSites[site].area &&
            sQuickStartRoomContentSites[i].room == sQuickStartRoomContentSites[site].room) {
            slot++;
        }
    }
    return slot;
}

static void QuickStartSetupContentSite(s32 site) {
    const QuickStartContentSite* entry = &sQuickStartRoomContentSites[site];
    u8 kind;
    s32 extra, b;
    // Never during a room scroll or reload. The Grimblade dojo joins its
    // ante room by a scroll seam, and mid-scroll there are frames where
    // gRoomControls.room already names the dojo while origin still points
    // at the ante screen (the flip happens mid-frame; per-frame sampling
    // shows them changing "together", but this dispatcher runs between
    // the two writes). Every room-local coordinate this function touches
    // is wrong in that window - measured: the gate's prize re-dropped
    // INTO THE ANTE ROOM (with a partial pot cage around it), free to
    // take without ever striking the lever - the user's phantom-prize
    // report. QuickStartRoomSettled folds that measured condition together
    // with the border-walk window the region reward bug later exposed (the
    // room-tracker pointer check), so every dispatcher shares one settled
    // test.
    if (!QuickStartRoomSettled()) {
        return;
    }
    QuickStartRandomizeContentSiteOnce(site);
    // Above the "already collected" check on purpose. The vanilla payout has
    // to go every time the room loads, not only on the visit that spawns the
    // event - otherwise a room whose event is long since collected quietly
    // goes back to handing out its original chest or heart piece.
    QuickStartClearVanillaRoomContent();
    if (QuickStartContentSiteWantsClear(entry->area, entry->room)) {
        QuickStart2DoorClearRoomObstacles(entry->area, entry->room);
    }
    // A gated site does not exist until its fusion is done. This is what
    // keeps the Goron cave's four stages one-per-chamber: each stage's
    // event is behind the wall its own fusion punches open, so the player
    // cannot see or reach the next one early. Checked here rather than in
    // the randomizer above on purpose - the roll is latched once per run
    // either way, and doing it here means a chamber that opens mid-run
    // spawns on the next room load with the roll it always had.
    if (entry->gateKinstone != 0 && !CheckKinstoneFused(entry->gateKinstone)) {
        return;
    }
    if (QsCheckSiteFlag(GF_CONTENT_SITE_DONE(site))) {
        return;
    }
    kind = 0;
    for (b = 0; b < 3; b++) {
        if (QsCheckSiteFlag(GF_CONTENT_SITE_KIND_BIT(site, b))) {
            kind |= (1 << b);
        }
    }
    extra = 0;
    for (b = 0; b < 8; b++) {
        if (QsCheckSiteFlag(GF_CONTENT_SITE_EXTRA_BIT(site, b))) {
            extra |= (1 << b);
        }
    }
    // Room flags are per ROOM, but the Boomerang chamber holds five events
    // at once, so they cannot all use flags 0-5 the way a lone event does -
    // the first one to set "already spawned" would silence the other four
    // (seen in the emulator: one event appeared out of five). Each site
    // gets its own 8-flag window instead, based on its position among the
    // sites sharing its room, starting well clear of the low flags the rest
    // of this file uses. gRoomVars.flags is 52 bytes, so there is room for
    // far more of these than any room will ever hold.
    if (QuickStartSetupEventContent(kind, extra, entry->contentX, entry->contentY,
                                    64 + QuickStartContentSiteSlotInRoom(site) * 8)) {
        QsSetSiteFlag(GF_CONTENT_SITE_DONE(site));
    }
}

// One draw per save, same shape as QuickStartRandomizeSlotsOnce but for
// a single slot - no cross-slot dedup needed, there's only one connector.
// Placed here rather than alongside QuickStart2DoorGetTarget/GetSpawnInfo
// above (which don't need it) because it reads QUICKSTART_LADDER_REWARD_POOL_SIZE,
// not defined until sQuickStartLadderRewardPool further up this same
// function group.
static void QuickStart2DoorRandomizeOnce(void) {
    u8 pool, kind, roomIdx, poolSize;
    if (QsCheckFlag(GF_2DOOR_RANDOMIZED)) {
        return;
    }
    pool = (u8)((s32)Random() % 2);
    QuickStart2DoorSetPool(pool);
    if (pool == 0) {
        kind = QuickStartPickSmallKind();
    } else {
        kind = QuickStartPickLargeKind();
    }
    QuickStart2DoorSetKind(kind);
    if (kind == QS_EVENT_ITEM_DROP || kind == QS_EVENT_WAVES) {
        QuickStart2DoorSetExtra((u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE));
    } else if (kind == QS_EVENT_NPC) {
        QuickStart2DoorSetExtra((u8)((s32)Random() % 2));
    } else if (kind == QS_EVENT_MINIBOSS) {
        QuickStart2DoorSetExtra((u8)((s32)Random() % QUICKSTART_MINIBOSS_POOL_SIZE));
    } else if (kind == QS_EVENT_POT_LOTTERY) {
        QuickStart2DoorSetExtra(QuickStartPickPotRoomExtra());
    } else if (kind == QS_EVENT_CHEST_LOTTERY) {
        QuickStart2DoorSetExtra(QuickStartPickLotteryExtra());
    }
    poolSize = (pool == 0) ? QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE : QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
    roomIdx = (u8)((s32)Random() % poolSize);
    QuickStart2DoorSetRoomIndex(roomIdx);
    QsSetFlag(GF_2DOOR_RANDOMIZED);
}

// Absolute room-local spawn points for the 3 "overworld density" rooms -
// built from the same generic 3x3-plus-arms grid
// sQuickStartWaveRoomOffsets already uses elsewhere in this file (not an
// individually hand-walked survey like Castle Garden/Melari's
// Mine/Lon Lon Ranch's own offsets - those are still pending real
// playtesting), centered on each room's own entrance spot above.
static const s16 sQuickStart2DoorMelariEnemyOffsets[12][2] = {
    { 100, 100 }, { 76, 100 }, { 124, 100 }, { 100, 76 },  { 100, 124 }, { 76, 76 },
    { 124, 76 },  { 76, 124 }, { 124, 124 }, { 52, 100 },  { 148, 100 }, { 100, 52 },
};
static const s16 sQuickStart2DoorRainEnemyOffsets[12][2] = {
    { 100, 100 }, { 76, 100 }, { 124, 100 }, { 100, 76 },  { 100, 124 }, { 76, 76 },
    { 124, 76 },  { 76, 124 }, { 124, 124 }, { 52, 100 },  { 148, 100 }, { 100, 52 },
};
static const s16 sQuickStart2DoorMinishVillageEnemyOffsets[12][2] = {
    { 80, 110 }, { 56, 110 }, { 104, 110 }, { 80, 86 },  { 80, 134 }, { 56, 86 },
    { 104, 86 }, { 56, 134 }, { 104, 134 }, { 32, 110 }, { 128, 110 }, { 80, 62 },
};
#define QUICKSTART_2DOOR_OVERWORLD_ROOM_SQUARES 80
#define QUICKSTART_2DOOR_OVERWORLD_MAX_ENEMIES 6

static void QuickStart2DoorSpawnOverworldEnemiesOnce(u8 area, u8 room) {
    if (QsCheckRoomFlag(0)) {
        return;
    }
    if (area == AREA_CRENEL_MINISH_PATHS && room == ROOM_CRENEL_MINISH_PATHS_MELARI) {
        QuickStartSpawnEnemyGroup(sQuickStart2DoorMelariEnemyOffsets, ARRAY_COUNT(sQuickStart2DoorMelariEnemyOffsets),
                                   QUICKSTART_2DOOR_OVERWORLD_ROOM_SQUARES, QUICKSTART_2DOOR_OVERWORLD_MAX_ENEMIES);
    } else if (area == AREA_CRENEL_MINISH_PATHS && room == ROOM_CRENEL_MINISH_PATHS_RAIN) {
        QuickStartSpawnEnemyGroup(sQuickStart2DoorRainEnemyOffsets, ARRAY_COUNT(sQuickStart2DoorRainEnemyOffsets),
                                   QUICKSTART_2DOOR_OVERWORLD_ROOM_SQUARES, QUICKSTART_2DOOR_OVERWORLD_MAX_ENEMIES);
    } else {
        QuickStartSpawnEnemyGroup(sQuickStart2DoorMinishVillageEnemyOffsets,
                                   ARRAY_COUNT(sQuickStart2DoorMinishVillageEnemyOffsets),
                                   QUICKSTART_2DOOR_OVERWORLD_ROOM_SQUARES, QUICKSTART_2DOOR_OVERWORLD_MAX_ENEMIES);
    }
    QsSetRoomFlag(0);
}

// Same shape as QuickStartSetupWaveRoomContent, but keyed off the 2-door
// connector's own GF_2DOOR_* flags instead of a slotIndex - this file's
// established idiom (duplicate small per-context functions rather than
// thread an extra parameter through a shared one) rather than refactor the
// already-shipped ladder system.
static void QuickStart2DoorSetupWaveRoomContent(s32 contentX, s32 contentY) {
    u8 wave, difficulty;
    if (QsCheckRoomFlag(2)) {
        if (!QuickStartGroundItemAt(contentX, contentY)) {
            QsSetFlag(GF_2DOOR_DONE);
        }
        return;
    }
    if (!QsCheckRoomFlag(QUICKSTART_WAVE_ROOM_HINT_SHOWN_FLAG)) {
        QsSetRoomFlag(QUICKSTART_WAVE_ROOM_HINT_SHOWN_FLAG);
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 9), 0);
    }
    difficulty = QuickStartGetDifficulty();
    wave = QuickStartWaveRoomGetWave(0);
    if (QsCheckRoomFlag(0)) {
        if (QuickStartCountRoomEnemies() > 0) {
            return;
        }
        if (wave >= 2) {
            s32 extra = QuickStart2DoorGetExtra();
            u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) never become a floor
            // entity, so the test is "was it delivered", not "does an
            // entity exist" - see QuickStartSpawnRewardEntity.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(2);
            }
            return;
        }
        QuickStartWaveRoomSetWave(0, wave + 1);
        QsClearRoomFlag(0);
        return;
    }
    QuickStartSpawnWave(contentX, contentY, wave, difficulty);
    QsSetRoomFlag(0);
}

// 2-door pool counterparts of QuickStartSetupPotRoomContent/
// QuickStartSetupChestLotteryContent/QuickStartSetupFairyRoomContent above -
// same logic, GF_2DOOR_DONE/QuickStart2DoorGetExtra in place of the
// ladder-indexed flags, duplicated rather than shared for the same reason
// QuickStart2DoorSetupWaveRoomContent above is its own separate copy
// instead of taking a slotIndex.
// contentX/contentY are accepted and ignored, same as the content-site
// version: the generator anchors on the player's own arrival spot instead.
static void QuickStart2DoorSetupPotRoomContent(s32 contentX, s32 contentY) {
    s32 extra, anchorTX, anchorTY;
    if (QsCheckFlag(GF_2DOOR_DONE)) {
        return;
    }
    extra = QuickStart2DoorGetExtra();
    if (QsCheckRoomFlag(0)) {
        if (QuickStartGroundItemOfForm(sQuickStartLotteryPrizes[QuickStartLotteryPrizeIndex(extra)])) {
            QsSetRoomFlag(3);
            return;
        }
        if (QsCheckRoomFlag(3)) {
            QsSetFlag(GF_2DOOR_DONE);
        }
        return;
    }
    anchorTX = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) >> 4;
    anchorTY = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) >> 4;
    QuickStartPotRoomGenerate(extra, anchorTX, anchorTY, -1);
    QsSetRoomFlag(0);
}

static void QuickStart2DoorSetupChestLotteryContent(s32 contentX, s32 contentY) {
    static const s16 offsets[3] = { -16, 0, 16 };
    s32 extra, winnerSlot, prizeIndex;
    if (QsCheckFlag(GF_2DOOR_DONE)) {
        return;
    }
    extra = QuickStart2DoorGetExtra();
    winnerSlot = extra & 3;
    prizeIndex = QuickStartLotteryPrizeIndex(extra);
    if (QsCheckRoomFlag(0)) {
        if (CheckLocalFlag(QUICKSTART_CHEST_LOTTERY_FLAG(winnerSlot))) {
            QsSetFlag(GF_2DOOR_DONE);
        }
        return;
    }
    {
        s32 i;
        for (i = 0; i < 3; i++) {
            ClearLocalFlag(QUICKSTART_CHEST_LOTTERY_FLAG(i));
        }
        for (i = 0; i < 3; i++) {
            s32 localX = contentX + offsets[i];
            Entity* chest = CreateObject(SPECIAL_CHEST, QUICKSTART_CHEST_LOTTERY_FLAG(i), 0);
            if (chest != NULL) {
                chest->x.HALF.HI = gRoomControls.origin_x + localX;
                chest->y.HALF.HI = gRoomControls.origin_y + contentY;
                chest->collisionLayer = 1;
                chest->flags |= ENT_PERSIST;
                UpdateSpriteForCollisionLayer(chest);
            }
            if (i == winnerSlot) {
                s32 j;
                TileEntity* slot = NULL;
                for (j = 0; j < 8; j++) {
                    if (gSmallChests[j].tilePos == 0) {
                        slot = &gSmallChests[j];
                        break;
                    }
                }
                if (slot != NULL) {
                    slot->type = SMALL_CHEST;
                    slot->localFlag = (u8)QUICKSTART_CHEST_LOTTERY_FLAG(i);
                    slot->_2 = (u8)sQuickStartLotteryPrizes[prizeIndex];
                    slot->_3 = 0;
                    slot->tilePos = (u16)(((localX >> 4) & 0x3F) | (((contentY >> 4) & 0x3F) << 6));
                    slot->_6 = 1;
                    slot->_7 = 0;
                }
            }
        }
        QsSetRoomFlag(0);
    }
}

static void QuickStart2DoorSetupFairyRoomContent(s32 contentX, s32 contentY) {
    static const s16 offsets[2] = { -16, 16 };
    s32 i;
    if (QsCheckRoomFlag(0)) {
        return;
    }
    for (i = 0; i < 2; i++) {
        Entity* fairy = CreateObject(FAIRY, 0x60, 0);
        if (fairy != NULL) {
            fairy->x.HALF.HI = gRoomControls.origin_x + contentX + offsets[i];
            fairy->y.HALF.HI = gRoomControls.origin_y + contentY;
            fairy->collisionLayer = 1;
            UpdateSpriteForCollisionLayer(fairy);
        }
    }
    QsSetRoomFlag(0);
}

// Unlike QuickStartClearLadderRoomObstacles (which sweeps every pre-existing
// OBJECT/ENEMY/NPC, on the assumption each 1-door pool room needs a genuine
// blank canvas), the 2-door pool's own rooms were picked specifically for
// already having open floor around their furniture/decoration (bookshelves,
// tables, statues, etc. - all OBJECT-kind, per the user's own example: the
// library rooms' shelves shouldn't have been removed). Only ENEMY/NPC
// ("sprites" - the user's own word, living/character graphics as opposed to
// static decoration) are swept unconditionally here; OBJECT-kind is left
// alone except in ROOM_VEIL_FALLS_CAVES_EXIT, where the vanilla pots
// specifically needed removing per an earlier, separate request (see
// sQuickStart2DoorSmallRoomPool's own comment on that room).
static void QuickStart2DoorClearRoomObstacles(u8 area, u8 room) {
    s32 i;
    // The dojo joins ROOM_VEIL_FALLS_CAVES_EXIT in wanting its OBJECT-kind
    // content gone too, not just the living entities: its six furniture
    // pillars, archway and technique-scroll reward are exactly the "vanilla
    // content" the user asked to have cleared out of it, and they take up
    // most of the arena a miniboss or wave gauntlet needs.
    bool32 clearObjects = (area == AREA_VEIL_FALLS_CAVES && room == ROOM_VEIL_FALLS_CAVES_EXIT) ||
                          (area == AREA_DOJOS && room == ROOM_DOJOS_GRIMBLADE) ||
                          (area == AREA_HOUSE_INTERIORS_2 && room == ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH) ||
                          (area == AREA_HOUSE_INTERIORS_4 &&
                           (room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST ||
                            room == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST));
    // Every room that goes through here is a "? room" of some kind, so its
    // own vanilla payout goes too - same reasoning as the content sites.
    QuickStartClearVanillaRoomContent();
    if (QsCheckRoomFlag(1)) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* entity = &gEntities[i].base;
        if (!QuickStartEntityInCurrentRoom(entity) || entity == gRoomControls.camera_target) {
            continue;
        }
        if (entity->kind == ENEMY || entity->kind == NPC || (clearObjects && entity->kind == OBJECT)) {
            DeleteEntity(entity);
        }
    }
    QsSetRoomFlag(1);
}

// Dispatch for whichever room the save's one 2-door connector draw
// resolved to (see QuickStart2DoorRandomizeOnce/GetTarget above) - called
// every frame the player is standing in it (QuickStartRoomMonitor below).
// Same CHEST/MINIBOSS/NPC/WAVES shape as QuickStartSetupSlotRoomContent,
// duplicated with GF_2DOOR_*/QuickStart2DoorGetExtra in place of the
// ladder-indexed flags, plus the two size-survey special cases
// (ROOM_CAVES_HEART_PIECE_HALLWAY kept vanilla, the 3 overworld-density
// rooms) that ladder rooms don't need.
// Put the player at the door they actually came in by, rather than at the
// room's one hard-coded arrival spot.
//
// The entry side records which overworld door was used
// (GF_2DOOR_ENTERED_FROM_B); this turns that into a position using the
// room's own exit list, so A leads to A' and B to B'. Once per room entry.
#define QUICKSTART_2DOOR_ARRIVAL_PLACED_FLAG 52
static void QuickStart2DoorPlaceArrivalAtDoor(void) {
    s16 doorX, doorY;
    if (QsCheckRoomFlag(QUICKSTART_2DOOR_ARRIVAL_PLACED_FLAG) || gRoomTransition.transitioningOut) {
        return;
    }
    QsSetRoomFlag(QUICKSTART_2DOOR_ARRIVAL_PLACED_FLAG);
    if (!QuickStart2DoorDoorSpot(QsCheckFlag(GF_RIVER_ENTERED_FROM_B) ? 1 : 0, &doorX, &doorY)) {
        return;
    }
    gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + doorX;
    gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + doorY;
}

static void QuickStart2DoorSetupRoomContent(void) {
    u8 area, room, kind;
    s16 entranceX, entranceY, contentDX, contentDY;
    s32 contentX, contentY;

    QuickStart2DoorGetTarget(&area, &room);
    QuickStart2DoorPlaceArrivalAtDoor();
    // Above the kept-vanilla return too: a room we otherwise leave alone
    // still got its player placed by our own entrance coordinates.
    QuickStartRescuePlayerOntoGround();
    if (QuickStart2DoorIsKeptVanilla(area, room)) {
        return;
    }
    QuickStart2DoorClearRoomObstacles(area, room);
    QuickStart2DoorGetSpawnInfo(&entranceX, &entranceY, &contentDX, &contentDY);
    contentX = entranceX + contentDX;
    contentY = entranceY + contentDY;
    // The content spot is derived from that same unmeasured (100,100), so it
    // lands in the void alongside the player. Snap it to real ground before
    // anything is placed on it.
    {
        s16 groundX, groundY;
        if (!QuickStartTileIsOpen(contentX >> 4, contentY >> 4) &&
            QuickStartFindOpenTileNear(contentX, contentY, 1, &groundX, &groundY)) {
            contentX = groundX;
            contentY = groundY;
        }
    }

    if (QuickStart2DoorWantsOverworldEnemies(area, room)) {
        QuickStart2DoorSpawnOverworldEnemiesOnce(area, room);
        return;
    }
    if (QsCheckFlag(GF_2DOOR_DONE)) {
        return;
    }
    kind = QuickStart2DoorGetKind();
    if (kind == QS_EVENT_ITEM_DROP) {
        if (QsCheckRoomFlag(0)) {
            if (QuickStartGroundItemAt(contentX, contentY)) {
                QsSetRoomFlag(3);
                return;
            }
            if (QsCheckRoomFlag(3)) {
                QsSetFlag(GF_2DOOR_DONE);
                return;
            }
        }
        {
            s32 extra = QuickStart2DoorGetExtra();
            u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) never become a floor
            // entity, so the test is "was it delivered", not "does an
            // entity exist" - see QuickStartSpawnRewardEntity.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(0);
            }
        }
    } else if (kind == QS_EVENT_MINIBOSS) {
        if (QsCheckRoomFlag(2)) {
            if (!QuickStartGroundItemAt(contentX, contentY)) {
                QsSetFlag(GF_2DOOR_DONE);
            }
            return;
        }
        if (QsCheckRoomFlag(0)) {
            s32 i;
            for (i = 0; i < MAX_ENTITIES; i++) {
                Entity* enemy = &gEntities[i].base;
                if (enemy->kind == ENEMY && QuickStartEntityInCurrentRoom(enemy)) {
                    if (!PlayerInRange(enemy, 1, 56)) {
                        enemy->x.HALF.HI = gRoomControls.origin_x + contentX;
                        enemy->y.HALF.HI = gRoomControls.origin_y + contentY;
                    }
                    return;
                }
            }
            {
                Entity* itemEntity = CreateObject(GROUND_ITEM, ITEM_HEART_PIECE, 0);
                if (itemEntity != NULL) {
                    itemEntity->x.HALF.HI = gRoomControls.origin_x + contentX;
                    itemEntity->y.HALF.HI = gRoomControls.origin_y + contentY;
                    itemEntity->collisionLayer = 1;
                    itemEntity->flags |= ENT_PERSIST;
                    UpdateSpriteForCollisionLayer(itemEntity);
                    itemEntity->direction = IdleSouth;
                    QsSetRoomFlag(2);
                    gSave.miniboss_kills++;
                }
            }
            return;
        }
        {
            s32 extra = QuickStart2DoorGetExtra();
            const QuickStartEnemyPick* pick = &sQuickStartElites[(extra & 0x7f) % QUICKSTART_MINIBOSS_POOL_SIZE];
            if (QuickStartSpawnEnemiesOnOpenTiles(pick->id, pick->form, contentX, contentY,
                                                  QuickStartMinibossCount(pick->id), -1) > 0) {
                QsSetRoomFlag(0);
            }
        }
    } else if (kind == QS_EVENT_WAVES) {
        QuickStart2DoorSetupWaveRoomContent(contentX, contentY);
    } else if (kind == QS_EVENT_POT_LOTTERY) {
        QuickStart2DoorSetupPotRoomContent(contentX, contentY);
    } else if (kind == QS_EVENT_CHEST_LOTTERY) {
        QuickStart2DoorSetupChestLotteryContent(contentX, contentY);
    } else if (kind == QS_EVENT_FAIRY) {
        QuickStart2DoorSetupFairyRoomContent(contentX, contentY);
    } else {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
                // Fold the script's own "resolved" write into this room's
                // run latch (see QUICKSTART_NPC_RESOLVED_FLAG's comment).
                if (CheckGlobalFlag(QUICKSTART_NPC_RESOLVED_FLAG)) {
                    QsSetFlag(GF_2DOOR_DONE);
                }
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
                QuickStartLoadNpcScratchFlags((u8)QuickStart2DoorGetExtra());
                QuickStartMakeNpcTalkable(npc, sQuickStartEventNpcScripts[0]);
            }
        }
    }
}


// --- Which of a 2-door pool room's two doors did the player just use? -----
//
// The pool substitutes a random interior for a vanilla one that connects two
// overworld doors, A and B. Walk in at A, cross, come out at B; walk in at B,
// come out at A. For that to work the game has to know WHICH door the player
// left by - and until now it could not, because transitions.c had retargeted
// all 40 doors in the pool (20 rooms, 2 each) to the same destination AND the
// same landing spot. The destination carried no information, so every exit
// returned the player to the same overworld side and B -> A was impossible.
//
// Identifying the door by geometry is the obvious approach and the wrong one.
// Doors come in two shapes: WARP_TYPE_AREA rows carry a real position in
// startX/startY, but WARP_TYPE_BORDER rows leave those at 0 and encode their
// edge in the shape field instead, so no single position test distinguishes
// them - and four pool rooms have BOTH doors as borders.
//
// So the doors are tagged in the data instead, and the ENGINE does the
// matching. Each pool room's first door row carries endX/endY of
// QUICKSTART_2DOOR_TAG_A and its second QUICKSTART_2DOOR_TAG_B. DoExitTransition
// (scroll.c) copies whichever row actually fired into
// player_status.start_pos_x, so by the time this file sees the transition the
// tag is sitting there waiting to be read. Both shapes work identically
// because vanilla's own DoApplicableTransition picked the row, using its own
// predicates, exactly as it does for every other door in the game.
//
// The tags are sentinel landing coordinates: DoExitTransition only copies
// endX through verbatim when it is <= 0x3ff, so these sit just under that
// ceiling where no real landing spot ever lands. They are overwritten with
// the true destination the same frame.
#define QUICKSTART_2DOOR_TAG_A 0x3fe
#define QUICKSTART_2DOOR_TAG_B 0x3fd

// 0 for side A, 1 for side B, -1 if this transition is not one of ours.
static s32 QuickStart2DoorExitSide(void) {
    if (gRoomTransition.player_status.start_pos_x == QUICKSTART_2DOOR_TAG_A) {
        return 0;
    }
    if (gRoomTransition.player_status.start_pos_x == QUICKSTART_2DOOR_TAG_B) {
        return 1;
    }
    return -1;
}

// Where to put the player INSIDE a pool room when they arrive through its
// door `side`. Read off the room's own live exit list rather than a table, so
// this works for any room added to the pool later without new data.
//
// The two shapes need different readings, which is the whole reason this is a
// function and not a lookup:
//   WARP_TYPE_AREA   - startX/startY is the door's own position; land beside it.
//   WARP_TYPE_BORDER - startX/startY are 0 and `shape` names the room edge
//                      (0x03 north, 0x0c east, 0x30 south, 0xc0 west); land
//                      just inside that edge, centred on the room.
// Either way the result is snapped onto real open ground, because a door's
// nominal position is not always standable.
static bool32 QuickStart2DoorDoorSpot(s32 side, s16* outX, s16* outY) {
    const Transition* exits = gArea.pCurrentRoomInfo->exits;
    s32 i = 0;
    s16 x, y;
    if (exits == NULL) {
        return FALSE;
    }
    while (exits->warp_type != WARP_TYPE_END_OF_LIST) {
        if (i == side) {
            break;
        }
        exits++;
        i++;
    }
    if (exits->warp_type == WARP_TYPE_END_OF_LIST) {
        return FALSE;
    }
    if (exits->startX != 0 || exits->startY != 0) {
        x = (s16)exits->startX;
        y = (s16)exits->startY;
    } else {
        s16 w = (s16)gRoomControls.width;
        s16 h = (s16)gRoomControls.height;
        x = w / 2;
        y = h / 2;
        if (exits->shape & 0x03) {
            y = 32; // north edge
        } else if (exits->shape & 0x30) {
            y = h - 32; // south edge
        } else if (exits->shape & 0xc0) {
            x = 32; // west edge
        } else if (exits->shape & 0x0c) {
            x = w - 32; // east edge
        }
    }
    if (!QuickStartFindOpenTileNear(x, y, 1, outX, outY)) {
        *outX = x;
        *outY = y;
    }
    return TRUE;
}

// BUG FIX (user report): every one of this pool's real rooms has both its
// doors retargeted (transitions.c) to the same literal (0xb8,0x138) -
// confirmed in the emulator to be a real, walkable vanilla landing spot,
// but a DEAD END: it's a small wooden platform inside a sheep pen, reached
// only by walking down onto a real SURFACE_AUTO_LADDER tile that dead-ends
// against a fence a few tiles later - no path back to the connector's own
// entrance box (0xe2-0xee,0x1ae-0x1ba). Effectively the same "arrives on
// top of the ledge, can't get back down" bug as the user's own diagnosis,
// just discovered independently via direct emulator movement/collision
// tracing rather than assumed. Since transitions.c bakes that literal
// destination into every pool room's own door data at compile time (~40
// entries across the file), overriding it there per-room isn't practical;
// instead this reuses the exact same "let the real static transition fire,
// then correct start_pos_x/y before it completes" technique
// QuickStartFixupQuestionRoomReturn already established for the ladder
// pool. (232,476) is a plain, walkable patch of ground the emulator
// confirmed moves in all 4 directions from - genuinely adjacent to the
// entrance box (walking north from here re-enters it directly), unlike the
// old dead-end spot. Lon Lon Ranch's connector stays one-sided (unlike the
// new North Hyrule Field river bridge below): the user's own bug report
// describes one ladder's top and bottom, not two separate physical sides,
// so simply landing back next to the entrance is the whole fix - no
// GF_RIVER_ENTERED_FROM_B-style side tracking needed here.
static void QuickStartFixupCaveConnectorReturn(void) {
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomTransition.player_status.area_next != AREA_HYRULE_FIELD ||
        gRoomTransition.player_status.room_next != ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        return;
    }
    if (!QuickStart2DoorIsCurrentRoom()) {
        return;
    }
    // Same door-keyed return as the river bridge above. This connector used
    // to land the player on one hard-coded spot no matter which door they
    // left by, which is exactly the bug: it made the interior a dead end
    // that always spat you back out on the same side.
    if (QuickStart2DoorExitSide() == 1) {
        // Written out rather than borrowed. These used to read
        // QUICKSTART_CAVE_RETURN_X/Y - constants named for, and measured in,
        // North Hyrule Field's cave mouth, being applied to a Lon Lon Ranch
        // return purely because the numbers happened to suit. That connector
        // is gone now; the values stay, under their own roof.
        gRoomTransition.player_status.start_pos_x = 264;
        gRoomTransition.player_status.start_pos_y = 344;
    } else {
        gRoomTransition.player_status.start_pos_x = 232;
        gRoomTransition.player_status.start_pos_y = 476;
    }
}

// --- North Hyrule Field's river-crossing 2-door bridge ----------------------
//
// See the GF_RIVER_* comment above for the flag layout and why this is a
// separate draw from Lon Lon Ranch's own 2-door connector rather than a
// shared one - two independent connectors could otherwise both resolve to
// the same physical pool room, which can't correctly serve two different
// bridges' arrival spots at once.
static u8 QuickStartRiverBridgeGetPool(void) {
    return QsCheckFlag(GF_RIVER_POOL_BIT) ? 1 : 0;
}

static void QuickStartRiverBridgeSetPool(u8 pool) {
    if (pool) {
        QsSetFlag(GF_RIVER_POOL_BIT);
    }
}

static u8 QuickStartRiverBridgeGetRoomIndex(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 5; b++) {
        if (QsCheckFlag(GF_RIVER_ROOM_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartRiverBridgeSetRoomIndex(u8 value) {
    s32 b;
    for (b = 0; b < 5; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_RIVER_ROOM_BIT(b));
        }
    }
}

static u8 QuickStartRiverBridgeGetKind(void) {
    return QsCheckFlag(GF_RIVER_KIND_BIT) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
}

static u8 QuickStartRiverBridgeGetExtra(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 3; b++) {
        if (QsCheckFlag(GF_RIVER_EXTRA_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartRiverBridgeGetTarget(u8* area, u8* room) {
    u8 pool = QuickStartRiverBridgeGetPool();
    s32 poolIndex = QuickStartRiverBridgeGetRoomIndex();
    if (pool == 0) {
        poolIndex %= QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE;
        *area = sQuickStart2DoorSmallRoomPool[poolIndex].area;
        *room = sQuickStart2DoorSmallRoomPool[poolIndex].room;
    } else {
        poolIndex %= QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
        *area = sQuickStart2DoorLargeRoomPool[poolIndex].area;
        *room = sQuickStart2DoorLargeRoomPool[poolIndex].room;
    }
}

static void QuickStartRiverBridgeGetSpawnInfo(s16* entranceX, s16* entranceY) {
    u8 pool = QuickStartRiverBridgeGetPool();
    s32 poolIndex = QuickStartRiverBridgeGetRoomIndex();
    if (pool == 0) {
        poolIndex %= QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE;
        *entranceX = sQuickStart2DoorSmallRoomPool[poolIndex].entranceX;
        *entranceY = sQuickStart2DoorSmallRoomPool[poolIndex].entranceY;
    } else {
        poolIndex %= QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
        *entranceX = sQuickStart2DoorLargeRoomPool[poolIndex].entranceX;
        *entranceY = sQuickStart2DoorLargeRoomPool[poolIndex].entranceY;
    }
}

static bool32 QuickStartRiverBridgeIsCurrentRoom(void) {
    u8 area, room;
    if (!QsCheckFlag(GF_RIVER_RANDOMIZED)) {
        return FALSE;
    }
    QuickStartRiverBridgeGetTarget(&area, &room);
    return gRoomControls.area == area && gRoomControls.room == room;
}

// Same "roll it before the player can reach it" timing as every other pool
// draw in this file (see the Melari's Mine Main call site) - reads back
// Lon Lon Ranch's own 2-door draw (already rolled the same frame, called
// right before this one) purely to avoid claiming the identical physical
// room for both connectors.
static void QuickStartRandomizeRiverBridgeOnce(void) {
    u8 pool, kind, roomIdx, poolSize;
    u8 otherPool;
    s32 otherPoolSize, otherResolvedIdx;
    if (QsCheckFlag(GF_RIVER_RANDOMIZED)) {
        return;
    }
    otherPool = QuickStart2DoorGetPool();
    otherPoolSize = (otherPool == 0) ? QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE : QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
    otherResolvedIdx = (s32)QuickStart2DoorGetRoomIndex() % otherPoolSize;
    pool = (u8)((s32)Random() % 2);
    poolSize = (pool == 0) ? QUICKSTART_2DOOR_SMALL_ROOM_POOL_SIZE : QUICKSTART_2DOOR_LARGE_ROOM_POOL_SIZE;
    for (;;) {
        roomIdx = (u8)((s32)Random() % poolSize);
        if (!(pool == otherPool && (s32)roomIdx == otherResolvedIdx)) {
            break;
        }
    }
    QuickStartRiverBridgeSetPool(pool);
    QuickStartRiverBridgeSetRoomIndex(roomIdx);
    kind = ((s32)Random() % 2) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
    if (kind == QS_EVENT_NPC) {
        QsSetFlag(GF_RIVER_KIND_BIT);
        {
            s32 b;
            u8 extra = (u8)((s32)Random() % 2);
            for (b = 0; b < 3; b++) {
                if (extra & (1 << b)) {
                    QsSetFlag(GF_RIVER_EXTRA_BIT(b));
                }
            }
        }
    } else {
        s32 b;
        u8 extra = (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE);
        for (b = 0; b < 3; b++) {
            if (extra & (1 << b)) {
                QsSetFlag(GF_RIVER_EXTRA_BIT(b));
            }
        }
    }
    QsSetFlag(GF_RIVER_RANDOMIZED);
}

// Simple CHEST/NPC content only (same reasoning as Melari's East/Southeast
// rooms - this is a small passage room, not a combat-capable one), placed
// a fixed 20px south of the shared entrance/arrival spot every visit lands
// at regardless of which side the player entered from.
static void QuickStartSetupRiverBridgeRoomContent(void) {
    u8 area, room, kind, extra;
    s16 entranceX, entranceY;
    s32 contentX, contentY;
    // Before the DONE check, not after. Getting the player off a bad tile
    // is about the player's body, not about whether this room still owes
    // them a reward - and it used to sit below the early return, so once
    // the reward had been collected a return visit left them standing
    // wherever the entrance dropped them. In the Veil Falls rupee-path
    // hallway that is the middle of a water pool, which is exactly the
    // "spawns into water and gets stuck" report.
    QuickStartRescuePlayerOntoGround();
    if (QsCheckFlag(GF_RIVER_DONE)) {
        return;
    }
    QuickStartRiverBridgeGetTarget(&area, &room);
    QuickStart2DoorClearRoomObstacles(area, room);
    QuickStartRiverBridgeGetSpawnInfo(&entranceX, &entranceY);
    contentX = entranceX;
    contentY = entranceY + 20;
    // The entrance spots are measured per room now (see the pool table),
    // but keep snapping the content spot against live collision anyway.
    {
        s16 groundX, groundY;
        if (!QuickStartTileIsOpen(contentX >> 4, contentY >> 4) &&
            QuickStartFindOpenTileNear(contentX, contentY, 1, &groundX, &groundY)) {
            contentX = groundX;
            contentY = groundY;
        }
    }
    kind = QuickStartRiverBridgeGetKind();
    extra = QuickStartRiverBridgeGetExtra();
    if (kind == QS_EVENT_ITEM_DROP) {
        if (QsCheckRoomFlag(0)) {
            if (QuickStartGroundItemAt(contentX, contentY)) {
                QsSetRoomFlag(3);
                return;
            }
            if (QsCheckRoomFlag(3)) {
                QsSetFlag(GF_RIVER_DONE);
            }
            return;
        }
        {
            u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) never become a floor
            // entity, so the test is "was it delivered", not "does an
            // entity exist" - see QuickStartSpawnRewardEntity.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(0);
            }
        }
    } else {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
                // Fold the script's own "resolved" write into this room's
                // run latch (see QUICKSTART_NPC_RESOLVED_FLAG's comment).
                if (CheckGlobalFlag(QUICKSTART_NPC_RESOLVED_FLAG)) {
                    QsSetFlag(GF_RIVER_DONE);
                }
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
                QuickStartLoadNpcScratchFlags((u8)extra);
                QuickStartMakeNpcTalkable(npc, sQuickStartEventNpcScripts[0]);
            }
        }
    }
}

// The bridge's two real-world entrances - (280,238) is the user's own given
// ladder position; (120,238) was found by tracing the river (a vertical
// water band confirmed via a live collision-grid dump, roughly tiles
// x=192-224) west from there to a matching dock structure on the far bank.
// Whichever one the player steps into, GF_RIVER_ENTERED_FROM_B records
// which side so QuickStartFixupRiverBridgeReturn can send them out the
// other one later, regardless of which of the pool room's 2 real doors
// they actually leave through.
// RETIRED, per the user: "we should be setting all entrances/exits/rooms
// as vanilla rooms now... the two-way cave connection in North Hyrule
// Field is still using the old pool of 1-door and 2-door ? rooms. We
// should now retire that system ENTIRELY. Connections should now only be
// their vanilla connections, or they should be blocked entrances."
//
// This was the two-sided river crossing: two synthetic trigger spots on
// either bank of North Hyrule Field's river, both warping into whichever
// room the 2-door pool had drawn that save, with a return fixup that sent
// the player out the far side. It is off, so both spots are ordinary
// ground - walking over them does nothing, which is the "blocked" case.
//
// The body is kept rather than deleted because the two bank positions are
// hand-walked survey data (QUICKSTART_RIVER_SIDE_A/B_*), and if the river
// ever gets a REAL crossing those coordinates are where it goes.
#define QUICKSTART_POOL_CONNECTORS_ENABLED 0

static void QuickStartProcessRiverBridgeLink(void) {
    s16 localX, localY;
    u8 targetArea, targetRoom;
    s16 entranceX, entranceY;
    bool32 fromB;
#if !QUICKSTART_POOL_CONNECTORS_ENABLED
    return;
#endif
    if (gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomControls.area != AREA_HYRULE_FIELD || gRoomControls.room != ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD) {
        return;
    }
    localX = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
    localY = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
    if (localX >= QUICKSTART_RIVER_SIDE_A_X - 6 && localX <= QUICKSTART_RIVER_SIDE_A_X + 6 &&
        localY >= QUICKSTART_RIVER_SIDE_A_Y - 6 && localY <= QUICKSTART_RIVER_SIDE_A_Y + 6) {
        fromB = FALSE;
    } else if (localX >= QUICKSTART_RIVER_SIDE_B_X - 6 && localX <= QUICKSTART_RIVER_SIDE_B_X + 6 &&
               localY >= QUICKSTART_RIVER_SIDE_B_Y - 6 && localY <= QUICKSTART_RIVER_SIDE_B_Y + 6) {
        fromB = TRUE;
    } else {
        return;
    }
    if (fromB) {
        QsSetFlag(GF_RIVER_ENTERED_FROM_B);
    } else {
        QsClearFlag(GF_RIVER_ENTERED_FROM_B);
    }
    QuickStartRiverBridgeGetTarget(&targetArea, &targetRoom);
    QuickStartRiverBridgeGetSpawnInfo(&entranceX, &entranceY);
    gRoomTransition.player_status.area_next = targetArea;
    gRoomTransition.player_status.room_next = targetRoom;
    gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
    gRoomTransition.player_status.start_pos_x = entranceX;
    gRoomTransition.player_status.start_pos_y = entranceY;
    gRoomTransition.player_status.layer = 1;
    gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
    gRoomTransition.transitioningOut = 1;
}

// Same "let the real transition fire, then correct the destination before
// it completes" technique as QuickStartFixupCaveConnectorReturn/
// QuickStartFixupQuestionRoomReturn - whichever of the room's 2 real doors
// triggers this, the destination becomes whichever side the player did
// NOT enter from, making the crossing genuinely reversible in both
// directions.
static void QuickStartFixupRiverBridgeReturn(void) {
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (!QuickStartRiverBridgeIsCurrentRoom()) {
        return;
    }
    gRoomTransition.player_status.area_next = AREA_HYRULE_FIELD;
    gRoomTransition.player_status.room_next = ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD;
    // Keyed off WHICH DOOR the player left by, read from the tag the fired
    // transition planted in start_pos_x - not off which side they came in
    // from. That is what makes the crossing work in both directions: door
    // A' always returns to overworld A and B' to B, so A -> B and B -> A are
    // the same mechanism rather than two cases. GF_RIVER_ENTERED_FROM_B is
    // no longer consulted here; it only ever encoded the entry side, which
    // could not distinguish "crossed the room" from "turned around".
    {
        s32 side = QuickStart2DoorExitSide();
        if (side == 1) {
            gRoomTransition.player_status.start_pos_x = QUICKSTART_RIVER_SIDE_B_ARRIVAL_X;
            gRoomTransition.player_status.start_pos_y = QUICKSTART_RIVER_SIDE_B_ARRIVAL_Y;
        } else {
            gRoomTransition.player_status.start_pos_x = QUICKSTART_RIVER_SIDE_A_ARRIVAL_X;
            gRoomTransition.player_status.start_pos_y = QUICKSTART_RIVER_SIDE_A_ARRIVAL_Y;
        }
    }
}

// --- North Hyrule Field's cave mouth (264,304) -------------------------
//
// A third, independent draw from the same 2-door pool - excluded from
// whichever rooms the cave connector and the river bridge above already
// claimed. One-sided like the cave connector (see GF_CAVE_* comment for
// why no side-tracking is needed here).
static u8 QuickStartCaveGetPool(void) {
    return QsCheckFlag(GF_CAVE_POOL_BIT) ? 1 : 0;
}

static void QuickStartCaveSetPool(u8 pool) {
    if (pool) {
        QsSetFlag(GF_CAVE_POOL_BIT);
    }
}

static u8 QuickStartCaveGetRoomIndex(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 5; b++) {
        if (QsCheckFlag(GF_CAVE_ROOM_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

static void QuickStartCaveSetRoomIndex(u8 value) {
    s32 b;
    for (b = 0; b < 5; b++) {
        if (value & (1 << b)) {
            QsSetFlag(GF_CAVE_ROOM_BIT(b));
        }
    }
}

static u8 QuickStartCaveGetKind(void) {
    return QsCheckFlag(GF_CAVE_KIND_BIT) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
}

static u8 QuickStartCaveGetExtra(void) {
    u8 value = 0;
    s32 b;
    for (b = 0; b < 3; b++) {
        if (QsCheckFlag(GF_CAVE_EXTRA_BIT(b))) {
            value |= (1 << b);
        }
    }
    return value;
}

// This connector is no longer a draw. It used to intercept the player at
// North Hyrule Field local (264,304) - six pixels short of the field's own
// real cave mouth at (264,312) - and teleport them into a room drawn from
// the 2-door pool. The room that mouth actually leads to is
// ROOM_CAVES_TO_GRAVEYARD, and re-reading its exit list settles something
// this file used to claim twice: it does NOT escape to Royal Valley. All
// four of its doors are two mouths back into North Hyrule Field, a border
// south back into the same field, and one into
// ROOM_CAVES_HEART_PIECE_HALLWAY - which is itself a ? room whose only
// other exit is that same field. The pair is a closed pocket and always
// was, so there was never anything to contain it from.
//
// So the mouth goes back to being an ordinary vanilla door, and the room
// behind it hosts a ? event like every other pocket interior. Everything
// below this point - the kind/extra roll, the content spawn, the DONE latch
// - is the connector's own machinery, unchanged; only where it points is
// fixed now instead of drawn.
static void QuickStartCaveGetTarget(u8* area, u8* room) {
    *area = QUICKSTART_CAVE_AREA;
    *room = QUICKSTART_CAVE_ROOM;
}

static void QuickStartCaveGetSpawnInfo(s16* entranceX, s16* entranceY) {
    // The arrival point of the field's own mouth
    // (gExitList_HyruleField_NorthHyruleField, endX/endY 0x108,0xd8).
    *entranceX = 0x108;
    *entranceY = 0xd8;
}

static bool32 QuickStartCaveIsCurrentRoom(void) {
    u8 area, room;
    if (!QsCheckFlag(GF_CAVE_RANDOMIZED)) {
        return FALSE;
    }
    QuickStartCaveGetTarget(&area, &room);
    return gRoomControls.area == area && gRoomControls.room == room;
}

// Reads back BOTH the cave connector's and the river bridge's own draws
// (both already rolled earlier this same frame - see the call order in
// QuickStartRoomMonitor) so this third draw can't collide with either.
static void QuickStartRandomizeCaveOnce(void) {
    u8 kind;
    if (QsCheckFlag(GF_CAVE_RANDOMIZED)) {
        return;
    }
    // No pool draw to deconflict any more - the room is fixed, so this only
    // rolls what is IN it. GF_CAVE_POOL_BIT and GF_CAVE_ROOM_BIT are left
    // defined but unwritten; they are 6 contiguous flags held in reserve
    // rather than reshuffled, because moving anything in this block is the
    // silent-collision hazard its own comment warns about.
    kind = ((s32)Random() % 2) ? QS_EVENT_NPC : QS_EVENT_ITEM_DROP;
    if (kind == QS_EVENT_NPC) {
        QsSetFlag(GF_CAVE_KIND_BIT);
        {
            s32 b;
            u8 extra = (u8)((s32)Random() % 2);
            for (b = 0; b < 3; b++) {
                if (extra & (1 << b)) {
                    QsSetFlag(GF_CAVE_EXTRA_BIT(b));
                }
            }
        }
    } else {
        s32 b;
        u8 extra = (u8)((s32)Random() % QUICKSTART_DRAW_SEED_RANGE);
        for (b = 0; b < 3; b++) {
            if (extra & (1 << b)) {
                QsSetFlag(GF_CAVE_EXTRA_BIT(b));
            }
        }
    }
    QsSetFlag(GF_CAVE_RANDOMIZED);
}

// Same simple CHEST/NPC content as the river bridge above.
static void QuickStartSetupCaveRoomContent(void) {
    u8 area, room, kind, extra;
    s16 entranceX, entranceY;
    s32 contentX, contentY;
    // Before the DONE check - same reasoning as the river bridge above.
    QuickStartRescuePlayerOntoGround();
    if (QsCheckFlag(GF_CAVE_DONE)) {
        return;
    }
    QuickStartCaveGetTarget(&area, &room);
    QuickStart2DoorClearRoomObstacles(area, room);
    QuickStartCaveGetSpawnInfo(&entranceX, &entranceY);
    contentX = entranceX;
    contentY = entranceY + 20;
    // Content spot still snapped against live collision.
    {
        s16 groundX, groundY;
        if (!QuickStartTileIsOpen(contentX >> 4, contentY >> 4) &&
            QuickStartFindOpenTileNear(contentX, contentY, 1, &groundX, &groundY)) {
            contentX = groundX;
            contentY = groundY;
        }
    }
    kind = QuickStartCaveGetKind();
    extra = QuickStartCaveGetExtra();
    if (kind == QS_EVENT_ITEM_DROP) {
        if (QsCheckRoomFlag(0)) {
            if (QuickStartGroundItemAt(contentX, contentY)) {
                QsSetRoomFlag(3);
                return;
            }
            if (QsCheckRoomFlag(3)) {
                QsSetFlag(GF_CAVE_DONE);
            }
            return;
        }
        {
            u16 rewardItem = QuickStartDrawItem(extra & 0x3f, QS_CAT_DROP);
            // Direct-grant items (the level-2 sword) never become a floor
            // entity, so the test is "was it delivered", not "does an
            // entity exist" - see QuickStartSpawnRewardEntity.
            if (QuickStartRewardDelivered(rewardItem, contentX, contentY)) {
                QsSetRoomFlag(0);
            }
        }
    } else {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (gEntities[i].base.kind == NPC && gEntities[i].base.id == ZELDA) {
                // Fold the script's own "resolved" write into this room's
                // run latch (see QUICKSTART_NPC_RESOLVED_FLAG's comment).
                if (CheckGlobalFlag(QUICKSTART_NPC_RESOLVED_FLAG)) {
                    QsSetFlag(GF_CAVE_DONE);
                }
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
                QuickStartLoadNpcScratchFlags((u8)extra);
                QuickStartMakeNpcTalkable(npc, sQuickStartEventNpcScripts[0]);
            }
        }
    }
}

// The cave's own real-world entrance box - a plain synthetic position
// check, same technique as the retired cave-connector trigger/
// QuickStartProcessRiverBridgeLink above, not dependent on the real cave
// door's own transition data at all.
// "Fully contained" per the user's request: once inside Castle Garden or the
// Minish House Interiors rooms, no transition - real or our own - is allowed
// to land anywhere else. This is a blanket safety net on top of the specific
// links above, not a replacement for them: it catches every OTHER real exit
// these rooms have (Castle Garden alone has 5 more WARP_TYPE_AREA doors and a
// WARP_TYPE_BORDER one to Hyrule Field) regardless of whether a given one
// currently fires under QUICKSTART - checked every frame, right after
// UpdateDoorTransition and UpdateScroll (see the call site in
// QuickStartRoomMonitor, itself called after both of those every frame) so a
// same-frame cancel always lands before the fade actually starts.
// AREA_TREE_INTERIORS is included too, since the retired ladder-link trigger'
// own transition into it would otherwise get cancelled by this same function
// the instant it fires - it's listed here as a whole area (rather than
// per-room) because Minish House Interiors already needed to be. The "? room"
// pool's other areas (Caves, Great Fairies, Royal Valley Graves) deliberately
// AREN'T added here: each pool room was selected specifically for having
// exactly one real exit (see sQuickStartQuestionRoomPool above), so there's
// no "every OTHER real exit" left for a blanket area-wide net to catch - the
// one real exit each has is already individually retargeted in transitions.c,
// same mechanism as Tree Interiors' ladder rooms below.
//
// AREA_CASTOR_DARKNUT and AREA_MELARIS_MINE were on this list and are not any
// more, and dropping them is load-bearing rather than cosmetic. Castle
// Garden's south border still points at Melari's Mine (transitions.c) from
// when the mine was the hub; with the mine no longer contained, a transition
// from contained Castle Garden to non-contained Melari's Mine is exactly what
// the cancel at the bottom of QuickStartEnforceContainment is for, so that
// edge is now a wall - which is what it should be, since walking out of the
// bottom of Castle Garden used to hand the player a free warp to region slot
// 0. Putting either area back on the route means putting it back on this list.
static bool32 QuickStartAreaContained(u8 area) {
    return area == AREA_CASTLE_GARDEN || area == AREA_MINISH_HOUSE_INTERIORS || area == AREA_TREE_INTERIORS;
}

// Which ladder slot the current room is standing in for, or -1 if it isn't
// one of them. Only slot 0 is live - it backs Castle Garden's northwest
// ladder, the one door still served by a pool draw (see
// QuickStartProcessDoorRedirects). Slots 1-3 and the 15 retired door
// entrances that used to follow them are all gone; they had to be skipped
// rather than merely ignored, and that is not cosmetic: a retired slot's
// pool/room bits are never rolled, so they read back as pool 0 / room
// index 0, and a loop over them would falsely claim whichever real room
// sits at small-pool index 0 - a room another system owns now.
//
// Which physical room slot 0 maps to still varies per save, so a plain
// area/room comparison against fixed constants doesn't work; this checks
// against its current runtime assignment instead.
static s32 QuickStartFindSlotForCurrentRoom(void) {
    s32 rawIndex, poolIndex;
    u8 area, room;
    rawIndex = QuickStartSlotGetRoomIndex(0);
    if (QuickStartSlotGetPool(0) == 0) {
        poolIndex = rawIndex % QUICKSTART_SMALL_ROOM_POOL_SIZE;
        area = sQuickStartSmallRoomPool[poolIndex].area;
        room = sQuickStartSmallRoomPool[poolIndex].room;
    } else {
        poolIndex = rawIndex % QUICKSTART_MEDIUM_ROOM_POOL_SIZE;
        area = sQuickStartMediumRoomPool[poolIndex].area;
        room = sQuickStartMediumRoomPool[poolIndex].room;
    }
    if (gRoomControls.area == area && gRoomControls.room == room) {
        return 0;
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
// the hedge immediately east. Indexed directly by slotIndex (0-3), not by
// draw order, so indices 2 and 3 are unused placeholders here: index 2 is
// retired entirely (see sQuickStartLinks' own comment on the Ranch House
// reset), and index 3 (Goron Cave Stairs door)'s pool room is redirected
// back to Lon Lon Ranch entirely (not just repositioned within Castle
// Garden) by QuickStartFixupQuestionRoomReturn's own slotIndex == 3
// special case below - both are skipped before this array is ever read
// with that index.
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
    s32 slotIndex;
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomTransition.player_status.area_next != AREA_CASTLE_GARDEN ||
        gRoomTransition.player_status.room_next != ROOM_CASTLE_GARDEN_MAIN) {
        return;
    }
    slotIndex = QuickStartFindSlotForCurrentRoom();
    if (slotIndex < 0) {
        return;
    }
    gRoomTransition.player_status.start_pos_x = sQuickStartLadderReturnSpots[slotIndex][0];
    gRoomTransition.player_status.start_pos_y = sQuickStartLadderReturnSpots[slotIndex][1];
}

// Two real vanilla doors whose far side is decided per save rather than by
// the transition data. Both are caught the same way: the door fires
// normally, and this rewrites player_status before the transition lands, so
// the player gets vanilla's own door animation and spawn handling and only
// the destination differs.
//
// This replaces the synthetic position-box teleport for both cases. A box
// fired on proximity rather than on the door itself, which is what made the
// old entrances feel mis-aimed; catching the real transition can't miss,
// because it only runs when the door the player actually walked into has
// already decided to fire.
static void QuickStartProcessDoorRedirects(void) {
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    // Castle Garden's northwest ladder - BLOCKED, per the user: "for the
    // one ladder in Hyrule Castle Garden that was not working (the one that
    // led to the castle dungeon) we can go ahead and block that entrance
    // for now."
    //
    // Its vanilla connection is the Great Fairy cellar, which opens onward
    // into Hyrule Castle - a sprawl this run has no business in. This
    // ladder used to answer that by drawing a random single-door "? room",
    // and it was the last place the old pool system was still used for its
    // original purpose. With the pools retired the choice is vanilla or
    // blocked, and vanilla here means the castle, so: blocked.
    //
    // Cancelling transitioningOut is the same way containment refuses every
    // other transition it does not want (see QuickStartCancelUncontained
    // above) - the player simply stays put, exactly as if the ladder led
    // nowhere.
    if (gRoomTransition.player_status.area_next == AREA_HYRULE_CASTLE_CELLAR &&
        gRoomTransition.player_status.room_next == ROOM_HYRULE_CASTLE_CELLAR_0) {
        gRoomTransition.transitioningOut = 0;
        return;
    }
}


// "? room" pool entries outside Minish House Interiors (Veil Falls Caves,
// Royal Valley Graves) deliberately aren't added wholesale to
// QuickStartAreaContained's area list - those areas are used
// all over the real game from many unrelated vanilla entrances, and
// blanket-containing them would block every one of THOSE rooms' own real
// exits back to the ordinary overworld, a regression far bigger than this
// feature. Instead, this checks the one specific transition
// the retired ladder-link trigger itself is about to make - into whichever
// pool room the ladder the player just stepped into currently resolves
// to - and lets that one through regardless of which area it's in, same
// as the fixed-area escape hatch does for Tree Interiors/Minish House
// Interiors.
static bool32 QuickStartIsCurrentLadderTarget(u8 area, u8 room) {
    s32 i;
    for (i = 0; i < 2; i++) {
        u8 targetArea, targetRoom;
        QuickStartGetSlotTarget(i, &targetArea, &targetRoom);
        if (area == targetArea && room == targetRoom) {
            return TRUE;
        }
    }
    return FALSE;
}

// A "transition" whose destination is the room the player is already in.
// Vanilla uses this shape for in-place respawns, and the Minish portal is
// the one that matters here: enterPortalSubtask.c's sub_0804AD6C sets
// area_next/room_next to gRoomControls' own values and flips
// transitioningOut, to hand the player back to the same room at
// PL_SPAWN_MINISH.
//
// It cannot escape a pocket by construction, so no containment rule has any
// business cancelling it - and cancelling it is fatal rather than merely
// wrong. By the time it fires, the portal sequence has already blanked the
// screen, turned the player's collision and sprite off and taken his
// priority; killing the transition leaves him invisible and uncontrollable
// with nothing left to restore him, while the music plays on. That is the
// "screen froze during the shrinking animation" report exactly.
//
// It also explains why shrinking worked in one region and not the next.
// The FIRST use of a portal type runs the full falling-into-the-Minish-world
// cutscene, which lives in its own gMain.substate - GameMain_Update, and so
// this whole file's per-frame monitor, does not run during it, so the
// transition survives. Every use after that skips the cutscene
// (sub_0804AD18 gates on ENTRANCE_0 + portal_type, which the cutscene sets)
// and respawns inline during ordinary gameplay, right where the monitor can
// cancel it.
static bool32 QuickStartTransitionStaysInSameRoom(void) {
    return gRoomTransition.player_status.area_next == gRoomControls.area &&
           gRoomTransition.player_status.room_next == gRoomControls.room;
}

// The overworld RING: the seven regions circling the missing Hyrule Town -
// Castle Garden, North Hyrule Field, Lon Lon Ranch, Eastern Hills (3 rooms),
// South Hyrule Field, Western Wood (3 rooms), and Trilby Highlands. Per the
// user's overworld-expansion redesign, travel between these is FREE and
// vanilla-shaped: every border between two ring rooms works exactly as
// vanilla built it, plus the two "town bridge" borders that stitch the gap
// the missing town leaves (NHF south <-> SHF north, LLR west <-> Trilby
// east - see transitions.c). The old per-run warp boxes between regions are
// retired with this.
//
// Everything OUTSIDE the ring is blocked in the data itself: the border
// rows to Veil Falls, Lake Hylia, Minish Woods, Castor Wilds, Royal Valley
// and Mt Crenel are compiled out under QUICKSTART, so those edges simply
// stop the player. The containment functions below are the safety net for
// door-type transitions, not the primary wall.
static bool32 QuickStartIsRingRegionRoom(u8 area, u8 room) {
    if (area == AREA_CASTLE_GARDEN && room == ROOM_CASTLE_GARDEN_MAIN) {
        return TRUE;
    }
    if (area != AREA_HYRULE_FIELD) {
        return FALSE;
    }
    switch (room) {
        case ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD:
        case ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD:
        case ROOM_HYRULE_FIELD_LON_LON_RANCH:
        case ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS:
        case ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH:
        case ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER:
        case ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH:
        case ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH:
        case ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER:
        case ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH:
            return TRUE;
        default:
            return FALSE;
    }
}

// A transition between two ring rooms, in either direction - always allowed,
// unconditionally, so the ring reads as one connected map rather than
// opening and closing per run. (Replaces QuickStartIsGardenFieldCrossing,
// which allowed exactly one such pair.)
static bool32 QuickStartIsRingCrossing(u8 fromArea, u8 fromRoom, u8 toArea, u8 toRoom) {
    return QuickStartIsRingRegionRoom(fromArea, fromRoom) && QuickStartIsRingRegionRoom(toArea, toRoom);
}

static void QuickStartEnforceContainment(void) {
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (QuickStartTransitionStaysInSameRoom()) {
        return;
    }
    if (!QuickStartAreaContained(gRoomControls.area)) {
        return;
    }
    if (QuickStartIsCurrentLadderTarget(gRoomTransition.player_status.area_next, gRoomTransition.player_status.room_next)) {
        return;
    }
    // Real vanilla travel inside the "? room" pocket. Two things need this.
    //
    // AREA_TREE_INTERIORS is on QuickStartAreaContained's list, so without
    // it the tree rooms' own real vanilla exits - back out to their field,
    // or down into the Boomerang cave hub - would all be cancelled,
    // trapping the player inside the first tree they enter.
    //
    // AREA_CASTLE_GARDEN is on that list too, and Castle Garden's two
    // ladders are real vanilla doors now: the Great Fairy cellar and
    // Grimblade's dojo entrance. Without this, stepping onto either ladder
    // would be cancelled the same frame it fired - which is exactly the
    // failure mode that made real doors look like they "never work" under
    // QUICKSTART in the first place.
    //
    // Anything else still falls through to the cancel below.
    if (QuickStartIsPocketTransition(gRoomControls.area, gRoomControls.room,
                                     gRoomTransition.player_status.area_next,
                                     gRoomTransition.player_status.room_next)) {
        return;
    }
    // A contained ring room (Castle Garden) leaving for any other ring room
    // - free travel across the whole ring, per the overworld expansion.
    if (QuickStartIsRingCrossing(gRoomControls.area, gRoomControls.room,
                                 gRoomTransition.player_status.area_next,
                                 gRoomTransition.player_status.room_next)) {
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
// position box into the two ranch house rooms, and the retired ladder-link trigger'
// own transition into whichever pool room ladder 3 (the Goron Cave Stairs
// door) currently resolves to, are both explicitly allowed through below.
static void QuickStartEnforceLonLonContainment(void) {
    u8 ladder3TargetArea, ladder3TargetRoom;
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (QuickStartTransitionStaysInSameRoom()) {
        return;
    }
    if (gRoomControls.area != AREA_HYRULE_FIELD || gRoomControls.room != ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        return;
    }
    // Any other ring room - free travel, including the west "town bridge"
    // border into Trilby Highlands and the ranch's own seam down into
    // Eastern Hills North. (Also covers a transition back into the ranch
    // itself, which the old self-room check allowed explicitly.)
    if (QuickStartIsRingCrossing(gRoomControls.area, gRoomControls.room,
                                 gRoomTransition.player_status.area_next,
                                 gRoomTransition.player_status.room_next)) {
        return;
    }
    // The shallow-water cave, down the staircase a Kinstone fusion reveals.
    // A real vanilla WARP_TYPE_AREA door, same situation as the ranch houses
    // below: this only has to avoid cancelling it. The way back needs nothing
    // - AREA_CAVES is not a contained area, so the cave's own exit is not
    // policed at all.
    if (gRoomTransition.player_status.area_next == AREA_CAVES &&
        gRoomTransition.player_status.room_next == ROOM_CAVES_LON_LON_RANCH_WALLET) {
        return;
    }
    // Talon and Malon's house, reset to vanilla (see sQuickStartLinks' own
    // comment) - no custom trigger box for either room anymore, just the
    // real vanilla WARP_TYPE_AREA doors themselves, same "may not always
    // fire under QUICKSTART" situation as Castle Garden's own real north
    // door. This just lets either one through without canceling it if it
    // does fire - nothing else is done for this house anymore.
    if (gRoomTransition.player_status.area_next == AREA_HOUSE_INTERIORS_4 &&
        (gRoomTransition.player_status.room_next == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST ||
         gRoomTransition.player_status.room_next == ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST)) {
        return;
    }
    // The cave connector's own synthetic entrance (the retired cave-connector trigger)
    // fires from right here in Lon Lon Ranch, targeting whichever real
    // 2-door pool room the save's draw resolved to - varies per save, so
    // (unlike the fixed exceptions above) this has to be resolved at check
    // time rather than compared against a single constant. Replaces the
    // old GENTARI_EXIT-specific exception now that the connector draws from
    // a real pool instead of one fixed room.
    {
        u8 doorTargetArea, doorTargetRoom;
        QuickStart2DoorGetTarget(&doorTargetArea, &doorTargetRoom);
        if (gRoomTransition.player_status.area_next == doorTargetArea &&
            gRoomTransition.player_status.room_next == doorTargetRoom) {
            return;
        }
    }
    QuickStartGetSlotTarget(3, &ladder3TargetArea, &ladder3TargetRoom);
    if (gRoomTransition.player_status.area_next == ladder3TargetArea &&
        gRoomTransition.player_status.room_next == ladder3TargetRoom) {
        return;
    }
    // The Goron Cave door, a real vanilla WARP_TYPE_AREA door again (the
    // synthetic entrance that used to shadow it is retired). Same shape as
    // the pocket exception in the other two containment functions.
    if (QuickStartIsPocketTransition(gRoomControls.area, gRoomControls.room,
                                     gRoomTransition.player_status.area_next,
                                     gRoomTransition.player_status.room_next)) {
        return;
    }
    gRoomTransition.transitioningOut = 0;
}

// South Hyrule Field, North Hyrule Field, and Trilby Highlands - same
// "AREA_HYRULE_FIELD is too big to blanket-contain" situation
// QuickStartEnforceLonLonContainment's own comment describes (all 3 are
// big vanilla overworld screens with several real border/door exits of
// their own, most leading to areas entirely outside this run - Hyrule
// Town, Veil Falls, Royal Valley, Mt Crenel, depending on the room), so
// each needs the same kind of room-scoped containment Lon Lon Ranch
// already gets - generalized here to cover all 3 at once, since (unlike
// Lon Lon Ranch's own small, fixed set of exceptions - the wallet cave,
// the two ranch houses, the Goron Cave Stairs pool room) the only real
// destinations any of these 3 rooms needs to allow are generic: the
// chain's own "next" region (varies per save, same dynamic lookup Lon
// Lon's version already uses), and whichever pool room any of the 15
// single-door "? room" entrances physically inside the room being left
// currently resolves to (the retired ladder-entrance table - these fire their
// own real transition later this same frame via
// the retired ladder-link trigger, but this containment check runs first
// and would otherwise cancel them out from under themselves during the
// multi-frame transition-out window, exactly the bug this function
// exists to prevent for illegitimate transitions). Cancels anything else
// (transitioningOut = 0), which is what actually blocks every other real
// vanilla border these rooms still have.
static void QuickStartEnforceFieldRegionContainment(void) {
    s32 i;
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (QuickStartTransitionStaysInSameRoom()) {
        return;
    }
    // Every AREA_HYRULE_FIELD ring room is policed here now - the ranch
    // keeps its own function below only because its exception list (wallet
    // cave, ranch houses, Goron cave, the 2-door connector) is longer.
    if (gRoomControls.area != AREA_HYRULE_FIELD ||
        gRoomControls.room == ROOM_HYRULE_FIELD_LON_LON_RANCH ||
        !QuickStartIsRingRegionRoom(gRoomControls.area, gRoomControls.room)) {
        return;
    }
    // Any other ring room - free travel across the whole ring, including
    // the two "town bridge" borders and Castle Garden. See
    // QuickStartIsRingCrossing.
    if (QuickStartIsRingCrossing(gRoomControls.area, gRoomControls.room,
                                 gRoomTransition.player_status.area_next,
                                 gRoomTransition.player_status.room_next)) {
        return;
    }
    // The river bridge's own two entrances (QuickStartProcessRiverBridgeLink)
    // fire from right here in North Hyrule Field, targeting whichever real
    // pool room this save's draw resolved to - same "varies per save,
    // resolve at check time" reasoning as QuickStartEnforceLonLonContainment's
    // own cave-connector exception.
    if (gRoomControls.room == ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD && QsCheckFlag(GF_RIVER_RANDOMIZED)) {
        u8 targetArea, targetRoom;
        QuickStartRiverBridgeGetTarget(&targetArea, &targetRoom);
        if (gRoomTransition.player_status.area_next == targetArea && gRoomTransition.player_status.room_next == targetRoom) {
            return;
        }
    }
    // The restored vanilla "? room" doors leaving these 3 field rooms - the
    // 5 North Hyrule Field trees plus its Heart Piece Hallway cave, South
    // Hyrule Field's 3 doors plus Link's House, and Trilby Highlands' 4.
    // Unlike every other exception in this function these aren't synthetic
    // links at all - they're real WARP_TYPE_AREA transitions fired by
    // vanilla's own UpdateDoorTransition, so there's nothing to look up
    // per save; the destination just has to be inside the pocket.
    if (QuickStartIsPocketTransition(gRoomControls.area, gRoomControls.room,
                                     gRoomTransition.player_status.area_next,
                                     gRoomTransition.player_status.room_next)) {
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
            // arrival). The one link that set it explicitly aimed at Castor
            // Darknut Hall and is retired with it; every remaining link
            // leaves it alone, matching this function's prior behavior.
            gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
            gRoomTransition.transitioningOut = 1;
            return;
        }
    }
}

// The Boomerang chamber and its five entrances.
//
// Vanilla builds this as a one-way prize room: you drop in, open the
// Magical Boomerang chest, and the ladders back up appear as part of that
// event. Under QUICKSTART nobody opens that chest - it is deleted - so
// without this the room is a trap with two working exits out of five, and
// the four tree ladders leading down into it never fire at all.
//
// Two different problems, both fixed by writing the tile the engine's own
// door check reads:
//
//  - The trees. Each tree hollow draws a ladder going down, but it is
//    tilemap art with nothing behind it: the tile at the door reads 0x00,
//    and unlike Castle Garden's ladders there is no HIDDEN_LADDER_DOWN
//    object to unlock, so there is nothing to reveal. TILE_TYPE_422 is the
//    centre tile HiddenLadderDown itself lays down, and it maps to
//    ACT_TILE_63 - one of the four values UpdateDoorTransition fires on.
//
//  - The chamber's own exits. Its northwest and northeast ladders are armed
//    in the map data already (they read ACT_TILE_241), but the southwest
//    and southeast ones and the staircase back up to the field are not.
//    Note that LadderUp's own SetTile(SPECIAL_TILE_35) is NOT what arms
//    these - that produces actTile 0x53, which is not door-capable; it is
//    the map data that arms the two that already work.
#define QUICKSTART_TREE_LADDER_DOWN_X 0x78
#define QUICKSTART_TREE_LADDER_DOWN_Y 0x54

static bool32 QuickStartIsBoomerangTree(u8 area, u8 room) {
    return area == AREA_TREE_INTERIORS &&
           (room == ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST || room == ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST ||
            room == ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST || room == ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST);
}

// Arms a door by writing ONLY its actTile - the single value
// UpdateDoorTransition actually reads (it fires on ACT_TILE_40/41/63/241).
// Nothing about the tile's graphics or its collision is touched.
//
// This started out copying HiddenLadderDown_Init instead, laying down its
// full 3x3 TILE_TYPE_418..426 patch. That was wrong, and it is what caused
// the artifacts and the invisible walls: those nine tile types are used
// by exactly one thing in the whole game, Castle Garden's hidden ladders,
// and they mean "ladder" only in that area's tileset. Writing them into
// the Caves and Tree Interiors tilesets stamps whatever art those indices
// happen to address there - hence the visual garbage - and each one also
// carries its own collision (see gUnk in playerItemBow.c's table), which
// is what was blocking Link on tiles that looked like open floor.
//
// The doorways already have ladder and staircase art drawn on them by
// vanilla; the only thing missing was the actTile. So set that and nothing
// else.
static void QuickStartArmLadderTiles(s32 localX, s32 localY) {
    SetActTileAtTilePos(ACT_TILE_63, TILE_POS(localX >> 4, localY >> 4), 1);
}

static void QuickStartOpenBoomerangChamber(void) {
    if (QsCheckRoomFlag(6)) {
        return;
    }
    if (QuickStartIsBoomerangTree(gRoomControls.area, gRoomControls.room)) {
        QsSetRoomFlag(6);
        // Two overlapping patches, not one. The tree's ladder is approached
        // from BELOW, unlike Castle Garden's (which the player steps down
        // onto from above), and a single patch centred on the door left a
        // few pixels of solid lip at its bottom edge: forcing the player
        // onto the door tile fired the transition every time, but walking
        // up into it stopped dead at y=91. Extending the patch one tile
        // further down gives a walkable run all the way onto the door.
        // One tile, not the two overlapping patches this used to need. Those
        // existed only to work around a collision lip the tile-type patch
        // was itself creating; with nothing but the actTile changing, the
        // vanilla floor underneath is untouched and there is no lip.
        QuickStartArmLadderTiles(QUICKSTART_TREE_LADDER_DOWN_X, QUICKSTART_TREE_LADDER_DOWN_Y);
        return;
    }
    if (gRoomControls.area != AREA_CAVES || gRoomControls.room != ROOM_CAVES_BOOMERANG) {
        return;
    }
    QsSetRoomFlag(6);
    QuickStartArmLadderTiles(0x48, 0xd8);  // southwest ladder up
    QuickStartArmLadderTiles(0x108, 0xd8); // southeast ladder up
    QuickStartArmLadderTiles(0xa8, 0xb8);  // the staircase back up to the field
    // The Magical Boomerang chest. Its spot is the fifth event's spot now,
    // per the user's own request to replace it rather than keep both.
    {
        s32 i;
        for (i = 0; i < MAX_ENTITIES; i++) {
            Entity* ent = &gEntities[i].base;
            if (ent->kind == OBJECT && ent->id == CHEST_SPAWNER && QuickStartEntityInCurrentRoom(ent)) {
                DeleteEntity(ent);
            }
        }
    }
}

// The engine's RNG state (0x03001150) is a plain scrambler with no entropy
// input at all - state = ror(state * 3, 13) - and it resets to the fixed
// constant 0x1234567 on every reset. Nothing ever seeds it. So the only
// thing that makes one run differ from another is HOW MANY times Random()
// happened to have been called before a given roll, and that is a function
// of elapsed frames. Measured directly: booting with the same input
// sequence produced byte-identical draws every time, and only changing the
// number of idle frames changed them.
//
// That is why the same rooms kept rolling the same events playthrough after
// playthrough. The boot sequence is effectively fixed - the player mashes
// through the same menus - so every run arrived at each "? room" with the
// generator in the same state.
//
// This folds the player's own timing in: every frame that carries new input
// burns one extra Random(). The number of input frames before the player
// reaches any given room is genuinely variable between playthroughs, so
// every roll made after the player has started pressing buttons diverges.
// It costs one call per input frame and needs no state of its own.
//
// Rolls made BEFORE any input - the ones in GameTask_Transition - are not
// covered by this and are still fixed per build.
static void QuickStartStirRandom(void) {
    if (gPlayerState.playerInput.newInput != 0) {
        Random();
    }
}

// Trilby Highlands' boulder-and-hole crossing, solved on arrival.
//
// A large part of the region's south and west sits behind it, and the hole
// ships open, so that ground was unreachable and any wave enemy placed
// there could never be cleared. Vanilla's puzzle is to shove the boulder
// one tile into the hole; under QUICKSTART it simply starts shoved.
//
// This does not fake the result - it drives vanilla's own mechanism.
// PushableRock's init path (sub_0808A644, pushableRock.c) already contains
// the whole "am I sitting on a hole" case: it checks its tile's actTile for
// ACT_TILE_25/ACT_TILE_240, and if so lays SPECIAL_TILE_21 over the hole,
// sets the puzzle's own flag and drops the rock into its settled state. So
// moving the rock onto the hole and bouncing it back to action 0 makes the
// game solve the puzzle itself, exactly as though the player had pushed it.
//
// The hole is found by scanning rather than hardcoded: the boulder sits at
// (344,664) with its hole one tile north at (344,648), but a search of the
// tiles around whatever rock is present costs nothing and keeps this
// working if either moves.
// The tail of PushableRockEntity (src/object/pushableRock.c), mirrored here
// because that struct lives in its own .c file with no header. Only the two
// fields below are read: PushableRock_Init -> sub_0808A644 stashes the tile
// that was under the rock before it stamped its own solid SPECIAL_TILE_27
// over it, and that is exactly what has to be put back before the rock is
// moved anywhere.
typedef struct {
    Entity base;
    u8 unk_68[8];
    u16 tileIndex;
    u8 collisionData;
    u8 unk_73;
    u16 tilePos;
} QuickStartPushableRock;

// Switch-operated bridges: a gap in a real vanilla structure that closes
// when the room's own switch is thrown, and stays closed for the rest of
// the run.
//
// North Hyrule Field ships with a wooden bridge over the river that is
// built but not joined - two planks reaching out from either bank with
// three tiles of open water between them. The room also has a HITTABLE_LEVER
// at local (56,456), which vanilla wires to nothing this build can find:
// it toggles ROOM flag 100 (its hitFlag reads 0x8064 - index 100, type 2)
// and nothing in LoadRoomTileEntities consumes that flag. So the lever is
// free for us to give a job to, and joining the bridge is the one the user
// asked for.
//
// The fill is done by COPYING A NEIGHBOURING TILE rather than by writing a
// tile type. That distinction matters and is the general method to reuse
// for anything else that needs to extend a structure: SetTile takes a tile
// index, GetTileIndex hands back the one already at a position, and a tile
// lifted from two tiles away in the same room is by construction from that
// room's own tileset - graphics, collision and act tile all consistent.
// Writing a TILE_TYPE_* constant instead is what put foreign artwork and
// invisible walls in the Boomerang chamber (see QuickStartArmLadderTiles,
// which had to be rewritten to touch actTiles only). Measured here: the gap
// reads collision 48 / actTile 16 (water) and the planks either side read
// collision 0 / actTile 14, so a copied plank tile brings the walkable
// collision with it and nothing has to be hardcoded.
//
// Two flags, because they answer different questions. armRoomFlag is
// vanilla's own room flag - deliberately NOT run through QsCheckRoomFlag's
// private window, since the lever writes it directly - and only says "the
// switch is thrown right now"; room flags reset on every room load, so on
// its own the bridge would come apart the moment the player left. doneFlag
// is one of ours, so it survives the round trip. The per-visit flag stops
// the copy re-running every frame.
typedef struct {
    u8 area;
    u8 room;
    u16 armRoomFlag; // vanilla's, set by the room's own switch
    u16 doneFlag;    // ours, latched for the rest of the run
    s16 donorX;      // an intact tile of the structure, on each filled row
    s16 minX;
    s16 maxX;
    s16 minY;
    s16 maxY;
} QuickStartSwitchBridge;

#define QUICKSTART_BRIDGE_APPLIED_FLAG 50

static const QuickStartSwitchBridge sQuickStartSwitchBridges[] = {
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 100, GF_NHF_BRIDGE_JOINED, 144, 160, 192, 592, 608 },
};

static void QuickStartUpdateSwitchBridges(void) {
    s32 i, x, y;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartSwitchBridges); i++) {
        const QuickStartSwitchBridge* bridge = &sQuickStartSwitchBridges[i];
        if (gRoomControls.area != bridge->area || gRoomControls.room != bridge->room) {
            continue;
        }
        if (!QsCheckFlag(bridge->doneFlag)) {
            // Raw CheckRoomFlag on purpose - this is the lever's own bit,
            // written by vanilla code, not one of ours.
            if (!CheckRoomFlag(bridge->armRoomFlag)) {
                continue;
            }
            QsSetFlag(bridge->doneFlag);
        }
        if (QsCheckRoomFlag(QUICKSTART_BRIDGE_APPLIED_FLAG)) {
            continue;
        }
        for (y = bridge->minY; y <= bridge->maxY; y += 16) {
            // The donor's tile TYPE, not its raw tile index. SetTile(index)
            // updates mapData and the collision/act maps - measured, the gap
            // went from index 465-467 / collision 48 to the donor's index 23
            // / collision 0 - but the player then walked across water that
            // still looked like water, because nothing redrew the on-screen
            // BG buffer. SetTileType is the path vanilla itself uses for a
            // visible change (it is what HittableLever calls to flip its own
            // tile), and going through the type keeps this donor-relative:
            // still no tileset constant hardcoded anywhere.
            u32 donor = GetTileTypeAtTilePos(TILE_POS(bridge->donorX >> 4, y >> 4), 1);
            for (x = bridge->minX; x <= bridge->maxX; x += 16) {
                SetTileType(donor, TILE_POS(x >> 4, y >> 4), 1);
            }
        }
        // SetTile updates the map's collision and act tiles immediately, but
        // the visible background is only re-streamed as the camera scrolls -
        // so without this the player walks across water that still looks
        // like water (confirmed by screenshot: collision read 0/14 across
        // the gap while the tiles on screen were unchanged). Same one-byte
        // "redraw what's on screen" request every other tile-editing site in
        // the engine makes, e.g. cutscene.c.
        gUpdateVisibleTiles = 1;
        QsSetRoomFlag(QUICKSTART_BRIDGE_APPLIED_FLAG);
    }
}

static void QuickStartFillBoulderHoles(void) {
    s32 i, dx, dy;
    // Every ring region, not just Trilby any more: this replaced Lon Lon
    // Ranch's retired teleport-and-stamp solver (whose SetTileType write
    // left a black square over each filled hole - see the RETIRED note by
    // QuickStartClearEasternHillsNpcs), and driving vanilla's own settle
    // path is the method that renders correctly. Scoped to ring rooms so a
    // 2-door pool cave's pushable-rock PUZZLE is never solved out from
    // under the player.
    if (!QuickStartIsRingRegionRoom(gRoomControls.area, gRoomControls.room)) {
        return;
    }
    // Settled-room guard (QuickStartRoomSettled) - the scan and the
    // teleport below are origin-relative.
    if (!QuickStartRoomSettled()) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* rock = &gEntities[i].base;
        if (rock->kind != OBJECT || rock->id != PUSHABLE_ROCK || !QuickStartEntityInCurrentRoom(rock)) {
            continue;
        }
        // action 3 is "already settled into a hole" - leave those alone, or
        // this would re-trigger the fill every frame.
        if (rock->action == 0 || rock->action == 3) {
            continue;
        }
        for (dy = -3; dy <= 3; dy++) {
            for (dx = -3; dx <= 3; dx++) {
                s32 lx = (rock->x.HALF.HI - gRoomControls.origin_x) + dx * 16;
                s32 ly = (rock->y.HALF.HI - gRoomControls.origin_y) + dy * 16;
                u32 tilePos = TILE_POS(lx >> 4, ly >> 4);
                u32 actTile = GetActTileAtTilePos(tilePos, rock->collisionLayer);
                if (actTile != ACT_TILE_25 && actTile != ACT_TILE_240) {
                    continue;
                }
                // Put the rock's original tile back before moving it.
                // PushableRock_Init stamps SPECIAL_TILE_27 - a solid tile -
                // wherever the rock is standing, and vanilla only ever
                // un-stamps it in PushableRock_Action1, on the frame a real
                // push starts. Teleporting the rock skipped that, so the
                // solid tile stayed behind at the rock's starting spot and
                // read in play as an invisible wall right where the boulder
                // used to be (reported by the user). This is the same
                // SetTile(tileIndex, tilePos) call Action1 makes.
                SetTile(((QuickStartPushableRock*)rock)->tileIndex, ((QuickStartPushableRock*)rock)->tilePos,
                        rock->collisionLayer);
                rock->x.HALF.HI = gRoomControls.origin_x + ((lx >> 4) * 16 + 8);
                rock->y.HALF.HI = gRoomControls.origin_y + ((ly >> 4) * 16 + 8);
                rock->action = 0;
                return;
            }
        }
    }
}

// Lon Lon Ranch's house doors.
//
// The player starts with the Lon Lon Key and still cannot open the
// front-left door, which left both ranch house rooms unreachable. The cause
// is not the key and not the interior door: both exterior doors are
// HOUSE_DOOR_EXT objects, and the west one runs with ENT_SCRIPTED set, so
// HouseDoorExterior_Type2 hands its open/closed state to a script instead
// of to the ordinary "stand against it holding up" check
// (sub_08086954). That script is vanilla's own key/story gate, and nothing
// in this run ever satisfies it.
//
// Rather than fight the script, this does what vanilla's own sub_0808692C
// does: drops ENT_SCRIPTED, puts the door back on the plain walk-up-to-open
// type, and resets its timer. The door then behaves like every other house
// door in the game. Per the user's own call this is unconditional for now -
// the house is simply open - with the key or a minish-door route left as a
// later change if it should be earned instead.
static void QuickStartUnlockRanchHouseDoors(void) {
    s32 i;
    if (gRoomControls.area != AREA_HYRULE_FIELD || gRoomControls.room != ROOM_HYRULE_FIELD_LON_LON_RANCH) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind != OBJECT || ent->id != HOUSE_DOOR_EXT || !QuickStartEntityInCurrentRoom(ent)) {
            continue;
        }
        if (ent->flags & ENT_SCRIPTED) {
            ent->flags &= ~ENT_SCRIPTED;
            ent->type2 = 2;
            ent->action = (ent->frameIndex == 0) ? 1 : 2;
            ent->subAction = 0;
            ent->timer = 8;
        }
    }
}

// Unlocks the vanilla fixtures that genuinely have no working vanilla path
// under QUICKSTART: Link's House's own front door (its story-driven lock
// has no story to open it) and any Kinstone-fusion portal stone (no
// kinstone economy yet).
//
// What this deliberately does NOT touch any more - both used to be
// force-revealed here, and the user reversed that call ("The ladders and
// tree stump should be hidden, initially"):
//
//  - HIDDEN_LADDER_DOWN (Castle Garden's two "? room" ladders): in vanilla
//    they stay invisible - ordinary ground, no door actTile - until the
//    cover on top (the garden's grass tufts) is cleared. That reveal path
//    is entirely self-contained and works under QUICKSTART:
//    HiddenLadderDown_Action1 polls its own tile every frame and latches
//    its flag the moment the cover is gone, and its Init then lays down
//    TILE_TYPE_418..426, whose centre (422) is the ACT_TILE_63 the vanilla
//    door transition fires on. Cut the grass, get a ladder.
//
//  - TREE_HIDING_PORTAL (the tree stump hiding each region's Minish
//    portal): vanilla reveals it on PLAYER_BOUNCE against its own
//    ACT_TILE_84 - a Pegasus Boots dash into the tree. That makes every
//    stump portal (and everything behind it: South Hyrule Field's two
//    Minish rooms, Castle Garden's northeast wall hole) an item-gated
//    route that only a run that CHOSE the boots can open, which is now the
//    intended design, mirroring how the Flippers gate Trilby Highlands.
static void QuickStartFixupRoomFixtures(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* entity = &gEntities[i].base;
        if (entity->kind != OBJECT || !QuickStartEntityInCurrentRoom(entity)) {
            continue;
        }
        if (entity->id == HOUSE_DOOR_INT && entity->action == 1) {
            // Link's House has the same problem one level down. Its front
            // door is a HOUSE_DOOR_INT, and HouseDoorInterior_Action1
            // (src/object/houseDoorInterior.c) only opens on "stand against
            // it holding the right direction" when its unk7d is 0 - Link's
            // House's own instance ships with unk7d = 1 (read back live
            // from the running game), so in vanilla that door is opened by
            // the story instead, through its doorFlags. Its doorFlags is 0,
            // i.e. there is no flag that would ever open it.
            //
            // That makes the room a trap under QUICKSTART: the front door
            // in South Hyrule Field lets the player walk in, and nothing
            // lets them walk back out. Clearing unk7d restores the ordinary
            // "walk into the door and it opens" behaviour every other house
            // in the game has, using vanilla's own mechanism rather than a
            // synthetic exit box.
            ((GenericEntity*)entity)->field_0x7c.BYTES.byte1 = 0;
        } else if (entity->id == MINISH_PORTAL_STONE && entity->action == 1) {
            // The other cover vanilla uses for the same thing, revealed by a
            // Kinstone fusion rather than a roll. None of the five current
            // regions has one, but it costs a branch and it means a region
            // added later needs no new code. This one needs no action bounce
            // - MinishPortalStone_Action1 polls its own flag every frame and
            // runs the reveal animation itself once it is set.
            SetFlag(((GenericEntity*)entity)->field_0x86.HWORD);
        }
    }
}

// Dynamic counterpart to sQuickStartLinks/QuickStartProcessLinks above -
// the region chain's own two kinds of transition, both needing a
// destination resolved at trigger time instead of a fixed table row, same
// reasoning as the retired ladder-link trigger/the retired cave-connector trigger:
// each region's own "onward" exit box (sQuickStartRegionPool's
// exitMinX/MaxX/MinY/MaxY, reused verbatim from the old static Castle
// Garden/Lon Lon Ranch rows), leading to whichever region is next after the
// CURRENT room's own slot - or nowhere, if the current room is already the
// chain's last slot, since winning happens at the reward spot instead of by
// walking anywhere further.
//
// There used to be a second kind here: Melari's Mine's Door B, the hub's own
// way into region slot 0. That job belongs to the pit in Cloud Tops now
// (QuickStartProcessHubHoleLink), and the mine is off the route, so the box
// is gone with it.
//
// RETIRED: QuickStartSkipMelarisMine. Melari's Mine was the hub, and this
// warped the player straight out of it to region slot 0 the moment they
// arrived, so a playthrough reached the overworld without walking the hub.
// Home of the Wind Tribe is the hub now and the pit in Cloud Tops is how a
// run reaches slot 0, so the mine is off the route entirely - which also
// retires the free warp this handed anyone who walked out of the bottom of
// Castle Garden (whose south border still points at the mine; see
// transitions.c). The mine's own content is left intact per the user - the
// area comes back when the region pool grows.
// RETIRED: QuickStartProcessRegionChainLinks, the per-run warp boxes that
// teleported the player from each region's "onward" exit box to whichever
// region the chain drew next. The ring's regions connect by their real
// vanilla borders now (plus the two "town bridge" borders in transitions.c),
// so walking between regions needs no synthetic trigger at all - see
// QuickStartIsRingRegionRoom. The struct's exit box fields go with the next
// region-table reshape.

// Is this one of the hub's rooms? The tower is one area (four floors) and
// its roof is another; both are ours end to end.
// Room flag for the one-shot door unblock below. Well clear of the low
// numbers vanilla room logic uses (see QUICKSTART_ROOM_FLAG_ORIGIN).
#define QUICKSTART_HUB_DOOR_OPENED_FLAG 55

static bool32 QuickStartIsHubRoom(void) {
    return gRoomControls.area == AREA_WIND_TRIBE_TOWER || gRoomControls.area == AREA_WIND_TRIBE_TOWER_ROOF;
}

// The hub's vanilla population, swept every frame.
//
// Home of the Wind Tribe is full of Wind Tribe members - NPC ids 0x49 and
// 0x4a, measured one per floor plus three clustered on Floor 1 - and they
// stand in doorways. The user could not get off the first floor to reach the
// wind crest or the hole because of them.
//
// Not folded into QuickStartClearVanillaRoomContent for two reasons. That
// one is latched to run once per room visit, and the tower's own NPCs arrive
// on a script rather than at load - the chief reappeared after the item
// selection finished, which a one-shot sweep cannot catch. And it deletes
// ground items, which would take the item-choice row with it.
//
// So: enemies and NPCs only, every frame, and never our own sign. ZELDA is
// the entity kind every QUICKSTART NPC borrows (the sign, the merchant, the
// kinstone fusers, the hunt giver), so skipping it protects all of them.
//
// The ROOF is exempt from the enemy half, and has to be: it is the one hub
// room that spawns a wave of its own (QuickStartRoofMonitor below), and an
// every-frame enemy sweep would delete that wave on the frame it appeared.
// Nothing is lost by the exemption - a live entity dump of the roof found no
// vanilla enemies on it, only objects.
static void QuickStartClearHubRoom(void) {
    s32 i;
    bool32 sweepEnemies;
    if (!QuickStartIsHubRoom()) {
        return;
    }
    sweepEnemies = gRoomControls.area != AREA_WIND_TRIBE_TOWER_ROOF;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent == gRoomControls.camera_target) {
            continue;
        }
        if ((sweepEnemies && ent->kind == ENEMY) || (ent->kind == NPC && ent->id != ZELDA)) {
            DeleteEntity(ent);
            continue;
        }
        // The roof's vanilla BIG_VORTEX at (120,72) - the whirlwind that
        // carries the player to the Palace of Winds. That is a whole
        // dungeon outside this mode's world, so the warp goes; per the
        // user, the roof is a combat bonus room, not a door.
        if (ent->kind == OBJECT && ent->id == BIG_VORTEX) {
            DeleteEntity(ent);
        }
    }
    // The front door needs more than the NPC standing in it removed.
    //
    // Measured: the Entrance room's doorway tiles (columns 6-8, row 18) read
    // 0x5f - walkable, the same path-tile value Castle Garden uses - but the
    // two rows BELOW them, 19 and 20, read 0x0f, fully solid. So the player
    // walks into the doorway, stops at y=302, and the south border transition
    // to Cloud Tops (which fires on crossing the room's edge at y=336) can
    // never trigger. The Wind Tribe's ARCHWAY object sits at (120,328), on
    // the far side of that wall.
    //
    // This is the same shape as the Castle Garden guard blocks: vanilla walls
    // an early-game player out of late-game content with solid tiles, keyed
    // on a plot flag this mode never sets. Clearing the collision opens it.
    // Only the three doorway columns, so the rest of the south wall stays.
    if (gRoomControls.area == AREA_WIND_TRIBE_TOWER && gRoomControls.room == ROOM_WIND_TRIBE_TOWER_ENTRANCE &&
        !QsCheckRoomFlag(QUICKSTART_HUB_DOOR_OPENED_FLAG)) {
        QsSetRoomFlag(QUICKSTART_HUB_DOOR_OPENED_FLAG);
        for (i = 6; i <= 8; i++) {
            SetTileType(TILE_TYPE_0, TILE_POS(i, 19), LAYER_BOTTOM);
            SetTileType(TILE_TYPE_0, TILE_POS(i, 20), LAYER_BOTTOM);
        }
    }
}

// --- The inn (Floor 2) ----------------------------------------------------
//
// Three bed alcoves at tiles (4,3) / (7,3) / (10,3) (QUICKSTART_HUB.md's
// Floor 2 survey - each alcove is its own one-tile-wide recess in the north
// wall, so standing in one is an unambiguous, deliberate act). Rest is a
// two-step R interaction handled entirely in C - no script, no interaction
// registration: the first R press in an alcove quotes that bed's price
// (which arms it, room flags 9-11, per visit), the second R press takes the
// rupees, heals, and plays a sleep fade. Walking out of the alcove disarms,
// so an armed state always describes the bed the player is standing at,
// and a stray R elsewhere can never charge anyone. The R button is free
// here: nothing on this floor is liftable and R's other jobs all need a
// target. Healing per the agreed spec: 50 rupees = 25% of max (min 1
// heart), 200 = 50% (min 2 hearts), 500 = full. A heart is 4 units
// (gSave.stats.maxHealth), and ModHealth clamps at max on its own. Beds
// are repeatable - the inn is a rupee sink, not a once-latch. The two
// chest props between the alcoves are the still-open half of the inn spec
// (COMMON/UNCOMMON rewards) and are wired separately via the small-chest
// table (see the chest research note in the roadmap).
#define QUICKSTART_INN_ARMED_FLAG(i) (9 + (i))

static void QuickStartInnMonitor(void) {
    static const u8 sBedTileX[3] = { 4, 7, 10 };
    static const u16 sBedPrice[3] = { 50, 200, 500 };
    s32 i, tx, ty, heal;
    if (gRoomControls.area != AREA_WIND_TRIBE_TOWER || gRoomControls.room != ROOM_WIND_TRIBE_TOWER_FLOOR_2) {
        return;
    }
    if (!QuickStartRoomSettled()) {
        return;
    }
    tx = (gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x) >> 4;
    ty = (gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y) >> 4;
    for (i = 0; i < 3; i++) {
        if (tx == sBedTileX[i] && (ty == 3 || ty == 4)) {
            break;
        }
    }
    if (i == 3) {
        // Not at any bed: disarm whatever was armed.
        for (i = 0; i < 3; i++) {
            if (QsCheckRoomFlag(QUICKSTART_INN_ARMED_FLAG(i))) {
                QsClearRoomFlag(QUICKSTART_INN_ARMED_FLAG(i));
            }
        }
        return;
    }
    // Never process R while any textbox is up (the offer itself included) -
    // a plain message box doesn't necessarily move the player off
    // PLAYER_NORMAL, so the action check alone is not enough.
    if (gMessage.state & MESSAGE_ACTIVE) {
        return;
    }
    if (gPlayerEntity.base.action != PLAYER_NORMAL) {
        return;
    }
    if (!(gInput.newKeys & R_BUTTON)) {
        return;
    }
    if (!QsCheckRoomFlag(QUICKSTART_INN_ARMED_FLAG(i))) {
        s32 j;
        for (j = 0; j < 3; j++) {
            QsClearRoomFlag(QUICKSTART_INN_ARMED_FLAG(j));
        }
        QsSetRoomFlag(QUICKSTART_INN_ARMED_FLAG(i));
        MessageRequest(TEXT_INDEX(TEXT_CUSTOM, (46 + i)));
        MsgInit();
        return;
    }
    if (gSave.stats.rupees < sBedPrice[i]) {
        MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 49));
        MsgInit();
        return;
    }
    ModRupees(-(s32)sBedPrice[i]);
    if (i == 0) {
        heal = (s32)gSave.stats.maxHealth / 4;
        if (heal < 4) {
            heal = 4;
        }
    } else if (i == 1) {
        heal = (s32)gSave.stats.maxHealth / 2;
        if (heal < 8) {
            heal = 8;
        }
    } else {
        heal = gSave.stats.maxHealth;
    }
    ModHealth(heal);
    // Disarm so the next R quotes the price again rather than instantly
    // charging for a second night.
    QsClearRoomFlag(QUICKSTART_INN_ARMED_FLAG(i));
    // The sleep read: the same proven fade the win/reset path uses, behind
    // the wake-up line's textbox.
    SetFade(FADE_IN_OUT | FADE_BLACK_WHITE | FADE_INSTANT, 8);
    SoundReq(SFX_SECRET);
    MessageRequest(TEXT_INDEX(TEXT_CUSTOM, 50));
    MsgInit();
}

// --- The hub's hint sprites ----------------------------------------------
//
// Six Wind Tribe wanderers standing around the hub, each with one line about
// how this mode works (gCustomStrings 20-25, script_QuickStartHubHints.inc).
// Per the user they stay OUT of the spawn room, the shop and the roof - those
// three already have a job - and go in the rooms that are otherwise just
// corridors: the tower entrance, Floor 2, and the clifftop by the wind crest.
//
// Every spot below is an interior tile of the component the player actually
// walks, flooded from that room's own arrival point rather than read off the
// collision map (tools/quickstart/emu.py). Worth naming, because the tower's
// two interior rooms are each split in two:
//
//   Entrance  arrival (136,248); the reachable block is rows 13-18, and the
//             front door out to Cloud Tops is columns 6-8. The two hints
//             flank that walk at x=88 and x=152, leaving the middle clear.
//   Floor 2   same shape, same flanking pair. (Its bed alcoves are up in the
//             other block - that is the inn's floor, still to be built.)
//   Cloud Tops arrival (488,360) from the tower door; the crest is at
//             (488,424) and the pit just south of it. The two hints sit level
//             with the crest at x=392 and x=536, well clear of both, so the
//             player passes between them on the way down to the pit.
extern Script script_QuickStartHubHint0;
extern Script script_QuickStartHubHint1;
extern Script script_QuickStartHubHint2;
extern Script script_QuickStartHubHint3;
extern Script script_QuickStartHubHint4;
extern Script script_QuickStartHubHint5;

typedef struct {
    u8 area;
    u8 room;
    s16 x;
    s16 y;
    Script* script;
} QuickStartHubHint;

static const QuickStartHubHint sQuickStartHubHints[] = {
    { AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_ENTRANCE, 88, 264, &script_QuickStartHubHint0 },
    { AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_ENTRANCE, 152, 264, &script_QuickStartHubHint1 },
    { AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_2, 88, 264, &script_QuickStartHubHint2 },
    { AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_2, 152, 264, &script_QuickStartHubHint3 },
    { AREA_CLOUD_TOPS, ROOM_CLOUD_TOPS_CLOUD_TOPS, 392, 408, &script_QuickStartHubHint4 },
    { AREA_CLOUD_TOPS, ROOM_CLOUD_TOPS_CLOUD_TOPS, 536, 408, &script_QuickStartHubHint5 },
};

// Idempotent by position rather than by flag, the same way
// QuickStartSpawnStarterChoiceOnce is: these rooms are re-entered constantly,
// and a room flag would be wiped by the reload while a global flag would have
// to be cleared per run for no benefit. A hint already standing on its own
// tile is the only evidence needed that it does not want spawning again.
//
// ZELDA is the entity kind every QUICKSTART NPC borrows, which also means
// QuickStartClearHubRoom's every-frame NPC sweep spares these - it only
// deletes NPCs whose id is something else.
// ==================== The trophy case, in the hub =======================
//
// Vanilla's own display case, lifted out of Carlov's shop. FIGURINE_DEVICE
// type 0 is the CASE (type 1 is the lotto machine beside it): it registers
// itself with AddInteractableCheckableObject, so the game draws the "you
// can check this" prompt and routes the button press for us, and its
// handler answers with MenuFadeIn(7, 0xff) - subtask 7 is the figurine
// menu and 0xff is its browse-everything flavour, which is precisely the
// screen we want. Nothing about the interaction had to be rebuilt; only
// its SHOP07_TANA gating had to be bypassed, since this mode never sets
// Carlov's story flags (see the two QUICKSTART branches in
// figurineDevice.c).
//
// It carries gfx 81 / sprite 183 in its object definition - a real entity
// sprite, not painted tiles - so it renders in the tower's tileset the
// same as anywhere else (doctrine 6, the lesson the sprite-less lever
// taught). It also stamps SPECIAL_TILE_34 across its three base tiles for
// collision, which is engine-special rather than tileset art.
//
// WHERE: Floor 3, the spawn room, tile (3,3) - the west end of the open
// hall's top row (rows 3-7 by tx 2-12, measured in docs/QUICKSTART_HUB.md
// sec 2). That row is otherwise empty: the sign NPC is a row above at
// y=40, the item-selection row is a row below at y=72, and the player
// arrives at y=120. So the case stands against the north wall like
// furniture should, in the first room of every run, without narrowing the
// walk to anything.
#define QUICKSTART_TROPHY_CASE_X 56
#define QUICKSTART_TROPHY_CASE_Y 56

// Idempotent by position, exactly like the hub hints below: hub rooms are
// re-entered constantly, and a case already standing on its own tile is
// all the evidence needed that it does not want spawning again. It
// survives QuickStartClearHubRoom's sweep for free - that deletes enemies
// and non-ZELDA NPCs, and this is an OBJECT.
static void QuickStartSpawnTrophyCaseOnce(void) {
    s32 i;
    Entity* box;
    if (gRoomControls.area != AREA_WIND_TRIBE_TOWER || gRoomControls.room != ROOM_WIND_TRIBE_TOWER_FLOOR_3) {
        return;
    }
    if (!QuickStartRoomSettled()) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == FIGURINE_DEVICE) {
            return;
        }
    }
    box = CreateObject(FIGURINE_DEVICE, 0, 0);
    if (box == NULL) {
        return;
    }
    box->x.HALF.HI = gRoomControls.origin_x + QUICKSTART_TROPHY_CASE_X;
    box->y.HALF.HI = gRoomControls.origin_y + QUICKSTART_TROPHY_CASE_Y;
    box->collisionLayer = 1;
    box->flags |= ENT_PERSIST;
    UpdateSpriteForCollisionLayer(box);
}

static void QuickStartSpawnHubHintsOnce(void) {
    s32 i, j;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartHubHints); i++) {
        const QuickStartHubHint* hint = &sQuickStartHubHints[i];
        Entity* npc;
        bool32 present = FALSE;
        if (gRoomControls.area != hint->area || gRoomControls.room != hint->room) {
            continue;
        }
        for (j = 0; j < MAX_ENTITIES; j++) {
            Entity* ent = &gEntities[j].base;
            if (ent->kind == NPC && ent->id == ZELDA && ent->x.HALF.HI == gRoomControls.origin_x + hint->x &&
                ent->y.HALF.HI == gRoomControls.origin_y + hint->y) {
                present = TRUE;
                break;
            }
        }
        if (present) {
            continue;
        }
        npc = CreateNPC(ZELDA, 0, 0);
        if (npc != NULL) {
            npc->x.HALF.HI = gRoomControls.origin_x + hint->x;
            npc->y.HALF.HI = gRoomControls.origin_y + hint->y;
            npc->collisionLayer = 1;
            npc->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(npc);
            npc->direction = IdleSouth;
            QuickStartMakeNpcTalkable(npc, hint->script);
        }
    }
}

// --- The hub's way out: the hole in Cloud Tops ---------------------------
//
// Cloud Tops has exactly ONE Transition row (gExitList_CloudTops_House, back
// into the tower at 488,344), so the pit down to vanilla's lower cloud levels
// is a TILE handled by holeManager.c, not an exit that could be retargeted in
// transitions.c.
//
// This started as a position box, the same technique every other synthetic
// entrance in this file uses, and it did not work in play: the user walked
// into the pit and fell to the vanilla cloud level below. The box was written
// off a survey of "special" tiles at rows 34-36, which are not the pit at all.
// The real geometry is in holeManager.c's own gHoleTransitions table, which is
// the authority and should have been read first: the pit in front of the wind
// crest is the row `{ 0x01, 0x08, 0x01, 0x01, ..., 0x1d, 0x1d, 0x03, 0x03 }` -
// tiles (29,29) 3x3, i.e. pixels (464,464)-(512,512). The box sat at y
// 552-600, a good 40px SOUTH of it, so the player fell through the real pit
// before ever reaching the trigger.
//
// Rather than move the box onto the right coordinates, catch the fall itself.
// DoHoleTransition (holeManager.c) sets gRoomTransition.transitioningOut and
// fills player_status exactly the way a real door does, so the same
// rewrite-the-destination idiom QuickStartProcessDoorRedirects uses works
// here, and works for EVERY pit in the room rather than one hand-measured
// rectangle. Cloud Tops' only non-pit exit is the tower door (area 48), so
// "a transition out of here that is heading to another Cloud Tops room" is an
// exact description of a pit fall.
//
// The drop is left as the hole manager set it up - TRANSITION_CUT, start_anim
// 4, PL_SPAWN_DROP - so the player really does fall out of the sky into the
// region, which is what the design asks for. Only where they land is ours.
//
// The hole drops the player into this run's drawn DROP region - the same
// place every fall within a run (the draw is latched), somewhere new each
// run. The Element is guaranteed within two map regions of it (see
// QuickStartRollElementRegionOnce).
static void QuickStartProcessHubHoleLink(void) {
    const QuickStartRegion* first;
    if (gRoomControls.area != AREA_CLOUD_TOPS || gRoomControls.room != ROOM_CLOUD_TOPS_CLOUD_TOPS) {
        return;
    }
    if (!gRoomTransition.transitioningOut) {
        return;
    }
    if (gRoomTransition.player_status.area_next != AREA_CLOUD_TOPS) {
        return;
    }
    // Explicit-and-idempotent, same reasoning the retired chain roll used:
    // the draw is rolled unconditionally elsewhere, but a run must never
    // begin with the drop/element regions undrawn.
    QuickStartRollElementRegionOnce();
    first = &sQuickStartRegionPool[QuickStartDropRegionIndex()];
    gRoomTransition.player_status.area_next = first->area;
    gRoomTransition.player_status.room_next = first->room;
    gRoomTransition.player_status.start_pos_x = first->entranceX;
    gRoomTransition.player_status.start_pos_y = first->entranceY;
    gRoomTransition.player_status.layer = 1;
}

// --- The hub's roof: one wave, one uncommon-or-rare reward ---------------
//
// Per the user: "roof = enemies at slightly higher difficulty than the run,
// clearing them gives an uncommon-or-rare REWARD." Optional content - the run
// never routes through here, the player climbs one more flight because they
// want to.
//
// GEOMETRY, flooded from the arrival tile rather than eyeballed off the
// collision map (tools/quickstart/emu.py; the flood is what caught that the
// roof's top rows are a separate component). The roof is 240x416 and the
// player arrives from Floor 3 at (184,328). The component reachable from
// there is 121 tiles spanning rows 10-24:
//
//   rows 11-13  a wide north band, columns 1-13
//   rows 14-19  a west corridor, columns 1-5
//   rows 20-24  the south arena, narrowing from columns 1-13 to 4-10
//
// Rows 0-5 (the tower's peak and its two wings) are NOT in that component,
// which is exactly why this uses a hand-placed offset table rather than
// QuickStartSpawnEnemiesOnOpenTiles: that spawner rings outward from an
// anchor over ANY open tile within 40 rings, and would happily put a third of
// the wave somewhere the player cannot follow.
//
// Every offset below is an interior tile of that component - open, with all
// four neighbours open, at least three tiles from its neighbours in the list,
// and none within a tile of the arrival spot so the player is not dropped
// into the middle of the fight.
static const s16 sQuickStartRoofEnemyOffsets[14][2] = {
    { 40, 184 },  { 104, 184 }, { 200, 184 }, { 72, 200 },  { 136, 200 },
    { 40, 232 },  { 72, 248 },  { 40, 280 },  { 72, 296 },  { 40, 328 },
    { 88, 328 },  { 120, 344 }, { 88, 376 },  { 136, 376 },
};
// The arena is 121 tiles, i.e. 30 of the 32x32 squares this density figure is
// measured in. 60 is deliberately double that, and is tuning rather than a
// survey result: at the honest 30 the formula (squares / tier density) yields
// two enemies at difficulty 2 and six at difficulty 12, which is not a fight
// worth climbing for. At 60 it runs 4 -> 10 across the difficulty range, and
// the cap below holds the top end.
#define QUICKSTART_ROOF_ROOM_SQUARES 60
#define QUICKSTART_ROOF_MAX_ENEMIES 10
// "Slightly higher difficulty than the run", clamped to the table's top row.
#define QUICKSTART_ROOF_DIFFICULTY_BONUS 2
// Centre of the north band, 128px from the arrival spot, so the reward is
// something the player walks to rather than lands on.
#define QUICKSTART_ROOF_REWARD_X 120
#define QUICKSTART_ROOF_REWARD_Y 200

// Two bits of run-scoped state, because the roof is its own AREA: leaving it
// for Floor 3 unloads the room and resets every room flag, so nothing keyed
// on those can remember that the wave was already beaten.
//   0 - not cleared
//   1 - cleared, reward is on the floor
//   2 - reward collected; the roof is finished for this run
#define GF_ROOF_STATE_BIT(b) (89 + (b)) // b = 0..1
// The reward's own draw seed, six bits, stored alongside the state.
//
// Not a cosmetic detail: the reward has a re-drop arm (state 1 with nothing on
// the floor means the player left and came back), and rolling a fresh seed
// there turns the roof into a slot machine - clear it once, then walk down a
// flight and back up until the draw hands over a Heart Container. Measured
// doing exactly that: the same cleared roof produced ITEM_RUPEE100 and then
// ITEM_BOTTLE_RED_POTION on consecutive visits. Rolling once, at the clear,
// and replaying it makes every re-drop the same item.
#define GF_ROOF_SEED_BIT(b) (91 + (b)) // b = 0..5

static u8 QuickStartRoofGetState(void) {
    return (u8)((CheckLocalFlagByBank(FLAG_BANK_11, GF_ROOF_STATE_BIT(0)) ? 1 : 0) |
                (CheckLocalFlagByBank(FLAG_BANK_11, GF_ROOF_STATE_BIT(1)) ? 2 : 0));
}

static void QuickStartRoofSetState(u8 state) {
    s32 b;
    for (b = 0; b < 2; b++) {
        if (state & (1 << b)) {
            SetLocalFlagByBank(FLAG_BANK_11, GF_ROOF_STATE_BIT(b));
        } else {
            ClearLocalFlagByBank(FLAG_BANK_11, GF_ROOF_STATE_BIT(b));
        }
    }
}

static s32 QuickStartRoofGetSeed(void) {
    s32 b, seed = 0;
    for (b = 0; b < 6; b++) {
        if (CheckLocalFlagByBank(FLAG_BANK_11, GF_ROOF_SEED_BIT(b))) {
            seed |= (1 << b);
        }
    }
    return seed;
}

static void QuickStartRoofSetSeed(s32 seed) {
    s32 b;
    for (b = 0; b < 6; b++) {
        if (seed & (1 << b)) {
            SetLocalFlagByBank(FLAG_BANK_11, GF_ROOF_SEED_BIT(b));
        } else {
            ClearLocalFlagByBank(FLAG_BANK_11, GF_ROOF_SEED_BIT(b));
        }
    }
}

// UNCOMMON three times in four, RARE the fourth - "an uncommon or rare
// REWARD", weighted so the rare end stays a treat. Four is a power of two on
// purpose: agbcc has no __umodsi3, and a modulus by anything else in this
// tree fails to LINK rather than to compile.
//
// The seed is rolled on the first drop only and replayed on every re-drop, so
// which item this roof gives is decided once - see GF_ROOF_SEED_BIT.
static void QuickStartRoofSpawnReward(void) {
    s32 seed, tier;
    Entity* itemEntity;
    if (QuickStartRoofGetState() == 0) {
        seed = (s32)Random() & 0x3f;
        QuickStartRoofSetSeed(seed);
    } else {
        seed = QuickStartRoofGetSeed();
    }
    tier = ((seed & 3) == 0) ? QS_TIER_RARE : QS_TIER_UNCOMMON;
    itemEntity = CreateObject(GROUND_ITEM, QuickStartDrawAtTier(QuickStartDrawPick(seed), QS_CAT_REWARD, tier), 0);
    if (itemEntity != NULL) {
        itemEntity->x.HALF.HI = gRoomControls.origin_x + QUICKSTART_ROOF_REWARD_X;
        itemEntity->y.HALF.HI = gRoomControls.origin_y + QUICKSTART_ROOF_REWARD_Y;
        itemEntity->collisionLayer = 1;
        itemEntity->flags |= ENT_PERSIST;
        UpdateSpriteForCollisionLayer(itemEntity);
        itemEntity->direction = IdleSouth;
        QuickStartRoofSetState(1);
        QsSetRoomFlag(1);
    }
}

// Same earned/dropped/confirmed shape as QuickStartSpawnRegionRewardOnce,
// minus the re-drop arm - see the state-1 comment below for why the roof
// treats any absence of the item as "done".
//
// Room flag 0 is "this visit's wave is out", and it lives in room flags on
// purpose. Leaving the roof mid-fight and returning gives a fresh wave, which
// is the honest reading of "clearing them gives a reward" - the fight is one
// visit's work, not something to whittle down over several trips.
// The roof's two fairy pots (vanilla room data: POT type 96 at local x 24
// and 216; the two type-0 pots beside them stay vanilla). Vanilla
// respawns them on every room load, which under QUICKSTART meant a free
// fairy top-up per hub visit - the user's report. One life each per run:
// room flags 5/6 record "this visit saw the pot standing", so a later
// absence within the same visit means the player took it (broke it, or
// lifted it and walked off - either way it is spent). That latches the
// per-run GF_FAIRY_POT_BIT, and every later visit's respawn is
// deleted the frame it appears - the same every-frame delete shape
// QuickStartClearHubRoom already uses.
#define QUICKSTART_ROOF_FAIRY_POT_TYPE 96

static void QuickStartRoofFairyPotsOnce(void) {
    static const s16 potX[2] = { 24, 216 };
    s32 i, j;
    for (i = 0; i < 2; i++) {
        Entity* pot = NULL;
        for (j = 0; j < MAX_ENTITIES; j++) {
            Entity* ent = &gEntities[j].base;
            if (ent->kind == OBJECT && ent->id == POT && ent->type == QUICKSTART_ROOF_FAIRY_POT_TYPE &&
                ent->x.HALF.HI - gRoomControls.origin_x == potX[i]) {
                pot = ent;
                break;
            }
        }
        if (QsCheckFlag(GF_FAIRY_POT_BIT(i))) {
            if (pot != NULL) {
                DeleteEntity(pot);
            }
            continue;
        }
        if (pot != NULL) {
            QsSetRoomFlag(5 + i);
        } else if (QsCheckRoomFlag(5 + i)) {
            QsSetFlag(GF_FAIRY_POT_BIT(i));
        }
    }
}

static void QuickStartRoofMonitor(void) {
    u8 state;
    if (gRoomControls.area != AREA_WIND_TRIBE_TOWER_ROOF || gRoomControls.room != ROOM_WIND_TRIBE_TOWER_ROOF_0) {
        return;
    }
    QuickStartRoofFairyPotsOnce();
    state = QuickStartRoofGetState();
    if (state >= 2) {
        return;
    }
    if (state == 1) {
        // The reward drops ONCE, at the first wave's clear, and that is
        // the end of the roof's generosity - per the user. There used to
        // be a re-drop arm here (state 1 + nothing on the floor + a fresh
        // visit -> place it again), meant for "left without picking it
        // up", but it could not tell that apart from "picked it up on the
        // way out": grabbing the reward on the same frame as the stair
        // transition means this monitor never runs again in the roof room
        // to see the item vanish, state sticks at 1, and the next visit's
        // re-drop hands out a second copy (the user's report). Now any
        // absence promotes straight to 2: taken or abandoned, the roof is
        // finished for the run.
        if (QuickStartGroundItemAt(QUICKSTART_ROOF_REWARD_X, QUICKSTART_ROOF_REWARD_Y)) {
            return;
        }
        QuickStartRoofSetState(2);
        return;
    }
    if (!QsCheckRoomFlag(0)) {
        u8 difficulty = QuickStartGetDifficulty() + QUICKSTART_ROOF_DIFFICULTY_BONUS;
        if (difficulty > QUICKSTART_MAX_DIFFICULTY) {
            difficulty = QUICKSTART_MAX_DIFFICULTY;
        }
        QuickStartSpawnEnemyGroupAtDifficulty(sQuickStartRoofEnemyOffsets, ARRAY_COUNT(sQuickStartRoofEnemyOffsets),
                                              QUICKSTART_ROOF_ROOM_SQUARES, QUICKSTART_ROOF_MAX_ENEMIES, difficulty);
        // Latch only if something actually came out. The spawner gives up
        // when the GFX table is at its reserve, and without this check an
        // empty spawn would read as an instantly-cleared wave on the very
        // next frame and hand over the reward for nothing.
        if (QuickStartCountRoomEnemies() > 0) {
            QsSetRoomFlag(0);
        }
        return;
    }
    if (QuickStartCountRoomEnemies() > 0) {
        return;
    }
    QuickStartRoofSpawnReward();
}

// Polled every frame regardless of item-choice phase (unlike
// QuickStartUpdateItemChoice, which is specific to the hub's spawn floor) so
// that leaving the starting room still gets QUICKSTART treatment.
// D2's one reset besides a genuine wave clear: the player LEFT the region.
// "Left" is defined by where they are seen standing, not by which door they
// took - settled in a different pool region, or anywhere in the hub, clears
// every OTHER region's remainder (and the hub clears all of them, so an
// ocarina round trip is a fresh start everywhere). Settled in a pocket room
// (a ? room interior, a cave, a Minish house, a 2-door room) matches
// neither arm and touches nothing - which is exactly the "excursions within
// the region persist" half of the rule, and it makes the fusion room-reload
// free: that reload re-enters the SAME region room. Guarded by the settled
// predicate so a transition's torn frames can't misattribute the player.
static void QuickStartResetOtherWaveRemainders(void) {
    s32 i, current;
    if (!QuickStartRoomSettled()) {
        return;
    }
    if (QuickStartIsHubRoom()) {
        current = -1;
    } else {
        current = QuickStartCurrentRegionPoolIndex();
        if (current < 0) {
            return;
        }
    }
    for (i = 0; i < QUICKSTART_REGION_POOL_SIZE; i++) {
        if (i != current && QuickStartRegionGetAliveCount(i) != 0) {
            QuickStartRegionSetAliveCount(i, 0);
        }
    }
}

// Make a reward on the floor read as a reward.
//
// The standing "? rooms never pay" report has survived every check aimed
// at it: the items demonstrably spawn, and a 34-item sweep showed every
// one of them collectable. Which leaves the possibility that they are
// simply not being NOTICED - a heart piece lying in grass at the far end
// of a field looks like scenery, and the kind was called "chest" in the
// tables for so long that a floor item may just not read as the payout.
//
// Vanilla already has the vocabulary for "this thing matters":
// CreateSparkleFx (objectUtils.c) scatters FX_SPARKLE4 around a parent,
// which is what treasure and secrets use. Emitting it on a slow cycle
// turns our drops into something that catches the eye from across a room
// without becoming a light show.
//
// Scoped to OUR items only. ENT_PERSIST is the marker every reward this
// file places carries and no vanilla room pickup sets, so Lon Lon's
// native heart piece stays as quiet as it has always been.
// A MASK, not a period: agbcc emits __umodsi3 for a modulo by anything
// that is not a power of two, and its runtime library does not provide
// one (the same constraint QuickStartTierPick documents). 31 is a sparkle
// about twice a second per item.
#define QUICKSTART_SPARKLE_PHASE_MASK 31
#define QUICKSTART_SPARKLE_MAX_ITEMS 4

static void QuickStartSparkleRewards(void) {
    s32 i, lit = 0;
    // One item per frame at most, and each item only on its own slot's
    // phase: the effect is an entity, and a room holding several drops
    // should not spend four entity slots on sparkles in the same frame.
    if (!QuickStartRoomSettled()) {
        return;
    }
    for (i = 0; i < MAX_ENTITIES && lit < QUICKSTART_SPARKLE_MAX_ITEMS; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind != OBJECT || ent->id != GROUND_ITEM) {
            continue;
        }
        if ((ent->flags & ENT_PERSIST) == 0) {
            continue;
        }
        lit++;
        // Stagger by slot so several drops twinkle out of step.
        if (((gSave.run_frames + (u32)i) & QUICKSTART_SPARKLE_PHASE_MASK) != 0) {
            continue;
        }
        CreateSparkleFx(ent);
    }
}

static void QuickStartRoomMonitor(void) {
    s32 regionSlot;
    // Run clock for the scoring system's time bonus (QuickStartComputeScore
    // below) - called once per real frame during normal gameplay (from
    // GameMain_Update) plus a handful of extra frames during each room's
    // brief transition window (also called from QuickStartUpdate,
    // GameMain_ChangeRoom) - close enough for a bonus threshold, not worth
    // separating the two call sites over. gSave.run_frames itself is reset
    // to 0 once per run in GameTask_Transition.
    if (gSave.run_frames < 0xFFFFFFFF) {
        gSave.run_frames++;
    }
    QuickStartDrawDifficultyHUD();
    // Before any content runs, so a reward placed on an earlier frame is
    // already immortal by the time this frame's "is it still there?" check
    // looks for it.
    QuickStartRefreshPlacedItemTimers();
    // Every room, not just the ones that can apply a handicap: its whole job
    // is to notice that the player has LEFT the room that stripped them and
    // hand the kit back.
    QuickStartHandicapMonitor();
    QuickStartEnforceContainment();
    QuickStartEnforceLonLonContainment();
    QuickStartEnforceFieldRegionContainment();
    QuickStartFixupQuestionRoomReturn();
    // Runs before the containment checks would see the rewritten
    // destination, so a redirected door is judged on where it is actually
    // going rather than on its vanilla destination.
    QuickStartProcessDoorRedirects();
    QuickStartFixupCaveConnectorReturn();
    QuickStartFixupRiverBridgeReturn();
    // Every per-run draw is rolled unconditionally, not in a specific room.
    //
    // These used to live in Melari's Mine's own branch, on the reasoning
    // that the hub is always visited before anything they feed becomes
    // reachable. That stopped being true the moment the mine stopped being
    // the hub: a draw that never runs leaves every
    // pool index at 0, so every ? room in the run would resolve to the
    // first row of its pool. Each of these is latched by its own
    // GF_*_RANDOMIZED flag, so running them every frame from anywhere
    // costs a handful of flag reads and removes the dependency on any one
    // room being entered.
    QuickStartRollElementRegionOnce();
    QuickStartRandomizeSlotsOnce();
    QuickStart2DoorRandomizeOnce();
    QuickStartRandomizeRiverBridgeOnce();
    QuickStartRandomizeCaveOnce();
    QuickStartRandomizeMelariEastOnce();
    QuickStartRandomizeMelariSoutheastOnce();
    QuickStartRandomizeShopOnce();
    QuickStartRandomizeQuestOnce();
    // Also unconditional: the two rooms that need it today are Castle
    // Garden Main and Link's House, but the checks are per-entity rather
    // than per-room, so any other room's hidden ladder or stuck house door
    // gets the same treatment for free.
    QuickStartFixupRoomFixtures();
    // Same "make a vanilla fixture actually work" job, for the Boomerang
    // chamber's five entrances and its chest.
    QuickStartOpenBoomerangChamber();
    QuickStartUnlockRanchHouseDoors();
    QuickStartFillBoulderHoles();
    QuickStartUpdateSwitchBridges();
    // Global invariant, so it runs everywhere rather than only in the
    // regions that spawn: keep free GFX slots above the reserve.
    QuickStartEnforceGfxReserve();
    // Global invariant too: a camera following a deleted entity follows
    // garbage (see the function's comment for the measured NHF case).
    QuickStartRescueDanglingCamera();
    // The food charms/curses' per-frame half (knockback scaling, enemy
    // haste, shooter cadence) - a single mask read when none are held.
    QuickStartApplyFoodEffects();
    // Inert in play (one guarded compare); the measurement harness's spawn
    // hook - see the mailbox comment above QuickStartMeasureMailbox.
    QuickStartMeasureMailbox();
    QuickStartStirRandom();
    // Retired along with the retired ladder-entrance table itself (now empty) -
    // kept as a call so the dormant synthetic-entrance path stays whole; it
    // returns immediately without matching anything.
    // Same reasoning as the retired ladder-link trigger above - the 2-door
    // pool's one entrance (Lon Lon Ranch's cave mouth) targets a different
    // real room every save, so it can't be folded into a specific room's
    // Same reasoning again - North Hyrule Field's river bridge has two
    // entrances (either bank), each targeting a different real room every
    // save.
    QuickStartProcessRiverBridgeLink();
    // (The region chain's own "onward" exit boxes used to be processed
    // here too - retired with the overworld expansion, the ring's regions
    // connect by their real vanilla borders now.)
    // Deliberately outside the region-chain dispatch below, and ahead of the
    // wave spawner: the fusers are a handful of entities sharing one sprite
    // sheet, while a wave is dozens that can pull the gfx table down to the
    // reserve, so claiming the slot first means a difficulty-12 wave can
    // never be the reason a gate has no fuser standing at it. Being outside
    // the dispatch also means a region's gates are live whether or not this
    // save's chain happens to include it.
    QuickStartSpawnRegionFusers();
    QuickStartTinglePayout();
    QuickStartReloadRoomAfterFusion();
    regionSlot = QuickStartCurrentRegionPoolIndex();
    QuickStartResetOtherWaveRemainders();
    QuickStartClearHubRoom();
    QuickStartSparkleRewards();
    QuickStartInnMonitor();
    QuickStartProcessHubHoleLink();
    QuickStartRoofMonitor();
    QuickStartSpawnHubHintsOnce();
    QuickStartSpawnTrophyCaseOnce();
    // Melari's Mine and its three side rooms are DORMANT, not deleted. The
    // mine was the hub and nothing routes into it any more (its one remaining
    // inbound pointer, Castle Garden's south border, is walled by containment
    // now that the area is off the contained list), so none of these branches
    // can fire today. They are kept whole per the user: the area comes back
    // when the region pool grows, and re-pointing one transition is all it
    // takes. Nothing here costs anything while it is unreachable.
    if (gRoomControls.area == AREA_MELARIS_MINE && gRoomControls.room == ROOM_MELARIS_MINE_MAIN) {
        QuickStartClearMelarisMineObstacles();
        QuickStartSpawnMelarisMineRewardOnce();
        QuickStartSpawnMelarisMineEnemiesOnce();
    } else if (gRoomControls.area == AREA_MINISH_HOUSE_INTERIORS &&
               gRoomControls.room == ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST) {
        QuickStartSetupMelariSoutheastRoomContent();
    } else if (gRoomControls.area == AREA_MINISH_HOUSE_INTERIORS &&
               gRoomControls.room == ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST) {
        QuickStartSetupMelariEastRoomContent();
    } else if (regionSlot >= 0) {
        // Whichever region this save's chain put the current room in -
        // Castle Garden and Lon Lon Ranch today, more later as new regions
        // get surveyed and added to sQuickStartRegionPool.
        QuickStartRegionMonitor(regionSlot);
        // Ground-item pickup alone sets a skill's ITEM_SKILL_* inventory
        // flag but (outside of a full player (re)init) doesn't itself
        // refresh gPlayerState.skills - same gap already hit and fixed for
        // the earlier Woods-gauntlet prototype's boss-skill reward. Cheap
        // and idempotent to just keep it in sync every frame here instead
        // of needing an exact "on pickup" hook. Only Castle Garden's own
        // reward pool has any ITEM_SKILL_* entries today, but this is
        // harmless (and correct to keep doing) for any future region whose
        // pool does too.
        UpdatePlayerSkills();
    } else if (gRoomControls.area == QUICKSTART_SHOP_AREA && gRoomControls.room == QUICKSTART_SHOP_ROOM) {
        // The hub's first floor. No obstacle sweep of its own: every hub room
        // already gets QuickStartClearHubRoom, which clears the Wind Tribe's
        // enemies and NPCs while sparing our ZELDA-kind merchant. The old
        // blanket "delete every OBJECT that isn't a SHOP_ITEM" sweep the
        // Stockwell room used would have taken this floor's two ARCHWAY
        // objects with it - and those sit on the stair doors at (136,216) and
        // (184,216), the room's only way in or out.
        QuickStartSpawnShopMerchantOnce(QUICKSTART_SHOP_MERCHANT_X, QUICKSTART_SHOP_MERCHANT_Y);
        QuickStartMaintainShop(sQuickStartShopRoomItemOffsets);
    } else if (QuickStart2DoorIsCurrentRoom()) {
        // Whichever real 2-door pool room the save's cave-connector draw
        // resolved to (see QuickStart2DoorRandomizeOnce/GetTarget) - its own
        // obstacle clear and content roll are both handled inside
        // QuickStart2DoorSetupRoomContent (it skips the clear entirely for
        // ROOM_CAVES_HEART_PIECE_HALLWAY, kept fully vanilla).
        QuickStart2DoorSetupRoomContent();
    } else if (QuickStartRiverBridgeIsCurrentRoom()) {
        // Whichever real 2-door pool room North Hyrule Field's own river
        // bridge draw resolved to (see QuickStartRandomizeRiverBridgeOnce/
        // QuickStartRiverBridgeGetTarget) - a separate draw from the cave
        // connector above, so this can never be the same physical room as
        // that branch.
        QuickStartSetupRiverBridgeRoomContent();
    } else if (QuickStartCaveIsCurrentRoom()) {
        // Whichever real 2-door pool room North Hyrule Field's own cave
        // mouth draw resolved to - a third, separate draw from the two
        // above, so this can never be the same physical room as either.
        QuickStartSetupCaveRoomContent();
    } else if (QuickStartFindContentSiteForCurrentRoom() >= 0) {
        // A real vanilla room, reached through its own real vanilla door,
        // that simply has a randomized event spawned inside it. No pool
        // draw, no synthetic entrance, no return-spot table - see
        // sQuickStartRoomContentSites.
        //
        // Every site keyed to this room runs, not just the first. Only the
        // Boomerang chamber has more than one (five, one per entrance), but
        // looping unconditionally means adding a second event to any room
        // is one table row and nothing else.
        s32 site;
        for (site = 0; site < QUICKSTART_CONTENT_SITE_COUNT; site++) {
            if (gRoomControls.area == sQuickStartRoomContentSites[site].area &&
                gRoomControls.room == sQuickStartRoomContentSites[site].room) {
                QuickStartSetupContentSite(site);
            }
        }
    } else {
        // Falls through to here for whichever pool room the Goron Cave
        // Stairs door (slot 3) currently resolves to - same generic
        // dispatch as Castle Garden's own two ladders (slots 0-1).
        s32 slotIndex = QuickStartFindSlotForCurrentRoom();
        if (slotIndex >= 0) {
            QuickStartSetupSlotRoomContent(slotIndex);
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

// ---------------------------------------------------------------------------
// Kinstone fusers
//
// The supply side of the economy is enemy drops (see itemUtils.c's QUICKSTART
// hook). This is the demand side: a placed sprite the player walks up to and
// presses L at, which opens the gate its fusion is wired to in vanilla.
//
// Vanilla decides what a fuser offers through GetFusionToOffer (common.c),
// which is driven entirely by gUnk_08001DCC - a ROM table keyed by a fuser id
// that GetFuserId derives from the entity's own kind/id/type triple. That is
// useless for arbitrary placement: it can only ever offer what the table says
// that particular NPC offers, and it has no row for an entity we invented.
// So we skip it. AddInteractableObject takes the kinstone id directly, and
// the fusion trigger in playerUtils.c (CheckPlayerInteractions) only asks
// whether the candidate's kinstoneId is in 1..100 - it never consults the
// fuser tables. Passing our own id there is all it takes.
//
// Everything downstream then works unmodified: the kinstone menu matches on
// shape (KinstoneMenu_Type3_Overlay1), writes the fused bit, fires the
// world-event cutscene that redraws the room, and NotifyFusersOnFusionDone
// retires this candidate so the fuser stops offering.
typedef struct {
    u8 area;
    u8 room;
    u8 kinstoneId;
} QuickStartFuser;

extern Script script_QuickStartFuser;

// Which gate each fuser opens. No coordinates: where it stands is a per-run
// roll over the region's own scatter list below.
static const QuickStartFuser sQuickStartFusers[] = {
    // Castle Garden - the two fountain staircases at the north end. Both
    // read as water until fused; the fusion lays the stairs over the pond.
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, KINSTONE_18 },
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, KINSTONE_35 },
    // Lon Lon Ranch - staircase, the wall-punching Goron over the cave
    // entrance, and a fusion treasure chest.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_1E },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_29 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_60 },
    // The Goron cave's three wall fusions. In vanilla these are offered by
    // the wall-punching Gorons standing inside the cave, but those are NPCs
    // and every content-site room sweeps its vanilla NPCs, so nothing in
    // this mode offered them and the cave's chain could not be advanced at
    // all. They live on the ranch's own fuser scatter instead, which puts
    // them within reach of the region the cave belongs to.
    //
    // Only these three exist as fusers. Vanilla's state machine also knows
    // KINSTONE_2A and 2B, and both were briefly listed here, but neither
    // opens a wall - in vanilla they only add another Goron to the line, and
    // the main chamber is a content site so those Gorons are swept anyway.
    // They gated nothing, they were indistinguishable in play from a fusion
    // that does nothing at all, and each one cost a scatter spot that the
    // fusions people actually need were competing against. Dropping them
    // takes Lon Lon Ranch from 8 of its 9 spots to 6, which is the point:
    // KINSTONE_29 alone decides whether the cave opens, so it should not be
    // one of eight things hiding in the same field.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_25 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_26 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, KINSTONE_2F },
    // North Hyrule Field - the four middle tree stumps are one fusion each,
    // and those four ladders are the only way into the Boomerang chamber's
    // four quadrants. Plus the fairy fountain tree and a chest.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_40 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_4D },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_59 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_5A },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_2D },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, KINSTONE_5F },
    // South Hyrule Field - heart piece tree, staircase, chest.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, KINSTONE_32 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, KINSTONE_58 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD, KINSTONE_53 },
    // Trilby Highlands - rupee cave, an obstacle patch, two chests.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, KINSTONE_3F },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, KINSTONE_22 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, KINSTONE_52 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, KINSTONE_5E },
    // --- The overworld expansion's regions --------------------------------
    // Discovered from the data, not guessed: every kinstone whose
    // gKinstoneWorldEvents row is a real world event (subtask 8) with its
    // gWorldEvents area/room inside Eastern Hills or Western Wood. Nine
    // fusions qualified; the two BEANSTALK-type ones (KINSTONE_2E in EH
    // Center, KINSTONE_24 in WW South) are deliberately left out - a
    // beanstalk's whole payoff is climbing OUT of the ring to the cloud
    // rooms, which containment cancels, and a fusion that grows a ladder
    // the player cannot use reads as a bug. The other seven all resolve
    // inside their own room (a golden enemy, fusion chests, a cave patch).
    //
    // Eastern Hills North: KINSTONE_16 (world event at (200,376)) and
    // KINSTONE_55 (the golden enemy at (120,440), OUGONTEKI_D).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH, KINSTONE_16 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH, KINSTONE_55 },
    // Western Wood Center: KINSTONE_3D (world event at (312,88)).
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER, KINSTONE_3D },
    // Western Wood North: five fusions, the densest room in the ring.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, KINSTONE_11 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, KINSTONE_21 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, KINSTONE_3A },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, KINSTONE_48 },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH, KINSTONE_4C },
};

// --- F10: the COMPASS's pause-map feeds (called from pauseMenuScreen6.c) --
//
// Is this kinstone one a fuser in this mode actually offers? The compass's
// marker loop is scoped to these, not to all 91 vanilla fusions - a marker
// for a fusion no fuser will ever offer would be a lie.
u32 QuickStartCompassKinstone(u32 kinstoneId) {
    s32 i;
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartFusers); i++) {
        if (sQuickStartFusers[i].kinstoneId == kinstoneId) {
            return TRUE;
        }
    }
    return FALSE;
}

// The Element-region marker: TRUE + world coordinates when the compass is
// owned and the run's element region is rolled. Deliberately the CENTER of
// the region's room, never the reward spot - the compass narrows the hunt
// to a region, it does not end it (the user's rule). The vanilla map screen
// only ever shows the page for the location the player is standing in, so
// in play this marker appears once the player is in the right region -
// confirmation on arrival; the pickup receipt (QuickStartNoteFoodItem) is
// what names the region from anywhere.
u32 QuickStartElementMapMarker(u16* x, u16* y) {
    const QuickStartRegion* region;
    RoomHeader* hdr;
    if (GetInventoryValue(ITEM_COMPASS) == 0 || !QsCheckFlag(GF_ELEMENT_REGION_ROLLED)) {
        return FALSE;
    }
    region = &sQuickStartRegionPool[QuickStartElementRegionIndex()];
    hdr = gAreaRoomHeaders[region->area] + region->room;
    *x = hdr->map_x + (hdr->pixel_width / 2);
    *y = hdr->map_y + (hdr->pixel_height / 2);
    return TRUE;
}

// Nine places per region a fuser can stand, and NOT hand-picked:
// tools/quickstart/find_fuser_spots.py boots this ROM, floods the walkable
// graph from the region entrance with every gate still shut, keeps only
// tiles with open ground on all eight sides, and then farthest-point samples
// them - seeding the region's arrival point, its reward drop and every one
// of its gates as already taken. The result covers the whole walkable map
// instead of clustering, and no two spots are within six tiles of each
// other. The invariant checker re-verifies every one.
//
// Nine rather than ten because Castle Garden and Trilby Highlands run out of
// room at that spacing, and a uniform row is worth more than one extra spot
// in three of the five regions.
#define QUICKSTART_FUSER_SPOTS_PER_REGION 9

typedef struct {
    u8 area;
    u8 room;
    s16 spots[QUICKSTART_FUSER_SPOTS_PER_REGION][2];
} QuickStartFuserSpots;

static const QuickStartFuserSpots sQuickStartFuserSpots[] = {
    { AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      { { 776, 328 }, { 248, 280 }, { 328, 488 }, { 424, 104 }, { 584, 104 },
        { 664, 488 }, { 488, 376 }, { 408, 216 }, { 600, 216 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      { { 56, 376 }, { 680, 248 }, { 424, 152 }, { 648, 760 }, { 696, 440 },
        { 88, 552 }, { 56, 200 }, { 120, 696 }, { 648, 616 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      { { 24, 600 }, { 312, 744 }, { 552, 744 }, { 792, 744 }, { 504, 104 },
        { 984, 632 }, { 472, 600 }, { 904, 216 }, { 264, 616 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      { { 56, 632 }, { 840, 72 }, { 312, 632 }, { 488, 56 }, { 56, 88 },
        { 312, 88 }, { 424, 456 }, { 664, 88 }, { 472, 632 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      { { 392, 888 }, { 24, 408 }, { 344, 744 }, { 248, 136 }, { 280, 888 },
        { 40, 584 }, { 136, 584 }, { 360, 152 }, { 456, 552 } } },
    // The three expansion rooms that host fusers, generated the same way
    // (flood + farthest-point sample) with the region's enemy-offset grid,
    // its gates, its entrance and its reward spot all seeded as taken, so a
    // fuser can never stand on a wave spawn point or the reward drop.
    // Western Wood Center is a 30x10 corridor, so its nine spots sit closer
    // together than the six-tile spacing the big rooms keep - it hosts one
    // fuser, so only one of them is ever occupied.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH,
      { { 136, 120 }, { 136, 296 }, { 168, 264 }, { 168, 328 }, { 296, 248 },
        { 328, 104 }, { 328, 376 }, { 360, 424 }, { 376, 232 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER,
      { { 280, 56 }, { 280, 104 }, { 296, 72 }, { 328, 120 }, { 344, 104 },
        { 392, 104 }, { 408, 40 }, { 408, 88 }, { 408, 120 } } },
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH,
      { { 248, 360 }, { 264, 504 }, { 280, 408 }, { 376, 72 }, { 392, 328 },
        { 56, 248 }, { 296, 536 }, { 344, 136 }, { 376, 168 } } },
};

// One 4-bit roll for the whole run, rolled lazily the first time a fuser
// needs a position. Eighteen fusers would want eighteen stored positions;
// this stores one number and derives all of them, which is the only shape
// that fits - there are five free flag offsets left below 707.
static u32 QuickStartFuserScatter(void) {
    s32 b;
    u32 value = 0;
    if (!QsCheckFlag(GF_FUSER_SCATTER_ROLLED)) {
        u32 roll = (u32)((s32)Random() & 0xf);
        for (b = 0; b < 4; b++) {
            if (roll & (1 << b)) {
                QsSetFlag(GF_FUSER_SCATTER_BIT(b));
            }
        }
        QsSetFlag(GF_FUSER_SCATTER_ROLLED);
    }
    for (b = 0; b < 4; b++) {
        if (QsCheckFlag(GF_FUSER_SCATTER_BIT(b))) {
            value |= 1 << b;
        }
    }
    return value;
}

// Step 4 through a list of 9 is injective for the first nine callers (4 and 9
// are coprime), so the fusers in a region can never be handed the same spot -
// North Hyrule Field's six included. The region index is folded in as well so
// the five regions do not all rotate in lockstep between runs.
static bool32 QuickStartFuserSpot(const QuickStartFuser* fuser, s32 indexInRegion, s16* x, s16* y) {
    s32 r;
    for (r = 0; r < (s32)ARRAY_COUNT(sQuickStartFuserSpots); r++) {
        if (sQuickStartFuserSpots[r].area == fuser->area && sQuickStartFuserSpots[r].room == fuser->room) {
            s32 slot = (indexInRegion * 4 + (s32)QuickStartFuserScatter() + r * 2) %
                       QUICKSTART_FUSER_SPOTS_PER_REGION;
            *x = sQuickStartFuserSpots[r].spots[slot][0];
            *y = sQuickStartFuserSpots[r].spots[slot][1];
            return TRUE;
        }
    }
    return FALSE;
}

// Reads/writes the 7-bit "already reloaded for this fusion" id. Zero means
// no fusion has needed one yet, which is safe: KINSTONE_NONE is 0 and no
// real fusion uses it.
static u32 QuickStartFusionReloadedId(void) {
    s32 b;
    u32 id = 0;
    for (b = 0; b < 7; b++) {
        if (QsCheckFlag(GF_FUSION_RELOADED_ID_BIT(b))) {
            id |= 1 << b;
        }
    }
    return id;
}

static void QuickStartSetFusionReloadedId(u32 id) {
    s32 b;
    for (b = 0; b < 7; b++) {
        if (id & (1 << b)) {
            QsSetFlag(GF_FUSION_RELOADED_ID_BIT(b));
        } else {
            QsClearFlag(GF_FUSION_RELOADED_ID_BIT(b));
        }
    }
}

// Walk back into the room we are already standing in, so the map is rebuilt
// with the fusion applied. gFuseInfo.kinstoneId survives the cutscene (only
// the next InitializeFuseInfo clears it), which is what identifies the
// fusion that just completed; the stored id stops this from firing again on
// the reload it causes, and again on every later visit.
static void QuickStartReloadRoomAfterFusion(void) {
    s32 i;
    u32 fused = gFuseInfo.kinstoneId;
    if (gRoomTransition.transitioningOut || fused == KINSTONE_NONE) {
        return;
    }
    // Wait for the fusion's own cutscene to finish handing control back.
    // Firing a room transition while the world-event subtask is still up
    // interleaves two screen changes.
    if (gPlayerState.controlMode != CONTROL_1 || (gMessage.state & MESSAGE_ACTIVE) != 0) {
        return;
    }
    if (QuickStartFusionReloadedId() == fused || !CheckKinstoneFused(fused)) {
        return;
    }
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartFusers); i++) {
        const QuickStartFuser* fuser = &sQuickStartFusers[i];
        if (fuser->kinstoneId != fused || gRoomControls.area != fuser->area ||
            gRoomControls.room != fuser->room) {
            continue;
        }
        QuickStartSetFusionReloadedId(fused);
        gRoomTransition.player_status.area_next = gRoomControls.area;
        gRoomTransition.player_status.room_next = gRoomControls.room;
        gRoomTransition.player_status.spawn_type = PL_SPAWN_DEFAULT;
        gRoomTransition.player_status.start_pos_x = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
        gRoomTransition.player_status.start_pos_y = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
        gRoomTransition.player_status.layer = 1;
        gRoomTransition.type = TRANSITION_FADE_BLACK_SLOW;
        gRoomTransition.transitioningOut = 1;
        return;
    }
}

// Bit 0 Nayru, bit 1 Farore, bit 2 Din - read by CalculateDamage
// (collision.c) instead of the single gSave.stats.charm byte, so more than
// one charm can be in effect at a time.
u8 QuickStartCharmMask(void) {
    s32 n;
    u8 mask = 0;
    for (n = 0; n < 3; n++) {
        if (CheckLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(n))) {
            mask |= 1 << n;
        }
    }
    return mask;
}

// Called from playerItemBottle.c the moment a charm is drunk. Vanilla sets
// gSave.stats.charm and a 3600-frame timer there and lets it run out; this
// records the charm as owned for the rest of the run on top of that.
void QuickStartNoteCharm(u32 bottleContent) {
    // The trophy case's three bottle-charm rows can only be lit from here.
    // A charm arrives as a FILLED BOTTLE, so the id GiveItem sees is a
    // bottle, not the charm inside it - the catalog hook on that path
    // would light "Empty Bottle" and never Nayru, Farore or Din.
    QuickStartMarkCatalogItem(bottleContent);
    switch (bottleContent) {
        case BOTTLE_CHARM_NAYRU:
            SetLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(0));
            break;
        case BOTTLE_CHARM_FARORE:
            SetLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(1));
            break;
        case BOTTLE_CHARM_DIN:
            SetLocalFlagByBank(FLAG_BANK_11, QUICKSTART_CHARM_BIT(2));
            break;
    }
}

// --- Food charms and curses (F4) ------------------------------------------

// The six effects the player currently carries, as
// QUICKSTART_FOOD_* bits. Read by QuickStartApplyFoodEffects each frame
// and by UpdatePlayerMovement (playerUtils.c) for the walk-speed charm.
u32 QuickStartFoodMask(void) {
    s32 n;
    u32 mask = 0;
    for (n = 0; n < QUICKSTART_FOOD_COUNT; n++) {
        if (QsCheckFlag(GF_FOOD_BIT(n))) {
            mask |= 1 << n;
        }
    }
    return mask;
}

// Called from GiveItem (itemUtils.c) for EVERY item grant, so it covers
// ground pickups, chests and scripted gives alike; a no-op for the other
// ~250 item ids. First taste of a given food sets its run-long bit and
// announces the effect through Ezlo - the item-get text alone just names
// a pastry, which tells the player nothing about what it did to them.
// ===================== The trophy case catalog =========================
//
// The player's record of everything this mode can hand them - the reward
// tiers in all six categories, the ordinary things that fall out of pots
// and enemies, and the Earth Element - browsed at the trophy case in the
// hub. An entry stays blank until the player has actually held that item
// at least once; after that its name and a description of what it DOES
// are readable forever.
//
// WHERE THE LEDGER LIVES: gSave.figurines, vanilla's 36-byte (288-bit)
// figurine bitset. This mode has no figurines - no Carlov, no lotto
// machine, `figurineCount` never leaves 0 - so the array is dead storage
// that is nevertheless saved, loaded and carried across runs with the
// rest of the file, which is exactly the lifetime a cross-run discovery
// ledger needs. It also means the vanilla figurine MENU's own ownership
// test (ReadBit(gSave.figurines, idx), figurineMenu.c) keeps working
// untouched: only the entry COUNT, the two text lookups and the picture
// needed re-pointing.
//
// Indices are 1-based to match that menu, so catalog row i is menu entry
// i + 1 and ledger bit i + 1.
//
// The categories are the tier table's own (QS_CAT_*), in the order the
// list reads top to bottom. Rows are grouped by category on purpose: the
// menu is a flat scrolling list with no headings of its own, so grouping
// IS the structure the player sees.
typedef struct {
    u16 item;
    u8 category;
} QuickStartCatalogEntry;

// ITEM_BOTTLE1 appears once here even though the tier table lists it
// twice (as a REWARD and as a WEAPON draw) - the catalog is a record of
// THINGS, not of draw rows, so an item that can arrive two ways is still
// one entry. Everything else is one row per tier-table row, plus the
// pickups and the Element, which are not tier draws at all.
static const QuickStartCatalogEntry sQuickStartCatalog[] = {
    // --- The goal ---------------------------------------------------
    { ITEM_EARTH_ELEMENT, QS_CAT_KEY },
    // --- Ordinary pickups: pots, grass, enemy drops ------------------
    { ITEM_HEART, QS_CAT_REWARD },
    { ITEM_RUPEE1, QS_CAT_REWARD },
    { ITEM_RUPEE5, QS_CAT_REWARD },
    { ITEM_RUPEE20, QS_CAT_REWARD },
    { ITEM_BOMBS5, QS_CAT_REWARD },
    { ITEM_ARROWS5, QS_CAT_REWARD },
    { ITEM_KINSTONE, QS_CAT_REWARD },
    { ITEM_FAIRY, QS_CAT_REWARD },
    // --- Rewards ----------------------------------------------------
    { ITEM_RUPEE50, QS_CAT_REWARD },
    { ITEM_RUPEE100, QS_CAT_REWARD },
    { ITEM_RUPEE200, QS_CAT_REWARD },
    { ITEM_HEART_PIECE, QS_CAT_REWARD },
    { ITEM_HEART_CONTAINER, QS_CAT_REWARD },
    { ITEM_BOTTLE1, QS_CAT_REWARD },
    { ITEM_BOTTLE_BLUE_POTION, QS_CAT_REWARD },
    { ITEM_BOTTLE_RED_POTION, QS_CAT_REWARD },
    { ITEM_BOTTLE_FAIRY, QS_CAT_REWARD },
    // --- Weapons and tools ------------------------------------------
    { ITEM_SMITH_SWORD, QS_CAT_WEAPON },
    { ITEM_RED_SWORD, QS_CAT_WEAPON },
    { ITEM_SHIELD, QS_CAT_WEAPON },
    { ITEM_MIRROR_SHIELD, QS_CAT_WEAPON },
    { ITEM_BOW, QS_CAT_WEAPON },
    { ITEM_LARGE_QUIVER, QS_CAT_WEAPON },
    { ITEM_BOMBS, QS_CAT_WEAPON },
    { ITEM_REMOTE_BOMBS, QS_CAT_WEAPON },
    { ITEM_BOMBBAG, QS_CAT_WEAPON },
    { ITEM_BOOMERANG, QS_CAT_WEAPON },
    { ITEM_MAGIC_BOOMERANG, QS_CAT_WEAPON },
    { ITEM_GUST_JAR, QS_CAT_WEAPON },
    { ITEM_FIRE_ROD, QS_CAT_WEAPON },
    { ITEM_MAP, QS_CAT_WEAPON },
    { ITEM_COMPASS, QS_CAT_WEAPON },
    // --- Key items --------------------------------------------------
    { ITEM_PEGASUS_BOOTS, QS_CAT_KEY },
    { ITEM_ROCS_CAPE, QS_CAT_KEY },
    { ITEM_MOLE_MITTS, QS_CAT_KEY },
    { ITEM_FLIPPERS, QS_CAT_KEY },
    { ITEM_LANTERN_OFF, QS_CAT_KEY },
    { ITEM_OCARINA, QS_CAT_KEY },
    { ITEM_PACCI_CANE, QS_CAT_KEY },
    { ITEM_GRIP_RING, QS_CAT_KEY },
    { ITEM_POWER_BRACELETS, QS_CAT_KEY },
    // --- Sword skills -----------------------------------------------
    { ITEM_SKILL_SPIN_ATTACK, QS_CAT_SKILL },
    { ITEM_SKILL_GREAT_SPIN, QS_CAT_SKILL },
    { ITEM_SKILL_ROCK_BREAKER, QS_CAT_SKILL },
    { ITEM_SKILL_ROLL_ATTACK, QS_CAT_SKILL },
    { ITEM_SKILL_DASH_ATTACK, QS_CAT_SKILL },
    { ITEM_SKILL_DOWN_THRUST, QS_CAT_SKILL },
    { ITEM_SKILL_SWORD_BEAM, QS_CAT_SKILL },
    { ITEM_SKILL_PERIL_BEAM, QS_CAT_SKILL },
    // --- Stat upgrades ----------------------------------------------
    { ITEM_ARROW_BUTTERFLY, QS_CAT_STAT },
    { ITEM_DIG_BUTTERFLY, QS_CAT_STAT },
    { ITEM_SWIM_BUTTERFLY, QS_CAT_STAT },
    { BOTTLE_CHARM_NAYRU, QS_CAT_STAT },
    { BOTTLE_CHARM_FARORE, QS_CAT_STAT },
    { BOTTLE_CHARM_DIN, QS_CAT_STAT },
    // --- Charms and curses ------------------------------------------
    { ITEM_BRIOCHE, QS_CAT_CHARM },
    { ITEM_CROISSANT, QS_CAT_CHARM },
    { ITEM_CAKE, QS_CAT_CHARM },
    { ITEM_QST_BOOK1, QS_CAT_CHARM },
    { ITEM_QST_BOOK2, QS_CAT_CHARM },
    { ITEM_QST_BOOK3, QS_CAT_CHARM },
    { ITEM_QST_TINGLE_TROPHY, QS_CAT_CHARM },
    { ITEM_JABBERNUT, QS_CAT_CHARM },
    { ITEM_QST_CARLOV_MEDAL, QS_CAT_CHARM },
    { ITEM_QST_BROKEN_SWORD, QS_CAT_CHARM },
    { ITEM_SHELLS, QS_CAT_CHARM },
    { ITEM_PIE, QS_CAT_CHARM },
    { ITEM_QST_DOGFOOD, QS_CAT_CHARM },
    { ITEM_QST_MUSHROOM, QS_CAT_CHARM },
};

#define QUICKSTART_CATALOG_COUNT ((s32)ARRAY_COUNT(sQuickStartCatalog))

// The two string blocks. Names run from QUICKSTART_CATALOG_NAME_BASE, one
// per row in table order; descriptions from QUICKSTART_CATALOG_DESC_BASE
// the same way; the single "not yet found" placeholder sits directly
// above the names. gCustomStrings is indexed by a u8, so 256 is the hard
// ceiling for the whole mode - this block is by far its largest tenant
// and the count check below is what keeps it honest.
#define QUICKSTART_CATALOG_LOCKED_STRING 60
#define QUICKSTART_CATALOG_NAME_BASE 61
#define QUICKSTART_CATALOG_DESC_BASE (QUICKSTART_CATALOG_NAME_BASE + QUICKSTART_CATALOG_COUNT)
// Build breaks if the two blocks run off the end of a u8 text index.
typedef char QuickStartCatalogStringsFit[(QUICKSTART_CATALOG_DESC_BASE + QUICKSTART_CATALOG_COUNT <= 256) ? 1 : -1];
// ...and if the ledger outgrows the bitset it borrows.
typedef char QuickStartCatalogLedgerFits[(QUICKSTART_CATALOG_COUNT < 288) ? 1 : -1];

s32 QuickStartCatalogCount(void) {
    return QUICKSTART_CATALOG_COUNT;
}

// index is 1-based (menu convention). Out of range answers "locked",
// which is the safe direction: a bad index shows nothing rather than
// reading a neighbouring string.
bool32 QuickStartCatalogOwned(s32 index) {
    if (index < 1 || index > QUICKSTART_CATALOG_COUNT) {
        return FALSE;
    }
    return ReadBit(gSave.figurines, (u32)index) != 0;
}

u32 QuickStartCatalogNameText(s32 index) {
    if (index < 1 || index > QUICKSTART_CATALOG_COUNT || !QuickStartCatalogOwned(index)) {
        return TEXT_INDEX(TEXT_CUSTOM, QUICKSTART_CATALOG_LOCKED_STRING);
    }
    return TEXT_INDEX(TEXT_CUSTOM, (QUICKSTART_CATALOG_NAME_BASE + index - 1));
}

u32 QuickStartCatalogDescText(s32 index) {
    return TEXT_INDEX(TEXT_CUSTOM, (QUICKSTART_CATALOG_DESC_BASE + index - 1));
}

// The item id behind an entry, for the menu's picture pane.
u32 QuickStartCatalogItem(s32 index) {
    if (index < 1 || index > QUICKSTART_CATALOG_COUNT) {
        return ITEM_NONE;
    }
    return sQuickStartCatalog[index - 1].item;
}

// Mark an item found. Called from the every-grant chokepoint below, so
// ground pickups, chest payouts, hub selections and scripted gives all
// land here without each needing its own hook.
//
// The bottle charms are the one case the item id cannot answer on its
// own: Nayru/Farore/Din arrive as a filled BOTTLE, so the id seen here is
// a bottle id and the charm rows would never light. They are marked
// separately by the charm code itself (QuickStartMarkCatalogItem is
// exported for exactly that).
void QuickStartMarkCatalogItem(u32 item) {
    s32 i;
    for (i = 0; i < QUICKSTART_CATALOG_COUNT; i++) {
        if (sQuickStartCatalog[i].item == item) {
            WriteBit(gSave.figurines, (u32)(i + 1));
            return;
        }
    }
}

void QuickStartNoteFoodItem(u32 item) {
    s32 n;
    QuickStartMarkCatalogItem(item);
    // F10's two tools ride this same GiveItem chokepoint for their pickup
    // receipts (this runs BEFORE GiveItem sets the inventory bit, so a zero
    // read means "first grant" - the once-latch for free). The compass
    // receipt names the Element's REGION, never the spot: strings 52-58 in
    // ring-enum order.
    if (item == ITEM_MAP || item == ITEM_COMPASS) {
        if (GetInventoryValue(item) == 0) {
            if (item == ITEM_MAP) {
                CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 51), 0);
            } else {
                CreateEzloHint(
                    TEXT_INDEX(TEXT_CUSTOM,
                               (52 + QuickStartRingRegionOfPoolIndex(QuickStartElementRegionIndex()))),
                    0);
            }
        }
        return;
    }
    switch (item) {
        case ITEM_BRIOCHE:
            n = 0;
            break;
        case ITEM_CROISSANT:
            n = 1;
            break;
        case ITEM_CAKE:
            n = 2;
            break;
        case ITEM_PIE:
            n = 3;
            break;
        case ITEM_QST_DOGFOOD:
            n = 4;
            break;
        case ITEM_QST_MUSHROOM:
            n = 5;
            break;
        case ITEM_QST_BOOK1:
            n = 6;
            break;
        case ITEM_QST_BOOK2:
            n = 7;
            break;
        case ITEM_QST_BOOK3:
            n = 8;
            break;
        case ITEM_QST_TINGLE_TROPHY:
            n = 9;
            break;
        case ITEM_JABBERNUT:
            n = 10;
            break;
        case ITEM_QST_CARLOV_MEDAL:
            n = 11;
            break;
        case ITEM_QST_BROKEN_SWORD:
            n = 12;
            break;
        // The Mysterious Shells, repurposed as the run's luck charm - the
        // last item from the original F4 wish list (rare-reward-chance-up).
        // The shells are a vanilla collectible this mode never used for
        // anything, and "a pocketful of lucky shells" is about as close to
        // self-explaining as this roster gets.
        case ITEM_SHELLS:
            n = 13;
            break;
        default:
            return;
    }
    if (!QsCheckFlag(GF_FOOD_BIT(n))) {
        QsSetFlag(GF_FOOD_BIT(n));
        // The first thirteen announce through consecutive strings 33..45.
        // The fourteenth cannot: 46 is already the inn's first bed offer,
        // so it has its own slot rather than shifting five other blocks.
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, ((n == 13) ? 59 : (33 + n))), 0);
    }
}

// Which enemy kinds actually shoot projectiles, for the Mushroom curse.
// Curated rather than inferred: the fire-rate trick below leans on each
// of these AIs pacing its shots (and everything else) off super->timer,
// which was checked per id, not assumed game-wide.
static bool32 QuickStartEnemyShootsProjectiles(u32 id) {
    switch (id) {
        case OCTOROK:
        case OCTOROK_GOLDEN:
        case BUSINESS_SCRUB:
        case WIZZROBE_WIND:
        case WIZZROBE_FIRE:
        case WIZZROBE_ICE:
        case STALFOS:
            return TRUE;
    }
    return FALSE;
}

// The per-frame half of the food effects. Knockback and speed cannot be
// patched at their dozens of assignment sites (collision.c writes
// knockback in ~15 handlers; every enemy AI rewrites its own speed per
// state), so this adjusts the FIELDS after the fact instead - they are
// consumed over many frames, and the low bit is used as an "already
// scaled" marker (all vanilla values are even) so a value is never
// scaled twice, while an AI overwriting its speed simply gets re-scaled
// on the next pass. CHUCHU_BOSS pieces are exempt from every enemy-side
// effect: their fields double as scripted stage machinery.
static void QuickStartApplyFoodEffects(void) {
    u8 mask = QuickStartFoodMask();
    u32 v;
    s32 i;
    if (mask == 0) {
        return;
    }
    // Humble Pie first, the Cake last: holding both resolves to immune.
    if ((mask & QUICKSTART_FOOD_CURSE_KNOCKBACK) && gPlayerEntity.base.knockbackDuration != 0 &&
        gPlayerEntity.base.knockbackSpeed != 0 && (gPlayerEntity.base.knockbackSpeed & 1) == 0) {
        v = gPlayerEntity.base.knockbackSpeed * 2;
        if (v > 1536) {
            v = 1536;
        }
        gPlayerEntity.base.knockbackSpeed = v | 1;
    }
    if (mask & QUICKSTART_FOOD_STEADFAST) {
        gPlayerEntity.base.knockbackDuration = 0;
        gPlayerEntity.base.knockbackSpeed = 0;
    }
    if (mask & (QUICKSTART_FOOD_SWORD_KNOCKBACK | QUICKSTART_FOOD_CURSE_ENEMY_SPEED | QUICKSTART_FOOD_CURSE_FIRE_RATE)) {
        for (i = 0; i < MAX_ENTITIES; i++) {
            Entity* ent = &gEntities[i].base;
            if (ent->kind != ENEMY || ent->id == CHUCHU_BOSS) {
                continue;
            }
            if ((mask & QUICKSTART_FOOD_SWORD_KNOCKBACK) && ent->knockbackDuration != 0 && ent->knockbackSpeed != 0 &&
                (ent->knockbackSpeed & 1) == 0) {
                v = ent->knockbackSpeed * 2;
                if (v > 1536) {
                    v = 1536;
                }
                ent->knockbackSpeed = v | 1;
            }
            if ((mask & QUICKSTART_FOOD_CURSE_ENEMY_SPEED) && ent->speed > 0 && (ent->speed & 1) == 0) {
                v = (u32)ent->speed + ((u32)ent->speed >> 1);
                if (v > 0x400) {
                    v = 0x400;
                }
                ent->speed = (s16)(v | 1);
            }
            // Every other frame, tick shooter timers one extra step: their
            // whole cadence - aim, fire, recover - runs half again as
            // fast, which reads as trigger-happy. Never past 1, so an
            // AI's own "did my timer just hit zero" edge is never eaten.
            if ((mask & QUICKSTART_FOOD_CURSE_FIRE_RATE) && (gRoomTransition.frameCount & 1) != 0 && ent->timer > 1 &&
                QuickStartEnemyShootsProjectiles(ent->id)) {
                ent->timer--;
            }
        }
    }
}

// Called from the merchant script right after the vanilla DisablePauseMenu
// helpers, which blank the whole HUD (hideFlags = HUD_HIDE_ALL). Deciding
// whether to buy something is exactly a "can I afford this" question, so the
// one number that must not vanish for the length of that conversation is the
// rupee count. Everything else stays hidden.
void QuickStartShopShowRupees(void) {
    gHUD.hideFlags &= ~HUD_HIDE_RUPEES;
}

static void QuickStartMakeNpcFuser(Entity* npc, u32 kinstoneId) {
    s32 index;

    npc->action = 0;
    npc->animationState = IdleSouth;
    StartCutscene(npc, &script_QuickStartFuser);
    // INTERACTION_FUSE as the candidate type, not INTERACTION_TALK: the A
    // button's switch in CheckPlayerInteractions has no case for it, so it
    // falls to the default and does nothing at all. That matters - the TALK
    // case parks the player in PL_STATE_TALKEZLO waiting for a script that
    // would never answer, since script_QuickStartFuser only ever handles
    // INTERACTION_FUSE. L still works, because the fusion branch runs
    // before that switch and keys off the kinstone id alone.
    index = AddInteractableObject(npc, INTERACTION_FUSE, kinstoneId);
    if (index >= 0) {
        // Same stale-candidate-slot reasoning as QuickStartMakeNpcTalkable
        // above, and the same oversized hitbox: an 8x8 interact window is
        // no way to find a fusion stone in an open field.
        gPossibleInteraction.candidates[index].interactDirections = 0;
        gPossibleInteraction.candidates[index].customHitbox = &sQuickStartNpcInteractHitbox;
    }
}

// Called every frame from QuickStartRegionMonitor. Cheap: the area/room test
// rejects all but this region's own rows immediately, and CheckKinstoneFused
// retires each one for good the moment its gate opens.
// ==================== Tingle's kinstone fusion =========================
//
// "Tingle should be there and the player can fuse Kinstones with them. If
// they fuse correctly, they should receive a heart container" (the user,
// Aug 2026). Built entirely on the fuser machinery above rather than as a
// new system: a Tingle is a fuser with a different sprite and our own
// payout, so it scatters over the same per-region spot list, uses the same
// script and the same oversized interact hitbox, and retires the same way
// once its gate is fused.
//
// WHICH FUSION. KINSTONE_2A, and the choice is the whole design. Its
// vanilla world event adds another Goron to the line in Goron Cave's main
// chamber - a room that is a content site here, so its vanilla occupants
// are swept every frame. In other words the fusion's own payload is inert
// in this mode, which is exactly what a fusion wants to be when the reward
// is ours to give. This mode listed 2A as an ordinary fuser once before
// and dropped it for being pointless (see the note in sQuickStartFusers);
// pointless is the property being reused here.
//
// The sprite is the real thing: TINGLE_SIBLINGS, whose definition carries
// four forms (the four siblings) each with a genuine entity sprite, so it
// renders wherever it stands. StartCutscene sets ENT_SCRIPTED, which sends
// the NPC's own update down its scripted branch - the same path the ZELDA
// fusers take - so none of its vanilla talking logic gets a say.
typedef struct {
    u8 area;
    u8 room;
    u8 kinstoneId;
    u8 form; // 0-3, which sibling
} QuickStartTingle;

static const QuickStartTingle sQuickStartTingles[] = {
    // Trilby Highlands, which already has a scatter spot list and is where
    // the Mole Mitts cave and its ledge live - so the region that gained a
    // dig-cave event also gained the reason to walk it.
    { AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, KINSTONE_2A, 0 },
};

#define QUICKSTART_TINGLE_COUNT ((s32)ARRAY_COUNT(sQuickStartTingles))
// One paid-out bit each, and GF_TINGLE_PAID_BIT only has four.
typedef char QuickStartTingleBitsFit[(QUICKSTART_TINGLE_COUNT <= 4) ? 1 : -1];

// The payout. Polled rather than hooked because a fusion completes inside
// the kinstone menu's own cutscene, several layers away from anything this
// file runs - and CheckKinstoneFused is the same test the fuser spawner
// already uses to retire a gate, so the two can never disagree about
// whether the fusion happened.
static void QuickStartTinglePayout(void) {
    s32 i;
    if (!QuickStartRoomSettled()) {
        return;
    }
    for (i = 0; i < QUICKSTART_TINGLE_COUNT; i++) {
        const QuickStartTingle* t = &sQuickStartTingles[i];
        s16 lx, ly, spotX, spotY;
        if (gRoomControls.area != t->area || gRoomControls.room != t->room) {
            continue;
        }
        if (!CheckKinstoneFused(t->kinstoneId) || QsCheckFlag(GF_TINGLE_PAID_BIT(i))) {
            continue;
        }
        // At the player's feet: the fusion cutscene leaves them standing
        // where they fused, and Tingle himself is already retired by then
        // (the spawner skips a fused row), so there is no NPC left to drop
        // it beside. Snapped to open ground like every other reward.
        lx = gPlayerEntity.base.x.HALF.HI - gRoomControls.origin_x;
        ly = gPlayerEntity.base.y.HALF.HI - gRoomControls.origin_y;
        if (!QuickStartTileIsOpen(lx >> 4, ly >> 4) && QuickStartFindOpenTileNear(lx, ly, 1, &spotX, &spotY)) {
            lx = spotX;
            ly = spotY;
        }
        if (QuickStartSpawnRewardEntity(ITEM_HEART_CONTAINER, lx, ly) == NULL) {
            // No entity slot this frame; leave the bit clear and try again
            // next frame rather than eating the prize.
            continue;
        }
        QsSetFlag(GF_TINGLE_PAID_BIT(i));
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 201), 0);
    }
}

static void QuickStartSpawnRegionFusers(void) {
    s32 i, indexInRegion = 0;
    // Settled-room guard (QuickStartRoomSettled): this runs OUTSIDE the
    // region dispatch, and its "already spawned" identity is an exact
    // origin-relative coordinate match - computed against a mid-transition
    // origin it would both spawn the sprite at a wrong world position and
    // then fail to recognize it after the room settles, leaving an orphan
    // and spawning a duplicate.
    if (!QuickStartRoomSettled()) {
        return;
    }
    for (i = 0; i < (s32)ARRAY_COUNT(sQuickStartFusers); i++) {
        const QuickStartFuser* fuser = &sQuickStartFusers[i];
        s32 worldX, worldY, e;
        s16 localX, localY;
        bool32 alreadyThere;
        if (gRoomControls.area != fuser->area || gRoomControls.room != fuser->room) {
            continue;
        }
        // Counted over the rows for THIS room only, and counted before the
        // fused check - so opening one gate does not shuffle the fusers that
        // are still standing.
        indexInRegion++;
        if (CheckKinstoneFused(fuser->kinstoneId)) {
            continue;
        }
        if (!QuickStartFuserSpot(fuser, indexInRegion - 1, &localX, &localY)) {
            continue;
        }
        worldX = gRoomControls.origin_x + localX;
        worldY = gRoomControls.origin_y + localY;
        // Position is the identity check. No two spots in a region are within
        // six tiles of each other (find_fuser_spots.py enforces that), so an
        // exact coordinate match can only ever be this row's own sprite - and
        // it survives the entity list being rebuilt, which a "did I spawn
        // yet" flag would not.
        alreadyThere = FALSE;
        for (e = 0; e < MAX_ENTITIES; e++) {
            if (gEntities[e].base.kind == NPC && gEntities[e].base.id == ZELDA &&
                gEntities[e].base.x.HALF.HI == worldX && gEntities[e].base.y.HALF.HI == worldY) {
                alreadyThere = TRUE;
                break;
            }
        }
        if (alreadyThere) {
            continue;
        }
        if (!QuickStartGfxBudgetForSpawn()) {
            return;
        }
        {
            // ZELDA for the same reason the merchant and the ? room signs
            // use her: her entity kind is the one proven to work with the
            // generic StartCutscene script attachment. Every fuser in a
            // room shares the one sheet, so the whole set costs a single
            // gfx slot. Cosmetic placeholder, per the "reuse a resident
            // sprite" call - a real fusion-stone sprite is the follow-up.
            Entity* npc = CreateNPC(ZELDA, 0, 0);
            if (npc == NULL) {
                return;
            }
            npc->x.HALF.HI = worldX;
            npc->y.HALF.HI = worldY;
            npc->collisionLayer = 1;
            UpdateSpriteForCollisionLayer(npc);
            npc->direction = IdleSouth;
            QuickStartMakeNpcFuser(npc, fuser->kinstoneId);
        }
    }
    // Tingle rides the same loop's tail: same scatter list, same identity
    // check, same retirement. The only differences are the sprite and that
    // his slot index is pushed past the region's own fusers (indexInRegion
    // keeps counting) so he never lands on top of one.
    for (i = 0; i < QUICKSTART_TINGLE_COUNT; i++) {
        const QuickStartTingle* tingle = &sQuickStartTingles[i];
        QuickStartFuser asFuser;
        s32 worldX, worldY, e;
        s16 localX, localY;
        bool32 alreadyThere = FALSE;
        if (gRoomControls.area != tingle->area || gRoomControls.room != tingle->room) {
            continue;
        }
        indexInRegion++;
        if (CheckKinstoneFused(tingle->kinstoneId)) {
            continue;
        }
        asFuser.area = tingle->area;
        asFuser.room = tingle->room;
        asFuser.kinstoneId = tingle->kinstoneId;
        if (!QuickStartFuserSpot(&asFuser, indexInRegion - 1, &localX, &localY)) {
            continue;
        }
        worldX = gRoomControls.origin_x + localX;
        worldY = gRoomControls.origin_y + localY;
        for (e = 0; e < MAX_ENTITIES; e++) {
            if (gEntities[e].base.kind == NPC && gEntities[e].base.id == TINGLE_SIBLINGS &&
                gEntities[e].base.x.HALF.HI == worldX && gEntities[e].base.y.HALF.HI == worldY) {
                alreadyThere = TRUE;
                break;
            }
        }
        if (alreadyThere || !QuickStartGfxBudgetForSpawn()) {
            continue;
        }
        {
            Entity* npc = CreateNPC(TINGLE_SIBLINGS, tingle->form, 0);
            if (npc == NULL) {
                continue;
            }
            npc->x.HALF.HI = worldX;
            npc->y.HALF.HI = worldY;
            npc->collisionLayer = 1;
            UpdateSpriteForCollisionLayer(npc);
            npc->direction = IdleSouth;
            QuickStartMakeNpcFuser(npc, tingle->kinstoneId);
        }
    }
}

// Every choice phase reuses this same 3-slot item row. Columns 5, 7 and 9 of
// the hub's third-floor hall, which is 11 tiles wide (columns 2-12) - one
// clear tile between each, tightened from two per the user ("one tile closer
// together ... it will look visually better"), still wide enough that walking
// up to one cannot brush its neighbour.
static const s16 sQuickStartItemOffsets[QUICKSTART_ITEM_CHOICES] = { 88, 120, 152 };
// The hall row the items sit on - one tile further from the player's arrival
// spot than it used to be, also per the user. See the spawn comment in
// GameTask_Transition for the full vertical layout.
#define QUICKSTART_ITEM_ROW_Y 72

// Called exactly once per phase (QuickStartSpawnStarterChoiceOnce's own NPC
// scan guards the phase-0 call, and the phase==1/phase==3 reload handlers
// below each fire their own call exactly once transitioning into that
// phase), so shuffling fresh on every call - rather than needing any
// persisted state - still means each of the 3 rounds' left-to-right order
// is independently randomized once per game, instead of always the same
// bombs/bow/boomerang (etc.) order every time. Same Fisher-Yates shape as
// QuickStartSpawnEnemyGroup's own indices shuffle elsewhere in this file.
static void QuickStartSpawnItems(const QuickStartItemChoice* choices) {
    s32 i, r, tmp;
    s32 order[QUICKSTART_ITEM_CHOICES];
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        order[i] = i;
    }
    for (i = 0; i < QUICKSTART_ITEM_CHOICES - 1; i++) {
        r = (s32)Random() % (QUICKSTART_ITEM_CHOICES - i);
        tmp = order[i];
        order[i] = order[i + r];
        order[i + r] = tmp;
    }
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        Entity* itemEntity = CreateObject(GROUND_ITEM, choices[order[i]].itemId, 0);
        if (itemEntity != NULL) {
            itemEntity->x.HALF.HI = gRoomControls.origin_x + sQuickStartItemOffsets[i];
            itemEntity->y.HALF.HI = gRoomControls.origin_y + QUICKSTART_ITEM_ROW_Y;
            itemEntity->collisionLayer = 1;
            itemEntity->flags |= ENT_PERSIST;
            UpdateSpriteForCollisionLayer(itemEntity);
        }
    }
}

// How many of a round's item entities are still sitting on the row.
//
// This, and not an inventory scan, is how a round now detects "the player
// chose". The three items are drawn from the tier table at spawn time and
// nothing persists WHICH three were drawn (this file's statics don't
// survive - see the .data/linker.ld note elsewhere in this file - so
// remembering them would cost gSave.flags bits), and the pickup itself is
// not uniformly observable anyway: a rupee adds to the wallet rather than
// setting an inventory slot, and a bottled charm lands in a bottle. What IS
// uniform is that ItemOnGround deletes itself the moment it's taken
// (ItemOnGround_SetFlagAndDelete), so counting what's left on the row works
// for every item the table can produce.
static s32 QuickStartChoiceRowRemaining(void) {
    s32 i, j, count = 0;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* e = &gEntities[i].base;
        if (e->kind != OBJECT || e->id != GROUND_ITEM || (e->flags & ENT_DELETED)) {
            continue;
        }
        if (e->y.HALF.HI - gRoomControls.origin_y != QUICKSTART_ITEM_ROW_Y) {
            continue;
        }
        for (j = 0; j < QUICKSTART_ITEM_CHOICES; j++) {
            if (e->x.HALF.HI - gRoomControls.origin_x == sQuickStartItemOffsets[j]) {
                count++;
                break;
            }
        }
    }
    return count;
}

// Is vanilla's "Link holds the item overhead" cutscene on screen?
//
// Scanned by entity rather than read off gPriorityHandler: AnyPrioritySet()
// would also be true for anything else in the room that happens to raise a
// priority, and this gates a phase advance - a false positive here would be
// a soft-lock, not a glitch. CreateItemEntity builds exactly this pair
// (LINK_HOLDING_ITEM plus the LINK_ANIMATION that drives its frames, both
// kind OBJECT), and both are deleted when the sequence ends.
static bool32 QuickStartItemGetCutsceneRunning(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* e = &gEntities[i].base;
        if (e->kind != OBJECT || (e->flags & ENT_DELETED)) {
            continue;
        }
        if (e->id == LINK_HOLDING_ITEM || e->id == LINK_ANIMATION) {
            return TRUE;
        }
    }
    return FALSE;
}

// Every entry of (catMask, tierMask) the run can actually use right now,
// deduplicated. The dedup matters: ITEM_BOTTLE1 is listed twice in the tier
// table (once as a REWARD, once as a WEAPON), and a row that offered the
// same item in two of its three slots would be a round with two real
// choices, not three.
#define QUICKSTART_CHOICE_POOL_MAX 16
static s32 QuickStartCollectChoiceCandidates(u8 catMask, u8 tierMask, u16* out, s32 max) {
    s32 i, j, n = 0;
    for (i = 0; i < QUICKSTART_TIER_COUNT && n < max; i++) {
        const QuickStartTierEntry* e = &sQuickStartTiers[i];
        if ((e->cat & catMask) == 0 || (tierMask & QS_TIER_BIT(e->tier)) == 0) {
            continue;
        }
        if (!QuickStartTierEntryUsable(e)) {
            continue;
        }
        // A choice row is three items lying on the floor to be looked at
        // and walked into. An item with no floor form cannot be one of
        // them - it would leave a gap the player can neither see nor pick,
        // and granting it invisibly would defeat the point of a CHOICE. So
        // direct-grant items are drops and rewards only, never offers.
        if (QuickStartItemNeedsDirectGrant(e->item)) {
            continue;
        }
        for (j = 0; j < n; j++) {
            if (out[j] == e->item) {
                break;
            }
        }
        if (j == n) {
            out[n++] = e->item;
        }
    }
    return n;
}

// Draws 3 distinct items for one hub round out of the tier table and hands
// them to QuickStartSpawnItems, which shuffles their left-to-right order.
//
// If the requested band cannot supply 3 usable entries the draw WIDENS to
// every tier of the same categories rather than showing a short row. No
// round needs that today - the narrowest band is round 2's six rare
// REWARD/STAT entries, and all six are usable at run start because the boot
// grant hands out one empty bottle (see gSave.stats.bottles[0] = 0x20
// above), which is what the bottled fairy and the three charms require. It
// is the safety net for a band that runs dry later, not a live path.
//
// The pick is `Random() & 0x3F` reduced by subtraction, not a modulo:
// `count` is a runtime value and agbcc emits a call to __umodsi3 for
// division by anything but a constant, which its runtime library does not
// provide (the same constraint QuickStartTierPick documents). Six bits
// keeps that subtraction loop to at most 63 steps - reducing a full 32-bit
// Random() the same way would take hundreds of millions.
static void QuickStartSpawnChoiceRow(u8 catMask, u8 tierMask) {
    QuickStartItemChoice choices[QUICKSTART_ITEM_CHOICES];
    u16 pool[QUICKSTART_CHOICE_POOL_MAX];
    u8 used[QUICKSTART_ITEM_CHOICES];
    s32 count, i, j, draw;

    count = QuickStartCollectChoiceCandidates(catMask, tierMask, pool, QUICKSTART_CHOICE_POOL_MAX);
    if (count < QUICKSTART_ITEM_CHOICES) {
        count = QuickStartCollectChoiceCandidates(catMask, QS_TIER_ANY, pool, QUICKSTART_CHOICE_POOL_MAX);
    }
    // A heart piece is always usable (repeatable, no requirement), so a row
    // can never come up empty even if the categories somehow run dry.
    for (i = 0; i < QUICKSTART_ITEM_CHOICES; i++) {
        choices[i].itemId = ITEM_HEART_PIECE;
    }
    for (i = 0; i < QUICKSTART_ITEM_CHOICES && i < count; i++) {
        for (;;) {
            draw = (s32)(Random() & 0x3f);
            while (draw >= count) {
                draw -= count;
            }
            for (j = 0; j < i; j++) {
                if (used[j] == draw) {
                    break;
                }
            }
            if (j == i) {
                break;
            }
        }
        used[i] = (u8)draw;
        choices[i].itemId = pool[draw];
    }
    QuickStartSpawnItems(choices);
}

// Round 1: the run's key item. Which one the player takes is what decides
// the overworld path to the Earth Element (see
// QuickStartRandomizeRegionChainOnce below). All 9 QS_CAT_KEY entries are
// candidates - the previous hardcoded array listed only 5 - though the
// Ocarina of Wind is granted at boot and so is never usable here, leaving 8
// in practice.
#define QUICKSTART_CHOICE_ROW_1_CATS QS_CAT_KEY
#define QUICKSTART_CHOICE_ROW_1_TIERS QS_TIER_ANY
// Round 2: rare rewards and stat upgrades, per the user - the round that
// used to be a fixed heart container / 100 rupees / red potion.
#define QUICKSTART_CHOICE_ROW_2_CATS (QS_CAT_REWARD | QS_CAT_STAT)
#define QUICKSTART_CHOICE_ROW_2_TIERS QS_TIER_BIT(QS_TIER_RARE)
// Round 3: skills, rare excluded - the two rare skills (Down Thrust, Great
// Spin) both have prerequisites the player is unlikely to hold this early
// anyway, and holding them back leaves something for a "? room" to pay out.
#define QUICKSTART_CHOICE_ROW_3_CATS QS_CAT_SKILL
#define QUICKSTART_CHOICE_ROW_3_TIERS QS_TIER_NOT_RARE

static void QuickStartSpawnStarterChoice(void) {
    Entity* npc;

    QuickStartSpawnChoiceRow(QUICKSTART_CHOICE_ROW_1_CATS, QUICKSTART_CHOICE_ROW_1_TIERS);

    npc = CreateNPC(ZELDA, 0, 0);
    if (npc != NULL) {
        npc->x.HALF.HI = gRoomControls.origin_x + 120;
        npc->y.HALF.HI = gRoomControls.origin_y + 40;
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

// THE reason "? rooms" kept turning up empty.
//
// Every ground item in this engine is on a self-destruct: itemOnGround.c's
// sub_080814A4 sets unk_6c to 600 frames (ten seconds), or 120 if unk_69 is
// 10, and sub_080814C0 deletes the item when it reaches zero. That is right
// for an enemy's rupee drop and completely wrong for a reward deliberately
// placed in a room for the player to come and find.
//
// QuickStartRefreshItemTimers above exists precisely to stop that, and until
// now it was called from exactly ONE place: the hub's item-choice rows. It
// was written when the hub was the whole game, and never extended when the
// "? room" content sites were built - so every site reward, region reward,
// miniboss drop, wave payout and hunt prize has been quietly expiring.
//
// The consequence was worse than a vanishing item, because the "did it really
// get picked up, or did it just disappear?" guard reads the disappearance as
// a pickup and latches the site DONE forever. Sixty-one percent of content
// sites roll the item-drop kind, so most "? rooms" in a run were being
// permanently marked as looted having never shown anything at all. Confirmed
// by probing all 26 content-site rooms: every item-drop site read done=1 with
// zero ground items in the room.
//
// Only OUR items are refreshed, matched on ENT_PERSIST - which every reward
// this file places sets and no vanilla drop does. Refreshing everything would
// make enemy drops immortal and fill the 72-entity table during a wave.
static void QuickStartRefreshPlacedItemTimers(void) {
    s32 i;
    for (i = 0; i < MAX_ENTITIES; i++) {
        Entity* ent = &gEntities[i].base;
        if (ent->kind == OBJECT && ent->id == GROUND_ITEM && (ent->flags & ENT_PERSIST)) {
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


// The item-selection phase, mirrored somewhere it survives leaving the room.
//
// gRoomTransition.field_0x4[0] is transient: it is reset when a room loads.
// That was invisible in Castor Darknut, where the player had no reason to
// walk out mid-selection, and became a real bug the moment the hub gave them
// four floors to wander - stepping downstairs and back restarted the whole
// selection, handing out a second and third set of items.
//
// FLAG_BANK_11 bits 85-88 hold the same value (0-10 fits in four bits). The
// mirror is written by QuickStartHubSetPhase and read back on room entry.
#define GF_HUB_PHASE_BIT(b) (85 + (b)) // b = 0..3

static u8 QuickStartHubGetPhase(void) {
    s32 b;
    u8 v = 0;
    for (b = 0; b < 4; b++) {
        if (CheckLocalFlagByBank(FLAG_BANK_11, GF_HUB_PHASE_BIT(b))) {
            v |= (1 << b);
        }
    }
    return v;
}

static void QuickStartHubSetPhase(u8 phase) {
    s32 b;
    gRoomTransition.field_0x4[0] = phase;
    for (b = 0; b < 4; b++) {
        if (phase & (1 << b)) {
            SetLocalFlagByBank(FLAG_BANK_11, GF_HUB_PHASE_BIT(b));
        } else {
            ClearLocalFlagByBank(FLAG_BANK_11, GF_HUB_PHASE_BIT(b));
        }
    }
}

// Phase progression for gRoomTransition.field_0x4[0]:
//   0 - choosing the run's key item (3 of 5: Pegasus Boots/Roc's Cape/Mole
//       Mitts/Zora Flippers/Lantern) - decides which region the chain
//       routes to (QuickStartRandomizeRegionChainOnce)
//   1 - pending key item pickup cutscene
//   2 - choosing bonus reward (heart container/100 rupees/red potion)
//   3 - pending bonus reward pickup cutscene
//   4 - choosing tiger scroll (spin attack/roll attack/peril beam)
//   5 - pending tiger scroll pickup cutscene
//   6-9 - retired (Castor Darknut Main's three combat waves and the chest
//         that followed them); phase 5 now jumps straight to 10
//   10 - done
static void QuickStartUpdateItemChoice(void) {
    u8 phase = gRoomTransition.field_0x4[0];

    // Scoped to the hub's spawn floor alone. The guard mattered more when
    // this machine still ran combat waves - wandering out of the room right
    // as a wave's last enemy died spawned the next one wherever the player
    // happened to be standing, using whatever room's
    // gRoomControls.origin_x/y was active - but it is still what stops the
    // item rows being placed against another room's origin. Nothing spawns
    // and no phase advances outside this room.
    if (gRoomControls.area != QUICKSTART_AREA || gRoomControls.room != QUICKSTART_ROOM) {
        return;
    }
    // Re-entering the room zeroed the transient copy; take the mirror back.
    if (QuickStartHubGetPhase() > phase) {
        phase = QuickStartHubGetPhase();
        gRoomTransition.field_0x4[0] = phase;
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
        // ...and on the vanilla item-get cutscene, if one is running.
        //
        // A round now ends the frame its chosen item ENTITY disappears (see
        // QuickStartChoiceRowRemaining), which for a cutscene item is the
        // frame the cutscene starts: itemOnGround.c's sub_08081420 creates
        // the Link-animation/holding-item pair and only then deletes the
        // ground item. GiveItem doesn't run until LinkHoldingItem_Action1
        // several frames later, so tearing the row down and reloading the
        // room here would cancel the pickup the player just made. The old
        // inventory-based detection never saw this window because it
        // couldn't fire until GiveItem had already run.
        if (QuickStartItemGetCutsceneRunning()) {
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
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + QUICKSTART_HUB_SPAWN_X;
            gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + QUICKSTART_HUB_SPAWN_Y;
            QuickStartSpawnChoiceRow(QUICKSTART_CHOICE_ROW_2_CATS, QUICKSTART_CHOICE_ROW_2_TIERS);
            QuickStartHubSetPhase(2);
        } else if (phase == 3) {
            // No manual maxHealth bump here any more. This used to add 8
            // (one heart) on the belief that ITEM_HEART_CONTAINER has no
            // pickup effect of its own, and QuickStartApplyHeartContainerBonusOnce
            // added a second 8 on the same belief - but vanilla already
            // grants it: a ground-item pickup runs
            // itemOnGround.c's sub_08081420 -> CreateItemEntity and a shop
            // purchase runs script.c's ScriptCommand_BuyShopItem ->
            // InitItemGetSequence, and both build the same LINK_HOLDING_ITEM
            // with timer 0, whose LinkHoldingItem_Action3 case 0 does
            // `maxHealth += 8` for exactly this item. Three grants for one
            // container is why the round-2 choice took the player from 2
            // hearts to 5 (reported by the user).
            //
            // Same reasoning as phase 1 above: reposition before the skill
            // item row spawns at the same reused coordinates.
            gPlayerEntity.base.x.HALF.HI = gRoomControls.origin_x + QUICKSTART_HUB_SPAWN_X;
            gPlayerEntity.base.y.HALF.HI = gRoomControls.origin_y + QUICKSTART_HUB_SPAWN_Y;
            QuickStartSpawnChoiceRow(QUICKSTART_CHOICE_ROW_3_CATS, QUICKSTART_CHOICE_ROW_3_TIERS);
            QuickStartHubSetPhase(4);
        } else {
            // UpdatePlayerSkills (playerUtils.c) is what actually turns the
            // ITEM_SKILL_* inventory flag into a usable gPlayerState.skills
            // bit - it normally only runs once per full player (re)init,
            // which this mid-game reload doesn't trigger (the player entity
            // persists across RELOAD_ALL, unlike a real area transition).
            UpdatePlayerSkills();
            // Phase 10 = "the hub is finished with this run", not 6. Phases
            // 6-9 were Castle Darknut's three waves and the chest that
            // followed them, and with the waves retired phase 6 found an
            // empty room, fell straight through 7 and 8, and dropped that
            // chest's HEART PIECE on the floor the instant the third item
            // was taken - the stray heart piece the user reported. The whole
            // combat tail is skipped instead of being left to run dry.
            // RETIRED: this used to spawn wave 1 the moment the third item
            // was taken - Castor Darknut Main's third act, back when the
            // selection room was also a combat room. The hub has no combat
            // phase: the player picks three items and walks downstairs. Per
            // the user, "after item selection, no enemies spawn".
            //
            // Worth keeping the reason it was edge-triggered rather than
            // polled, in case a hub wave is ever wanted: an idempotent
            // "spawn if the room is empty" poll resurrected enemies the
            // player had already killed every time they walked back in.
            QuickStartHubSetPhase(10);
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

    if (phase == 0 && !QsCheckRoomFlag(41)) {
        // One-time custom Ezlo hint, moved here from QuickStartSpawnStarterChoice
        // (see its own comment) - that function runs during
        // GameMain_ChangeRoom's brief room-entry transition, before the
        // player is back in real control, so CreateEzloHint's queued_action
        // was getting reset before PlayerTalkEzlo ever ran. This branch runs
        // every frame of real GAMEMAIN_UPDATE gameplay (see the QUICKSTART
        // block right after PausePlayer, below in this file), so the player
        // is guaranteed to actually be in a state that can process it. Room
        // flag 41, like every other room flag in this file, is offset into
        // QUICKSTART's own private window (QsSetRoomFlag) - it does not
        // collide with the real vanilla content this room is tied to
        // (Castor Wilds' own Darknut/Kinstone guardian fight).
        CreateEzloHint(TEXT_INDEX(TEXT_CUSTOM, 5), 0);
        QsSetRoomFlag(41);
    }

    if (phase == 0 || phase == 2 || phase == 4) {
        // "One of the three is gone" - see QuickStartChoiceRowRemaining for
        // why the round is no longer detected by scanning inventory for the
        // items it offered.
        //
        // The `> 0` half is not redundant. This function also runs during
        // GameMain_ChangeRoom (QuickStartUpdate), which can be a frame or
        // two ahead of the row actually being spawned; an empty row must
        // read as "not spawned yet", not as "all three taken".
        s32 remaining = QuickStartChoiceRowRemaining();
        bool32 pickedUp = (remaining > 0 && remaining < QUICKSTART_ITEM_CHOICES);
        QuickStartRefreshItemTimers();
        if (pickedUp) {
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
            //
            // Which skill was taken is found by scanning the tier table's
            // QS_CAT_SKILL rows for one the player now owns, rather than by
            // scanning the three that were offered - nothing persists which
            // three those were (see QuickStartChoiceRowRemaining). At most
            // one can match: the per-run reset clears the inventory, and
            // rounds 1 and 2 hand out key items and rewards, so round 3 is
            // the first skill of the run.
            if (phase == 4) {
                s32 i;
                for (i = 0; i < QUICKSTART_TIER_COUNT; i++) {
                    u16 skillItem = sQuickStartTiers[i].item;
                    if ((sQuickStartTiers[i].cat & QS_CAT_SKILL) && GetInventoryValue(skillItem) != 0) {
                        MessageRequest(TEXT_INDEX(TEXT_ITEM_GET, gItemMetaData[skillItem].textId));
                        break;
                    }
                }
            }
            QuickStartHubSetPhase(phase + 1);
        }
        return;
    }

    // RETIRED: phases 6-9, Castor Darknut Main's three combat waves and the
    // heart-piece chest that followed them. Finishing the third item pick now
    // jumps straight to phase 10 (see the phase 5 handler above), so nothing
    // can reach these any more - and while they were still reachable, the
    // retired waves left phase 6 looking at an empty room, which fell through
    // 7 and 8 and dropped that chest's heart piece on the floor the instant
    // selection ended. The hub's combat lives on the roof instead.
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
    // during every room-entry reload, not just ones on the hub's spawn floor.
    if (gRoomControls.area != QUICKSTART_AREA || gRoomControls.room != QUICKSTART_ROOM) {
        return;
    }
    // Read the persistent mirror, not gRoomTransition.field_0x4[0]. That
    // byte is transient RAM that a room load zeroes, so walking downstairs
    // and back up put phase 0 back in front of this check and respawned the
    // starter row - a fresh set of three free key items every trip, and the
    // whole selection running a second time. Harmless in Castor Darknut
    // Main, where the player never left the room before the phase was over;
    // fatal in a four-floor hub. QuickStartUpdateItemChoice below restores
    // the transient copy from the same mirror, but it runs after this.
    if (QuickStartHubGetPhase() == 0) {
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
