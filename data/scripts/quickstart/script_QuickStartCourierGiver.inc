@ The courier's giver (Oct 2026, the redesign's P2 section 6.2): a vanilla
@ delivery errand handed over as a quest. Same shape as the carry giver -
@ the script picks the line, C holds the state:
@
@   QuickStartCourierCanStart   - TRUE while the parcel has not been taken
@   QuickStartCourierSayOffer   - opens the skin's offer (the errand's own
@                                 words: the Smith's sword, a library book,
@                                 the Wake-Up Mushroom)
@   QuickStartCourierBegin      - picks the receiver's region against the
@                                 kit held now and starts the carry; Ezlo
@                                 names the region on the next quiet frame
@   QuickStartCourierIsDone     - TRUE once delivered
SCRIPT_START script_QuickStartCourierGiver
script_QuickStartCourierGiver_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartCourierGiver_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartCourierIsDone
	JumpIf script_QuickStartCourierGiver_spent
	Call QuickStartCourierCanStart
	JumpIfNot script_QuickStartCourierGiver_waiting
	Call QuickStartCourierSayOffer
	WaitUntilTextboxCloses
	Call QuickStartCourierBegin
	Jump script_QuickStartCourierGiver_done
script_QuickStartCourierGiver_waiting:
	MessageNoOverlap TEXT_CUSTOM3, 126
	WaitUntilTextboxCloses
	Jump script_QuickStartCourierGiver_done
script_QuickStartCourierGiver_spent:
	MessageNoOverlap TEXT_CUSTOM3, 128
	WaitUntilTextboxCloses
script_QuickStartCourierGiver_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartCourierGiver_loop
SCRIPT_END
