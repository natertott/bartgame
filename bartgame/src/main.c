/* BARTGAME entry: init, then the frame loop. Logic runs during the frame
   and everything the frame prepared is pushed at the next VBlank. */
#include "gba.h"
#include "video.h"
#include "room.h"
#include "actor.h"
#include "player.h"
#include "sound.h"
#include "text.h"
#include "game.h"
#include "performance.h"

int main(void) {
    video_init();
    sound_init();
    tiles_init();
    text_init();
    perf_init();
    game_init();
    for (;;) {
        frame_wait();
        perf_frame_begin();
        PERF_CALL(PF_VIDEO,video_flush());
        PERF_CALL(PF_TEXT_FLUSH,text_flush());
        PERF_CALL(PF_UPLOAD,vram_flush_queue());
        PERF_CALL(PF_TILE_ANIMATION,tiles_animate());
        PERF_CALL(PF_INPUT,input_read());
        oam_clear();
        PERF_CALL(PF_GAME,game_update());
        fade_update();
        PERF_CALL(PF_SOUND,sound_update());
        perf_frame_end();
    }
    return 0;
}
