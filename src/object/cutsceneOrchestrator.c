/**
 * @file cutsceneOrchestrator.c
 * @ingroup Objects
 *
 * @brief Cutscene Orchestrator object
 */
#include "entity.h"
#include "script.h"
#include "hitbox.h"
#ifdef QUICKSTART
#include "area.h"
#include "room.h"
#include "roomid.h"
#endif

void CutsceneOrchestrator(Entity* this) {
#ifdef QUICKSTART
    // The two Great Fairy fountains the mode keeps vanilla (Minish Woods and
    // Mount Crenel) are the exception: there the orchestrator IS the fairy -
    // script_GreatFairyBombs / script_GreatFairyRupees wait on the bomb or
    // the rupees, raise her, ask the question and pay out (game.c
    // QuickStartFairyHonestyReward). Deleting it left a fairy who never
    // woke up, measured in the emulator: both rooms held the GREAT_FAIRY
    // object and no orchestrator. The graveyard fountain is NOT excepted;
    // it hosts the Fountain of Sacrifice instead.
    if (gRoomControls.area == AREA_GREAT_FAIRIES &&
        (gRoomControls.room == ROOM_GREAT_FAIRIES_MINISH_WOODS || gRoomControls.room == ROOM_GREAT_FAIRIES_CRENEL)) {
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
        return;
    }
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
