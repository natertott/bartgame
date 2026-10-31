#ifndef SOUND_H
#define SOUND_H
#include "gba.h"

enum {
    SFX_NONE, SFX_SWORD, SFX_HURT, SFX_ROLL, SFX_BUMP, SFX_FALL, SFX_ITEM, SFX_JUMP,
    SFX_HIT, SFX_KILL, SFX_PICKUP, SFX_HEART, SFX_KEY, SFX_DOOR, SFX_BOMB_SET, SFX_BOMB,
    SFX_TEXT, SFX_MENU, SFX_SPIT, SFX_LAMP, SFX_SECRET, SFX_CHEST, SFX_BOSS_HIT, SFX_WIN,
    SFX_COUNT
};

/* One source recording per cartridge, avoiding the32MiB ROM limit. */
enum {
    BGM_NONE = 0,
    BGM_SOURCE = 1,
    BGM_COUNT = 2
};

/* Review mailbox: write1 to restart the source, 0xFFFF to stop.
   Frame is the timeline frame just processed (first update is frame0).
   It wraps to loop_frame at the playback boundary. */
extern volatile u16 gAudioReviewRequest;
extern volatile u16 gAudioReviewActive;
extern volatile u32 gAudioReviewFrame;

void sound_init(void);
void sound_update(void);
void sfx_play(int id);
void bgm_play(int id);
void bgm_stop(void);

#endif
