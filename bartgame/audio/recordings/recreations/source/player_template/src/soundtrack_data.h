#ifndef SOUNDTRACK_DATA_H
#define SOUNDTRACK_DATA_H
#include "gba.h"

/* Optional event fields retained for the shared driver interface. Direct
   source-audio playback sets events=NULL,event_count=0. */
typedef struct SoundtrackEvent {
    u16 frame;
    u16 reg;
    u16 env;
    u8 channel;
    u8 unused;
} SoundtrackEvent;

typedef struct SoundtrackSong {
    const signed char* pcmL;
    const signed char* pcmR;
    const SoundtrackEvent* events;
    u16 event_count;
    u16 total_frames;
    u16 loop_frame;
    u16 loop_event;
    u32 pcm_loop_offset;
    const char* title;
    u16 timer_reload;
    u16 sound_bias;
} SoundtrackSong;

/* Slot0=silence,slot1=one complete uploaded source recording.
   PCM streams are separate signed8-bit L/R planes, each aligned16B.
   Both streams have the same length, >=8192 trailing zero guard samples,
   the same four-byte-aligned pcm_loop_offset. Streams play directly from
   ROM via DMA1/FIFO_A(left), DMA2/FIFO_B(right), with shared Timer0.
   total_frames and all event times use16777216/280896Hz video timing.
   Set total_frames=ceil(source_seconds*16777216/280896),loop_frame=0,
   loop_event=0,pcm_loop_offset=0. Zero pad from the true source ending to
   this frame boundary before adding the guards. No PSG events are used.
   The effective sample rate is16777216/(65536-timer_reload), not an
   arbitrary integer rate. Resample source audio to that hardware clock
   offline, preserving pitch and duration. Preferred synchronized modes:
   timer_reload=0xFF00,bias=0x4200 gives65536Hz samples and8-bit/65536Hz PWM;
   timer_reload=0xFE00,bias=0x0200 gives32768Hz samples and9-bit/32768Hz PWM.
   Asynchronous timer/PWM rates introduce audible timing distortion and
   must not be selected merely to save cartridge bytes.
   title should begin with its source code, e.g."R01 - Source title".
   The caller must update sound once per frame; guard bounds cover <=3
   delayed frames plus FIFO prefetch, not arbitrary main-loop stalls. */
extern const SoundtrackSong gSoundtrackSongs[2];
#endif
