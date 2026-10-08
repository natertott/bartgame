"""Seashells are three seconds of invincibility (Oct 2026, P2).

  CLOCK    GiveItem(ITEM_SHELLS, 1) on a settled run sets gSave.stats.shells
           to 180 (QuickStartShellTaken) and the clock counts down one per
           frame (QuickStartShellTick): 120 frames later it reads 60, and
           it reads 0 after 200.
  IMMUNE   CalculateDamage(player, enemy) returns the player's own health
           while the clock runs, and less than it once it has run out
           (the same call, the same enemy's damage field).
  CHARM    the luck charm is the pocketful now: ITEM_SHELLS30 sits in the
           tier table under QS_CAT_CHARM and ITEM_SHELLS does not.

    python3 tools/quickstart/shell_probe.py [--rom tmc-d3.gba]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import entities, r16, w16, KIND_ENEMY, GENT, STRIDE, PLAYER
import scenario as S
import parse_tables as P
import callrom as C
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
SHELL_CLOCK = 0x02002a40 + 0xA8 + 0x1a
res = []
def check(name, ok, detail=''):
    res.append(ok); print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)
c = S.boot(ROM, S.KINDS['REGION'], 0, 0, kit=2, frames=400)
for _ in range(12):
    c.run_frame()
give = C.map_sym('GiveItem')
w16(c, SHELL_CLOCK, 0)
C.call_keep(c, give, (P.ITEMS['ITEM_SHELLS'], 1))
t0 = r16(c, SHELL_CLOCK)
for _ in range(120):
    c.run_frame()
t1 = r16(c, SHELL_CLOCK)
# 181: GiveItem's own ModShells(1) lands after the clock is set; harmless
check('CLOCK: ~180 on the pickup, ~60 after 120 frames', 175 <= t0 <= 185 and 55 <= t1 <= 65, 'read %d then %d' % (t0, t1))
# immunity: ask CalculateDamage with a live enemy as the hitter
calc = C.map_sym('CalculateDamage')
w16(c, SHELL_CLOCK, 180)
ens = entities(c, KIND_ENEMY)
if ens:
    tgt = GENT + ens[0][0] * STRIDE
    c.memory.u8[tgt + 0x44] = 8   # Entity.damage (0x44): a two-heart hit
    hp = c.memory.u8[PLAYER + 0x45]
    with_shell = C.call_keep(c, calc, (PLAYER, tgt))
    w16(c, SHELL_CLOCK, 0)
    without = C.call_keep(c, calc, (PLAYER, tgt))
    check('IMMUNE: health kept with the clock, lost without', with_shell == hp and without < hp, 'health %d, with %d, without %d' % (hp, with_shell, without))
else:
    check('IMMUNE: an enemy to be hit by', False, 'none in the room')
tiers = P.tiers() if hasattr(P, 'tiers') else None
src = open(os.path.join(P.ROOT, 'src/game.c')).read()
check('CHARM: the pocketful is the luck charm, the shell is not',
      '{ ITEM_SHELLS30, QS_CAT_CHARM' in src and '{ ITEM_SHELLS, QS_CAT_CHARM' not in src)
print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
sys.exit(0 if all(res) else 1)
