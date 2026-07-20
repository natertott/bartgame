/**
 * @file cutsceneOrchestrator.c
 * @ingroup Objects
 *
 * @brief Cutscene Orchestrator object
 */
#include "entity.h"
#include "script.h"
#include "hitbox.h"

void CutsceneOrchestrator(Entity* this) {
#ifdef QUICKSTART
    // Castor Darknut Main's default entity set (see sub_unk3_CastorDarknut_Main
    // in roomInit.c, selected whenever LV4_0a_TSUBO is unset - always true for
    // a fresh QUICKSTART boot) spawns this to drive
    // script_CutsceneOrchestratorDarknutFight: a locked-door miniboss
    // encounter with its own camera/script state machine, exactly the kind of
    // half-executed cutscene that made Castle Garden unusable as a sandbox.
    // Keep this room as a clean space for our own item/combat loop instead.
    DeleteThisEntity();
    return;
#endif
    if ((this->flags & ENT_SCRIPTED) != 0) {
        if (this->action == 0) {
            this->action = 1;
            this->hitbox = (Hitbox*)&gHitbox_2;
            InitScriptForNPC(this);
        } else {
            ExecuteScriptAndHandleAnimation(this, NULL);
        }
    } else {
        this->action = 1;
    }
}
