@ Cloud Tops Gregal sick
SCRIPT_START script_GregalSick
	BeginBlock
	DoPostScriptAction 0x000a
	SetAnimation 0x0000
	EndBlock
	CheckLocalFlag SORA_ELDER_RECOVER
	JumpIf script_08014BE8
script_08014B48:
	EndBlock
	BeginBlock
	CheckRoomFlag 0x0000
	JumpIf script_08014B70
	CheckEntityInteractType
	JumpIfNot script_08014B48
	EndBlock
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_WIND_TRIBE, 0x01
	WaitUntilTextboxCloses
	Wait 0x000f
	EnablePlayerControl
	Jump script_08014B48
script_08014B70:
	EndBlock
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
.ifdef QUICKSTART
	@ QUICKSTART: the two sync waits here pair with a tribesperson who
	@ switches to script_WindTribespeople6 only while WARP_EVENT_END is
	@ unset (windTribespeople.c) - this mode sets it at run start, and the
	@ hub sweep removes him besides, so the waits would never end. The cure
	@ plays without him.
	DoPostScriptAction 0x0004
	Wait 0x001e
.else
	SetSyncFlag 0x00000001
	DoPostScriptAction 0x0004
	WaitForSyncFlagAndClear 0x00000002
.endif
	SetAnimation 0x0010
	Call sub_0806CCF8
	Wait 0x0014
	Call sub_0806CD04
	Wait 0x0014
	Call sub_0806CD14
	Wait 0x0014
	Call sub_0806CD20
	Wait 0x0014
	Call sub_0806CD30
	Wait 0x0014
	Call sub_0806CD3C
	Wait 0x0014
	Call sub_0806CD4C
	PlaySound SFX_SECRET
.ifndef QUICKSTART
	SetSyncFlag 0x00000001
	WaitForSyncFlagAndClear 0x00000002
.endif
	Call EnablePauseMenu
	EnablePlayerControl
script_08014BE8:
	SetAnimation 0x0010
	Call sub_0806CD4C
script_08014BF2:
	CheckEntityInteractType
	JumpIfNot script_08014BF2
	SetPlayerIdle
	CheckLocalFlag SORA_ELDER_TALK1ST
	JumpIf script_08014C1C
	SetLocalFlag SORA_ELDER_TALK1ST
.ifdef QUICKSTART
	@ QUICKSTART: our thanks and a RARE draw at the feet (game.c,
	@ QuickStartGregalReward) - vanilla's 100 shells would be three seconds
	@ of invincibility in this mode.
	MessageNoOverlap TEXT_CUSTOM3, 129
	WaitUntilTextboxCloses
	Call QuickStartGregalReward
	Jump script_08014C22
.else
	MessageNoOverlap TEXT_WIND_TRIBE, 0x07
	WaitUntilTextboxCloses
	SetIntVariable 100
	GivePlayerItem ITEM_SHELLS
	WaitPlayerGetItem
	Jump script_08014C22
.endif
script_08014C1C:
	MessageNoOverlap TEXT_WIND_TRIBE, 0x08
	WaitUntilTextboxCloses
script_08014C22:
	Wait 0x000f
	EnablePlayerControl
	Jump script_08014BF2
