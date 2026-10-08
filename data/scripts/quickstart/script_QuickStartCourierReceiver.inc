@ The courier's receiver: takes the parcel and pays (QuickStartCourierDeliver
@ drops a RARE draw at the player's feet and closes the quest; its condition
@ is FALSE when there is nothing to hand over). Line numbers are
@ gCustomStrings3: 127 "I am waiting for a delivery", 128 "Thank you again".
SCRIPT_START script_QuickStartCourierReceiver
script_QuickStartCourierReceiver_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartCourierReceiver_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartCourierIsDone
	JumpIf script_QuickStartCourierReceiver_spent
	Call QuickStartCourierDeliver
	JumpIfNot script_QuickStartCourierReceiver_waiting
	Call QuickStartCourierSayThanks
	WaitUntilTextboxCloses
	Jump script_QuickStartCourierReceiver_done
script_QuickStartCourierReceiver_waiting:
	MessageNoOverlap TEXT_CUSTOM3, 127
	WaitUntilTextboxCloses
	Jump script_QuickStartCourierReceiver_done
script_QuickStartCourierReceiver_spent:
	MessageNoOverlap TEXT_CUSTOM3, 128
	WaitUntilTextboxCloses
script_QuickStartCourierReceiver_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartCourierReceiver_loop
SCRIPT_END
