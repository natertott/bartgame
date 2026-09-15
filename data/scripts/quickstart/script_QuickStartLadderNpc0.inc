@ Quickstart Castle Garden ladder mini-dungeon NPC (ladder 0). Friendly/evil
@ and the one-time-only gate are both decided by QuickStartRandomizeLaddersOnce
@ (src/game.c) and stored as global flags 0x69 (1 = evil, 0 = friendly) and
@ 0x71 (already resolved) - literal numbers here since script .inc files
@ can't see game.c's C #defines. ModRupees clamps at both 0 and the wallet
@ cap (gameUtils.c), so no affordability check is needed before taking.
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c) - this used to borrow real,
@ unrelated vanilla dialogue lines instead (TEXT_ANJU,0x07 and
@ TEXT_HAPPY_HEARTH,0x08), back before TEXT_CUSTOM existed and this
@ project's text was only a compiled binary asset (translations/USA.bin)
@ with no editable source. ModRupees's amount is a fixed 100 in every branch
@ here, so it's written directly into the custom text instead of needing
@ the old ScriptCommand_SetMessageValue/BeginBlock dance real TEXT_ANJU,0x07
@ required for its own {rupees} template slot.
SCRIPT_START script_QuickStartLadderNpc0
script_QuickStartLadderNpc0_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartLadderNpc0_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	CheckGlobalFlag 0x71
	JumpIf script_QuickStartLadderNpc0_already
	CheckGlobalFlag 0x69
	JumpIf script_QuickStartLadderNpc0_evil
	ModRupees 100
	MessageNoOverlap TEXT_CUSTOM, 1
	SetGlobalFlag 0x71
	Jump script_QuickStartLadderNpc0_done
script_QuickStartLadderNpc0_evil:
	ModRupees -100
	MessageNoOverlap TEXT_CUSTOM, 2
	SetGlobalFlag 0x71
	Jump script_QuickStartLadderNpc0_done
script_QuickStartLadderNpc0_already:
	MessageNoOverlap TEXT_CUSTOM, 3
script_QuickStartLadderNpc0_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartLadderNpc0_loop
SCRIPT_END
