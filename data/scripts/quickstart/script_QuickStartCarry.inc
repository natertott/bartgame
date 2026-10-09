@ The carry quest's giver, standing at A with the parcel pot beside them
@ (game.c, "The carry quest, one room"). The Call helpers answer through the
@ condition register:
@
@   QuickStartCarryIsWon     - TRUE once the parcel has been delivered
@   QuickStartCarryCanStart  - TRUE while the ask has not been made
@   QuickStartCarryBegin     - flips the quest ACCEPTED; the parcel appears
@                              on the next frame (QuickStartCarryMonitor)
@
@ Lines (gCustomStrings2): 197-198 the ask, 199 "still waiting", 201 done.
SCRIPT_START script_QuickStartCarry
script_QuickStartCarry_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartCarry_loop
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
script_QuickStartCarry_spent:
	MessageNoOverlap TEXT_CUSTOM2, 201
	WaitUntilTextboxCloses
script_QuickStartCarry_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartCarry_loop
SCRIPT_END
