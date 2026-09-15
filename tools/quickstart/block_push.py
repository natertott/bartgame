"""Does the Power Bracelets alone move a clone block, at every block size?

Finds each block as a connected component of act tile 114, stands the player
against the middle of each of its four edges facing in, holds that direction,
and reports whether ANY of the block's tiles stopped being act-114 (the
ground truth that the block moved). Run twice per room, with and without the
bracelets. Deliberately does NOT look for a PUSHED_BLOCK entity: object id 0
is shared with ground items and camera targets, so that check false-positives.
"""
import sys, os
sys.path.insert(0, os.path.abspath('tools/quickstart'))
from emu import boot, warp, here, w16, r16, PLAYER
import parse_tables as P

MAPB, MAPT = 0x02025eb0, 0x0200b650
ACT_OFF, ACT_CLONE_BLOCK = 0xb004, 114
INV = 0x02002a40 + 0xF2
BRACELETS = P.ITEMS['ITEM_POWER_BRACELETS']
RC = 0x03000bf0


def give(c, item, v):
    a, sh = INV + (item >> 2), (item & 3) * 2
    c.memory.u8[a] = (c.memory.u8[a] & ~(3 << sh)) | ((v & 3) << sh)


def act_hits(c, layer):
    base = (MAPB if layer == 1 else MAPT) + ACT_OFF
    return [p for p in range(0x1000) if c.memory.u8[base + p] == ACT_CLONE_BLOCK]


def components(hits):
    hs, seen, out = set(hits), set(), []
    for p0 in hits:
        if p0 in seen:
            continue
        stack, comp = [p0], []
        seen.add(p0)
        while stack:
            q = stack.pop()
            comp.append(q)
            for nb in (q - 1, q + 1, q - 0x40, q + 0x40):
                if nb in hs and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        out.append(comp)
    return out


def find_blocks(area, room, ex, ey, rom):
    c = boot(rom)
    warp(c, area, room, ex, ey)
    if here(c) != (area, room):
        return None, None, 'did not land (got %s)' % (here(c),)
    for layer in (c.memory.u8[PLAYER + 0x38], 1, 2):
        hits = act_hits(c, layer)
        if hits and len(hits) <= 64:
            return layer, components(hits), None
        if hits:
            return None, None, ('act tile 114 covers %d tiles - not the clone block '
                                'in this tileset' % len(hits))
    return None, None, 'no act-tile-114 on either layer'


def try_push(area, room, ex, ey, layer, comp, want, rom):
    xs = {q & 0x3f for q in comp}
    ys = {q >> 6 for q in comp}
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    sides = {
        'from_below': ((cx, y1 + 1), 'UP'),
        'from_above': ((cx, y0 - 1), 'DOWN'),
        'from_right': ((x1 + 1, cy), 'LEFT'),
        'from_left':  ((x0 - 1, cy), 'RIGHT'),
    }
    moved = []
    base = (MAPB if layer == 1 else MAPT) + ACT_OFF
    for name, ((ptx, pty), key) in sides.items():
        c = boot(rom)
        warp(c, area, room, ex, ey)
        if here(c) != (area, room):
            continue
        give(c, BRACELETS, 1 if want else 0)
        ox, oy = r16(c, RC + 6), r16(c, RC + 8)
        w16(c, PLAYER + 0x2e, (ptx << 4) + 8 + ox)
        w16(c, PLAYER + 0x32, (pty << 4) + 8 + oy)
        c.memory.u8[PLAYER + 0x38] = layer
        before = [c.memory.u8[base + q] for q in comp]
        kk = getattr(c, 'KEY_' + key)
        c.set_keys(kk)
        for _ in range(180):
            c.run_frame()
            if [c.memory.u8[base + q] for q in comp] != before:
                moved.append(name)
                break
        c.clear_keys(kk)
        del c
    return (x1 - x0 + 1, y1 - y0 + 1), moved


ROOMS = [
    ('AREA_CAVES', 'ROOM_CAVES_LON_LON_RANCH', 120, 200),
    ('AREA_CAVES', 'ROOM_CAVES_TRILBY_HIGHLANDS', 120, 200),
    ('AREA_CAVES', 'ROOM_CAVES_TO_GRAVEYARD', 120, 200),
    ('AREA_ROYAL_VALLEY_GRAVES', 'ROOM_ROYAL_VALLEY_GRAVES_HEART_PIECE', 168, 88),
]
rom = sys.argv[1] if len(sys.argv) > 1 else 'tmc.gba'
print('rom:', rom)
for an, rn, ex, ey in ROOMS:
    a, r = P.AREAS[an], P.ROOMS[rn]
    layer, comps, err = find_blocks(a, r, ex, ey, rom)
    print('== %s / %s' % (an, rn))
    if err:
        print('   ' + err)
        continue
    for comp in comps:
        for want in (True, False):
            size, moved = try_push(a, r, ex, ey, layer, comp, want, rom)
            print('   %dx%d block, %-10s -> %s'
                  % (size[0], size[1], 'bracelets' if want else 'bare',
                     ', '.join(moved) if moved else 'DID NOT MOVE from any side'))
    sys.stdout.flush()
