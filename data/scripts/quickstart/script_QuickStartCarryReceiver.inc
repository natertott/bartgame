@ The carry quest's receiver, standing at B. Walking up with the parcel
@ delivers by itself (QuickStartCarryMonitor's proximity test); a talk
@ while holding it delivers too:
@
@   QuickStartCarryTryDeliver - FIRST, before SetPlayerIdle puts the pot
@                               down: TRUE (and paid) when the player holds
@                               the parcel
@   QuickStartCarryIsWon      - TRUE once delivered
@
@ Lines: gCustomStrings2 200 thanks, 201 done; gCustomStrings3 130 waiting
@ (QUICKSTART_CARRY_RECEIVER_TEXT).
SCRIPT_START script_QuickStartCarryReceiver
script_QuickStartCarryReceiver_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartCarryReceiver_loop
	Call QuickStartCarryTryDeliver
	JumpIf script_QuickStartCarryReceiver_delivered
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartCarryIsWon
	JumpIf script_QuickStartCarryReceiver_spent
	MessageNoOverlap TEXT_CUSTOM3, 130
	WaitUntilTextboxCloses
	Jump script_QuickStartCarryReceiver_done
script_QuickStartCarryReceiver_delivered:
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM2, 200
	WaitUntilTextboxCloses
	Jump script_QuickStartCarryReceiver_done
script_QuickStartCarryReceiver_spent:
	MessageNoOverlap TEXT_CUSTOM2, 201
	WaitUntilTextboxCloses
script_QuickStartCarryReceiver_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartCarryReceiver_loop
SCRIPT_END
