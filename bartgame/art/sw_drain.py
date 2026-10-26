"""The Drain's hall for the build: painted (sw_hall.py), cut into cells
(sw_cut.py), with what each cell is: its collision by quarter, its type.

    METATILES   the hall's own metatiles, named swh_NNN
    PALETTES    the palettes packed for them, sw_pal0..
    GROUND, OVERLAY   the hall as rows of metatile names
"""
import sw_hall as HL
import sw_cut

W, H = HL.W, HL.H
EXIT = (9, 2)               # the drain hole: up to the wood
# in front of the Peddler's counter the hero is drawn over it
FRONT = {(x, y) for x in range(1, 8) for y in (6, 7)}


def _solid():
    """the hall's solid 8x8 quarters, as a set of (qx, qy)"""
    s = set()

    def box(x0, y0, x1, y1):
        for qy in range(y0 // 8, (y1 + 7) // 8):
            for qx in range(x0 // 8, (x1 + 7) // 8):
                s.add((qx, qy))

    box(0, 0, HL.PW, HL.WALL_Y1)                    # the back wall
    for qy in range(2 * EXIT[1], 2 * EXIT[1] + 4):  # but the drain hole and its mouth
        s.discard((2 * EXIT[0], qy))
        s.discard((2 * EXIT[0] + 1, qy))
    box(0, 0, HL.SIDE, HL.PH)                       # the side walls
    box(HL.PW - HL.SIDE, 0, HL.PW, HL.PH)
    box(HL.CX - HL.BASIN_RX - 8, HL.WALL_Y1, HL.CX + HL.BASIN_RX + 8, HL.BASIN_Y1)
    box(HL.SIDE, HL.WALL_Y1, HL.STALL_X1, HL.COUNTER_Y1 + 2)   # the stall
    # the Gatekeeper's corner: shelf and candles at the wall, the table,
    # the crates and the barrel
    box(HL.RUG_X0 - 16, HL.WALL_Y1, HL.RUG_X1 + 24, HL.WALL_Y1 + 8)
    box(HL.RUG_X1, HL.WALL_Y1, HL.RUG_X1 + 24, 80)
    box(400, HL.WALL_Y1, 448, 96)
    box(HL.SIDE, 224, 56, HL.FE_COPE)               # the lower floor's corners
    box(424, 224, HL.PW - HL.SIDE, HL.FE_COPE)
    # the banks, the channel, the front edge, the pool: all but the bridge
    for (y0, y1) in ((144, 208), (HL.FE_COPE, HL.PH)):
        box(HL.SIDE, y0, HL.PW - HL.SIDE, y1)
    for qy in range(144 // 8, 208 // 8):
        for qx in range(HL.BRIDGE_X0 // 8, HL.BRIDGE_X1 // 8):
            s.discard((qx, qy))
    return s


SOLID = _solid()


def types(cx, cy):
    q = [(2 * cx, 2 * cy), (2 * cx + 1, 2 * cy), (2 * cx, 2 * cy + 1), (2 * cx + 1, 2 * cy + 1)]
    coll = sum(b for (k, b) in zip(q, (8, 4, 2, 1)) if k in SOLID)
    if (cx, cy) == EXIT:
        return ('EXIT', 0)
    if (cx, cy) in FRONT and coll == 0:
        return ('FRONT', 0)
    return ('SOLID' if coll == 15 else 'FLOOR', coll)


CUT = sw_cut.cut(HL.paint, HL.TICKS, types)
print('drain hall: %d metatiles (%d animated), %d palettes, %d pixels remapped' % (
    len(CUT['metatiles']), sum(1 for m in CUT['metatiles'] if 'frames' in m), len(CUT['palettes']),
    sum(n for *_, n in sw_cut.REDUCED)))
METATILES = CUT['metatiles']
PALETTES = CUT['palettes']
GROUND = CUT['ground']
OVERLAY = CUT['overlay']
