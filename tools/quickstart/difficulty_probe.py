"""The difficulty counter: seeded once, up on a win, down on a death.

  SEED     a brand-new save's first run reads the build's starting
           difficulty (QUICKSTART_START_DIFFICULTY, 3 on the d3 build), and
           the seeded latch (GF_DIFFICULTY_SEEDED) is set
  DEATH    the player dies (health 0, the run's bottled fairy emptied so it
           cannot revive them): the game-over screen comes, and the counter
           is one lower - down through 2 to 1
  FLOOR    a death at 1 leaves it at 1
  CONTINUE the game-over's Continue goes back to the game, still at the
           demoted value
  KEPT     a save already past the start (5) keeps it on its first run: the
           seed only ever raises

    python3 tools/quickstart/difficulty_probe.py [--rom tmc-d3.gba]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import press, PLAYER
import scenario as S
import parse_tables as P
from chain_audit import dismiss

ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else os.path.join(P.ROOT, 'tmc-d3.gba')
SAVE = 0x02002a40
HEALTH = SAVE + 0xA8 + 2
BOTTLES = SAVE + 0xA8 + 0x0E
GF_DIFFICULTY_BIT0 = 174
GF_DIFFICULTY_SEEDED = 704
TASK = 0x03001000 + 2      # gMain.task (main.h)
TASK_GAMEOVER = 3
res = []


def check(name, ok, detail=''):
    res.append(bool(ok))
    print('%s %-44s %s' % ('PASS' if ok else 'FAIL', name, detail), flush=True)


def qs(c, n):
    b = emu.QS_BIT0 + n
    return (c.memory.u8[emu.SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def difficulty(c):
    return sum(qs(c, GF_DIFFICULTY_BIT0 + b) << b for b in range(4))


def set_difficulty(c, v):
    for b in range(4):
        emu.qs_set(c, GF_DIFFICULTY_BIT0 + b, (v >> b) & 1)


def die(c):
    """Empty the bottles (the run's fairy revives), take the health, and
    run out the death until the game-over task has run its first state.
    Returns the counter then, or None if no game over came."""
    dismiss(c)
    for i in range(4):
        c.memory.u8[BOTTLES + i] = P.ITEMS['ITEM_BOTTLE_EMPTY']
    for _ in range(3000):
        c.memory.u8[HEALTH] = 0
        c.memory.u8[PLAYER + 0x45] = 0   # the entity's health is what the death test reads
        c.run_frame()
        if c.memory.u8[TASK] == TASK_GAMEOVER:
            break
    else:
        return None
    for _ in range(300):
        c.run_frame()
    return difficulty(c)


def continue_game(c):
    """Continue (the first choice): A until the player stands with health."""
    for _ in range(60):
        press(c, c.KEY_A, 3, 30)
        if c.memory.u8[HEALTH] > 0 and c.memory.u8[PLAYER + 0x45] > 0 and c.memory.u8[PLAYER + 0x0c] == 1:
            break
    for _ in range(300):
        c.run_frame()


def main():
    c = S.boot(ROM, 0, frames=300)
    check('SEED: a new save starts at the build difficulty', difficulty(c) == 3 and qs(c, GF_DIFFICULTY_SEEDED),
          'difficulty %d, seeded %d' % (difficulty(c), qs(c, GF_DIFFICULTY_SEEDED)))
    for _ in range(600):   # out of the run's arrival (Ezlo talks in the hub)
        c.run_frame()
    dismiss(c)
    seen = [difficulty(c)]
    for _ in range(3):
        seen.append(die(c))
        continue_game(c)
    check('DEATH: each death is one lower, down to 1', seen[:3] == [3, 2, 1], 'counter %s' % seen)
    check('FLOOR: a death at 1 stays at 1', seen[3] == 1, 'counter %s' % seen)
    check('CONTINUE: back in the game at the demoted value', c.memory.u8[HEALTH] > 0 and difficulty(c) == 1,
          'health %d, difficulty %d, room %s' % (c.memory.u8[HEALTH], difficulty(c), emu.here(c)))
    # A save already at 5 that has never been seeded keeps its 5.
    c = S.boot(ROM, 0, frames=1)
    ok = False
    for _ in range(600):
        set_difficulty(c, 5)
        emu.qs_set(c, GF_DIFFICULTY_SEEDED, 0)
        c.run_frame()
        if c.memory.u8[emu.ROOM_CONTROLS + 4] != 0:
            break
    for _ in range(300):
        c.run_frame()
    check('KEPT: the seed never lowers a save', difficulty(c) == 5, 'difficulty %d' % difficulty(c))
    print('RESULT %s %d/%d' % ('PASS' if all(res) else 'FAIL', sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == '__main__':
    sys.exit(main())
