@ Quickstart Castle Garden ladder mini-dungeon NPC (ladder 2). Same as
@ script_QuickStartLadderNpc0.inc, just this ladder's own flag pair: 0x81
@ (1 = evil, 0 = friendly) and 0x89 (already resolved). See
@ script_QuickStartLadderNpc1.inc for why TEXT_ANJU,0x07 / TEXT_HAPPY_HEARTH,
@ 0x08 replaced the old TEXT_BURLOV,30/31 (real, unrelated dialogue
@ fragments) and why the SetMessageValue call needs its own BeginBlock.
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
	BeginBlock
	MessageNoOverlap TEXT_ANJU, 0x07
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 100
	EndBlock
	SetGlobalFlag 0x89
	Jump script_QuickStartLadderNpc2_done
script_QuickStartLadderNpc2_evil:
	ModRupees -100
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
	SetGlobalFlag 0x89
	Jump script_QuickStartLadderNpc2_done
script_QuickStartLadderNpc2_already:
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
script_QuickStartLadderNpc2_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartLadderNpc2_loop
SCRIPT_END
