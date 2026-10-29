BARTGAME - selected Step-and-cut sword release

Open bartgame-step-and-cut-7c46553.gba in mGBA or on compatible GBA hardware.
This is the full standalone game; no commercial base ROM is needed.
Source: 7c46553ff80bf558daa66f02c2b6d4d9f468e888
Branch: art-reboot
ROM SHA256: 547674bfd44f79cd5614f3188bad86f8ed8a4a9ea9cee060e1236ca0c832c97a

Step-and-cut is the default in normal builds and direct asset generation.
The reviewed eight-pose body and blade share one clock and matching damage
bounds in all four directions. Four preparation updates, seven live updates,
seven recovery updates, 18 total (about301ms). The visible step transfers
weight without changing the player's world position. Existing saves work.

D-pad: walk. A/B/L: assigned items (B starts as sword, L as shield).
A: talk. R: roll while moving, lift while still, throw a carried object.
Start: inventory/key items/map; assign items to A/B/L in the inventory.
Approach chests from below. Bombs crack stone; candle burns silk; cape jumps gaps.

Real mGBA preview and validation:
https://github.com/natertott/bartgame/blob/art-reboot/art-review/step-and-cut/README.md
