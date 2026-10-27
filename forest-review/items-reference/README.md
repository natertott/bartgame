# Supplied item artwork — actual mGBA review

The item and shield designs are imported from the two supplied screenshots.
The checkerboard is removed, and their pixel shapes, shading and glints are
retained at the GBA's native sprite sizes.

## Before and after

![Previous and imported inventory and HUD](before-after.png)

These are actual mGBA 0.10.5 framebuffers, enlarged 2× without smoothing.

## In the running game

![Imported HUD icons, inventory, pickups, shop and earned reward](in-game.png)

Inventory and ground-item displays are rendering fixtures. The Blightseeds
reward is earned by completing the actual generated plate trial. Native
240×160 screenshots are in the folders below.

## Both shield designs

![Wooden and green-and-gold shields in the actual inventory](shield-inventory.png)

![Both shield sets, facing all four directions](shield-directions.png)

The wooden shield is the starting design. The green-and-gold shield is
wired as an upgrade variant; its review fixture sets ownership explicitly.
It has not been assigned to a new chest or quest in this artwork update.

## Held items

![Imported leafy bow in use](clips/bow-east.gif)

![Imported purple lantern in use](clips/lantern-north.gif)

![Imported cloak during a cape jump](clips/cape-east.gif)

These clips show genuine item-button actions in mGBA. They crop the actual
framebuffers and enlarge them 3× with nearest-neighbour scaling; frame
timing is retained at a 30fps sample rate.

## Complete source-art catalogue

![Imported source sprites at native size and enlarged](source-catalogue.png)

This last image is a **source-asset preview**, separate from emulator
captures. Large inventory icons use individual palettes to retain shading;
world sprites share four material palettes. The smaller 16×16 forms lose
some fine detail, as expected at that size.

[Native new frames](after/) · [Native previous frames](before/) ·
[Item source screenshot](../../bartgame/art/ref/items-reference.jpg) ·
[Shield source screenshot](../../bartgame/art/ref/shields-reference.jpg) ·
[Updated ROM download](../../downloads/README.md) ·
[Validation](validation.json) · [Import metadata](import.json) ·
[Implementation and capture instructions](../../bartgame/docs/REFERENCE_ITEMS.md)
