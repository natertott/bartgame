/* The Drain's Cream exit uses the same native stamp as the Forest ladder. */
#include "hub_services.h"
#include "game.h"
#include "room.h"

void hub_services_build(void) {
    int x,y;
    u16 ground[15],overlay[15];
    if(gGame.area!=AREA_SEWER)return;
    /* Copy before writing, so the placement remains independent of the
       relative source/destination. Exact metatile IDs retain native pixels,
       timing, palette, collision and the ladder's recognizable up arrow. */
    for(y=0;y<5;y++)for(x=0;x<3;x++) {
        ground[y*3+x]=room_get(8+x,y);
        overlay[y*3+x]=room_get_overlay(8+x,y);
    }
    for(y=0;y<5;y++)for(x=0;x<3;x++) {
        room_set(18+x,y,ground[y*3+x]);
        room_set_overlay(18+x,y,overlay[y*3+x]);
    }
    room_render();
}
