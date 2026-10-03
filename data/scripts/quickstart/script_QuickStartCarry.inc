@ Quickstart carry-quest giver ("fetch it back to me"). Same shape as the
@ hunt, scavenger and stealth givers: the script shows the right line and
@ hands control to C, because a script .inc cannot read the QUICKSTART flag
@ window. The Call helpers answer through the condition register:
@
@   QuickStartCarryTryDeliver - FIRST, before SetPlayerIdle puts the parcel
@                               down: TRUE (and the quest is paid) when the
@                               player walked up holding the parcel
@   QuickStartCarryIsWon      - TRUE once the parcel has been delivered
@   QuickStartCarryCanStart   - TRUE while the ask has not been made
@   QuickStartCarryBegin      - picks the parcel's region against the kit the
@                               player holds right now and flips the quest
@                               RUNNING; Ezlo names the region on the next
@                               quiet frame (QuickStartCarryMonitor)
SCRIPT_START script_QuickStartCarry
script_QuickStartCarry_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartCarry_loop
	Call QuickStartCarryTryDeliver
	JumpIf script_QuickStartCarry_delivered
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartCarryIsWon
	JumpIf script_QuickStartCarry_spent
	Call QuickStartCarryCanStart
	JumpIfNot script_QuickStartCarry_running
	MessageNoOverlap TEXT_CUSTOM2, 197
	WaitUntilTextboxCloses
	MessageNoOverlap TEXT_CUSTOM2, 198
	WaitUntilTextboxCloses
	Call QuickStartCarryBegin
	Jump script_QuickStartCarry_done
script_QuickStartCarry_running:
	MessageNoOverlap TEXT_CUSTOM2, 199
	WaitUntilTextboxCloses
	Jump script_QuickStartCarry_done
script_QuickStartCarry_delivered:
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM2, 200
	WaitUntilTextboxCloses
	Jump script_QuickStartCarry_done
script_QuickStartCarry_spent:
	MessageNoOverlap TEXT_CUSTOM2, 201
	WaitUntilTextboxCloses
script_QuickStartCarry_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartCarry_loop
SCRIPT_END
