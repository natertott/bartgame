@ Quickstart Castle Garden ladder mini-dungeon NPC (ladder 2). Same as
@ script_QuickStartLadderNpc0.inc, just this ladder's own flag pair: 0x81
@ (1 = evil, 0 = friendly) and 0x89 (already resolved).
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c) - see script_QuickStartLadderNpc0.inc
@ for why this replaced the old borrowed TEXT_ANJU,0x07 / TEXT_HAPPY_HEARTH,0x08
@ real dialogue lines and their BeginBlock/SetMessageValue dance.
SCRIPT_START script_QuickStartLadderNpc2
script_QuickStartLadderNpc2_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartLadderNpc2_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	CheckGlobalFlag 0x89
	JumpIf script_QuickStartLadderNpc2_already
	CheckGlobalFlag 0x81
	JumpIf script_QuickStartLadderNpc2_evil
	ModRupees 100
	MessageNoOverlap TEXT_CUSTOM, 1
	SetGlobalFlag 0x89
	Jump script_QuickStartLadderNpc2_done
script_QuickStartLadderNpc2_evil:
	ModRupees -100
	MessageNoOverlap TEXT_CUSTOM, 2
	SetGlobalFlag 0x89
	Jump script_QuickStartLadderNpc2_done
script_QuickStartLadderNpc2_already:
	MessageNoOverlap TEXT_CUSTOM, 3
script_QuickStartLadderNpc2_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartLadderNpc2_loop
SCRIPT_END
