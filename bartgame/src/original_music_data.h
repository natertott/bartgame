#ifndef ORIGINAL_MUSIC_DATA_H
#define ORIGINAL_MUSIC_DATA_H
#include "gba.h"
#include "sound.h"

/* Native-game recordings imported from forest-art, not new compositions.
   The ROM stream contains signed8-bit mono samples at32768Hz, followed by
   >=8192 bytes of the next loop's musical continuation for safe FIFO prefetch. */
typedef struct {
    const s8* pcm;
    u32 samples, loop_sample;
    u16 total_frames, loop_frame, source_id;
    const char* title;
} OriginalSong;
extern const OriginalSong gOriginalSongs[BGM_COUNT];
#endif
