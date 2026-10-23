/* BARTGAME: the Blight Heart. Phase 8 fills this in; for now a stub that
   compiles so enemies can link. */
#include "gba.h"
#include "actor.h"
#include "boss.h"

void boss_spawn(int px, int py) {
    (void)px;
    (void)py;
}
void boss_update(Actor* e) {
    (void)e;
}
void boss_draw(Actor* e) {
    actor_draw(e);
}
void boss_defeated(Actor* e) {
    (void)e;
}
void boss_died(Actor* e) {
    (void)e;
}
bool8 boss_is_dying(void) {
    return FALSE;
}
