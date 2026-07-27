@ Quickstart item-choice NPC dialogue: instructions to pick one item.
@ Genuine custom text via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c) - this used to show
@ TEXT_BURLOV,30, a real, unrelated mid-sentence Carlov/Burlov dialogue
@ fragment ("Now, when you're...") that happened to be reachable, not
@ actual instructions, back before TEXT_CUSTOM existed.
SCRIPT_START script_QuickStartChooseOne
script_QuickStartChooseOne_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartChooseOne_loop
	SetPlayerIdle
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 4
	WaitUntilTextboxCloses
	EnablePlayerControl
	Jump script_QuickStartChooseOne_loop
SCRIPT_END
