"""The blessing tiers (Oct 2026, the redesign's P2 section 9): one sprite
per pastry in three colours - brown the blessing, GREEN its curse, GOLD the
blessing and an extra.

  GREEN    the reward spawner turns a curse item into its blessing's sprite
           in green: QuickStartSpawnRewardEntity(ITEM_PIE) puts a BRIOCHE
           with type2 1 on the floor (dog food a croissant, the mushroom a
           cake).
  GOLD     a blessing pastry comes up gold about one time in four (200
           spawns of the brioche, type2 2).
  TINT     a tiered pastry on the floor draws from a palette slot of its
           own, claimed under 0xF000 | tier << 8 | source slot; the green
           copy reads green (G over R and B), the gold copy gold (R and G
           over B), and the brown original is left alone.
  SNAP     a screenshot of the three tiers side by side (the eye check).
  FULL     with every palette slot taken, a green pastry whose palette is
           shared cannot be tinted; it turns back into the curse's own item
           (the mushroom), so a curse never passes for a blessing.
  CURSE    GiveItem(ITEM_BRIOCHE, 1) sets the pie's curse (food bit 3), not
           the brioche's blessing (bit 0).
  BRIOCHE  GiveItem(ITEM_BRIOCHE, 2): a heart container more, every heart
           full, and the brioche's blessing.
  CROISS.  GiveItem(ITEM_CROISSANT, 2): the croissant's blessing and the
           fleet charm (bit 20).
  FLEET    with the fleet charm, entering a room starts the seashell clock
           at 120 (two seconds untouchable); without it, it stays at 0.
  CAKE     walking onto a gold cake (the floor path, type2 through the pickup):
           the cake's blessing and the rupee and heart charms (bits 2, 9, 11).
  FREE     once the tinted pastries are gone, their palette slots are given
           back (no slot leaks per pastry).

    python3 tools/quickstart/blessing_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, r16, w16, warp, here, snap, KIND_OBJECT, GENT, STRIDE, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
import callrom as C
import chain_audit as A
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else '/tmp'
SAVE = 0x02002a40
HEALTH, MAXHEALTH = SAVE + 0xA8 + 2, SAVE + 0xA8 + 3
SHELL_CLOCK = SAVE + 0xA8 + 0x1a
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)

I = P.ITEMS
spawn = C.game_sym('QuickStartSpawnRewardEntity')
give = C.map_sym('GiveItem')
mask = lambda c: C.call_keep(c, C.map_sym('QuickStartFoodMask'), ())
delete = C.map_sym('DeleteEntity')
PLIST = 0x02001a00   # gPaletteList (linker.ld)
PBUF = 0x020176a0    # gPaletteBuffer (linker.ld)

def run(c, n):
    for _ in range(n):
        c.memory.u8[PLAYER + 0x45] = c.memory.u8[MAXHEALTH]
        c.run_frame()

def local_player(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))

def ent(ptr):
    return (ptr - GENT) // STRIDE

def put(c, item, dx, dy):
    px, py = local_player(c)
    p = C.call_keep(c, spawn, (item, (px + dx) & 0xFFFF, (py + dy) & 0xFFFF))
    return p

def rgb(c, slot, i):
    v = c.memory.u8[PBUF + ((16 + slot) * 16 + i) * 2] | (c.memory.u8[PBUF + ((16 + slot) * 16 + i) * 2 + 1] << 8)
    return (v & 31, (v >> 5) & 31, (v >> 10) & 31)

def slot_of(c, p):
    return c.memory.u8[p + 0x1a] & 0xf

def pal_id(c, slot):
    return c.memory.u8[PLIST + slot * 4 + 2] | (c.memory.u8[PLIST + slot * 4 + 3] << 8)

def pal_state(c, slot):
    return c.memory.u8[PLIST + slot * 4] & 0xf

def sums(c, slot):
    r = g = b = 0
    for i in range(1, 16):
        x = rgb(c, slot, i); r += x[0]; g += x[1]; b += x[2]
    return r, g, b

c = S.boot(ROM, S.KINDS['REGION'], 0, 0, kit=2, frames=400)
A.kill_all(c); run(c, 30); A.dismiss(c)

# GREEN: the curse items come out as their blessing's sprite, tier 1
got = []
for curse, want in (('ITEM_PIE', 'ITEM_BRIOCHE'), ('ITEM_QST_DOGFOOD', 'ITEM_CROISSANT'), ('ITEM_QST_MUSHROOM', 'ITEM_CAKE')):
    p = put(c, I[curse], 0, 40)
    got.append((curse, p != 0 and c.memory.u8[p + 10] == I[want] and c.memory.u8[p + 11] == 1))
    if p:
        C.call_keep(c, delete, (p,))
check('GREEN: each curse is its blessing, in green', all(g for _, g in got), str(got))

# GOLD: one in four
n = gold = 0
for _ in range(200):
    p = put(c, I['ITEM_BRIOCHE'], 0, 40)
    if p:
        n += 1; gold += c.memory.u8[p + 11] == 2
        C.call_keep(c, delete, (p,))
    run(c, 1)   # a deleted entity's slot is freed at the frame's end
check('GOLD: a brioche is gold about one time in four', n == 200 and 30 <= gold <= 70, '%d of %d' % (gold, n))

# TINT: the three tiers side by side, in the hub's selection hall - a quiet
# room, so the palette slots are not all taken by a region's cast (that case
# is FULL below). Green and gold first: each claims a slot of its own.
ct = S.boot(ROM, 0, seed=3, frames=300)
run(ct, 30)
p_green = put(ct, I['ITEM_QST_MUSHROOM'], 0, -24)
p_gold = 0
for _ in range(40):
    p = put(ct, I['ITEM_CAKE'], 32, -24)
    if p and ct.memory.u8[p + 11] == 2:
        p_gold = p; break
    if p:
        C.call_keep(ct, delete, (p,))
    run(ct, 1)
p_plain = put(ct, I['ITEM_CAKE'], -32, -24)
while p_plain and ct.memory.u8[p_plain + 11] != 0:   # a gold roll: try again
    C.call_keep(ct, delete, (p_plain,)); run(ct, 1); p_plain = put(ct, I['ITEM_CAKE'], -32, -24)
run(ct, 60)
ok = p_plain and p_green and p_gold
if ok:
    sp, sg, sd = slot_of(ct, p_plain), slot_of(ct, p_green), slot_of(ct, p_gold)
    ig, id_ = pal_id(ct, sg), pal_id(ct, sd)
    gr, gg, gb = sums(ct, sg); dr, dg, db = sums(ct, sd)
    check('TINT: the green cake has its own slot', sg != sp and (ig & 0xFF00) == 0xF100, 'plain slot %d, green slot %d id %#x' % (sp, sg, ig))
    check('TINT: the gold cake has its own slot', sd not in (sp, sg) and (id_ & 0xFF00) == 0xF200, 'gold slot %d id %#x' % (sd, id_))
    check('TINT: green reads green, gold reads gold', gg > gr and gg > gb and dr > db and dg > db,
          'green rgb sums %s, gold %s, plain %s' % ((gr, gg, gb), (dr, dg, db), sums(ct, sp)))
    path = os.path.join(OUT, 'blessing_tiers.png'); snap(ct, path)
    check('SNAP: the three tiers, saved', os.path.exists(path), path)
else:
    check('TINT: three cakes on the floor', False, 'plain %#x green %#x gold %#x' % (p_plain, p_green, p_gold))
# FULL: every free object palette slot taken (forged), a plain cake down
# (its palette then shared): the green one cannot be tinted, so it must turn
# back into the curse's own item rather than pass for a blessing.
saved = [ct.memory.u8[PLIST + i] for i in range(64)]
for k in range(6, 15):   # all of them, so no earlier green slot can be shared
    ct.memory.u8[PLIST + k * 4] = 0x13; ct.memory.u8[PLIST + k * 4 + 1] = 1
    ct.memory.u8[PLIST + k * 4 + 2] = 0x34; ct.memory.u8[PLIST + k * 4 + 3] = 0x12 + k
pp = put(ct, I['ITEM_CAKE'], -32, 8)
pg = put(ct, I['ITEM_QST_MUSHROOM'], -32, 8)
run(ct, 10)
types = [e[3] for e in entities(ct, KIND_OBJECT, 0) if e[5] - r16(ct, ROOM_CONTROLS + 8) == local_player(ct)[1] + 8]
check('FULL: an untintable green turns back into its curse', I['ITEM_QST_MUSHROOM'] in types,
      'item types at the spot %s' % types)
for i in range(64):
    ct.memory.u8[PLIST + i] = saved[i]

# CURSE through GiveItem's parameter
m0 = mask(c)
C.call_keep(c, give, (I['ITEM_BRIOCHE'], 1)); A.dismiss(c)
m1 = mask(c)
check('CURSE: a green brioche is the pie', (m1 & 8) and not (m1 & 1) and not (m0 & 8), 'mask %#x -> %#x' % (m0, m1))

# BRIOCHE gold
c.memory.u8[MAXHEALTH] = 24   # the kit's 20 hearts sit at the cap
mh0 = c.memory.u8[MAXHEALTH]; c.memory.u8[HEALTH] = 4
C.call_keep(c, give, (I['ITEM_BRIOCHE'], 2)); A.dismiss(c)
mh1, h1, m2 = c.memory.u8[MAXHEALTH], c.memory.u8[HEALTH], mask(c)
check('BRIOCHE: a heart more, all full, the blessing', mh1 == mh0 + 8 and h1 == mh1 and (m2 & 1), 'max %d -> %d, health %d, mask %#x' % (mh0, mh1, h1, m2))

# FLEET: none before the gold croissant
area, room = here(c)
w16(c, SHELL_CLOCK, 0)
warp(c, area, room, *local_player(c), frames=1)
best = 0
for _ in range(150):
    run(c, 1); best = max(best, r16(c, SHELL_CLOCK))
check('FLEET: no grace before the gold croissant', best == 0, 'clock peaked at %d' % best)
C.call_keep(c, give, (I['ITEM_CROISSANT'], 2)); A.dismiss(c)
m3 = mask(c)
check('CROISS.: the blessing and the fleet charm', (m3 & 2) and (m3 & (1 << 20)), 'mask %#x' % m3)
w16(c, SHELL_CLOCK, 0)
warp(c, area, room, *local_player(c), frames=1)
best = 0
for _ in range(150):
    run(c, 1); best = max(best, r16(c, SHELL_CLOCK))
check('FLEET: two seconds on entering a room', 110 <= best <= 121, 'clock peaked at %d' % best)

# CAKE gold, taken off the floor
A.kill_all(c); run(c, 30); A.dismiss(c)
from emu import coll_at
px0, py0 = local_player(c)
dx, dy = next(((x, y) for x, y in ((0, 32), (32, 0), (-32, 0), (0, -32), (32, 32), (-32, 32), (32, -32), (-32, -32))
               if coll_at(c, (px0 + x) >> 4, (py0 + y) >> 4) == 0), (0, 32))
p = 0
for _ in range(40):
    p = put(c, I['ITEM_CAKE'], dx, dy)
    if p and c.memory.u8[p + 11] == 2:
        break
    if p:
        C.call_keep(c, delete, (p,)); p = 0
    run(c, 1)
run(c, 40)
print('  cake entity %#x type %d type2 %d at (%d, %d), player (%d, %d)' % (p, c.memory.u8[p + 10] if p else -1, c.memory.u8[p + 11] if p else -1,
      r16(c, p + 0x2e) if p else 0, r16(c, p + 0x32) if p else 0, r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)))
gslot = slot_of(c, p) if p else -1
m4 = mask(c)
if p:
    w16(c, PLAYER + 0x2e, r16(c, p + 0x2e)); w16(c, PLAYER + 0x32, r16(c, p + 0x32))
for _ in range(10):
    run(c, 30); A.dismiss(c)
m5 = mask(c)
check('CAKE: a gold cake off the floor pays its extra', p and not (m4 & 4) and (m5 & 4) and (m5 & (1 << 9)) and (m5 & (1 << 11)),
      'mask %#x -> %#x' % (m4, m5))

# FREE: every tinted slot handed back once its pastries are gone
for e in entities(c, KIND_OBJECT, 0):
    C.call_keep(c, delete, (GENT + e[0] * STRIDE,))
run(c, 30)
held = [(s, hex(pal_id(c, s)), pal_state(c, s)) for s in range(6, 16) if (pal_id(c, s) & 0xF000) == 0xF000 and pal_id(c, s) != 0xFFFF and pal_state(c, s) == 3]
check('FREE: no tinted slot still held', not held, 'held %s' % held)

print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
