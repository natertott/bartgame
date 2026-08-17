@ Quickstart hub hint sprites. Six Wind Tribe wanderers scattered through the
@ hub's non-working rooms (tower entrance, Floor 2, and the clifftop by the
@ wind crest); see sQuickStartHubHints in src/game.c for where each one
@ stands and what it is for.
@
@ One script per hint rather than a single script branching on scratch flags:
@ each spot needs its own script object to attach to, and the scripts are
@ otherwise identical.
@
@ WHICH LINE each one speaks is no longer baked in here. It used to be
@ "hint N shows string N", six MessageNoOverlap literals; F5 replaced that
@ with a pool of eighteen dealt six-at-a-time per run, and a pool is exactly
@ the thing a .inc file cannot see - it lives in game.c next to the spot
@ table it is dealt across. So each script asks for its line instead:
@
@     Call QuickStartHubHintPick   @ sets intVariable from the run's deal
@     MessageNoOverlapVar          @ shows whatever intVariable holds
@
@ QuickStartHubHintPick works out which spot it is speaking for from the
@ NPC's own position, so the six scripts stay interchangeable.
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c).

SCRIPT_START script_QuickStartHubHint0
script_QuickStartHubHint0_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartHubHint0_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	Call QuickStartHubHintPick
	MessageNoOverlapVar
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
	Call QuickStartHubHintPick
	MessageNoOverlapVar
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
	Call QuickStartHubHintPick
	MessageNoOverlapVar
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
	Call QuickStartHubHintPick
	MessageNoOverlapVar
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
	Call QuickStartHubHintPick
	MessageNoOverlapVar
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
	Call QuickStartHubHintPick
	MessageNoOverlapVar
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartHubHint5_loop
SCRIPT_END
