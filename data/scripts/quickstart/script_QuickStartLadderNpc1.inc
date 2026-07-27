@ Quickstart Castle Garden ladder mini-dungeon NPC (ladder 1). Same as
@ script_QuickStartLadderNpc0.inc, just this ladder's own flag pair: 0x75
@ (1 = evil, 0 = friendly) and 0x7d (already resolved).
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c) - see script_QuickStartLadderNpc0.inc
@ for why this replaced the old borrowed TEXT_ANJU,0x07 / TEXT_HAPPY_HEARTH,0x08
@ real dialogue lines and their BeginBlock/SetMessageValue dance.
SCRIPT_START script_QuickStartLadderNpc1
script_QuickStartLadderNpc1_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartLadderNpc1_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	CheckGlobalFlag 0x7d
	JumpIf script_QuickStartLadderNpc1_already
	CheckGlobalFlag 0x75
	JumpIf script_QuickStartLadderNpc1_evil
	ModRupees 100
	MessageNoOverlap TEXT_CUSTOM, 1
	SetGlobalFlag 0x7d
	Jump script_QuickStartLadderNpc1_done
script_QuickStartLadderNpc1_evil:
	ModRupees -100
	MessageNoOverlap TEXT_CUSTOM, 2
	SetGlobalFlag 0x7d
	Jump script_QuickStartLadderNpc1_done
script_QuickStartLadderNpc1_already:
	MessageNoOverlap TEXT_CUSTOM, 3
script_QuickStartLadderNpc1_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartLadderNpc1_loop
SCRIPT_END
