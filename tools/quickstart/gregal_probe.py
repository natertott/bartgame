"""Gregal's ghost (Oct 2026, the redesign's P2 section 6.2), with the Gust Jar.

  SICK     on the tower's shop floor (Floor 1) Gregal lies sick with the
           evil spirit over him - vanilla's scene, loaded by roomInit.c
           under QUICKSTART although the mode sets WARP_EVENT_END at run
           start - and the hub sweep leaves him standing.
  PULL     the real Gust Jar catches the spirit (its hold count falls); with
           Link kept under it as it circles (a player tracking it), the
           jar holds it for the full count and it yields and is gone - evilSpirit.c sets SORA_ELDER_RECOVER and room flag 0
           itself, and his script plays the cure.
  THANKS   talking to him afterwards plays our thanks and pays a RARE draw
           at the feet (QuickStartGregalReward): the kit changes.
  ONCE     a second talk pays nothing more.
  GONE     back on the floor later the same run, he is not there (cured).

    python3 tools/quickstart/gregal_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, here, warp, press, snap, r16, w16, KIND_NPC, KIND_OBJECT, PLAYER, ROOM_CONTROLS, SAVE_FLAGS
import scenario as S
import parse_tables as P
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '/tmp'
SAVE = 0x02002a40
MSG = 0x02000050
NPC = {}
import re
for line in open(os.path.join(P.ROOT, 'include/npc.h')):
    m = re.match(r'\s*/\*0x([0-9a-f]+)\*/\s*(\w+),', line)
    if m:
        NPC[m.group(2)] = int(m.group(1), 16)
GREGAL = NPC['GREGAL']
SPIRIT = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())['EVIL_SPIRIT']
TOWER, F1, F2 = P.AREAS['AREA_WIND_TRIBE_TOWER'], P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_1'], P.ROOMS['ROOM_WIND_TRIBE_TOWER_FLOOR_2']
GUST = P.ITEMS['ITEM_GUST_JAR']
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = 24
        c.run_frame()
def dismiss(c, limit=900):
    quiet = 0
    for _ in range(limit):
        if c.memory.u8[MSG] == 0:
            run(c, 1); quiet += 1
            if quiet >= 30:
                return
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0
def kit(c):
    st = SAVE + 0xA8
    keep = [0, 1] + list(range(4, 0x12)) + [0x18, 0x19]
    return bytes(c.memory.u8[st + i] for i in keep) + bytes(c.memory.u8[SAVE + 0xF2 + i] for i in range(34))

c = S.boot(ROM, 0, seed=5, frames=300)
dismiss(c)
c.memory.u8[SAVE + 0x3C] = 0x51
# the Gust Jar, owned and on B
b, sh = GUST >> 2, (GUST & 3) * 2
c.memory.u8[SAVE + 0xF2 + b] = (c.memory.u8[SAVE + 0xF2 + b] & ~(3 << sh) & 0xFF) | (1 << sh)
c.memory.u8[SAVE + 0xA8 + 0x0c + 1] = GUST
warp(c, TOWER, F1, 120, 248, frames=240); dismiss(c); run(c, 60)
g = entities(c, KIND_NPC, GREGAL); sp = entities(c, KIND_OBJECT, SPIRIT)
check('SICK: Gregal and the spirit on the shop floor', here(c) == (TOWER, F1) and len(g) >= 1 and len(sp) >= 1,
      'room %s gregal %s spirit %s' % (here(c), g[:1], sp[:1]))
snap(c, os.path.join(OUT, 'gregal_sick.png'))
if g and sp:
    ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
    gx, gy = g[0][4], g[0][5]
    # The real jar first: stand in the mouth of the spirit's alcove, face
    # up, hold B. The jar does catch it - the spirit's gustJarTolerance
    # (entity +0x1d, 240 frames of hold) drops while it crosses the cone -
    # but it circles over the bed and the count resets each time it leaves,
    # so a player has to follow it. (Forging the contact byte does not work
    # here: the collision pass clears it before the spirit reads it.)
    from emu import GENT, STRIDE
    before = len(entities(c, KIND_OBJECT, SPIRIT))
    warp(c, TOWER, F1, 136, 72, frames=120); dismiss(c); run(c, 30)
    press(c, c.KEY_UP, 4, 2)
    c.set_keys(c.KEY_B)
    lowest = 240
    for f in range(300):
        run(c, 1)
        core = [e for e in entities(c, KIND_OBJECT, SPIRIT) if e[3] == 0]
        if core:
            lowest = min(lowest, c.memory.u8[GENT + core[0][0] * STRIDE + 0x1d])
    c.clear_keys(c.KEY_B)
    check('PULL: the real jar catches the spirit', lowest < 240, 'its hold count fell to %d of 240' % lowest)
    # Then follow it, as a player would: Link kept under the spirit in the
    # hall's top row, facing up, the jar held.
    f = -1
    c.set_keys(c.KEY_B)
    for f in range(900):
        core = [e for e in entities(c, KIND_OBJECT, SPIRIT) if e[3] == 0]
        if not core:
            break
        x = max(ox + 120, min(ox + 196, core[0][4]))
        w16(c, PLAYER + 0x2e, x); w16(c, PLAYER + 0x32, oy + 84)
        c.memory.u8[PLAYER + 0x14] = 0   # animationState: facing up
        run(c, 1)
    c.clear_keys(c.KEY_B)
    run(c, 60)
    gone = not entities(c, KIND_OBJECT, SPIRIT)
    # the cure scene runs on its own; let it, then talk
    for _ in range(10):
        run(c, 60); dismiss(c)
    check('PULL: held, the spirit yields and is gone', gone, 'spirit objects %d -> %d after %d frames' % (before, len(entities(c, KIND_OBJECT, SPIRIT)), f))
    k0 = kit(c)
    g = entities(c, KIND_NPC, GREGAL)
    if g:
        w16(c, PLAYER + 0x2e, g[0][4]); w16(c, PLAYER + 0x32, g[0][5] + 24); run(c, 10)
        press(c, c.KEY_UP, 4, 2); press(c, c.KEY_R, 4, 8); dismiss(c); run(c, 60); dismiss(c)
    k1 = kit(c)
    items = len(entities(c, KIND_OBJECT, 0))
    check('THANKS: talking pays a draw', k1 != k0 or items > 0, 'kit changed %s, ground items %d' % (k1 != k0, items))
    snap(c, os.path.join(OUT, 'gregal_thanks.png'))
    k2 = kit(c); i2 = len(entities(c, KIND_OBJECT, 0))
    g = entities(c, KIND_NPC, GREGAL)
    if g:
        w16(c, PLAYER + 0x2e, g[0][4]); w16(c, PLAYER + 0x32, g[0][5] + 24); run(c, 10)
        press(c, c.KEY_UP, 4, 2); press(c, c.KEY_R, 4, 8); dismiss(c); run(c, 60)
    check('ONCE: a second talk pays nothing more', kit(c) == k2 and len(entities(c, KIND_OBJECT, 0)) <= i2,
          'kit changed %s' % (kit(c) != k2))
    warp(c, TOWER, F2, 136, 248, frames=200); dismiss(c)
    warp(c, TOWER, F1, 120, 248, frames=200); dismiss(c); run(c, 30)
    check('GONE: cured, he is not on the floor later', not entities(c, KIND_NPC, GREGAL) and not entities(c, KIND_OBJECT, SPIRIT),
          'gregal %s spirit %s' % (entities(c, KIND_NPC, GREGAL)[:1], entities(c, KIND_OBJECT, SPIRIT)[:1]))
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
