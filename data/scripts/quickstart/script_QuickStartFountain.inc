@ The Fountain of Sacrifice's asking sprite (game.c QuickStartSacrificeMonitor).
@ One custom line explaining the deal; the mechanic itself is carry-driven,
@ so the sprite only ever talks.
SCRIPT_START script_QuickStartFountain
script_QuickStartFountain_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartFountain_loop
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 229
	WaitUntilTextboxCloses
	EnablePlayerControl
	Jump script_QuickStartFountain_loop
SCRIPT_END
