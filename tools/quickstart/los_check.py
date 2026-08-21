"""F2 research: does the guard line-of-sight mechanism work outside its
scripted rooms?

Static reading says it should: the LOS is a self-contained projectile
pair (an invisible emitter riding its parent, firing short-lived
invisible rays in the parent's facing that die on walls), and "spotted"
is nothing but `parent->type = 0xff`. This transplants it into North
Hyrule Field, attached to a plain ZELDA npc - the same kind every quest
giver already is - and checks both halves:

  * player standing IN the facing line       -> type flips to 0xff
  * player standing BEHIND the parent        -> type stays 0 (control)
"""
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, warp, here, poison_here, press, entities, KIND_ENEMY, GENT, STRIDE, r16
from callrom import call_keep
import parse_tables as P

ROM = '/home/user/bartgame/tmc.gba'
CREATE_NPC = 0x08078e68
CREATE_PROJECTILE = 0x080b22bc
GUARD_LOS = 12
ZELDA = 0x2b  # npc.inc: ZELDA is?
import re
for line in open('/home/user/bartgame/build/USA/enum_include/npc.inc'):
    m = re.match(r'\.set (ZELDA), (\d+)', line.strip())
    if m:
        ZELDA = int(m.group(2))
PLAYER = 0x03001160

def w16a(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF

def run(player_dx, player_dy, facing, label):
    from emu import qs_site_set
    c = boot(ROM)
    # The Grimblade dojo, its site forced DONE - a quiet room whose entity
    # free list has real room (NHF's, after a wave, does not: zeroing kind
    # does not unlink a slot, and CreateNPC comes back NULL).
    base = 16 * 13
    qs_site_set(c, base, 1)
    qs_site_set(c, base + 12, 1)
    poison_here(c)
    warp(c, 37, 5, 0x78, 0xa0)
    for _ in range(240):
        c.run_frame()
    for _ in range(6):
        press(c, c.KEY_A, 4, 4)
    ox, oy = r16(c, 0x03000bf0 + 6), r16(c, 0x03000bf0 + 8)
    gx, gy = ox + 120, oy + 96
    npc = call_keep(c, CREATE_NPC, (ZELDA, 0, 0))
    assert npc != 0
    w16a(c, npc + 0x2e, gx)
    w16a(c, npc + 0x32, gy)
    c.memory.u8[npc + 0x38] = 1          # collisionLayer (0x1d is gustJarTolerance!)
    proj = call_keep(c, CREATE_PROJECTILE, (GUARD_LOS,))
    assert proj != 0
    # exactly what guard.c does at its own spawn
    c.memory.u8[proj + 0x0a] = 0            # type = 0 (the emitter)
    for i, b in enumerate((npc & 0xFF, (npc >> 8) & 0xFF, (npc >> 16) & 0xFF, (npc >> 24) & 0xFF)):
        c.memory.u8[proj + 0x50 + i] = b    # Entity* parent at +0x50
    c.memory.u8[proj + 0x0f] = 60           # subtimer at +0x0f
    # place the player and pin the parent's facing every frame
    w16a(c, PLAYER + 0x2e, gx + player_dx)
    w16a(c, PLAYER + 0x32, gy + player_dy)
    for _ in range(240):
        c.memory.u8[npc + 0x3e] = facing    # knockbackDirection at +0x3e
        w16a(c, PLAYER + 0x2e, gx + player_dx)
        w16a(c, PLAYER + 0x32, gy + player_dy)
        c.run_frame()
    spotted = c.memory.u8[npc + 0x0a]
    print(f'{label}: parent type after 240f = {spotted:#x} '
          f'({"SPOTTED" if spotted == 0xff else "not spotted"})')
    return spotted

print('entity offsets: type +0x0a, subtimer +0x0f, knockbackDirection +0x3e, parent +0x50')
a = run(0, 60, 2, 'player 60px SOUTH, guard facing south')
b = run(0, -60, 2, 'player 60px NORTH, guard facing south (control)')
ok = (a == 0xff and b != 0xff)
if '--range' in sys.argv:
    for d in (40, 70, 80, 96, 112):
        run(0, d, 2, 'range: player %dpx SOUTH' % d)
print('PASS: the LOS transplants' if ok else 'FAIL / offsets need checking')
sys.exit(0 if ok else 1)
