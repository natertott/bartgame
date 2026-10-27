/* BARTGAME: the save file, one, in SRAM. Byte writes of a checksummed
   record: the whole World (gates, roles, flags, the map's marks), the
   PlayerState and the run's counts. */
#include "gba.h"
#include "util.h"
#include "world.h"
#include "player.h"
#include "game.h"
#include "save.h"
#include "myst.h"

#define SRAM ((volatile u8*)0x0E000000)
#define SAVE_MAGIC 0x54524142u /* "BART" */
#define SAVE_VERSION 2
#define SAVE_LEGACY_VERSION 1

/* the string emulators and flash carts look for to give the ROM SRAM */
const char gSramId[] __attribute__((used)) = "SRAM_V113";

typedef struct {
    u32 magic;
    u16 version, size;
    World world;
    PlayerState pl;
    u16 deaths, kills;
    u32 run_frames;
    u32 sum;
} SaveFile;

static SaveFile sFile EWRAM_BSS;

static u32 checksum(const u8* p, int n) {
    u32 s = 0x9E3779B9u;
    int i;
    for (i = 0; i < n; i++)
        s = (s ^ p[i]) * 16777619u;
    return s;
}

static void sram_write(const void* src, int n) {
    const u8* p = src;
    int i;
    for (i = 0; i < n; i++)
        SRAM[i] = p[i];
}

static void sram_read(void* dst, int n) {
    u8* p = dst;
    int i;
    for (i = 0; i < n; i++)
        p[i] = SRAM[i];
}

static bool8 file_valid(void) {
    return sFile.magic == SAVE_MAGIC && (sFile.version == SAVE_VERSION || sFile.version == SAVE_LEGACY_VERSION) && sFile.size == sizeof(SaveFile) &&
           sFile.sum == checksum((const u8*)&sFile, sizeof(SaveFile) - 4);
}

void save_write(void) {
    volatile const char* id = gSramId;
    (void)*id;
    sFile.magic = SAVE_MAGIC;
    sFile.version = SAVE_VERSION;
    sFile.size = sizeof(SaveFile);
    sFile.world = gWorld;
    sFile.pl = gPl;
    sFile.deaths = gGame.deaths;
    sFile.kills = gGame.kills;
    sFile.run_frames = gGame.run_frames;
    sFile.sum = checksum((const u8*)&sFile, sizeof(SaveFile) - 4);
    sram_write(&sFile, sizeof(SaveFile));
}

bool8 save_exists(void) {
    sram_read(&sFile, sizeof(SaveFile));
    return file_valid();
}

/* Old runs stored a free overworld item chest and an unrelated optional
   mystery in each key room. Keep their graph and inventory intact, but turn
   each unclaimed reward into the new solvable trial. In particular an old
   optional mystery's MF_DONE must not consume the required item reward. */
static void migrate_legacy_trials(void) {
    static const u8 kinds[3] = { MK_SWITCHES, MK_WAVES, MK_MINIBOSS };
    static const u8 items[3] = { ITEM_BOMBS, ITEM_LAMP, ITEM_CLOAK };
    int i;
    for (i = 0; i < CELLS; i++) {
        Cell* c = &gWorld.cells[i];
        int key;
        if (c->role != ROLE_KEYITEM || c->role_arg < 1 || c->role_arg > 3)
            continue;
        key = c->role_arg - 1;
        gWorld.myst[i] = MYST_PACK(kinds[key], MS_MEDIUM, (gWorld.seed + i) % 3);
        if (gPl.items & items[key]) {
            c->flags |= CF_ITEM_TAKEN | CF_CHEST_OPEN;
            gWorld.myst_flags[i] |= MF_DONE | MF_WON;
        } else {
            c->flags &= ~(CF_ITEM_TAKEN | CF_CHEST_OPEN);
            gWorld.myst_flags[i] = 0;
        }
    }
}

bool8 save_load(void) {
    sram_read(&sFile, sizeof(SaveFile));
    if (!file_valid())
        return FALSE;
    gWorld = sFile.world;
    gPl = sFile.pl;
    gGame.deaths = sFile.deaths;
    gGame.kills = sFile.kills;
    gGame.run_frames = sFile.run_frames;
    gGame.seed = gWorld.seed;
    if (sFile.version == SAVE_LEGACY_VERSION) {
        migrate_legacy_trials();
        save_write(); /* persist the upgraded record with a fresh checksum */
    }
    return TRUE;
}

void save_erase(void) {
    int i;
    for (i = 0; i < 8; i++)
        SRAM[i] = 0;
}
