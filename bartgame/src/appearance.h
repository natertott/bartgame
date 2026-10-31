#ifndef APPEARANCE_H
#define APPEARANCE_H
#include "gba.h"

/* Shape and color are independent. The HUD keeps the selected Winebound
   drawing/palette; these preferences affect the menus and dialogue. */
enum { AP_WINEBOUND, AP_MOSSBOUND, AP_IVORY, AP_COUNT };
#define APPEARANCE_SRAM_OFFSET 0x7F00u /* reserved final256 bytes of32KB SRAM */
extern u8 gAppearanceStyle, gAppearancePalette; /* read-only presentation probes */
extern const char* const gAppearanceStyleNames[AP_COUNT];
extern const char* const gAppearancePaletteNames[AP_COUNT];
void appearance_init(void);
void appearance_save(void);
void appearance_apply(void);
bool8 appearance_set_style(int style);
bool8 appearance_set_palette(int palette);
u8 appearance_style(void);
u8 appearance_palette(void);
u16 appearance_revision(void);
const u16* ui_current_tiles(void);
const u16* ui_current_marks(void);
#endif
