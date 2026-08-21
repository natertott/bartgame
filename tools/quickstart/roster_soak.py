"""Does every roster enemy survive simply EXISTING in a field room?

The admission probe measured "spawns and dies to the sword". It never
measured lifespan, and several vanilla kinds turn out to be
spawner-lifecycle enemies that self-despawn (or die, paying kill drops)
within seconds of a raw CreateEnemy in an open room: the user's
"enemies dying as soon as the player enters the area, often with an item
drop". This soak raw-spawns every roster row in the quiet Grimblade dojo (its
site forced DONE, so nothing else spawns or interferes - and no wave
slots need zeroing, which corrupts the entity free list) and watches
each for 600 frames. An entry passes only if its enemy is still alive at
the end. Lifecycle self-despawns show anywhere; terrain-specific deaths
are a separate placement question.

Usage: python3 tools/quickstart/roster_soak.py [start_row [end_row]]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, poison_here, press, entities, r16, qs_set, qs_site_set, GENT, STRIDE, KIND_ENEMY
from callrom import call_keep, map_sym
import parse_tables as P

ROM = os.path.join(P.ROOT, 'tmc.gba')
CREATE_ENEMY = map_sym('CreateEnemy')
UPDATE_SPRITE = map_sym('UpdateSpriteForCollisionLayer')
DELETE_ENTITY = map_sym('DeleteEntity')

ENEMY_NAMES = {}
for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc')):
    m = re.match(r'\.set (\w+), (\d+)', line.strip())
    if m:
        ENEMY_NAMES.setdefault(int(m.group(2)), m.group(1))


def roster_rows():
    G = P.GAME
    rows = []
    for level in ('sQuickStartLevel1', 'sQuickStartLevel2', 'sQuickStartLevel3', 'sQuickStartLevel4',
                  'sQuickStartLevel5', 'sQuickStartElites'):
        i = G.find(level + '[] = {')
        j = G.find('\n};', i)
        body = re.sub(r'//[^\n]*', '', G[i:j])
        body = re.sub(r'/\*.*?\*/', '', body)
        for m in re.finditer(r'\{ (\w+), (\d+)\s*,', body):
            rows.append((level, m.group(1), int(m.group(2))))
    return rows


def main():
    rows = roster_rows()
    enemy_ids = {}
    for line in open(os.path.join(P.ROOT, 'build/USA/enum_include/enemy.inc')):
        m = re.match(r'\.set (\w+), (\d+)', line.strip())
        if m:
            enemy_ids[m.group(1)] = int(m.group(2))
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(rows)

    c = boot(ROM)
    base = 16 * 13
    qs_site_set(c, base, 1)
    qs_site_set(c, base + 12, 1)
    poison_here(c)
    warp(c, 37, 5, 0x78, 0xa0)
    for _ in range(10):
        press(c, c.KEY_A, 5, 5)
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    SPOT_X, SPOT_Y = ox + 120, oy + 96

    def w16a(a, v):
        c.memory.u8[a] = v & 0xFF
        c.memory.u8[a + 1] = (v >> 8) & 0xFF

    failures = []
    for n, (level, name, form) in enumerate(rows[start:end], start):
        eid = enemy_ids[name]
        ptr = call_keep(c, CREATE_ENEMY, (eid, form))
        if ptr == 0:
            print(f'{n:>2} {level[11:]:<7} {name:<18} form {form}: SPAWN FAILED')
            failures.append((name, form, 'spawn failed'))
            continue
        w16a(ptr + 0x2e, SPOT_X)
        w16a(ptr + 0x32, SPOT_Y)
        c.memory.u8[ptr + 0x38] = 1
        call_keep(c, UPDATE_SPRITE, (ptr,))
        slot = (ptr - GENT) // STRIDE
        alive_at = 0
        for f in range(600):
            c.run_frame()
            k = c.memory.u8[GENT + slot * STRIDE + 8]
            i2 = c.memory.u8[GENT + slot * STRIDE + 9]
            if k != KIND_ENEMY or i2 != eid:
                break
            alive_at = f
        ok = alive_at >= 599
        if ok:
            call_keep(c, DELETE_ENTITY, (ptr,))
        for _ in range(20):
            c.run_frame()
        for (idx, k2, ident2, typ2, x2, y2) in entities(c, kind=KIND_ENEMY):
            call_keep(c, DELETE_ENTITY, (GENT + idx * STRIDE,))
        for _ in range(10):
            c.run_frame()
        print(f'{n:>2} {level[11:]:<7} {name:<18} form {form}: '
              f'{"alive at 600" if ok else "GONE at f%d" % alive_at}')
        if not ok:
            failures.append((name, form, 'gone at f%d' % alive_at))
    print(f'\n{len(failures)} failing row(s):')
    for f in failures:
        print('   ', f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
