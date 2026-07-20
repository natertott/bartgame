@ Quickstart item-choice NPC dialogue: instructions to pick one item
SCRIPT_START script_QuickStartChooseOne
script_QuickStartChooseOne_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartChooseOne_loop
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_BURLOV, 30
	WaitUntilTextboxCloses
	EnablePlayerControl
	Jump script_QuickStartChooseOne_loop
SCRIPT_END
