/* Source-mix/instrument comparison: ROM PCM -> DMA1/FIFO A (left) and
   DMA2/FIFO B (right). The PCM contains either the intact source mix or
   the separately reconstructed instruments. timer_reload/sound_bias select the hardware rate
   and DAC mode. Shared hardware-event support remains unused. No sample
   mixer, decoder, sample RAM, heap,
   per-sample interrupt, floating point, or runtime pitch conversion.

   Timer0 uses the source descriptor. Song clocks follow the hardware VBlank
   counter, catching up after a delayed main-loop update; generated PCM
   and event timelines use the GBA's real frame rate.
   DMA1/DMA2 and Timer0 are exclusively owned here; DMA3 remains video's.
   Pulse1/noise retain the original SFX. See soundtrack_data.h for the
   exporter contract and the required end/prefetch padding. */
#include "gba.h"
#include "sound.h"
#include "soundtrack_data.h"

#define REG_FIFO_A REG32(0xA0)
#define REG_FIFO_B REG32(0xA4)
#define REG_DMA1SAD REG32(0xBC)
#define REG_DMA1DAD REG32(0xC0)
#define REG_DMA1CNT REG32(0xC4)
#define REG_DMA2SAD REG32(0xC8)
#define REG_DMA2DAD REG32(0xCC)
#define REG_DMA2CNT REG32(0xD0)
#define PCM_CONTROL 0x120Eu /* PSG100%, A/B100%, A left/B right, sharedTimer0 */
#define PCM_FIFO_RESET 0x8800u
#define PCM_DMA_CONTROL 0xB6400000u /* enable,special,32bit,repeat,dst fixed */

volatile u16 gAudioReviewRequest;
volatile u16 gAudioReviewActive;
volatile u32 gAudioReviewFrame;

/* Defined by video.c in gameplay and by the standalone review player.
   Its ISR increments once per hardware video frame, including overruns. */
extern volatile u32 gFrame;

static const SoundtrackSong* sSong;
static u32 sSongEpoch;
static u16 sEventIndex;
static u8 sSfxTimer;
static u8 sSfxCur;

/* Signed-about-midpoint triangle: a complete 32-sample wave cycle.
   Packed in memory order (GBA CPU is little endian). */
static const u32 sBassWave[4] = {
    0xEFCDAB89, 0x98BADCFE, 0x10325476, 0x67452301
};

static void music_channels_off(void) {
    REG_SOUND2CNT_L = 0;
    REG_SOUND2CNT_H = 0x8000;
    REG_SOUND3CNT_H = 0;
}

/* Repointing is only necessary on start or a song boundary. FIFO reset
   discards old DMA prefetch; padding makes bounded main-loop jitter safe.
   No DMA IRQ and no sample buffer are necessary for this ROM stream. */
static void pcm_start(const signed char* left, const signed char* right,
                      u16 timer_reload, u16 sound_bias) {
    REG_TM0CNT_H = 0;
    REG_DMA1CNT = 0;
    REG_DMA2CNT = 0;
    REG_SOUNDBIAS = sound_bias;
    REG_SOUNDCNT_H = PCM_CONTROL | PCM_FIFO_RESET;
    REG_DMA1SAD = (u32)left;
    REG_DMA1DAD = REG_BASE + 0xA0;
    REG_DMA2SAD = (u32)right;
    REG_DMA2DAD = REG_BASE + 0xA4;
    REG_DMA1CNT = PCM_DMA_CONTROL;
    REG_DMA2CNT = PCM_DMA_CONTROL;
    REG_TM0CNT_L = timer_reload;
    REG_TM0CNT_H = 0x0080;
}

void sound_init(void) {
    REG_TM0CNT_H = 0;
    REG_DMA1CNT = 0;
    REG_DMA2CNT = 0;
    REG_SOUNDCNT_X = 0x0080;
    REG_SOUNDCNT_L = 0xFF77;
    REG_SOUNDCNT_H = PCM_FIFO_RESET | 2; /* reset FIFOs, Direct Sound muted */
    REG_SOUNDBIAS = 0x0200;
    REG_SOUND1CNT_H = 0;
    REG_SOUND1CNT_X = 0x8000;
    REG_SOUND4CNT_L = 0;
    REG_SOUND4CNT_H = 0x8000;
    music_channels_off();
    /* Select playing bank1 while writing inactive bank0, then play bank0. */
    REG_SOUND3CNT_L = 0x0040;
    WAVE_RAM[0] = sBassWave[0];
    WAVE_RAM[1] = sBassWave[1];
    WAVE_RAM[2] = sBassWave[2];
    WAVE_RAM[3] = sBassWave[3];
    REG_SOUND3CNT_L = 0x0080;
    sSong = NULL;
    sSongEpoch = 0;
    sEventIndex = 0;
    sSfxTimer = 0;
    sSfxCur = 0;
    gAudioReviewRequest = 0;
    gAudioReviewActive = 0;
    gAudioReviewFrame = 0;
}

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
    if ((unsigned)id >= SFX_COUNT || id == SFX_NONE)
        return;
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

void bgm_stop(void) {
    REG_TM0CNT_H = 0;
    REG_DMA1CNT = 0;
    REG_DMA2CNT = 0;
    REG_SOUNDCNT_H = PCM_FIFO_RESET | 2;
    music_channels_off();
    /* Noise is exclusively SFX in this engine; leave active effects intact. */
    if (!sSfxTimer) {
        REG_SOUND4CNT_L = 0;
        REG_SOUND4CNT_H = 0x8000;
    }
    sSong = NULL;
    gAudioReviewActive = 0;
    gAudioReviewFrame = 0;
    sSongEpoch = 0;
    sEventIndex = 0;
}

void bgm_play(int id) {
    if ((unsigned)id >= BGM_COUNT)
        return;
    if (id == BGM_NONE) {
        bgm_stop();
        return;
    }
    if (id == gAudioReviewActive)
        return;
    const SoundtrackSong* song = &gSoundtrackSongs[id];
    if (!song->pcmL || !song->pcmR || !song->total_frames)
        return;
    music_channels_off();
    sSong = song;
    sSongEpoch = gFrame;
    sEventIndex = 0;
    gAudioReviewActive = id;
    gAudioReviewFrame = 0;
    pcm_start(song->pcmL, song->pcmR, song->timer_reload, song->sound_bias);
}

void sound_update(void) {
    if (sSfxTimer && --sSfxTimer == 0) {
        REG_SOUND1CNT_H = 0;
        REG_SOUND1CNT_X = 0x8000;
        REG_SOUND4CNT_L = 0;
        REG_SOUND4CNT_H = 0x8000;
    }
    /* A RAM mailbox lets the audio review harness select music while
       running the same compiled driver and data as the gameplay ROM. */
    u16 request = gAudioReviewRequest;
    if (request) {
        gAudioReviewRequest = 0;
        if (request == 0xFFFF) {
            bgm_stop();
        } else if (request < BGM_COUNT) {
            /* Review requests intentionally restart even the current song. */
            bgm_stop();
            bgm_play(request);
        }
    }
    const SoundtrackSong* song = sSong;
    if (!song)
        return;
    u32 now = gFrame;
    u32 frame = now - sSongEpoch;
    u16 index = sEventIndex;
    if (frame >= song->total_frames) {
        frame = song->loop_frame;
        sSongEpoch = now - frame;
        index = song->loop_event;
        music_channels_off();
        pcm_start(song->pcmL + song->pcm_loop_offset,
                  song->pcmR + song->pcm_loop_offset,
                  song->timer_reload, song->sound_bias);
    }
    while (index < song->event_count) {
        const SoundtrackEvent* event = &song->events[index];
        if (event->frame > frame)
            break;
        if (event->channel == 2) {
            REG_SOUND2CNT_L = event->env;
            REG_SOUND2CNT_H = event->env ? event->reg : 0x8000;
        } else if (event->channel == 3) {
            REG_SOUND3CNT_H = event->env;
            if (event->env)
                REG_SOUND3CNT_X = event->reg;
        }
        ++index;
    }
    sEventIndex = index;
    gAudioReviewFrame = frame;
}
