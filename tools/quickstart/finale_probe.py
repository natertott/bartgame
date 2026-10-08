"""The finale is drawn when the fourth trial completes, from live reach
(Oct 2026, the redesign's P0.1), not at the hub's exit by map distance.

  BEFORE   on a fresh run the element region index is -1 and the element
           flag is clear; the chain monitor still runs (it gates on the
           DROP roll now).
  AFTER    with the four pre-steps forced complete (the fourth made an
           ITEM step with no item to want), one settled frame later the
           element flag is set, the carrier bits are set, and the element
           row's REGION is inside QuickStartReachableRegions(held) - the
           region the run can actually reach at that moment.
  COMPASS  QuickStartElementMapMarker answers FALSE before the roll and
           TRUE after, with the compass held.

Two seeds, so the roll is seen landing in two different places.

    python3 tools/quickstart/finale_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, poison_here, press
import scenario as S
import parse_tables as P
import callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL, PROGRESS, ROLLED, HINTED = 0x26, 0x2B, 0x30, 0x35, 0x36, 0x37
QS_CHAIN_ITEM = 0
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-50s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
def s32(v): return v - (1 << 32) if v >= (1 << 31) else v
landed = []
for sd in (3, 11):
    c = S.boot(ROM, 0, seed=sd, frames=300)
    elem = C.call_keep(c, C.game_sym('QuickStartElementRegionIndex'), ())
    drop = C.call_keep(c, C.game_sym('QuickStartDropRegionIndex'), ())
    check('BEFORE: seed %d, no element yet, the drop is rolled' % sd, s32(elem) == -1 and 0 <= drop < len(P.region_pool()),
          'element %d drop %d' % (s32(elem), drop))
    marker_before = C.call_keep(c, C.map_sym('QuickStartElementMapMarker'), (0x02000000, 0x02000004))
    # force the four pre-steps: three done, the fourth an ITEM step wanting nothing
    for i in range(4):
        c.memory.u8[SAVE + CHAIN_KIND + i] = QS_CHAIN_ITEM
        c.memory.u8[SAVE + CHAIN_WHERE + i] = 0
        c.memory.u8[SAVE + CHAIN_DETAIL + i] = 0
    c.memory.u8[SAVE + PROGRESS] = 3
    c.memory.u8[SAVE + ROLLED] = 4
    c.memory.u8[SAVE + HINTED] = 0x0f
    # the monitor runs in a region room, not the hub: land in the drop row
    row = P.region_pool()[drop]
    poison_here(c); warp(c, row['area'], row['room'], row['entrance'][0], row['entrance'][1], frames=400)
    for _ in range(12):
        press(c, c.KEY_A, 3, 17)
    for _ in range(120):
        c.run_frame()
    elem = s32(C.call_keep(c, C.game_sym('QuickStartElementRegionIndex'), ()))
    carrier = C.call_keep(c, C.game_sym('QuickStartWinCarrier'), ())
    held = C.call_keep(c, C.game_sym('QuickStartHeldReachMask'), ())
    regions = C.call_keep(c, C.game_sym('QuickStartReachableRegions'), (held,))
    ring = C.call_keep(c, C.game_sym('QuickStartRegionOfPoolIndex'), (elem,)) if elem >= 0 else -1
    reachable = elem >= 0 and (regions >> ring) & 1
    landed.append((drop, elem, carrier))
    check('AFTER: seed %d, the finale is drawn inside live reach' % sd, elem >= 0 and reachable and carrier in (0, 1, 2),
          'drop %d -> element row %d (ring %d), carrier %d, reachable regions %#x' % (drop, elem, ring, carrier, regions))
    C.call_keep(c, C.map_sym('SetInventoryValue'), (P.ITEMS['ITEM_COMPASS'], 1))
    marker_after = C.call_keep(c, C.map_sym('QuickStartElementMapMarker'), (0x02000000, 0x02000004))
    check('COMPASS: seed %d, marker only after the roll' % sd, marker_before == 0 and marker_after == 1,
          'before %d after %d' % (marker_before, marker_after))
check('TWO PLACES: the two seeds did not land the same finale', len({(e, cr) for _d, e, cr in landed}) == 2 or landed[0][0] != landed[1][0], str(landed))
print('RESULT', 'PASS' if all(res) else 'FAIL', '%d/%d' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
