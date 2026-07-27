@ Quickstart Melari's Mine merchant: real vanilla pick-up -> talk -> buy shop
@ UX (the same one Stockwell/Goron Merchant use), not a per-item dialogue
@ menu. The catalog is displayed as liftable SHOP_ITEM pedestal props
@ (spawned/restocked by QuickStartMaintainMelarisMineShop in game.c) - the
@ player carries one over and this script completes the sale using the
@ same ScriptCommand_SaleItemConfirmMessage / CheckShopItemPrice /
@ BuyShopItem trio Beedle and Talon's own scripts use, called with arg 0 so
@ each reads gRoomVars.shopItemType (whatever's currently being carried)
@ instead of a hardcoded item.
@
@ HasRoomItemForSale MUST be checked before anything that can drop a held
@ object - DisablePauseMenuAndPutAwayItems calls PlayerDropHeldObject(),
@ and dropping a SHOP_ITEM entity clears gRoomVars.shopItemType right back
@ to 0 (see sub_080819B4 in itemForSale.c). An earlier version of this
@ script called DisablePauseMenuAndPutAwayItems unconditionally as its
@ first step (copied from the old dialogue-only merchant, which never had
@ anything to drop), so it always dropped whatever the player was carrying
@ before ever checking if there was something to sell - the merchant would
@ always fall through to the generic "nothing for sale" message even while
@ visibly holding an item. Fixed by checking HasRoomItemForSale first and
@ only calling DisablePauseMenu (not …AndPutAwayItems) in the sell branch -
@ mirrors script_GoronMerchant.inc exactly.
@
@ script_QuickStartMerchant_done unconditionally calls
@ ScriptCommand_PlayerDropHeldObject - same shared cleanup spot
@ script_GoronMerchant.inc uses (its script_080108B2) after either a
@ completed sale, a declined one, or an unaffordable one. Dropping the held
@ object is what makes the SHOP_ITEM entity's own per-frame check in
@ ItemForSale_Action2 (heldObject == 0) fire sub_080819B4: if
@ gRoomVars.shopItemType is already 0 (BuyShopItem cleared it - the sale
@ went through) it deletes the now-consumed prop, which
@ QuickStartMaintainMelarisMineShop then restocks; otherwise (declined, or
@ CheckShopItemPrice failed for insufficient rupees, in which case
@ shopItemType was never cleared) it instead resets the prop back to its
@ original pedestal position - the item is handed back rather than lost.
@
@ Text: genuine custom dialogue via TEXT_CUSTOM (see gCustomStrings, game.c;
@ TEXT_CUSTOM/sub_0805EEB4, message.h/text.c). The greeting used to show
@ TEXT_BURLOV,30, the same borrowed, unrelated mid-sentence Carlov/Burlov
@ fragment ("Now, when you're...") the item-choice sign used before it got
@ its own custom text; the "can't afford it" line used TEXT_PICOLYTE,0x09, a
@ real Picolyte-shop line that's equally out of context here.
SCRIPT_START script_QuickStartMerchant
script_QuickStartMerchant_loop:
	CheckEntityInteractType
	JumpIfNot script_QuickStartMerchant_loop
	HasRoomItemForSale
	JumpIf script_QuickStartMerchant_sell
	SetPlayerIdle
	Call DisablePauseMenuAndPutAwayItems
	FacePlayer
	MessageNoOverlap TEXT_CUSTOM, 6
	Jump script_QuickStartMerchant_done
script_QuickStartMerchant_sell:
	SetPlayerIdle
	Call DisablePauseMenu
	FacePlayer
	CallWithArg ScriptCommand_SaleItemConfirmMessage, 0x00000000
	WaitUntilTextboxCloses
	CheckTextboxResult
	JumpIfNot script_QuickStartMerchant_done
	CallWithArg ScriptCommand_CheckShopItemPrice, 0x00000000
	JumpIfNot script_QuickStartMerchant_cant_afford
	CallWithArg ScriptCommand_BuyShopItem, 0x00000000
	WaitPlayerGetItem
	Jump script_QuickStartMerchant_done
script_QuickStartMerchant_cant_afford:
	MessageNoOverlap TEXT_CUSTOM, 7
	WaitUntilTextboxCloses
script_QuickStartMerchant_done:
	Call ScriptCommand_PlayerDropHeldObject
	WaitUntilTextboxCloses
	Call EnablePauseMenu
	EnablePlayerControl
	Jump script_QuickStartMerchant_loop
SCRIPT_END
