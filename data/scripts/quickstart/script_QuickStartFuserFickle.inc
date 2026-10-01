@ Quickstart Kinstone fuser who is NOT in the mood. Vanilla's own fickleness
@ (GetFusionToOffer rolls fuserStability against Random() % 100 and refuses),
@ carried over to this mode's placed fusers and scaled by difficulty:
@ QuickStartSpawnRegionFusers rolls each fuser once as it is created, and a
@ fuser that loses the roll is made talkable with this script instead of
@ being registered as a fusion (QuickStartMakeNpcTalkable rather than
@ QuickStartMakeNpcFuser). Same face, same spot - only the L prompt is gone.
@ Leave the room and come back and the roll is fresh, which is exactly how
@ vanilla's fickle fusers behave ("exit the school and re-enter it until she
@ does"). The first fuser placed in a room is never fickle, so a region
@ always has at least one gate on offer.
SCRIPT_START script_QuickStartFuserFickle
script_QuickStartFuserFickle_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartFuserFickle_loop
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM2, 189
	WaitUntilTextboxCloses
	EnablePlayerControl
	Jump script_QuickStartFuserFickle_loop
SCRIPT_END
