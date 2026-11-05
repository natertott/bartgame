/* Original BARTGAME soundtrack: native recorded mix streamed straight from
   ROM to the GBA FIFO. No runtime decoder, mixer, sample RAM or DMA3 use.
   Timer0=32768Hz; Timer1 counts actual consumed samples. A VBlank heartbeat
   keeps looping safe even while room construction blocks normal game logic.
   The PCM guard contains the loop continuation, so there is no silent tail.
   Pulse1/noise retain the existing gameplay SFX; music pulse2/wave are muted. */
#include "gba.h"
#include "video.h"
#include "sound.h"
#include "original_music_data.h"

#define REG_FIFO_A REG32(0xA0)
#define REG_DMA1SAD REG32(0xBC)
#define REG_DMA1DAD REG32(0xC0)
#define REG_DMA1CNT REG32(0xC4)
#define REG_TM1CNT_L REG16(0x104)
#define REG_TM1CNT_H REG16(0x106)
#define PCM_CONTROL 0x0306u /* PSG100%, FIFO_A100%, A routed both speakers */
#define PCM_FIFO_RESET 0x0800u
#define PCM_DMA_CONTROL 0xB6400000u /* special,32bit,repeat,destination fixed */

/* Read-only capture diagnostics. These are never external control requests. */
volatile u16 gOriginalMusicBgm, gOriginalMusicTrack;
volatile u32 gOriginalMusicSamples, gOriginalMusicLoops, gOriginalMusicDmaOffset;

static const OriginalSong* sSong;
static u16 sSampleCounter;
static u8 sSfxTimer, sSfxCur, sPulseHeld, sNoiseHeld;
static void (*sPriorVBlankHook)(void);

static void music_channels_off(void) {
    REG_SOUND2CNT_L=0;
    REG_SOUND2CNT_H=0x8000;
    REG_SOUND3CNT_H=0;
}

/* Caller holds IRQ exclusion or is already inside VBlank. Only DMA1 and
   timers0/1 are touched; video DMA3 and profiler timers2/3 are independent. */
static void pcm_begin(const OriginalSong* song,u32 sample) {
    sample &= ~3u; /* DMA word alignment, at most3 samples (<0.1ms) backward */
    REG_TM0CNT_H=0;
    REG_TM1CNT_H=0;
    REG_DMA1CNT=0;
    REG_SOUNDBIAS=0x0200; /* synchronous9-bit32768Hz PWM */
    REG_SOUNDCNT_H=PCM_CONTROL|PCM_FIFO_RESET;
    REG_DMA1SAD=(u32)(song->pcm+sample);
    REG_DMA1DAD=REG_BASE+0xA0;
    REG_DMA1CNT=PCM_DMA_CONTROL;
    REG_TM1CNT_L=0;
    REG_TM1CNT_H=0x0084; /* enable, cascade from sample timer0 */
    sSampleCounter=0;
    gOriginalMusicSamples=sample;
    gOriginalMusicDmaOffset=sample;
    REG_TM0CNT_L=0xFE00;
    REG_TM0CNT_H=0x0080;
}

/* Runs once per physical VBlank, including logic overruns and modal menus.
   At32768 samples/sec a16-bit difference spans two seconds; VBlank samples
   it about60 times/sec, so ordinary counter wrap is unambiguous. */
void sound_vblank(void) {
    const OriginalSong* song=sSong;
    if (song) {
        u16 count=REG_TM1CNT_L;
        u32 position=gOriginalMusicSamples+(u16)(count-sSampleCounter);
        sSampleCounter=count;
        if (position>=song->samples) {
            position=song->loop_sample+(position-song->samples);
            gOriginalMusicLoops++;
            /* The musical guard has already played this overrun. Repoint at
               its corresponding loop position, never reset to the loop head. */
            pcm_begin(song,position);
        } else gOriginalMusicSamples=position;
    }
    if (sPriorVBlankHook) sPriorVBlankHook();
}

void sound_init(void) {
    REG_TM0CNT_H=0;
    REG_TM1CNT_H=0;
    REG_DMA1CNT=0;
    REG_SOUNDCNT_X=0x0080;
    REG_SOUNDCNT_L=0xFF77;
    REG_SOUNDCNT_H=PCM_FIFO_RESET|2;
    REG_SOUNDBIAS=0x0200;
    REG_SOUND1CNT_H=0;
    REG_SOUND1CNT_X=0x8000;
    REG_SOUND4CNT_L=0;
    REG_SOUND4CNT_H=0x8000;
    music_channels_off();
    sSong=NULL;
    sSampleCounter=0;
    sSfxTimer=sSfxCur=sPulseHeld=sNoiseHeld=0;
    gOriginalMusicBgm=gOriginalMusicTrack=0;
    gOriginalMusicSamples=gOriginalMusicLoops=gOriginalMusicDmaOffset=0;
    if (gVBlankHook!=sound_vblank) sPriorVBlankHook=gVBlankHook;
    gVBlankHook=sound_vblank;
}

static void ch1(u16 sweep, u16 env, u16 freq) {
    sPulseHeld=(env&0x0700)==0; /* period0 has no automatic decay */
    REG_SOUND1CNT_L = sweep;
    REG_SOUND1CNT_H = env;
    REG_SOUND1CNT_X = freq | 0x8000;
}

static void ch4(u16 env, u16 poly) {
    sNoiseHeld=(env&0x0700)==0;
    REG_SOUND4CNT_L = env;
    REG_SOUND4CNT_H = poly | 0x8000;
}

void sfx_play(int id) {
    if (sSfxTimer && id < sSfxCur)
        return;
    sSfxCur = id;
    sSfxTimer = 8;
    switch (id) {
        case SFX_SWORD: ch1(0x0039, 0xC180, 0x0600); break;
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
    u16 ime;
    const OriginalSong* song;
    if ((unsigned)id>=BGM_COUNT) id=BGM_NONE;
    if (id==gOriginalMusicBgm) return;
    ime=REG_IME;REG_IME=0;
    sSong=NULL;
    REG_TM0CNT_H=0;
    REG_TM1CNT_H=0;
    REG_DMA1CNT=0;
    REG_SOUNDCNT_H=PCM_FIFO_RESET|2;
    music_channels_off();
    gOriginalMusicBgm=id;
    gOriginalMusicLoops=0;
    gOriginalMusicSamples=gOriginalMusicDmaOffset=0;
    song=&gOriginalSongs[id];
    gOriginalMusicTrack=song->source_id;
    if (song->pcm) {
        sSong=song;
        pcm_begin(song,0);
    }
    REG_IME=ime;
}

void bgm_stop(void) {
    bgm_play(BGM_NONE);
}

void sound_update(void) {
    if (sSfxTimer && --sSfxTimer==0) {
        /* Period0 envelopes hold forever in hardware. End only those notes
           at their declared SFX timeout; naturally decaying tails continue. */
        if (sPulseHeld) {
            REG_SOUND1CNT_H=0;
            REG_SOUND1CNT_X=0x8000;
            sPulseHeld=0;
        }
        if (sNoiseHeld) {
            REG_SOUND4CNT_L=0;
            REG_SOUND4CNT_H=0x8000;
            sNoiseHeld=0;
        }
    }
    /* Music is maintained by the existing VBlank-hook chain. The menu's
       input hook calls its saved hook, so browsing never pauses a track. */
}
