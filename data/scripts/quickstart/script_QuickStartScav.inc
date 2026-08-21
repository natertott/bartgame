@ Quickstart scavenger-hunt giver (F1). Same one-NPC-per-run shape as the
@ hunt giver next door in this directory: which region hosts it and where
@ it stands are decided in C (QuickStartScavRollOnce, src/game.c); this
@ script only shows the right line and hands control to C through the
@ script system's condition register.
@
@   QuickStartScavCanStart - TRUE while this NPC still has a chase to give
@                            (and no other timed quest owns the clock)
@   QuickStartScavBegin    - despawns the region's wave, releases the
@                            thief and the slow-you-down swarm, starts the
@                            60-second clock
@
@ The fiction: a Keaton stole the giver's prize. Kill the Keaton within
@ the time and the prize comes back to the giver's spot for you to keep.
SCRIPT_START script_QuickStartScav
script_QuickStartScav_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartScav_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartScavCanStart
	JumpIfNot script_QuickStartScav_spent
	MessageNoOverlap TEXT_CUSTOM, 27
	WaitUntilTextboxCloses
	@ F1c stake announcement - same branch as the hunt giver's.
	Call QuickStartStakeIsNone
	JumpIf script_QuickStartScav_begin
	Call QuickStartStakeIsRupees
	JumpIf script_QuickStartScav_stake1
	Call QuickStartStakeIsHealth
	JumpIf script_QuickStartScav_stake2
	MessageNoOverlap TEXT_CUSTOM, 219
	Jump script_QuickStartScav_stakewait
script_QuickStartScav_stake1:
	MessageNoOverlap TEXT_CUSTOM, 217
	Jump script_QuickStartScav_stakewait
script_QuickStartScav_stake2:
	MessageNoOverlap TEXT_CUSTOM, 218
script_QuickStartScav_stakewait:
	WaitUntilTextboxCloses
script_QuickStartScav_begin:
	Call QuickStartScavBegin
	Jump script_QuickStartScav_done
script_QuickStartScav_spent:
	MessageNoOverlap TEXT_CUSTOM, 30
	WaitUntilTextboxCloses
script_QuickStartScav_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartScav_loop
SCRIPT_END
