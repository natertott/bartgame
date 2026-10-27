/* BARTGAME: video setup, VBlank flush, OAM shadow, fades. */
#include "gba.h"
#include "video.h"

volatile u32 gFrame;
volatile u8 gVBlankFlag;
u16 gKeysHeld, gKeysDown, gKeysUp;

OamEntry gOam[128] ALIGN4;
u8 gOamCount;
s16 gBgScroll[4][2];
u16 gPalBg[256] ALIGN4;
u16 gPalObj[256] ALIGN4;
u8 gPalDirty;
s8 gFadeLevel; /* 0 = normal, 16 = black */
static s8 sFadeTarget;
static u8 sFadeSpeed;

void (*gVBlankHook)(void);

void vblank_isr(void) {
    gVBlankFlag = 1;
    gFrame++;
    if (gVBlankHook)
        gVBlankHook();
}

void video_init(void) {
    REG_DISPCNT = DCNT_BLANK;
    REG_WAITCNT = 0x4317; /* prefetch, ROM 3/1 waits */
    REG_DISPSTAT = 0x0008; /* VBlank IRQ */
    REG_IE = 0x0001;
    REG_IME = 1;
    gOamCount = 0;
    oam_clear();
    oam_flush();
    REG_BG0CNT = BGCNT_PRIO(0) | BGCNT_CHARBASE(2) | BGCNT_SCREENBASE(23) | BGCNT_SIZE_32x32;
    REG_BG1CNT = BGCNT_PRIO(1) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(24) | BGCNT_SIZE_64x64;
    REG_BG2CNT = BGCNT_PRIO(2) | BGCNT_CHARBASE(0) | BGCNT_SCREENBASE(28) | BGCNT_SIZE_64x64;
    REG_BG3CNT = BGCNT_PRIO(3) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(22) | BGCNT_SIZE_32x32; /* the menu's backdrop */
    REG_BLDCNT = 0;
    REG_BLDY = 0;
}

void video_show(u16 flags) {
    REG_DISPCNT = DCNT_MODE0 | DCNT_OBJ_1D | flags;
}

void input_read(void) {
    u16 now = ~REG_KEYINPUT & KEY_ANY;
    gKeysDown = now & ~gKeysHeld;
    gKeysUp = gKeysHeld & ~now;
    gKeysHeld = now;
}

void oam_clear(void) {
    int i;
    for (i = 0; i < 128; i++) {
        gOam[i].attr0 = ATTR0_HIDE;
        gOam[i].attr1 = 0;
        gOam[i].attr2 = 0;
    }
    gOamCount = 0;
}

OamEntry* oam_alloc(void) {
    if (gOamCount >= 128)
        return NULL;
    return &gOam[gOamCount++];
}

void oam_flush(void) {
    dma3_copy32(gOam, MEM_OAM, sizeof(gOam));
}

void pal_set_bg(int slot, const u16* colors) {
    memcpy32(&gPalBg[slot * 16], colors, 32);
    gPalDirty = 1;
}

void pal_set_obj(int slot, const u16* colors) {
    memcpy32(&gPalObj[slot * 16], colors, 32);
    gPalDirty = 1;
}

static u16 fade_color(u16 c, int level) {
    if (level <= 0)
        return c;
    if (level >= 16)
        return 0;
    int r = (c & 31) * (16 - level) >> 4;
    int g = ((c >> 5) & 31) * (16 - level) >> 4;
    int b = ((c >> 10) & 31) * (16 - level) >> 4;
    return RGB15(r, g, b);
}

static void pal_upload(void) {
    static u16 tmp[256] ALIGN4;
    int i;
    if (gFadeLevel == 0) {
        dma3_copy32(gPalBg, MEM_PAL_BG, 512);
        dma3_copy32(gPalObj, MEM_PAL_OBJ, 512);
        return;
    }
    for (i = 0; i < 256; i++)
        tmp[i] = fade_color(gPalBg[i], gFadeLevel);
    dma3_copy32(tmp, MEM_PAL_BG, 512);
    for (i = 0; i < 256; i++)
        tmp[i] = fade_color(gPalObj[i], gFadeLevel);
    dma3_copy32(tmp, MEM_PAL_OBJ, 512);
}

void fade_start(int target, int speed) {
    sFadeTarget = target;
    sFadeSpeed = speed ? speed : 1;
    gPalDirty = 1;
}

bool8 fade_done(void) {
    return gFadeLevel == sFadeTarget;
}

void fade_set(int level) {
    gFadeLevel = sFadeTarget = level;
    gPalDirty = 1;
}

void fade_update(void) {
    if (gFadeLevel == sFadeTarget)
        return;
    if (gFadeLevel < sFadeTarget) {
        gFadeLevel += sFadeSpeed;
        if (gFadeLevel > sFadeTarget)
            gFadeLevel = sFadeTarget;
    } else {
        gFadeLevel -= sFadeSpeed;
        if (gFadeLevel < sFadeTarget)
            gFadeLevel = sFadeTarget;
    }
    gPalDirty = 1;
}

/* Called right after VBlank: push everything the frame prepared. */
void video_flush(void) {
    oam_flush();
    if ((REG_DISPCNT & 7) == DCNT_MODE3) {
        /* Direct-colour title pixels do not pass through a BG palette.
           Fade the bitmap and its OBJ words together in hardware. */
        REG_BLDCNT = 0x00C0 | DCNT_BG2 >> 8 | DCNT_OBJ >> 8;
        REG_BLDY = gFadeLevel;
        if (gPalDirty) {
            dma3_copy32(gPalObj, MEM_PAL_OBJ, 512);
            gPalDirty = 0;
        }
        return;
    }
    REG_BG0HOFS = gBgScroll[0][0];
    REG_BG0VOFS = gBgScroll[0][1];
    REG_BG1HOFS = gBgScroll[1][0];
    REG_BG1VOFS = gBgScroll[1][1];
    REG_BG2HOFS = gBgScroll[2][0];
    REG_BG2VOFS = gBgScroll[2][1];
    REG_BG3HOFS = gBgScroll[3][0];
    REG_BG3VOFS = gBgScroll[3][1];
    if (gPalDirty) {
        pal_upload();
        gPalDirty = 0;
    }
}

void frame_wait(void) {
    gVBlankFlag = 0;
    vblank_wait();
}
