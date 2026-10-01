@ QUICKSTART hub sign, after the third and last item pick. The same ZELDA
@ sign that said "Choose one of these items!" through the three rounds
@ stays in the room (it used to be deleted with the row, which read as the
@ sprite vanishing the moment the skill was taken) and says goodbye instead.
SCRIPT_START script_QuickStartChosen
script_QuickStartChosen_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartChosen_loop
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM2, 194
	WaitUntilTextboxCloses
	EnablePlayerControl
	Jump script_QuickStartChosen_loop
SCRIPT_END
