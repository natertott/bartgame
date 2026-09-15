@ Quickstart Kinstone fuser. One script, every fuser - unlike the vanilla
@ fuser scripts (e.g. script_CastorWildsStatueLeft) this one does NOT name a
@ kinstone id, because there are eighteen of them and a script .inc cannot
@ read C state. src/game.c registers the interaction itself with
@ AddInteractableFuser(npc, kinstoneId) (QuickStartMakeNpcFuser), so all this
@ script has to do is drive the fuse state machine once the player presses L.
@
@ _0807EA4C is ScriptCommand_0807EA4C: when interactType is INTERACTION_FUSE
@ it calls InitializeFuseInfo(entity, 0, 0, 0) - the three zeros are the
@ "here is my offer" / "maybe another time" / "let us fuse" text ids, and
@ zero means say nothing, which is what we want from a wordless roadside
@ fusion stone. Any other interactType makes it set commandSize = 0, i.e.
@ stay parked on this command and re-check next frame, so this doubles as
@ the idle wait loop.
@
@ UpdateFusion then runs PerformFuseAction every frame until the kinstone
@ menu resolves. On success the engine has already written the fused bit
@ (KinstoneMenu_Type5_Overlay0), played the world-event cutscene, and set
@ this candidate's kinstoneId to KINSTONE_NEEDS_REPLACEMENT
@ (NotifyFusersOnFusionDone) so the fuser stops offering - nothing left for
@ the script to do either way, so both outcomes just loop back round.
SCRIPT_START script_QuickStartFuser
script_QuickStartFuser_loop:
	_0807EA4C
	UpdateFusion
	SetPlayerIdle
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartFuser_loop
SCRIPT_END
