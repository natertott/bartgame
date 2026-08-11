@ Quickstart hub hint sprites. Six Wind Tribe wanderers scattered through the
@ hub's non-working rooms (tower entrance, Floor 2, and the clifftop by the
@ wind crest); see sQuickStartHubHints in src/game.c for where each one
@ stands and what it is for.
@
@ One script per hint rather than a single script branching on scratch flags.
@ Each is four lines of real work and the whole point is that hint N shows
@ string N - a flag-encoded index would be more machinery than the thing it
@ selects, and script .inc files cannot see game.c's C #defines, so the
@ branch numbers would be bare literals with nothing to check them against.
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c) - strings 20-25, one per hint,
@ in the same order as the table in game.c.

SCRIPT_START script_QuickStartHubHint0
script_QuickStartHubHint0_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint0_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 20
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint0_loop
SCRIPT_END

SCRIPT_START script_QuickStartHubHint1
script_QuickStartHubHint1_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint1_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 21
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint1_loop
SCRIPT_END

SCRIPT_START script_QuickStartHubHint2
script_QuickStartHubHint2_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint2_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 22
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint2_loop
SCRIPT_END

SCRIPT_START script_QuickStartHubHint3
script_QuickStartHubHint3_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint3_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 23
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint3_loop
SCRIPT_END

SCRIPT_START script_QuickStartHubHint4
script_QuickStartHubHint4_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint4_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 24
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint4_loop
SCRIPT_END

SCRIPT_START script_QuickStartHubHint5
script_QuickStartHubHint5_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint5_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 25
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint5_loop
SCRIPT_END
