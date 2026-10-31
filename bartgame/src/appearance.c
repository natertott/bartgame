/* Independent title-screen preferences. The run's legacy/version2 SRAM
   record stays byte-for-byte compatible and save_erase never touches this
   separate twelve-byte record at the end of ordinary32KB SRAM. */
#include "gba.h"
#include "video.h"
#include "assets.h"
#include "appearance.h"

#define PREFS_SRAM ((volatile u8*)(0x0E000000u + APPEARANCE_SRAM_OFFSET))
#define PREFS_MAGIC 0x4F545242u /* BRTO: BART appearance options */
u8 gAppearanceStyle, gAppearancePalette;
static u16 sAppearanceRevision;
const char* const gAppearanceStyleNames[AP_COUNT] = {
    "Winebound Folio", "Mossbound Fieldbook", "Ivory Reliquary"
};
const char* const gAppearancePaletteNames[AP_COUNT] = {
    "Wine / gilt", "Moss / brass", "Ivory / slate"
};

static u32 prefs_checksum(const u8* data) {
    u32 sum = 2166136261u;
    int i;
    for (i = 0; i < 8; i++) sum = (sum ^ data[i]) * 16777619u;
    return sum;
}

void appearance_init(void) {
    u32 words[3];
    u8* data = (u8*)words;
    int i;
    gAppearanceStyle = gAppearancePalette = 0;
    for (i = 0; i < 12; i++) data[i] = PREFS_SRAM[i];
    if (words[0] == PREFS_MAGIC && data[4] == 1 && data[5] < AP_COUNT &&
        data[6] < AP_COUNT && data[7] == 0 && words[2] == prefs_checksum(data)) {
        gAppearanceStyle = data[5];
        gAppearancePalette = data[6];
    }
    sAppearanceRevision++;
    appearance_apply();
}

void appearance_save(void) {
    u32 words[3];
    u8* data = (u8*)words;
    int i;
    words[0] = PREFS_MAGIC;
    data[4] = 1;
    data[5] = gAppearanceStyle;
    data[6] = gAppearancePalette;
    data[7] = 0;
    words[2] = prefs_checksum(data);
    /* Write validity last, so an interrupted update falls back safely. */
    PREFS_SRAM[0] = 0;
    for (i = 1; i < 12; i++) PREFS_SRAM[i] = data[i];
    PREFS_SRAM[0] = data[0];
}

void appearance_apply(void) {
    const u16* menu = appearance_palettes + gAppearancePalette * 16;
    u16 map[16];
    int i;
    pal_set_bg(PAL_SLOT_MENU, menu);
    /* Continuation and selection pointers use their own UI slot. The
       separate HUD/minimap slot15 retains its fixed Winebound palette. */
    pal_set_obj(PAL_OBJ_UI, menu);
    for (i = 0; i < 16; i++) map[i] = pal_bg[PAL_BG_MAP * 16 + i];
    /* Only neutral map paper/ink follows the UI. Terrain, player and
       landmark meanings stay stable; the HUD/minimap palette is untouched. */
    map[1] = menu[UI_INK_DARK];
    map[2] = menu[UI_INK_NAVY];
    map[3] = menu[UI_INK_EDGE];
    map[13] = menu[UI_INK_RAISED];
    map[15] = menu[UI_INK_CREAM];
    pal_set_bg(PAL_SLOT_MAP, map);
}

bool8 appearance_set_style(int style) {
    if (style < 0 || style >= AP_COUNT || style == gAppearanceStyle) return FALSE;
    gAppearanceStyle = style;
    sAppearanceRevision++;
    return TRUE;
}
bool8 appearance_set_palette(int palette) {
    if (palette < 0 || palette >= AP_COUNT || palette == gAppearancePalette) return FALSE;
    gAppearancePalette = palette;
    sAppearanceRevision++;
    appearance_apply();
    return TRUE;
}
u8 appearance_style(void) { return gAppearanceStyle; }
u8 appearance_palette(void) { return gAppearancePalette; }
u16 appearance_revision(void) { return sAppearanceRevision; }
const u16* ui_current_tiles(void) {
    return appearance_ui_tiles + gAppearanceStyle * UI_TILE_COUNT * 16;
}
const u16* ui_current_marks(void) {
    return appearance_mark_tiles + gAppearanceStyle * APPEARANCE_MARK_COUNT * 16;
}
