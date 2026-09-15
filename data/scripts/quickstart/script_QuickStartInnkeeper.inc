@ The hub inn's keeper, on Floor 2 of the Home of the Wind Tribe.
@
@ This is vanilla's Happy Hearth Inn machinery, moved. Hyrule Town's inn is
@ run by Emma (npc subtype 0x47, script_Emma, data/scripts/hyruleTown/): the
@ player talks to her, a textbox offers three rooms at three prices, and the
@ choice comes back through _0807EB38 into a JumpTable. That is exactly the
@ interaction this mode's inn wanted and could not get from three beds you
@ had to stand on and press R at - "walking up to the beds and 'talking' to
@ them is not intuitive", per the user, which is fair: nothing else in the
@ game is operated that way.
@
@ What is reused verbatim: Emma herself, the TEXT_HAPPY_HEARTH bank (0x01 the
@ offer with its three-way choice, 0x03/0x04/0x05 the per-room confirms, 0x07
@ "not enough rupees", 0x08 the thank-you, 0x09 the polite decline), and the
@ whole shape of the script including the loop back to the offer after any
@ branch ends.
@
@ What is ours: the three prices, pushed into the message with
@ SetMessageValue exactly as vanilla does (so the numbers on screen are the
@ ones actually charged), and what renting DOES. Vanilla's branches end with
@ Call sub_0806C578/588/598, which walk the player off to the rented bedroom;
@ ours end in QuickStartInnRest{Small,Regular,Large}, which heal and fade on
@ the spot. Vanilla's SetLocalFlag 0x0091 is dropped with them - that is a
@ Hyrule Town story flag and this inn is not part of that story.
@
@ The beds are repeatable here, so every branch loops back to the offer
@ rather than retiring the NPC: the inn is a rupee sink, not a one-shot.
@
@ MessageNoOverlap, not vanilla's MessageFromTarget. MessageFromTarget wants
@ the message-target state a room-data NPC is set up with; on a keeper this
@ mode created the box opened and then never advanced - measured, it sat in
@ state 0x04 on message 0x01 through ten A presses. MessageNoOverlap is the
@ form every other QUICKSTART NPC script already uses.

@ NOTE the preamble vanilla has and this does NOT. script_Emma opens with
@ BeginBlock / _0807E9D4 / DoPostScriptAction 0x0a / SetAnimationState, and
@ uses SetAnimationState around the conversation. All of it assumes an NPC
@ placed by room data with vanilla's own animation set up; on an NPC we
@ created with CreateNPC the script never reached its interact loop at all -
@ measured, the textbox simply never opened. Starting straight at the loop,
@ the way every other QUICKSTART NPC script does, is what makes a
@ transplanted Emma answer.
SCRIPT_START script_QuickStartInnkeeper
script_QuickStartInnkeeper_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartInnkeeper_loop
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	BeginBlock
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x01
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 50
	CallWithArg ScriptCommand_SetMessageValue, (SMV_FIELD_0X14 << 16) | 200
	CallWithArg ScriptCommand_SetMessageValue, (SMV_FIELD_0X18 << 16) | 500
	EndBlock
	WaitUntilTextboxCloses
	_0807EB38
	JumpTable script_QuickStartInnkeeper_decline, script_QuickStartInnkeeper_small, script_QuickStartInnkeeper_regular, script_QuickStartInnkeeper_large

script_QuickStartInnkeeper_small:
	BeginBlock
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x03
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 50
	EndBlock
	WaitUntilTextboxCloses
	HasRupees 50
	JumpIfNot script_QuickStartInnkeeper_broke
	ModRupees -50
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
	WaitUntilTextboxCloses
	Call QuickStartInnRestSmall
	Jump script_QuickStartInnkeeper_done

script_QuickStartInnkeeper_regular:
	BeginBlock
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x04
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 200
	EndBlock
	WaitUntilTextboxCloses
	HasRupees 200
	JumpIfNot script_QuickStartInnkeeper_broke
	ModRupees -200
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
	WaitUntilTextboxCloses
	Call QuickStartInnRestRegular
	Jump script_QuickStartInnkeeper_done

script_QuickStartInnkeeper_large:
	BeginBlock
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x05
	CallWithArg ScriptCommand_SetMessageValue, (SMV_RUPEES << 16) | 500
	EndBlock
	WaitUntilTextboxCloses
	HasRupees 500
	JumpIfNot script_QuickStartInnkeeper_broke
	ModRupees -500
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x08
	WaitUntilTextboxCloses
	Call QuickStartInnRestLarge
	Jump script_QuickStartInnkeeper_done

script_QuickStartInnkeeper_broke:
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x07
	Jump script_QuickStartInnkeeper_done

script_QuickStartInnkeeper_decline:
	MessageNoOverlap TEXT_HAPPY_HEARTH, 0x09

script_QuickStartInnkeeper_done:
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartInnkeeper_loop
SCRIPT_END
