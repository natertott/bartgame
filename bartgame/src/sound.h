#ifndef SOUND_H
#define SOUND_H
#include "gba.h"

enum {
    SFX_NONE, SFX_SWORD, SFX_HURT, SFX_ROLL, SFX_BUMP, SFX_FALL, SFX_ITEM, SFX_JUMP,
    SFX_HIT, SFX_KILL, SFX_PICKUP, SFX_HEART, SFX_KEY, SFX_DOOR, SFX_BOMB_SET, SFX_BOMB,
    SFX_TEXT, SFX_MENU, SFX_SPIT, SFX_LAMP, SFX_SECRET, SFX_CHEST, SFX_BOSS_HIT, SFX_WIN,
    SFX_COUNT
};

enum { BGM_NONE, BGM_SEWER, BGM_FOREST, BGM_BOSS, BGM_TITLE, BGM_WIN };

void sound_init(void);
void sound_update(void);
void sfx_play(int id);
void bgm_play(int id);
void bgm_stop(void);

#endif
