@ Quickstart stealth-quest giver (F2, "the watch"). Same shape as the hunt
@ and scavenger givers: the script shows the right line and hands control to
@ C, because a script .inc cannot read the QUICKSTART flag window. The Call
@ helpers answer through the script system's own condition register:
@
@   QuickStartStealthCanStart - TRUE when this NPC still has a watch to set
@   QuickStartStealthBegin    - starts the clock and flips the quest RUNNING;
@                               the watchmen and the partner are placed by
@                               QuickStartStealthMonitor on the next frame,
@                               which is also what re-places them after a
@                               room reload
@
@ The stake announcement is the shared F1c block - same three lines every
@ timed quest uses (TEXT_CUSTOM 217-219), so a player learns the stake
@ vocabulary once.
SCRIPT_START script_QuickStartStealth
script_QuickStartStealth_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartStealth_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartStealthCanStart
	JumpIfNot script_QuickStartStealth_spent
	MessageNoOverlap TEXT_CUSTOM2, 18
	WaitUntilTextboxCloses
	MessageNoOverlap TEXT_CUSTOM2, 23
	WaitUntilTextboxCloses
	Call QuickStartStakeIsNone
	JumpIf script_QuickStartStealth_begin
	Call QuickStartStakeIsRupees
	JumpIf script_QuickStartStealth_stake1
	Call QuickStartStakeIsHealth
	JumpIf script_QuickStartStealth_stake2
	MessageNoOverlap TEXT_CUSTOM, 219
	Jump script_QuickStartStealth_stakewait
script_QuickStartStealth_stake1:
	MessageNoOverlap TEXT_CUSTOM, 217
	Jump script_QuickStartStealth_stakewait
script_QuickStartStealth_stake2:
	MessageNoOverlap TEXT_CUSTOM, 218
script_QuickStartStealth_stakewait:
	WaitUntilTextboxCloses
script_QuickStartStealth_begin:
	Call QuickStartStealthBegin
	Jump script_QuickStartStealth_done
script_QuickStartStealth_spent:
	MessageNoOverlap TEXT_CUSTOM2, 22
	WaitUntilTextboxCloses
script_QuickStartStealth_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartStealth_loop
SCRIPT_END
