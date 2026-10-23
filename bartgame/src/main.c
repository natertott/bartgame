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

int main(void) {
    video_init();
    sound_init();
    tiles_init();
    text_init();
    game_init();
    for (;;) {
        frame_wait();
        video_flush();
        text_flush();
        vram_flush_queue();
        tiles_animate();
        input_read();
        oam_clear();
        game_update();
        fade_update();
        sound_update();
    }
    return 0;
}
