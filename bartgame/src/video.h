#ifndef VIDEO_H
#define VIDEO_H
#include "gba.h"

extern volatile u32 gFrame;
extern u16 gKeysHeld, gKeysDown, gKeysUp;
extern OamEntry gOam[128];
extern u8 gOamCount;
extern s16 gBgScroll[4][2];
extern u16 gPalBg[256];
extern u16 gPalObj[256];
extern u8 gPalDirty;
extern s8 gFadeLevel;
extern void (*gVBlankHook)(void);

void vblank_isr(void);
void video_init(void);
void video_show(u16 flags);
void input_read(void);
void oam_clear(void);
OamEntry* oam_alloc(void);
void oam_flush(void);
void pal_set_bg(int slot, const u16* colors);
void pal_set_obj(int slot, const u16* colors);
void fade_start(int target, int speed);
void fade_set(int level);
bool8 fade_done(void);
void fade_update(void);
void video_flush(void);
void frame_wait(void);

#endif
