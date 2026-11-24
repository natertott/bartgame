# Bloom’s combat and controls

The original handoff calls for an independent GBA engine with Minish Cap movement,
item controls, and collision behavior. The action timings and collision model in
this pass follow that handoff. Bloom’s poses, tools, enemies, and generated rooms
provide the game-specific silhouettes and targets. [Original handoff](../../docs/newgame/00_README.md) · [Player and movement](../../docs/newgame/02_PLAYER_AND_MOVEMENT.md) · [From-scratch engine](../../docs/newgame/12_FROM_SCRATCH_ENGINE.md) · [Entities and damage](../../docs/newgame/04_ENTITIES_ENEMIES_OBJECTS.md) · [Items](../../docs/newgame/05_ITEMS_AND_ECONOMY.md)

## Reference behavior

| Game | Ordinary ground sword | Movement and equipment |
| --- | --- | --- |
| The Minish Cap | The original swing has 15 finite animation updates. A child weapon derives its offset and half-extents from the current pose and facing. At age three its center travels north, east, south or west of Link according to the respective animation. Tile reaction uses a separate pose cue. | Eight-direction travel and four-direction facing, with a normal walk at 1.25 px per update and guard at 0.75. R roll speed and protection come from animation cues. Equipped sword techniques have their own input windows during a roll, charge or dash. |
| Oracle of Ages and Seasons | The ordinary script has holds of 3, 3, 8 and 3 updates. The blade moves through facing-specific offsets with independent X and Y collision radii. The item table also checks elevation. | Eight travel angles use 1 px per update on clear ground, 0.75 in grass and 0.5 on stairs. A and B dispatch separate item behaviors. Walking with an extended sword holds facing. Pegasus Seeds can accelerate a Roc’s Feather jump. |
| Link’s Awakening DX | The draw, start and middle sword states load timers of 3, 3 and 8. Facing and sword state index body pose, blade pose and contact offsets together. The middle shape is wider east and west than north and south. | Ordinary walking uses 1 px per update cardinally and 0.75 per axis diagonally. The grounded swing commits facing and position. Held shield and Pegasus Boots input is read separately from new item presses. Boots can extend Feather travel or carry an equipped sword thrust. |

Source measurements come from the original USA Minish Cap animation data and
the decompilation’s animation, item and collision routines. The Oracle and Link’s
Awakening comparisons use pinned disassembly sources. [Minish Cap animation data](../../docs/newgame/data/player_animations.csv) · [Minish Cap sword](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/playerItem/playerItemSword.c#L266) · [Minish Cap collision](https://github.com/zeldaret/tmc/blob/6fb6dfb4a7efbe24d0fd1dda5097af6131faacde/src/collision.c#L185) · [Oracle weapon geometry](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/object_code/common/items/postUpdate.s#L176) · [Oracle item dispatch](https://github.com/Stewmath/oracles-disasm/blob/21c924afdc8a13225e849214479d5113da2ec226/code/parentItemUsage.s#L147) · [Link’s Awakening sword states](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/bank2.asm#L758) · [Link’s Awakening item input](https://github.com/zladx/LADX-Disassembly/blob/2a5c2c0d6df93a54df81ae9e1fe28b5c2fd60d03/src/code/home/check_items_to_use.asm#L112)

## Sword contact in BARTGAME

Step-and-cut takes 15 updates. Its three cutting poses occupy ages 2–9 and
each facing has its own grip, visible steel and sweep. The asset build packs
those markings and a one-pixel contact margin into 32 hardware-aligned rows per
pose. The game intersects those rows with a target’s hurtbox. This lets a
centered target connect on the appropriate motion while an empty corner of the
sweep’s bounding rectangle stays safe. The bounding rectangle still provides
nearby tile candidates and a diagnostic for the emulator probes.

Body, projectile, and ordinary sword contacts share projected positions and
check elevation separately. Body contact has a 10 px depth allowance. The
sword uses 12 px so Bloom can reach the game’s low hovering enemies. Different
known Cream tiers prevent contact through a shelf. Armour still handles hits
by side, the Confessor’s cut uses the blade’s current position, and the exposed
summit core retains its own raised target. A seed meeting the live blade can
reflect before it reaches Bloom’s body. Bushes, thorns, loose pickups and
Fourfold clone attacks use the same facing-specific contact.

## Movement and equipped actions

Bloom walks at 1.25 px per update, with diagonal movement normalized. Holding
the shield fixes facing and sets the base walking speed to 0.75 px per update.
R resolves the current four-way facing at roll entry. The original roll has
25 finite pose updates and a terminal update. Its movement starts at 3 px,
continues at 2 px, then accelerates by 0.125 px per update. The protected part
ends at age 18. A learned Roll Attack requires a sword press in a roll sword
window. [Minish Cap roll states](https://github.com/natertott/bartgame/blob/9aaf2a59b093e77e1316540b4fe43057b100fa3c/src/player.c#L2056) · [Minish Cap sword techniques](https://github.com/natertott/bartgame/blob/9aaf2a59b093e77e1316540b4fe43057b100fa3c/src/item/itemSword.c#L32)

Spin charge starts after the cut, tracks the physical sword button, and follows
the 80-update threshold or 40-update Fast Spin threshold. Bloom’s A/B/L loadout,
contextual R interactions, impact Blightseeds, and Grip Bracelet attacks retain
their existing game roles. Minish Cap’s Roc’s Cape starts at 2 px of vertical
velocity and allows aerial steering and a second lift. Bloom’s Petal Cloak
uses the same launch velocity with a fixed 42.5 px cardinal jump for generated
gaps. [Cape launch](../../src/item/itemRocsCape.c) · [Air movement](../../asm/src/player.s) · [Item roles and controls](../README.md)

## mGBA verification

`tools/combat_contacts_native.py` exercises centered hits, misses behind Bloom,
elevation, projectiles, body volume, guarding, roll and spin thresholds.
`tools/sword_study_probe.py` compares the generated blade rows, rendered frames
and damage in all four facings, including misses in the empty corners of the
old rectangles. The tests use declared actor or position fixtures and read
back damage after actual button input. The full Cream and Trading Cards probes
exercise boss weak points, wall combat, quest rewards and saved progress.
