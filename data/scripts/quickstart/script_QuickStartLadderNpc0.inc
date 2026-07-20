@ Quickstart Castle Garden ladder mini-dungeon NPC (ladder 0). Friendly/evil
@ and the one-time-only gate are both decided by QuickStartRandomizeLaddersOnce
@ (src/game.c) and stored as global flags 0x69 (1 = evil, 0 = friendly) and
@ 0x71 (already resolved) - literal numbers here since script .inc files
@ can't see game.c's C #defines. ModRupees clamps at both 0 and the wallet
@ cap (gameUtils.c), so no affordability check is needed before taking.
@
@ Text: TEXT_BURLOV,30/31 turned out to be real, unrelated mid-sentence
@ Carlov/Burlov dialogue fragments (verified by screenshotting them in the
@ emulator - they read like "Now, when you're..." with no connection to
@ rupees at all), not safe placeholder text - this project's text is a
@ compiled binary asset (translations/USA.bin) with no editable source, so
@ new custom strings can't be authored; every index belongs to some real
@ NPC's real dialogue. TEXT_ANJU,0x07 is Anju's cucco-minigame rupee-prize
@ line ("You got {rupees} Rupees! ...") - it already carries a {rupees}
@ template slot (see gMessage.rupees in ScriptCommand_SetMessageValue,
@ script.c) intended for exactly this kind of dynamic amount, so it reads
@ correctly regardless of context. TEXT_HAPPY_HEARTH,0x08 is Emma's shared
@ "payment accepted" line, reused as-is (both her inn scripts show it after
@ two different rupee amounts already, so it's meant to be amount-agnostic).
@ SetMessageValue's CallWithArg must be wrapped in the same BeginBlock as
@ the preceding MessageNoOverlap (copied from script_RentSmallRoom.inc/
@ script_MalonHyruleTown.inc) - unlike a plain sequence of script lines,
@ BeginBlock/EndBlock is what makes MessageNoOverlap and the value it reads
@ resolve on the same step; without it the message renders before the
@ value is set and displays "0" instead of the real amount (confirmed by
@ screenshotting both orderings).
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
	BeginBlock
	MessageNoOverlap TEXT_ANJU, 0x07
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 100
	EndBlock
	SetGlobalFlag 0x71
	Jump script_QuickStartLadderNpc0_done
script_QuickStartLadderNpc0_evil:
	ModRupees -100
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
	SetGlobalFlag 0x71
	Jump script_QuickStartLadderNpc0_done
script_QuickStartLadderNpc0_already:
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
script_QuickStartLadderNpc0_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartLadderNpc0_loop
SCRIPT_END
