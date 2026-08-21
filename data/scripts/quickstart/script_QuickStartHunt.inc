@ Quickstart hunt-quest giver. One script, one NPC per run - which region
@ hosts it, where in that region it stands, whether it is the handicap
@ variant, and which weapon that variant leaves you are all decided in C
@ (QuickStartHuntRollOnce, src/game.c) and stored in gSave.timer4, because a
@ script .inc cannot read C state.
@
@ All this script does is show the right line and hand control to C. The
@ branch is on QUICKSTART flag 202+... which a script cannot address either,
@ so the three outcomes are told apart by Call helpers that answer through
@ the script system's own condition register instead:
@
@   QuickStartHuntCanStart  - TRUE when this NPC still has a hunt to give
@   QuickStartHuntIsHandicap - TRUE when the offer is the stripped-kit one
@   QuickStartHuntBegin     - starts the clock, spawns the pack, and (for the
@                             handicap variant) takes the player's kit
@
@ Call sets the condition from the helper's return value, exactly the way
@ ScriptCommand_Call/JumpIf are used together elsewhere in this build, so
@ "Call X / JumpIfNot label" reads as an ordinary if.
SCRIPT_START script_QuickStartHunt
script_QuickStartHunt_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHunt_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartHuntCanStart
	JumpIfNot script_QuickStartHunt_spent
	Call QuickStartHuntIsHandicap
	JumpIf script_QuickStartHunt_handicap
	MessageNoOverlap TEXT_CUSTOM, 15
	Jump script_QuickStartHunt_go
script_QuickStartHunt_handicap:
	MessageNoOverlap TEXT_CUSTOM, 16
script_QuickStartHunt_go:
	WaitUntilTextboxCloses
	@ F1c: the stake is announced before the clock starts. The tier helpers
	@ answer through the condition register like every Call here; tier 3
	@ falls through to the harshest line.
	Call QuickStartStakeIsNone
	JumpIf script_QuickStartHunt_begin
	Call QuickStartStakeIsRupees
	JumpIf script_QuickStartHunt_stake1
	Call QuickStartStakeIsHealth
	JumpIf script_QuickStartHunt_stake2
	MessageNoOverlap TEXT_CUSTOM, 219
	Jump script_QuickStartHunt_stakewait
script_QuickStartHunt_stake1:
	MessageNoOverlap TEXT_CUSTOM, 217
	Jump script_QuickStartHunt_stakewait
script_QuickStartHunt_stake2:
	MessageNoOverlap TEXT_CUSTOM, 218
script_QuickStartHunt_stakewait:
	WaitUntilTextboxCloses
script_QuickStartHunt_begin:
	Call QuickStartHuntBegin
	Jump script_QuickStartHunt_done
script_QuickStartHunt_spent:
	MessageNoOverlap TEXT_CUSTOM, 19
	WaitUntilTextboxCloses
script_QuickStartHunt_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHunt_loop
SCRIPT_END
