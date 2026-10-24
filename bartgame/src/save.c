/* BARTGAME: the save file, one, in SRAM. Byte writes of a checksummed
   record: the whole World (gates, roles, flags, the map's marks), the
   PlayerState and the run's counts. */
#include "gba.h"
#include "util.h"
#include "world.h"
#include "player.h"
#include "game.h"
#include "save.h"

#define SRAM ((volatile u8*)0x0E000000)
#define SAVE_MAGIC 0x54524142u /* "BART" */
#define SAVE_VERSION 1

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
    return sFile.magic == SAVE_MAGIC && sFile.version == SAVE_VERSION && sFile.size == sizeof(SaveFile) &&
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
    return TRUE;
}

void save_erase(void) {
    int i;
    for (i = 0; i < 8; i++)
        SRAM[i] = 0;
}
