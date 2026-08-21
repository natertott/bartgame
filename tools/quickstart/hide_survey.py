"""What can the scavenger hunt hide UNDER, per ring region?

The two F1 hide modes need tiles the player transforms on purpose:
  * under-bush: a tile the sword CUTS - solid before, open after. Found
    by predicate, not by hand: solid collision + a tile TYPE that the
    slashing diff (scratchpad cut_diff) proved transformable.
  * buried: a tile the Mole Mitts DIG - actTiles reads TILE_ACT_DIG (0xd).

Prints per ring region how many of each exist and a few sample tiles, so
the runtime picker's fallback logic is grounded in what is actually there.
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, r16, coll_at
from callrom import call_keep
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
GTT = 0x080002b0
ACT = 0x02025eb0 + 0xb004  # gMapBottom.actTiles
TILE_ACT_DIG = 0xd

for region in P.region_pool():
    c = boot(ROM)
    poison_here(c)
    warp(c, region['area'], region['room'], region['entrance'][0], region['entrance'][1])
    if here(c) != (region['area'], region['room']):
        print(f"{region['roomName'][5:]:<38} did not land")
        continue
    for _ in range(60):
        c.run_frame()
    W = r16(c, 0x03000bf0 + 0x1e) // 16
    H = r16(c, 0x03000bf0 + 0x20) // 16
    bushes, digs = [], []
    for ty in range(H):
        for tx in range(W):
            act = c.memory.u8[ACT + tx + (ty << 6)]
            if act == TILE_ACT_DIG:
                digs.append((tx, ty))
            elif coll_at(c, tx, ty) != 0:
                t = call_keep(c, GTT, (tx | (ty << 6), 1))
                # Solid + a type in the proven-cuttable families. 51-63 is
                # the bush/shrub band the slash diff transformed; 424-431
                # is the tall-foliage band that also went to 0 under the
                # sword in North Hyrule Field.
                if t in (51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63) or 424 <= t <= 431:
                    bushes.append((tx, ty))
    print(f"{region['roomName'][5:]:<38} bush-like {len(bushes):>3} {bushes[:4]}  dig {len(digs):>3} {digs[:4]}")
