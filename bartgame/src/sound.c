/* BARTGAME: sound on the GBA's PSG channels. No mixer, near-zero CPU.
   Channel 1 (square, sweep): sound effects. Channel 2 (square): melody.
   Channel 3 (wave): bass drone. Channel 4 (noise): percussion and hits.
   The tracker runs once a frame. Music comes in phase 9; for now the
   channels are set up and effects play. */
#include "gba.h"
#include "sound.h"

static u8 sSfxTimer;
static u8 sSfxCur;
static u8 sBgm;

void sound_init(void) {
    REG_SOUNDCNT_X = 0x80;      /* master on */
    REG_SOUNDCNT_L = 0xFF77;    /* all channels both sides, volume 7 */
    REG_SOUNDCNT_H = 0x0002;    /* PSG 100% */
    REG_SOUNDBIAS = 0x0200;
    sSfxTimer = 0;
}

/* square channel 1 note: freq in 11-bit register units, env, duty, sweep */
static void ch1(u16 sweep, u16 env, u16 freq) {
    REG_SOUND1CNT_L = sweep;
    REG_SOUND1CNT_H = env;
    REG_SOUND1CNT_X = freq | 0x8000;
}

static void ch4(u16 env, u16 poly) {
    REG_SOUND4CNT_L = env;
    REG_SOUND4CNT_H = poly | 0x8000;
}

void sfx_play(int id) {
    /* a louder or equal effect replaces a quieter one in progress */
    if (sSfxTimer && id < sSfxCur)
        return;
    sSfxCur = id;
    sSfxTimer = 8;
    switch (id) {
        case SFX_SWORD: ch1(0x0039, 0xC180, 0x0600); break;              /* sweep down, short */
        case SFX_HURT: ch1(0x002E, 0xA1C0, 0x0400); ch4(0xA100, 0x0057); break;
        case SFX_ROLL: ch1(0x0017, 0x6280, 0x0300); break;
        case SFX_BUMP: ch4(0x7100, 0x0045); break;
        case SFX_FALL: ch1(0x003F, 0xD2C0, 0x0580); break;
        case SFX_ITEM: ch1(0x0000, 0xF080, 0x06C0); sSfxTimer = 20; break;
        case SFX_JUMP: ch1(0x0014, 0x7280, 0x0420); break;
        case SFX_HIT: ch4(0xC100, 0x0036); ch1(0x0039, 0x8180, 0x0500); break;
        case SFX_KILL: ch4(0xF200, 0x0067); sSfxTimer = 12; break;
        case SFX_PICKUP: ch1(0x0000, 0x8180, 0x0700); break;
        case SFX_HEART: ch1(0x0000, 0xA180, 0x0680); break;
        case SFX_KEY: ch1(0x0000, 0xB1C0, 0x0720); sSfxTimer = 14; break;
        case SFX_DOOR: ch4(0xA300, 0x0047); ch1(0x0040, 0x9280, 0x0200); break;
        case SFX_BOMB_SET: ch1(0x0000, 0x5080, 0x0580); break;
        case SFX_BOMB: ch4(0xF700, 0x0074); sSfxTimer = 30; break;
        case SFX_TEXT: ch1(0x0000, 0x3080, 0x0740); sSfxTimer = 2; break;
        case SFX_MENU: ch1(0x0000, 0x6080, 0x0700); break;
        case SFX_SPIT: ch4(0x6100, 0x0032); break;
        case SFX_LAMP: ch4(0x9300, 0x0024); ch1(0x0020, 0x7280, 0x0400); break;
        case SFX_SECRET: ch1(0x0000, 0xF1C0, 0x0740); sSfxTimer = 24; break;
        case SFX_CHEST: ch1(0x0000, 0xC180, 0x0640); sSfxTimer = 16; break;
        case SFX_BOSS_HIT: ch4(0xE200, 0x0056); ch1(0x0037, 0xB1C0, 0x0380); break;
        case SFX_WIN: ch1(0x0000, 0xF0C0, 0x0700); sSfxTimer = 40; break;
        default: break;
    }
}

void bgm_play(int id) {
    sBgm = id;
}

void bgm_stop(void) {
    sBgm = BGM_NONE;
}

void sound_update(void) {
    if (sSfxTimer)
        sSfxTimer--;
}
