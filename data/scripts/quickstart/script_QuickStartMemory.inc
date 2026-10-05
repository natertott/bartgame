@ Quickstart blink-memory sprites: one script for both rooms, the C decides
@ which room this is (a script .inc cannot read the QUICKSTART tables).
@
@   QuickStartMemoryIsLesson     - TRUE in the lesson room
@   QuickStartMemoryLessonTaught - marks the lesson site DONE for the chain
@   QuickStartMemoryIsSolved     - TRUE once the recital has paid
@
@ The lesson's second line is TEXT_CUSTOM2 24, the old blink puzzle's own
@ ("They blink in an order. Watch it, then say it back to them.").
SCRIPT_START script_QuickStartMemory
script_QuickStartMemory_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartMemory_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartMemoryIsLesson
	JumpIf script_QuickStartMemory_lesson
	Call QuickStartMemoryIsSolved
	JumpIf script_QuickStartMemory_solved
	MessageNoOverlap TEXT_CUSTOM2, 203
	WaitUntilTextboxCloses
	MessageNoOverlap TEXT_CUSTOM2, 204
	WaitUntilTextboxCloses
	Jump script_QuickStartMemory_done
script_QuickStartMemory_lesson:
	MessageNoOverlap TEXT_CUSTOM2, 202
	WaitUntilTextboxCloses
	MessageNoOverlap TEXT_CUSTOM2, 24
	WaitUntilTextboxCloses
	Call QuickStartMemoryLessonTaught
	Jump script_QuickStartMemory_done
script_QuickStartMemory_solved:
	MessageNoOverlap TEXT_CUSTOM2, 205
	WaitUntilTextboxCloses
script_QuickStartMemory_done:
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartMemory_loop
SCRIPT_END
