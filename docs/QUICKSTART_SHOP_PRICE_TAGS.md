# Showing shop prices without talking to the shopkeeper

Research answer for "can each item in the store display its cost in the
room?". Short version: **yes, and the cheapest route is genuinely cheap** -
because the shop room does not scroll.

## What exists today

- Prices are per-run rolls (`GF_SHOP_PRICE_BIT`, game.c) read back through
  `QuickStartGetShopPrice`, which `GetItemPrice` (itemUtils.c) calls.
- The player learns a price only by carrying an item to the merchant and
  reading `ScriptCommand_SaleItemConfirmMessage`'s textbox. That is one
  round trip per item, times nine items.
- The stock sits on three shelves at nine fixed offsets
  (`sQuickStartShopRoomItemOffsets`), all inside a single 240x160 screen.

## The three ways to draw a number

### 1. BG0 tile writes - recommended

`RenderDigits(iconVramIndex, count, isTextYellow, digits)` (ui.c) already
draws a rupee icon plus a right-aligned number into `gBG0Buffer`, which is
the HUD's own background layer. `DrawRupees` and `DrawKeys` are its only
callers today; nothing about it is rupee-specific.

BG0 is screen space, not world space, so a tile written at a given position
stays put while the world scrolls. Normally that rules it out for labelling
a thing in the room - but the shop is one non-scrolling screen, so every
shelf is always at the same screen tile. A nine-entry table of BG0 offsets,
written once on room entry and cleared on exit, puts a price under each
item and never has to track the camera.

- Cost: one table of nine `u16` offsets, one function, no new art (the digit
  and rupee-icon tiles are already resident for the HUD), no entity slots,
  no GFX slots.
- Risk: BG0 is shared with the HUD. The rupee counter lives at buffer
  offsets 0x258/0x278 (bottom right); the shelves are in the upper two
  thirds, so there is room, but the exact offsets need measuring against a
  real frame rather than derived on paper.
- Caveat to confirm first: that the room truly never scrolls. Every shop
  offset in the table is inside 240x160, which is strong evidence, but
  `room_dims` on the live room settles it in one boot.

### 2. OAM sprites parented to each item

Draw the digits as sprites positioned from each `SHOP_ITEM` entity's own
world coordinates, the way `ItemUIElement` parents the HUD item icon to its
button plate.

- Works in any room, scrolling or not - the only option if prices are ever
  wanted on items outside the shop.
- Costs OAM entries and at least one GFX slot for a digit sheet, and the
  budget work says never to spend a slot casually. In the shop specifically
  the room is otherwise empty, so it would fit; the objection is that it
  buys nothing over option 1 there.

### 3. A price sign per shelf, read by walking into it

Three signs, each naming its shelf's three prices in a textbox. Reuses the
? room sign NPC verbatim - no new mechanism at all.

- Cheapest to build by a wide margin, and it fits the game's own idiom.
- But it is still "read a textbox to learn a price", which is most of what
  the request is trying to get away from. Worth having as a fallback if the
  BG0 offsets turn out to collide with the HUD.

## Recommendation

Option 1. It is the only one that puts the number where the eye already is,
it reuses `RenderDigits` as-is, and it spends no entity or GFX budget - which
matters, because the fusers just took the last comfortable GFX slot in South
Hyrule Field.

Sequence: confirm the room does not scroll; measure the nine BG0 tile
offsets against a captured frame; write and clear them from the shop's own
room monitor. Add a checker assertion that no price offset lands on the
rupee counter's own tiles.

## Related: the rupee counter during the sale

Already fixed - `QuickStartShopShowRupees` (game.c), called from both
branches of `script_QuickStartMerchant`. The vanilla `DisablePauseMenu`
helpers blank the whole HUD for the length of a conversation, which took the
rupee count away at exactly the moment the player is deciding whether they
can afford something. The helper puts that one bit back and leaves the rest
hidden.
